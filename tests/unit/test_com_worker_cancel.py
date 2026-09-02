"""타임아웃으로 포기한 작업은 나중에 몰래 실행되면 안 된다 ."""
import threading
import time

import pytest

from sw.com_worker import ComWorker
from sw.models import SwError


def test_queued_job_is_cancelled_after_timeout():
    w = ComWorker(init_com=False)
    ran = []
    release = threading.Event()

    def slow():
        release.wait(5)
        ran.append("slow")

    def later():
        ran.append("later")

    t = threading.Thread(target=lambda: w.run(slow, timeout=10), daemon=True)
    t.start()
    time.sleep(0.05)  # slow가 STA 스레드를 점유한 상태
    with pytest.raises(SwError) as e:
        w.run(later, write=True, timeout=0.2)
    assert e.value.code == "BUSY" and "취소" in e.value.message
    release.set()
    t.join(2)
    time.sleep(0.2)
    assert ran == ["slow"], ran  # later는 실행되지 않았다


def test_started_job_timeout_says_it_may_complete():
    w = ComWorker(init_com=False)
    release = threading.Event()

    def slow():
        release.wait(5)
        return "done"

    with pytest.raises(SwError) as e:
        w.run(slow, write=True, timeout=0.2)
    assert "이미 시작" in e.value.message
    release.set()
