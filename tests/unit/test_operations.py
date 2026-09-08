"""FIX-06 회귀(2026-09-08): operation 상태 기록, timeout 후 실행 중인 쓰기가 있으면 새 쓰기 거부,
부분 결과(progress) 기록, operations.jsonl 영속."""
import json
import threading
import time

import pytest

from sw import com_worker as cw
from sw.com_worker import ComWorker, progress
from sw.models import SwError


def _wait(pred, t=3.0):
    t0 = time.time()
    while time.time() - t0 < t:
        if pred():
            return True
        time.sleep(0.01)
    return False


def test_completed_op_is_recorded_with_summary():
    w = ComWorker(init_com=False)

    def add(a, b):
        return {"change_set_id": "cs1", "dirty_documents": ["A.SLDPRT"], "raw": object()}

    assert w.run(add, 1, 2, write=True)["change_set_id"] == "cs1"
    r = w.recent(5)[0]
    assert r["name"] == "add" and r["state"] == cw.COMPLETED and r["write"] is True
    assert r["result"] == {"change_set_id": "cs1", "dirty_documents": ["A.SLDPRT"]}  # 객체·잡동사니는 요약에서 빠진다
    assert r["duration_s"] >= 0 and r["started_at"] and r["finished_at"]
    w.close()


def test_failed_op_records_error_and_exception_carries_op_id():
    w = ComWorker(init_com=False)

    def boom():
        raise SwError("COM_ERROR", "x")

    with pytest.raises(SwError) as ei:
        w.run(boom)
    r = w.recent(1)[0]
    assert r["state"] == cw.FAILED and r["error"] == "COM_ERROR: x" and ei.value.op_id == r["op_id"]
    w.close()


def test_cancelled_before_start_is_recorded_and_never_runs():
    w = ComWorker(init_com=False)
    release = threading.Event()
    ran = []

    def slow():
        release.wait(5)
        ran.append("slow")

    def later():
        ran.append("later")

    t = threading.Thread(target=lambda: w.run(slow, timeout=10), daemon=True)
    t.start()
    assert _wait(lambda: any(r["state"] == cw.RUNNING for r in w.recent()))
    with pytest.raises(SwError) as e:
        w.run(later, write=True, timeout=0.2)
    assert e.value.code == "BUSY" and e.value.details["state"] == cw.CANCELLED
    release.set()
    t.join(2)
    time.sleep(0.2)
    assert w.get(e.value.details["op_id"])["state"] == cw.CANCELLED and ran == ["slow"]
    w.close()


def test_timeout_running_write_blocks_new_writes_until_resolved():
    w = ComWorker(init_com=False)
    release = threading.Event()
    calls = []

    def slow_write():
        progress(deleted=["A-1"])
        release.wait(5)
        progress(deleted=["A-2"])
        return {"deleted": ["A-1", "A-2"], "still_present": []}

    with pytest.raises(SwError) as e1:
        w.run(slow_write, write=True, timeout=0.5)
    op = e1.value.details["op_id"]
    assert e1.value.details["state"] == cw.TIMEOUT_RUNNING
    assert e1.value.details["side_effects"] == {"deleted": ["A-1"]}  # 포기 시점까지 이미 지워진 것
    assert [u["op_id"] for u in w.unresolved_writes()] == [op]
    # 결과 미확정인 쓰기가 있으면 새 쓰기는 거부되고 큐에도 들어가지 않는다 (같은 삭제를 두 번 하지 않도록)
    with pytest.raises(SwError) as e2:
        w.run(lambda: calls.append("dup"), write=True, timeout=1)
    assert e2.value.code == "BUSY" and "실행 중" in e2.value.message and op in e2.value.message
    # 읽기는 큐에 들어가 앞 작업이 끝난 뒤 실행된다
    t = threading.Thread(target=lambda: calls.append(w.run(lambda: "read-ok", timeout=5)), daemon=True)
    t.start()
    release.set()
    t.join(3)
    assert _wait(lambda: w.get(op)["state"] == cw.COMPLETED_AFTER_TIMEOUT)
    r = w.get(op)
    assert r["side_effects"] == {"deleted": ["A-1", "A-2"]} and r["result"] == {"deleted": ["A-1", "A-2"], "still_present": []}
    assert w.unresolved_writes() == [] and calls == ["read-ok"]
    assert w.run(lambda: "w2", write=True) == "w2"  # 확정된 뒤엔 쓰기가 다시 된다
    w.close()


def test_failed_after_timeout_is_recorded():
    w = ComWorker(init_com=False)
    release = threading.Event()

    def slow_fail():
        release.wait(5)
        raise ValueError("late")

    with pytest.raises(SwError) as e:
        w.run(slow_fail, write=True, timeout=0.5)
    release.set()
    op = e.value.details["op_id"]
    assert _wait(lambda: w.get(op)["state"] == cw.FAILED_AFTER_TIMEOUT)
    assert w.get(op)["error"] == "ValueError: late" and w.unresolved_writes() == []
    w.close()


def test_operations_log_persists_transitions(tmp_path):
    p = tmp_path / "journal" / "operations.jsonl"
    w = ComWorker(init_com=False, log_path=p)
    w.run(lambda: 1, name="one")

    def two():
        raise ValueError("x")

    with pytest.raises(ValueError):
        w.run(two, write=True)
    w.close()
    rows = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]
    assert [(r["name"], r["state"]) for r in rows] == [("one", cw.RUNNING), ("one", cw.COMPLETED),
                                                       ("two", cw.RUNNING), ("two", cw.FAILED)]
    assert rows[3]["error"].startswith("ValueError") and rows[3]["write"] is True


def test_progress_outside_worker_is_noop():
    progress(x=1)


def test_summarize_result_keeps_only_known_keys():
    s = cw.summarize_result({"saved": [{"title": "A.SLDPRT", "path": "C:/a"}], "plan_id": "p", "other": 1})
    assert s == {"plan_id": "p", "saved": ["A.SLDPRT"]}
    assert cw.summarize_result(None) == "NoneType"
