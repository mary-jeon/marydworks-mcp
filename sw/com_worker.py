from __future__ import annotations

import ctypes
import logging
import queue
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .models import SwError

log = logging.getLogger("sw.com")
RPC_E_CALL_REJECTED = -2147418111  # 0x80010001
RPC_E_SERVERCALL_RETRYLATER = -2147417846  # 0x8001010A
MUTEX_NAME = "Global\\marydworks-mcp-com"


def is_busy_error(exc: BaseException) -> bool:
    hr = getattr(exc, "hresult", None)
    if hr is None and getattr(exc, "args", None):
        hr = exc.args[0] if isinstance(exc.args[0], int) else None
    return hr in (RPC_E_CALL_REJECTED, RPC_E_SERVERCALL_RETRYLATER)


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
    done: threading.Event = field(default_factory=threading.Event)
    result: Any = None
    exc: BaseException | None = None
    started: bool = False    # STA 스레드가 실행을 시작했는가
    cancelled: bool = False  # 호출자가 타임아웃으로 포기했는가 — 아직 시작 전이면 실행하지 않는다


class ComWorker:
    """모든 COM 호출을 STA 스레드 1개에서 직렬 실행한다."""

    def __init__(self, init_com: bool = True, retry_delay: float = 0.5, max_retries: int = 10, mutex_timeout: float = 30.0):
        self._q: queue.Queue = queue.Queue()
        self._init_com = init_com
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.mutex_timeout = mutex_timeout
        self._mutex = _NamedMutex() if init_com else None
        self._t = threading.Thread(target=self._loop, name="sw-com-sta", daemon=True)
        self._t.start()

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
        if job.cancelled:
            # 호출자가 이미 BUSY로 포기한 작업. 특히 쓰기는 "실패"라고 보고된 뒤 몰래 적용되면 안 된다.
            job.exc = SwError("BUSY", "타임아웃으로 취소된 작업 — 실행하지 않음")
            job.done.set()
            return
        job.started = True
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
            job.done.set()

    def run(self, fn: Callable, *args, write: bool = False, timeout: float = 120.0, **kw) -> Any:
        job = _Job(fn, args, kw, write)
        self._q.put(job)
        if not job.done.wait(timeout):
            job.cancelled = True
            if job.started:
                # 이미 COM 안에서 도는 중이라 중단할 수 없다. 나중에 끝날 수 있음을 숨기지 않는다.
                what = "쓰기 작업" if job.write else "호출"
                raise SwError("BUSY", f"SolidWorks {what}이 {timeout:.0f}초 안에 끝나지 않았습니다. "
                                      "작업은 이미 시작되어 SolidWorks가 응답하면 그대로 완료될 수 있습니다 — "
                                      "재시도 전에 sw_status로 실제 상태를 확인하세요")
            raise SwError("BUSY", f"SolidWorks가 {timeout:.0f}초 안에 응답하지 않아 대기열의 작업을 취소했습니다 (실행되지 않음)")
        if job.exc:
            raise job.exc
        return job.result

    def close(self):
        self._q.put(None)
        self._t.join(timeout=5)


WORKER: ComWorker | None = None


def worker() -> ComWorker:
    global WORKER
    if WORKER is None:
        WORKER = ComWorker()
    return WORKER
