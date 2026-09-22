# 2026-09-17: 사용자 지시 ① TA2 스트로크 85→150(상승 −425 유지, 하강 −510→−575) ② 가이드 샤프트 2→4(앞 x 0 / 뒤 x 90, y ±240) ③ Ø16→Ø20(LHFRW20·PSSFAQ20·SHFSS20, MISUMI 규격표 원문)
#            ④ 상승 호스 U자 폭 114→190(중심선 불룩 149) — 하강도 활(직선 불가: 자유길이 413 > 하강 간격 296)
# 1단계(이 파일): 백업 → 새 파트(B10b 부시·J23d 홀더·J2d 봉·J19j 호스 2) → J1c·J5l 스케치 제자리 편집 → B9h D3 150 → B9i SaveAs
import os, sys, json, math, shutil
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-17"
BK=r"<MCP_DIR>\_backup\20260917-stroke150"
STAGE=sys.argv[1] if len(sys.argv)>1 else "all"
rep={"stage":STAGE}
# ---------- 설계 상수 ----------
ZP_UP=-425.0; ZP_DN=-575.0; STROKE=ZP_UP-ZP_DN            # 150
SH_XS=(0.0,90.0); SH_Y=240.0                              # 4점
BUSH=dict(dr=20,D=32,L=80,H=54,T=8,d=5.5,d1=9,t=5.1,PCD=43)   # LHFRW20 규격표
HOLD=dict(L=60,T=20,H=37,A=34,L1=48,d=7,D1=24,B=22,C=15,M="M5")   # SHFSS20 규격표
SHAFT_L=660; SHAFT_B=13; SHAFT_TOP=3.0                    # PSSFAQ20-660-B13: 전장 673, 상단 z +3(나사 13 = 판 t10 + 3)
HOSE_TOP=-154.6; STUB=52.4; ENG=15.0; HN_THR=20.4; HN_HEX=14.2
HOSE_BOT=lambda zp: zp-ENG+HN_THR+HN_HEX                  # zp+19.6
D_UP=HOSE_TOP-HOSE_BOT(ZP_UP); D_DN=HOSE_TOP-HOSE_BOT(ZP_DN)   # 250.8 / 400.8
G_UP=D_UP-2*STUB; G_DN=D_DN-2*STUB                        # 146 / 296 (자유 구간 양단 간격)
BULGE_UP=190.0-41.0                                       # 사용자 「U자 폭 190」 → 중심선 149
def solve_bow_bulge(gap,bulge):
    th=2*math.atan(bulge/(gap/2)); R=gap/(4*math.sin(th)); return R,th,4*R*th
def solve_bow_len(gap,Lf):
    f=lambda t: math.sin(t)/t-gap/Lf; lo,hi=1e-3,3.0
    for _ in range(200):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    t=(lo+hi)/2; R=Lf/(4*t); return R,t,2*R*(1-math.cos(t))
