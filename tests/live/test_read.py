import pytest

from sw import api, read
from sw.models import DocSelector
from sw.selectors import resolve

pytestmark = pytest.mark.live


def test_status_connected(cfg):
    s = read.status()
    assert s["connected"] and s["open_count"] > 0
    assert any(d["path"].lower() == cfg["assembly_path"].lower() for d in s["documents"])


def test_summary_part(cfg):
    e = cfg["expect"]
    d = read.summary(DocSelector(path=cfg["part_path"]))
    assert d["type"] == "part"
    assert d["material"]["value"] == e["part_material"]
    assert abs(d["mass_properties"]["mass_kg"] - e["part_mass_kg"]) < 0.05
    assert abs(d["bbox_mm"]["x"] - e["part_bbox_x_mm"]) < 1
    for k, v in e["part_props"].items():
        assert d["custom_properties"]["file"][k]["resolved"] == v


def test_bom_top_level(cfg):
    e = cfg["expect"]
    b = read.bom(DocSelector(path=cfg["assembly_path"]), "top_level")
    assert len(b["rows"]) == e["bom_rows"]
    assert sum(r["instances"] for r in b["rows"]) == e["bom_instances"]


def test_configuration_restored_after_summary(cfg):
    app = api.get_app()
    m, _ = resolve(app, DocSelector(path=cfg["part_path"]))
    before = api.active_config_name(m)
    read.summary(DocSelector(path=cfg["part_path"], configuration=before))
    assert api.active_config_name(m) == before


def test_snapshot_restores_active_document(cfg, tmp_path):
    app = api.get_app()
    before = api.doc_title(app.ActiveDoc)
    r = read.snapshot(DocSelector(path=cfg["part_path"]), ["iso", "front"], str(tmp_path))
    assert len(r["files"]) == 2 and all(f["bytes"] > 10000 for f in r["files"])
    assert api.doc_title(app.ActiveDoc) == before


def test_audit_runs(cfg):
    a = read.audit(DocSelector(path=cfg["assembly_path"]), required_props=["TITLE"])
    assert a["counts"]["rows"] == cfg["expect"]["bom_rows"]
    assert isinstance(a["qty_mismatch"], list)
