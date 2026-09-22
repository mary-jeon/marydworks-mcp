# 2026-09-22 사용자 지시: 하강 시 호스(이동판 전체)가 22.21 더 내려가게 — A안(TA2-2H-150 유지, 행정 전체를 22.21 아래로)
#   고정 러그 J8g(40x23, 핀 @16) -> J8h(40x45.21, 핀 @38.21) 신규, TA2 B9k·후단 핀 G11f z 26 -> 48.21, 거리_상승 360 -> 382.21 / 거리_하강 510 -> 532.21
#   가이드 봉 J2d PSSFAQ20-580 -> J2e PSSFAQ20-605 (부시 하강 하단 -604.21 이 봉 끝 -590 을 넘으므로), 호스 J19n -> J19o (낙차 +22.21, 자유길이 552 -> 574)
# usage: down22_0922.py backup | parts | asm | station | finalize
import os, sys, json, math, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv, _wrap
STAGE=sys.argv[1]; mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-22"; rep={"stage":STAGE}
DROP=22.21
ZP_UP0,ZP_DN0=-360.0,-510.0; ZP_UP=ZP_UP0-DROP; ZP_DN=ZP_DN0-DROP
LUG_H0,PIN_H0=23.0,16.0; LUG_H=LUG_H0+DROP; PIN_H=PIN_H0+DROP; LUG_W=40.0; LUG_T=5.8; PIN_D=8.0
TA2_Z0=26.0; TA2_Z=TA2_Z0+DROP
SH_L0,SH_B=580.0,13.0; SH_L=605.0; SH_EXT0=SH_L0+SH_B; SH_EXT=SH_L+SH_B
P_J8G=Zp("J8g_lug_PL5.8_40x23_pin16.SLDPRT"); P_J8H=Zp("J8h_lug_PL5.8_40x45_pin38.SLDPRT")
P_J2D=Zp("J2d_guide_shaft_MISUMI_PSSFAQ20-580-B13_catalog.SLDPRT"); P_J2E=Zp("J2e_guide_shaft_MISUMI_PSSFAQ20-605-B13_catalog.SLDPRT")
P_UP0=Zp("J19n_hose_YASUNG_HSPF-032_up_loop190.SLDPRT"); P_DN0=Zp("J19n_hose_YASUNG_HSPF-032_dn_loop142.SLDPRT")
BK=r"<MCP_DIR>\_backup\20260922-down22"
# ---- 호스 기하(stroke150_d_hose_0917.py 와 동일 규약, ZP 만 변경) ----
HOSE_TOP=-154.6; STUB=52.4; HB=lambda zp: zp-15+20.4+14.2
PITCH=45.0; S1=50.0; RC_UP=(190.0-41.0)/2; XOFF=0.0; YOFF=PITCH; EX,EY=-1.0,0.0
D_UP=HOSE_TOP-HB(ZP_UP); D_DN=HOSE_TOP-HB(ZP_DN)
def loop_len(Rc,N=720):
    L=0.0; prev=None
    for i in range(N+1):
        ph=2*math.pi*i/N; k=(ph-math.sin(ph))/(2*math.pi); pt=(EX*Rc*(1-math.cos(ph))+XOFF*k, EY*Rc*(1-math.cos(ph))+YOFF*k, -Rc*math.sin(ph))
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
W_DN=2*RC_DN+41
print(f"hose: D {D_UP:.2f}/{D_DN:.2f} Lf {LF:.1f} cut {L_HOSE:.0f} | up Rc {RC_UP} w {2*RC_UP+41:.0f} s2 {S2_UP:.2f} | dn Rc {RC_DN:.2f} w {W_DN:.0f} s2 {S2_DN:.2f}")
rep["hose"]=dict(D_UP=D_UP,D_DN=D_DN,Lf=LF,cut=L_HOSE,Rc_up=RC_UP,Rc_dn=RC_DN,s2_up=S2_UP,s2_dn=S2_DN)
P_UP=Zp("J19o_hose_YASUNG_HSPF-032_up_loop190.SLDPRT"); P_DN=Zp(f"J19o_hose_YASUNG_HSPF-032_dn_loop{W_DN:.0f}.SLDPRT")
HOSE_SPEC="야성하이텍 슈퍼스프링호스(무독) HSPF-032: 내경 32.0±1.0·외경 41.0±1.0·0.5/2.5 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 3D 내경은 바브(Ø34) 위 늘어난 34로 표현. 최소 굽힘반경 카탈로그 미기재."
AREA=math.pi*(20.5**2-17.0**2)
if STAGE=="backup":
    os.makedirs(BK,exist_ok=True)
    for p in (ASM,P_J8G,P_J2D,P_UP0,P_DN0):
        shutil.copy2(p,os.path.join(BK,os.path.basename(p))); print("backup",os.path.basename(p),os.path.getsize(p))
    rep["backup"]=os.listdir(BK); json.dump(rep,open(os.path.join(VER,"down22_0922_backup.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1); print("DONE backup"); sys.exit(0)
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def last_sketch(d): return [n for n,t in feats(d) if t=="ProfileFeature"][-1]
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
def volume(d): return d.Extension.CreateMassProperty.Volume*1e9
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
def save_new(d,path,copy=False):
    assert not clean_orphans(d); e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,(3 if copy else 1),NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d)); assert ok
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def close_unsaved_new():
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith(("파트","Part")): app.CloseDoc(tt); print("closed unsaved",tt)
def sel_plane_p(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def origin_sel(d,append):
    for nm in ("Point1@원점","Point1@Origin"):
        if d.Extension.SelectByID2(nm,"EXTSKETCHPOINT",0,0,0,append,0,NOD,0): return True
    return False
def rel(d,kind,*ents):
    d.ClearSelection2(True)
    for i,e in enumerate(ents): assert e.Select4(i>0,NOD),kind
    d.SketchAddConstraints(kind); d.ClearSelection2(True)
def rel_o(d,kind,e):
    d.ClearSelection2(True); assert e.Select4(False,NOD); assert origin_sel(d,True); d.SketchAddConstraints(kind); d.ClearSelection2(True)
def dim(d,name,e1,e2,at,how="d"):
    d.ClearSelection2(True); assert e1.Select4(False,NOD)
    if e2=="origin": assert origin_sel(d,True)
    elif e2 is not None: assert e2.Select4(True,NOD)
    fn={"d":d.AddDimension2,"h":d.AddHorizontalDimension2,"v":d.AddVerticalDimension2}[how]
    dd=fn(at[0],at[1],0.0); d.ClearSelection2(True); assert dd is not None,name
    dm=dd.GetDimension2(0); dm.Name=name; return round(dm.SystemValue*1000,3)
def sk_map(sk,conv=0):
    a=list(sk.ModelToSketchTransform.ArrayData); R=[a[0:3],a[3:6],a[6:9]]; t=a[9:12]
    if conv==0: return lambda px,py,pz:[(R[i][0]*px+R[i][1]*py+R[i][2]*pz)+t[i] for i in range(3)][:2]
    return lambda px,py,pz:[(R[0][i]*px+R[1][i]*py+R[2][i]*pz)+t[i] for i in range(3)][:2]
def sketch_xy(sk,px,py,pz,conv): return sk_map(sk,conv)(px,py,pz)
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
def loop_points(Rc):
    z0=-(STUB+S1); N=96; pts=[]
    for i in range(N+1):
        ph=2*math.pi*i/N; k=(ph-math.sin(ph))/(2*math.pi); pts.append((EX*Rc*(1-math.cos(ph))+XOFF*k, EY*Rc*(1-math.cos(ph))+YOFF*k, z0-Rc*math.sin(ph)))
    return pts,z0
def build_hose(path,Rc,D,title,spec_add):
    if os.path.exists(path): print("  exists",os.path.basename(path)); return
    pts,z0=loop_points(Rc); zend=-D; L=(STUB+S1)+loop_len(Rc)+(z0-zend); print(f"  loop pts {len(pts)} path length {L:.1f} (target {L_HOSE:.1f})"); assert abs(L-L_HOSE)<1.0,(L,L_HOSE)
    close_unsaved_new(); d=app.NewDocument(tmpl,0,0,0)
    ring=lambda sm,cx=0.0,cy=0.0:(sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(20.5)),sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(17.0)))
    assert sel_plane_p(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; ring(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch(d); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(-z0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f,"stub1"; f.Name="직선_상단"
    bx=bbox(d); assert abs(bx[2]-z0)<0.05 and abs(bx[5])<0.05, bx
    d.SketchManager.Insert3DSketch(True); d.SketchManager.AddToDB=True
    arr=[]
    for q in pts: arr+=[mm(q[0]),mm(q[1]),mm(q[2])]
    sp=d.SketchManager.CreateSpline2(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr),False); d.SketchManager.AddToDB=False; assert sp is not None,"spline"
    d.SketchManager.Insert3DSketch(True); d.ClearSelection2(True); path_sk=[n for n,t in feats(d) if t=="3DProfileFeature"][-1]
    f=None
    for conv in (0,1):
        assert sel_face_at(d,z0,(18.7,0.0)),"stub1 end face"
        d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; cx,cy=sketch_xy(sk,0.0,0.0,mm(z0),conv)
        sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(cx,cy,0,mm(20.5)); sm.CreateCircleByRadius(cx,cy,0,mm(17.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        prof_sk=last_sketch(d)
        d.ClearSelection2(True); assert d.Extension.SelectByID2(prof_sk,"SKETCH",0,0,0,False,1,NOD,0); assert d.Extension.SelectByID2(path_sk,"SKETCH",0,0,0,True,4,NOD,0)
        f=d.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False); d.EditRebuild3
        v=volume(d) if (f is not None and len(bodies(d))==1) else None; v_exp=AREA*((-z0)+loop_len(Rc)); print(f"  loop conv {conv} center ({cx*1000:.2f},{cy*1000:.2f}) vol {None if v is None else round(v)} exp {round(v_exp)}")
        if v and abs(v-v_exp)/v_exp<0.015 and not ww(d): f.Name="고리_스윕"; break
        if f is not None: f.Select2(False,0); d.EditDelete(); d.EditRebuild3
        f=None; clean_orphans(d)
    assert f,"loop sweep"
    f=None
    for conv in (0,1):
        assert sel_face_at(d,z0,(XOFF+18.7,YOFF)),"loop end face"
        d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; cx,cy=sketch_xy(sk,mm(XOFF),mm(YOFF),mm(z0),conv)
        sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(cx,cy,0,mm(20.5)); sm.CreateCircleByRadius(cx,cy,0,mm(17.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        skn=last_sketch(d)
        for dirn in (True,False):
            d.ClearSelection2(True); d.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
            f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(z0-zend),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
            if f is None: continue
            v=volume(d) if len(bodies(d))==1 else None; v_exp=AREA*L_HOSE; endface=sel_face_at(d,zend,(XOFF+18.7,YOFF)); d.ClearSelection2(True)
            print(f"  stub2 conv {conv} dirn {dirn} vol {None if v is None else round(v)} exp {round(v_exp)} endface {endface}")
            if v and abs(v-v_exp)/v_exp<0.015 and endface and len(bodies(d))==1: f.Name="직선_하단"; break
            f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
        if f is not None: break
        clean_orphans(d)
    assert f,"stub2"
    bx=bbox(d); print("  hose box(loose)",bx,"vol",round(volume(d)),"ww",ww(d)); assert not ww(d)
    set_props(d,{"TITLE":title,"SPEC":HOSE_SPEC+spec_add,"Material":"PVC","QT'Y":"1","DATE":DATE,"REMARK":"구매품(야성판매). 접힌 고리 폭 상승 시 190. 고리는 나선 1회전(−x 앞쪽, 피치 45를 +y로 φ−sinφ 분배해 양단 접선 수직), 나가는 다리 (0,+45)(이동판 소켓 위치). 이동판 행정을 22.21 내린 뒤(상승 −382.21/하강 −532.21) 낙차에 맞춰 J19n을 대체. 실물은 자중·강선 탄성으로 형상이 달라질 수 있음."},mat="PVC 경질")
    save_new(d,path); app.CloseDoc(d.GetTitle)
old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
try:
    # ================= 1. 파트 =================
    if STAGE=="parts":
        # (a) 고정 러그 J8h: 윗면(XZ) 스케치 사각 40 x 45.21(z 0 -> -45.21) + Ø8 @ z -38.21, +y 5.8 돌출. 좌표계 = J8g 와 동일(box [-20,0,-45.21, 20,5.8,0])
        if not os.path.exists(P_J8H):
            close_unsaved_new(); d=app.NewDocument(tmpl,0,0,0); g={}; f=None
            for conv in (1,0):      # 윗면 스케치의 ModelToSketchTransform 규약(전치 여부)은 bbox 로 판정
                assert sel_plane_p(d,"윗면"); d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; S=sk_map(sk,conv); sm=d.SketchManager
                p1=S(mm(-LUG_W/2),0,0); p2=S(mm(LUG_W/2),0,mm(-LUG_H)); pc=S(0,0,mm(-PIN_H))
                sm.AddToDB=True; rect=sm.CreateCornerRectangle(p1[0],p1[1],0,p2[0],p2[1],0); ci=sm.CreateCircleByRadius(pc[0],pc[1],0,mm(PIN_D/2)); sm.AddToDB=False
                segs=[_wrap(x) for x in (rect or [])]; print('  rect segs',len(segs),'conv',conv)
                def sp_(seg): return pv(seg,"GetStartPoint2"),pv(seg,"GetEndPoint2")
                lines=[s_ for s_ in segs if pv(s_,"GetType")==0]; assert len(lines)==4,len(lines)
                oy=S(0,0,0)[1]; top=[s_ for s_ in lines if all(abs(pv(q,"Y")-oy)<1e-9 for q in sp_(s_))]; assert len(top)==1,len(top); top=top[0]
                side=[s_ for s_ in lines if s_ is not top and abs(pv(sp_(s_)[0],"X")-pv(sp_(s_)[1],"X"))<1e-9]; assert len(side)==2,len(side); side=side[0]
                assert abs(S(0,0,1.0)[1]-S(0,0,0)[1])>0.5,"expect model Z along sketch vertical on Top plane"
                rel_o(d,"sgATMIDDLE",top)
                d.ClearSelection2(True); pv(ci,"GetCenterPoint2").Select4(False,NOD); origin_sel(d,True); d.SketchAddConstraints("sgVERTICALPOINTS2D"); d.ClearSelection2(True)
                g["러그_폭"]=dim(d,"러그_폭",top,None,(S(0,0,mm(6))[0],S(0,0,mm(6))[1]),"h")
                g["러그_높이"]=dim(d,"러그_높이",side,None,(S(mm(28),0,mm(-LUG_H/2))[0],S(mm(28),0,mm(-LUG_H/2))[1]),"v")
                g["핀구멍_Ø8_H7"]=dim(d,"핀구멍_Ø8_H7",ci,None,(S(mm(9),0,mm(-PIN_H-9))[0],S(mm(9),0,mm(-PIN_H-9))[1]))
                g["핀_높이"]=dim(d,"핀_높이",pv(ci,"GetCenterPoint2"),"origin",(S(mm(-30),0,mm(-PIN_H/2))[0],S(mm(-30),0,mm(-PIN_H/2))[1]),"v")
                st=sk.GetConstrainedStatus; print("  lug sketch status",st,g); d.SketchManager.InsertSketch(True); d.ClearSelection2(True); skn=last_sketch(d); d.FeatureByName(skn).Name="러그_스케치"
                for dirn in (False,True):
                    d.ClearSelection2(True); assert d.Extension.SelectByID2("러그_스케치","SKETCH",0,0,0,False,0,NOD,0)
                    f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(LUG_T),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
                    if f is None: continue
                    bx=bbox(d); print("  lug extrude conv",conv,"dirn",dirn,bx)
                    if abs(bx[1])<0.01 and abs(bx[4]-LUG_T)<0.01 and abs(bx[2]+LUG_H)<0.01 and abs(bx[5])<0.01 and abs(bx[0]+LUG_W/2)<0.01: f.Name="러그_t5.8"; break
                    f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
                if f is not None: break
                # 이 규약은 틀림 -> 스케치 삭제 후 다른 규약
                d.ClearSelection2(True)
                if d.Extension.SelectByID2("러그_스케치","SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
                d.EditRebuild3; assert not bodies(d)
            assert f,"lug extrude"; assert st==3,("lug sketch not fully defined",st)
            vol=volume(d); calc=(LUG_W*LUG_H-math.pi/4*PIN_D**2)*LUG_T; print("  lug vol",round(vol,1),"calc",round(calc,1),"ww",ww(d)); assert abs(vol-calc)<1.0 and not ww(d)
            pr0=get_props(act(P_J8G)); app.ActivateDoc3(d.GetTitle,False,0,I4()); d=app.ActiveDoc
            set_props(d,{"TITLE":f"LUG PL5.8 40x{LUG_H:.2f} (고정판 밑, TA2 후단 클레비스 핀 @{PIN_H:.2f})",
                "SPEC":f"PL 6T STS304 → 두께 5.8 ±0.05 기계가공(TA2 후단 CNC 슬롯 6.0 삽입 틈 0.15~0.25), 40(x)×{LUG_H:.2f}(z), 핀 구멍 Ø8 H7(+0.015/0) 중심 판 밑면 아래 {PIN_H:.2f}. 고정판 J1d 밑면 (85,0)에 필릿 용접.",
                "Material":"STS304","QT'Y":"1","DATE":DATE,"TOLERANCE":pr0.get("TOLERANCE","두께 5.8 ±0.05(f급) — TA2 슬롯 6.0. 핀 구멍 Ø8 H7 — 핀 SHCCG8-22.8 g6 틈 0.005~0.029. 일반공차 KS B ISO 2768-1 m(JIS B 0405 m 원문)."),
                "REMARK":f"자작. J8g(40×23, 핀 @16) 대체 — 이동판 행정을 22.21 내리기 위해(TA2-2H-150 유지) 후단 핀을 22.21 아래로. 핀 높이 {PIN_H:.2f} ±0.2."},mat="STS 304")
            save_new(d,P_J8H); rep["J8h"]={"dims":g,"status":st,"vol":round(vol,1),"calc":round(calc,1),"box":bbox(d)}; app.CloseDoc(d.GetTitle)
        # (b) 가이드 봉 J2e: J2d 를 복사본으로 저장 -> 돌출 593 -> 618 (L605 + B13)
        if not os.path.exists(P_J2E):
            d=act(P_J2D); e=I4(); w=I4(); ok=d.Extension.SaveAs(P_J2E,0,3,NOD,e,w); print("  copy J2d -> J2e",ok,e.value,w.value); assert ok and os.path.exists(P_J2E)
            d=act(P_J2E); assert d.GetTitle.startswith("J2e"), d.GetTitle
            dm=d.Parameter("D1@봉_Ø20_L593"); assert dm is not None; r=dm.SetSystemValue3(mm(SH_EXT),2,None); d.ForceRebuild3(False); bx=bbox(d); print("  J2e dim set",r,"box",bx); assert abs(bx[2]+SH_EXT)<0.01 and abs(bx[5])<0.01,bx
            d.FeatureByName("봉_Ø20_L593").Name=f"봉_Ø20_L{SH_EXT:.0f}"
            pr=get_props(d)
            set_props(d,{"TITLE":f"GUIDE SHAFT Ø20 L{SH_L:.0f} (한쪽 M20 나사 13) — MISUMI PSSFAQ20-{SH_L:.0f}-B13","SPEC":f"MISUMI PSSFAQ20-{SH_L:.0f}-B13","DATE":DATE,
                "REMARK":f"구매품. PSSFAQ20-{SH_L:.0f}. J2d(L580) 대체 — 이동판 행정 22.21 하향으로 하강 시 부시 하단(−604.21)이 봉 끝(−590)을 넘어 L 605(봉 끝 −615, 여유 10.8). L 605가 MISUMI 지정 가능 길이(1 mm 단위)인지 발주 전 확인."})
            e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved J2e",e.value,w.value,"ww",ww(d)); rep["J2e"]={"box":bx,"orphans":orphan_sketches(d)}; app.CloseDoc(d.GetTitle)
        # (c) 호스 J19o up / dn
        build_hose(P_UP,RC_UP,D_UP,"HOSE 32A (상승 상태, 고리 폭 190) — YASUNG HSPF-032",
            f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 상승(낙차 {D_UP:.1f}): 바브 {STUB:.1f} + 직선 {S1:.0f} + 나선 1회전 Rc {RC_UP:.1f}(−x 쪽, 피치 +y {PITCH:.0f}, 고리 바깥 폭 {2*RC_UP+41:.0f}) + 직선 {S2_UP:.0f} + 바브. Rc = 내경의 {RC_UP/32:.2f}배.")
        build_hose(P_DN,RC_DN,D_DN,f"HOSE 32A (하강 상태, 고리 폭 {W_DN:.0f}) — YASUNG HSPF-032",
            f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 하강(낙차 {D_DN:.1f}): 바브 + 직선 {S1:.0f} + 나선 1회전 Rc {RC_DN:.1f}(−x 쪽, 피치 +y {PITCH:.0f}, 고리 바깥 폭 {W_DN:.0f}) + 직선 {S2_DN:.0f} + 바브. Rc = 내경의 {RC_DN/32:.2f}배.")
        for p in (P_UP,P_DN):
            d=act(p); rep[os.path.basename(p)]={"box":bbox(d),"vol":round(volume(d)),"orphans":orphan_sketches(d),"ww":ww(d)}; print("  ",os.path.basename(p),rep[os.path.basename(p)]); app.CloseDoc(d.GetTitle)
    # ================= 2. 어셈블리 =================
    if STAGE in ("asm","verify"):
        a=app.GetOpenDocumentByName(ASM) or open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
        def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
        def mates_iter():
            f=pv(a,"FirstFeature")
            while f is not None:
                if pv(f,"GetTypeName2")=="MateGroup":
                    sf=f.GetFirstSubFeature
                    while sf is not None: yield sf; sf=sf.GetNextSubFeature
                f=pv(f,"GetNextFeature")
        def set_mate_dist(name,val):
            m=[x for x in mates_iter() if x.Name==name]; assert len(m)==1,name; m=m[0]
            dm=a.Parameter(f"D1@{name}"); assert dm is not None,name; old=round(dm.SystemValue*1000,3)
            r=dm.SetSystemValue3(mm(val),2,None); a.EditRebuild3; new=round(a.Parameter(f"D1@{name}").SystemValue*1000,3); print(f"  mate {name}: {old} -> {new} (r={r})"); return old,new
        def replace(prefix,newpath,tag_old,tag_new):
            a.ShowConfiguration2("상승"); a.EditRebuild3; root=cm.ActiveConfiguration.GetRootComponent3(True)
            old=[c for c in pv(root,"GetChildren") if c.Name2.startswith(prefix)]; print("  replace",[c.Name2 for c in old],"->",os.path.basename(newpath))
            if not old: return
            a.ClearSelection2(True)
            for i,c in enumerate(old): c.Select4(i>0,NOD,False)
            ok=a.ReplaceComponents2(newpath,"",True,0,True); print("   ReplaceComponents2",ok); a.ClearSelection2(True); a.ForceRebuild3(False)
            for sf in mates_iter():
                if tag_old in sf.Name: sf.Name=sf.Name.replace(tag_old,tag_new)
        if STAGE=="asm":
            a.ShowConfiguration2("상승"); a.EditRebuild3
            rep["mates"]={}
            for name,val in (("거리_상승",-ZP_UP),("거리_하강",-ZP_DN),("고정_B9k-1_z",TA2_Z),("고정_G11f-1_z",TA2_Z)): rep["mates"][name]=set_mate_dist(name,val)
            replace("J8g_",P_J8H,"J8g","J8h"); replace("J2d_",P_J2E,"J2d","J2e")
            replace("J19n_hose_YASUNG_HSPF-032_up",P_UP,"J19n","J19o"); replace("J19n_hose_YASUNG_HSPF-032_dn",P_DN,"J19n","J19o")
            # 러그 J8h 위치 = J8g 와 동일 메이트(고정_J8h-1_x 85 / y 2.9 / z 10) 그대로; 구성별 호스 억제 상태 확인·보정
            for cfg in CFGS:
                a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); want_up=cfg in ("상승","1.상승했을때(해석)")
                up=[n for n in cc if n.startswith("J19o_") and "up_loop" in n]; dn=[n for n in cc if n.startswith("J19o_") and "dn_loop" in n]; assert len(up)==1 and len(dn)==1,(up,dn)
                for n,on in ((up[0],want_up),(dn[0],not want_up)):
                    c=cc[n]; st=c.GetSuppression2
                    if on and st!=2: c.SetSuppression2(2); print("   unsuppress",cfg,n)
                    if (not on) and st!=0: c.SetSuppression2(0); print("   suppress",cfg,n)
                a.EditRebuild3
        # ---- 검증(asm·verify 공통): 위치·오류·간섭 ----
        out={}
        for cfg in CFGS:
            a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); w_=ww(a); row={"ww":w_}
            pos={n:(xform(c)["t_mm"],box(c),c.GetSuppression2) for n,c in cc.items() if n.startswith(("J5p","J8h","J8g","B9k","G11f","J11e","J9f","J2e","J2d","J19o","J19n","B10b","H16d","G13f","F4"))}
            row["pos"]={n:v for n,v in pos.items()}
            zp=[v[0][2] for n,v in pos.items() if n.startswith("J5p")][0]; row["ZP"]=zp
            print(f"[{cfg}] ww {w_} ZP {zp}")
            for n,(t,b,s) in sorted(pos.items()):
                if s==2 or n.startswith(("J19",)): print(f"   {n[:50]:50s} supp {s} t={t} box={b}")
            a.ClearSelection2(True); idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
            itf=sorted([([c_.Name2[:26] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r_:-r_[1]); idm.Done(); a.ClearSelection2(True)
            row["interf"]=itf; print(f"   interferences {len(itf)}:",[(v,cs) for cs,v in itf if v>0.05][:12])
            out[cfg]=row
        a.ShowConfiguration2("상승"); a.ForceRebuild3(False); rep["asm"]=out
        exp_up=ZP_UP; exp_dn=ZP_DN
        assert abs(out["상승"]["ZP"]-exp_up)<0.02 and abs(out["하강"]["ZP"]-exp_dn)<0.02,(out["상승"]["ZP"],out["하강"]["ZP"])
    # ================= 3. 스테이션 검사(S00000MU0: 사용자 창, 저장 안 함) =================
    if STAGE=="station":
        a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
        if a.GetSaveFlag:
            e=I4(); w=I4(); ok=a.Save3(1,e,w); print("saved 염수주입라인.SLDASM",ok,e.value,w.value); assert ok
        GROUND=1109.0
        LINE=("B9k","J25a","J8h","J9f","G11f","J11e","G3e","B4e","G13f","G13g","H16d","J19o","J5p","J1d","J2e","B10b","F4")
        PS=Zp("S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PS); assert s is not None; app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager; cfg0=scm.ActiveConfiguration.Name
        print("station cfg0",cfg0,"cfgs",list(pv(s,"GetConfigurationNames")))
        def leaves():
            out=[]
            def walk(c,depth):
                for ch in (pv(c,"GetChildren") or []):
                    if ch.GetSuppression2!=2: continue
                    kids=pv(ch,"GetChildren")
                    if kids in (None,()): out.append((ch.Name2,ch))
                    elif depth<8: walk(ch,depth+1)
            walk(scm.ActiveConfiguration.GetRootComponent3(True),0); return out
        def below(bx,others,margin,depth_lim):
            res=[]
            for n,b in others:
                if b is None: continue
                if b[1]>bx[4]+margin or b[4]<bx[1]-margin or b[2]>bx[5]+margin or b[5]<bx[2]-margin: continue
                gap=b[0]-bx[3]
                if -30<=gap<=depth_lim: res.append((round(gap,2),n,b))
            return sorted(res)
        short=lambda n:n.split("/")[-1]
        for cfg in ("하강","상승"):
            s.ShowConfiguration2(cfg); s.ForceRebuild3(False); lv=leaves()
            line=[(n,c) for n,c in lv if short(n).startswith(LINE)]; others=[(n,c) for n,c in lv if not short(n).startswith(LINE)]
            lb={short(n):box(c) for n,c in line}; ob=[(n,box(c)) for n,c in others]
            print(f"\n[station {cfg}] line parts {len(line)} others {len(others)}")
            row={"line_boxes":lb,"below":{}}
            for key in ("J5p","J2e","G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP-2","J19o","B10b","J11e","B9k","J8h"):
                for n,b in lb.items():
                    if not n.startswith(key) or b is None: continue
                    r=below(b,ob,0.0,80.0); row["below"][n]=r
                    print(f"  {n[:50]} x {b[0]:.1f}~{b[3]:.1f} (지상고 {GROUND-b[3]:.1f}~{GROUND-b[0]:.1f})")
                    for gap,on,o in r[:5]: print(f"     gap {gap:7.2f}  {on[-62:]}  x {o[0]:.1f}~{o[3]:.1f} y {o[1]:.0f}~{o[4]:.0f} z {o[2]:.0f}~{o[5]:.0f}")
            s.ClearSelection2(True)
            for n,c in line+others: c.Select4(True,NOD,False)
            idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
            rows=[([short(c_.Name2) for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
            ext=[r for r in rows if any(x.startswith(LINE) for x in r[0]) and not all(x.startswith(LINE) for x in r[0])]
            print(f"[station {cfg}] all {len(rows)} | line<->external {len(ext)}: {ext[:10]}")
            row["ext"]=ext; row["all"]=len(rows); rep[cfg]=row
        s.ShowConfiguration2(cfg0); s.ForceRebuild3(False); print("station cfg restored",scm.ActiveConfiguration.Name,"dirty",s.GetSaveFlag)
    # ================= 4. 마무리: 고아 스케치·저장·창 닫기 =================
    if STAGE=="finalize":
        res={}
        for p in (P_J8H,P_J2E,P_UP,P_DN):
            d=act(p); o=orphan_sketches(d); res[os.path.basename(p)]={"orphans":o,"ww":ww(d),"dirty":d.GetSaveFlag}
            if d.GetSaveFlag: e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved",os.path.basename(p))
            app.CloseDoc(d.GetTitle); print("  closed",os.path.basename(p),res[os.path.basename(p)])
        a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
        if a.GetSaveFlag: e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved 염수주입라인.SLDASM",e.value,w.value)
        # 라인 어셈블리 창은 S00000 이 참조 -> 창만 닫음(문서는 메모리에 남음)
        open_titles=[x.GetTitle for x in (pv(app,"GetDocuments") or [])]; print("open docs with window:",[t for t in open_titles if t.startswith(("J8","J2e","J19o","염수"))])
        for p in (P_J8G,P_J2D,P_UP0,P_DN0):
            dd=app.GetOpenDocumentByName(p)
            if dd is not None: print("  old part still loaded (referenced?)",os.path.basename(p))
        rep["finalize"]=res
        PS=Zp("S00000MU0.SLDASM"); app.ActivateDoc3(PS,False,0,I4()); print("active",app.ActiveDoc.GetTitle)
finally:
    app.SetUserPreferenceToggle(10,old_pref)
json.dump(rep,open(os.path.join(VER,f"down22_0922_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE",STAGE)
