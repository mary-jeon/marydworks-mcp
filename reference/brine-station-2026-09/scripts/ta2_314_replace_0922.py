# 2026-09-22: 라인 어셈블리 B9k(RL 274) → B9l(TraceParts 150314 STEP) ReplaceComponents2(기준면 메이트 재부착), 구성별 참조, 검증, 저장
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n); rep={}
P_B9L=Zp("B9l_TiMOTION_TA2-2H-150314-5511-010-1.SLDPRT"); P_B9K=Zp("B9k_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT"); assert os.path.exists(P_B9L)
stop=watchdog(); app=connect()
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
a=app.GetOpenDocumentByName(ASM) or open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def mates_iter():
    f=pv(a,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="MateGroup":
            sf=f.GetFirstSubFeature
            while sf is not None: yield sf; sf=sf.GetNextSubFeature
        f=pv(f,"GetNextFeature")
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
old=[c for n,c in cc.items() if n.startswith("B9k")]; assert len(old)==1,[n for n in cc if n.startswith("B9")]
x0=xform(old[0]); print("B9k t",x0["t_mm"])
a.ClearSelection2(True); old[0].Select4(False,NOD,False)
ok=a.ReplaceComponents2(P_B9L,"상승",True,0,True); print("ReplaceComponents2",ok); a.ClearSelection2(True); a.ForceRebuild3(False); assert ok
for sf in mates_iter():
    if "B9k" in sf.Name: sf.Name=sf.Name.replace("B9k","B9l")
cc=comps(); nm=[n for n in cc if n.startswith("B9l")]; assert len(nm)==1,nm; nm=nm[0]
x1=xform(cc[nm]); print("B9l t",x1["t_mm"],"R",x1["R"]); assert max(abs(p-q) for p,q in zip(x0["t_mm"],x1["t_mm"]))<0.02 and x1["t_mm"][2]==-26.0
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; want=("하강" if cfg in ("하강","2.하강했을때(해석)") else "상승")
    c=comps()[nm]
    if c.ReferencedConfiguration!=want: c.ReferencedConfiguration=want; a.EditRebuild3
    c=comps()[nm]; print(f"  [{cfg}] ww {ww(a)} B9l cfg {c.ReferencedConfiguration} supp {c.GetSuppression2} box {box(c)}")
    rep[cfg]={"ww":ww(a),"cfg":c.ReferencedConfiguration,"box":box(c)}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps()
    pin=[n for n in cc if n.startswith("J11e")][0]; print(f"  [{cfg}] J11e t {xform(cc[pin])['t_mm']}  B9l box {box(cc[nm])}")
    a.ClearSelection2(True); idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    res=sorted([([c_.Name2[:28] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
    print(f"[{cfg}] interferences {len(res)}:",[(v,cs) for cs,v in res if v>0.05][:10]); rep[f"interf_{cfg}"]=res
a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved asm",e.value,w.value)
for p in (P_B9L,P_B9K):
    d=app.GetOpenDocumentByName(p)
    if d is not None and d.GetPathName.lower()==P_B9K.lower(): app.CloseDoc(d.GetTitle); print("closed",os.path.basename(p))
app.ActivateDoc3(Zp("S00000MU0.SLDASM"),False,0,I4()); print("active",app.ActiveDoc.GetTitle)
json.dump(rep,open(os.path.join(VER,"ta2_b9l_replace_0922.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE")
