"""marydworks-mcp: SolidWorks MCP 서버. 도구 등록만 하고 실제 작업은 sw/ 패키지에 있다."""
from __future__ import annotations

import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Optional

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from sw import read, write
from sw.com_worker import worker
from sw.models import DocSelector, SwError, envelope

ROOT = Path(__file__).resolve().parent
(ROOT / "journal").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger().addHandler(logging.FileHandler(ROOT / "journal" / "server.log", encoding="utf-8"))
log = logging.getLogger("sw.server")

server = MCPServer("solidworks")


def _call(fn, *args, write: bool = False, timeout: float = 120.0, **kw) -> Any:
    try:
        return worker().run(fn, *args, write=write, timeout=timeout, **kw)
    except SwError as e:
        msg = f"{e.code}: {e.message}"
        details = dict(e.details)
        if getattr(e, "op_id", None):
            details.setdefault("op_id", e.op_id)  # sw_status.operations에서 같은 id로 찾을 수 있다
        if details:
            msg += "\n" + json.dumps(details, ensure_ascii=False)
        raise ToolError(msg) from e
    except ToolError:
        raise
    except Exception as e:  # noqa: BLE001
        op = getattr(e, "op_id", None) or uuid.uuid4().hex[:12]
        log.exception("INTERNAL operation_id=%s", op)
        raise ToolError(f"INTERNAL: 내부 오류 (operation_id={op}, {type(e).__name__}: {e})") from e


def _sel(doc: Optional[dict]) -> DocSelector:
    return DocSelector(**(doc or {"active": True}))


@server.tool(
    name="sw_status",
    description="SolidWorks 연결 상태·버전·열린 문서 목록(수정됨/읽기전용/활성)·최상위 어셈블리·Simulation 상태·최근 operation(timeout 후 실행 중인 쓰기 포함). SolidWorks를 실행하지는 않음.",
)
def sw_status() -> dict:
    return envelope(_call(read.status))


@server.tool(
    name="sw_summary",
    description="파트/어셈블리 사양 요약: 경로·구성·사용자속성(파일+구성)·재질·바디·질량·외형치수(근사)·피처 수. doc 생략 시 활성 문서. doc={active|path|title, configuration?}.",
)
def sw_summary(doc: Optional[dict] = None) -> dict:
    return envelope(_call(read.summary, _sel(doc)))


@server.tool(
    name="sw_bom",
    description="어셈블리 부품 집계. structure: top_level(직계만)|parts_only(모든 파트 평면)|indented(계층). instances=실제 개수, qty_property=QT'Y 속성값, qty_mismatch로 불일치 표시. lightweight는 resolve_lightweight=true일 때만 해석.",
)
def sw_bom(doc: Optional[dict] = None, structure: str = "top_level", resolve_lightweight: bool = False, include_mass: bool = True) -> dict:
    # resolve_lightweight=true는 경량 컴포넌트를 해석해 어셈블리를 수정 상태로 만든다 → 쓰기로 취급(재시도 없음, 효과 보고)
    data = _call(read.bom, _sel(doc), structure, resolve_lightweight, include_mass, write=resolve_lightweight, timeout=300)
    eff = {"changed_in_memory": True, "note": "resolve_lightweight로 경량 컴포넌트가 해석되어 어셈블리가 수정 상태가 될 수 있음"} if resolve_lightweight else {}
    return envelope(data, effects=eff)


@server.tool(
    name="sw_snapshot",
    description="문서를 iso/front/top/right/back/left/bottom 뷰로 캡처해 BMP 저장, 경로·sha256 반환. 시점·활성 문서 복원. views 기본 [iso,front,top,right].",
)
def sw_snapshot(doc: Optional[dict] = None, views: Optional[list[str]] = None, out_dir: Optional[str] = None) -> dict:
    out_dir = out_dir or str(ROOT / "journal" / "snapshots")
    data = _call(read.snapshot, _sel(doc), views or ["iso", "front", "top", "right"], out_dir, write=True, timeout=300)
    return envelope(data, effects={"files_created": [f["path"] for f in data["files"]]})


