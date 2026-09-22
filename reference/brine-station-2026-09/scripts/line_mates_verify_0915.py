# 읽기 전용: 염수주입라인 고정(f) 잔여·메이트 목록·구성별 간섭(상승/하강)·자유도(거리 메이트 억제 시 이동 가능 여부는 메이트 구조로 기록)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=r"<PROJECT_DIR>\_검증"
stop=watchdog(); app=connect(); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    a.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
MT={0:"일치",1:"동심",5:"거리",6:"각도"}
mates=[]
f=pv(a,"FirstFeature")
while f is not None:
    if pv(f,"GetTypeName2")=="MateGroup":
        sf=f.GetFirstSubFeature
        while sf is not None:
            m=sf.GetSpecificFeature2; ents=[m.MateEntity(i).ReferenceComponent.Name2 if m.MateEntity(i).ReferenceComponent else "ASM" for i in range(m.GetMateEntityCount)]
            mates.append((sf.Name,MT.get(m.Type,m.Type),ents)); sf=sf.GetNextSubFeature
    f=pv(f,"GetNextFeature")
print("mates",len(mates)); [print("  ",m) for m in mates]
rep={"mates":mates,"cfg":{}}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps()
    fixed=[n for n,c in cc.items() if c.IsFixed]; act={n:c for n,c in cc.items() if c.GetSuppression2==2}
    rows=interf(list(act.values())) if cfg in ("상승","하강") else None
    rep["cfg"][cfg]={"fixed":fixed,"ww":ww(),"active":sorted(act),"pos":{n:xform(c)["t_mm"] for n,c in act.items()},"interf":rows}
    print(f"[{cfg}] fixed {fixed} ww {ww()} active {len(act)} interf {rows}")
a.ShowConfiguration2("상승"); a.EditRebuild3
print("dirty",a.GetSaveFlag)
json.dump(rep,open(os.path.join(VER,"line_mates_verify_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("verify done")
