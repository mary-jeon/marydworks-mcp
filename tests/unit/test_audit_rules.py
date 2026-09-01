from sw.read import audit_rules

ROWS = [
    {"part_number": "PART-101", "file": r"Z:\a\PART-101.SLDPRT", "state": "ok", "instances": 4, "qty_property": "4", "qty_mismatch": False,
     "material": {"value": "STS 304", "state": "ok"}, "props": {"SPEC": "100x100", "DATE": ""}},
    {"part_number": "PART-204 - 복사본 (2)", "file": r"Z:\a\PART-204 - 복사본 (2).SLDPRT", "state": "ok", "instances": 1, "qty_property": "3", "qty_mismatch": True,
     "material": {"value": None, "state": "not_assigned"}, "props": {"SPEC": "", "DATE": "2026.01.01"}},
    {"part_number": "PART-103", "file": r"Z:\a\PART-103.SLDPRT", "state": "lightweight", "instances": 2, "qty_property": None, "qty_mismatch": None,
     "material": {"value": None, "state": "lightweight"}, "props": {}},
]


def test_rules():
    a = audit_rules(ROWS, ["SPEC", "DATE"])
    assert a["missing_properties"] == [{"part_number": "PART-101", "missing": ["DATE"]},
                                       {"part_number": "PART-204 - 복사본 (2)", "missing": ["SPEC"]}]
    assert a["qty_mismatch"] == [{"part_number": "PART-204 - 복사본 (2)", "instances": 1, "qty_property": "3"}]
    assert a["copy_named_files"] == [r"Z:\a\PART-204 - 복사본 (2).SLDPRT"]
    assert a["material_not_assigned"] == ["PART-204 - 복사본 (2)"]
    assert a["not_resolved"] == [{"part_number": "PART-103", "state": "lightweight"}]
    assert a["counts"] == {"rows": 3, "issues": 6}
