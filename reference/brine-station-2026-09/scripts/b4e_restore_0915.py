# B4e 복구: 파트 축정렬_회전 삭제·저장(원상) → 어셈블리 B4e 메이트 삭제 → 원래 배치 R_B4D·t(−63,0,−85) → 3면 메이트(R·t 전부 검증) → 박스·간섭 확인
import os, sys, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
B4E="B4e_actuator_KOSAPLUS_KE005-F357C14-DC-1"; J1C="J1c_fixed_plate_185x580_t10-2"
RB=np.array([[0,0,1],[0,1,0],[-1,0,0]],float); TB=np.array([-63.0,0.0,-85.0])
stop=watchdog(); app=connect(); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
# --- 파트 원상 복구
c=comps()[B4E]; P=c.GetPathName; d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
n_del=0
while d.Extension.SelectByID2("축정렬_회전","BODYFEATURE",0,0,0,False,0,NOD,0): d.EditDelete(); d.ClearSelection2(True); n_del+=1
d.ForceRebuild3(False); f=pv(d,"FirstFeature"); names=[]
while f is not None: names.append(f.Name); f=pv(f,"GetNextFeature")
print("part rotation feats deleted",n_del,"tail",names[-3:],"ww",ww(d)); assert not [n for n in names if n.startswith("축정렬")]
e=I4(); w=I4(); print("save part",d.Save3(1,e,w),e.value)
# --- 어셈블리
app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; a.ShowConfiguration2("상승"); a.EditRebuild3
def mates_iter():
    f=pv(a,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="MateGroup":
            sf=f.GetFirstSubFeature
            while sf is not None: yield sf; sf=sf.GetNextSubFeature
        f=pv(f,"GetNextFeature")
def del_mate(n):
    a.ClearSelection2(True)
    if a.Extension.SelectByID2(n,"MATE",0,0,0,False,0,NOD,0): a.EditDelete()
    a.ClearSelection2(True)
for m in [m.Name for m in mates_iter()]:
    if "B4e" in m: del_mate(m); print("  deleted mate",m)
c=comps()[B4E]; arr=list(RB[0])+list(RB[1])+list(RB[2])+[TB[0]/1000,TB[1]/1000,TB[2]/1000,1.0,0,0,0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.ForceRebuild3(True)
c=comps()[B4E]; print("B4e placed",xform(c),"box",box(c))
KO=("우측면","윗면","정면"); EN=("Right Plane","Top Plane","Front Plane")
def sel_plane(comp,axis,append):
    for nm in (KO[axis],EN[axis]):
        if a.Extension.SelectByID2(f"{nm}@{comp}@염수주입라인","PLANE",0,0,0,append,1,NOD,0): return True
    return False
def xf_ok():
    a.ForceRebuild3(False); x=xform(comps()[B4E]); return max(abs(x["R"][i][j]-RB[i][j]) for i in range(3) for j in range(3))<1e-3 and max(abs(p-q) for p,q in zip(x["t_mm"],TB))<0.02, x
for k in range(3):
    j=int(np.argmax(np.abs(RB[k]))); sign=1 if RB[k][j]>0 else -1; off=TB[j]; name=f"고정_B4e-1_{'xyz'[j]}"
    variants=[(0 if sign>0 else 1,False),(1 if sign>0 else 0,False)] if abs(off)<1e-6 else [(0 if sign>0 else 1,False),(0 if sign>0 else 1,True),(1 if sign>0 else 0,False),(1 if sign>0 else 0,True)]
    done=False
    for al,fl in variants:
        # 매 시도 전 위치 원복(솔버가 돌려놓은 경우 대비)
        c=comps()[B4E]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
        a.ClearSelection2(True); assert sel_plane(B4E,k,False) and sel_plane(J1C,j,True)
        err=I4(); m=a.AddMate5(0 if abs(off)<1e-6 else 5,al,fl,abs(off)/1000,0,0,0,0,0,0,0,False,False,0,err); a.ClearSelection2(True)
        if m is None: print("   fail",name,err.value); continue
        f=list(mates_iter())[-1]; f.Name=name; g,x=xf_ok()
        if g and not ww(a): done=True; print("  mate",name,"ok al",al,"flip",fl); break
        print("   retry",name,al,fl,x["R"],x["t_mm"]); del_mate(name)
    assert done, name
a.ForceRebuild3(True); c=comps()[B4E]; print("final",xform(c),"box",box(c),"ww",ww(a))
def interf(items):
    a.ClearSelection2(True)
    for c_ in items: c_.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); rows=interf([c_ for c_ in cc.values() if c_.GetSuppression2==2]); print(f"[{cfg}] interf >0.05:",[r for r in rows if r[1]>0.05],"total",len(rows),"ww",ww(a))
a.ShowConfiguration2("상승"); a.EditRebuild3
x=app.GetOpenDocumentByName(P)
if x is not None: app.CloseDoc(x.GetTitle)
stop.set(); print("restore done (asm not saved)")
