import pytest

from sw.models import SwError
from sw.write import DEFAULT_TEMPLATE, drawing_plan


def test_plan_ok(tmp_path):
    t = tmp_path / "도면.DRWDOT"
    t.write_bytes(b"x")
    p = drawing_plan({"title": "PART-105.SLDPRT", "path": r"Z:\a\PART-105.SLDPRT", "type": "part"}, str(t), ["front", "top", "right", "iso"], True, False)
    assert p["template"] == str(t) and p["views"] == ["front", "top", "right", "iso"]
    assert p["bom"] is False  # 파트는 BOM 없음
    p2 = drawing_plan({"title": "A.SLDASM", "path": r"Z:\a\A.SLDASM", "type": "assembly"}, str(t), ["iso"], True, False)
    assert p2["bom"] is True


def test_plan_rejects(tmp_path):
    with pytest.raises(SwError) as ei:
        drawing_plan({"title": "x", "path": r"Z:\x.SLDPRT", "type": "part"}, str(tmp_path / "없음.DRWDOT"), ["front"], False, False)
    assert ei.value.code == "DOC_NOT_FOUND"
    t = tmp_path / "t.DRWDOT"
    t.write_bytes(b"x")
    with pytest.raises(SwError):
        drawing_plan({"title": "x", "path": r"Z:\x.SLDPRT", "type": "part"}, str(t), ["front", "weird"], False, False)
    with pytest.raises(SwError):
        drawing_plan({"title": "d", "path": r"Z:\d.SLDDRW", "type": "drawing"}, str(t), ["front"], False, False)
    with pytest.raises(SwError):
        drawing_plan({"title": "x", "path": "", "type": "part"}, str(t), ["front"], False, False)


def test_default_template_path():
    assert DEFAULT_TEMPLATE.endswith("도면.DRWDOT")
