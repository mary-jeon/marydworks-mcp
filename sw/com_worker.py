"""SolidWorks COM 호출 직렬화 + operation 상태 기록.

모든 COM 호출은 STA 스레드 1개에서 순서대로 실행한다. 호출자가 timeout으로 포기해도 이미 시작한 COM 작업은
중단할 수 없다. 그래서 작업(operation)마다 상태를 기록하고, 결과가 확인되지 않은 쓰기 작업이 남아 있는 동안은
새 쓰기를 받지 않는다 — 같은 삽입·삭제·저장을 모르고 두 번 실행하지 않기 위해서다 (2026-09-07 검토 FIX-06).
"""
from __future__ import annotations

import ctypes
import json
import logging
import queue
import sys
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .models import SwError

log = logging.getLogger("sw.com")
RPC_E_CALL_REJECTED = -2147418111  # 0x80010001
RPC_E_SERVERCALL_RETRYLATER = -2147417846  # 0x8001010A
MUTEX_NAME = "Global\\marydworks-mcp-com"
MAX_OPS = 200  # 메모리에 남기는 최근 operation 수. 파일(operations.jsonl)에는 전부 남는다.

# operation 상태 — queued → running → completed | failed.
# 호출자가 timeout으로 포기하면: 시작 전이면 cancelled(실행 안 함), 실행 중이면 timeout_running(결과 미확정) →
# 나중에 끝나면 completed_after_timeout(효과가 남아 있다) | failed_after_timeout.
QUEUED = "queued"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
TIMEOUT_RUNNING = "timeout_running"
COMPLETED_AFTER_TIMEOUT = "completed_after_timeout"
FAILED_AFTER_TIMEOUT = "failed_after_timeout"

_SUMMARY_KEYS = ("dry_run", "plan_id", "change_set_id", "dirty_documents", "saved", "path", "component", "mates_added",
                 "mate_failure", "deleted", "failed", "still_present", "drawing_title", "views_created", "files")


def is_busy_error(exc: BaseException) -> bool:
    hr = getattr(exc, "hresult", None)
    if hr is None and getattr(exc, "args", None):
        hr = exc.args[0] if isinstance(exc.args[0], int) else None
    return hr in (RPC_E_CALL_REJECTED, RPC_E_SERVERCALL_RETRYLATER)


def summarize_result(result: Any) -> Any:
    """operation 기록용 결과 요약. 문서 객체·긴 목록은 넣지 않는다."""
    if not isinstance(result, dict):
        return type(result).__name__
    out = {}
    for k in _SUMMARY_KEYS:
        if k not in result:
            continue
        v = result[k]
        if isinstance(v, list):
            v = [(x.get("title") or x.get("path") or x.get("name")) if isinstance(x, dict) else x for x in v][:50]
        elif isinstance(v, str) and len(v) > 300:
            v = v[:300] + "…"
        out[k] = v
    return out


def _error_text(exc: BaseException) -> str:
    if isinstance(exc, SwError):
        return f"{exc.code}: {exc.message}"
    return f"{type(exc).__name__}: {exc}"[:500]


class _NamedMutex:
    """프로세스 간 직렬화. Windows가 아니거나 생성 실패면 no-op."""

    def __init__(self, name: str = MUTEX_NAME):
        self.handle = None
        if sys.platform == "win32":
            k = ctypes.windll.kernel32
            self.handle = k.CreateMutexW(None, False, name) or None

    def acquire(self, timeout_s: float) -> bool:
        if not self.handle:
            return True
        rc = ctypes.windll.kernel32.WaitForSingleObject(self.handle, int(timeout_s * 1000))
        return rc in (0, 0x80)  # WAIT_OBJECT_0, WAIT_ABANDONED

    def release(self):
        if self.handle:
            ctypes.windll.kernel32.ReleaseMutex(self.handle)


