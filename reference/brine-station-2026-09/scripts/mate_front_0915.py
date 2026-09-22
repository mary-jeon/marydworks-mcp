# 2026-09-15 사용자 지시: S00000MU0 메이트 일치88(S10007MU0-3 정면↔S20002MU0-3 정면) → S10001MU0-1 정면↔S20002MU0-3 정면으로 교체, L-BRACKET_PUMP-BODY-1 제거. (백업 생략: 사용자 지시) 저장은 별도(sw_save only_under)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=r"<PROJECT_DIR>\_검증"
PS=os.path.join(Z,"S00000MU0.SLDASM")
stop=watchdog(); app=connect(); s=app.GetOpenDocumentByName(PS); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
assert scm.ActiveConfiguration.Name=="기본"
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    s.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
out=[]
def walk(c,depth):
    for ch in (pv(c,"GetChildren") or []):
        out.append((ch.Name2,ch))
        if depth<2: walk(ch,depth+1)
def scan():
    out.clear(); walk(scm.ActiveConfiguration.GetRootComponent3(True),0); return dict(out)
cc=scan()
top={n:c for n,c in cc.items() if n.count("/")==0}
def interf(items):
    s.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True); return rows
TOPS=[n for n in ("S10000MU0-1","S20000MU0-1","S30000MU0-1","900000MU1-1") if n in top]
rep={"before":{"S20000_box":box(top["S20000MU0-1"]),"ww":ww()}}
rep["before"]["interf"]=interf([top[n] for n in TOPS]); print("before interf",rep["before"]["interf"],"S20000 box",rep["before"]["S20000_box"])
# 일치88 삭제
s.ClearSelection2(True); ok=s.Extension.SelectByID2("일치88","MATE",0,0,0,False,0,NOD,0); assert ok, "select 일치88"
ok=s.EditDelete(); print("delete 일치88",ok); s.ClearSelection2(True)
# 면 선택: 월드 좌표 점으로(GetBody 면 박스는 파트 로컬 좌표라 사용 불가 — 실측)
sm=s.SelectionManager
def pick(pt,comp_name,append):
    ok=s.Extension.SelectByID2("","FACE",pt[0]/1000,pt[1]/1000,pt[2]/1000,append,1,NOD,0); assert ok, ("pick",pt)
    i=sm.GetSelectedObjectCount2(-1); comp=sm.GetSelectedObjectsComponent4(i,-1); o=sm.GetSelectedObject6(i,-1)
    n=[round(v,3) for v in pv(o,"Normal")]; print("  picked",comp.Name2,"n(local)",n,"box(local)",[round(v*1000,1) for v in o.GetBox])
    assert comp.Name2==comp_name, comp.Name2
s.ClearSelection2(True)
pick((-500,-812.5,-50),"S20000MU0-1/S20002MU0-3",False)
pick((0,-725,50),"S10000MU0-1/S10001MU0-1",True)
err=I4(); m=s.AddMate5(0,0,False,0,0,0,0,0,0,0,0,False,False,0,err); print("AddMate5",m is not None,"err",err.value); s.ClearSelection2(True)
assert m is not None and err.value in (0,1), err.value
try: m.GetFeature.Name="일치_S20002-3정면_S10001-1정면"
except Exception as ex: print("rename exc",ex)
# L 브라켓 제거
cc=scan(); lb=[n for n in cc if n.startswith("L-BRACKET_PUMP-BODY")]; print("L bracket comps",lb)
for n in lb:
    s.ClearSelection2(True); cc[n].Select4(False,NOD,False); print("delete",n,s.EditDelete()); s.ClearSelection2(True)
s.ForceRebuild3(False); cc=scan(); top={n:c for n,c in cc.items() if n.count("/")==0}
rep["after"]={"S20000_box":box(top["S20000MU0-1"]),"S20002-3_box":box(cc["S20000MU0-1/S20002MU0-3"]),"S10001-1_box":box(cc["S10000MU0-1/S10001MU0-1"]),"ww":ww(),"L_bracket_remaining":[n for n in cc if "L-BRACKET" in n]}
rep["after"]["interf"]=interf([top[n] for n in TOPS])
print("after S20000 box",rep["after"]["S20000_box"],"S20002-3",rep["after"]["S20002-3_box"]); print("ww",rep["after"]["ww"]); print("after interf",rep["after"]["interf"])
print("dirty",s.GetSaveFlag)
json.dump(rep,open(os.path.join(VER,"mate_front_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("mate edit done (not saved)")
