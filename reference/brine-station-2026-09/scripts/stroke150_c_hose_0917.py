# 2026-09-17 4단계(사용자 「호스: 접힌 고리 폭이 상승 시 190」·「아무거나 진행」): 나선 1회전 고리 호스(상승 Rc 74.5 → 폭 190 / 하강 Rc 50.5 → 폭 142),
#   나가는 다리 x −45 오프셋 → 이동판 소켓·호스니플·노즐·클램프 x −45, 이동판 앞 30 연장(J5l 180×540 → J5m 210×540)
import os, sys, json, math, re
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-17"
STAGE=sys.argv[1] if len(sys.argv)>1 else "all"; rep={"stage":STAGE}
ZP_UP=-360.0; ZP_DN=-510.0; HOSE_TOP=-154.6; STUB=52.4; HB=lambda zp: zp-15+20.4+14.2
PITCH=45.0; S1=35.0; RC_UP=(190.0-41.0)/2; XOFF=-PITCH          # 나가는 다리(이동측) x = −45
D_UP=HOSE_TOP-HB(ZP_UP); D_DN=HOSE_TOP-HB(ZP_DN)
def loop_len(Rc,N=720):
    L=0.0; prev=None
    for i in range(N+1):
        ph=2*math.pi*i/N; pt=(XOFF*(ph-math.sin(ph))/(2*math.pi), Rc*(1-math.cos(ph)), -Rc*math.sin(ph))
        if prev: L+=math.dist(prev,pt)
        prev=pt
    return L
LH_UP=loop_len(RC_UP); S2_UP=D_UP-2*STUB-S1; LF=S1+LH_UP+S2_UP; L_HOSE=LF+2*STUB
S2_DN=D_DN-2*STUB-S1; LH_DN=LF-S1-S2_DN
lo,hi=10.0,RC_UP
for _ in range(60):
    mid=(lo+hi)/2
    if loop_len(mid)<LH_DN: lo=mid
    else: hi=mid
RC_DN=(lo+hi)/2
print(f"hose: D {D_UP:.1f}/{D_DN:.1f} Lf {LF:.1f} cut {L_HOSE:.0f} | up Rc {RC_UP} w {2*RC_UP+41:.0f} s2 {S2_UP:.1f} | dn Rc {RC_DN:.1f} w {2*RC_DN+41:.0f} s2 {S2_DN:.1f}")
rep["hose"]=dict(D_UP=D_UP,D_DN=D_DN,Lf=LF,cut=L_HOSE,Rc_up=RC_UP,Rc_dn=RC_DN,pitch=PITCH,s1=S1,s2_up=S2_UP,s2_dn=S2_DN)
P_J5L=Zp("J5l_moving_plate_180x540_t8.SLDPRT"); P_J5M=Zp("J5m_moving_plate_210x540_t8.SLDPRT")
P_UP=Zp("J19m_hose_YASUNG_HSPF-032_up_loop190.SLDPRT"); P_DN=Zp(f"J19m_hose_YASUNG_HSPF-032_dn_loop{2*RC_DN+41:.0f}.SLDPRT")
J1C="J1c_fixed_plate_185x580_t10-2"
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def sel_plane_p(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
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
def clean_orphans(d):
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); print("  orphan sketch deleted",n)
    d.EditRebuild3; return orphan_sketches(d)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def set_props(d,props,mat=None):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    if mat:
        try: d.SetMaterialPropertyName2("","이텍",mat)
        except Exception as ex: print("  mat exc",ex)
def get_props(d):
    cp=d.Extension.CustomPropertyManager(""); return {k:cp.Get(k) for k in (pv(cp,"GetNames") or [])}
def save_new(d,path):
    assert not clean_orphans(d); e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d)); assert ok
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def close_unsaved_new():
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith(("파트","Part")): app.CloseDoc(tt); print("closed unsaved",tt)
def circ_xy(s):
    cpt=pv(s,"GetCenterPoint2")
    try: cx,cy=cpt[0]*1000,cpt[1]*1000
    except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
    r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
    return cx,cy,r
