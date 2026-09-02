"""쓰기 도구 구현. 모든 함수는 ComWorker 스레드 안에서 호출된다.

절차: dry_run=True → plan_id → dry_run=False(plan_id) → sw_save(change_set_id).
"""
from __future__ import annotations

import datetime
import hashlib
import logging
import os
from typing import Optional

from . import api
from .journal import journal, save_order
from .models import DocSelector, SwError
from .read import bom, custom_properties
from .selectors import normalize_path, pick, resolve

log = logging.getLogger("sw.write")
SW_CUSTOM_INFO_TEXT = 30
SW_ADD_REPLACE = 2
SW_SAVE_SILENT = 1
SW_SAVE_REFERENCED = 2
SW_REBUILD_ALL = 1

# ---------------------------------------------------------------- set_properties


def substitute(value, ctx: dict) -> str:
    if not isinstance(value, str):
        return str(value)
    if value == "$today":
        return datetime.date.today().strftime("%Y-%m-%d")  # 프로젝트 DATE 속성은 날짜 타입, yyyy-MM-dd
    if value == "$instances":
        if "instances" not in ctx:
            raise SwError("PLAN_STALE", "$instances를 쓰려면 assembly를 지정해야 합니다")
        return str(ctx["instances"])
    if value.startswith("$expr:"):
        return value[len("$expr:"):]
    return value


def _is_formula(v) -> bool:
    return isinstance(v, str) and v.startswith('"') and "@" in v


def plan_property_changes(current: dict, props: dict) -> tuple[list, list]:
    changes, warnings = [], []
    for name, after in props.items():
        cur = current.get(name)
        if cur is None:
            changes.append({"name": name, "before": None, "after": after, "action": "add"})
            continue
        if _is_formula(cur["value"]) and not _is_formula(after):
            warnings.append(f"{name}: 기존 값이 수식({cur['value']})이라 건너뜀. 덮어쓰려면 '$expr:' 접두어로 지정")
            continue
        if str(cur["value"]) == str(after):
            continue
        changes.append({"name": name, "before": cur["value"], "after": after, "action": "set", "type": cur.get("type", SW_CUSTOM_INFO_TEXT)})
    return changes, warnings


def _targets(app, docs: list[DocSelector], scope: str):
    out = []
    for sel in docs:
        m, info = resolve(app, sel)
        cfg = sel.configuration or (api.active_config_name(m) if scope == "configuration" else "")
        out.append((m, info, cfg if scope == "configuration" else ""))
    return out


def set_properties(docs: list[DocSelector], scope: str, props: dict, assembly: Optional[DocSelector],
                   dry_run: bool, plan_id: Optional[str]) -> dict:
    if scope not in ("file", "configuration"):
        raise SwError("INTERNAL", "scope는 file 또는 configuration")
    app = api.get_app()
    inst_by_path: dict = {}
    if assembly is not None:
        for r in bom(assembly, "parts_only", include_mass=False)["rows"]:
            inst_by_path[normalize_path(r["file"])] = r["instances"]
    targets = _targets(app, docs, scope)
    per_doc, precondition, all_warnings = [], {}, []
    for m, info, cfg in targets:
        ctx = {}
        if normalize_path(info["path"]) in inst_by_path:
            ctx["instances"] = inst_by_path[normalize_path(info["path"])]
        resolved_props = {k: substitute(v, ctx) for k, v in props.items()}
        current = custom_properties(m, cfg)
        changes, warnings = plan_property_changes(current, resolved_props)
        all_warnings += [f"{info['title']}: {w}" for w in warnings]
        per_doc.append({"document": info["title"], "path": info["path"], "configuration": cfg, "changes": changes})
        precondition[info["document_id"] + "|" + cfg] = {c["name"]: c["before"] for c in changes}
    if dry_run:
        plan = journal().create_plan("sw_set_properties", [d["document"] for d in per_doc], per_doc, [], precondition, 200)
        return {"dry_run": True, "plan_id": plan["plan_id"], "expires_in_s": 600, "documents": per_doc, "warnings": all_warnings}
    if not plan_id:
        raise SwError("PLAN_STALE", "dry_run=false에는 plan_id가 필요합니다")
    journal().check_plan(plan_id, "sw_set_properties", precondition)
    dirty, dirty_ids = [], []
    for (m, info, cfg), d in zip(targets, per_doc):
        if not d["changes"]:
            continue
        ext = api.cast("IModelDocExtension", m.Extension)
        cp = api.cast("ICustomPropertyManager", ext.CustomPropertyManager(cfg))
        for c in d["changes"]:
            typ = int(c.get("type") or SW_CUSTOM_INFO_TEXT)
            if c["action"] == "add":
                rc = cp.Add3(c["name"], SW_CUSTOM_INFO_TEXT, str(c["after"]), SW_ADD_REPLACE)
            elif typ in (SW_CUSTOM_INFO_TEXT, 0):
                rc = cp.Set2(c["name"], str(c["after"]))
            else:
                # 날짜(64)·숫자(3) 등: Set2에 형식이 안 맞는 텍스트를 주면 이름 목록에서 사라진 '유령' 값이 남아
                # 이후 Add3까지 막는다(실측 확인). 구형 API로 완전히 지우고 같은 타입으로 재추가한다.
                m.DeleteCustomInfo2(cfg, c["name"])
                rc = cp.Add3(c["name"], typ, str(c["after"]), SW_ADD_REPLACE)
                if rc == 3:
                    raise SwError("COM_ERROR", f"{info['title']} {c['name']}: 값 {c['after']!r}이 속성 타입({typ})과 맞지 않습니다 (날짜는 yyyy-MM-dd)")
            if rc != 0:
                raise SwError("COM_ERROR", f"{info['title']} {c['name']} 설정 실패 rc={rc}")
        dirty.append(info["title"])
        dirty_ids.append(info["document_id"])
    cs = journal().mark_applied(plan_id, dirty, [], dirty_ids)
    return {"dry_run": False, "change_set_id": cs, "applied": per_doc, "dirty_documents": dirty, "warnings": all_warnings}


