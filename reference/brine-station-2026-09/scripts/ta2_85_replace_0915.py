# 2026-09-15: 염수주입라인.SLDASM B9g(스트로크 140 대용) → B9h(TA2-2H-085339 발주 형번) 교체, 위치 (85,0,−26)·구성별 참조구성 상승/하강 유지, 간섭 확인, 저장, 파트 닫기
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=r"<PROJECT_DIR>\_검증"
NEW=os.path.join(Z,"B9h_TiMOTION_TA2-2H-085339-5511-010-1.SLDPRT"); assert os.path.exists(NEW)
I3=[[1,0,0],[0,1,0],[0,0,1]]; POS=(85.0,0.0,-26.0)
stop=watchdog(); app=connect()
a=app.GetOpenDocumentByName(ASM)
if a is None: open_doc(app,ASM,2)
app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def interf(doc,items):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
old=[n for n in cc if n.startswith("B9g_TiMOTION")]; assert len(old)==1, old; old=old[0]
supp={}; refc={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; c=comps()[old]; supp[cfg]=c.GetSuppression2; refc[cfg]=c.ReferencedConfiguration
print("old",old,"supp",supp,"refcfg",refc,"t",xform(comps()[old])["t_mm"])
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); c=cc[old]
if app.GetOpenDocumentByName(NEW) is None: open_doc(app,NEW,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
a.ClearSelection2(True); c.Select4(False,NOD,False)
ok=a.ReplaceComponents2(NEW,"상승",True,True,True); print("ReplaceComponents2",ok); a.ClearSelection2(True); a.EditRebuild3
cc=comps(); new=[n for n in cc if n.startswith("B9h_TiMOTION")]; assert len(new)==1, new; new=new[0]; print("new",new)
rep={"old":old,"new":new,"cfg":{}}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); c=cc[new]
    st=c.GetSuppression2
    if st!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True); cc=comps(); c=cc[new]
    move_fixed(c,I3,POS)
    if cfg in ("상승","하강"):
        try: c.ReferencedConfiguration=cfg
        except Exception as ex: print("  refcfg exc",ex)
    a.ForceRebuild3(False); cc=comps(); c=cc[new]
    if supp[cfg]!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps(); c=cc[new]
    b=box(c) if c.GetSuppression2==2 else None
    pins={n:xform(cc[n])["t_mm"] for n in cc if n.startswith(("G11f_","J11e_")) and cc[n].GetSuppression2==2}
    rep["cfg"][cfg]={"supp":c.GetSuppression2,"refcfg":c.ReferencedConfiguration,"t":xform(c)["t_mm"],"box":b,"pins":pins,"whatswrong":ww(a)}
    print(f"[{cfg}] supp {c.GetSuppression2} refcfg {c.ReferencedConfiguration} t {xform(c)['t_mm']} box {b} pins {pins} ww {ww(a)}")
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_={n:c for n,c in cc.items() if c.GetSuppression2==2}
    rows=interf(a,list(act_.values())); rep["interf_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); assert not any(r.startswith("B9g_") for r in refs), refs
e=I4(); w=I4(); ok=a.Save3(1,e,w); print("save asm",ok,e.value,w.value); rep["save"]=ok
x=app.GetOpenDocumentByName(NEW)
if x is not None: app.CloseDoc(x.GetTitle)
print("open docs",[x_.GetTitle for x_ in (pv(app,"GetDocuments") or [])])
json.dump(rep,open(os.path.join(VER,"ta2_b9h_replace_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("replace done")
