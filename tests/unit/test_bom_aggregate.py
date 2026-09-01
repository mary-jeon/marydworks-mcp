from sw.read import aggregate

# traverse 결과 형태: level, path, title, config, doc_type, suppression(0..3), excluded, virtual
R = [
    dict(level=1, path=r"Z:\a\PART-101.SLDPRT", title="PART-101.SLDPRT", config="기본", doc_type="part", suppression=2, excluded=False, virtual=False),
    dict(level=1, path=r"Z:\a\PART-101.SLDPRT", title="PART-101.SLDPRT", config="기본", doc_type="part", suppression=2, excluded=False, virtual=False),
    dict(level=1, path=r"Z:\a\SUB.SLDASM", title="SUB.SLDASM", config="기본", doc_type="assembly", suppression=2, excluded=False, virtual=False),
    dict(level=2, path=r"Z:\a\PART-102.SLDPRT", title="PART-102.SLDPRT", config="기본", doc_type="part", suppression=1, excluded=False, virtual=False),
    dict(level=2, path=r"Z:\a\PART-103.SLDPRT", title="PART-103.SLDPRT", config="기본", doc_type="part", suppression=0, excluded=False, virtual=False),
    dict(level=1, path="", title="파트1^TOP", config="기본", doc_type="part", suppression=2, excluded=True, virtual=True),
]


def test_top_level_counts_direct_children_only():
    rows = aggregate(R, "top_level")
    by = {r["part_number"]: r for r in rows}
    assert by["PART-101"]["instances"] == 2
    assert by["SUB"]["instances"] == 1 and by["SUB"]["type"] == "assembly"
    assert "PART-102" not in by


def test_parts_only_flattens_and_skips_assemblies():
    rows = aggregate(R, "parts_only")
    by = {r["part_number"]: r for r in rows}
    assert set(by) == {"PART-101", "PART-102", "PART-103", "파트1^TOP"}
    assert by["PART-102"]["state"] == "lightweight"
    assert by["PART-103"]["state"] == "suppressed" and by["PART-103"]["instances"] == 0
    assert by["파트1^TOP"]["state"] == "virtual" and by["파트1^TOP"]["excluded_from_bom"] is True


def test_indented_keeps_levels_in_order():
    rows = aggregate(R, "indented")
    assert [(r["level"], r["part_number"]) for r in rows][:3] == [(1, "PART-101"), (1, "PART-101"), (1, "SUB")]


def test_suppressed_not_counted_but_listed():
    rows = aggregate(R, "parts_only")
    # 억제(0)는 0, lightweight(1)·가상은 센다: 2 + 1 + 0 + 1
    assert sum(r["instances"] for r in rows) == 4