@dataclass
class _Job:
    fn: Callable
    args: tuple
    kw: dict
    write: bool
    name: str = ""
    op_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    state: str = QUEUED
    queued_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    done: threading.Event = field(default_factory=threading.Event)
    result: Any = None
    exc: BaseException | None = None
    started: bool = False    # STA 스레드가 실행을 시작했는가
    cancelled: bool = False  # 호출자가 타임아웃으로 포기했는가 — 아직 시작 전이면 실행하지 않는다
    side_effects: dict = field(default_factory=dict)  # 실행 중 progress()로 남긴 부분 결과(삽입된 컴포넌트, 적용된 문서…)

    def record(self) -> dict:
        r = {"op_id": self.op_id, "name": self.name, "write": self.write, "state": self.state,
             "queued_at": self.queued_at, "started_at": self.started_at, "finished_at": self.finished_at,
             "side_effects": dict(self.side_effects)}
        if self.started_at and self.finished_at:
            r["duration_s"] = round(self.finished_at - self.started_at, 3)
        if self.exc is not None:
            r["error"] = _error_text(self.exc)
        if self.state in (COMPLETED, COMPLETED_AFTER_TIMEOUT):
            r["result"] = summarize_result(self.result)
        return r


_CURRENT = threading.local()  # STA 스레드에서 지금 실행 중인 _Job


def progress(**fields) -> None:
    """실행 중인 쓰기 함수가 부분 결과를 operation 기록에 남긴다 (예: progress(deleted=["A-1"])).
    타임아웃·예외로 끝나도 무엇이 이미 바뀌었는지 sw_status.operations에서 볼 수 있게 하기 위함.
    리스트 값은 누적, 그 외는 덮어쓴다. worker 스레드 밖에서 부르면 아무 일도 하지 않는다."""
    job = getattr(_CURRENT, "job", None)
    if job is None:
        return
    for k, v in fields.items():
        if isinstance(v, list) and isinstance(job.side_effects.get(k), list):
            job.side_effects[k].extend(v)
        else:
            job.side_effects[k] = list(v) if isinstance(v, list) else v