@server.tool(
    name="sw_audit",
    description="어셈블리 점검: 필수 속성 누락(required_props 기본 SPEC/Material/QT'Y/DATE), 실제 수량 vs QT'Y 불일치, '복사본' 파일 참조, 재질 미지정, lightweight/억제, interference=true면 간섭 쌍.",
)
def sw_audit(doc: Optional[dict] = None, required_props: Optional[list[str]] = None, interference: bool = False,
             max_components: int = 200, timeout_s: int = 60) -> dict:
    data = _call(read.audit, _sel(doc), required_props, interference, max_components, timeout_s, timeout=timeout_s + 120)
    return envelope(data, warnings=data.pop("warnings", []))


# ---------------------------------------------------------------- 쓰기 도구 (dry_run → plan_id → sw_save)


def _write_effects(dry_run: bool, data: dict) -> dict:
    if dry_run:
        return {}
    d = data.get("dirty_documents", [])
    return {"changed_in_memory": True, "dirty_documents": d, "pending_saves": d}


@server.tool(
    name="sw_set_properties",
    description="사용자 속성 변경. dry_run=true(기본)는 plan_id와 변경 전/후만 반환; dry_run=false+plan_id로 적용(메모리, 저장은 sw_save). doc 하나 또는 docs[] 여러 개, scope file|configuration. 값 특수어: $today, $instances(assembly 지정 시 실제 개수), $expr:수식. 수식 속성은 $expr: 없이는 보존.",
)
def sw_set_properties(props: dict, doc: Optional[dict] = None, docs: Optional[list[dict]] = None, scope: str = "file",
                      assembly: Optional[dict] = None, dry_run: bool = True, plan_id: Optional[str] = None) -> dict:
    sels = [DocSelector(**d) for d in docs] if docs else [_sel(doc)]
    data = _call(write.set_properties, sels, scope, props, DocSelector(**assembly) if assembly else None, dry_run, plan_id,
                 write=True, timeout=300)
    return envelope(data, warnings=data.pop("warnings", []), effects=_write_effects(dry_run, data))


@server.tool(
    name="sw_save",
    description="저장. change_set_id(적용된 변경의 문서를 파트→어셈블리→도면 순서로) 또는 doc 하나. 저장된 적 없는 문서는 out_path 필요(기존 파일 덮어쓰지 않음). only_under=[폴더…]면 그 밖의 문서는 저장 거부(공용 라이브러리 보호). dry_run=true면 저장 목록만.",
)
def sw_save(change_set_id: Optional[str] = None, doc: Optional[dict] = None, out_path: Optional[str] = None, dry_run: bool = True,
            only_under: Optional[list[str]] = None) -> dict:
    data = _call(write.save, change_set_id, DocSelector(**doc) if doc else None, out_path, dry_run, only_under, write=True, timeout=600)
    eff = {} if dry_run else {"files_created": [s["path"] for s in data["saved"] if out_path]}
    return envelope(data, effects=eff)


@server.tool(
    name="sw_delete_components",
    description="어셈블리 직계 컴포넌트 삭제(메모리). names[] 정확 일치 또는 path_contains 경로 필터. dry_run=true(기본)가 삭제 대상 전수 목록과 plan_id를 반환하고, dry_run=false+plan_id로만 실행. 저장은 별도 sw_save.",
)
def sw_delete_components(assembly: dict, names: Optional[list[str]] = None, path_contains: Optional[str] = None,
                         dry_run: bool = True, plan_id: Optional[str] = None) -> dict:
    data = _call(write.delete_components, DocSelector(**assembly), names or [], path_contains, dry_run, plan_id, write=True, timeout=600)
    return envelope(data, effects=_write_effects(dry_run, data))


