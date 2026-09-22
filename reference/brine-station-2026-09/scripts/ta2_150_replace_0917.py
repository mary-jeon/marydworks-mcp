# 2026-09-17: 라인 어셈블리에서 B9j(대용 형상) → B9k(TraceParts 150274 STEP) 교체, 구성별 참조, 검증, 저장
import os, sys, json, re
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); rep={}
P_B9K=Zp("B9k_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT"); J1C="J1c_fixed_plate_185x580_t10-2"; T=[85.0,0.0,-26.0]
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
def mate_names(): return [m.Name for m in mates_iter()]
def del_mate(name):
    a.ClearSelection2(True)
    if a.Extension.SelectByID2(name,"MATE",0,0,0,False,0,NOD,0): a.EditDelete()
    a.ClearSelection2(True)
KO=("우측면","윗면","정면"); EN=("Right Plane","Top Plane","Front Plane")
def sel_plane(comp,axis,append):
    for nm in (KO[axis],EN[axis]):
        if a.Extension.SelectByID2(f"{nm}@{comp}@염수주입라인","PLANE",0,0,0,append,1,NOD,0): return True
    return False
def add_mate(mtype,align,flip=False,dist=0.0,name=None):
    err=I4(); m=a.AddMate5(mtype,align,flip,dist,0.0,0.0,0,0,0,0,0,False,False,0,err); a.ClearSelection2(True)
    ok=(m is not None); f=None
    if ok:
        f=list(mates_iter())[-1]
        if name:
            try: f.Name=name
            except Exception as ex: print("  rename exc",ex)
    return ok,err.value,f
def t_ok(comp,t_exp):
    a.EditRebuild3; x=xform(comps()[comp]); return max(abs(p-q) for p,q in zip(x["t_mm"],t_exp))<0.02 and max(abs(x["R"][i][j]-(1.0 if i==j else 0.0)) for i in range(3) for j in range(3))<1e-3, x
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
old=[n for n in cc if n.startswith("B9j")]; print("delete",old)
for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
a.EditRebuild3
if app.GetOpenDocumentByName(P_B9K) is None: open_doc(app,P_B9K,1)
app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
c=a.AddComponent5(P_B9K,0,"",False,"",mm(T[0]),mm(T[1]),mm(T[2])); assert c is not None
arr=[1.0,0,0,0,1.0,0,0,0,1.0]+[mm(T[0]),mm(T[1]),mm(T[2]),1.0,0.0,0.0,0.0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
nm=c.Name2; print("inserted",nm); EXIST=set(mate_names())
for j in range(3):
    off=T[j]; name=f"고정_B9k-{nm.rsplit('-',1)[1]}_{'xyz'[j]}"; done=False
    variants=[(0,False),(1,False)] if abs(off)<1e-6 else [(0,False),(0,True),(1,False),(1,True)]
    for al,fl in variants:
        a.ClearSelection2(True); assert sel_plane(nm,j,False) and sel_plane(J1C,j,True)
        ok,e,f=add_mate(0,al,False,0,name) if abs(off)<1e-6 else add_mate(5,al,fl,abs(off)/1000,name)
        if not ok:
            nms=mate_names()
            if nms and re.fullmatch(r"(거리|일치|동심|각도)\d+",nms[-1]): del_mate(nms[-1])
            continue
        g,x=t_ok(nm,T)
        if g and not ww(a): done=True; break
        del_mate(name)
    assert done,name
print("mated",t_ok(nm,T))
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; comps()[nm].ReferencedConfiguration=("하강" if cfg in ("하강","2.하강했을때(해석)") else "상승"); a.EditRebuild3
    print(f"  [{cfg}] ww {ww(a)} B9k cfg {comps()[nm].ReferencedConfiguration} box {box(comps()[nm])}")
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); a.ClearSelection2(True)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
    print(f"[{cfg}] interferences {len(res)}"); [print("   ",v,[c_[:40] for c_ in cs]) for cs,v in res if v>0.05 and not all(c_.startswith("B4e") or c_.startswith("G3e") for c_ in cs)]
    rep[f"interf_{cfg}"]=res
a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved asm",e.value,w.value)
d=app.GetOpenDocumentByName(P_B9K)
if d is not None: app.CloseDoc(d.GetTitle)
json.dump(rep,open(os.path.join(DESK,"_검증","ta2_b9k_replace_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE")
