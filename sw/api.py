"""SolidWorks COM 연결·캐스팅 공통 헬퍼. 반드시 ComWorker 스레드 안에서 호출한다."""
from __future__ import annotations

import logging
import os
from typing import Iterator

from .models import SwError
from .selectors import normalize_path

log = logging.getLogger("sw.api")
TLB = ("{83A33D31-27C5-11CE-BFD4-00400513BB57}", 0, 32, 0)
DOC_TYPES = {1: "part", 2: "assembly", 3: "drawing"}
_mod = None


def mod():
    global _mod
    if _mod is None:
        from win32com.client import gencache

        _mod = gencache.EnsureModule(*TLB)
        if _mod is None:
            raise SwError("INTERNAL", "SolidWorks 타입 라이브러리(sldworks.tlb) 모듈을 만들지 못했습니다")
    return _mod


def cast(iface_name: str, obj):
    """동적 Dispatch 반환값을 조기 바인딩 인터페이스로 감싼다. None은 None."""
    if obj is None:
        return None
    return getattr(mod(), iface_name)(getattr(obj, "_oleobj_", obj))


def dyn(obj, name: str = "SldWorks"):
    """by-ref out 인자가 있는 메서드용 동적 프록시 (makepy 프록시는 [out] long에 실패)."""
    import win32com.client.dynamic as d

    return d.DumbDispatch(getattr(obj, "_oleobj_", obj), name)


def byref_int():
    import pythoncom
    from win32com.client import VARIANT

    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def empty_dispatch():
    """SaveAs3의 ExportData/AdvancedSaveAsOptions처럼 '객체 없음'을 뜻하는 인자. None을 넘기면 형식 오류."""
    import pythoncom
    from win32com.client import VARIANT

    return VARIANT(pythoncom.VT_DISPATCH, None)


_APP_OVERRIDE = None


def set_app_override(app) -> None:
    """백그라운드(비가시) 인스턴스가 켜져 있으면 모든 도구가 그 인스턴스를 쓴다. None이면 사용자 세션(ROT)."""
    global _APP_OVERRIDE
    _APP_OVERRIDE = app


def get_app():
    import pythoncom
    import win32com.client

    if _APP_OVERRIDE is not None:
        return _APP_OVERRIDE
    try:
        raw = win32com.client.GetActiveObject("SldWorks.Application")
    except pythoncom.com_error as e:
        raise SwError("SW_NOT_RUNNING", "실행 중인 SolidWorks를 찾지 못했습니다. SolidWorks를 먼저 여세요") from e
    return cast("ISldWorks", raw)


def g(obj, name: str):
    """동적 Dispatch에서 인자 없는 메서드/속성을 읽는다 (SolidWorks는 둘을 구분 못 함).

    조기 바인딩 cast()는 객체당 첫 QueryInterface가 ~27ms라 수백 개 문서를 열거할 때 쓰면 안 된다.
    동적 접근은 0.3ms."""
    v = getattr(obj, name)
    return v() if callable(v) else v


def raw_docs(app) -> list:
    """열린 문서 전부를 동적 Dispatch로 (1회 호출 + 문서당 0ms)."""
    import win32com.client

    # GetDocuments()가 이미 CDispatch 래퍼를 주면 다시 Dispatch()하지 않는다 — 재래핑은 문서당 COM 호출을 유발(바쁠 때 348개 19초)
    return [r if hasattr(r, "_oleobj_") else win32com.client.Dispatch(r) for r in (app.GetDocuments() or [])]


def iter_docs(app) -> Iterator:
    """조기 바인딩 IModelDoc2 순회. 문서당 ~27ms — 소수 문서만 필요할 때 쓰고, 목록 작성은 list_docs."""
    for r in (app.GetDocuments() or []):
        yield cast("IModelDoc2", r)


def active_config_name(m) -> str:
    cm = cast("IConfigurationManager", m.ConfigurationManager)
    cfg = cast("IConfiguration", cm.ActiveConfiguration) if cm else None
    return cfg.Name if cfg else ""


def doc_title(m, path: str | None = None) -> str:
    if path is None:
        path = g(m, "GetPathName") or ""
    return os.path.basename(path) if path else (g(m, "GetTitle") or "")


def doc_key(m) -> str:
    path = g(m, "GetPathName") or ""
    return normalize_path(path) or doc_title(m, path)


def _active_key(app) -> str:
    a = app.ActiveDoc
    return doc_key(a) if a else ""


def doc_info(app, m, active_key: str | None = None, with_config: bool = True, light: bool = False) -> dict:
    """문서 정보. m은 조기 바인딩이든 동적이든 상관없음(g()로 읽음).
    with_config=False면 구성 조회(ConfigurationManager, COM 3회)를 건너뛴다.
    light=True면 dirty/read_only(COM 2회)도 건너뛴다 — 문서 찾기용 열거에 사용."""
    path = g(m, "GetPathName") or ""
    title = doc_title(m, path)
    if active_key is None:
        active_key = _active_key(app)
    key = normalize_path(path) or title
    t = int(g(m, "GetType"))
    return {
        "document_id": key,
        "title": title,
        "path": path,
        "type": DOC_TYPES.get(t, str(t)),
        "configuration": (active_config_name(cast("IModelDoc2", m)) if t != 3 else "") if with_config else None,
        "dirty": None if light else bool(g(m, "GetSaveFlag")),
        "read_only": None if light else bool(g(m, "IsOpenedReadOnly")),
        "active": key == active_key,
        "virtual": ("^" in title) or (path == "" and t != 3),
    }


def list_docs(app, with_config: bool = False, with_raw: bool = False, light: bool = False) -> list[dict]:
    """열린 문서 목록 (동적 접근). with_raw=True면 각 항목에 '_raw'(동적 Dispatch) 포함.
    light=True면 문서당 COM 2회(경로·타입)만 — 찾기용. SolidWorks가 바쁘면 호출당 수십 ms라 호출 수가 곧 시간."""
    active_key = _active_key(app)
    out = []
    for r in raw_docs(app):
        d = doc_info(app, r, active_key, with_config, light)
        if not with_config and d["active"] and d["type"] != "drawing":
            d["configuration"] = active_config_name(cast("IModelDoc2", r))  # 활성 문서만 구성 채움
        if with_raw:
            d["_raw"] = r
        out.append(d)
    return out


def find_doc(app, sel_info: dict):
    """list_docs 항목(_raw 포함)에서 조기 바인딩 IModelDoc2를 만든다."""
    return cast("IModelDoc2", sel_info["_raw"])


def activate(app, m):
    """문서를 활성화. ActivateDoc3의 by-ref Errors 때문에 dyn 사용."""
    title = m.GetTitle()
    err = byref_int()
    dyn(app).ActivateDoc3(title, False, 0, err)
    a = cast("IModelDoc2", app.ActiveDoc)
    if a is None or a.GetTitle() != title:
        raise SwError("COM_ERROR", f"문서를 활성화하지 못했습니다: {title}")
    return a
