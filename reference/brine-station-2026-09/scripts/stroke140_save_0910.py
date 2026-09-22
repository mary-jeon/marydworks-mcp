# 2026-09-10: 스트로크 140 — 파일명 갱신(SaveAs로 참조 자동 갱신) + 저장. 대상은 Station 폴더만.
#  B9f_TiMOTION_TA2-2H-120_RL339_clevisU → B9f_TiMOTION_TA2-2H-140_RL339_clevisU
#  J19e_hose_3-4in_dn_straight_L336     → J19e_hose_3-4in_dn_straight_L356   (상승 R54는 재해 결과 R54.2라 이름 유지)
#  구 파일은 디스크에 남음 → SW 종료 후 sw-mcp\_backup\20260910-unused\ 로 이동
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n)
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
stop=watchdog(); app=connect()
REN=[("B9f_TiMOTION_TA2-2H-120_RL339_clevisU.SLDPRT","B9f_TiMOTION_TA2-2H-140_RL339_clevisU.SLDPRT"),
     ("J19e_hose_3-4in_dn_straight_L336.SLDPRT","J19e_hose_3-4in_dn_straight_L356.SLDPRT")]
rep={}
for old,new in REN:
    po,pn=Zp(old),Zp(new); assert not os.path.exists(pn), "exists "+pn
    d=app.GetOpenDocumentByName(po); assert d is not None, old
    app.ActivateDoc3(po,False,0,I4()); d=app.ActiveDoc
    e=I4(); w=I4(); ok=d.Extension.SaveAs(pn,0,1,NOD,e,w)   # 1 = silent
    print("SaveAs",new,ok,e.value,w.value); assert ok and os.path.exists(pn)
    rep[new]={"saveas":ok,"err":e.value,"warn":w.value}
# 상승 호스(이름 유지) 저장
hu=app.GetOpenDocumentByName(Zp("J19e_hose_3-4in_up_bow_R54.SLDPRT")); app.ActivateDoc3(Zp("J19e_hose_3-4in_up_bow_R54.SLDPRT"),False,0,I4()); hu=app.ActiveDoc
e=I4(); w=I4(); ok=hu.Save3(1,e,w); print("save up hose",ok,e.value,w.value); rep["J19e_hose_3-4in_up_bow_R54.SLDPRT"]={"save":ok,"err":e.value,"warn":w.value}
# 어셈블리: 참조 확인 후 저장
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager
a.ShowConfiguration2("상승"); a.EditRebuild3
names={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.EditRebuild3
    for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"):
        names[c.Name2]=os.path.basename(c.GetPathName)
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted(set(names.values())); print("refs",refs); rep["asm_refs"]=refs
assert "B9f_TiMOTION_TA2-2H-140_RL339_clevisU.SLDPRT" in refs and "J19e_hose_3-4in_dn_straight_L356.SLDPRT" in refs
assert not any(("TA2-2H-120" in r) or ("L336" in r) for r in refs), "old refs remain"
# 저장 대상이 Station 폴더 밖이면 중단
dirty=[(dd.GetPathName,dd.GetSaveFlag) for dd in pv(app,"GetDocuments") or []]
outside=[p for p,f in dirty if f and not p.startswith(Z)]
print("dirty",[(os.path.basename(p),f) for p,f in dirty if f]); assert not outside, outside
e=I4(); w=I4(); ok=a.Save3(1,e,w); print("save asm",ok,e.value,w.value); rep["asm"]={"save":ok,"err":e.value,"warn":w.value}
rep["still_dirty"]=[os.path.basename(dd.GetPathName) for dd in pv(app,"GetDocuments") or [] if dd.GetSaveFlag]
print("still dirty",rep["still_dirty"])
json.dump(rep,open(os.path.join(VER,"stroke140_save_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("save done")
