# 2026-09-15 사용자 승인: S30000MU0 사용자 작성 (f) 8개 → 호스트 부품 기준면에 3면 일치/거리 메이트(강체) 후 고정 해제. 저장 안 함(별도 sw_save)
import os, sys, json, math, re
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=r"<PROJECT_DIR>\_검증"
P=os.path.join(Z,"S30000MU0.SLDASM"); ASMN="S30000MU0"
HOST={"S30017MU0-1":"S30006MU0-1","C-HHSN65A_hinge-1":"S30006MU0-1","C-HHSN65A_hinge-2":"S30006MU0-1","S30008MU0-5":"S30006MU0-1","S30008MU0-6":"S30006MU0-1",
      "C-1170-2S_latch-1":"S30017MU0-1","C-1170-2S_keeper-1":"S30008MU0-5","C-1170-2S_keeper-2":"S30008MU0-6"}
ORDER=["S30017MU0-1","C-HHSN65A_hinge-1","C-HHSN65A_hinge-2","S30008MU0-5","S30008MU0-6","C-1170-2S_latch-1","C-1170-2S_keeper-1","C-1170-2S_keeper-2"]
stop=watchdog(); app=connect(); s=app.GetOpenDocumentByName(P); app.ActivateDoc3(P,False,0,I4()); s=app.ActiveDoc; cm=s.ConfigurationManager
CFGS=list(pv(s,"GetConfigurationNames")); WORK="상승"
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    s.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def set_supp(c,on):
    st=c.GetSuppression2
    if on and st!=2: s.ClearSelection2(True); c.Select4(False,NOD,False); s.EditUnsuppress2; s.ClearSelection2(True)
    if (not on) and st==2: s.ClearSelection2(True); c.Select4(False,NOD,False); s.EditSuppress2; s.ClearSelection2(True)
def mates_iter():
    f=pv(s,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="MateGroup":
            sf=f.GetFirstSubFeature
            while sf is not None: yield sf; sf=sf.GetNextSubFeature
        f=pv(f,"GetNextFeature")
def mate_names(): return [m.Name for m in mates_iter()]
def del_mate(n):
    s.ClearSelection2(True)
    if s.Extension.SelectByID2(n,"MATE",0,0,0,False,0,NOD,0): s.EditDelete()
    s.ClearSelection2(True)
KO=("우측면","윗면","정면"); EN=("Right Plane","Top Plane","Front Plane")
def sel_plane(comp,axis,append):
    for nm in (KO[axis],EN[axis]):
        if s.Extension.SelectByID2(f"{nm}@{comp}@{ASMN}","PLANE",0,0,0,append,1,NOD,0): return True
    return False
# 스냅샷(구성별 억제·변환)
SNAP=os.path.join(VER,"s30_mates_snap0_0915.json")
if not os.path.exists(SNAP):
    snap={}
    for cfg in CFGS:
        s.ShowConfiguration2(cfg); s.EditRebuild3; snap[cfg]={n:(c.GetSuppression2,xform(c)["R"],xform(c)["t_mm"],c.IsFixed) for n,c in comps().items()}
    json.dump(snap,open(SNAP,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
snap=json.load(open(SNAP,encoding="utf-8"))
s.ShowConfiguration2(WORK); s.EditRebuild3; cc=comps()
for n in ORDER+list(set(HOST.values())): set_supp(cc[n],True)
s.ForceRebuild3(False); cc=comps(); EXIST=set(mate_names()); print("existing mates",len(EXIST),"ww",ww())
def set_xf(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def xf_ok(n,R,t):
    s.ForceRebuild3(False); x=xform(comps()[n]); return max(abs(x["R"][i][j]-R[i][j]) for i in range(3) for j in range(3))<1e-3 and max(abs(p-q) for p,q in zip(x["t_mm"],t))<0.02, x
rep={}
for n in ORDER:
    h=HOST[n]; Rp=np.array(snap[WORK][n][1]); tp=np.array(snap[WORK][n][2]); Rh=np.array(snap[WORK][h][1]); th=np.array(snap[WORK][h][2])
    c=comps()[n]
    if c.IsFixed: s.ClearSelection2(True); c.Select4(False,NOD,False); s.UnfixComponent(); s.ClearSelection2(True)
    made=[]
    for k in range(3):
        nk=Rp[k]; dots=[float(nk@Rh[j]) for j in range(3)]; j=int(np.argmax(np.abs(dots))); assert abs(dots[j])>0.999,(n,k,dots); sign=1 if dots[j]>0 else -1
        off=float((tp-th)@Rh[j]); name=f"고정_{n}_{'xyz'[j]}"
        if name in EXIST: made.append(name+"(기존)"); continue
        variants=[(0 if sign>0 else 1,False),(1 if sign>0 else 0,False)] if abs(off)<1e-6 else [(0 if sign>0 else 1,False),(0 if sign>0 else 1,True),(1 if sign>0 else 0,False),(1 if sign>0 else 0,True)]
        done=False
        for al,fl in variants:
            c=comps()[n]; set_xf(c,Rp.tolist(),tp.tolist()); s.EditRebuild3
            s.ClearSelection2(True); assert sel_plane(n,k,False),(n,k); assert sel_plane(h,j,True),(h,j)
            err=I4(); m=s.AddMate5(0 if abs(off)<1e-6 else 5,al,fl,abs(off)/1000,0,0,0,0,0,0,0,False,False,0,err); s.ClearSelection2(True)
            nm=mate_names()
            if m is None:
                if nm and nm[-1] not in EXIST and re.fullmatch(r"(거리|일치)\d+",nm[-1]): del_mate(nm[-1])
                print("   fail",name,err.value); continue
            f=list(mates_iter())[-1]; f.Name=name; g,x=xf_ok(n,Rp,tp)
            if g and not ww(): done=True; EXIST.add(name); break
            print("   retry",name,al,fl,x["t_mm"],ww()); del_mate(name); set_xf(comps()[n],Rp.tolist(),tp.tolist()); s.EditRebuild3
        assert done,(n,name); made.append(name)
    print(f"  {n:22s} host {h:14s} mates {made}")
# 억제 상태 복원 + 구성별 검증
for cfg in CFGS:
    s.ShowConfiguration2(cfg); s.EditRebuild3; cc=comps()
    for n,c in cc.items(): set_supp(c,snap[cfg][n][0]==2)
    s.ForceRebuild3(False); cc=comps()
    drift=[(n,xform(c)["t_mm"],snap[cfg][n][2]) for n,c in cc.items() if c.GetSuppression2==2 and max(abs(p-q) for p,q in zip(xform(c)["t_mm"],snap[cfg][n][2]))>0.02]
    rdrift=[n for n,c in cc.items() if c.GetSuppression2==2 and max(abs(xform(c)["R"][i][j]-snap[cfg][n][1][i][j]) for i in range(3) for j in range(3))>1e-3]
    fixed=[n for n,c in cc.items() if c.IsFixed]
    rep[cfg]={"ww":ww(),"drift":drift,"rdrift":rdrift,"fixed":fixed}; print(f"[{cfg}] ww {ww()} fixed {fixed} drift {drift} rdrift {rdrift}")
s.ShowConfiguration2(snap and "상승"); s.EditRebuild3
json.dump(rep,open(os.path.join(VER,"s30_mates_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("s30 mates done (not saved)")
