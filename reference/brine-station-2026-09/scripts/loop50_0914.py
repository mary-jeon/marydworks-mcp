# 2026-09-14 밤: 50A 호스 루프 라인(C안) — 직선 승강 구조(가이드봉·부시·이동판·TA2) 복원 + 호스 수평 헤어핀(R 200 가정)
#  고정: J1c → G13d → 밸브(G3d, 태성 대용) → 클로즈 니플 N1 → 엘보 E1(0,0,-246, 포트 +z/+y) → 호스니플(+y) → 호스 leg1 +y(x 0) → 반원(뒤쪽 +x) → leg2 -y(x 400)
#  이동: 호스니플(+y) → 엘보 E2(400,0,ZP+65, 포트 +y/-x) → 수평관 P1(x 122~363) → 엘보 E3(85,0,ZP+65, 포트 +x/-z) → 노즐관 P2(판 Ø61 관통 용접, 끝 ZP-100)
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
DATE="2026-09-14"
ENG=20.0; ELB_A=57.0; ELB_D=80.0; ELB_BORE=60.6; ELB_PASS=52.0
Z_VALVE_BOT=-178.0; N1_L=51.0
Z_E1=Z_VALVE_BOT-(N1_L-2*ENG)-ELB_A          # -246
HN_THR=29.0; HN_HEX=8.0; HN_BARB=60.0; HN_L=97.0
HOSE_R=200.0                                   # 가정(야성 미기재)
LEG=176.0; HOSE_X2=2*HOSE_R                    # leg 길이, 다리 간격 400
Y_HOSE_END=ELB_A-ENG+HN_THR+HN_HEX             # 74 (엘보 중심 → 호스 끝)
ZP_UP=-390.0; ZP_DN=-530.0
E_MOV_DZ=65.0                                  # 이동 엘보 중심 = 판 상면 + 65
NOZ_X=85.0; TA2_Y=-80.0; TA2_X=85.0
P1_X0=NOZ_X+ELB_A-ENG; P1_X1=HOSE_X2-ELB_A+ENG; P1_L=P1_X1-P1_X0   # 122~363, L 241
P2_TOP=E_MOV_DZ-ELB_A+ENG; P2_L=P2_TOP+100.0    # 28 → L 128 (끝 ZP-100)
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_FLIP=[[1,0,0],[0,-1,0],[0,0,-1]]
R_E1=[[0,1,0],[-1,0,0],[0,0,1]]                 # 파트 +x → 라인 +y, +z → +z
R_HN=[[1,0,0],[0,0,1],[0,-1,0]]                 # 파트 -z(바브) → 라인 +y
R_E2=[[0,1,0],[0,0,-1],[-1,0,0]]                # 파트 +x → 라인 +y(호스), +z → -x(관)
R_P1=[[0,1,0],[0,0,-1],[-1,0,0]]                # 파트 -z → 라인 +x
R_E3=R_FLIP                                    # 파트 +x → 라인 +x(관), +z → -z(노즐)
def hose_geom(dz):
    c=math.hypot(HOSE_X2,dz); Rp=c/2; a=math.atan2(-dz,HOSE_X2)   # dz<0: 이동단이 아래
    cs,sn=math.cos(a),math.sin(a)
    R=[[cs,0,-sn],[0,1,0],[sn,0,cs]]           # 파트 X → (cs,0,-sn), Y → +y, Z → (sn,0,cs)
    L=2*LEG+math.pi*Rp
    return Rp,R,L
print("E1 z",Z_E1,"P1",P1_X0,P1_X1,P1_L,"P2 top/L",P2_TOP,P2_L)
for tag,zp in (("up",ZP_UP),("dn",ZP_DN)):
    Rp,R,L=hose_geom(zp+E_MOV_DZ-Z_E1); print(f"hose {tag}: dz {zp+E_MOV_DZ-Z_E1} R' {Rp:.1f} L {L:.1f}")
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
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
def clean_orphans(d):
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3; return orphan_sketches(d)
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bodies(d))
def del_feat(d,name):
    d.ClearSelection2(True); d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(name,"SKETCH",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
def extrude(d,depth,name,start_off=0.0,flip=False,dirflag=True,merge=True):
    T0=3 if start_off else 0
    f=d.FeatureManager.FeatureExtrusion3(True,False,dirflag,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,T0,mm(start_off),flip); d.EditRebuild3
    assert f is not None, "extrude "+name; f.Name=name; return f
def cut_blind(d,depth,name,start_off=0.0,flip=False,dirflag=True):
    T0=3 if start_off else 0
    f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,T0,mm(start_off),flip,False); d.EditRebuild3
    assert f is not None, "cut "+name; f.Name=name; return f