HOSE_SPEC="야성하이텍 슈퍼스프링호스(무독) HSPF-032: 내경 32.0±1.0·외경 41.0±1.0·0.5/2.5 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 3D 내경은 바브(Ø34) 위 늘어난 34로 표현. 최소 굽힘반경 카탈로그 미기재."
def loop_points(Rc,s2,D):
    """고리 중심선 점열(φ 0→2π), 피치 x(φ)=XOFF·(φ−sinφ)/2π → 양단 접선 −z. 반환: (pts, z0, zend, 전체 길이)"""
    z0=-(STUB+S1); N=96; pts=[]
    for i in range(N+1):
        ph=2*math.pi*i/N; pts.append((XOFF*(ph-math.sin(ph))/(2*math.pi), Rc*(1-math.cos(ph)), z0-Rc*math.sin(ph)))
    zend=-D; L=(STUB+S1)+loop_len(Rc)+(z0-zend); return pts,z0,zend,L
def volume(d): return d.Extension.CreateMassProperty.Volume*1e9
AREA=math.pi*(20.5**2-17.0**2)
def sketch_xy(sk,px,py,pz,conv):
    """모델 좌표(m) → 스케치 좌표(m). conv 0: out=R·p+t, 1: out=Rᵀ·p+t"""
    a=list(sk.ModelToSketchTransform.ArrayData); R=[a[0:3],a[3:6],a[6:9]]; t=a[9:12]; sc=a[12] if len(a)>12 and a[12] else 1.0
    if conv==0: o=[sc*(R[i][0]*px+R[i][1]*py+R[i][2]*pz)+t[i] for i in range(3)]
    else: o=[sc*(R[0][i]*px+R[1][i]*py+R[2][i]*pz)+t[i] for i in range(3)]
    return o[0],o[1]
def sel_face_at(d,z,pt):
    d.ClearSelection2(True)
    for b in bodies(d):
        for fc in list(pv(b,"GetFaces") or []):
            sf=fc.GetSurface; isp=sf.IsPlane
            if callable(isp): isp=isp()
            if not isp: continue
            gb=fc.GetBox; gb=gb() if callable(gb) else gb; bx=[v*1000 for v in gb]
            if abs(bx[2]-z)>0.05 or abs(bx[5]-z)>0.05: continue
            if bx[0]-0.01<=pt[0]<=bx[3]+0.01 and bx[1]-0.01<=pt[1]<=bx[4]+0.01:
                sd=d.SelectionManager.CreateSelectData
                if fc.Select4(False,sd) and d.SelectionManager.GetSelectedObjectCount2(-1)==1: return True
    return False
