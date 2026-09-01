"""읽기 도구 구현. 모든 함수는 ComWorker 스레드 안에서 호출된다."""
from __future__ import annotations

import contextlib
import hashlib
import logging
import os
import re
import time

from . import api
from .models import DocSelector, SwError, state_value
from .selectors import normalize_path, resolve

log = logging.getLogger("sw.read")
SIM_PROGIDS = ("SldWorks.Simulation", "CosmosWorks.CosmosWorks")
SIM_DIR = r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\Simulation"
SUPPRESSION = {0: "suppressed", 1: "lightweight", 2: "ok", 3: "ok"}
VIEW_IDS = {"front": 1, "back": 2, "left": 3, "right": 4, "top": 5, "bottom": 6, "iso": 7}


# ---------------------------------------------------------------- status

def _simulation_state(app) -> dict:
    loaded = False
    for pid in SIM_PROGIDS:
        try:
            if app.GetAddInObject(pid):
                loaded = True
                break
        except Exception:  # noqa: BLE001
            pass
    return {"registered": os.path.isdir(SIM_DIR), "loaded": loaded, "license": "unknown"}


def _referenced_paths(app, docs: list[dict]) -> set[str]:
    """docs는 list_docs(with_raw=True) 결과. 어셈블리·도면의 참조 경로 집합."""
    refs: set[str] = set()
    for d in docs:
        if d["type"] in ("assembly", "drawing"):
            try:
                deps = d["_raw"].GetDependencies2(False, True, False) or ()
                refs.update(normalize_path(deps[i]) for i in range(1, len(deps), 2))
            except Exception:  # noqa: BLE001
                pass
    return refs


def status() -> dict:
    try:
        app = api.get_app()
    except SwError as e:
        if e.code == "SW_NOT_RUNNING":
            return {"connected": False, "version": None, "active": None, "documents": [], "open_count": 0,
                    "dirty_count": 0, "dirty_documents": [], "top_level_assemblies": [], "simulation": None}
        raise
    docs = api.list_docs(app, with_raw=True)
    referenced = _referenced_paths(app, docs)
    top_asms = [d["path"] or d["title"] for d in docs
                if d["type"] == "assembly" and normalize_path(d["path"]) not in referenced]
    for d in docs:
        d.pop("_raw", None)
    from . import background

    return {
        "connected": True,
        "mode": "background" if background._STATE["app"] is not None else "user",
        "version": app.RevisionNumber(),
        "active": next((d for d in docs if d["active"]), None),
        "documents": docs,
        "open_count": len(docs),
        "dirty_count": sum(1 for d in docs if d["dirty"]),
        "dirty_documents": [d["title"] for d in docs if d["dirty"]],
        "top_level_assemblies": top_asms,
        "simulation": _simulation_state(app),
    }


# ---------------------------------------------------------------- common readers

@contextlib.contextmanager
def with_configuration(m, name: str | None):
    """구성을 바꿔 읽고 끝나면 원래 구성으로 복원."""
    if not name:
        yield
        return
    original = api.active_config_name(m)
    if name == original:
        yield
        return
    if not m.ShowConfiguration2(name):
        raise SwError("DOC_NOT_FOUND", f"구성이 없습니다: {name}")
    try:
        yield
    finally:
        m.ShowConfiguration2(original)


def custom_properties(m, config: str = "") -> dict:
    ext = api.cast("IModelDocExtension", m.Extension)
    cp = api.cast("ICustomPropertyManager", ext.CustomPropertyManager(config))
    out = {}
    for name in (cp.GetNames() or []):
        # Get6(name, UseCached=True) -> (ret, ValOut, ResolvedValOut, WasResolved, LinkToProperty)
        r = cp.Get6(name, True)
        val, resolved = (r[1], r[2]) if isinstance(r, tuple) else (r, r)
        out[name] = {"value": val, "resolved": resolved, "type": int(cp.GetType2(name))}
    return out


