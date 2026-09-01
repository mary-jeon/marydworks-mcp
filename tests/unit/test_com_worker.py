import threading
import time

import pytest

from sw.com_worker import ComWorker, is_busy_error
from sw.models import SwError


class Busy(Exception):
    hresult = -2147418111


def test_runs_on_single_thread():
    w = ComWorker(init_com=False)
    ids = {w.run(lambda: threading.get_ident()) for _ in range(5)}
    assert len(ids) == 1 and ids != {threading.get_ident()}
    w.close()


def test_exception_propagates():
    w = ComWorker(init_com=False)

    def boom():
        raise ValueError("x")

    with pytest.raises(ValueError):
        w.run(boom)
    w.close()


def test_read_retries_on_busy_then_succeeds():
    w = ComWorker(init_com=False, retry_delay=0.01)
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise Busy()
        return "ok"

    assert w.run(fn) == "ok" and calls["n"] == 3
    w.close()


def test_write_does_not_retry():
    w = ComWorker(init_com=False, retry_delay=0.01)
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise Busy()

    with pytest.raises(SwError) as ei:
        w.run(fn, write=True)
    assert ei.value.code == "BUSY" and calls["n"] == 1
    w.close()


def test_timeout():
    w = ComWorker(init_com=False)
    with pytest.raises(SwError) as ei:
        w.run(lambda: time.sleep(0.5), timeout=0.05)
    assert ei.value.code == "BUSY"
    w.close()


def test_is_busy_error():
    class E(Exception):
        hresult = -2147417846

    assert is_busy_error(E())
    assert not is_busy_error(ValueError())