# ---------------------------------------------------------------- save


class _RenameEvents:
    """DAssemblyDocEvents 핸들러. Save3 중 RenamedDocumentNotify가 오면 닫힌 참조 갱신을 설정."""

    search_folders: list[str] = []
    update_unopened: bool = False
    result: dict = {}

    def OnRenamedDocumentNotify(self, swObj):
        try:
            refs = api.cast("IRenamedDocumentReferences", swObj)
            refs.UpdateWhereUsedReferences = self.update_unopened
            refs.IncludeFileLocations = True
            for f in self.search_folders:
                refs.AddSearchFolder(f)
            found = refs.Search()
            arr = refs.ReferencesArray
            arr = arr() if callable(arr) else arr
            self.result = {"searched": bool(found), "references": list(arr or [])}
            refs.CompletionAction = 0  # swRenamedDocumentFinalAction_Ok
        except Exception as e:  # noqa: BLE001
            self.result = {"error": f"{type(e).__name__}: {e}"}
        return 0


def save_model(app, m, out_path: Optional[str] = None, rename: Optional[dict] = None) -> dict:
    # Save3/SaveAs3는 비활성 문서에도 동작한다(실측 확인) → 사용자 화면의 활성 탭을 바꾸지 않는다.
    # 이름 변경 저장만 RenamedDocumentNotify 처리를 위해 부모를 활성화한다.
    if rename and int(m.GetType()) == 2:
        api.activate(app, m)
    err, warn = api.byref_int(), api.byref_int()
    result: dict = {"title": m.GetTitle()}
    if out_path:
        ext = api.cast("IModelDocExtension", m.Extension)
        ok = api.dyn(ext).SaveAs3(out_path, 0, SW_SAVE_SILENT, api.empty_dispatch(), api.empty_dispatch(), err, warn)
    elif rename and int(m.GetType()) == 2:
        # 이름 바뀐 컴포넌트가 있는 어셈블리: Silent로 저장하면 8192(RequiresSavingReferences)로 거부된다.
        # SaveReferenced만 주고, RenamedDocumentNotify 이벤트를 싱크로 받아 참조 갱신을 처리한다 (실측 확인).
        # WithEvents()는 GetTypeInfo가 없는 SolidWorks에서 실패하므로 gen_py 이벤트 클래스를 직접 인스턴스화한다.
        handler = None
        try:
            import win32com.client

            ev = win32com.client.getevents(api.mod().AssemblyDoc.CLSID)

            class _Sink(ev, _RenameEvents):
                pass

            handler = _Sink(m)  # _oleobj_를 가진 래퍼를 넘겨야 함
            handler.search_folders = rename["search_folders"]
            handler.update_unopened = rename["update_unopened"]
        except Exception as e:  # noqa: BLE001
            result["warning"] = f"닫힌 참조 갱신 이벤트 미연결({type(e).__name__}) — SolidWorks 대화상자가 떴을 수 있음"
        try:
            ok = api.dyn(m).Save3(SW_SAVE_REFERENCED, err, warn)
        finally:
            if handler is not None:
                result["references"] = handler.result
                try:
                    handler.close()
                except Exception:  # noqa: BLE001
                    pass
    else:
        ok = api.dyn(m).Save3(SW_SAVE_SILENT, err, warn)
    e, w = int(err.value or 0), int(warn.value or 0)
    if not ok or e:
        raise SwError("COM_ERROR", f"저장 실패: {m.GetTitle()} errors={e} warnings={w}")
    result.update(path=out_path or m.GetPathName(), errors=e, warnings=w)
    return result


