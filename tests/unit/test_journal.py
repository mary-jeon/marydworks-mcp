import json
import time
from pathlib import Path

import pytest

from sw.journal import Journal, precondition_hash, save_order
from sw.models import SwError


def mk(tmp_path, ttl=600):
    return Journal(tmp_path, ttl_s=ttl)


def test_plan_roundtrip_and_apply(tmp_path):
    j = mk(tmp_path)
    pre = {"PART-105.SLDPRT": {"DATE": "2026.01.01"}}
    p = j.create_plan("sw_set_properties", [{"title": "PART-105.SLDPRT"}], [{"before": "2026.01.01", "after": "2026.09.01"}], [], pre, 200)
    assert p["plan_id"] and p["status"] == "pending" and p["precondition_hash"] == precondition_hash(pre)
    assert Path(tmp_path, "plans", p["plan_id"] + ".json").exists()
    p2 = j.check_plan(p["plan_id"], "sw_set_properties", pre)
    assert p2["plan_id"] == p["plan_id"]
    cs = j.mark_applied(p["plan_id"], ["PART-105.SLDPRT"], [])
    assert j.get_change_set(cs)["dirty_documents"] == ["PART-105.SLDPRT"]
    with pytest.raises(SwError) as ei:
        j.check_plan(p["plan_id"], "sw_set_properties", pre)
    assert ei.value.code == "PLAN_ALREADY_APPLIED"


def test_stale(tmp_path):
    j = mk(tmp_path)
    p = j.create_plan("t", [], [], [], {"a": 1}, 10)
    with pytest.raises(SwError) as ei:
        j.check_plan(p["plan_id"], "t", {"a": 2})
    assert ei.value.code == "PLAN_STALE"


def test_expired(tmp_path):
    j = mk(tmp_path, ttl=0.01)
    p = j.create_plan("t", [], [], [], {}, 10)
    time.sleep(0.05)
    with pytest.raises(SwError) as ei:
        j.check_plan(p["plan_id"], "t", {})
    assert ei.value.code == "PLAN_EXPIRED"


def test_wrong_tool_and_unknown(tmp_path):
    j = mk(tmp_path)
    p = j.create_plan("t1", [], [], [], {}, 10)
    with pytest.raises(SwError) as ei:
        j.check_plan(p["plan_id"], "t2", {})
    assert ei.value.code == "PLAN_STALE"
    with pytest.raises(SwError) as ei:
        j.check_plan("nope", "t1", {})
    assert ei.value.code == "DOC_NOT_FOUND"


def test_max_targets(tmp_path):
    j = mk(tmp_path)
    with pytest.raises(SwError) as ei:
        j.create_plan("t", [{"i": i} for i in range(3)], [], [], {}, 2)
    assert ei.value.code == "PLAN_STALE"


def test_backup_manifest(tmp_path):
    j = mk(tmp_path / "journal")
    src = tmp_path / "PART-105.SLDPRT"
    src.write_bytes(b"abc")
    man = j.backup([str(src)], related=["Z:\\x\\ASSY-A.SLDASM"], reason="rename")
    d = Path(man["dir"])
    assert (d / "PART-105.SLDPRT").read_bytes() == b"abc"
    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    assert m["files"][0]["sha256"] and m["related"] == ["Z:\\x\\ASSY-A.SLDASM"] and m["reason"] == "rename"


def test_save_order():
    docs = [{"title": "d.SLDDRW", "type": "drawing"}, {"title": "a.SLDASM", "type": "assembly"}, {"title": "p.SLDPRT", "type": "part"}]
    assert [d["title"] for d in save_order(docs)] == ["p.SLDPRT", "a.SLDASM", "d.SLDDRW"]
