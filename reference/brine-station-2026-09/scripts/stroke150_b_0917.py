# 2026-09-17 3단계(사용자 「B로 갑시다」): 상승 −360 / 하강 −510, 스트로크 150 → 봉 PSSFAQ20-580, 호스 U190(R40)/활(R59), TA2 설치길이 274 대용 형상(B9j), 어셈블리 갱신
import os, sys, json, math, re
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-17"
STAGE=sys.argv[1] if len(sys.argv)>1 else "all"; rep={"stage":STAGE}
ZP_UP=-360.0; ZP_DN=-510.0; STROKE=ZP_UP-ZP_DN; SH_XS=(0.0,90.0); SH_Y=240.0
RL_NEW=ZP_UP+60+26          # 274 = 전단 핀(ZP+60) − 후단 핀(−26)
SHAFT_L=580; SHAFT_B=13; SHAFT_TOP=3.0     # 전장 593, 하단 −590 (부시 하단 하강 −582 → 여유 8)
HOSE_TOP=-154.6; STUB=52.4; HB=lambda zp: zp-15+20.4+14.2
D_UP=HOSE_TOP-HB(ZP_UP); D_DN=HOSE_TOP-HB(ZP_DN); G_UP=D_UP-2*STUB; G_DN=D_DN-2*STUB; BULGE_UP=149.0
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
print(f"hose: D_UP {D_UP:.1f} D_DN {D_DN:.1f} | free {LF:.1f} total {L_HOSE:.1f} | up R {R_UP:.1f} θ {math.degrees(T_UP):.1f}° | dn R {R_DN:.1f} θ {math.degrees(T_DN):.1f}° bulge {BULGE_DN:.1f}")
rep["hose"]=dict(D_UP=D_UP,D_DN=D_DN,Lf=LF,L_total=L_HOSE,R_up=R_UP,th_up=math.degrees(T_UP),R_dn=R_DN,th_dn=math.degrees(T_DN),bulge_dn=BULGE_DN)
P_J2=Zp(f"J2d_guide_shaft_MISUMI_PSSFAQ20-{SHAFT_L}-B{SHAFT_B}_catalog.SLDPRT")
P_UP=Zp(f"J19k_hose_YASUNG_HSPF-032_up_U190_R{R_UP:.0f}.SLDPRT"); P_DN=Zp(f"J19k_hose_YASUNG_HSPF-032_dn_bow_R{R_DN:.0f}.SLDPRT")
P_B9I=Zp("B9i_TiMOTION_TA2-2H-150339-5511-010-1.SLDPRT"); P_B9J=Zp("B9j_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT")
J1C="J1c_fixed_plate_185x580_t10-2"; J5L="J5l_moving_plate_180x540_t8-1"
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
# ---------- 헬퍼(1·2단계와 동일) ----------
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
def bboxes(d): return [[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies(d)]
def new_sketch(d,plane,draw):
    assert sel_plane_p(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def extrude_neg(d,depth,name):
    f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f, name; f.Name=name; return f
def set_props(d,props,mat=None):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    if mat:
        try: d.SetMaterialPropertyName2("","이텍",mat)
        except Exception as ex: print("  mat exc",ex)
def save_new(d,path):
    assert not clean_orphans(d); e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d)); assert ok
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def close_unsaved_new():
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith(("파트","Part")): app.CloseDoc(tt); print("closed unsaved",tt)
HOSE_SPEC="야성하이텍 슈퍼스프링호스(무독) HSPF-032: 내경 32.0±1.0·외경 41.0±1.0·0.5/2.5 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 3D 내경은 바브(Ø34) 위 늘어난 34로 표현. 최소 굽힘반경 카탈로그 미기재."
def segs_from(list_):
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    for it in list_:
        if it[0]=="line":
            dd=it[1]; x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1; continue
        rad,ang=it[1],it[2]; side=1 if ang>0 else -1
        cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h); h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
        segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    return segs,(x,y)
