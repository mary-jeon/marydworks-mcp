import datetime

from sw.write import plan_property_changes, substitute


def test_substitute_today_and_instances_and_expr():
    today = datetime.date.today().strftime("%Y-%m-%d")
    assert substitute("$today", {}) == today
    assert substitute("$instances", {"instances": 4}) == "4"
    assert substitute('$expr:"SW-Mass@S1.SLDPRT"', {}) == '"SW-Mass@S1.SLDPRT"'
    assert substitute("plain", {}) == "plain"
    assert substitute(3, {}) == "3"


def test_plan_changes_preserves_formula():
    cur = {"DATE": {"value": "2026.01.01", "resolved": "2026.01.01", "type": 30},
           "Material": {"value": '"SW-Material@S1.SLDPRT"', "resolved": "STS 304", "type": 30}}
    changes, warnings = plan_property_changes(cur, {"DATE": "2026.09.01", "Material": "STS 316", "NEW": "x"})
    assert {c["name"]: (c["before"], c["after"], c["action"]) for c in changes} == {
        "DATE": ("2026.01.01", "2026.09.01", "set"), "NEW": (None, "x", "add")}
    assert warnings and "Material" in warnings[0] and "$expr:" in warnings[0]


def test_plan_changes_skips_unchanged():
    cur = {"DATE": {"value": "a", "resolved": "a", "type": 30}}
    changes, _ = plan_property_changes(cur, {"DATE": "a"})
    assert changes == []
