# 2026-09-15: 32A 라인(사용자 확정: 호스 직선 승강·탱크 고정·32A 강행) — 파트 생성/수정 + 어셈블리 재구성
#  스택(라인 z, J1c 상면 0): G13f 니플 0~−50(판 10 삽입) → 밸브 G3e −35~−135(물림 15) → H16d 고정 −120(육각 −140.4~−154.6, 바브 −207)
#   → 호스(하강 직선 L 335.8 / 상승 스텁 52.4×2 + 4원호 R≈36.5, +y 불룩 74) → H16d 뒤집음(원점 ZP−15, 육각 ZP+5.4~19.6) → 소켓 G13g ZP~ZP−51(판 플러시) → 노즐 G13f ZP−36~ZP−86
#  ZP 상승 −425 / 하강 −510 (노즐 끝 1,539 / 1,454). 봉 (0,±240), TA2 (0,−110), 러그 J8e 고정·J9f 이동(핀 +60).
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-15"
ENG=15.0; NIP_L=50.0; VALVE_L=100.0; PAD=63.0
Z_VALVE_TOP=-NIP_L+ENG; Z_VALVE_C=Z_VALVE_TOP-VALVE_L/2; Z_VALVE_BOT=Z_VALVE_TOP-VALVE_L      # −35 / −85 / −135
HN_THR=20.4; HN_HEX=14.2; HN_L=87.0; HN_BARB=HN_L-HN_THR-HN_HEX                                  # 52.4
Z_HN_FIX=Z_VALVE_BOT+ENG; HOSE_TOP=Z_HN_FIX-HN_THR-HN_HEX                                        # −120 / −154.6
SOCK_L=51.0; NOZ_X=SOCK_L-ENG+NIP_L                                                             # 86: 판 상면 → 노즐 끝
ZP_UP=-511.0+NOZ_X; ZP_DN=-596.0+NOZ_X; STROKE=ZP_UP-ZP_DN                                       # −425 / −510 / 85
HN_MOV_ORG=lambda zp: zp-ENG; HOSE_BOT=lambda zp: HN_MOV_ORG(zp)+HN_THR+HN_HEX                   # zp+19.6
L_HOSE=HOSE_TOP-HOSE_BOT(ZP_DN); D_UP=HOSE_TOP-HOSE_BOT(ZP_UP)                                    # 335.8 / 250.8
TA2_X=0.0; TA2_Y=-110.0; PIN_H=60.0; LUG_H=69.0
SH_X=0.0; SH_Y=240.0
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_FLIP=[[1,0,0],[0,-1,0],[0,0,-1]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
R_G3D=[[0,1,0],[-1,0,0],[0,0,1]]; R_B4D=[[0,0,1],[0,1,0],[-1,0,0]]; R_B10=[[0,0,-1],[0,1,0],[1,0,0]]; R_J23=[[0,1,0],[-1,0,0],[0,0,1]]; R_K6=[[1,0,0],[0,-1,0],[0,0,-1]]
STUB=HN_BARB
def solve_bow():
    f=lambda t: math.sin(t)/t-(D_UP-2*STUB)/(L_HOSE-2*STUB); lo,hi=1e-3,3.0
    for _ in range(100):
        m=(lo+hi)/2
        if f(lo)*f(m)<=0: hi=m
        else: lo=m
    t=(lo+hi)/2; return (L_HOSE-2*STUB)/(4*t),t
R_BOW,T_BOW=solve_bow(); BULGE=2*R_BOW*(1-math.cos(T_BOW))
print(f"stack: valve {Z_VALVE_TOP}~{Z_VALVE_BOT}, hose top {HOSE_TOP}, ZP {ZP_UP}/{ZP_DN}, hose L {L_HOSE:.1f} D_UP {D_UP:.1f} bow R {R_BOW:.2f} t {math.degrees(T_BOW):.1f} bulge {BULGE:.1f}")
def segs_from(list_):
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    for it in list_:
        if it[0]=="line":
            dd=it[1]; x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1; continue
        rad,ang=it[1],it[2]
        if abs(ang)<1e-9: continue
        side=1 if ang>0 else -1
        cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
        h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
        segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    return segs,(x,y)
segs_up,end_up=segs_from([("line",STUB),("arc",R_BOW,T_BOW),("arc",R_BOW,-T_BOW),("arc",R_BOW,-T_BOW),("arc",R_BOW,T_BOW),("line",STUB)])
print("bow end",[round(v,2) for v in end_up],"(expect 0,",-D_UP,")")
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
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
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
    orph=clean_orphans(d); assert not orph, ("orphans remain",orph)
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d),"orphans 0"); assert ok
def circ_xy(s):
    cpt=pv(s,"GetCenterPoint2")
    try: cx,cy=cpt[0]*1000,cpt[1]*1000
    except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
    r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
    return cx,cy,r