def pick_change_set_docs(cs: dict, wanted: list[dict], open_docs: list[dict]) -> list[dict]:
    """change_set이 가리키는 문서를 열린 문서 목록에서 고른다 (순수 함수 — 단위 테스트 대상).

    핸들로 이미 채운 `wanted`는 그대로 두고, 나머지는 dirty_ids(정규화 경로)로 먼저 대조한다.
    id가 없는 옛 change_set만 제목으로 대조하되, 같은 제목이 둘 이상 열려 있으면 고르지 않고 멈춘다 —
    계획에 없던 다른 폴더의 동명 파일을 저장하는 사고를 막기 위해서다.
    """
    have_ids = {d["document_id"] for d in wanted}
    have_titles = {d["title"] for d in wanted}
    out = list(wanted)
    for did in cs.get("dirty_ids") or []:
        if did in have_ids:
            continue
        hits = [d for d in open_docs if d["document_id"] == did]
        if hits:
            out.append(hits[0])
            have_ids.add(did)
            have_titles.add(hits[0]["title"])
    remaining = [t for t in cs["dirty_documents"] if t not in have_titles]
    for t in remaining:
        hits = [d for d in open_docs if d["title"] == t and d["document_id"] not in have_ids]
        if len(hits) > 1:
            raise SwError("DOC_AMBIGUOUS", f"같은 이름의 문서가 {len(hits)}개 열려 있어 어느 것을 저장할지 정할 수 없습니다: {t}",
                          {"candidates": [h.get("path") for h in hits]})
        if hits:
            out.append(hits[0])
            have_ids.add(hits[0]["document_id"])
            have_titles.add(t)
    missing = [t for t in cs["dirty_documents"] if t not in have_titles]
    if missing:
        raise SwError("DOC_NOT_FOUND", f"change_set의 문서가 열려 있지 않습니다: {sorted(missing)}")
    return out


def check_save_scope(docs: list[dict], only_under: list[str]) -> list[str]:
    """only_under 밖의 문서 경로를 돌려준다 (순수 함수). 공용 라이브러리·타 프로젝트 문서가
    저장 루프에 딸려 들어가는 사고를 막는 화이트리스트."""
    if not only_under:
        return []
    roots = [normalize_path(r).rstrip("\\/") + os.sep for r in only_under]
    outside = []
    for d in docs:
        p = d.get("path")
        if not p:
            continue  # 미저장 문서는 out_path로 별도 판정
        if not any(normalize_path(p).startswith(r) for r in roots):
            outside.append(p)
    return outside


def save(change_set_id: Optional[str], doc: Optional[DocSelector], out_path: Optional[str], dry_run: bool,
         only_under: Optional[list[str]] = None) -> dict:
    app = api.get_app()
    rename = None
    if change_set_id:
        cs = journal().get_change_set(change_set_id)
        rename = cs.get("rename")
        handles = journal().get_handles(change_set_id)
        wanted = []
        if handles:
            # 생성/변경 도구가 보관한 문서 객체로 직접 (제목 중복·미저장·이름 바뀐 문서 안전)
            active_key = api._active_key(app)
            for h in handles:
                d = api.doc_info(app, h, active_key)
                d["_raw"] = h
                wanted.append(d)
        need = [t for t in cs["dirty_documents"] if t not in {d["title"] for d in wanted}]
        # 핸들로 못 채운 문서만 전체 열거로 찾는다 (열거는 SolidWorks가 바쁠 때 1분 이상)
        open_docs = api.list_docs(app, with_raw=True, light=True) if need else []
        wanted = pick_change_set_docs(cs, wanted, open_docs)
    elif doc is not None:
        if doc.path and not doc.active:
            m0, info0 = resolve(app, doc)  # 경로면 열거 없이 1회 호출
            info0["_raw"] = m0
            wanted = [info0]
        else:
            wanted = [pick(api.list_docs(app, with_raw=True), doc)]
    else:
        raise SwError("PLAN_STALE", "change_set_id 또는 doc 중 하나가 필요합니다")
    ordered = save_order(wanted)
    unsaved = [d["title"] for d in ordered if not d["path"]]
    if unsaved and not out_path:
        raise SwError("FILE_EXISTS", "저장된 적 없는 문서는 out_path가 필요합니다: " + ", ".join(unsaved))
    if len(unsaved) > 1 and out_path:
        raise SwError("FILE_EXISTS", f"out_path 하나에 미저장 문서 {len(unsaved)}개를 저장할 수 없습니다 (뒤의 것이 앞의 것을 덮어씀): "
                                     + ", ".join(unsaved) + " — 문서별로 sw_save(doc=..., out_path=...)")
    if out_path and os.path.exists(out_path):
        raise SwError("FILE_EXISTS", f"이미 존재: {out_path}")
    outside = check_save_scope(ordered, only_under or [])
    if outside:
        raise SwError("FILE_EXISTS", f"only_under 밖의 문서 {len(outside)}개는 저장하지 않습니다 (공용 라이브러리·타 프로젝트 보호)",
                      {"outside": outside, "only_under": only_under})
    if dry_run:
        return {"dry_run": True, "will_save": [{"title": d["title"], "path": d["path"] or out_path, "dirty": d["dirty"], "type": d["type"]} for d in ordered]}
    saved = []
    for d in ordered:
        m = api.find_doc(app, d)
        saved.append(save_model(app, m, out_path if not d["path"] else None, rename))
    if change_set_id:
        journal().mark_saved(change_set_id, [s["title"] for s in saved])
    return {"dry_run": False, "saved": saved}


