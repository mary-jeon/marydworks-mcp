# 2026-09-10: 염수주입라인.SLDASM에서 근사 모델 B9f → TraceParts STEP 파트 B9g 교체 + 핀 위치를 실측 U 폭(후단 22.4·전단 17.6)에 맞춰 이동
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
NEW=os.path.join(Z,"B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT"); assert os.path.exists(NEW)
I3=[[1,0,0],[0,1,0],[0,0,1]]; AX=70.0; Z_REAR_PIN=-26.0; ZP_UP=-390.0; ZP_DN=-530.0; PIN_ROD_H=25.0
U_REAR=22.4; U_FRONT=17.6
PINS={"G11e_MISUMI_SHCCG8-18.4_pin-1":(AX,-U_REAR/2,Z_REAR_PIN),"J11d_MISUMI_SHCCG8-20.4_pin-1":(AX,-U_FRONT/2,ZP_UP+PIN_ROD_H),"J11d_MISUMI_SHCCG8-20.4_pin-2":(AX,-U_FRONT/2,ZP_DN+PIN_ROD_H)}
stop=watchdog(); app=connect()
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
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
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
old=[n for n in cc if n.startswith("B9f_TiMOTION")]; assert len(old)==1, old; old=old[0]
supp={}; refc={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; c=comps()[old]; supp[cfg]=c.GetSuppression2; refc[cfg]=c.ReferencedConfiguration
print("old",old,"supp",supp,"refcfg",refc)
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); c=cc[old]
if app.GetOpenDocumentByName(NEW) is None: open_doc(app,NEW,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
a.ClearSelection2(True); c.Select4(False,NOD,False)
ok=a.ReplaceComponents2(NEW,"상승",True,True,True); print("ReplaceComponents2",ok); a.ClearSelection2(True); a.EditRebuild3
cc=comps(); new=[n for n in cc if n.startswith("B9g_TiMOTION")]; assert len(new)==1, new; new=new[0]; print("new",new)
rep={"old":old,"new":new,"cfg":{}}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); c=cc[new]
    move_fixed(c,I3,(AX,0,Z_REAR_PIN))
    for n,t in PINS.items():
        if n in cc: move_fixed(cc[n],I3,t)
    a.ForceRebuild3(False); cc=comps(); c=cc[new]
    st=c.GetSuppression2
    if supp[cfg]==2 and st!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
    if supp[cfg]!=2 and st==2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps(); c=cc[new]
    if c.GetSuppression2==2 and refc[cfg] in ("상승","하강"): c.ReferencedConfiguration=refc[cfg]; a.ForceRebuild3(False); cc=comps(); c=cc[new]
    b=box(c) if c.GetSuppression2==2 else None
    rep["cfg"][cfg]={"supp":c.GetSuppression2,"refcfg":c.ReferencedConfiguration,"t":xform(c)["t_mm"],"box":b,"pins":{n:xform(cc[n])["t_mm"] for n in PINS if n in cc},"whatswrong":ww(a)}
    print(f"[{cfg}] supp {c.GetSuppression2} refcfg {c.ReferencedConfiguration} box {b} ww {ww(a)}")
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_={n:c for n,c in cc.items() if c.GetSuppression2==2}
    rows=interf(a,list(act_.values())); rep["interf_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
    for n in (new,"J8e_lug_PL6_40x26-1","J9d_lug_PL6_40x31-1","J9d_lug_PL6_40x31-2","G11e_MISUMI_SHCCG8-18.4_pin-1","J11d_MISUMI_SHCCG8-20.4_pin-1","J11d_MISUMI_SHCCG8-20.4_pin-2"):
        if n in act_: print("   ",n,box(act_[n]))
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); assert not any(r.startswith("B9f_") for r in refs), refs
e=I4(); w=I4(); ok=a.Save3(1,e,w); print("save asm",ok,e.value,w.value); rep["save"]=ok
json.dump(rep,open(os.path.join(VER,"ta2_replace_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("replace done")