def _mass(ext) -> dict | None:
    mp = api.cast("IMassProperty", ext.CreateMassProperty())
    if mp is None:
        return None
    return {"mass_kg": round(mp.Mass, 4), "volume_mm3": round(mp.Volume * 1e9, 1),
            "surface_area_mm2": round(mp.SurfaceArea * 1e6, 1), "density_kg_m3": round(mp.Density, 1)}


def _bbox(box) -> dict | None:
    if not box or len(box) < 6:
        return None
    return {"x": round((box[3] - box[0]) * 1000, 2), "y": round((box[4] - box[1]) * 1000, 2),
            "z": round((box[5] - box[2]) * 1000, 2), "note": "approximate (GetPartBox/GetBox)"}


def _material(m) -> dict:
    raw = m.MaterialIdName or ""
    if not raw:
        return {"value": None, "database": None, "state": "not_assigned", "source": "MaterialIdName"}
    db, _, name = raw.rpartition("|")
    return {"value": name or raw, "database": db or None, "state": "ok", "source": "MaterialIdName"}


# ---------------------------------------------------------------- summary

def summary(sel: DocSelector) -> dict:
    app = api.get_app()
    m, info = resolve(app, sel)
    with with_configuration(m, sel.configuration):
        ext = api.cast("IModelDocExtension", m.Extension)
        cfg = api.active_config_name(m) if info["type"] != "drawing" else ""
        data = {
            **info,
            "configurations": list(m.GetConfigurationNames() or []) if info["type"] != "drawing" else [],
            "custom_properties": {"file": custom_properties(m, ""), "configuration": custom_properties(m, cfg) if cfg else {}},
            "feature_count": int(api.cast("IFeatureManager", m.FeatureManager).GetFeatureCount(False)),
        }
        if info["type"] == "part":
            pd = api.cast("IPartDoc", m)
            data["material"] = _material(m)
            bodies = []
            for b in (pd.GetBodies2(0, True) or []):
                b = api.cast("IBody2", b)
                try:
                    mat = (b.GetMaterialIdName() or "").rpartition("|")[2] or None
                except Exception:  # noqa: BLE001
                    mat = None
                bodies.append({"name": b.Name, "material": mat})
            data["bodies"] = bodies
            data["mass_properties"] = _mass(ext)
            data["bbox_mm"] = _bbox(pd.GetPartBox(True))
        elif info["type"] == "assembly":
            a = api.cast("IAssemblyDoc", m)
            data["component_count"] = {"top_level": int(a.GetComponentCount(True)), "total": int(a.GetComponentCount(False))}
            data["mass_properties"] = _mass(ext)
            data["bbox_mm"] = _bbox(a.GetBox(0))
    return data


# ---------------------------------------------------------------- bom

def traverse(root_comp, level: int = 1) -> list[dict]:
    """컴포넌트 트리를 평평한 레코드 목록으로."""
    out = []
    for c in (root_comp.GetChildren() or []):
        c = api.cast("IComponent2", c)
        path = c.GetPathName() or ""
        title = os.path.basename(path) if path else c.Name2
        rec = dict(level=level, path=path, title=title, config=c.ReferencedConfiguration or "",
                   doc_type="assembly" if path.lower().endswith(".sldasm") else "part",
                   suppression=int(c.GetSuppression2()), excluded=bool(c.ExcludeFromBOM), virtual=bool(c.IsVirtual),
                   component=c.Name2, _comp=c)
        out.append(rec)
        if rec["doc_type"] == "assembly" and rec["suppression"] != 0:
            out.extend(traverse(c, level + 1))
    return out


def _state(rec) -> str:
    if rec["virtual"]:
        return "virtual"
    return SUPPRESSION.get(rec["suppression"], "unavailable")


def _row_key(r) -> tuple:
    return (normalize_path(r["path"]) or r["title"], r["config"])


def aggregate(records: list[dict], structure: str) -> list[dict]:
    def row(r):
        return {"part_number": os.path.splitext(r["title"])[0], "file": r["path"], "configuration": r["config"],
                "type": r["doc_type"], "instances": 0 if r["suppression"] == 0 else 1,
                "state": _state(r), "excluded_from_bom": r["excluded"], "level": r["level"]}

    if structure == "indented":
        return [row(r) for r in records]
    pool = [r for r in records if r["level"] == 1] if structure == "top_level" else [r for r in records if r["doc_type"] == "part"]
    merged: dict = {}
    for r in pool:
        k = _row_key(r)
        if k not in merged:
            merged[k] = row(r)
            merged[k].pop("level")
        else:
            merged[k]["instances"] += 0 if r["suppression"] == 0 else 1
    return list(merged.values())


