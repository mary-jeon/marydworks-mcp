# 2026-09-10: 염수주입라인.SLDASM에서 근사 모델 B4b → 제조사 STEP 합성 파트 B4c 교체 (CLAUDE.md §4 매핑)
#  B4c 파트 좌표: Z=스템 축, z0=취부면, 몸체 +z. 라인 배치: R_g(e_x→(0,0,1), e_y→(−1,0,0), e_z→(0,−1,0)), t=(0,−48,−74.5)
#   → 라인에서 x −40.9~32.7 · y −166.9~−48(취부면 y −48 = 밸브 패드) · z −155.3~−48.5 (종전 B4b x −32.7~59.4: 넓은 쪽이 +x에서 −x로 — STEP 실형상은 거울상 배치가 불가)
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
NEW=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT"); assert os.path.exists(NEW)
R_G=[[0,0,1],[-1,0,0],[0,-1,0]]; T=(0.0,-48.0,-74.5)
EXP=[-40.9,-166.93,-155.25,32.7,-48.0,-48.5]
stop=watchdog(); app=connect()
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); title=a.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
def interf(doc,items):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
old=[n for n in cc if n.startswith("B4b_actuator")]; assert len(old)==1, old; old=old[0]
supp={cfg:None for cfg in CFGS}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; supp[cfg]=comps()[old].GetSuppression2
print("old",old,"supp by cfg",supp)
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); c=cc[old]
if app.GetOpenDocumentByName(NEW) is None: open_doc(app,NEW,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
a.ClearSelection2(True); c.Select4(False,NOD,False)
ok=a.ReplaceComponents2(NEW,"",True,True,True); print("ReplaceComponents2",ok); a.ClearSelection2(True); a.EditRebuild3
cc=comps(); new=[n for n in cc if n.startswith("B4c_actuator")]; assert len(new)==1, new; new=new[0]; print("new",new)
rep={"old":old,"new":new,"supp":supp,"cfg":{}}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); c=cc[new]
    move_fixed(c,R_G,T); a.ForceRebuild3(False); cc=comps(); c=cc[new]
    st=c.GetSuppression2
    if supp[cfg]==2 and st!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
    if supp[cfg]!=2 and st==2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps(); c=cc[new]; xf=xform(c); b=box(c) if c.GetSuppression2==2 else None
    rep["cfg"][cfg]={"supp":c.GetSuppression2,"t":xf["t_mm"],"R":xf["R"],"box":b,"whatswrong":ww(a)}
    print(f"[{cfg}] supp {c.GetSuppression2} t {xf['t_mm']} box {b} ww {ww(a)}")
    if b: assert all(abs(p-q)<0.3 for p,q in zip(b,EXP)), ("box mismatch",b,EXP)
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(a,act_); rep["interf_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs B4?",[r for r in refs if r.startswith("B4")])
assert not any(r.startswith("B4b_") for r in refs)
dirty=[(os.path.basename(dd.GetPathName),dd.GetSaveFlag) for dd in pv(app,"GetDocuments") or [] if dd.GetSaveFlag and dd.GetPathName]
outside=[p for p,f in dirty if not os.path.join(Z,p).startswith(Z)]
e=I4(); w=I4(); ok=a.Save3(1,e,w); print("save asm",ok,e.value,w.value); rep["save"]=ok
json.dump(rep,open(os.path.join(VER,"ke002_replace_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("replace done")