class ComWorker:
    """모든 COM 호출을 STA 스레드 1개에서 직렬 실행하고 operation 상태를 기록한다."""

    def __init__(self, init_com: bool = True, retry_delay: float = 0.5, max_retries: int = 10, mutex_timeout: float = 30.0,
                 log_path: Path | str | None = None):
        self._q: queue.Queue = queue.Queue()
        self._init_com = init_com
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.mutex_timeout = mutex_timeout
        self._mutex = _NamedMutex() if init_com else None
        self._ops: OrderedDict[str, _Job] = OrderedDict()
        self._ops_lock = threading.Lock()  # 상태 전이와 목록 변경을 직렬화 (run()의 timeout 판정 ↔ _exec의 시작/종료 경쟁)
        self.log_path = Path(log_path) if log_path else None
        self._t = threading.Thread(target=self._loop, name="sw-com-sta", daemon=True)
        self._t.start()

    # ------------------------------------------------------------ operation 기록

    def _set(self, job: _Job, state: str):
        """_ops_lock을 잡은 채로만 부른다."""
        job.state = state
        if self.log_path:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"t": time.time(), **job.record()}, ensure_ascii=False, default=str) + "\n")
            except OSError as e:  # 기록 실패가 COM 작업을 막아선 안 된다
                log.warning("operations.jsonl 기록 실패: %s", e)

    def _remember(self, job: _Job):
        with self._ops_lock:
            self._ops[job.op_id] = job
            while len(self._ops) > MAX_OPS:
                self._ops.popitem(last=False)

    def recent(self, n: int = 20) -> list[dict]:
        """최근 operation(최신 먼저)."""
        with self._ops_lock:
            jobs = list(self._ops.values())[-n:]
        return [j.record() for j in reversed(jobs)]

    def unresolved_writes(self) -> list[dict]:
        """호출자는 timeout으로 포기했지만 COM 안에서 아직 실행 중인 쓰기 작업 — 결과가 확정되기 전엔 새 쓰기를 받지 않는다."""
        with self._ops_lock:
            return [j.record() for j in self._ops.values() if j.write and j.state == TIMEOUT_RUNNING]

    def get(self, op_id: str) -> dict | None:
        with self._ops_lock:
            j = self._ops.get(op_id)
        return j.record() if j else None

    # ------------------------------------------------------------ 실행

    def _loop(self):
        if self._init_com:
            import pythoncom

            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        try:
            while True:
                job = self._q.get()
                if job is None:
                    break
                self._exec(job)
        finally:
            if self._init_com:
                import pythoncom

                pythoncom.CoUninitialize()

    def _exec(self, job: _Job):
        with self._ops_lock:
            if job.cancelled:
                # 호출자가 이미 BUSY로 포기한 작업. 특히 쓰기는 "실패"라고 보고된 뒤 몰래 적용되면 안 된다.
                job.exc = SwError("BUSY", "타임아웃으로 취소된 작업 — 실행하지 않음")
                if job.state != CANCELLED:
                    self._set(job, CANCELLED)
                job.done.set()
                return
            job.started = True
            job.started_at = time.time()
            self._set(job, RUNNING)
        _CURRENT.job = job
        try:
            if self._mutex and not self._mutex.acquire(self.mutex_timeout):
                raise SwError("BUSY", "다른 marydworks-mcp 프로세스가 SolidWorks를 사용 중입니다 (30초 대기 초과)")
            try:
                attempts = 1 if job.write else self.max_retries
                for i in range(attempts):
                    try:
                        job.result = job.fn(*job.args, **job.kw)
                        break
                    except BaseException as e:  # noqa: BLE001
                        if is_busy_error(e):
                            if i + 1 < attempts:
                                time.sleep(self.retry_delay)
                                continue
                            raise SwError("BUSY", "SolidWorks가 응답하지 않습니다 (대화상자가 열려 있는지 확인)") from e
                        raise
            finally:
                if self._mutex:
                    self._mutex.release()
        except BaseException as e:  # noqa: BLE001
            job.exc = e
        finally:
            _CURRENT.job = None
            with self._ops_lock:
                job.finished_at = time.time()
                if job.exc is None:
                    self._set(job, COMPLETED_AFTER_TIMEOUT if job.cancelled else COMPLETED)
                else:
                    self._set(job, FAILED_AFTER_TIMEOUT if job.cancelled else FAILED)
                if job.cancelled:
                    log.warning("timeout 후 완료된 작업 %s(op_id=%s): %s — 효과가 남아 있을 수 있음", job.name, job.op_id, job.state)
            job.done.set()

    def run(self, fn: Callable, *args, write: bool = False, timeout: float = 120.0, name: str | None = None, **kw) -> Any:
        job = _Job(fn, args, kw, write, name=name or getattr(fn, "__name__", type(fn).__name__))
        if write:
            pending = self.unresolved_writes()
            if pending:
                p = pending[0]
                raise SwError("BUSY", f"이전 쓰기 작업 {p['name']}(op_id={p['op_id']})이 타임아웃 후에도 아직 실행 중입니다. "
                                      "결과가 확인되기 전에는 새 쓰기를 받지 않습니다(중복 실행 방지) — sw_status의 operations로 확인",
                              {"unresolved_writes": pending})
        self._remember(job)
        self._q.put(job)
        if not job.done.wait(timeout):
            with self._ops_lock:
                job.cancelled = True
                if job.state == RUNNING:
                    self._set(job, TIMEOUT_RUNNING)
                elif job.state == QUEUED:
                    self._set(job, CANCELLED)
                started = job.started
            if started:
                # 이미 COM 안에서 도는 중이라 중단할 수 없다. 나중에 끝날 수 있음을 숨기지 않는다.
                what = "쓰기 작업" if job.write else "호출"
                raise SwError("BUSY", f"SolidWorks {what}이 {timeout:.0f}초 안에 끝나지 않았습니다. "
                                      "작업은 이미 시작되어 SolidWorks가 응답하면 그대로 완료될 수 있습니다 — "
                                      f"재시도 전에 sw_status.operations에서 op_id={job.op_id}의 상태를 확인하세요",
                              {"op_id": job.op_id, "state": job.state, "side_effects": dict(job.side_effects)})
            raise SwError("BUSY", f"SolidWorks가 {timeout:.0f}초 안에 응답하지 않아 대기열의 작업을 취소했습니다 (실행되지 않음)",
                          {"op_id": job.op_id, "state": job.state})
        if job.exc:
            try:
                job.exc.op_id = job.op_id  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                pass
            raise job.exc
        return job.result

    def close(self):
        self._q.put(None)
        self._t.join(timeout=5)


WORKER: ComWorker | None = None


def worker() -> ComWorker:
    global WORKER
    if WORKER is None:
        from .journal import default_root

        WORKER = ComWorker(log_path=default_root() / "operations.jsonl")
    return WORKER
