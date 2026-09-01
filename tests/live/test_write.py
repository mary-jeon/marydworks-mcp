import os

import pytest

from sw import api, read, write
from sw.models import DocSelector, SwError
from sw.selectors import resolve

pytestmark = pytest.mark.live


def _remark(cfg):
    m, _ = resolve(api.get_app(), DocSelector(path=cfg["part_path"]))
    return read.custom_properties(m, "").get("REMARK", {}).get("value", "") or ""


def _set_remark(cfg, value):
    sel = DocSelector(path=cfg["part_path"])
    r = write.set_properties([sel], "file", {"REMARK": value}, None, True, None)
    if r["documents"][0]["changes"]:
        write.set_properties([sel], "file", {"REMARK": value}, None, False, r["plan_id"])


def test_set_properties_dry_run_apply_revert(cfg):
    sel = DocSelector(path=cfg["part_path"])
    before = _remark(cfg)
    r = write.set_properties([sel], "file", {"REMARK": "mcp-test"}, None, True, None)
    assert r["dry_run"] and r["documents"][0]["changes"][0]["after"] == "mcp-test"
    a = write.set_properties([sel], "file", {"REMARK": "mcp-test"}, None, False, r["plan_id"])
    assert a["change_set_id"] and a["dirty_documents"]
    assert _remark(cfg) == "mcp-test"
    _set_remark(cfg, before)  # 되돌리기 (저장하지 않음)
    assert _remark(cfg) == before


def test_stale_plan_rejected(cfg):
    sel = DocSelector(path=cfg["part_path"])
    before = _remark(cfg)
    r = write.set_properties([sel], "file", {"REMARK": "x1"}, None, True, None)
    _set_remark(cfg, "x2")  # dry_run 이후 값이 바뀜
    with pytest.raises(SwError) as ei:
        write.set_properties([sel], "file", {"REMARK": "x1"}, None, False, r["plan_id"])
    assert ei.value.code == "PLAN_STALE"
    _set_remark(cfg, before)


def test_export_step(cfg, tmp_path):
    out = str(tmp_path / "part.step")
    r = write.export(DocSelector(path=cfg["part_path"]), "step", out, False)
    assert os.path.getsize(out) == r["bytes"] > 1000
    with pytest.raises(SwError) as ei:
        write.export(DocSelector(path=cfg["part_path"]), "step", out, False)
    assert ei.value.code == "FILE_EXISTS"


def test_create_drawing_and_save(cfg, tmp_path):
    sel = DocSelector(path=cfg["part_path"])
    r = write.create_drawing(sel, None, ["front", "top", "right", "iso"], False, False, True, None)
    assert r["dry_run"]
    a = write.create_drawing(sel, None, ["front", "top", "right", "iso"], False, False, False, r["plan_id"])
    assert set(a["views_created"]) == {"front", "top", "right", "iso"}
    out = str(tmp_path / "part_test.SLDDRW")
    s = write.save(a["change_set_id"], None, out, False)  # 미저장 도면은 change_set 핸들로 저장
    assert os.path.isfile(out) and s["saved"][0]["path"] == out