@server.tool(
    name="sw_export",
    description="내보내기: step/stl/png(파트·어셈블리), pdf/dxf(도면). 기존 파일은 overwrite=true일 때만. 생성 후 크기·sha256 검증.",
)
def sw_export(out_path: str, format: str, doc: Optional[dict] = None, overwrite: bool = False) -> dict:
    data = _call(write.export, _sel(doc), format, out_path, overwrite, write=True, timeout=600)
    eff = {"files_created": [data["path"]]}
    if data.get("backup"):
        eff["backup"] = data["backup"]
    return envelope(data, effects=eff)


@server.tool(
    name="sw_rename_document",
    description="어셈블리 안의 부품 파일 이름 변경(RenameDocument). dry_run으로 영향(열린 참조 문서·기존 파일 충돌·백업)을 먼저 보고, 적용 후 sw_save(change_set_id)로 부모 어셈블리를 저장해야 파일명이 바뀜. 닫힌 문서 참조는 update_unopened_references+search_folders. sync_properties로 RELATION NO./TITLE 동시 갱신.",
)
def sw_rename_document(target: dict, parent_assembly: dict, new_name: str, update_unopened_references: bool = False,
                       search_folders: Optional[list[str]] = None, sync_properties: Optional[dict] = None,
                       move_existing: bool = False, dry_run: bool = True, plan_id: Optional[str] = None) -> dict:
    data = _call(write.rename_document, DocSelector(**target), DocSelector(**parent_assembly), new_name, update_unopened_references,
                 search_folders or [], sync_properties, move_existing, dry_run, plan_id, write=True, timeout=600)
    return envelope(data, effects=_write_effects(dry_run, data))


@server.tool(
    name="sw_add_component",
    description="어셈블리에 부품 삽입(position_mm) + 단순 메이트(coincident/concentric/distance; 엔티티는 {type,xyz_mm,name?}). 실패 시 rollback=delete_component(기본). dry_run→plan_id→적용, 저장은 sw_save.",
)
def sw_add_component(assembly: dict, part_path: str, position_mm: list[float], mates: Optional[list[dict]] = None,
                     rollback: str = "delete_component", dry_run: bool = True, plan_id: Optional[str] = None) -> dict:
    data = _call(write.add_component, DocSelector(**assembly), part_path, position_mm, mates or [], rollback, dry_run, plan_id,
                 write=True, timeout=600)
    return envelope(data, effects=_write_effects(dry_run, data))


@server.tool(
    name="sw_create_drawing",
    description="모델에서 도면 생성(메모리): 템플릿 기본 도면.DRWDOT, views front/top/right/iso, 어셈블리면 BOM 표, auto_dimension 옵션. 저장은 sw_save(doc, out_path), PDF는 sw_export. 치수 배치는 사람이 정리.",
)
def sw_create_drawing(doc: Optional[dict] = None, template: Optional[str] = None, views: Optional[list[str]] = None,
                      bom: bool = True, auto_dimension: bool = False, dry_run: bool = True, plan_id: Optional[str] = None) -> dict:
    data = _call(write.create_drawing, _sel(doc), template, views or ["front", "top", "right", "iso"], bom, auto_dimension, dry_run, plan_id,
                 write=True, timeout=600)
    return envelope(data, effects=_write_effects(dry_run, data))


@server.tool(
    name="sw_background",
    description="비가시(백그라운드) SolidWorks 인스턴스. action=start(paths[]: 열 파일; 사용자 창에 열린 파일은 거부)면 창 없는 SolidWorks를 띄워 문서를 열고, 이후 모든 sw_* 도구가 그 인스턴스를 대상으로 동작. status로 확인, stop(discard_changes)으로 종료. 사용자 화면을 전혀 건드리지 않는 일괄 작업용.",
)
def sw_background(action: str, paths: Optional[list[str]] = None, discard_changes: bool = False) -> dict:
    from sw import background

    if action == "start":
        data = _call(background.start, paths or [], write=True, timeout=400)
    elif action == "stop":
        data = _call(background.stop, discard_changes, write=True, timeout=300)
    elif action == "status":
        data = _call(background.status)
    else:
        raise ToolError("INTERNAL: action은 start|stop|status")
    return envelope(data)


if __name__ == "__main__":
    server.run(transport="stdio")
