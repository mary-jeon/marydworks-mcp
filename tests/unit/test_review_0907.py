"""2026-09-07 검토(P0-1 plan 묶기 · P0-2 out_path 범위 · P0-3 백업 충돌 · P1-1 메이트 성공코드)의 회귀 테스트."""
import json
import time
from pathlib import Path

from sw.journal import Journal, precondition_hash
from sw.write import add_component_precondition, check_save_scope, mate_succeeded


class _Mate:
    pass


def test_mate_no_error_is_1():
    m = _Mate()
    assert mate_succeeded(m, 1)          # swAddMateError_NoError
    assert mate_succeeded(m, 0)          # ErrorUknown but mate exists (some versions)
    assert not mate_succeeded(None, 1)
    assert not mate_succeeded(m, 4)      # IncorrectSelections
    assert not mate_succeeded(None, 0)


def test_save_scope_checks_out_path():
    assert check_save_scope([], [r"C:\proj"], r"D:\lib\new.SLDPRT") == [r"D:\lib\new.SLDPRT"]
    assert check_save_scope([], [r"C:\proj"], r"C:\proj\sub\new.SLDPRT") == []
    assert check_save_scope([], [], r"D:\lib\new.SLDPRT") == []   # only_under 없으면 종전과 같이 검사 안 함


def test_add_component_plan_binds_position_and_mates():
    a = add_component_precondition(r"C:\p\A.SLDASM", 3, r"C:\p\B.SLDPRT", [0, 0, -10], [], "delete_component")
    b = add_component_precondition(r"C:\p\A.SLDASM", 3, r"C:\p\B.SLDPRT", [0, 0, -20], [], "delete_component")
    c = add_component_precondition(r"C:\p\A.SLDASM", 3, r"C:\p\B.SLDPRT", [0, 0, -10], [{"type": "coincident"}], "delete_component")
    assert precondition_hash(a) != precondition_hash(b)
    assert precondition_hash(a) != precondition_hash(c)
    assert precondition_hash(a) == precondition_hash(add_component_precondition(r"C:\p\A.SLDASM", 3, r"C:\p\B.SLDPRT", [0.0, 0.0, -10.0], [], "delete_component"))


def test_backup_keeps_same_basename_from_two_folders(tmp_path):
    j = Journal(tmp_path / "journal")
    a = tmp_path / "x" / "same.txt"; b = tmp_path / "y" / "same.txt"
    a.parent.mkdir(); b.parent.mkdir()
    a.write_bytes(b"AAA"); b.write_bytes(b"BBB")
    man = j.backup([str(a), str(b)], related=[], reason="t")
    assert len(man["files"]) == 2
    backups = [Path(f["backup"]) for f in man["files"]]
    assert backups[0] != backups[1]
    assert backups[0].read_bytes() == b"AAA" and backups[1].read_bytes() == b"BBB"
    m = json.loads((Path(man["dir"]) / "manifest.json").read_text(encoding="utf-8"))
    assert {f["source"] for f in m["files"]} == {str(a), str(b)}


def test_backup_dirs_unique_within_same_second(tmp_path):
    j = Journal(tmp_path / "journal")
    src = tmp_path / "s.txt"; src.write_bytes(b"1")
    d1 = j.backup([str(src)], related=[], reason="a")["dir"]
    d2 = j.backup([str(src)], related=[], reason="b")["dir"]
    assert d1 != d2 and (Path(d1) / "s.txt").exists() and (Path(d2) / "s.txt").exists()