# ---------------------------------------------------------------- export

FORMATS = {"step": (".step", {"part", "assembly"}), "stl": (".stl", {"part", "assembly"}),
           "png": (".png", {"part", "assembly", "drawing"}), "pdf": (".pdf", {"drawing"}), "dxf": (".dxf", {"drawing"})}


def export_check(doc_type: str, fmt: str, out_path: str, overwrite: bool) -> str:
    if fmt not in FORMATS:
        raise SwError("INTERNAL", f"format은 {list(FORMATS)} 중 하나")
    ext, allowed = FORMATS[fmt]
    if doc_type not in allowed:
        raise SwError("INTERNAL", f"{fmt}는 {sorted(allowed)} 문서에만 가능 (현재 {doc_type})")
    if not out_path.lower().endswith(ext):
        raise SwError("INTERNAL", f"out_path 확장자는 {ext}여야 합니다")
    if os.path.exists(out_path) and not overwrite:
        raise SwError("FILE_EXISTS", f"이미 존재: {out_path} (overwrite=true로 허용)")
    return ext


def export(sel: DocSelector, fmt: str, out_path: str, overwrite: bool) -> dict:
    app = api.get_app()
    m, info = resolve(app, sel)
    export_check(info["type"], fmt, out_path, overwrite)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    backup_dir = None
    if os.path.exists(out_path):
        # overwrite=true여도 덮어쓰기 전 원본을 _backup/에 남긴다 (rename과 같은 규칙)
        backup_dir = journal().backup([out_path], related=[info.get("path") or info["title"]],
                                      reason=f"export overwrite {os.path.basename(out_path)}")["dir"]
    # 비활성 문서에서도 SaveAs3 내보내기가 된다(실측 확인) → 활성 탭을 건드리지 않는다.
    m.ClearSelection2(True)
    ext = api.cast("IModelDocExtension", m.Extension)
    err, warn = api.byref_int(), api.byref_int()
    ok = api.dyn(ext).SaveAs3(out_path, 0, SW_SAVE_SILENT, api.empty_dispatch(), api.empty_dispatch(), err, warn)
    e = int(err.value or 0)
    if not ok or e or not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
        raise SwError("COM_ERROR", f"내보내기 실패 또는 파일 미생성: {out_path} (errors={e})")
    data = open(out_path, "rb").read()
    return {"path": out_path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "warnings_bits": int(warn.value or 0),
            "backup": backup_dir}


# ---------------------------------------------------------------- rename


def rename_sequence(old_numbers: list[int], removed: int, prefix: str, suffix: str, width: int = 2) -> list[tuple[str, str]]:
    return [(f"{prefix}{n:0{width}d}{suffix}", f"{prefix}{n - 1:0{width}d}{suffix}") for n in sorted(x for x in old_numbers if x > removed)]


def find_referencing_docs(docs: list[dict], target_path: str) -> list[str]:
    want = normalize_path(target_path)
    return [d["title"] for d in docs if any(normalize_path(p) == want for p in d.get("deps", []))]


_DEPS_CACHE: dict = {"t": 0.0, "data": None}


def _deps_of_open_docs(app, max_age_s: float = 90.0) -> list[dict]:
    """열린 문서의 참조 목록. 문서 348개 × 5회 호출이라 SolidWorks가 바쁠 때 1분 넘게 걸리므로
    같은 프로세스 안에서는 max_age_s 동안 캐시한다 (dry_run → apply 사이 재사용)."""
    import time

    if _DEPS_CACHE["data"] is not None and time.time() - _DEPS_CACHE["t"] < max_age_s:
        return _DEPS_CACHE["data"]
    out = []
    for d in api.list_docs(app, with_raw=True, light=True):
        deps = []
        if d["type"] in ("assembly", "drawing"):
            try:
                raw = d["_raw"].GetDependencies2(False, True, False) or ()
                deps = [raw[i] for i in range(1, len(raw), 2)]
            except Exception:  # noqa: BLE001
                pass
        out.append({"title": d["title"], "type": d["type"], "path": d["path"], "deps": deps})
    _DEPS_CACHE.update(t=time.time(), data=out)
    return out


