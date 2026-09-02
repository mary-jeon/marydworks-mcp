"""save()의 순수 판정 함수 — 검토에서 나온 구멍을 고정한다.

- change_set 문서를 제목이 아니라 문서 id(정규화 경로)로 고른다
- 같은 제목이 둘 이상이면 고르지 않고 멈춘다 (DOC_AMBIGUOUS)
- only_under 밖의 문서는 저장 거부
- 삭제 대상 선택은 names/path_contains로만, 이름 오타는 실패
"""
import pytest

from sw.models import SwError
from sw.write import check_save_scope, pick_change_set_docs, select_delete_targets


def _doc(title, path, did=None):
    return {"title": title, "path": path, "document_id": did or path.lower(), "type": "part", "dirty": True}


A1 = _doc("PART-1.SLDPRT", r"C:\proj\PART-1.SLDPRT")
A2 = _doc("PART-1.SLDPRT", r"C:\lib\PART-1.SLDPRT")
B = _doc("PART-2.SLDPRT", r"C:\proj\PART-2.SLDPRT")


def test_ids_win_over_titles():
    cs = {"dirty_documents": ["PART-1.SLDPRT"], "dirty_ids": [A1["document_id"]]}
    out = pick_change_set_docs(cs, [], [A2, A1, B])
    assert [d["path"] for d in out] == [A1["path"]]


def test_ambiguous_title_without_ids_stops():
    cs = {"dirty_documents": ["PART-1.SLDPRT"], "dirty_ids": []}
    with pytest.raises(SwError) as e:
        pick_change_set_docs(cs, [], [A1, A2])
    assert e.value.code == "DOC_AMBIGUOUS"


def test_unique_title_without_ids_is_fine():
    cs = {"dirty_documents": ["PART-2.SLDPRT"]}
    assert pick_change_set_docs(cs, [], [A1, B]) == [B]


def test_missing_document_reported():
    cs = {"dirty_documents": ["PART-9.SLDPRT"], "dirty_ids": ["c:\\proj\\part-9.sldprt"]}
    with pytest.raises(SwError) as e:
        pick_change_set_docs(cs, [], [A1, B])
    assert e.value.code == "DOC_NOT_FOUND"


def test_handles_are_kept_and_not_duplicated():
    cs = {"dirty_documents": ["PART-1.SLDPRT", "PART-2.SLDPRT"], "dirty_ids": [A1["document_id"], B["document_id"]]}
    out = pick_change_set_docs(cs, [A1], [A1, B, A2])
    assert [d["path"] for d in out] == [A1["path"], B["path"]]


def test_save_scope_blocks_library_docs():
    outside = check_save_scope([A1, A2, B], [r"C:\proj"])
    assert outside == [A2["path"]]
    assert check_save_scope([A1, B], []) == []


def test_delete_targets_by_name_and_path():
    kids = [{"name": "BOLT-1", "path": r"Z:\lib\BOLT.SLDPRT"}, {"name": "NOZZLE-1", "path": r"Z:\lib\NOZZLE.SLDPRT"},
            {"name": "FRAME-1", "path": r"C:\proj\FRAME.SLDPRT"}]
    assert [t["name"] for t in select_delete_targets(kids, ["BOLT-1"], None)] == ["BOLT-1"]
    assert [t["name"] for t in select_delete_targets(kids, [], r"Z:\lib\BOLT")] == ["BOLT-1"]
    assert [t["name"] for t in select_delete_targets(kids, [], r"Z:\lib")] == ["BOLT-1", "NOZZLE-1"]
    assert select_delete_targets(kids, [], None) == []
    with pytest.raises(SwError):
        select_delete_targets(kids, ["BOLT-2"], None)