def bom(sel: DocSelector, structure: str = "top_level", resolve_lightweight: bool = False, include_mass: bool = True) -> dict:
    if structure not in ("top_level", "parts_only", "indented"):
        raise SwError("INTERNAL", f"structure 값이 잘못됨: {structure} (top_level|parts_only|indented)")
    app = api.get_app()
    m, info = resolve(app, sel)
    if info["type"] != "assembly":
        raise SwError("DOC_NOT_FOUND", "sw_bom은 어셈블리에만 사용할 수 있습니다")
    with with_configuration(m, sel.configuration):
        cm = api.cast("IConfigurationManager", m.ConfigurationManager)
        root = api.cast("IComponent2", api.cast("IConfiguration", cm.ActiveConfiguration).GetRootComponent3(True))
        records = traverse(root)
        if resolve_lightweight:
            for r in records:
                if r["suppression"] == 1:
                    r["_comp"].SetSuppression2(2)
                    r["suppression"] = 2
        rows = aggregate(records, structure)
        first_comp: dict = {}
        for r in records:
            first_comp.setdefault(_row_key(r), r["_comp"])
        cache: dict = {}
        for row in rows:
            comp = first_comp.get((normalize_path(row["file"]) or row["part_number"], row["configuration"]))
            if comp is None:
                comp = first_comp.get((normalize_path(row["file"]) or row["file"], row["configuration"]))
            md = api.cast("IModelDoc2", comp.GetModelDoc2()) if comp is not None else None
            if md is None:
                st = row["state"] if row["state"] != "ok" else "unavailable"
                row.update(material=state_value(None, st), spec=None, qty_property=None, qty_mismatch=None, bbox_mm=None, mass_kg=None)
                continue
            ck = (normalize_path(row["file"]), row["configuration"])
            if ck not in cache:
                props = {**custom_properties(md, ""), **custom_properties(md, row["configuration"])}
                ext = api.cast("IModelDocExtension", md.Extension)
                cache[ck] = {
                    "material": _material(md) if row["type"] == "part" else state_value(None, "unavailable"),
                    "spec": (props.get("SPEC") or {}).get("resolved"),
                    "qty_property": (props.get("QT'Y") or {}).get("resolved"),
                    "bbox_mm": _bbox(api.cast("IPartDoc", md).GetPartBox(True)) if row["type"] == "part" else None,
                    "mass_kg": (_mass(ext) or {}).get("mass_kg") if include_mass else None,
                }
            row.update(cache[ck])
            qp = row["qty_property"]
            try:
                row["qty_mismatch"] = (int(float(qp)) != row["instances"]) if qp not in (None, "") else None
            except ValueError:
                row["qty_mismatch"] = None
    return {"assembly": info["title"], "configuration": api.active_config_name(m), "structure": structure,
            "component_total": len(records), "rows": rows}


# ---------------------------------------------------------------- snapshot

def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot(sel: DocSelector, views: list[str], out_dir: str, width: int = 1600, height: int = 900) -> dict:
    bad = [v for v in views if v not in VIEW_IDS]
    if bad:
        raise SwError("INTERNAL", f"알 수 없는 뷰: {bad} (가능: {list(VIEW_IDS)})")
    os.makedirs(out_dir, exist_ok=True)
    app = api.get_app()
    m, info = resolve(app, sel)
    prev_active = api.cast("IModelDoc2", app.ActiveDoc)
    api.activate(app, m)
    mv = api.cast("IModelView", m.ActiveView)
    saved_orient, saved_scale, saved_trans = mv.Orientation3, mv.Scale2, mv.Translation3
    files = []
    stem = re.sub(r"[^\w\-]+", "_", os.path.splitext(info["title"])[0])
    try:
        for v in views:
            m.ShowNamedView2("", VIEW_IDS[v])
            m.ViewZoomtofit2()
            path = os.path.join(out_dir, f"{stem}_{v}.bmp")
            if not m.SaveBMP(path, width, height):
                raise SwError("COM_ERROR", f"SaveBMP 실패: {path}")
            files.append({"view": v, "path": path, "sha256": _sha256(path), "bytes": os.path.getsize(path)})
    finally:
        mv.Orientation3 = saved_orient
        mv.Scale2 = saved_scale
        mv.Translation3 = saved_trans
        m.GraphicsRedraw2()
        if prev_active is not None and prev_active.GetTitle() != m.GetTitle():
            api.activate(app, prev_active)
    return {"document": info["title"], "files": files}


