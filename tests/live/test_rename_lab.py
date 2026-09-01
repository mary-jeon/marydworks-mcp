"""파일명 변경·부품 추가는 되돌리기 어려우므로, 실제 프로젝트가 아니라 Pack and Go로 복사한
`rename_lab_dir`의 어셈블리가 열려 있을 때만 실행한다. 원본 파일명과 같은 파일이 사용자 세션에
열려 있으면 SolidWorks가 원본을 재사용하므로, 원본은 닫힌 세션에서 실행할 것."""
import os

import pytest

from sw import read, write
from sw.models import DocSelector

pytestmark = pytest.mark.live


@pytest.fixture
def lab(cfg):
    lab_dir = cfg.get("rename_lab_dir", "")
    s = read.status()
    asm = next((d for d in s["documents"] if lab_dir and d["path"].lower().startswith(lab_dir.lower()) and d["type"] == "assembly"), None)
    if asm is None:
        pytest.skip("rename_lab 어셈블리가 열려 있지 않음")
    return lab_dir, asm


def test_rename_dry_run_apply_save(cfg, lab):
    lab_dir, asm = lab
    tgt = DocSelector(path=os.path.join(lab_dir, cfg["rename_lab_target"]))
    par = DocSelector(path=asm["path"])
    new = os.path.splitext(cfg["rename_lab_target"])[0] + "_R"
    r = write.rename_document(tgt, par, new, False, [], None, False, True, None)
    assert r["dry_run"] and r["new_path"].endswith(new + ".SLDPRT")
    a = write.rename_document(tgt, par, new, False, [], None, False, False, r["plan_id"])
    assert a["change_set_id"] and os.path.isdir(a["backup"])
    write.save(a["change_set_id"], None, None, False)
    assert os.path.isfile(os.path.join(lab_dir, new + ".SLDPRT"))


def test_add_component_without_mates(cfg, lab):
    lab_dir, asm = lab
    part = os.path.join(lab_dir, cfg["rename_lab_extra_part"])
    r = write.add_component(DocSelector(path=asm["path"]), part, [0, 0, 500], [], "delete_component", True, None)
    a = write.add_component(DocSelector(path=asm["path"]), part, [0, 0, 500], [], "delete_component", False, r["plan_id"])
    assert a["component"] and a["mates_added"] == []
