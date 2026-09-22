import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
R_B10=[[0,0,-1],[0,1,0],[1,0,0]]
stop=watchdog(); app=connect(); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
rep={}
for cfg in list(pv(a,"GetConfigurationNames")):
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,c in cc.items():
        if n.startswith("B10_"):
            sup=c.GetSuppression2; t=xform(c)["t_mm"]
            if sup!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
            move_fixed(c,R_B10,t)
            if sup!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps()
    if cfg in ("상승","하강"):
        act_=[c for n,c in cc.items() if c.GetSuppression2==2]; rows=interf(act_); rep[cfg]=rows
        print(f"[{cfg}] B10 boxes",[box(cc[n]) for n in cc if n.startswith("B10_") and cc[n].GetSuppression2==2],"간섭",len(rows))
        for r in sorted(rows,key=lambda r:-r[1])[:10]: print("    ",r)
a.ShowConfiguration2("상승"); a.EditRebuild3
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
json.dump(rep,open(r"<PROJECT_DIR>\_검증\loop50_interf_0914.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set()
