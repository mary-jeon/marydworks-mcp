import pytest
from sw.models import DocSelector, SwError
from sw.selectors import pick, normalize_path

DOCS = [
    {"title": "ASSY-A.SLDASM", "path": r"Z:\a\ASSY-A.SLDASM", "active": True},
    {"title": "PART-105.SLDPRT", "path": r"Z:\a\PART-105.SLDPRT", "active": False},
    {"title": "파트1.SLDPRT", "path": r"Z:\a\파트1.SLDPRT", "active": False},
    {"title": "파트1.SLDPRT", "path": r"Z:\b\파트1.SLDPRT", "active": False},
    {"title": "도면1", "path": "", "active": False},
]


def test_default_is_active():
    assert pick(DOCS, DocSelector())["title"] == "ASSY-A.SLDASM"


def test_path_case_insensitive():
    assert pick(DOCS, DocSelector(path=r"z:\A\part-105.sldprt"))["title"] == "PART-105.SLDPRT"


def test_title_unique():
    assert pick(DOCS, DocSelector(title="part-105.sldprt"))["path"].endswith("PART-105.SLDPRT")


def test_title_ambiguous_lists_candidates():
    with pytest.raises(SwError) as ei:
        pick(DOCS, DocSelector(title="파트1.SLDPRT"))
    assert ei.value.code == "DOC_AMBIGUOUS"
    assert [c["path"] for c in ei.value.details["candidates"]] == [r"Z:\a\파트1.SLDPRT", r"Z:\b\파트1.SLDPRT"]


def test_title_not_found():
    with pytest.raises(SwError) as ei:
        pick(DOCS, DocSelector(title="없음.SLDPRT"))
    assert ei.value.code == "DOC_NOT_FOUND"


def test_unsaved_doc_by_title():
    assert pick(DOCS, DocSelector(title="도면1"))["path"] == ""


def test_no_active():
    docs = [dict(d, active=False) for d in DOCS]
    with pytest.raises(SwError) as ei:
        pick(docs, DocSelector(active=True))
    assert ei.value.code == "DOC_NOT_FOUND"


def test_normalize_path():
    assert normalize_path(r"Z:\A\..\a\X.SLDPRT") == normalize_path(r"z:/a/x.sldprt")
    assert normalize_path("") == ""