def build_hose(path,R,T,D,bulge,title,spec_add):
    if os.path.exists(path): return
    segs,end=segs_from([("line",STUB),("arc",R,T),("arc",R,-T),("arc",R,-T),("arc",R,T),("line",STUB)])
    assert abs(end[0])<0.05 and abs(end[1]+D)<0.05, end
    done=False
    for direction in (1,-1):
        dh=app.NewDocument(tmpl,0,0,0)
        assert sel_plane_p(dh,"정면"); dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
        for sg in segs:
            if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0); continue
            cc_,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]; sm.CreateArc(mm(cc_[0]),mm(cc_[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
        sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
        skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
        Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
        print(f"  bow direction {direction}: sketch length {Ls:.1f} (target {L_HOSE:.1f})")
        if abs(Ls-L_HOSE)>2.0: app.CloseDoc(dh.GetTitle); continue
        assert sel_plane_p(dh,"윗면"); dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(20.5)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(17.0)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
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
        set_props(dh,{"TITLE":title,"SPEC":HOSE_SPEC+spec_add,"Material":"PVC","QT'Y":"1","DATE":DATE,"REMARK":"구매품(야성판매). 사용자 지시 「U자 폭 190」·스트로크 150(상승 −360/하강 −510, B안). 상승·하강 모두 활 형상."},mat="PVC 경질")
        save_new(dh,path); done=True; break
    assert done, "bow hose "+os.path.basename(path)
    app.CloseDoc(os.path.basename(path))
# ---------- 1. 파트 ----------
if STAGE in ("all","parts"):
    close_unsaved_new()
    if not os.path.exists(P_J2):
        d=app.NewDocument(tmpl,0,0,0)
        new_sketch(d,"정면",lambda sm:sm.CreateCircleByRadius(0,0,0,mm(10.0))); extrude_neg(d,SHAFT_L+SHAFT_B,f"봉_Ø20_L{SHAFT_L+SHAFT_B}")
        bx=bbox(d); assert abs(bx[2]+(SHAFT_L+SHAFT_B))<0.01, bx
        set_props(d,{"TITLE":f"GUIDE SHAFT Ø20 L{SHAFT_L} (한쪽 M20 나사 {SHAFT_B}) — MISUMI PSSFAQ20-{SHAFT_L}-B{SHAFT_B}","SPEC":f"MISUMI PSSFAQ20-{SHAFT_L}-B{SHAFT_B}(정밀 리니어 샤프트 한쪽 수나사, D 공차 g6 −0.007/−0.020, 나사 M20×2.5 길이 {SHAFT_B}, 전장 {SHAFT_L+SHAFT_B}). 상단 z +3, 나사부는 J1c 관통 Ø20.5(t10) 안, 홀더 SHFSS20 클램프. 하강(ZP −510) 부시 하단 −582 대비 봉 하단 −590(여유 8) — 봉 하단 지상고 1,460은 로봇 HP300(bbox 상단 1,456) 회피 한계. **규격표 치수 모델(나사·모따기 미표현) — MISUMI STEP 교체 대기.**",
          "Material":"SUS440C 상당(EN 1.4037, MISUMI 기재)","QT'Y":"4","DATE":DATE,"TOLERANCE":"외경 g6 −0.007/−0.020 (MISUMI 규격표 D20)","REMARK":"구매품. PSSFAQ16-590→PSSFAQ20-580 교체, 4점(앞 x 0·뒤 x 90, y ±240)."},mat="AISI 440C")
        save_new(d,P_J2); app.CloseDoc(d.GetTitle)
    build_hose(P_UP,R_UP,T_UP,D_UP,BULGE_UP,"HOSE 32A (상승 상태, U자 폭 190) — YASUNG HSPF-032",
        f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 상승(낙차 {D_UP:.1f}): 바브 구간 {STUB:.1f}×2 직선 + 4원호 활 R{R_UP:.1f} ±{math.degrees(T_UP):.1f}°, +y로 {BULGE_UP:.0f} 불룩(외곽 폭 190). R{R_UP:.0f} = 내경의 {R_UP/32:.2f}배 — 굽힘반경 카탈로그 미기재.")
    build_hose(P_DN,R_DN,T_DN,D_DN,BULGE_DN,"HOSE 32A (하강 상태, 활 굽힘) — YASUNG HSPF-032",
        f" 절단 = 자유길이 {LF:.0f} + 바브 2×{STUB:.0f} ≈ {L_HOSE:.0f}. 하강(낙차 {D_DN:.1f}): 바브 구간 {STUB:.1f}×2 직선 + 4원호 활 R{R_DN:.1f} ±{math.degrees(T_DN):.1f}°, +y로 {BULGE_DN:.0f} 불룩(외곽 폭 {BULGE_DN+41:.0f}). R{R_DN:.0f} = 내경의 {R_DN/32:.2f}배.")
    rep["parts"]=[os.path.basename(p) for p in (P_J2,P_UP,P_DN)]
# ---------- 2. TA2 설치길이 274 대용 형상 → B9j ----------
if STAGE in ("all","ta2"):
    if not os.path.exists(P_B9J):
        d=act(P_B9I); SH=339.0-RL_NEW   # 65
        d.ShowConfiguration2("상승"); d.EditRebuild3; bb=bboxes(d); print("  상승 bodies before",bb)
        rod=[b for b in bb if b[3]<=40][0]; body=[b for b in bb if b[3]>40][0]
        # (a) 기존 로드 연장 피처 삭제(+스케치)
        f=d.FeatureByName("로드_연장_하강")
        if f is not None:
            d.ClearSelection2(True); f.Select2(False,0); d.EditDelete(); d.EditRebuild3; clean_orphans(d); print("  로드_연장_하강 deleted")
        # (b) 로드 바디 +65 z 이동(전 구성)
        d.ShowConfiguration2("상승"); d.EditRebuild3
        rb=[b for b in bodies(d) if [round(v*1000,1) for v in pv(b,"GetBodyBox")][3]<=40]; assert len(rb)==1
        d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; rb[0].Select2(True,sd)
        mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(SH),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); d.EditRebuild3; assert mv is not None; mv.Name="설치길이274_로드이동"
        bb=bboxes(d); print("  after rod move",bb); rod2=[b for b in bb if b[3]<=40][0]; assert abs(rod2[2]-(rod[2]+SH))<0.1, (rod,rod2)
        # (c) 튜브 끝 65 절단: 정면 스케치 링(r 10.5~32) 시작오프셋 |z_body_end| 깊이 65, +z 방향 → 로드(Ø20)는 남김
        z_end=body[2]; new_sketch(d,"정면",lambda sm:(sm.CreateCircleByRadius(0,0,0,mm(32.0)),sm.CreateCircleByRadius(0,0,0,mm(10.5))))
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; ok=False
        for dirn,flip in ((False,True),(True,True),(True,False),(False,False)):
            d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
            c=d.FeatureManager.FeatureCut4(True,False,dirn,0,0,mm(SH+0.5),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(abs(z_end)-0.5),flip,False); d.EditRebuild3
            if c is None: continue
            bb=bboxes(d); bd=[b for b in bb if b[3]>40]
            good=bool(bd) and abs(bd[0][2]-(z_end+SH))<0.6 and not ww(d)
            print("   cut try",dirn,flip,bb,"good",good)
            if good: c.Name="설치길이274_튜브컷"; ok=True; break
            c.Select2(False,0); d.EditDelete(); d.EditRebuild3
        assert ok, "tube cut"
        # (d) 하강 로드 연장 재생성: 하강 구성에서 로드 상단 → 튜브 끝
        d.ShowConfiguration2("하강"); d.EditRebuild3; bb=bboxes(d); print("  하강 bodies",bb)
        rodd=[b for b in bb if b[3]<=40][0]; bodyd=[b for b in bb if b[3]>40][0]; gap=bodyd[2]-rodd[5]; print("  gap",gap); assert gap>0
        z0=rodd[5]-5.0; depth=gap+10.0
        new_sketch(d,"정면",lambda sm:sm.CreateCircleByRadius(0,0,0,mm(10.0))); sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; ok=False
        for dirn,flip in ((False,True),(True,True),(True,False),(False,False)):
            d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
            ext=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,3,mm(abs(z0)),flip); d.EditRebuild3
            if ext is None: continue
            bb=bboxes(d); good=any(b[2]<=rodd[2]+0.1 and b[5]>=bodyd[5]-0.1 for b in bb) and not ww(d); print("   ext try",dirn,flip,bb,"good",good)
            if good: ext.Name="로드_연장_하강"; ok=True; break
            ext.Select2(False,0); d.EditDelete(); d.EditRebuild3
        assert ok, "rod ext"
        assert not clean_orphans(d)
        d.FeatureByName("로드_연장_하강").SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
        for cfg in ("상승","하강","기본"):
            d.ShowConfiguration2(cfg); d.EditRebuild3; print(f"  [{cfg}]",bboxes(d),"ww",ww(d)); rep[f"b9j_{cfg}"]=bboxes(d)
        d.ShowConfiguration2("상승"); d.EditRebuild3
        set_props(d,{"TITLE":"LINEAR ACTUATOR TA2-2H stroke 150 / retracted 274 — TiMOTION TA2-2H-150274-5511-010-1",
          "SPEC":"TiMOTION TA2-2H-150274-5511-010-1: 코드 H 500 N(push/pull)·17/14 mm/s·셀프락 500 N·24 V DC, 스트로크 150(표준 범위 20~150), Retracted Length 274 ≥ 150+119(후단 5·전단 5 클레비스 U, 데이터시트 20160711-M p.6), 리미트 스위치 1(양단 차단), IP66D, −25~+65 ℃, 케이블 1000. 구성 상승 = 로드 후퇴(핀 간격 274) / 하강 = 로드 −150 신장(424). **3D 형상: TA2-2H-085339 TraceParts STEP를 튜브 −65·로드 +65로 가공한 대용 — 150274 STEP 교체 대기.**",
          "REMARK":"구매품. 사용자 지시 스트로크 85→150(B안: 상승 위치 65 상향, 하강 유지). 주문 표기: TA2-2H-150, Retracted Length 274, 후단 5·전단 5(홀 Ø8), 방향 0°, 리미트 스위치 1, 출력신호 0.","DATE":DATE})
        e=I4(); w=I4(); ok=d.Extension.SaveAs(P_B9J,0,1,NOD,e,w); print("  SaveAs B9j",ok,e.value,w.value); assert ok
# ---------- 2b. TA2 274 대용 파트(원시 형상, STEP 실측 치수, 시작오프셋 미사용) → B9j ----------
if STAGE in ("all","ta2b","ta2b_B"):
    if STAGE!="ta2b_B":
        d=app.GetOpenDocumentByName(P_B9I)
        if d is not None:
            d.ShowConfiguration2("상승"); d.EditRebuild3; bb=bboxes(d); print("  B9i 상승 bodies",bb); assert any(abs(b[2]+349)<0.1 for b in bb), "B9i not restored"
    if not os.path.exists(P_B9J):
        if STAGE!="ta2b_B": close_unsaved_new(); d=app.NewDocument(tmpl,0,0,0)
        else:
            docs=[x for x in list(pv(app,"GetDocuments") or []) if x.GetType==1 and not x.GetPathName]; assert docs, "no unsaved part"
            app.ActivateDoc3(docs[-1].GetTitle,False,0,I4()); d=app.ActiveDoc; print("  phase B attached to",d.GetTitle,bboxes(d))
        TUBE_END=-(RL_NEW-22.8); TIP=-(RL_NEW+10.0)     # −251.2 / −284
        vol=lambda: d.Extension.CreateMassProperty.Volume*1e9
        def ext(d,plane,draw,depth,name,dirn=True,merge=True):
            new_sketch(d,plane,draw); sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
            d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0), sk
            f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False); d.EditRebuild3
            if f is None:
                skf=d.FeatureByName(sk); segs=list(pv(skf.GetSpecificFeature2,"GetSketchSegments") or []); act_=d.SketchManager.ActiveSketch
                print(f"   [{name}] ext None: sketch {sk} segs {len(segs)} activeSketch {act_ is not None} selcount {d.SelectionManager.GetSelectedObjectCount2(-1)} feats {[n for n,t in feats(d)][-4:]}")
                d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
                f=d.FeatureManager.FeatureExtrusion3(True,False,(not dirn),0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False); d.EditRebuild3
                print("   retry flipped ->",None if f is None else bboxes(d))
            assert f,name; f.Name=name; return f
        def cut_blind(d,depth,name,vmin,vmax,sk=None):
            v0=vol(); sk=sk or [n for n,t in feats(d) if t=="ProfileFeature"][-1]
            for dirn in (False,True):
                d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
                c=d.FeatureManager.FeatureCut4(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
                if c is None: continue
                dv=v0-vol(); print(f"   {name} dirn={dirn} dv={dv:.0f} (want {vmin}~{vmax})")
                if vmin<=dv<=vmax and not ww(d): c.Name=name; return c
                c.Select2(False,0); d.EditDelete(); d.EditRebuild3
            raise AssertionError(name)
        def sel_face(pt):
            d.ClearSelection2(True); return d.Extension.SelectByID2("","FACE",mm(pt[0]),mm(pt[1]),mm(pt[2]),False,0,NOD,0)
        def sketch_on_face(pt,draw):
            assert sel_face(pt), ("face",pt); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            return [n for n,t in feats(d) if t=="ProfileFeature"][-1]
        def ext_face(pt,draw,depth,name,merge,zmin_exp,zmax_exp):
            """면 위 스케치 → 돌출, bbox(z) 검증으로 방향 자동. (act_diag 검증 경로를 그대로 인라인)"""
            d.ClearSelection2(True); okf=d.Extension.SelectByID2("","FACE",mm(pt[0]),mm(pt[1]),mm(pt[2]),False,0,NOD,0); assert okf,("face",pt)
            d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
            skf=d.FeatureByName(sk); nseg=len(list(pv(skf.GetSpecificFeature2,"GetSketchSegments") or [])); print(f"   {name}: sketch {sk} segs {nseg} active {d.SketchManager.ActiveSketch is not None}")
            for dirn in (False,True):
                d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
                f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False); d.EditRebuild3
                if f is None: print(f"   {name} dirn={dirn} -> None ww {ww(d)}"); continue
                bb=bboxes(d); hit=any(abs(b[2]-zmin_exp)<0.06 and abs(b[5]-zmax_exp)<0.06 for b in bb)
                print(f"   {name} dirn={dirn} -> {bb} {'OK' if hit else ''}")
                if hit and not ww(d): f.Name=name; return f
                f.Select2(False,0); d.EditDelete(); d.EditRebuild3
            raise AssertionError(name)
        if STAGE!="ta2b_B":
            # phase A: 후단 요크 24×22.4 z −15~0 / 0~+11 + 슬롯(z +11 → −4). 이후 피처는 같은 프로세스에서 None 반환(원인 미상) → 별도 프로세스(phase B)
            ext(d,"정면",lambda sm:sm.CreateCornerRectangle(mm(-12),mm(-11.2),0,mm(12),mm(11.2),0),15.0,"후단요크_하",dirn=True)
            ext(d,"정면",lambda sm:sm.CreateCornerRectangle(mm(-12),mm(-11.2),0,mm(12),mm(11.2),0),11.0,"후단요크_상",dirn=False)
            bb=bboxes(d); assert len(bb)==1 and abs(bb[0][5]-11)<0.05 and abs(bb[0][2]+15)<0.05, bb
            sk=sketch_on_face((0,8,11.0),lambda sm:sm.CreateCornerRectangle(mm(-13),mm(-3),0,mm(13),mm(3),0))
            cut_blind(d,15.0,"후단슬롯_6",24*6*15-5,24*6*15+5,sk)
            bb=bboxes(d); assert len(bb)==1, bb
            import subprocess; stop.set()
            r=subprocess.run([sys.executable,"-u",os.path.abspath(__file__),"ta2b_B"],capture_output=True,text=True,encoding="utf-8",errors="replace"); print(r.stdout[-6000:]); print(r.stderr[-3000:])
            assert r.returncode==0 and os.path.exists(P_B9J), "phase B failed"
            raise SystemExit(0)
        # 3) 튜브 Ø42(보어 r10.5): 요크 밑면(z −15) 위 스케치 → −z 236.2 (z −15 ~ −251.2), 병합
        ext_face((8.0,8.0,-15.0),lambda sm:(sm.CreateCircleByRadius(0,0,0,mm(21.0)),sm.CreateCircleByRadius(0,0,0,mm(10.5))),-TUBE_END-15.0,"튜브_Ø42",True,TUBE_END,11.0)
        # 4) 모터 하우징 박스(STEP 실측 x 24.9~64.1, y −29.1~20.0, z −14.9~−115.5; 튜브와 병합되도록 x 15부터): 요크 밑면 보어 안 점(0,6,−15)
        ext_face((0.0,6.0,-15.0),lambda sm:sm.CreateCornerRectangle(mm(15.0),mm(-29.1),0,mm(64.1),mm(20.0),0),100.5,"모터하우징_실측박스",True,TUBE_END,11.0)
        bb=bboxes(d); assert len(bb)==1 and abs(bb[0][3]-64.1)<0.05, bb
        # 5) 전단 요크 24×17.6: 튜브 끝면(z −251.2, r 16) 위 스케치 → −z 32.8, 별도 바디
        ext_face((16.0,0.0,TUBE_END),lambda sm:sm.CreateCornerRectangle(mm(-12),mm(-8.8),0,mm(12),mm(8.8),0),TUBE_END-TIP,"전단요크",False,TIP,TUBE_END)
        bb=bboxes(d); assert len(bb)==2, bb
        # 6) 로드 Ø20: 전단 요크 윗면(z −251.2, 보어 안 점 (0,6)) 위 스케치 → +z 235.2 (z −251.2 ~ −16), 요크와 병합(튜브와는 0.5 틈)
        ext_face((0.0,6.0,TUBE_END),lambda sm:sm.CreateCircleByRadius(0,0,0,mm(10.0)),-TUBE_END-16.0,"로드_Ø20",True,TIP,-16.0)
        bb=bboxes(d); print("   after rod",bb); assert len(bb)==2 and any(abs(b[2]-TIP)<0.05 and abs(b[5]+16.0)<0.05 for b in bb), bb
        # 7) 전단 슬롯 y ±3: 팁면(z −284) 위 스케치 → +z 14 컷
        sk=sketch_on_face((11.0,7.0,TIP),lambda sm:sm.CreateCornerRectangle(mm(-13),mm(-3),0,mm(13),mm(3),0))
        cut_blind(d,14.0,"전단슬롯_6",1400,2100,sk)
        # 9) 핀홀 Ø8 (y축) 후단 z 0 · 전단 z −274 : 윗면 스케치 → 양방향 관통
        assert sel_plane_p(d,"윗면"); d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True
        for zc in (0.0,-RL_NEW,RL_NEW): d.SketchManager.CreateCircleByRadius(0,0,mm(zc),mm(4.0))
        d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        skp=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
        # 윗면 스케치의 원 위치 확인(스케치 x=월드 x, 스케치 y=−z 또는 +z) → 3개(0, ±274) 그려 하나는 허공, 나머지가 요크를 뚫음
        v0=vol(); d.Extension.SelectByID2(skp,"SKETCH",0,0,0,False,0,NOD,0)
        c=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert c,"핀홀"; c.Name="핀홀_Ø8_후단전단"
        print("   핀홀 dv",round(v0-vol()),"bodies",bboxes(d),"ww",ww(d)); assert not ww(d)
        bb=bboxes(d); assert len(bb)==2, bb
        # 10) 구성 상승/하강, 하강 = 로드+전단요크 바디 −150
        for cfg,desc in (("상승","로드 후퇴, 핀 간격 274"),("하강","로드 150 신장, 핀 간격 424")): d.AddConfiguration3(cfg,desc,"",0)
        d.ShowConfiguration2("하강"); d.EditRebuild3
        rb=[b for b in bodies(d) if abs([round(v*1000,1) for v in pv(b,"GetBodyBox")][2]-TIP)<0.05]; assert len(rb)==1
        d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; rb[0].Select2(True,sd)
        mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(-STROKE),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); d.EditRebuild3; assert mv is not None; mv.Name="로드_하강_이동"
        bb=bboxes(d); print("  하강 bodies",bb); assert any(abs(b[2]-(TIP-STROKE))<0.1 for b in bb), bb
        mv.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
        for cfg in ("상승","하강","기본"):
            d.ShowConfiguration2(cfg); d.EditRebuild3; print(f"  [{cfg}]",bboxes(d),"ww",ww(d)); rep[f"b9j_{cfg}"]=bboxes(d)
        d.ShowConfiguration2("상승"); d.EditRebuild3
        set_props(d,{"TITLE":"LINEAR ACTUATOR TA2-2H stroke 150 / retracted 274 — TiMOTION TA2-2H-150274-5511-010-1",
          "SPEC":"TiMOTION TA2-2H-150274-5511-010-1: 코드 H 500 N(push/pull)·17/14 mm/s·셀프락 500 N·24 V DC, 스트로크 150(표준 범위 20~150), Retracted Length 274 ≥ 150+119(후단 5·전단 5 클레비스 U, 데이터시트 20160711-M p.6), 리미트 스위치 1(양단 차단), IP66D, −25~+65 ℃, 케이블 1000. 구성 상승 = 로드 후퇴(핀 간격 274) / 하강 = 로드 −150 신장(424). **3D 형상: 원시 형상 대용 — 튜브 Ø42·로드 Ø20·모터 하우징 박스(x 24.9~64.1, y −29.1~20.0, z 0~−115.5)·요크 폭 22.4/17.6·슬롯 6·홀 Ø8은 085339 TraceParts STEP 실측값, 튜브 길이 = 설치길이 −22.8. 150274 STEP 교체 대기.** 파트 좌표: 후단 핀 원점, 축 −Z, 핀 축 Y, 모터 +X.",
          "MATERIAL":"AL casting/SUS rod","QT'Y":"1","DATE":DATE,"TOLERANCE":"TiMOTION 데이터시트: 전단 클레비스 U 슬롯 6.0·구멍 8.0, 후단 슬롯 6.0·구멍 8.0 — 공차 미기재(승인도면 요청). 핀 SHCCG8 g6 ↔ 구멍 8.0 공차 미확인.",
          "REMARK":"구매품. 사용자 지시 스트로크 85→150(B안: 상승 위치 65 상향, 하강 유지). 주문 표기: TA2-2H-150, Retracted Length 274, 후단 5·전단 5(홀 Ø8), 방향 0°, 리미트 스위치 1, 출력신호 0."})
        save_new(d,P_B9J); app.CloseDoc(d.GetTitle)