def rename_document(target: DocSelector, parent: DocSelector, new_name: str, update_unopened_references: bool,
                    search_folders: list[str], sync_properties: Optional[dict], move_existing: bool,
                    dry_run: bool, plan_id: Optional[str]) -> dict:
    if os.path.splitext(new_name)[1]:
        raise SwError("INTERNAL", "new_name은 확장자 없이 지정 (예: PART-104)")
    app = api.get_app()
    tm, tinfo = resolve(app, target)
    pm, pinfo = resolve(app, parent)
    if pinfo["type"] != "assembly":
        raise SwError("DOC_NOT_FOUND", "parent_assembly는 어셈블리여야 합니다")
    if not tinfo["path"]:
        raise SwError("DOC_NOT_FOUND", "저장된 적 없는 문서는 이름을 바꿀 수 없습니다")
    folder = os.path.dirname(tinfo["path"])
    new_path = os.path.join(folder, new_name + os.path.splitext(tinfo["path"])[1])
    exists = os.path.exists(new_path)
    if exists and not move_existing:
        raise SwError("FILE_EXISTS", f"이미 존재: {new_path} (move_existing=true면 _backup으로 옮김)")
    cm = api.cast("IConfigurationManager", pm.ConfigurationManager)
    root = api.cast("IComponent2", api.cast("IConfiguration", cm.ActiveConfiguration).GetRootComponent3(True))
    comps = [api.cast("IComponent2", c) for c in (root.GetChildren() or [])]
    comps = [c for c in comps if normalize_path(c.GetPathName()) == normalize_path(tinfo["path"])]
    if not comps:
        raise SwError("DOC_NOT_FOUND", f"{pinfo['title']}의 직계 컴포넌트 중 {tinfo['title']}이 없습니다")
    comp = comps[0]
    open_refs = find_referencing_docs(_deps_of_open_docs(app), tinfo["path"])
    precondition = {"target": tinfo["path"], "parent": pinfo["path"], "component": comp.Name2, "new_exists": exists,
                    "parent_dirty": pinfo["dirty"]}
    plan_body = {"target": tinfo, "parent": pinfo["title"], "component": comp.Name2, "new_name": new_name, "new_path": new_path,
                 "existing_file_will_move": exists, "open_referencing_docs": open_refs,
                 "update_unopened_references": update_unopened_references, "search_folders": search_folders or [folder],
                 "sync_properties": sync_properties or {},
                 "note": "RenameDocument는 메모리 임시 변경. sw_save(change_set_id)로 부모 어셈블리를 저장해야 파일명이 바뀜"}
    if dry_run:
        plan = journal().create_plan("sw_rename_document", [tinfo["title"]], [plan_body], [new_path], precondition, 20)
        return {"dry_run": True, "plan_id": plan["plan_id"], **plan_body}
    if not plan_id:
        raise SwError("PLAN_STALE", "dry_run=false에는 plan_id가 필요합니다")
    journal().check_plan(plan_id, "sw_rename_document", precondition)
    man = journal().backup([tinfo["path"], pinfo["path"]] + ([new_path] if exists else []),
                           related=open_refs, reason=f"rename {tinfo['title']} -> {new_name}")
    if exists:
        import shutil

        shutil.move(new_path, os.path.join(man["dir"], "moved_" + os.path.basename(new_path)))  # 드라이브가 달라도 이동
    api.activate(app, pm)
    pm.ClearSelection2(True)
    ext = api.cast("IModelDocExtension", pm.Extension)
    sel_name = f"{comp.Name2}@{os.path.splitext(pinfo['title'])[0]}"
    if not ext.SelectByID2(sel_name, "COMPONENT", 0, 0, 0, False, 0, None, 0):
        raise SwError("COM_ERROR", f"컴포넌트 선택 실패: {sel_name}")
    rc = int(ext.RenameDocument(new_name))
    if rc != 0:
        raise SwError("COM_ERROR", f"RenameDocument 실패 (swRenameDocumentError_e={rc})")
    ext.Rebuild(SW_REBUILD_ALL)
    synced = {}
    if sync_properties:
        cp = api.cast("ICustomPropertyManager", api.cast("IModelDocExtension", tm.Extension).CustomPropertyManager(""))
        for k, v in sync_properties.items():
            v = substitute(v, {})
            if cp.Set2(k, v) != 0:
                cp.Add3(k, SW_CUSTOM_INFO_TEXT, v, SW_ADD_REPLACE)
            synced[k] = v
    # 대상 파트는 이름이 이미 바뀌어 제목으로 다시 찾을 수 없다 → 부모 어셈블리를 핸들로 저장(SaveReferenced가 파트도 저장)
    dirty = [pinfo["title"]] + [r for r in open_refs if r not in (tinfo["title"], pinfo["title"])]
    cs = journal().mark_applied(plan_id, dirty, [], [pinfo["document_id"]])
    journal().get_change_set(cs)["rename"] = {"update_unopened": update_unopened_references, "search_folders": search_folders or [folder]}
    journal().attach_handles(cs, [pm])
    return {"dry_run": False, "change_set_id": cs, "renamed_component": comp.Name2, "new_name": new_name,
            "backup": man["dir"], "synced_properties": synced, "dirty_documents": dirty,
            "next": "sw_save(change_set_id) 로 부모 어셈블리를 저장하면 파일명이 바뀝니다"}


# ---------------------------------------------------------------- add_component

MATE_TYPES = {"coincident": 0, "concentric": 1, "distance": 5}
SW_MATE_ALIGN_CLOSEST = 2
ENTITY_TYPES = ("FACE", "EDGE", "PLANE", "AXIS", "VERTEX")