def edit_circles(d,sketch,rule,new_circles):
    # rule(cx,cy,r)->True 이면 삭제; new_circles [(cx,cy,r)] 추가; 매달린 구속 정리
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
HOSE_SPEC="야성하이텍 슈퍼스프링호스(무독) HSPF-032: 내경 32.0±1.0·외경 41.0±1.0·0.5/2.5 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 3D 내경은 바브(Ø34) 위 늘어난 34로 표현. 절단 = 자유길이 336 + 바브 2×52 ≈ 440. 최소 굽힘반경 카탈로그 미기재."
P_DN=Zp(f"J19i_hose_YASUNG_HSPF-032_dn_straight_L{L_HOSE:.0f}.SLDPRT"); P_UP=Zp(f"J19i_hose_YASUNG_HSPF-032_up_bow_R{R_BOW:.0f}.SLDPRT")
P5K=Zp("J5k_moving_plate_80x540_t8.SLDPRT"); P9F=Zp("J9f_lug_PL6_40x69_pin60.SLDPRT")
stage=sys.argv[1] if len(sys.argv)>1 else "parts"
if stage=="parts":
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith("파트"): app.CloseDoc(tt); print("closed unsaved",tt)
    # ---- 호스 하강(직선)
    if not os.path.exists(P_DN):
        d=app.NewDocument(tmpl,0,0,0); new_sketch(d,"정면",lambda sm:(sm.CreateCircleByRadius(0,0,0,mm(20.5)),sm.CreateCircleByRadius(0,0,0,mm(17.0)))); extrude_neg(d,L_HOSE,"호스_직선")
        bx=bbox(d); assert abs(bx[2]+L_HOSE)<0.1, bx
        set_props(d,{"TITLE":"HOSE 32A (하강 상태, 직선) — YASUNG HSPF-032","SPEC":HOSE_SPEC+f" 하강(승강 {STROKE:g}): 직선, 낙차 {L_HOSE:.1f}.","Material":"PVC","QT'Y":"1","DATE":DATE,
          "REMARK":"구매품(야성판매). 사용자 결정(09-15) 「호스 직선·일직선 승강·탱크 고정·32A 강행」. −30 ℃·염수 적합성 원문 없음."},mat="PVC 경질"); save_new(d,P_DN)
    # ---- 호스 상승(활)
    if not os.path.exists(P_UP):
        done=False
        for direction in (1,-1):
            dh=app.NewDocument(tmpl,0,0,0)
            assert sel_plane(dh,"정면"); dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
            for sg in segs_up:
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
            if not (abs(bx[1]+D_UP)<1.5 and (abs(bx[3]-(BULGE+20.5))<2.0 or abs(bx[0]+(BULGE+20.5))<2.0)): app.CloseDoc(dh.GetTitle); continue
            set_props(dh,{"TITLE":"HOSE 32A (상승 상태, 활 굽힘) — YASUNG HSPF-032","SPEC":HOSE_SPEC+f" 상승(낙차 {D_UP:.1f}): 바브 구간 {STUB:.1f}×2 직선 + 4원호 활 R{R_BOW:.1f} ±{math.degrees(T_BOW):.1f}°, +y로 {BULGE:.0f} 불룩. **R{R_BOW:.0f} = 내경의 {R_BOW/32:.2f}배 — 스프링호스 통례(1.5~2배)보다 작아 실물 접힘(킹크) 위험, 굽힘반경 미확인.**","Material":"PVC","QT'Y":"1","DATE":DATE,
              "REMARK":"사용자 결정(09-15) 「강제로 꾸겨 넣어서 32로」에 따른 형상. 실물 U자 접힘 간격 ≤32(반경 36)이어야 성립."},mat="PVC 경질")
            save_new(dh,P_UP); done=True; break
        assert done, "bow hose"
    # ---- 이동판 J5k 80×540 t8: 소켓 Ø49 @(0,0), 부시 Ø28.5 + 4×Ø3.3 PCD38 @(0,±240)
    if not os.path.exists(P5K):
        d=app.NewDocument(tmpl,0,0,0)
        def draw(sm):
            sm.CreateCornerRectangle(mm(-40),mm(-270),0,mm(40),mm(270),0); sm.CreateCircleByRadius(0,0,0,mm(24.5))
            for sy in (SH_Y,-SH_Y):
                sm.CreateCircleByRadius(mm(SH_X),mm(sy),0,mm(14.25))
                for dx,dy in ((19,0),(-19,0),(0,19),(0,-19)): sm.CreateCircleByRadius(mm(SH_X+dx),mm(sy+dy),0,mm(1.65))
        new_sketch(d,"정면",draw); extrude_neg(d,8.0,"판_t8"); bx=bbox(d); assert abs(bx[0]+40)<0.1 and abs(bx[3]-40)<0.1 and abs(bx[2]+8)<0.1, bx
        set_props(d,{"TITLE":"MOVING PLATE 80x540 t8 (노즐 축 대칭)","SPEC":"PL 8T STS304 80×540(x ±40, y ±270). 구멍: 소켓 SFS3-32 Ø49(0,0) 상면 플러시 삽입 양면 필릿 용접 / 부시 LHFRW16 Ø28.5 + M4 탭 4(PCD 38) @(0,±240). 러그 J9f 밑면 용접 @(0,−110). 종전 180×540에서 노즐 축 중심으로 축소(사용자 09-15 「샤프트바 중앙」).",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 하중 검토·Simulation 미실시(종전 §3-1은 J5e 기준)."},mat="STS 304"); save_new(d,P5K)
    # ---- 이동 러그 J9f PL6 40×69, 핀 Ø8 @60: 윗면(XZ) 스케치 → y 6 돌출. 원점 = 판 상면 중앙(x 0, z 0), 위로 69
    if not os.path.exists(P9F):
        d=app.NewDocument(tmpl,0,0,0)
        def drawlug(sm):
            sm.CreateCornerRectangle(mm(-20),0,0,mm(20),mm(LUG_H),0); sm.CreateCircleByRadius(0,mm(PIN_H),0,mm(4.0))
        sk=new_sketch(d,"윗면",drawlug)
        f=d.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(6.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f; f.Name="러그_t6"
        bx=bbox(d); print("J9f box",bx)
        # 판 두께가 ±y 중 어느 쪽으로 갔는지, z 부호는 어느 쪽인지 기록(배치 시 보정)
        set_props(d,{"TITLE":"LUG PL6 40x69 (이동판 위, TA2 로드 클레비스 핀 @60)","SPEC":"PL 6T STS304 40(x)×69(z), 핀 구멍 Ø8(SHCCG8 h7) 중심 판 상면 위 60. 이동판 J5k 상면 (0,−110)에 밑면 필릿 용접. TA2-2H 로드 클레비스 U(내폭 17.6/외폭 22.4)에 삽입.",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 종전 J9d(핀 25)에서 승강 85·ZP −425에 맞춰 핀 높이 60. 500 N 수계산·Simulation 미갱신."},mat="STS 304"); save_new(d,P9F)
        json.dump({"box":bx},open(os.path.join(VER,"j9f_build_0915.json"),"w"))
    # ---- J1c: 유로 구멍 Ø61→Ø43, 봉 구멍 (45,±240)→(0,±240), 홀더 탭(25|65,±240) 삭제 — 모든 스케치 순회
    P1=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); d=act(P1)
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    for skn,skt in feats(d):
        if skt!="ProfileFeature": continue
        d.ClearSelection2(True)
        if not d.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0): continue
        d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); found=[]
        for s in list(pv(sk,"GetSketchSegments") or []):
            ty=s.GetType() if callable(s.GetType) else s.GetType
            if ty==1: found.append(circ_xy(s))
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        big=[c for c in found if abs(c[0])<0.5 and abs(c[1])<0.5 and 30<c[2]<31]
        shafts=[c for c in found if abs(c[0]-45)<0.5 and abs(abs(c[1])-240)<0.5 and 8<c[2]<8.5]
        taps=[c for c in found if abs(abs(c[1])-240)<0.5 and (abs(c[0]-25)<0.5 or abs(c[0]-65)<0.5) and c[2]<3]
        if big or shafts or taps:
            print("J1c",skn,"big",big,"shafts",shafts,"taps",taps)
            new=[]
            if big: new.append((0,0,21.5))
            if shafts: new+= [(SH_X,SH_Y,8.25),(SH_X,-SH_Y,8.25)]
            n=edit_circles(d,skn,lambda cx,cy,r: (abs(cx)<0.5 and abs(cy)<0.5 and 30<r<31) or (abs(cx-45)<0.5 and abs(abs(cy)-240)<0.5 and 8<r<8.5) or (abs(abs(cy)-240)<0.5 and (abs(cx-25)<0.5 or abs(cx-65)<0.5) and r<3), new)
            print("  edited",n,"ww",ww(d))
    d.ForceRebuild3(False); assert not ww(d), ww(d)
    cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("SPEC") or ""
    s_=s_.replace("유로 구멍 Ø61(0,0): 배럴 니플 G13d R2(50A)를 10 삽입해 밑면 필릿 용접","유로 구멍 Ø43(0,0): 배럴 니플 G13f R1-1/4(ONDA SFN2-32, 32A)를 10 삽입해 밑면 필릿 용접")
    s_=s_.replace("가이드봉 Ø16.5 관통 2개소 @(45,±240)","가이드봉 Ø16.5 관통 2개소 @(0,±240)")
    cp.Set2("SPEC",s_+" | 09-15: 봉 (0,±240)로 이동, 홀더 탭 삭제(SK16 서포트는 L브래킷 K6 용접), TA2 러그 J8e @(0,−110)."); cp.Set2("DATE",DATE)
    orph=clean_orphans(d); assert not orph; e=I4(); w=I4(); print("save J1c",d.Save3(1,e,w),e.value)
    # ---- B9g: 하강 구성 로드 이동 140 → 85
    PB=Zp("B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT"); d=act(PB)
    try:
        dim=d.Parameter("D3@로드_하강_이동"); print("B9g dim current",dim.SystemValue*1000)
        cur=d.ConfigurationManager.ActiveConfiguration.Name; d.ShowConfiguration2("하강")
        ok=False
        try: ok=dim.SetSystemValue3(mm(STROKE),2,["하강"])
        except Exception as ex: print("  SetSystemValue3 exc",ex)
        if not ok:
            try: dim.SystemValue=mm(STROKE); ok=True
            except Exception as ex: print("  SystemValue exc",ex)
        d.EditRebuild3; v=dim.SystemValue*1000; d.ShowConfiguration2(cur); d.EditRebuild3
        print("B9g 하강 rod dim →",v,"ok",ok)
        cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("SPEC") or ""
        if "승강 85" not in s_: cp.Set2("SPEC",s_+" | 09-15: 승강 85로 축소(하강 구성 로드 −85). 스트로크 140 실린더를 제어 리미트로 85만 쓰거나 TA2-2H-85(RL 339) 발주 — 사수 결정.")
        e=I4(); w=I4(); print("save B9g",d.Save3(1,e,w),e.value)
    except Exception as ex: print("B9g dim edit failed",ex)
elif stage=="asm":
    j9=json.load(open(os.path.join(VER,"j9f_build_0915.json")))["box"]
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
        a.ShowConfiguration2(cfg); cc=comps(); g=[cc[n].GetSuppression2 for n in cc if n.startswith("G3d_")]; states[cfg]=g[0] if g else 0
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    for n in list(cc):
        if n.startswith(("E50_","N1_","P1_","P2_","J19g_","J19h_","J5h_","J5i_","H16c_","G13d_","G3d_","B4d_","G13e_","J17c_","J9d_")):
            sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    NEW={"G13f":("G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP.SLDPRT",3),"G3e":("G3e_valve_3PC_32A_TAESUNG_S3_alt_Tameson_BL2SA3-114.SLDPRT",1),"B4e":("B4e_actuator_KOSAPLUS_KE005-F357C14-DC.SLDPRT",1),
         "H16d":("H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP.SLDPRT",3),"G13g":("G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP.SLDPRT",2),
         "HDN":(os.path.basename(P_DN),1),"HUP":(os.path.basename(P_UP),1),"J5k":(os.path.basename(P5K),2),"J9f":(os.path.basename(P9F),2)}
    added={}
    for key,(fn,cnt) in NEW.items():
        p=Zp(fn); pre=fn.replace(".SLDPRT","")
        have=[n for n in comps() if n.startswith(pre+"-")]
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        for i in range(cnt-len(have)):
            c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0); assert c, fn
        a.EditRebuild3; added[key]=sorted([n for n in comps() if n.startswith(pre+"-")],key=lambda n:int(n.rsplit("-",1)[1])); print("added",key,added[key])
    cc=comps()
    # J9f 방향: 파트 박스에서 두께 방향(y) 부호와 z 부호 확인 → 라인: 판 상면 위 +z, 두께 y ±3
    ysign=1 if j9[4]>1 else -1; zsign=1 if j9[5]>1 else -1
    R_J9=[[1,0,0],[0,ysign*(1 if zsign>0 else -1),0],[0,0,zsign]]   # 행렬식 +1 유지
    if np.linalg.det(np.array(R_J9))<0: R_J9=[[-1,0,0],[0,R_J9[1][1],0],[0,0,R_J9[2][2]]]
    yoff=-3.0 if (ysign*R_J9[1][1])>0 else 3.0   # 두께 6이 y −3~+3 이 되도록
    PLACE={}
    PLACE[added["G13f"][0]]=(I3,(0,0,0),"fix"); PLACE[added["G3e"][0]]=(R_G3D,(0,0,Z_VALVE_C),"fix"); PLACE[added["B4e"][0]]=(R_B4D,(-PAD,0,Z_VALVE_C),"fix"); PLACE[added["H16d"][0]]=(I3,(0,0,Z_HN_FIX),"fix")
    for i,(zp,grp) in enumerate(((ZP_UP,"up"),(ZP_DN,"dn"))):
        PLACE[added["H16d"][1+i]]=(R_FLIP,(0,0,HN_MOV_ORG(zp)),grp); PLACE[added["G13g"][i]]=(I3,(0,0,zp),grp); PLACE[added["G13f"][1+i]]=(I3,(0,0,zp-SOCK_L+ENG),grp)
        PLACE[added["J5k"][i]]=(I3,(0,0,zp),grp); PLACE[added["J9f"][i]]=(R_J9,(TA2_X,TA2_Y+yoff,zp),grp)
    PLACE[added["HDN"][0]]=(I3,(0,0,HOSE_TOP),"dn"); PLACE[added["HUP"][0]]=(R_HOSE,(0,0,HOSE_TOP),"up")
    for n in cc:
        if n.startswith(("B9g_","J8e_")): PLACE[n]=(I3,(TA2_X,TA2_Y,-26.0),"fix")
        elif n.startswith("G11f_"): PLACE[n]=(I3,(TA2_X,TA2_Y-11.2,-26.0),"fix")
        elif n.startswith("J11e_"):
            up=n.endswith("-1"); PLACE[n]=(I3,(TA2_X,TA2_Y-8.8,(ZP_UP if up else ZP_DN)+PIN_H),"up" if up else "dn")
        elif n.startswith("J2c_"):
            PLACE[n]=(I3,(SH_X,SH_Y if n.endswith("-3") else -SH_Y,0),"fix")
        elif n.startswith("B10_"):
            i=int(n.rsplit("-",1)[1]); PLACE[n]=(R_B10,(SH_X,SH_Y if i in (1,3) else -SH_Y,ZP_UP if i in (1,2) else ZP_DN),"up" if i in (1,2) else "dn")
        elif n.startswith("J23c_"):
            PLACE[n]=(R_J23,(SH_X+27,SH_Y if n.endswith("-1") else -SH_Y,-26),"fix")
        elif n.startswith("K6_"):
            PLACE[n]=(R_K6,(SH_X+27,(SH_Y+30) if n.endswith("-1") else (-SH_Y+30),-10),"fix")
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,(R,t,grp) in PLACE.items():
            c=cc[n]; STRUCT=n.startswith(("J5k","J9f","J8e","B10"))
            if cfg=="상승": want=grp in ("fix","up")
            elif cfg=="하강": want=grp in ("fix","dn")
            elif STRUCT: want=(grp=="fix") or (grp=="up" and cfg.startswith("1.")) or (grp=="dn" and cfg.startswith("2."))
            else: want=(states[cfg]==2) and grp=="fix"
            set_supp(c,True); move_fixed(c,R,t)
            if n.startswith("B9g_") and cfg in ("상승","하강"):
                try: c.ReferencedConfiguration=cfg
                except Exception as ex: print("  refcfg exc",ex)
            set_supp(c,bool(want))
        a.ForceRebuild3(False); cc=comps()
        info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(PLACE)}
        print(f"[{cfg}] ww {ww(a)}")
        for n,v_ in info.items(): print("   ",n[:50],v_)
    a.ShowConfiguration2("상승"); a.EditRebuild3
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs)
    assert not any(r.startswith(("E50_","N1_","P1_","P2_","J19g_","J19h_","J5h_","J5i_","H16c_","G13d_","G3d_","B4d_","G13e_","J17c_","J9d_")) for r in refs), refs
    json.dump({"refs":refs,"stack":{"valve":[Z_VALVE_TOP,Z_VALVE_BOT],"hose_top":HOSE_TOP,"ZP":[ZP_UP,ZP_DN],"L_hose":L_HOSE,"D_up":D_UP,"R_bow":R_BOW,"bulge":BULGE}},open(os.path.join(VER,"line32_asm_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("asm stage done (not saved)")
stop.set()