R_UP,T_UP,LF=solve_bow_bulge(G_UP,BULGE_UP); R_DN,T_DN,BULGE_DN=solve_bow_len(G_DN,LF); L_HOSE=LF+2*STUB
print(f"hose: D_UP {D_UP:.1f} D_DN {D_DN:.1f} | free {LF:.1f} total {L_HOSE:.1f} | up R {R_UP:.1f} θ {math.degrees(T_UP):.1f}° bulge {BULGE_UP:.1f} | dn R {R_DN:.1f} θ {math.degrees(T_DN):.1f}° bulge {BULGE_DN:.1f}")
rep["hose"]=dict(D_UP=D_UP,D_DN=D_DN,Lf=LF,L_total=L_HOSE,R_up=R_UP,th_up_deg=math.degrees(T_UP),bulge_up=BULGE_UP,R_dn=R_DN,th_dn_deg=math.degrees(T_DN),bulge_dn=BULGE_DN)
P_B10=Zp("B10b_linear_bushing_MISUMI_LHFRW20_catalog.SLDPRT")
P_J23=Zp("J23d_shaft_support_MISUMI_SHFSS20_catalog.SLDPRT")
P_J2=Zp(f"J2d_guide_shaft_MISUMI_PSSFAQ20-{SHAFT_L}-B{SHAFT_B}_catalog.SLDPRT")
P_UP=Zp(f"J19j_hose_YASUNG_HSPF-032_up_U190_R{R_UP:.0f}.SLDPRT"); P_DN=Zp(f"J19j_hose_YASUNG_HSPF-032_dn_bow_R{R_DN:.0f}.SLDPRT")
P_J1C=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); P_J5L=Zp("J5l_moving_plate_180x540_t8.SLDPRT")
P_B9H=Zp("B9h_TiMOTION_TA2-2H-085339-5511-010-1.SLDPRT"); P_B9I=Zp("B9i_TiMOTION_TA2-2H-150339-5511-010-1.SLDPRT")
# ---------- 헬퍼 ----------
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def sel_plane(d,nm):
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
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def volume(d):
    mp=d.Extension.CreateMassProperty; return mp.Volume*1e9
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def extrude_neg(d,depth,name):
    f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f, name; f.Name=name; return f
def cut_neg(d,depth,name,through=False):
    T1=1 if through else 0; v0=volume(d); f=None; sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    for dirn in (False,True):
        d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0), sk
        f=d.FeatureManager.FeatureCut4(True,False,dirn,T1,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
        if f is None: continue
        if volume(d)<v0-1e-6: break
        f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
    assert f, name; f.Name=name; return f
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
    orph=[]
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3; orph=orphan_sketches(d); assert not orph, ("orphans remain",orph)
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d),"orphans 0"); assert ok
def circ_xy(s):
    cpt=pv(s,"GetCenterPoint2")
    try: cx,cy=cpt[0]*1000,cpt[1]*1000
    except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
    r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
    return cx,cy,r
def edit_circles(d,sketch,rule,new_circles):
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); assert d.Extension.SelectByID2(sketch,"SKETCH",0,0,0,False,0,NOD,0), sketch; d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
    for s in list(pv(sk,"GetSketchSegments") or []):
        ty=s.GetType() if callable(s.GetType) else s.GetType
        if ty==1:
            cx,cy,r=circ_xy(s)
            if rule(cx,cy,r): s.Select4(True,NOD); n+=1
    if n: d.Extension.DeleteSelection2(0)
    sm=d.SketchManager; sm.AddToDB=True
    for cx,cy,r in new_circles: sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(r))
    sm.AddToDB=False
    try:
        rm=d.SketchManager.ActiveSketch.RelationManager; dang=list(pv(rm,"GetRelations",1) or [])
        for rel in dang: rm.DeleteRelation(rel)
    except Exception as ex: print("  relation cleanup skipped",ex)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); return n
def circles_of(d,sketch):
    f=d.FeatureByName(sketch); s=f.GetSpecificFeature2; out=[]
    for g in list(pv(s,"GetSketchSegments") or []):
        ty=g.GetType() if callable(g.GetType) else g.GetType
        if ty==1: out.append(tuple(round(v,2) for v in circ_xy(g)))
    return sorted(out)
def cyl_faces(d):
    out=[]
    for b in bodies(d):
        for fc in list(pv(b,"GetFaces") or []):
            sf=fc.GetSurface
            if sf.IsCylinder():
                p=sf.CylinderParams; out.append((round(p[0]*1000,2),round(p[1]*1000,2),round(p[6]*1000,3)))
    return out
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def close_unsaved_new():
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith(("파트","Part")): app.CloseDoc(tt); print("closed unsaved",tt)
# ---------- 0. 백업 ----------
if STAGE in ("all","backup"):
    os.makedirs(BK,exist_ok=True)
    for p in (ASM,P_J1C,P_J5L,P_B9H):
        dst=os.path.join(BK,os.path.basename(p))
        if not os.path.exists(dst): shutil.copy2(p,dst); print("backup",os.path.basename(p))
    rep["backup"]=BK
