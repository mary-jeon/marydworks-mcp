# 2026-09-09 밤: 대공사 1단계 — 부품 생성/수정
#  사용자: ① J8b 6T 브래킷이 두껍고 판금이 아님 → 액추에이터를 로봇과 같은 제조사(TiMOTION TA2)로 바꿔 브래킷 최소화·판금(3.2T)
#          전동볼밸브도 로봇과 같은 코사플러스 KE002(+3PC 20A 볼밸브)로 ② 호스를 앞, 실린더를 뒤로. 호스는 하강 시 일직선.
#  라인 좌표: x 뒤(+), y 좌우, z 위(+), 원점 호퍼 출구, 고정판 상면 z 0.
#  새 배치: 호스/노즐 x 0(이동 소켓 y +10 편심 → 상승 시 굽힘 방향 +y로 확정), TA2·가이드봉 x +70.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
Zp=lambda n: os.path.join(Z,n)
# ---------- 배치 상수
AX=70.0; RY=240.0; OX=0.0; OY=10.0; ZP_UP=-390.0; ZP_DN=-510.0; STROKE=120.0
VALVE_L=80.0; VALVE_TOP=-34.5; NIP_FIX_TOP=VALVE_TOP-VALVE_L+0.5   # H16 상단 = 밸브 하단 안쪽 0.5 (나사 물림 표현)  -> -114
NIP_FIX_END=NIP_FIX_TOP-30.0                                        # -144
HOSE_R=47.0
TA2_RETRACT=STROKE+105.0   # 225 (후단 취부 1/2 + 전단 1/2/3, 출력신호 없음)
PIN_ROD_H=25.0             # 클레비스 핀 높이(이동판 상면 기준)
Z_REAR_PIN=ZP_UP+PIN_ROD_H+TA2_RETRACT   # -140
T_SM=3.2                   # 판금 두께(우리 규격: 데크·계단 3.2T)
# ---------- helpers
def new_part(): return app.NewDocument(tmpl,0,0,0)
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(b): return [round(v*1000,1) for v in pv(b,"GetBodyBox")]
def partbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bodies(d))
def sketch_on(d,plane,draw):
    assert sel_plane(d,plane),"plane "+plane
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    nm=last_sketch(d); d.Extension.SelectByID2(nm,"SKETCH",0,0,0,False,0,NOD,0); return nm
def extrude(d,depth,dir_neg=False,merge=True,mid=False,offset=0.0,name=None):
    # FeatureExtrusion3(Sd,Flip,Dir,T1,T2,D1,D2,Dchk1,Dchk2,Ddir1,Ddir2,Dang1,Dang2,OffRev1,OffRev2,TransSurf1,TransSurf2,Merge,UseFeatScope,UseAutoSel,T0,StartOffset,FlipStartOffset)
    T1=6 if mid else 0
    if offset: f=d.FeatureManager.FeatureExtrusion3(True,False,dir_neg,T1,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,1,mm(offset),False)
    else: f=d.FeatureManager.FeatureExtrusion3(True,False,dir_neg,T1,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False)
    d.EditRebuild3
    if f and name: f.Name=name
    return f
def cut_through(d,name=None,both=True):
    f=d.FeatureManager.FeatureCut4(True,False,False,1,1 if both else 0,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False)
    d.EditRebuild3
    if f and name: f.Name=name
    return f
def delete_feat(d,name):
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); d.EditRebuild3
def props(d,dct):
    cp=d.Extension.CustomPropertyManager(""); names=list(pv(cp,"GetNames") or [])
    for k,v in dct.items():
        if k in names: cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
def plane_at(d,base,dist,flip=False):
    """base 평면에서 dist 떨어진 기준면. InsertRefPlane(8|256, dist) = −쪽(메모리 실측). flip=True면 +쪽"""
    assert sel_plane(d,base)
    f=d.FeatureManager.InsertRefPlane(8|(0 if flip else 256),mm(abs(dist)),0,0,0,0); d.ClearSelection2(True); d.EditRebuild3
    return f.Name if f else None
