# line32 보정: J2c 배치(정렬순 ±240), G13g 소켓 양단 나사부 표현 컷 Ø42.8×15, 상승 호스 활 +y 방향, 라인 간섭 재검사, 저장
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
def orphan_sketches(d):
    fl=[]; f=pv(d,"FirstFeature")
    while f is not None: fl.append(f); f=pv(f,"GetNextFeature")
    parents=set()
    for f in fl:
        if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature"): continue
        for pf in (pv(f,"GetParents") or []):
            try: parents.add(pf.Name)
            except Exception: pass
        sf=pv(f,"GetFirstSubFeature")
        while sf is not None:
            try: parents.add(sf.Name)
            except Exception: pass
            sf=pv(sf,"GetNextSubFeature")
    return [f.Name for f in fl if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature") and f.Name not in parents]
def clean(d):
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3
# ---------- G13g 소켓: 양단 Ø42.8×15 컷(나사부 표현). 검증 = r21.4 원통면 z 범위
P=Zp("G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP.SLDPRT"); d=act(P); L=51.0; R=21.4; ENG=15.0
def bodies(): return list(pv(d,"GetBodies2",0,True) or [])
def r_faces():
    out=[]
    for fc in bodies()[0].GetFaces():
        s=fc.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000-R)<0.05: fb=[round(v*1000,2) for v in fc.GetBox]; out.append((fb[2],fb[5]))
    return out
def delete(n,kind="BODYFEATURE"):
    d.ClearSelection2(True); d.Extension.SelectByID2(n,kind,0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
def sketch_circle(r):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(r)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def offset_cut(r,start,depth,name,check):
    for dirflag in (True,False):
        for flip in (False,True):
            sk=sketch_circle(r)
            f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(start),flip,False); d.EditRebuild3
            if f is None: delete(sk,"SKETCH"); continue
            f.Name=name
            if check(): return True
            delete(name)
    return False
if "포트컷_상" not in feat_names(d):
    ok=False
    for dirflag in (True,False):
        sk=sketch_circle(R); f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(ENG),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
        if f is None: delete(sk,"SKETCH"); print("  top cut dir",dirflag,"None"); continue
        f.Name="포트컷_상"
        if any(abs(a+ENG)<0.3 and abs(b)<0.3 for a,b in r_faces()) and len(bodies())==1: ok=True; break
        print("  top cut dir",dirflag,"faces",r_faces()); delete("포트컷_상")
    assert ok, "socket top cut"
if "포트컷_하" not in feat_names(d):
    assert offset_cut(R,L-ENG,ENG,"포트컷_하",lambda: any(abs(a+L)<0.3 and abs(b+(L-ENG))<0.3 for a,b in r_faces()) and len(bodies())==1), "socket bottom cut"
clean(d); print("G13g port cuts",r_faces(),"ww",ww(d),"orphans",orphan_sketches(d))
cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("REMARK") or ""
if "포트컷" not in s_: cp.Set2("REMARK",s_+" 포트컷_상/하 = Rc 나사부 표현(Ø42.8×15, 니플 겹침 제거).")
e=I4(); w=I4(); print("save G13g",d.Save3(1,e,w),e.value)
# ---------- 어셈블리 보정
a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def set_supp(c,active):
    if (c.GetSuppression2==2)==active: return
    a.ClearSelection2(True); c.Select4(False,NOD,False)
    if active: a.EditUnsuppress2
    else: a.EditSuppress2
    a.ClearSelection2(True)
I3=[[1,0,0],[0,1,0],[0,0,1]]
R_HOSE_POS=[[0,1,0],[0,0,1],[1,0,0]]; R_HOSE_NEG=[[0,-1,0],[0,0,1],[-1,0,0]]
# 호스 활 파트의 불룩 방향(파트 x 부호) 실측
hup=[n for n in os.listdir(Z) if n.startswith("J19i_hose_YASUNG_HSPF-032_up_bow")][0]; dh=act(Zp(hup)); bh=[round(v*1000,2) for v in pv(list(pv(dh,"GetBodies2",0,True))[0],"GetBodyBox")]
bulge_pos=bh[3]>abs(bh[0]); print("hose bow part box",bh,"bulge +x?",bulge_pos)
R_H=R_HOSE_POS if bulge_pos else R_HOSE_NEG
a=act(ASM,2)
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    sh=sorted([n for n in cc if n.startswith("J2c_")],key=lambda n:int(n.rsplit("-",1)[1]))
    for i,n in enumerate(sh):
        c=cc[n]; sup=c.GetSuppression2; set_supp(c,True); move_fixed(c,I3,(0,240 if i==0 else -240,0)); set_supp(c,sup==2)
    for n in cc:
        if n.startswith("J19i_hose_YASUNG_HSPF-032_up_bow"):
            c=cc[n]; sup=c.GetSuppression2; set_supp(c,True); move_fixed(c,R_H,(0,0,-154.6)); set_supp(c,sup==2)
    a.ForceRebuild3(False); cc=comps()
    print(f"[{cfg}] ww {ww(a)} shafts",[(n[-2:],xform(cc[n])["t_mm"]) for n in sh],"hose bow box",[box(cc[n]) for n in cc if n.startswith("J19i_hose_YASUNG_HSPF-032_up_bow") and cc[n].GetSuppression2==2])
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
rep={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(act_); rep[cfg]=rows; print(f"[{cfg}] 간섭 {len(rows)}")
    for r in sorted(rows,key=lambda r:-r[1])[:10]: print("    ",r)
a.ShowConfiguration2("상승"); a.EditRebuild3
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
json.dump(rep,open(os.path.join(VER,"line32_interf_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("done")