def stack_extrude(d,z0,z1,draw,name,plane="정면"):
    # 스케치면 기준 좌표 s(양수) 방향으로 s0~s1 구간(파트 -법선 방향). 결과: 단일 바디, 범위 검증(정면: -z)
    first=(z0==0)
    for flip in (False,True):
        sk=new_sketch(d,plane,draw); f=extrude(d,z1-z0,name,start_off=(0.0 if first else z0),flip=flip)
        bs=bodies(d); zr=[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bs]
        ok=len(bs)==1 and abs(min(b[2] for b in zr)+z1)<0.05
        if ok: return
        del_feat(d,f.Name)
        if first: break
    raise SystemExit("stack seg failed "+name)
def ring(sm,ro,ri):
    sm.CreateCircleByRadius(0,0,0,mm(ro))
    if ri: sm.CreateCircleByRadius(0,0,0,mm(ri))
def set_props(d,props,mat="STS 304"):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍",mat)
    except Exception as ex: print("  mat exc",ex)
def save_new(d,path):
    orph=clean_orphans(d); assert not orph, ("orphans remain",orph)
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d),"orphans 0"); assert ok
def tube_part(path,ro,ri,L,props,fname,mat="STS 304"):
    if os.path.exists(path): print("exists",os.path.basename(path)); return
    d=app.NewDocument(tmpl,0,0,0); stack_extrude(d,0,L,lambda sm: ring(sm,ro,ri),fname)
    bx=partbox(d); assert abs(bx[2]+L)<0.1 and abs(bx[5])<0.1, bx; set_props(d,props,mat); save_new(d,path)
