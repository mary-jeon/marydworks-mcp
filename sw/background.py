"""백그라운드(비가시) SolidWorks 인스턴스.

사용자 창을 건드리지 않고 일괄 작업을 하기 위해 SolidWorks 프로세스를 하나 더 띄우고(Visible=False)
그 안에서 문서를 연다. 켜져 있는 동안 모든 도구는 이 인스턴스를 대상으로 동작한다(api.set_app_override).

규칙
- 대상 파일이 사용자 세션에 열려 있으면 거부한다(같은 파일을 두 인스턴스가 열면 충돌·읽기전용).
- 끝나면 stop(): 수정된 문서가 있으면 discard_changes=True일 때만 버리고, 아니면 거부.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

from . import api
from .models import SwError
from .selectors import normalize_path

log = logging.getLogger("sw.background")
SW_DOC_TYPES = {".sldprt": 1, ".sldasm": 2, ".slddrw": 3}
SW_OPEN_SILENT = 1  # swOpenDocOptions_Silent

_STATE: dict = {"app": None, "pid": None, "started": None, "paths": []}


def _sw_pids() -> set[int]:
    """현재 실행 중인 SLDWORKS.exe PID 집합 (tasklist 대신 PowerShell — 콘솔 cp949 문제 회피)."""
    import subprocess

    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-Process SLDWORKS -ErrorAction SilentlyContinue | ForEach-Object { $_.Id }) -join ','"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    return {int(x) for x in out.split(",") if x.strip().isdigit()}


def _user_session_open_paths() -> set[str]:
    """사용자 세션(ROT)에 열린 문서 경로. SolidWorks가 없으면 빈 집합."""
    import pythoncom
    import win32com.client

    try:
        raw = win32com.client.GetActiveObject("SldWorks.Application")
    except pythoncom.com_error:
        return set()
    user_app = api.cast("ISldWorks", raw)
    if _STATE["pid"] and int(user_app.GetProcessID()) == _STATE["pid"]:
        return set()  # ROT가 백그라운드 인스턴스를 가리키는 경우
    return {normalize_path(d["path"]) for d in api.list_docs(user_app, with_raw=False, light=True) if d["path"]}


def status() -> dict:
    app = _STATE["app"]
    if app is None:
        return {"active": False}
    try:
        docs = api.list_docs(app, with_raw=False)
    except Exception as e:  # noqa: BLE001
        return {"active": True, "pid": _STATE["pid"], "error": f"{type(e).__name__}: {e}"}
    return {"active": True, "pid": _STATE["pid"], "started": _STATE["started"], "opened_paths": _STATE["paths"],
            "documents": docs, "dirty_documents": [d["title"] for d in docs if d["dirty"]]}


def start(paths: list[str], timeout_s: float = 180.0) -> dict:
    if _STATE["app"] is not None:
        raise SwError("BUSY", "백그라운드 인스턴스가 이미 켜져 있습니다. sw_background(stop) 후 다시")
    paths = [os.path.abspath(p) for p in (paths or [])]
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        raise SwError("DOC_NOT_FOUND", f"파일이 없습니다: {missing}")
    bad_ext = [p for p in paths if os.path.splitext(p)[1].lower() not in SW_DOC_TYPES]
    if bad_ext:
        raise SwError("INTERNAL", f"SolidWorks 문서가 아닙니다: {bad_ext}")
    conflict = sorted(p for p in paths if normalize_path(p) in _user_session_open_paths())
    if conflict:
        raise SwError("DOC_OPEN_IN_USER_SESSION",
                      "사용자 SolidWorks 창에 열려 있는 파일은 백그라운드에서 열 수 없습니다. 먼저 닫아주세요",
                      {"conflict": conflict})

    import pythoncom
    import win32com.client

    # ⚠ 주의: SolidWorks가 이미 실행 중이면 DispatchEx/CoCreateInstance는 새 프로세스를 만들지 않고
    # 실행 중인 사용자 인스턴스를 돌려준다. 그 상태에서 Visible=False·CloseAllDocuments·ExitApp을 부르면 사용자 세션이
    # 통째로 종료된다. 따라서 백그라운드 모드는 SolidWorks가 하나도 떠 있지 않을 때만 시작하고, PID를 대조해 새 프로세스임을
    # 확인한 뒤에만 Visible=False를 건드린다.
    before = _sw_pids()
    if before:
        raise SwError("USER_SESSION_RUNNING",
                      "SolidWorks가 실행 중이라 백그라운드 인스턴스를 만들 수 없습니다(같은 인스턴스가 잡혀 사용자 세션이 닫힘). "
                      "SolidWorks를 완전히 종료한 뒤 다시 시도하거나, 사용자 창에서 그대로 작업하세요", {"running_pids": sorted(before)})
    t0 = time.time()
    raw = win32com.client.DispatchEx("SldWorks.Application")
    app = api.cast("ISldWorks", raw)
    pid = int(app.GetProcessID())
    if pid in before or pid not in _sw_pids():
        raise SwError("INTERNAL", f"새 SolidWorks 프로세스를 확인하지 못했습니다 (pid {pid}). 아무것도 변경하지 않았습니다")
    app.Visible = False
    try:
        app.UserControl = False
    except Exception:  # noqa: BLE001
        pass
    _STATE.update(app=app, pid=pid, started=time.strftime("%Y-%m-%d %H:%M:%S"), paths=[])
    opened, errors = [], []
    for p in paths:
        doc_type = SW_DOC_TYPES[os.path.splitext(p)[1].lower()]
        err, warn = api.byref_int(), api.byref_int()
        m = api.dyn(app).OpenDoc6(p, doc_type, SW_OPEN_SILENT, "", err, warn)
        e = int(err.value or 0)
        if m is None or e:
            errors.append({"path": p, "errors": e, "warnings": int(warn.value or 0)})
        else:
            opened.append(p)
        if time.time() - t0 > timeout_s:
            break
    _STATE["paths"] = opened
    api.set_app_override(app)
    if errors and not opened:
        stop(discard_changes=True)
        raise SwError("COM_ERROR", "백그라운드에서 문서를 열지 못했습니다", {"errors": errors})
    return {"pid": pid, "opened": opened, "errors": errors, "elapsed_s": round(time.time() - t0, 1),
            "note": "이제 모든 sw_* 도구는 이 인스턴스를 대상으로 동작합니다. 끝나면 sw_background(action='stop')"}


def stop(discard_changes: bool = False) -> dict:
    app = _STATE["app"]
    if app is None:
        return {"stopped": False, "note": "백그라운드 인스턴스가 없습니다"}
    dirty = []
    try:
        dirty = [d["title"] for d in api.list_docs(app, with_raw=False) if d["dirty"]]
    except Exception as e:  # noqa: BLE001
        log.warning("background status failed: %s", e)
    if dirty and not discard_changes:
        raise SwError("PLAN_STALE", "저장 안 된 문서가 있습니다. sw_save로 저장하거나 discard_changes=true로 버리세요",
                      {"dirty": dirty})
    api.set_app_override(None)
    pid = _STATE["pid"]
    try:
        # 우리가 만든 프로세스일 때만 종료한다 (PID 재확인)
        if pid is None or int(app.GetProcessID()) != pid:
            raise SwError("INTERNAL", "백그라운드 인스턴스 PID 불일치 — 종료하지 않습니다")
        app.CloseAllDocuments(True)
        app.ExitApp()
    except Exception as e:  # noqa: BLE001
        log.warning("ExitApp failed: %s", e)
    _STATE.update(app=None, pid=None, started=None, paths=[])
    return {"stopped": True, "pid": pid, "discarded": dirty}