def validate_mates(mates: list[dict]) -> list[dict]:
    out = []
    for i, m in enumerate(mates or []):
        t = m.get("type")
        if t not in MATE_TYPES:
            raise SwError("INTERNAL", f"mates[{i}].type은 {list(MATE_TYPES)} 중 하나")
        for side in ("a", "b"):
            e = m.get(side) or {}
            if e.get("type") not in ENTITY_TYPES or len(e.get("xyz_mm") or []) != 3:
                raise SwError("INTERNAL", f"mates[{i}].{side}는 type({'/'.join(ENTITY_TYPES)})과 xyz_mm[3] 필요")
        spec = {"code": MATE_TYPES[t], "type": t, "a": m["a"], "b": m["b"], "distance_m": 0.0}
        if t == "distance":
            if "distance_mm" not in m:
                raise SwError("INTERNAL", f"mates[{i}] distance에는 distance_mm 필요")
            spec["distance_m"] = float(m["distance_mm"]) / 1000.0
        out.append(spec)
    return out


def _select_entity(ext, e: dict, append: bool, mark: int) -> bool:
    x, y, z = (v / 1000.0 for v in e["xyz_mm"])
    return bool(ext.SelectByID2(e.get("name") or "", e["type"], x, y, z, append, mark, None, 0))


def add_component(assembly: DocSelector, part_path: str, position_mm: list[float], mates: list[dict],
                  rollback: str, dry_run: bool, plan_id: Optional[str]) -> dict:
    if not os.path.isfile(part_path):
        raise SwError("DOC_NOT_FOUND", f"부품 파일이 없습니다: {part_path}")
    if rollback not in ("delete_component", "keep"):
        raise SwError("INTERNAL", "rollback은 delete_component 또는 keep")
    if len(position_mm or []) != 3:
        raise SwError("INTERNAL", "position_mm은 [x, y, z]")
    specs = validate_mates(mates)
    app = api.get_app()
    pm, pinfo = resolve(app, assembly)
    if pinfo["type"] != "assembly":
        raise SwError("DOC_NOT_FOUND", "assembly는 어셈블리여야 합니다")
    a = api.cast("IAssemblyDoc", pm)
    before_count = int(a.GetComponentCount(True))
    precondition = {"assembly": pinfo["path"], "top_level_count": before_count, "part": normalize_path(part_path)}
    body = {"assembly": pinfo["title"], "part_path": part_path, "position_mm": position_mm, "mates": specs,
            "rollback": rollback, "top_level_count_before": before_count}
    if dry_run:
        plan = journal().create_plan("sw_add_component", [pinfo["title"]], [body], [], precondition, 1)
        return {"dry_run": True, "plan_id": plan["plan_id"], **body}
    if not plan_id:
        raise SwError("PLAN_STALE", "dry_run=false에는 plan_id가 필요합니다")
    journal().check_plan(plan_id, "sw_add_component", precondition)
    api.activate(app, pm)
    x, y, z = (v / 1000.0 for v in position_mm)
    comp = api.cast("IComponent2", a.AddComponent5(part_path, 0, "", False, "", x, y, z))
    if comp is None:
        raise SwError("COM_ERROR", "AddComponent5가 컴포넌트를 돌려주지 않았습니다 (경로/구성 확인)")
    ext = api.cast("IModelDocExtension", pm.Extension)
    added, failed = [], None
    for i, s in enumerate(specs):
        pm.ClearSelection2(True)
        if not (_select_entity(ext, s["a"], False, 1) and _select_entity(ext, s["b"], True, 1)):
            failed = f"mates[{i}] 엔티티 선택 실패"
            break
        # AddMate5(..., ErrorStatus[out]) -> (mate, errorStatus)
        r = a.AddMate5(s["code"], SW_MATE_ALIGN_CLOSEST, False, s["distance_m"], 0, 0, 0, 0, 0, 0, 0, False, False, 0)
        mate, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, 0)
        if mate is None or err != 0:
            failed = f"mates[{i}] AddMate5 실패 (swAddMateError_e={err})"
            break
        added.append(s["type"])
    pm.ClearSelection2(True)
    if failed and rollback == "delete_component":
        comp.Select4(False, None, False)
        pm.EditDelete()
        raise SwError("COM_ERROR", f"{failed} — 컴포넌트 삭제(rollback)")
    ext.Rebuild(SW_REBUILD_ALL)
    cs = journal().mark_applied(plan_id, [pinfo["title"]], [], [pinfo["document_id"]])
    return {"dry_run": False, "change_set_id": cs, "component": comp.Name2, "mates_added": added,
            "mate_failure": failed, "dirty_documents": [pinfo["title"]]}


# ---------------------------------------------------------------- delete_components