stage=sys.argv[1] if len(sys.argv)>1 else "parts"
if stage=="parts":
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith("파트"): app.CloseDoc(tt); print("closed unsaved",tt)
    # ---- E50 엘보 90° 50A (근사: 하이스텐 4세대 ISO 4144 PT 50A 중심→끝 A 57). 원점 = 중심, 포트 +z / +x
    P=Zp("E50_elbow90_Rc2_ISO4144_A57.SLDPRT")
    if not os.path.exists(P):
        d=app.NewDocument(tmpl,0,0,0)
        # +z 레그: 정면 스케치 원 Ø80, z 0~+57 (dirflag False = +z 방향, 박스로 검증)
        sk=new_sketch(d,"정면",lambda sm: ring(sm,ELB_D/2,0)); f=extrude(d,ELB_A,"레그_z",dirflag=False); bx=partbox(d)
        if bx[5]<ELB_A-0.1: del_feat(d,"레그_z"); sk=new_sketch(d,"정면",lambda sm: ring(sm,ELB_D/2,0)); extrude(d,ELB_A,"레그_z",dirflag=True); bx=partbox(d)
        assert abs(bx[5]-ELB_A)<0.1 and abs(bx[2])<0.1, bx
        # +x 레그: 우측면(YZ) 스케치 원 Ø80, x 0~+57
        for dirflag in (False,True):
            sk=new_sketch(d,"우측면",lambda sm: ring(sm,ELB_D/2,0)); f=extrude(d,ELB_A,"레그_x",dirflag=dirflag); bx=partbox(d)
            if abs(bx[3]-ELB_A)<0.1 and abs(bx[0]+ELB_D/2)<0.1 and len(bodies(d))==1: break
            del_feat(d,"레그_x")
        else: raise SystemExit("elbow x leg")
        # 중심 구: 회전 대신 근사 — 윗면(XZ) 스케치 원 Ø80을 y −40~+40 돌출(코너 채움)
        for dirflag in (False,True):
            sk=new_sketch(d,"윗면",lambda sm: ring(sm,ELB_D/2,0)); f=extrude(d,ELB_D/2,"코너_y+",dirflag=dirflag); bx=partbox(d)
            if abs(bx[4]-ELB_D/2)<0.1 and len(bodies(d))==1: break
            del_feat(d,"코너_y+")
        else: raise SystemExit("elbow corner +")
        for dirflag in (False,True):
            sk=new_sketch(d,"윗면",lambda sm: ring(sm,ELB_D/2,0)); f=extrude(d,ELB_D/2,"코너_y-",dirflag=dirflag); bx=partbox(d)
            if abs(bx[1]+ELB_D/2)<0.1 and len(bodies(d))==1: break
            del_feat(d,"코너_y-")
        else: raise SystemExit("elbow corner -")
        # 유로 Ø52: z 관통(정면 스케치, 양방향 관통) + x 관통(우측면)
        v0=vol(d)
        sk=new_sketch(d,"정면",lambda sm: ring(sm,ELB_PASS/2,0)); f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert f; f.Name="유로_z"
        sk=new_sketch(d,"우측면",lambda sm: ring(sm,ELB_PASS/2,0)); f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert f; f.Name="유로_x"
        v1=vol(d); print("  elbow passage dV",round(v0-v1))
        # 포트 나사부 Ø60.6 × 20: +z 끝(z 37~57), +x 끝(x 37~57) — 오프셋 시작 컷, 결과 원통면 범위로 검증
        def r303_faces(axis):
            out=[]
            for b in bodies(d):
                for fc in b.GetFaces():
                    s=fc.GetSurface
                    if s.IsCylinder and abs(s.CylinderParams[6]*1000-ELB_BORE/2)<0.05:
                        fb=[round(v*1000,1) for v in fc.GetBox]; out.append((fb[2],fb[5]) if axis=="z" else (fb[0],fb[3]))
            return out
        for axis,plane,(s0,s1) in (("z","정면",(ELB_A-ENG,ELB_A)),("x","우측면",(ELB_A-ENG,ELB_A))):
            done=False
            for dirflag in (True,False):
                for flip in (False,True):
                    sk=new_sketch(d,plane,lambda sm: ring(sm,ELB_BORE/2,0))
                    f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(ENG),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(s0),flip,False); d.EditRebuild3
                    if f is None: del_feat(d,sk); continue
                    f.Name="포트컷_"+axis; fr=r303_faces(axis)
                    if any(abs(a-s0)<0.3 and abs(b-s1)<0.3 for a,b in fr) and len(bodies(d))==1: done=True; break
                    del_feat(d,"포트컷_"+axis)
                if done: break
            assert done, "port cut "+axis
        bx=partbox(d); print("E50 box",bx,"vol",round(vol(d)),"ww",ww(d)); assert not ww(d)
        set_props(d,{"TITLE":"ELBOW 90deg 50A Rc2 (SUS304, ISO 4144)",
          "SPEC":"하이스텐 4세대 스텐 엘보 50A(2): 암나사 PT(Rc)2 양쪽, 중심→끝 A 57(제조사 페이지 원문값), SUS304, ISO 4144. 3D 근사형상(몸통 Ø80·유로 Ø52·포트 나사부 Ø60.6×20 표현 컷) — 제조사 3D 없음(histen.co.kr 확인).",
          "Material":"STS304","QT'Y":"3","DATE":DATE,"REMARK":"구매품(하이스텐 menu=105 prodseq=261). 근사형상·나사 미표현. 국내 동급(시흥에스티·대성 등)으로 대체 가능."})
        save_new(d,P)
    # ---- N1 클로즈 니플 R2 L51 (KS B 1533 50A 최소 51)
    tube_part(Zp("N1_close_nipple_R2_KS_L51.SLDPRT"),30.25,26.35,N1_L,{
      "TITLE":"CLOSE NIPPLE R2 (KS B 1533 50A)","SPEC":"KS B 1533 클로즈 니플 50A(2): 수나사 R2 양쪽, SUS304, L 51(규격 최소), OD 60.5·보어 52.7(Sch40). 밸브 G2 하단 20 + 엘보 E1 Rc2 상단 20 물림, 노출 11. 나사 미표현.",
      "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"규격품(KS B 1533 원문 50A 행)."},"클로즈니플_OD60.5_L51")
    # ---- P1 수평관 50A Sch40 L241 (양단 R2)
    tube_part(Zp(f"P1_pipe_50A_Sch40_L{P1_L:g}.SLDPRT"),30.25,26.35,P1_L,{
      "TITLE":"PIPE 50A 수평관 (이동판 위, 엘보 E3↔E2)","SPEC":f"STS304 50A Sch40(OD 60.5 t3.9, JIS G 3459 표8) L {P1_L:g}, 양단 수나사 R2(KS B 0222, 각 20 물림, 나사 미표현). 노즐 엘보 E3(+x 포트)에서 호스 엘보 E2(-x 포트)까지, 축 z = 판 상면 + {E_MOV_DZ:g}.",
      "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. E2·호스 끝은 이 관에 캔틸레버(판 밖 x 135~431) — 지지 브래킷 여부 미결."},"수평관_OD60.5")
    # ---- P2 노즐관 50A Sch40 L128 (상단 R2, 판 Ø61 관통 용접)
    tube_part(Zp(f"P2_nozzle_pipe_50A_Sch40_L{P2_L:g}.SLDPRT"),30.25,26.35,P2_L,{
      "TITLE":"NOZZLE PIPE 50A (이동판 관통 용접)","SPEC":f"STS304 50A Sch40(OD 60.5 t3.9) L {P2_L:g}. 상단 20 수나사 R2 → 엘보 E3 하단 Rc2. 이동판 J5h 구멍 Ø61(x {NOZ_X:g}, y 0) 관통, 양면 필릿 용접. 노즐 끝 = 판 상면 −100 → 지상고 상승 1,560 / 하강 1,420(로봇 개구 상단 아래 68).",
      "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 로봇 개구 안 여유: 뒤 13·앞 137·좌우 75(x 85 편심)."},"노즐관_OD60.5")
    # ---- 호스 J19g 상승/하강 (평면 헤어핀 스윕: 경로 정면(XY), 프로파일 윗면)
    for tag,zp in (("up",ZP_UP),("dn",ZP_DN)):
        Rp,R,L=hose_geom(zp+E_MOV_DZ-Z_E1)
        P=Zp(f"J19g_hose_YASUNG_HSPF-050_loop_{tag}_R{Rp:.0f}.SLDPRT")
        if os.path.exists(P): print("exists",os.path.basename(P)); continue
        done=False
        for direction in (1,-1):
            dh=app.NewDocument(tmpl,0,0,0)
            assert sel_plane(dh,"정면"); dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
            sm.CreateLine(0,0,0,0,mm(LEG),0); sm.CreateArc(mm(Rp),mm(LEG),0,0,mm(LEG),0,mm(2*Rp),mm(LEG),0,direction); sm.CreateLine(mm(2*Rp),mm(LEG),0,mm(2*Rp),0,0)
            sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
            Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
            bx_s=None
            print(f"  hose {tag} direction {direction}: sketch length {Ls:.1f} (target {L:.1f})")
            if abs(Ls-L)>2.0: app.CloseDoc(dh.GetTitle); continue
            assert sel_plane(dh,"윗면"); dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(31.0)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(26.25)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            dh.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or dh.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
            dh.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or dh.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
            f=None
            for attempt in ("swept3","swept4"):
                try:
                    if attempt=="swept3": f=dh.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                    else: f=dh.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                    if f: break
                except Exception as ex: print("  ",attempt,"exc",ex)
            if not f: app.CloseDoc(dh.GetTitle); continue
            dh.EditRebuild3; bx=partbox(dh); print(f"  hose {tag} box {bx} bodies {len(bodies(dh))}")
            # 검증: 상단 y = LEG+Rp+31, x 범위 -31 ~ 2Rp+31
            if not (len(bodies(dh))==1 and abs(bx[4]-(LEG+Rp+31))<0.5 and abs(bx[3]-(2*Rp+31))<0.5): app.CloseDoc(dh.GetTitle); continue
            set_props(dh,{"TITLE":f"HOSE 50A LOOP ({'상승' if tag=='up' else '하강'} 상태) — YASUNG HSPF-050",
              "SPEC":f"야성하이텍 슈퍼스프링호스(무독) HSPF-050: 내경 50.0±1.5·외경 62.0±1.5·0.4/1.6 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 수평 헤어핀 루프: 다리 {LEG:g}×2 + 반원 R{Rp:.1f}(양단 높이차 {abs(zp+E_MOV_DZ-Z_E1):g}로 기운 평면), 자유길이 {L:.0f}. 굽힘반경 설계값 {HOSE_R:g}은 가정(카탈로그 미기재) — 실물 굽힘 측정 또는 야성 확인 필요. 3D 내경은 바브 위 52.5로 표현. 절단 길이 = 긴 쪽(하강) + 바브 2×60.",
              "Material":"PVC","QT'Y":"1","DATE":DATE,"REMARK":"구매품(야성판매). 상승↔하강 자유길이 차는 실물 호스가 처짐으로 흡수(표현은 상태별 파트 2개). −30 ℃·염수 적합성 원문 없음."},mat="PVC 경질")
            save_new(dh,P); done=True; break
        assert done, "hose "+tag
    # ---- J5h 이동판: J5e SaveAs → 소켓 구멍 (0,10)Ø32 → (85,0)Ø61
    P5=Zp("J5e_moving_plate_180x540_t8.SLDPRT"); P5h=Zp("J5h_moving_plate_180x540_t8.SLDPRT")
    if not os.path.exists(P5h):
        d=act(P5); e=I4(); w=I4(); ok=d.Extension.SaveAs(P5h,0,1,NOD,e,w); print("SaveAs J5h",ok,e.value); assert ok
        d=act(P5h)
        if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
        for s in list(pv(sk,"GetSketchSegments") or []):
            ty=s.GetType() if callable(s.GetType) else s.GetType
            if ty==1:
                cpt=pv(s,"GetCenterPoint2")
                try: cx,cy=cpt[0]*1000,cpt[1]*1000
                except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
                r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
                if abs(cx)<0.5 and abs(cy-10)<0.5 and 15<r<18: s.Select4(True,NOD); n+=1
        if n: d.Extension.DeleteSelection2(0); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(mm(NOZ_X),0,0,mm(30.5)); d.SketchManager.AddToDB=False
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); bx=partbox(d); print("J5h hole edited",n,"box",bx,"ww",ww(d)); assert not ww(d) and n==1
        cp=d.Extension.CustomPropertyManager("")
        for k in ("TITLE","SPEC"):
            s_=cp.Get(k) or ""; s_=s_.replace("소켓 Ø32(KS Rp 소켓 OD)","노즐관 P2 Ø61 관통 구멍(85,0) 양면 필릿 용접").replace("소켓 Ø32","노즐관 Ø61(85,0)"); cp.Set2(k,s_)
        cp.Set2("DATE",DATE); orph=clean_orphans(d); assert not orph; e=I4(); w=I4(); print("save J5h",d.Save3(1,e,w),e.value)
    else: print("J5h exists")
    # ---- G3d 속성: 태성 정본, Tameson 형상 대용
    d=act(Zp("G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT"))
    set_props(d,{"TITLE":"BALL VALVE 3PC 50A (태성자동밸브 S3, 형상 대용: Tameson BL2SA3-200 STEP)",
      "SPEC":"태성자동밸브 3PC 나사식 볼밸브 50A(2) 자동장착형(S3): 면간 L 130(±1.6)·보어 Ø50·Body/Ball SUS304(SUS316)·Seat PTFE·10 kgf/cm²·유체 −10~90 ℃(태성 카탈로그 2013-36 p.12·도면 A110117-01-04·2012판 p.17). 밸브 단품 형번·ISO 패드(F05/F07)·스템 각형(□14/17)·나사(PT/PF)·질량·토크는 원문 미기재 → 태성 확인. 3D 형상 대용: Tameson BL2SA3-200(G2, L140, F05/F07 □14, 패드 78) — 면간 10 mm 차이는 스택에 미반영(태성 확정 시 재조정).",
      "Material":"STS316","QT'Y":"1","DATE":DATE,
      "REMARK":"로봇과 동일 제조사(태성) 지정(사용자 09-14). 형상 대용 STEP: tameson.com bl2sa3-200.step. 포트컷_상/하 = 나사부 표현. 액추에이터 코사 KE008(F05/F07 □14) 직결 가능 여부는 태성 패드·스템 확정 후."})
    e=I4(); w=I4(); print("save G3d props",d.Save3(1,e,w),e.value)
elif stage=="asm":
    a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); title=a.GetTitle.replace(".SLDASM","")
    def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
    def set_T(c,R,t):
        arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
        xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
    def move_fixed(c,R,t):
        a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
        set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
    def sel_comp(n): a.ClearSelection2(True); return a.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
    def set_supp(c,active):
        if (c.GetSuppression2==2)==active: return
        a.ClearSelection2(True); c.Select4(False,NOD,False)
        if active: a.EditUnsuppress2
        else: a.EditSuppress2
        a.ClearSelection2(True)
    states={}
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); cc=comps(); states[cfg]=[cc[n].GetSuppression2 for n in cc if n.startswith("G3d_")][0]
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    for n in list(cc):
        if n.startswith(("G13e_","J17c_","J19f_","J5g_")) or n.startswith(("J23b_shaft_support_MISUMI_SHFSS16_STEP-3","J23b_shaft_support_MISUMI_SHFSS16_STEP-4")):
            sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    # 봉 J2d → J2c(590) 복원
    P2c=Zp("J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT"); olds=[n for n in cc if n.startswith("J2d_")]
    if olds:
        if app.GetOpenDocumentByName(P2c) is None: open_doc(app,P2c,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P2c,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J2d→J2c",ok); assert ok; cc=comps()
    up_R,up_RM,_=hose_geom(ZP_UP+E_MOV_DZ-Z_E1); dn_R,dn_RM,_=hose_geom(ZP_DN+E_MOV_DZ-Z_E1)
    NEW={"E50":("E50_elbow90_Rc2_ISO4144_A57.SLDPRT",3),"N1":("N1_close_nipple_R2_KS_L51.SLDPRT",1),"P1":(f"P1_pipe_50A_Sch40_L{P1_L:g}.SLDPRT",1),"P2":(f"P2_nozzle_pipe_50A_Sch40_L{P2_L:g}.SLDPRT",1),
         "HUP":(f"J19g_hose_YASUNG_HSPF-050_loop_up_R{up_R:.0f}.SLDPRT",1),"HDN":(f"J19g_hose_YASUNG_HSPF-050_loop_dn_R{dn_R:.0f}.SLDPRT",1),
         "J5h":("J5h_moving_plate_180x540_t8.SLDPRT",2),"B10":("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",4),"B9g":("B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT",1),
         "J8e":("J8e_lug_PL6_40x26.SLDPRT",1),"J9d":("J9d_lug_PL6_40x31.SLDPRT",2),"G11f":("G11f_MISUMI_SHCCG8-22.8_pin.SLDPRT",1),"J11e":("J11e_MISUMI_SHCCG8-18_pin.SLDPRT",2),"H16c":("H16c_hose_nipple_PT2x52.5_L97.SLDPRT",2)}
    added={}
    for key,(fn,cnt) in NEW.items():
        p=Zp(fn); pre=fn.replace(".SLDPRT","")
        have=[n for n in comps() if n.startswith(pre+"-")]
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        for i in range(cnt-len(have)):
            c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0); assert c, fn
        a.EditRebuild3; added[key]=sorted([n for n in comps() if n.startswith(pre+"-")],key=lambda n:int(n.rsplit("-",1)[1])); print("added",key,added[key])
    cc=comps()
    PLACE={}   # name: (R, t, group) group fix/up/dn
    PLACE[added["N1"][0]]=(I3,(0,0,Z_VALVE_BOT+ENG),"fix")
    PLACE[added["E50"][0]]=(R_E1,(0,0,Z_E1),"fix")
    PLACE[added["H16c"][0]]=(R_HN,(0,ELB_A-ENG,Z_E1),"fix")
    # B9g(TA2)는 참조구성 상승/하강로 로드 길이 처리(기존 관례) — 위치 (85,-80,-26)
    PLACE[added["B9g"][0]]=(I3,(TA2_X,TA2_Y,-26.0),"fix"); PLACE[added["J8e"][0]]=(I3,(TA2_X,TA2_Y,-26.0),"fix"); PLACE[added["G11f"][0]]=(I3,(TA2_X,TA2_Y-11.2,-26.0),"fix")
    for i,(zp,grp) in enumerate(((ZP_UP,"up"),(ZP_DN,"dn"))):
        ze=zp+E_MOV_DZ
        PLACE[added["J5h"][i]]=(I3,(0,0,zp),grp); PLACE[added["J9d"][i]]=(I3,(TA2_X,TA2_Y,zp),grp); PLACE[added["J11e"][i]]=(I3,(TA2_X,TA2_Y-8.8,zp+25.0),grp)
        PLACE[added["B10"][2*i]]=(I3,(45,240,zp),grp); PLACE[added["B10"][2*i+1]]=(I3,(45,-240,zp),grp)
    # 이동 부품 중 인스턴스 1개(H16c-2, P1, P2, E3): 상승 위치에 두고 하강에서는 -140 이동(구성별 Transform)
    PLACE[added["H16c"][1]]=(R_HN,(HOSE_X2,ELB_A-ENG,ZP_UP+E_MOV_DZ),"mov1")
    PLACE[added["P1"][0]]=(R_P1,(P1_X0,0,ZP_UP+E_MOV_DZ),"mov1")
    PLACE[added["E50"][2]]=(R_E3,(NOZ_X,0,ZP_UP+E_MOV_DZ),"mov1")   # E3 (E50-3)
    PLACE[added["P2"][0]]=(I3,(NOZ_X,0,ZP_UP+P2_TOP),"mov1")
    PLACE[added["HUP"][0]]=(up_RM,(0,Y_HOSE_END,Z_E1),"up"); PLACE[added["HDN"][0]]=(dn_RM,(0,Y_HOSE_END,Z_E1),"dn")
    # E50 인스턴스 역할 정리: -1 E1(fix), -2 E2(mov1), -3 E3(mov1)
    PLACE[added["E50"][1]]=(R_E2,(HOSE_X2,0,ZP_UP+E_MOV_DZ),"mov1")
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,(R,t,grp) in PLACE.items():
            c=cc[n]; tt=t
            if grp=="mov1" and cfg=="하강": tt=(t[0],t[1],t[2]-(ZP_UP-ZP_DN))
            STRUCT=n.startswith(("J5h","J9d","J8e","B10"))
            if cfg=="상승": want=grp in ("fix","up","mov1")
            elif cfg=="하강": want=grp in ("fix","dn","mov1")
            elif STRUCT: want=(grp=="fix") or (grp=="up" and cfg.startswith("1.")) or (grp=="dn" and cfg.startswith("2."))
            else: want=(states[cfg]==2)
            set_supp(c,True); move_fixed(c,R,tt)
            if n.startswith("B9g_") and cfg in ("상승","하강"):
                try: c.ReferencedConfiguration=cfg
                except Exception as ex: print("  refcfg exc",ex)
            set_supp(c,bool(want))
        a.ForceRebuild3(False); cc=comps()
        info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(PLACE)}
        print(f"[{cfg}] ww {ww(a)}")
        for n,v_ in info.items(): print("   ",n[:52],v_)
    a.ShowConfiguration2("상승"); a.EditRebuild3
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs)
    assert not any(r.startswith(("G13e_","J17c_","J19f_","J5g_","J2d_","K1_","K2_","K3_","K4_","J5f_")) for r in refs), refs
    json.dump({"refs":refs,"E1":Z_E1,"P1":[P1_X0,P1_X1],"hose":{"up":up_R,"dn":dn_R}},open(os.path.join(VER,"loop50_asm_0914.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("asm stage done (not saved)")
stop.set()