def build_hose(path,Rc,s2,D,title,spec_add,rebuild=False):
    if os.path.exists(path) and not rebuild: return
    pts,z0,zend,L=loop_points(Rc,s2,D); print(f"  loop pts {len(pts)} path length {L:.1f} (target {L_HOSE:.1f})")
    assert abs(L-L_HOSE)<1.0, (L,L_HOSE)
    if rebuild:
        d=act(path)
        for n,t in reversed(feats(d)):
            if t in ("Sweep","Extrusion","Boss","ProfileFeature","3DProfileFeature"):
                d.ClearSelection2(True)
                if d.Extension.SelectByID2(n,"BODYFEATURE" if t in ("Sweep","Extrusion","Boss") else "SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
        d.ForceRebuild3(False); assert not bodies(d), "old body remains"; print("  cleared",os.path.basename(path))
    else:
        close_unsaved_new(); d=app.NewDocument(tmpl,0,0,0)
    ring=lambda sm,cx=0.0,cy=0.0:(sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(20.5)),sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(17.0)))
    # (1) 상단 직선: 정면 스케치 링 → −z 돌출 |z0|
    assert sel_plane_p(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; ring(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(-z0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f,"stub1"; f.Name="직선_상단"
    bx=bbox(d); assert abs(bx[2]-z0)<0.05 and abs(bx[5])<0.05, bx
    # (2) 고리: 경로 = 3D 스플라인(φ 0→2π), 프로파일 = 상단 직선 끝면(z0) 위 링
    d.SketchManager.Insert3DSketch(True); d.SketchManager.AddToDB=True
    arr=[]
    for q in pts: arr+= [mm(q[0]),mm(q[1]),mm(q[2])]
    sp=d.SketchManager.CreateSpline2(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr),False); d.SketchManager.AddToDB=False; assert sp is not None,"spline"
    d.SketchManager.Insert3DSketch(True); d.ClearSelection2(True); path_sk=[n for n,t in feats(d) if t=="3DProfileFeature"][-1]
    f=None
    for conv in (0,1):
        assert sel_face_at(d,z0,(18.7,0.0)),"stub1 end face"
        d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; cx,cy=sketch_xy(sk,0.0,0.0,mm(z0),conv)
        sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(cx,cy,0,mm(20.5)); sm.CreateCircleByRadius(cx,cy,0,mm(17.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        prof_sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
        d.ClearSelection2(True); assert d.Extension.SelectByID2(prof_sk,"SKETCH",0,0,0,False,1,NOD,0); assert d.Extension.SelectByID2(path_sk,"SKETCH",0,0,0,True,4,NOD,0)
        f=d.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False); d.EditRebuild3
        v=volume(d) if (f is not None and len(bodies(d))==1) else None; v_exp=AREA*((-z0)+loop_len(Rc)); print(f"  loop conv {conv} center ({cx*1000:.2f},{cy*1000:.2f}) vol {None if v is None else round(v)} exp {round(v_exp)}")
        if v and abs(v-v_exp)/v_exp<0.015 and not ww(d): f.Name="고리_스윕"; break
        if f is not None: f.Select2(False,0); d.EditDelete(); d.EditRebuild3
        f=None; clean_orphans(d)
    assert f,"loop sweep"; print("  after loop vol",round(volume(d)),"ww",ww(d))
    # (3) 하단 직선: 고리 끝면(z0, 중심 (XOFF,0)) 위 링 → −z 돌출 (z0−zend)
    f=None
    for conv in (0,1):
        assert sel_face_at(d,z0,(XOFF+18.7,0.0)),"loop end face"
        d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; cx,cy=sketch_xy(sk,mm(XOFF),0.0,mm(z0),conv)
        sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(cx,cy,0,mm(20.5)); sm.CreateCircleByRadius(cx,cy,0,mm(17.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        skn=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
        for dirn in (True,False):
            d.ClearSelection2(True); d.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
            f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(z0-zend),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
            if f is None: continue
            v=volume(d) if len(bodies(d))==1 else None; v_exp=AREA*L_HOSE; endface=sel_face_at(d,zend,(XOFF+18.7,0.0)); d.ClearSelection2(True)
            print(f"  stub2 conv {conv} dirn {dirn} vol {None if v is None else round(v)} exp {round(v_exp)} endface {endface}")
            if v and abs(v-v_exp)/v_exp<0.015 and endface and len(bodies(d))==1: f.Name="직선_하단"; break
            f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
        if f is not None: break
        clean_orphans(d)
    assert f,"stub2"
    bx=bbox(d); print("  hose box(loose)",bx,"vol",round(volume(d)),"ww",ww(d)); assert not ww(d)
    set_props(d,{"TITLE":title,"SPEC":HOSE_SPEC+spec_add,"Material":"PVC","QT'Y":"1","DATE":DATE,"REMARK":"구매품(야성판매). 사용자 지시 「접힌 고리 폭 상승 시 190」 반영. 고리는 나선 1회전(+y 쪽, 피치 45를 φ−sinφ로 분배해 양단 접선 수직), 나가는 다리 x −45(이동판 소켓 위치). 실물은 자중·강선 탄성으로 형상이 달라질 수 있음."},mat="PVC 경질")
    if rebuild:
        assert not clean_orphans(d); e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved(in place)",os.path.basename(path),e.value,w.value); app.CloseDoc(d.GetTitle)
    else: save_new(d,path); app.CloseDoc(d.GetTitle)
if STAGE=="rebuild":
    for path,Rc,s2,D in ((P_UP,RC_UP,S2_UP,D_UP),(P_DN,RC_DN,S2_DN,D_DN)):
        d=act(path); pr=get_props(d); build_hose(path,Rc,s2,D,pr.get("TITLE",""),pr.get("SPEC","").replace(HOSE_SPEC,""),rebuild=True)
# ---------- 1. 파트 ----------
if STAGE in ("all","parts"):
    build_hose(P_UP,RC_UP,S2_UP,D_UP,"HOSE 32A (상승 상태, 고리 폭 190) — YASUNG HSPF-032",
        f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 상승(낙차 {D_UP:.1f}): 바브 {STUB:.1f} + 직선 {S1:.0f} + 나선 1회전 Rc {RC_UP:.1f}(피치 {PITCH:.0f}, 고리 바깥 폭 {2*RC_UP+41:.0f}) + 직선 {S2_UP:.0f} + 바브. Rc = 내경의 {RC_UP/32:.2f}배.")
    build_hose(P_DN,RC_DN,S2_DN,D_DN,f"HOSE 32A (하강 상태, 고리 폭 {2*RC_DN+41:.0f}) — YASUNG HSPF-032",
        f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 하강(낙차 {D_DN:.1f}): 바브 + 직선 {S1:.0f} + 나선 1회전 Rc {RC_DN:.1f}(피치 {PITCH:.0f}, 고리 바깥 폭 {2*RC_DN+41:.0f}) + 직선 {S2_DN:.0f} + 바브. Rc = 내경의 {RC_DN/32:.2f}배.")
    # 이동판 J5l → J5m: 외곽 x −45 → −75, 소켓 Ø49 (0,0) → (−45,0)
    if not os.path.exists(P_J5M):
        d=act(P_J5L)
        if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
        for s in list(pv(sk,"GetSketchSegments") or []):
            ty=s.GetType() if callable(s.GetType) else s.GetType
            if ty==0: s.Select4(True,NOD); n+=1                       # 외곽선 4개
            elif ty==1:
                cx,cy,r=circ_xy(s)
                if abs(cx)<0.01 and abs(cy)<0.01 and abs(r-24.5)<0.01: s.Select4(True,NOD); n+=1   # 소켓 구멍
        d.Extension.DeleteSelection2(0); print("  J5l deleted segs",n)
        sm=d.SketchManager; sm.AddToDB=True
        sm.CreateCornerRectangle(mm(-75),mm(-270),0,mm(135),mm(270),0); sm.CreateCircleByRadius(mm(XOFF),0,0,mm(24.5)); sm.AddToDB=False
        try:
            rm=d.SketchManager.ActiveSketch.RelationManager
            for rel in list(pv(rm,"GetRelations",1) or []): rm.DeleteRelation(rel)
        except Exception as ex: print("  relation cleanup skipped",ex)
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False)
        bx=bbox(d); print("  J5m box",bx,"ww",ww(d),"orphans",orphan_sketches(d)); assert bx==[-75.0,-270.0,-8.0,135.0,270.0,0.0] and not ww(d) and not orphan_sketches(d), bx
        pr=get_props(d); sp=pr.get("SPEC","").replace("180×540(x −45~135, y ±270)","210×540(x −75~135, y ±270)").replace("Ø49(0,0)","Ø49(−45,0)")
        set_props(d,{"TITLE":pr.get("TITLE","").replace("180","210") if pr.get("TITLE") else "MOVING PLATE 210x540 t8","SPEC":sp,"DATE":DATE,"REMARK":"자작(판재 절단·탭). 호스 고리(나선) 나가는 다리 x −45에 맞춰 소켓 위치 이동, 앞 30 연장."})
        e=I4(); w=I4(); ok=d.Extension.SaveAs(P_J5M,0,1,NOD,e,w); print("  SaveAs J5m",ok,e.value,w.value); assert ok
        rep["J5m_spec"]=sp
# ---------- 2. 어셈블리 ----------
if STAGE in ("all","asm","verify","interf"):
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
    def xf_ok(comp,R_exp,t_exp):
        a.EditRebuild3; x=xform(comps()[comp]); dR=max(abs(x["R"][i][j]-R_exp[i][j]) for i in range(3) for j in range(3)); dt=max(abs(p-q) for p,q in zip(x["t_mm"],t_exp))
        return dR<1e-3 and dt<0.02, x
    def plane_mate(base,part,R,t_rel,t_exp,tag):
        made=[]; c=comps()[part]
        if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
        for k in range(3):
            n=R[k]; j=max(range(3),key=lambda i:abs(n[i])); assert abs(n[j])>0.999,(part,R); sign=1 if n[j]>0 else -1
            off=t_rel[j]; name=f"{tag}_{'xyz'[j]}"
            if name in EXIST: print("   skip",name); continue
            variants=[(0 if sign>0 else 1,False),(1 if sign>0 else 0,False)] if abs(off)<1e-6 else [(0 if sign>0 else 1,False),(0 if sign>0 else 1,True),(1 if sign>0 else 0,False),(1 if sign>0 else 0,True)]
            done=False
            for al,fl in variants:
                a.ClearSelection2(True); assert sel_plane(part,k,False),(part,k); assert sel_plane(base,j,True),(base,j)
                if abs(off)<1e-6: ok,e,f=add_mate(0,al,False,0,name)
                else: ok,e,f=add_mate(5,al,fl,abs(off)/1000,name)
                if not ok:
                    print("   mate fail",name,e); nm=mate_names()
                    if nm and nm[-1] not in EXIST and re.fullmatch(r"(거리|일치|동심|각도)\d+",nm[-1]): del_mate(nm[-1])
                    continue
                good,x=xf_ok(part,R,t_exp)
                if good and not ww(a): made.append(name); done=True; break
                print("   retry",name,al,fl,x["t_mm"],ww(a)); del_mate(name)
            assert done,("plane mate failed",name)
        g,x=xf_ok(part,R,t_exp); print(f"  {part[:44]:44s} {made} ok={g} t={x['t_mm']}"); return g
    I3=[[1,0,0],[0,1,0],[0,0,1]]
if STAGE in ("all","asm"):
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    J5=[n for n in cc if n.startswith("J5m_")]; assert J5, [n for n in cc if n.startswith("J5")]; J5=J5[0]; print("plate comp",J5)
    tj=xform(cc[J5])["t_mm"]; assert abs(tj[2]-ZP_UP)<0.02, tj
    # 이동측 소켓·노즐·호스니플 x 메이트: 일치(x 0) → 거리 45 (−x 쪽)
    MOV={"G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP-1":"이동_G13g-1_x","G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-2":"이동_G13f-2_x","H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP-2":"이동_H16d-2_x"}
    EXIST=set(mate_names())
    for comp,mname in MOV.items():
        x0=xform(cc[comp]); t_exp=[XOFF,x0["t_mm"][1],x0["t_mm"][2]]
        del_mate(mname); a.EditRebuild3; EXIST=set(mate_names()); done=False
        for al,fl in ((0,False),(0,True),(1,False),(1,True)):
            a.ClearSelection2(True); assert sel_plane(comp,0,False) and sel_plane(J5,0,True)
            ok,e,f=add_mate(5,al,fl,abs(XOFF)/1000,mname)
            if not ok: continue
            g,x=xf_ok(comp,x0["R"],t_exp)
            if g and not ww(a): done=True; print(f"  {comp[:40]} x -> {x['t_mm']}"); break
            del_mate(mname)
        assert done, comp
        EXIST=set(mate_names())
    # 호스: J19k 삭제 → J19m 삽입(원점 (0,0,−154.6), R 단위)
    cc=comps(); old=[n for n in cc if n.startswith("J19k_")]; print("delete",old)
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3
    for p in (P_UP,P_DN):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; EXIST=set(mate_names()); inserted=[]
    for p,tag in ((P_UP,"고정_J19mup"),(P_DN,"고정_J19mdn")):
        t=[0.0,0.0,HOSE_TOP]; c=a.AddComponent5(p,0,"",False,"",mm(t[0]),mm(t[1]),mm(t[2])); assert c is not None,p
        arr=[1.0,0,0,0,1.0,0,0,0,1.0]+[mm(t[0]),mm(t[1]),mm(t[2]),1.0,0.0,0.0,0.0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
        assert plane_mate(J1C,c.Name2,I3,t,t,f"{tag}-{c.Name2.rsplit('-',1)[1]}"); EXIST=set(mate_names()); inserted.append(c.Name2)
    up=[n for n in inserted if "up_loop" in n][0]; dn=[n for n in inserted if "dn_loop" in n][0]
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); want_up = cfg in ("상승","1.상승했을때(해석)")
        for n,on in ((up,want_up),(dn,not want_up)):
            c=cc[n]; st=c.GetSuppression2
            if on and st!=2: c.SetSuppression2(2)
            if (not on) and st!=0: c.SetSuppression2(0)
        a.EditRebuild3; cc=comps(); assert cc[up].GetSuppression2==(2 if want_up else 0) and cc[dn].GetSuppression2==(0 if want_up else 2)
    a.ShowConfiguration2("상승"); a.EditRebuild3; rep["inserted"]=inserted
if STAGE in ("all","asm","verify"):
    out={}
    for cfg in ("상승","하강"):
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); row={n:(xform(c)["t_mm"],box(c),c.GetSuppression2) for n,c in cc.items()}; out[cfg]=row
        print(f"[{cfg}] ww {ww(a)}")
        for n,(t,b,s) in sorted(row.items()):
            if s==2 and n.startswith(("J19m","J5m","G13f","G13g","H16d","F4")): print(f"   {n[:46]:46s} t={t} box={b}")
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
    json.dump(out,open(os.path.join(VER,"stroke150c_asm_positions_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
if STAGE in ("all","asm","interf"):
    for cfg in ("상승","하강"):
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); a.ClearSelection2(True)
        idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
        res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
        print(f"[{cfg}] interferences {len(res)}")
        for cs,v in res:
            if v>0.05: print("   ",v,[c[:40] for c in cs])
        rep[f"interf_{cfg}"]=res
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
json.dump(rep,open(os.path.join(VER,f"stroke150c_0917_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("DONE",STAGE)