# ---------- 3. 어셈블리 ----------
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
    def find_mate(name):
        for m in mates_iter():
            if m.Name==name: return m
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
    I3=[[1,0,0],[0,1,0],[0,0,1]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
if STAGE in ("all","asm"):
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); print("components",len(cc),"B9",[n for n in cc if n.startswith("B9")])
    # 거리 메이트: 상승 425→360(상승·1.), 하강 575→510(하강·2.)
    for mname,val,cfgs in (("거리_상승",-ZP_UP,("상승","1.상승했을때(해석)")),("거리_하강",-ZP_DN,("하강","2.하강했을때(해석)"))):
        fd=find_mate(mname); dim=fd.Parameter("D1"); print(mname,"before",dim.SystemValue*1000); r=dim.SetSystemValue3(mm(val),2,None)
        for cfg in cfgs:
            a.ShowConfiguration2(cfg); a.EditRebuild3
            if abs(dim.SystemValue*1000-val)>0.01: dim.SetSystemValue3(mm(val),1,None); a.EditRebuild3
            print("  ",cfg,"J5l z",xform(comps()[J5L])["t_mm"][2])
    a.ShowConfiguration2("상승"); a.EditRebuild3; tj=xform(comps()[J5L])["t_mm"]; assert abs(tj[2]-ZP_UP)<0.02, tj
    # 봉 660 → 580, 호스 J19j → J19k, TA2 B9i → B9j 교체
    cc=comps(); old=[n for n in cc if n.startswith(("J2d_guide_shaft_MISUMI_PSSFAQ20-660","J19j_","B9i_"))]; print("delete",old)
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3; cc=comps(); assert not any(n.startswith(("J2d_guide_shaft_MISUMI_PSSFAQ20-660","J19j_","B9i_")) for n in cc)
    for p in (P_J2,P_UP,P_DN,P_B9J):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    plan=[(P_J2,I3,[x,s*SH_Y,SHAFT_TOP],J1C,"고정_J2d") for x in SH_XS for s in (1,-1)]+[(P_UP,R_HOSE,[0.0,0.0,HOSE_TOP],J1C,"고정_J19kup"),(P_DN,R_HOSE,[0.0,0.0,HOSE_TOP],J1C,"고정_J19kdn"),(P_B9J,I3,[85.0,0.0,-26.0],J1C,"고정_B9j")]
    inserted=[]
    for path,R,t,base,tag in plan:
        c=a.AddComponent5(path,0,"",False,"",mm(t[0]),mm(t[1]),mm(t[2])); assert c is not None, path
        arr=[float(v) for v in R[0]+R[1]+R[2]]+[mm(t[0]),mm(t[1]),mm(t[2]),1.0,0.0,0.0,0.0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
        x=xform(comps()[c.Name2]); assert max(abs(x["R"][i][j]-R[i][j]) for i in range(3) for j in range(3))<1e-3 and max(abs(p-q) for p,q in zip(x["t_mm"],t))<0.02, ("transform",c.Name2,x)
        inserted.append((c.Name2,R,t,base,tag)); print("  inserted",c.Name2,x["t_mm"])
    a.EditRebuild3; EXIST=set(mate_names())
    for name,R,t,base,tag in inserted:
        assert plane_mate(base,name,R,list(t),t,f"{tag}-{name.rsplit('-',1)[1]}"), name; EXIST=set(mate_names())
    up=[n for n,_,_,_,_ in inserted if "up_U190" in n][0]; dn=[n for n,_,_,_,_ in inserted if "dn_bow" in n][0]; b9=[n for n,_,_,_,_ in inserted if n.startswith("B9j")][0]
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; c=comps()[b9]; want="하강" if cfg in ("하강","2.하강했을때(해석)") else "상승"
        c.ReferencedConfiguration=want; a.EditRebuild3; print(f"  [{cfg}] B9j ref cfg",comps()[b9].ReferencedConfiguration)
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); want_up = cfg in ("상승","1.상승했을때(해석)")
        for n,on in ((up,want_up),(dn,not want_up)):
            c=cc[n]; st=c.GetSuppression2
            if on and st!=2: c.SetSuppression2(2)
            if (not on) and st!=0: c.SetSuppression2(0)
        a.EditRebuild3; cc=comps(); assert cc[up].GetSuppression2==(2 if want_up else 0) and cc[dn].GetSuppression2==(0 if want_up else 2)
    a.ShowConfiguration2("상승"); a.EditRebuild3; rep["inserted"]=[i[0] for i in inserted]
if STAGE in ("all","asm","verify"):
    out={}
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); row={n:(xform(c)["t_mm"],box(c),c.GetSuppression2) for n,c in cc.items()}; out[cfg]=row
        print(f"[{cfg}] ww {ww(a)} J5l z {row[J5L][0][2]} fixed {[n for n,c in cc.items() if c.IsFixed]}")
        if cfg in ("상승","하강"):
            for n,(t,b,s) in sorted(row.items()):
                if s==2 and n.startswith(("B10b","J23d","J2d","J19k","B9j","J5l","G13f","J11e","J9f","F4")): print(f"   {n[:46]:46s} t={t} box={b}")
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
    json.dump(out,open(os.path.join(VER,"stroke150b_asm_positions_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
if STAGE in ("all","asm","interf"):
    for cfg in ("상승","하강"):
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); a.ClearSelection2(True)
        idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
        res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
        print(f"[{cfg}] interferences {len(res)}")
        for cs,v in res: print("   ",v,[c[:40] for c in cs])
        rep[f"interf_{cfg}"]=res
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
json.dump(rep,open(os.path.join(VER,f"stroke150b_0917_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("DONE",STAGE)