def sketch_on_plane(d,plane_name,draw):
    d.ClearSelection2(True); assert d.Extension.SelectByID2(plane_name,"PLANE",0,0,0,False,0,NOD,0),"plane "+plane_name
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    nm=last_sketch(d); d.Extension.SelectByID2(nm,"SKETCH",0,0,0,False,0,NOD,0); return nm
def extrude_from_plane(d,base,z0,depth,merge=True,name=None,draw=None,axis_min=None):
    """z0 위치의 기준면(정면 기준 z=z0)에 스케치 → -z로 depth 돌출. 결과 박스 min이 axis_min 근처가 되도록 방향 자동 판정"""
    pn=plane_at(d,base,z0,flip=(z0>0)); print("  plane",pn,"for z",z0)
    sketch_on_plane(d,pn,draw); n0=len(bodies(d)); f=extrude(d,depth,dir_neg=True,merge=merge,name=name)
    bb=partbox(d)
    if axis_min is not None and bb[2]>axis_min+1.0:
        delete_feat(d,name); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); f=extrude(d,depth,dir_neg=False,merge=merge,name=name); bb=partbox(d)
    return f,bb
def material(d,name="STS 304",db="이텍"):
    try: d.SetMaterialPropertyName2("",db,name)
    except Exception as ex: print("  material fail",ex)
def saveas(d,path):
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saveas",os.path.basename(path),ok,e.value,w.value); return ok
def save(d):
    e=I4(); w=I4(); ok=d.Save3(1,e,w); print("  save",d.GetTitle,ok); return ok
def sheetmetal(d,t,r,face_pick):
    """face_pick(faces)->(fixed_face, bend_edges). 실측 규칙: 고정면 mark1 + 바깥쪽 모서리 mark2 + FindBends=True"""
    b=bodies(d)[0]; fixed,edges=face_pick(list(b.GetFaces()))
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; ok=fixed.Select4(False,sd)
    for e in edges:
        s2=d.SelectionManager.CreateSelectData; s2.Mark=2; ok=ok and e.Select4(True,s2)
    v0=vol(d); f=d.FeatureManager.InsertConvertToSheetMetal2(mm(t),False,True,mm(r),0.0,0,0.5,0,0.5,False); d.EditRebuild3
    v1=vol(d); names=[n for n,ty in feats(d)]; ok2=any(ty=="SolidToSheetMetal" for n,ty in feats(d))
    print("  sheetmetal sel",ok,"feat",f.Name if f else None,"SolidToSheetMetal",ok2,"vol",round(v0),"->",round(v1))
    return ok2 and abs(v1-v0)<0.15*v0
def plane_face(faces,normal,zsel=None):
    best=None
    for fc in faces:
        s=fc.GetSurface
        if not s.IsPlane: continue
        n=[round(v,2) for v in fc.Normal]
        if n!=normal: continue
        fb=[v*1000 for v in fc.GetBox]
        if zsel and not zsel(fb): continue
        best=fc
    return best
def edges_of(face,cond):
    out=[]
    for e in (pv(face,"GetEdges") or []):
        cp=pv(e,"GetCurveParams3"); sp=[v*1000 for v in pv(cp,"StartPoint")]; ep=[v*1000 for v in pv(cp,"EndPoint")]
        if cond(sp,ep): out.append(e)
    return out
made={}
# 이전 실행에서 남은 무제 파트 문서 닫기(내가 만든 것만: 경로 없음)
dd=pv(app,"GetFirstDocument")
while dd:
    nx=pv(dd,"GetNext")
    if not pv(dd,"GetPathName") and pv(dd,"GetType")==1: print("close untitled",pv(dd,"GetTitle")); app.CloseDoc(pv(dd,"GetTitle"))
    dd=nx
