import pytest

from sw.models import SwError
from sw.write import export_check


def test_formats_by_doc_type(tmp_path):
    p = str(tmp_path / "x")
    assert export_check("part", "step", p + ".step", False) == ".step"
    assert export_check("assembly", "stl", p + ".stl", False) == ".stl"
    assert export_check("drawing", "pdf", p + ".pdf", False) == ".pdf"
    assert export_check("drawing", "dxf", p + ".dxf", False) == ".dxf"
    with pytest.raises(SwError) as ei:
        export_check("part", "pdf", p + ".pdf", False)
    assert ei.value.code == "INTERNAL"


def test_extension_must_match(tmp_path):
    with pytest.raises(SwError):
        export_check("part", "step", str(tmp_path / "x.stl"), False)


def test_no_overwrite(tmp_path):
    f = tmp_path / "x.step"
    f.write_bytes(b"1")
    with pytest.raises(SwError) as ei:
        export_check("part", "step", str(f), False)
    assert ei.value.code == "FILE_EXISTS"
    assert export_check("part", "step", str(f), True) == ".step"