def select_delete_targets(children: list[dict], names: list[str], path_contains: Optional[str]) -> list[dict]:
    """삭제 대상 고르기 (순수 함수). children = [{"name", "path"}]. names는 정확히 일치, path_contains는
    정규화 경로 부분 문자열. 둘 다 없으면 아무것도 고르지 않는다 — '전부'는 선택지가 아니다."""
    want = set(names or [])
    sub = normalize_path(path_contains) if path_contains else None
    out = []
    for c in children:
        by_name = c["name"] in want
        by_path = bool(sub) and sub in normalize_path(c.get("path") or "")
        if by_name or by_path:
            out.append(c)
    unknown = sorted(want - {c["name"] for c in children})
    if unknown:
        raise SwError("DOC_NOT_FOUND", f"어셈블리 직계 컴포넌트에 없는 이름: {unknown}")
    return out


def delete_components(assembly: DocSelector, names: list[str], path_contains: Optional[str],
                      dry_run: bool, plan_id: Optional[str]) -> dict:
    """어셈블리 직계 컴포넌트 삭제. 반드시 dry_run으로 전수 목록을 받은 뒤 plan_id로 적용. 저장은 sw_save.

    실제 사고(경로 필터 일괄 삭제 + 즉시 저장)의 재발 방지 — 목록·확인·저장이 세 단계로 나뉜다.
    """
    if not names and not path_contains:
        raise SwError("INTERNAL", "names 또는 path_contains 중 하나는 필요합니다 (전체 삭제는 지원하지 않음)")
    app = api.get_app()
    pm, pinfo = resolve(app, assembly)
    if pinfo["type"] != "assembly":
        raise SwError("DOC_NOT_FOUND", "assembly는 어셈블리여야 합니다")
    cm = api.cast("IConfigurationManager", pm.ConfigurationManager)
    root = api.cast("IComponent2", api.cast("IConfiguration", cm.ActiveConfiguration).GetRootComponent3(True))
    comps = [api.cast("IComponent2", c) for c in (root.GetChildren() or [])]
    children = [{"name": c.Name2, "path": c.GetPathName() or ""} for c in comps]
    targets = select_delete_targets(children, names or [], path_contains)
    precondition = {"assembly": pinfo["path"], "targets": sorted(t["name"] for t in targets),
                    "top_level_count": len(children), "dirty": pinfo["dirty"]}
    body = {"assembly": pinfo["title"], "assembly_path": pinfo["path"], "targets": targets,
            "remaining_after": len(children) - len(targets),
            "note": "메모리에서만 삭제됨. 저장은 sw_save(change_set_id) — Ctrl+Z로 되돌릴 수 있음"}
    if dry_run:
        plan = journal().create_plan("sw_delete_components", [t["name"] for t in targets], [body], [], precondition, 50)
        return {"dry_run": True, "plan_id": plan["plan_id"], **body}
    if not plan_id:
        raise SwError("PLAN_STALE", "dry_run=false에는 plan_id가 필요합니다")
    journal().check_plan(plan_id, "sw_delete_components", precondition)
    if not targets:
        raise SwError("DOC_NOT_FOUND", "삭제 대상이 없습니다")
    api.activate(app, pm)
    ext = api.cast("IModelDocExtension", pm.Extension)
    base = os.path.splitext(pinfo["title"])[0]
    deleted, failed = [], []
    for t in targets:
        pm.ClearSelection2(True)
        ok = ext.SelectByID2(f"{t['name']}@{base}", "COMPONENT", 0, 0, 0, False, 0, None, 0)
        if ok and ext.DeleteSelection2(0):
            deleted.append(t["name"])
        else:
            failed.append(t["name"])
    pm.ClearSelection2(True)
    ext.Rebuild(SW_REBUILD_ALL)
    # 보고는 말이 아니라 관측으로: 삭제 후 직계 컴포넌트를 다시 세어 대조한다
    after = [api.cast("IComponent2", c).Name2 for c in (root.GetChildren() or [])]
    still = [n for n in deleted if n in after]
    cs = journal().mark_applied(plan_id, [pinfo["title"]], [], [pinfo["document_id"]])
    return {"dry_run": False, "change_set_id": cs, "deleted": deleted, "failed": failed, "still_present": still,
            "top_level_count_after": len(after), "dirty_documents": [pinfo["title"]],
            "next": "sw_save(change_set_id) 로 저장. 저장 전이면 SolidWorks Ctrl+Z로 되돌릴 수 있음"}


# ---------------------------------------------------------------- create_drawing

DEFAULT_TEMPLATE = r"C:\ProgramData\SOLIDWORKS\SOLIDWORKS 2024\templates\도면.DRWDOT"
DRAWING_VIEWS = {"front", "top", "right", "iso"}
ISO_VIEW_NAMES = ("*Isometric", "*등각 보기", "*등각보기", "*Isometrisch", "*等轴测")


