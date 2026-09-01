from sw.write import find_referencing_docs, rename_sequence


def test_sequence_after_removal():
    # PART-104 삭제 → 5..11을 4..10으로, 낮은 번호부터
    seq = rename_sequence([5, 6, 7, 8, 9, 10, 11], removed=4, prefix="PART-1", suffix="", width=2)
    assert seq[0] == ("PART-105", "PART-104") and seq[-1] == ("PART-111", "PART-110") and len(seq) == 7


def test_find_referencing_docs():
    docs = [{"title": "ASSY-A.SLDASM", "type": "assembly", "deps": [r"Z:\a\PART-105.SLDPRT"]},
            {"title": "TOP-ASSY.SLDDRW", "type": "drawing", "deps": [r"Z:\a\ASSY-A.SLDASM"]},
            {"title": "X.SLDASM", "type": "assembly", "deps": []}]
    assert find_referencing_docs(docs, r"z:\A\PART-105.SLDPRT") == ["ASSY-A.SLDASM"]