# ---------- 1. 새 파트 ----------
if STAGE in ("all","parts"):
    close_unsaved_new()
    # 부시 LHFRW20 — 원점 = 플랜지 상면 중심, 축 −z (플랜지 z 0~−8, 몸체 z 0~−80), 취부홀 0°/90° PCD43
    if not os.path.exists(P_B10):
        d=app.NewDocument(tmpl,0,0,0)
        new_sketch(d,"정면",lambda sm:(sm.CreateCircleByRadius(0,0,0,mm(BUSH["H"]/2)),sm.CreateCircleByRadius(0,0,0,mm(BUSH["dr"]/2)))); extrude_neg(d,BUSH["T"],"플랜지_Ø54_t8")
        new_sketch(d,"정면",lambda sm:(sm.CreateCircleByRadius(0,0,0,mm(BUSH["D"]/2)),sm.CreateCircleByRadius(0,0,0,mm(BUSH["dr"]/2)))); extrude_neg(d,BUSH["L"],"몸체_Ø32_L80")
        r=BUSH["PCD"]/2; pts=[(r,0),(-r,0),(0,r),(0,-r)]
        new_sketch(d,"정면",lambda sm:[sm.CreateCircleByRadius(mm(x),mm(y),0,mm(BUSH["d"]/2)) for x,y in pts]); cut_neg(d,BUSH["T"]+1,"취부홀_4xØ5.5",through=True)
        new_sketch(d,"정면",lambda sm:[sm.CreateCircleByRadius(mm(x),mm(y),0,mm(BUSH["d1"]/2)) for x,y in pts]); cut_neg(d,BUSH["t"],"카운터보어_4xØ9_t5.1")
        bx=bbox(d); v=volume(d)
        v_exp=math.pi*((27**2-10**2)*8+(16**2-10**2)*72)-4*math.pi*2.75**2*8-4*math.pi*(4.5**2-2.75**2)*5.1
        print("  bushing box",bx,"vol",round(v),"expected",round(v_exp)); assert abs(bx[2]+80)<0.01 and abs(bx[5])<0.01 and abs(bx[3]-27)<0.01 and abs(v-v_exp)/v_exp<0.01, (bx,v,v_exp)
        set_props(d,{"TITLE":"LINEAR BUSHING Ø20 (플랜지붙이 더블형) — MISUMI LHFRW20","SPEC":"MISUMI LHFRW20(플랜지붙이 리니어부시 표준 더블형, 원형 플랜지): 내경 dr 20(0/−0.012)·외경 D 32(0/−0.019, 표면처리 없음)·L 80·플랜지 H 54·T 8·취부홀 4-Ø5.5 카운터보어 Ø9×5.1 PCD 43·정격 C 1,400 N / Co 2,740 N·허용 모멘트 26.8 N·m·질량 260 g. 하우징 구멍 Ø32 H7. **규격표 치수 모델(볼·씰 미표현) — MISUMI STEP 교체 대기.**",
          "Material":"미확인(MISUMI 카탈로그 재질표)","QT'Y":"4","DATE":DATE,"TOLERANCE":"내경 0/−0.012, 외경 0/−0.016→(D32) 0/−0.019 (MISUMI 규격표)","REMARK":"구매품. 09-17 Ø16(LHFRW16)→Ø20 교체, 4점."})
        save_new(d,P_B10); app.CloseDoc(d.GetTitle)
    # 홀더 SHFSS20 — 원점 = 플랜지 상면(J1c 밑면 접촉) 보어 중심, 축 −z(z 0~−20), L 60 = 로컬 x, 보스 +y
    if not os.path.exists(P_J23):
        d=app.NewDocument(tmpl,0,0,0)
        L,A,H,B,T=HOLD["L"],HOLD["A"],HOLD["H"],HOLD["B"],HOLD["T"]
        def draw(sm):
            sm.CreateCornerRectangle(mm(-L/2),mm(-A/2),0,mm(L/2),mm(A/2),0)
            sm.CreateCircleByRadius(0,0,0,mm(HOLD["dr"]/2 if "dr" in HOLD else 10.0))
            sm.CreateCircleByRadius(mm(HOLD["L1"]/2),0,0,mm(HOLD["d"]/2)); sm.CreateCircleByRadius(mm(-HOLD["L1"]/2),0,0,mm(HOLD["d"]/2))
        new_sketch(d,"정면",draw); extrude_neg(d,T,"플랜지_60x34_T20")
        new_sketch(d,"정면",lambda sm:sm.CreateCornerRectangle(mm(-B/2),mm(A/2-1),0,mm(B/2),mm(H-A/2),0)); extrude_neg(d,T,"클램프보스_22x3")
        new_sketch(d,"정면",lambda sm:sm.CreateCornerRectangle(mm(-0.75),mm(8.0),0,mm(0.75),mm(H-A/2+1),0)); cut_neg(d,T+1,"슬릿_1.5",through=True)
        bx=bbox(d); print("  holder box",bx); assert abs(bx[0]+30)<0.01 and abs(bx[3]-30)<0.01 and abs(bx[1]+17)<0.01 and abs(bx[4]-20)<0.01 and abs(bx[2]+20)<0.01, bx
        set_props(d,{"TITLE":"SHAFT HOLDER Ø20 (플랜지형 슬릿) — MISUMI SHFSS20","SPEC":"MISUMI SHFSS20(샤프트홀더 플랜지형 슬릿, 주조품 SUS304): 보어 D 20 H7·L 60·L1 48·2-d 7(취부 M6)·A 34·H 37·T 20·B 22·C 15·클램프 볼트 M5·질량 110 g. J1c 밑면에 M6 탭 2개로 취부, L(60) 방향 = 라인 y. **규격표 치수 모델(클램프 볼트·R 미표현) — MISUMI STEP 교체 대기.**",
          "Material":"SUS304","QT'Y":"4","DATE":DATE,"TOLERANCE":"보어 H7 +0.021/0(Ø20, 슬릿 가공 후 H8 가능 — MISUMI 규격표 주기)","REMARK":"구매품. 09-17 SHFSS16→SHFSS20 교체, 4점."},mat="AISI 304")
        save_new(d,P_J23); app.CloseDoc(d.GetTitle)
    # 봉 PSSFAQ20-660-B13 — 원점 = 상단 중심, −z 673 (나사 M20×13 상단, 형상은 단순 원통)
    if not os.path.exists(P_J2):
        d=app.NewDocument(tmpl,0,0,0)
        new_sketch(d,"정면",lambda sm:sm.CreateCircleByRadius(0,0,0,mm(10.0))); extrude_neg(d,SHAFT_L+SHAFT_B,"봉_Ø20_L673")
        bx=bbox(d); print("  shaft box",bx); assert abs(bx[2]+(SHAFT_L+SHAFT_B))<0.01, bx
        set_props(d,{"TITLE":f"GUIDE SHAFT Ø20 L{SHAFT_L} (한쪽 M20 나사 {SHAFT_B}) — MISUMI PSSFAQ20-{SHAFT_L}-B{SHAFT_B}","SPEC":f"MISUMI PSSFAQ20-{SHAFT_L}-B{SHAFT_B}(정밀 리니어 샤프트 한쪽 수나사, D 공차 g6 −0.007/−0.020, 나사 M20×2.5 길이 {SHAFT_B}, 전장 {SHAFT_L+SHAFT_B}). 상단 나사부는 J1c 관통 Ø20.5(t10) 안, 홀더 SHFSS20 클램프. 하강 시 부시 하단 −647 대비 봉 하단 −670(여유 23). **규격표 치수 모델(나사·모따기 미표현) — MISUMI STEP 교체 대기.**",
          "Material":"SUS440C 상당(EN 1.4037, MISUMI 기재)","QT'Y":"4","DATE":DATE,"TOLERANCE":"외경 g6 −0.007/−0.020 (MISUMI 규격표 D20)","REMARK":"구매품. 09-17 PSSFAQ16-590→PSSFAQ20-660 교체, 4점(앞 x 0·뒤 x 90, y ±240)."},mat="AISI 440C")
        save_new(d,P_J2); app.CloseDoc(d.GetTitle)
    # 호스 2종(상승 U190 / 하강 활) — 원점 = 호스 상단, 스케치 정면(x=+y 라인, y=z), 스텁 + 4원호 + 스텁
    def segs_from(list_):
        segs=[]; x,y,h=0.0,0.0,-math.pi/2
        for it in list_:
            if it[0]=="line":
                dd=it[1]; x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1; continue
            rad,ang=it[1],it[2]
            side=1 if ang>0 else -1
            cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
            h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
            segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
        return segs,(x,y)
    HOSE_SPEC="야성하이텍 슈퍼스프링호스(무독) HSPF-032: 내경 32.0±1.0·외경 41.0±1.0·0.5/2.5 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 3D 내경은 바브(Ø34) 위 늘어난 34로 표현. 최소 굽힘반경 카탈로그 미기재."
    def build_hose(path,R,T,D,bulge,title,spec_add):
        if os.path.exists(path): return
        segs,end=segs_from([("line",STUB),("arc",R,T),("arc",R,-T),("arc",R,-T),("arc",R,T),("line",STUB)])
        print("  bow end",[round(v,2) for v in end],"(expect 0,",-D,")"); assert abs(end[0])<0.05 and abs(end[1]+D)<0.05, end
        done=False
        for direction in (1,-1):
            dh=app.NewDocument(tmpl,0,0,0)
            assert sel_plane(dh,"정면"); dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
            for sg in segs:
                if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0); continue
                cc_,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]; sm.CreateArc(mm(cc_[0]),mm(cc_[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
            sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
            Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
            print(f"  bow direction {direction}: sketch length {Ls:.1f} (target {L_HOSE:.1f})")
            if abs(Ls-L_HOSE)>2.0: app.CloseDoc(dh.GetTitle); continue
            assert sel_plane(dh,"윗면"); dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(20.5)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(17.0)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            dh.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or dh.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
            dh.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or dh.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
            f=None
            for attempt in ("swept3","swept4"):
                try:
                    if attempt=="swept3": f=dh.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                    else: f=dh.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                    if f: break
                except Exception as ex: print("  ",attempt,"exc",ex)
            if not f: print("  sweep failed dir",direction); app.CloseDoc(dh.GetTitle); continue
            dh.EditRebuild3; bx=bbox(dh); print("  bow body box",bx)
            if not (abs(bx[1]+D)<1.5 and (abs(bx[3]-(bulge+20.5))<2.0 or abs(bx[0]+(bulge+20.5))<2.0)): app.CloseDoc(dh.GetTitle); continue
            set_props(dh,{"TITLE":title,"SPEC":HOSE_SPEC+spec_add,"Material":"PVC","QT'Y":"1","DATE":DATE,"REMARK":"구매품(야성판매). 사용자 지시(09-17) 「U자 폭 190」·스트로크 150. 상승/하강 두 상태 모두 활 형상(하강 직선 불가 — 자유길이 413 > 하강 간격 296)."},mat="PVC 경질")
            save_new(dh,path); done=True; break
        assert done, "bow hose "+os.path.basename(path)
        app.CloseDoc(os.path.basename(path))
    build_hose(P_UP,R_UP,T_UP,D_UP,BULGE_UP,"HOSE 32A (상승 상태, U자 폭 190) — YASUNG HSPF-032",
        f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 상승(낙차 {D_UP:.1f}): 바브 구간 {STUB:.1f}×2 직선 + 4원호 활 R{R_UP:.1f} ±{math.degrees(T_UP):.1f}°, +y로 {BULGE_UP:.0f} 불룩(외곽 폭 190). R{R_UP:.0f} = 내경의 {R_UP/32:.2f}배 — 굽힘반경 카탈로그 미기재.")
    build_hose(P_DN,R_DN,T_DN,D_DN,BULGE_DN,"HOSE 32A (하강 상태, 활 굽힘) — YASUNG HSPF-032",
        f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 하강(낙차 {D_DN:.1f}): 바브 구간 {STUB:.1f}×2 직선 + 4원호 활 R{R_DN:.1f} ±{math.degrees(T_DN):.1f}°, +y로 {BULGE_DN:.0f} 불룩(외곽 폭 {BULGE_DN+41:.0f}). R{R_DN:.0f} = 내경의 {R_DN/32:.2f}배.")
    rep["parts"]=[os.path.basename(p) for p in (P_B10,P_J23,P_J2,P_UP,P_DN)]
# ---------- 2. 판 제자리 편집 ----------
if STAGE in ("all","plates"):
    # J1c: Ø16.5@(45,±240)·M5탭@(25|65,±240) → Ø20.5@(0|90,±240)·M6탭(Ø5.0)@(0|90,±240±24)
    d=act(P_J1C); before=circles_of(d,"스케치3"); print("J1c circles before",before)
    if not any(abs(c[0])<0.01 and abs(abs(c[1])-240)<0.01 and abs(c[2]-10.25)<0.01 for c in before):
        new=[(x,s*SH_Y,10.25) for x in SH_XS for s in (1,-1)]+[(x,s*SH_Y+k*HOLD["L1"]/2,2.5) for x in SH_XS for s in (1,-1) for k in (1,-1)]
        n=edit_circles(d,"스케치3",lambda cx,cy,r: abs(abs(cy)-240)<0.01 and r<12,new); print("  J1c deleted",n,"added",len(new))
    d.ForceRebuild3(False); after=circles_of(d,"스케치3"); bx=bbox(d); print("J1c circles after",after,"box",bx,"ww",ww(d),"orphans",orphan_sketches(d))
    assert bx==[-75.0,-290.0,-10.0,110.0,290.0,0.0], bx; assert len(after)==1+4+8, after; assert not ww(d) and not orphan_sketches(d)
    pr=get_props(d); print("  J1c SPEC:",pr.get("SPEC")); rep["J1c_props_before"]=pr
    sp=pr.get("SPEC","")
    sp2=sp.replace("Ø16.5","Ø20.5").replace("(45,±240)","(0|90,±240)").replace("M5 탭","M6 탭").replace("SHFSS16","SHFSS20")
    if "4점" not in sp2: sp2+=" 가이드 봉 4점(앞 x 0·뒤 x 90, y ±240): 봉 관통 Ø20.5 ×4, 홀더 SHFSS20 취부 M6 탭 ×8(y ±24)."
    set_props(d,{"SPEC":sp2,"DATE":DATE}); print("  J1c SPEC ->",sp2)
    # J5l: Ø28@(45,±240)+4×Ø3.3 PCD38 → Ø32@(0|90,±240)+4×Ø4.2(M5) PCD43
    d=act(P_J5L); before=circles_of(d,"스케치1"); print("J5l circles before",before)
    if not any(abs(c[0])<0.01 and abs(abs(c[1])-240)<0.01 and abs(c[2]-16)<0.01 for c in before):
        r=BUSH["PCD"]/2
        new=[(x,s*SH_Y,16.0) for x in SH_XS for s in (1,-1)]+[(x+dx,s*SH_Y+dy,2.1) for x in SH_XS for s in (1,-1) for dx,dy in ((r,0),(-r,0),(0,r),(0,-r))]
        n=edit_circles(d,"스케치1",lambda cx,cy,r: abs(abs(cy)-240)<20.01 and abs(cy)>200 and r<15,new); print("  J5l deleted",n,"added",len(new))
    d.ForceRebuild3(False); after=circles_of(d,"스케치1"); bx=bbox(d); print("J5l circles after",after,"box",bx,"ww",ww(d),"orphans",orphan_sketches(d))
    assert bx==[-45.0,-270.0,-8.0,135.0,270.0,0.0], bx; assert len(after)==1+4+16, after; assert not ww(d) and not orphan_sketches(d)
    pr=get_props(d); print("  J5l SPEC:",pr.get("SPEC")); rep["J5l_props_before"]=pr
    sp=pr.get("SPEC","")
    sp2=sp.replace("Ø28 H7","Ø32 H7").replace("Ø28","Ø32").replace("M4×4","M5×4").replace("M4 ×4","M5 ×4").replace("(45,±240)","(0|90,±240)").replace("LHFRW16","LHFRW20")
    if "4점" not in sp2: sp2+=" 부시 LHFRW20 4점(앞 x 0·뒤 x 90, y ±240): 하우징 Ø32 H7(+0.025/0) ×4 + 취부 M5 탭 4×4(PCD 43, 0°/90°)."
    set_props(d,{"SPEC":sp2,"DATE":DATE}); print("  J5l SPEC ->",sp2)
    rep["J1c_circles"]=circles_of(act(P_J1C),"스케치3"); rep["J5l_circles"]=circles_of(act(P_J5L),"스케치1")
# ---------- 3. TA2 스트로크 150 → B9i ----------
if STAGE in ("all","ta2"):
    if not os.path.exists(P_B9I):
        d=act(P_B9H); f=d.FeatureByName("로드_하강_이동"); dim=f.Parameter("D3"); print("  D3 before",dim.SystemValue*1000)
        r=dim.SetSystemValue3(mm(STROKE),2,None); d.ForceRebuild3(False); print("  D3 set ret",r,"now",dim.SystemValue*1000)
        for cfg in ("상승","하강"):
            d.ShowConfiguration2(cfg); d.ForceRebuild3(False); bs=bodies(d); bb=[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bs]; print(f"  [{cfg}] bodies",bb); rep[f"ta2_{cfg}"]=bb
        d.ShowConfiguration2("상승"); d.ForceRebuild3(False)
        pr=get_props(d); print("  B9h props",pr)
        set_props(d,{"TITLE":"LINEAR ACTUATOR TA2-2H stroke 150 / retracted 339 — TiMOTION TA2-2H-150339-5511-010-1",
          "SPEC":"TiMOTION TA2-2H-150339-5511-010-1: 코드 H 500 N(push/pull)·17/14 mm/s·셀프락 500 N·24 V DC, 스트로크 150(표준 범위 20~150), Retracted Length 339 ≥ 150+119(후단 5·전단 5 클레비스 U, 데이터시트 20160711-M p.6), 리미트 스위치 1(양단 차단), IP66D, −25~+65 ℃, 케이블 1000. 구성 상승 = 로드 후퇴 / 하강 = 로드 −150 신장. **3D 형상: TA2-2H-085339 TraceParts STEP 대용(설치길이 339 동일) — 150339 STEP 교체 대기.**",
          "REMARK":"구매품. 09-17 사용자 지시 스트로크 85→150(상승 위치 유지, 하강 65 더 내림). 주문 표기: TA2-2H-150, Retracted Length 339, 후단 5·전단 5(홀 Ø8), 방향 0°, 리미트 스위치 1, 출력신호 0.","DATE":DATE})
        e=I4(); w=I4(); ok=d.Extension.SaveAs(P_B9I,0,1,NOD,e,w); print("  SaveAs B9i",ok,e.value,w.value); assert ok
        rep["B9i"]=os.path.basename(P_B9I)
json.dump(rep,open(os.path.join(VER,f"stroke150_parts_0917_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("DONE",STAGE)