def drawing_plan(model_info: dict, template: str, views: list[str], bom: bool, auto_dimension: bool) -> dict:
    if model_info["type"] == "drawing":
        raise SwError("INTERNAL", "도면에서 도면을 만들 수 없습니다")
    if not model_info["path"]:
        raise SwError("DOC_NOT_FOUND", "저장된 적 없는 모델은 도면을 만들 수 없습니다 (먼저 sw_save)")
    if not os.path.isfile(template):
        raise SwError("DOC_NOT_FOUND", f"도면 템플릿이 없습니다: {template}")
    bad = [v for v in views if v not in DRAWING_VIEWS]
    if bad:
        raise SwError("INTERNAL", f"views는 {sorted(DRAWING_VIEWS)} 중에서: {bad}")
    return {"model": model_info["title"], "model_path": model_info["path"], "template": template, "views": views,
            "bom": bool(bom and model_info["type"] == "assembly"), "auto_dimension": auto_dimension}


def _drawing_views(drw) -> list:
    """시트 뷰(첫 뷰)를 제외한 모델 뷰 목록."""
    out = []
    v = api.cast("IView", drw.GetFirstView())
    v = api.cast("IView", v.GetNextView()) if v else None
    while v:
        out.append(v)
        v = api.cast("IView", v.GetNextView())
    return out


def create_drawing(sel: DocSelector, template: Optional[str], views: list[str], bom: bool, auto_dimension: bool,
                   dry_run: bool, plan_id: Optional[str]) -> dict:
    app = api.get_app()
    m, info = resolve(app, sel)
    plan_body = drawing_plan(info, template or DEFAULT_TEMPLATE, views, bom, auto_dimension)
    precondition = {"model": info["path"], "dirty": info["dirty"]}
    if dry_run:
        plan = journal().create_plan("sw_create_drawing", [info["title"]], [plan_body], [], precondition, 1)
        return {"dry_run": True, "plan_id": plan["plan_id"], **plan_body,
                "note": "생성만 함(메모리). 저장은 sw_save(doc={title}, out_path=...), PDF는 sw_export"}
    if not plan_id:
        raise SwError("PLAN_STALE", "dry_run=false에는 plan_id가 필요합니다")
    journal().check_plan(plan_id, "sw_create_drawing", precondition)
    drw_raw = app.NewDocument(plan_body["template"], 0, 0.0, 0.0)
    if drw_raw is None:
        raise SwError("COM_ERROR", "NewDocument 실패 (템플릿 확인)")
    drw_m = api.cast("IModelDoc2", drw_raw)
    drw = api.cast("IDrawingDoc", drw_raw)
    created = []
    if any(v in ("front", "top", "right") for v in views):
        if not drw.Create3rdAngleViews2(plan_body["model_path"]):
            raise SwError("COM_ERROR", "Create3rdAngleViews2 실패")
        created += ["front", "top", "right"]
    if "iso" in views:
        # 표준 뷰 이름은 SolidWorks 언어판마다 다르다 (영문 *Isometric, 한국어 *등각 보기) → 모델에서 실제 이름을 찾는다
        available = [n for n in (m.GetModelViewNames() or [])]
        candidates = [n for n in available if n.lower().replace(" ", "") in {c.lower().replace(" ", "") for c in ISO_VIEW_NAMES}]
        ok = False
        for name in candidates + [n for n in ISO_VIEW_NAMES if n not in candidates]:
            if drw.CreateDrawViewFromModelView3(plan_body["model_path"], name, 0.32, 0.08, 0.0) is not None:
                ok = True
                break
        if not ok:
            raise SwError("COM_ERROR", f"등각 뷰 생성 실패 (모델 뷰 이름: {available})")
        created.append("iso")
    ext = api.cast("IModelDocExtension", drw_m.Extension)
    model_views = _drawing_views(drw)
    bom_inserted = False
    if plan_body["bom"] and model_views:
        first = model_views[0]
        drw_m.ClearSelection2(True)
        ext.SelectByID2(first.Name, "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)
        # IView.InsertBomTable4(UseAnchorPoint, X, Y, AnchorType, BomType(0=top level), Configuration, TableTemplate, Hidden, IndentedNumberingType, DetailedCutList)
        t = first.InsertBomTable4(False, 0.02, 0.27, 1, 0, "", "", False, 1, False)
        bom_inserted = t is not None
    if auto_dimension:
        for v in model_views:
            drw_m.ClearSelection2(True)
            ext.SelectByID2(v.Name, "DRAWINGVIEW", 0, 0, 0, False, 0, None, 0)
            try:
                drw.AutoDimension(0, 0, 0, 0, 0)
            except Exception as e:  # noqa: BLE001
                log.warning("AutoDimension 실패 %s: %s", v.Name, e)
    drw_m.ForceRebuild3(False)
    title = drw_m.GetTitle()
    cs = journal().mark_applied(plan_id, [title], [])
    journal().attach_handles(cs, [drw_m])  # 미저장 도면은 제목이 겹칠 수 있어 객체로 보관
    return {"dry_run": False, "change_set_id": cs, "drawing_title": title, "views_created": created, "bom_inserted": bom_inserted,
            "view_names": [v.Name for v in model_views], "dirty_documents": [title],
            "next": f"sw_save(doc={{'title':'{title}'}}, out_path='...SLDDRW') → sw_export(pdf)"}