# ================= 1) TA2 액추에이터 B9d =================
P_TA2=Zp("B9d_TiMOTION_TA2-2H-120_24V.SLDPRT")
if not os.path.exists(P_TA2):
    d=new_part()
    # 후단 탭 18×18 R9, 핀축 y, 원점=핀 중심, 축 -z
    def tab(sm):
        sm.CreateLine(mm(-9),mm(0),0,mm(-9),mm(11),0); sm.CreateLine(mm(-9),mm(11),0,mm(9),mm(11),0); sm.CreateLine(mm(9),mm(11),0,mm(9),mm(0),0)
        sm.CreateArc(0,0,0,mm(9),0,0,mm(-9),0,0,-1)   # 윗면: sy=-z → 위쪽(z+)이 sy<0. R9 반원은 sy<0 쪽
    sketch_on(d,"윗면",tab); extrude(d,18.0,mid=True,name="후단_탭")
    bb=partbox(d); print("tab box",bb)
    if bb[5]<8.5:  # 반원이 아래로 갔으면 다시
        delete_feat(d,"후단_탭"); delete_feat(d,last_sketch(d))
        def tab2(sm):
            sm.CreateLine(mm(-9),mm(0),0,mm(-9),mm(11),0); sm.CreateLine(mm(-9),mm(11),0,mm(9),mm(11),0); sm.CreateLine(mm(9),mm(11),0,mm(9),mm(0),0)
            sm.CreateArc(0,0,0,mm(9),0,0,mm(-9),0,0,1)
        sketch_on(d,"윗면",tab2); extrude(d,18.0,mid=True,name="후단_탭"); print("tab box2",partbox(d))
    # 기어박스 40(y)×75(x: -20~55, 모터 +x쪽)×101(z -11~-112)
    sketch_on(d,"윗면",lambda sm: sm.CreateCornerRectangle(mm(-20),mm(11),0,mm(55),mm(112),0)); extrude(d,40.0,mid=True,name="기어박스_모터")
    # 튜브 Ø38 z -112 → -(RETRACT-11)= -214 (전단 캡 = 로드 홀 -11)
    tube_end=TA2_RETRACT-11.0
    f,bb=extrude_from_plane(d,"정면",-112.0,tube_end-112.0,name="튜브",draw=lambda sm: sm.CreateCircleByRadius(0,0,0,mm(19)),axis_min=-tube_end)
    print("tube box",bb)
    # 로드 Ø20: z -150 → -(RETRACT+9) (홀 -225, 끝 -234), 별도 바디
    rod_end=TA2_RETRACT+9.0
    f,bb=extrude_from_plane(d,"정면",-150.0,rod_end-150.0,merge=False,name="로드",draw=lambda sm: sm.CreateCircleByRadius(0,0,0,mm(10)),axis_min=-rod_end)
    bs=bodies(d); print("bodies",[(pv(b,'Name'),bbox(b)) for b in bs])
    if len(bs)!=2: raise SystemExit("rod body not separate")
    # 핀 홀 Ø8: 후단(원점)·로드(z -225), 축 y
    sketch_on(d,"윗면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(4))); cut_through(d,"후단_핀홀_D8")
    sketch_on(d,"윗면",lambda sm: sm.CreateCircleByRadius(0,mm(TA2_RETRACT),0,mm(4))); cut_through(d,"로드_핀홀_D8")
    print("TA2 bodies",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    # 구성 상승/하강 (하강 = 로드 -120)
    for cfg,desc in (("상승","로드 후퇴"),("하강",f"로드 {STROKE:.0f} 신장")):
        d.AddConfiguration3(cfg,desc,"",0)
    d.ShowConfiguration2("하강"); d.EditRebuild3
    rod=min(bodies(d),key=lambda b:bbox(b)[2]); d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; rod.Select2(False,sd)
    mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(-STROKE),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); mv.Name="로드_하강_이동"; d.EditRebuild3
    print("하강 bodies",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    mv.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
    for cfg in ("상승","기본"):
        d.ShowConfiguration2(cfg); d.EditRebuild3; print(f" [{cfg}]",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    d.ShowConfiguration2("상승")
    material(d,"STS 304")
    props(d,{"TITLE":"LINEAR ACTUATOR TiMOTION TA2 (500 N)","SPEC":f"TiMOTION TA2-2H-{STROKE:.0f}: 24 V DC, 하중코드 H(500 N 밀기/당기기, 셀프락 500 N, 6000 rpm 모터 17/14 mm/s), 스트로크 {STROKE:.0f}, 설치길이(후퇴, 홀-홀) {TA2_RETRACT:.0f}=스트로크+105, 후단 취부 2(홀 Ø8)·전단 2(홀 Ø8)·후단 방향 0°, 리미트 스위치 1(양단 전류 차단), 출력신호 0, IP66D, 케이블 1000. 사용온도 −25~+65 ℃(하중코드 C·D·E·H·K·L)","MATERIAL":"AL casting/SUS rod","QT'Y":"1","REMARK":"로봇 커버 실린더 TA2-2H-200과 같은 제조사·코드. 3D는 데이터시트(20160711-M) 근사: 탭 18×18 R9, 기어박스 40×75×101, 튜브 Ø38, 로드 Ø20. 구성 상승/하강(로드 이동). 승인도면으로 치수 확정 필요"})
    saveas(d,P_TA2); made["B9d"]=partbox(d)
# ================= 2) 판금 U 브래킷 J8c (후단, 고정판 밑면 용접) =================
P_J8=Zp("J8c_sm_U_bracket_t3.2_25x140x40.SLDPRT")
W_IN=18.5; W_OUT=W_IN+2*T_SM   # 24.9
H_TOP=Z_REAR_PIN*0-(-10.0-Z_REAR_PIN)  # 판 밑면(-10) - 핀(-140) = 130 (로컬 z: 핀 0, 상단 +130)
H_TOP=(-10.0)-Z_REAR_PIN
if not os.path.exists(P_J8):
    d=new_part()
    def uprof(sm):  # 우측면 (sx,sy)->(Y=sy, Z=-sx): 점(Y,Z) -> (sx=-Z, sy=Y)
        yo=W_OUT/2; yi=W_IN/2; zt=H_TOP; zb=-10.0; zw=H_TOP-T_SM
        P=[(yo,zb),(yo,zt),(-yo,zt),(-yo,zb),(-yi,zb),(-yi,zw),(yi,zw),(yi,zb),(yo,zb)]
        for (a,b) in zip(P,P[1:]): sm.CreateLine(mm(-a[1]),mm(a[0]),0,mm(-b[1]),mm(b[0]),0)
    sketch_on(d,"우측면",uprof); extrude(d,40.0,mid=True,name="U_형상")
    print("J8c box",partbox(d))
    sketch_on(d,"우측면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(4))); cut_through(d,"핀홀_D8")
    ok=sheetmetal(d,T_SM,T_SM,lambda faces:(plane_face(faces,[0.0,0.0,1.0],lambda fb:fb[5]>H_TOP-0.5), edges_of(plane_face(faces,[0.0,0.0,1.0],lambda fb:fb[5]>H_TOP-0.5),lambda sp,ep: abs(sp[0]-ep[0])>30 and abs(abs(sp[1])-W_OUT/2)<0.2)))
    material(d,"STS 304")
    props(d,{"TITLE":"TA2 REAR BRACKET (SHEET METAL U)","SPEC":f"STS304 t{T_SM} 판금 절곡 U, 안폭 {W_IN}(TA2 후단 탭 18 + 0.25×2), 바깥 {W_OUT:.1f}, 높이 {H_TOP+10:.0f}(핀 중심 {H_TOP:.0f} 아래 10), 폭 40, 굽힘 r{T_SM}, 핀홀 Ø8 양측 관통","MATERIAL":"STS304","QT'Y":"1","REMARK":"고정판 J1c 밑면 (70, 0) 용접(웹 40×25 둘레 필릿 3). 종전 J8b 6T(LA25 포크용)를 대체. 핀 MISUMI SHCCG8. 판금 변환 "+("성공" if ok else "실패(솔리드, 도면에서 판금 지정)")})
    saveas(d,P_J8); made["J8c"]=partbox(d)
# ================= 3) 판금 U 클레비스 J9c (로드, 이동판 상면 용접) =================
P_J9=Zp("J9c_sm_U_clevis_t3.2_27x33x40.SLDPRT")
C_IN=20.5; C_OUT=C_IN+2*T_SM; C_H=PIN_ROD_H+8.0   # 33
if not os.path.exists(P_J9):
    d=new_part()
    def cprof(sm):
        yo=C_OUT/2; yi=C_IN/2
        P=[(yo,C_H),(yo,0.0),(-yo,0.0),(-yo,C_H),(-yi,C_H),(-yi,T_SM),(yi,T_SM),(yi,C_H),(yo,C_H)]
        for (a,b) in zip(P,P[1:]): sm.CreateLine(mm(-a[1]),mm(a[0]),0,mm(-b[1]),mm(b[0]),0)
    sketch_on(d,"우측면",cprof); extrude(d,40.0,mid=True,name="U_형상")
    print("J9c box",partbox(d))
    sketch_on(d,"우측면",lambda sm: sm.CreateCircleByRadius(mm(-PIN_ROD_H),0,0,mm(4))); cut_through(d,"핀홀_D8")
    ok=sheetmetal(d,T_SM,T_SM,lambda faces:(plane_face(faces,[0.0,0.0,-1.0],lambda fb:fb[2]<0.5), edges_of(plane_face(faces,[0.0,0.0,-1.0],lambda fb:fb[2]<0.5),lambda sp,ep: abs(sp[0]-ep[0])>30 and abs(abs(sp[1])-C_OUT/2)<0.2)))
    material(d,"STS 304")
    props(d,{"TITLE":"TA2 ROD CLEVIS (SHEET METAL U)","SPEC":f"STS304 t{T_SM} 판금 절곡 U, 안폭 {C_IN}(TA2 로드 Ø20 + 0.25×2), 바깥 {C_OUT:.1f}, 높이 {C_H:.0f}(핀 @{PIN_ROD_H:.0f}), 폭 40, 굽힘 r{T_SM}, 핀홀 Ø8 양측 관통","MATERIAL":"STS304","QT'Y":"1","REMARK":"이동판 J5e 상면 (70, 0) 용접. 종전 J9b 6T를 대체. 핀 MISUMI SHCCG8. 판금 변환 "+("성공" if ok else "실패(솔리드, 도면에서 판금 지정)")})
    saveas(d,P_J9); made["J9c"]=partbox(d)
# ================= 4) 핀 MISUMI SHCCG8 (D8 헤드·홈 치수는 미확인 → 근사) =================
def make_pin(path,L,title,remark):
    if os.path.exists(path): return
    d=new_part()
    sketch_on(d,"윗면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(4))); extrude(d,L,name="핀_D8")           # 윗면 돌출 +Y
    sketch_on(d,"윗면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(6))); extrude(d,2.0,dir_neg=True,name="헤드_D12")
    bb=partbox(d); print("pin box",bb)
    # 홈: 끝에서 3, 폭 1.15, 홈경 Ø7.6 (D10 값 비례 근사)
    sketch_on(d,"정면",lambda sm: (sm.CreateCircleByRadius(0,mm(L-3.0-0.575),0,mm(4.2)),sm.CreateCircleByRadius(0,mm(L-3.0-0.575),0,mm(3.8))))
    # (정면 원 두 개 컷은 홈이 아니라 관통이 되므로 홈은 속성에만 명기) → 스케치 삭제
    d.SketchManager.InsertSketch(True) if d.SketchManager.ActiveSketch else None
    delete_feat(d,last_sketch(d))
    material(d,"STS 304")
    props(d,{"TITLE":title,"SPEC":f"MISUMI 힌지핀 플랜지붙이 고정링 타입 SHCCG8-{L:g}: SUS304 Ø8, L {L:g}(0.1 단위 지정), 헤드 H12×T2, 고정링 홈 M0.9(+0.1/0)·홈경 7(+0.09/0)·끝에서 N3, E형 고정링 No.7 1개 부속(kr.misumi-ec.com 110300095750 규격표 D8 행)","MATERIAL":"SUS304","QT'Y":"1","REMARK":remark})
    saveas(d,path)
make_pin(Zp("G11d_MISUMI_SHCCG8-25.3_pin.SLDPRT"),25.3,"REAR PIN (MISUMI SHCCG8-25.3)","TA2 후단 탭 ↔ 브래킷 J8c(바깥 24.9 + 0.35). 헤드 −y 바깥, 고정링 +y")
make_pin(Zp("J11c_MISUMI_SHCCG8-27.3_pin.SLDPRT"),27.3,"ROD PIN (MISUMI SHCCG8-27.3)","TA2 로드 ↔ 클레비스 J9c(바깥 26.9 + 0.35). 인스턴스 2(상승/하강)")
# ================= 5) 3PC 볼밸브 G3b + KE002 액추에이터 B4b =================
P_G3=Zp("G3b_valve_3PC_3-4in_ISO_F03F04_SUS.SLDPRT")
PAD_H=48.0   # 바자밸브 3PC 자동장착용 3/4": L80, H1 48 (축→ISO 패드), F03/F04
if not os.path.exists(P_G3):
    d=new_part()
    sketch_on(d,"정면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(20))); extrude(d,VALVE_L,dir_neg=True,name="몸체_D40")
    bb=partbox(d); print("valve body box",bb)
    if bb[2]>-VALVE_L+1: delete_feat(d,"몸체_D40"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,VALVE_L,dir_neg=False,name="몸체_D40"); print("valve box2",partbox(d))
    # ISO 패드 보스 Ø45 → -y 방향, 중심 z -40
    def pad(sm): sm.CreateCircleByRadius(0,mm(VALVE_L/2),0,mm(22.5))    # 윗면: (sx,sy)->(X=sx, Z=-sy) → z=-40
    sketch_on(d,"윗면",pad); f=extrude(d,PAD_H,dir_neg=True,name="ISO패드_보스")
    bb=partbox(d); print("pad box",bb)
    if bb[1]>-PAD_H+1: delete_feat(d,"ISO패드_보스"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,PAD_H,dir_neg=False,name="ISO패드_보스"); print("pad box2",partbox(d))
    material(d,"STS 316")
    props(d,{"TITLE":"BALL VALVE 3PC 3/4in ISO5211 (자동장착용)","SPEC":"스텐 3PC 볼밸브 3/4\"(20A) 풀보어, ISO5211 F03/F04 패드, PT(Rc) 암나사 양단, L 80·축→패드 48·스템 9각(바자밸브 3PC 자동장착용 치수표 기준 — 태성자동밸브 20S3 형번으로 발주 시 치수 재확인)","MATERIAL":"SUS316(CF8M)","QT'Y":"1","REMARK":"코사플러스 KE002와 세트(로봇 KE002-10S3 계열의 20A판 = KE002-20S3). 종전 Tameson BL2SA3-034를 대체. 3D 근사(몸체 Ø40 원통)"})
    saveas(d,P_G3); made["G3b"]=partbox(d)
P_B4=Zp("B4b_actuator_KOSAPLUS_KE002_24VDC.SLDPRT")
if not os.path.exists(P_B4):
    d=new_part()
    # 취부면 y 0, 본체 -y로 118.9(DC). 스템축 = 원점. 평면치수: z +24.7~-80.6, x -32.7~+59.4
    def foot(sm): sm.CreateCornerRectangle(mm(-32.7),mm(-24.7),0,mm(59.4),mm(80.6),0)   # 윗면: sy=-z → z +24.7 ~ -80.6
    sketch_on(d,"윗면",foot); f=extrude(d,118.9,dir_neg=True,name="본체")
    bb=partbox(d); print("KE002 box",bb)
    if bb[1]>-118.0: delete_feat(d,"본체"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,118.9,dir_neg=False,name="본체"); print("KE002 box2",partbox(d))
    material(d,"AL")
    props(d,{"TITLE":"ELECTRIC ACTUATOR KOSAPLUS KE002 (24 VDC)","SPEC":"코사플러스 KE002-6G: 최대 토크 20 N·m, 24 V DC 1.5 A, 작동 14.5~17.5 s/90°, IP67, −20~+60 ℃, ISO5211 F03/F05·11각 스템 DP15, 0.9 kg, 리미트 스위치 2, 수동 5 mm 스패너, 케이블 PG11 1 m. 외형 92.1×105.3×118.9(DC)","MATERIAL":"AL 다이캐스트 분체도장","QT'Y":"1","REMARK":"로봇 KE002-10S3(C2)와 같은 제조사·모델(태성자동밸브 취급). 종전 Sun Yeh OM-1을 대체. 3D 근사(직육체). 히터 없음 — 옥외 −30 ℃ 요구 대비 하한 −20 ℃(Tameson과 동일, 사용자 09-08 수용)"})
    saveas(d,P_B4); made["B4b"]=partbox(d)
# ================= 6) 이동판 J5e =================
P_J5=Zp("J5e_moving_plate_180x540_t8.SLDPRT")
if not os.path.exists(P_J5):
    d=new_part()
    def plate(sm):
        sm.CreateCornerRectangle(mm(-45),mm(-270),0,mm(135),mm(270),0)
        sm.CreateCircleByRadius(mm(OX),mm(OY),0,mm(17))
        for y in (RY,-RY):
            sm.CreateCircleByRadius(mm(AX),mm(y),0,mm(14.25))
            for (dx,dy) in ((19,0),(-19,0),(0,19),(0,-19)): sm.CreateCircleByRadius(mm(AX+dx),mm(y+dy),0,mm(1.65))
    sketch_on(d,"정면",plate); extrude(d,8.0,dir_neg=True,name="판_t8")
    bb=partbox(d); print("J5e box",bb)
    if bb[5]>0.5: delete_feat(d,"판_t8"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,8.0,dir_neg=False,name="판_t8"); print("J5e box2",partbox(d))
    material(d,"STS 304")
    props(d,{"TITLE":"MOVING PLATE 180x540 t8","SPEC":f"STS304 PL 180(X −45~135)×540(Y ±270)×t8. 소켓 Ø34 @({OX:g},{OY:g}) 상면 플러시 삽입, 부시 MISUMI LHFRW16 Ø28.5 + M4 탭 십자 PCD38 @({AX:g},±{RY:g}), 클레비스 J9c 상면 (70,0) 용접","MATERIAL":"STS304","QT'Y":"1","REMARK":f"종전 J5d 220×540(소켓 x 100)을 대체: 호스를 앞(x 0)·실린더를 뒤(x 70)로. 소켓 y +{OY:g} 편심은 상승 시 호스 굽힘 방향(+y)을 정하기 위한 것(하강 시 기울기 {math.degrees(math.atan(OY/336)):.1f}°)"})
    saveas(d,P_J5); made["J5e"]=partbox(d)
# ================= 7) 호스 (하강 일직선 / 상승 활 굽힘) =================
def segs_from(list_):
    """list_: [('arc',R,ang)|('line',len)] 시작 (0,0) 방향 -y. hose_segments와 같은 규약"""
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    for it in list_:
        if it[0]=="line":
            dd=it[1]
            if dd<=1e-9: continue
            x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1
        else:
            rad,ang=it[1],it[2]
            if abs(ang)<1e-9: continue
            side=1 if ang>0 else -1
            cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
            h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
            segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    return segs,(x,y)
def seglen(segs): return sum((math.hypot(s[2][0]-s[1][0],s[2][1]-s[1][1]) if s[0]=="line" else abs(s[4])*math.hypot(s[2][0]-s[1][0],s[2][1]-s[1][1])) for s in segs)
def climb(sc,p0,steps,iters=3000):
    p=list(p0); v=sc(p); st=list(steps)
    while max(st)>1e-7 and iters>0:
        imp=False; iters-=1
        for i in range(len(p)):
            for dd in (1,-1):
                q=list(p); q[i]+=dd*st[i]; vq=sc(q)
                if vq<v: v,p=vq,q; imp=True
        if not imp: st=[u/2 for u in st]
    return v,p
D_DN=NIP_FIX_END-(ZP_DN+30.0); D_UP=NIP_FIX_END-(ZP_UP+30.0)   # 336, 216
# 하강: arc(47,a) + line 2t + arc(47,-a)
def dn_list(p): a,t=p; return [("arc",HOSE_R,a),("line",2*t),("arc",HOSE_R,-a)]
def sc_dn(p):
    if p[0]<0 or p[1]<0: return 1e6
    s,(ex,ey)=segs_from(dn_list(p)); return math.hypot(ex-OY,ey+D_DN)
v,(a_dn,t_dn)=climb(sc_dn,[0.03,160.0],[0.01,10.0]); segs_dn,end_dn=segs_from(dn_list([a_dn,t_dn])); L_HOSE=seglen(segs_dn)
print(f"dn path: resid {v:.4f} a {math.degrees(a_dn):.2f}° t {t_dn:.2f} end {end_dn} L {L_HOSE:.2f}")
# 상승: arc(R,t1)+arc(R,-t1)+arc(R,-t2)+arc(R,t2), 길이 L_HOSE, 끝 (OY, -D_UP)
def up_list(p): R,t1,t2=p; return [("arc",R,t1),("arc",R,-t1),("arc",R,-t2),("arc",R,t2)]
def sc_up(p):
    R,t1,t2=p
    if R<HOSE_R or t1<0 or t2<0: return 1e6
    s,(ex,ey)=segs_from(up_list(p)); return math.hypot(ex-OY,ey+D_UP)+abs(seglen(s)-L_HOSE)
v2,(R_up,t1,t2)=climb(sc_up,[55.0,1.5,1.5],[2.0,0.1,0.1]); segs_up,end_up=segs_from(up_list([R_up,t1,t2]))
bul=max(abs(p[0]) for s in segs_up for p in (s[1],s[2],s[3]) if s[0]=="arc")
print(f"up bow: resid {v2:.4f} R {R_up:.1f} θ1 {math.degrees(t1):.1f}° θ2 {math.degrees(t2):.1f}° end {end_up} L {seglen(segs_up):.2f} bulge(x) ≈ {bul:.1f}")
json.dump({"NIP_FIX_END":NIP_FIX_END,"OY":OY,"D_DN":D_DN,"D_UP":D_UP,"L":L_HOSE,"dn":{"a_deg":math.degrees(a_dn),"t":t_dn},"up":{"R":R_up,"t1_deg":math.degrees(t1),"t2_deg":math.degrees(t2),"bulge":bul},"segs_dn":segs_dn,"segs_up":segs_up},open(os.path.join(VER,"ta2_hose_paths_0909.json"),"w"),indent=1)
if v>0.5 or v2>0.5: raise SystemExit("hose solver residual too large")
def build_hose(path,segs,title,spec):
    if os.path.exists(path): return
    for direction in (1,-1):
        dh=new_part()
        try:
            sel_plane(dh,"정면"); dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
            for sg in segs:
                if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0)
                else:
                    cc_,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]
                    sm.CreateArc(mm(cc_[0]),mm(cc_[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
            sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
            Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
            print(f"  direction={direction}: sketch length {Ls:.2f} (target {seglen(segs):.2f})")
            if abs(Ls-seglen(segs))>1.0: app.CloseDoc(dh.GetTitle); continue
            sel_plane(dh,"윗면"); dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(14.1)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(9.5)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            dh.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or dh.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
            dh.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or dh.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
            f=None
            for attempt in ("swept3","swept4"):
                try:
                    if attempt=="swept3": f=dh.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                    else: f=dh.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                    if f: break
                except Exception as ex: print("  ",attempt,"exception",ex)
            if not f: raise RuntimeError("sweep failed")
            dh.EditRebuild3; print("  hose box",partbox(dh))
            props(dh,{"TITLE":title,"SPEC":spec,"MATERIAL":"실리콘(3겹 폴리에스터·와이어 보강)","QT'Y":"1","REMARK":"양단 호스니플 H16에 삽입 20 + T볼트 클램프. 상승/하강 형상은 같은 호스의 두 상태(인스턴스 억제)"})
            dh.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber"); dh.EditRebuild3
            saveas(dh,path); return
        except Exception as ex:
            print("FAIL hose",ex); app.CloseDoc(dh.GetTitle); raise
    raise SystemExit("hose sketch length mismatch")
spec_common=f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 최소 굽힘반경 47, 자유길이 {L_HOSE:.1f} + 니플 삽입 2×20 = 절단 약 {round(L_HOSE)+40}"
build_hose(Zp(f"J19e_hose_3-4in_dn_straight_L{round(L_HOSE)}.SLDPRT"),segs_dn,"HOSE 3/4in (하강: 일직선)",spec_common+f". 하강(스트로크 {STROKE:.0f}, 낙차 {D_DN:.0f}, 편심 {OY:g}) 경로: r47 {math.degrees(a_dn):.1f}° + 직선 {2*t_dn:.1f} + r47 −{math.degrees(a_dn):.1f}° (사실상 일직선, 기울기 {math.degrees(a_dn):.1f}°)")
build_hose(Zp(f"J19e_hose_3-4in_up_bow_R{round(R_up)}.SLDPRT"),segs_up,"HOSE 3/4in (상승: 활 굽힘)",spec_common+f". 상승(낙차 {D_UP:.0f}) 경로: R{R_up:.1f} {math.degrees(t1):.1f}°/−{math.degrees(t1):.1f}°/−{math.degrees(t2):.1f}°/{math.degrees(t2):.1f}° 4원호 활, +y로 {bul:.0f} 불룩 (최소 굽힘반경 47 대비 R{R_up:.1f})")
# ================= 8) 고정판 J1c 제자리 편집: 외곽 -110~75 → -75~110, Ø14 (-70,±240) → (70,±240) =================
P1=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); d=app.GetOpenDocumentByName(P1) or open_doc(app,P1,1); app.ActivateDoc3(P1,False,0,I4()); d=app.ActiveDoc
bb=partbox(d); print("J1c before",bb)
if bb[0]<-100:
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2("스케치3","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch()
    sk=d.SketchManager.ActiveSketch; segs=list(pv(sk,"GetSketchSegments") or [])
    d.ClearSelection2(True); n=0
    for s in segs:
        ty=s.GetType() if callable(s.GetType) else s.GetType
        if ty==0: s.Select4(True,NOD); n+=1
        elif ty==1:
            cp=pv(s,"GetCenterPoint2")
            try: cx=cp[0]
            except TypeError: cx=pv(cp,"X")
            if abs(cx*1000+70)<0.5: s.Select4(True,NOD); n+=1
    print("  selected segs",n); d.Extension.DeleteSelection2(0); sm=d.SketchManager; sm.AddToDB=True
    sm.CreateCenterRectangle(mm(17.5),0,0,mm(17.5+92.5),mm(290),0)
    for y in (RY,-RY): sm.CreateCircleByRadius(mm(AX),mm(y),0,mm(7.0))
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.EditRebuild3
    print("J1c after",partbox(d))
    cp=d.Extension.CustomPropertyManager("")
    cp.Set2("SPEC","185(X −75~110)×580(Y ±290) t10 STS304. 소켓 Ø28(0,0: 용접소켓 G13 판 밑 용접), 가이드봉 M16 탭 관통 2개소 @(70,±240)(드릴 Ø14 = 모델 구멍). 상면은 호퍼 립 밑면에 둘레 필릿 용접(§1-21 사양)")
    cp.Set2("REMARK","호스를 앞(x 0)·실린더(TA2)를 뒤(x 70)로 바꾸며 외곽·봉 구멍을 x 대칭으로 이동. TA2 브래킷 J8c 밑면 (70,0) 용접")
    save(d)
print("MADE",made); stop.set(); print("stage1 done")