# ---------------------------------------------------------------- audit

def audit_rules(rows: list[dict], required_props: list[str]) -> dict:
    missing, qty, copies, nomat, unresolved = [], [], [], [], []
    for r in rows:
        props = r.get("props") or {}
        miss = [p for p in required_props if not str(props.get(p) or "").strip()] if r["state"] == "ok" else []
        if miss:
            missing.append({"part_number": r["part_number"], "missing": miss})
        if r.get("qty_mismatch"):
            qty.append({"part_number": r["part_number"], "instances": r["instances"], "qty_property": r["qty_property"]})
        f = r.get("file") or ""
        if "복사본" in f or " - copy" in f.lower():
            copies.append(f)
        if (r.get("material") or {}).get("state") == "not_assigned":
            nomat.append(r["part_number"])
        if r["state"] not in ("ok", "virtual"):
            unresolved.append({"part_number": r["part_number"], "state": r["state"]})
    issues = len(missing) + len(qty) + len(copies) + len(nomat) + len(unresolved)
    return {"missing_properties": missing, "qty_mismatch": qty, "copy_named_files": copies,
            "material_not_assigned": nomat, "not_resolved": unresolved, "counts": {"rows": len(rows), "issues": issues}}


def audit(sel: DocSelector, required_props: list[str] | None = None, interference: bool = False,
          max_components: int = 200, timeout_s: int = 60) -> dict:
    required_props = required_props or ["SPEC", "Material", "QT'Y", "DATE"]
    b = bom(sel, "parts_only", include_mass=False)
    if b["component_total"] > max_components:
        raise SwError("BUSY", f"컴포넌트 {b['component_total']}개 > max_components {max_components}")
    app = api.get_app()
    m, info = resolve(app, sel)
    by_path = {normalize_path(d["path"]): d for d in api.list_docs(app, with_raw=True, light=True) if d["path"]}
    for r in b["rows"]:
        r["props"] = {}
        hit = by_path.get(normalize_path(r["file"])) if r["state"] == "ok" and r["file"] else None
        if hit is not None:
            md = api.find_doc(app, hit)
            p = {**custom_properties(md, ""), **custom_properties(md, r["configuration"])}
            r["props"] = {k: v["resolved"] for k, v in p.items()}
    result = audit_rules(b["rows"], required_props)
    result["assembly"] = info["title"]
    result["warnings"] = []
    if interference:
        t0 = time.time()
        a = api.cast("IAssemblyDoc", m)
        try:
            idm = api.cast("IInterferenceDetectionMgr", a.InterferenceDetectionManager)
            idm.TreatCoincidenceAsInterference = False
            idm.IncludeMultibodyPartInterferences = True
            pairs = []
            for it in (idm.GetInterferences() or []):
                it = api.cast("IInterference", it)
                comps = [api.cast("IComponent2", c).Name2 for c in (it.Components or [])]
                pairs.append({"components": comps, "volume_mm3": round(it.Volume * 1e9, 3)})
                if time.time() - t0 > timeout_s:
                    result["warnings"].append("간섭 검사 시간 초과 — 일부만 표시")
                    break
            idm.Done()
            result["interferences"] = pairs
        except Exception as e:  # noqa: BLE001
            result["interferences"] = None
            result["warnings"].append(f"간섭 검사 실패: {type(e).__name__}: {e}")
    return result
