# 2026-09-09 밤: 대공사 3단계 — 사용자 「브래킷이 안 생기게 실린더를 선정하라」
#  TA2 끝단 옵션을 후단 5(클레비스 U 홈 6·깊이 16·홀 8)·전단 5(클레비스 U 홈 6·깊이 10.5·홀 8)로 지정 → 우리 쪽은 굽힘 없는 평판 러그 PL6.
#  설치길이(후퇴) = 스트로크 + 119 = 239. 판금 U(J8c·J9c) 폐기 → 러그 J8d(고정판 밑면)·J9d(이동판 상면).
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
AX=70.0; ZP_UP=-390.0; ZP_DN=-510.0; STROKE=120.0; PIN_ROD_H=25.0
TA2_RETRACT=STROKE+119.0          # 239
Z_REAR_PIN=ZP_UP+PIN_ROD_H+TA2_RETRACT   # -126
LUG_T=6.0; LUG_W=40.0
REAR_U_OUT=18.0; FRONT_U_OUT=20.0  # TA2 클레비스 U 바깥폭(도면 근사: 후단 탭 18, 로드 Ø20) — 승인도면 확인
# ---------- helpers (1단계와 동일 규약)
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
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(b): return [round(v*1000,1) for v in pv(b,"GetBodyBox")]
def partbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def sketch_sel(d,plane_name,draw):
    d.ClearSelection2(True); assert d.Extension.SelectByID2(plane_name,"PLANE",0,0,0,False,0,NOD,0) or sel_plane(d,plane_name),"plane "+plane_name
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    nm=last_sketch(d); d.Extension.SelectByID2(nm,"SKETCH",0,0,0,False,0,NOD,0); return nm
def extrude(d,depth,dir_neg=False,merge=True,mid=False,name=None):
    T1=6 if mid else 0
    f=d.FeatureManager.FeatureExtrusion3(True,False,dir_neg,T1,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False); d.EditRebuild3
    if f and name: f.Name=name
    return f
def delete_feat(d,name):
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); d.EditRebuild3
def plane_at(d,base,dist,flip=False):
    assert sel_plane(d,base)
    f=d.FeatureManager.InsertRefPlane(8|(0 if flip else 256),mm(abs(dist)),0,0,0,0); d.ClearSelection2(True); d.EditRebuild3; return f.Name
def cut_blind(d,depth,dir_neg,name=None):
    f=d.FeatureManager.FeatureCut4(True,False,dir_neg,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    if f and name: f.Name=name
    return f
def cyl_r(d,r):
    out=[]
    for b in bodies(d):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05: out.append([round(v*1000,1) for v in fc.GetBox])
    return sorted(out)
def hole_y_through(d,sk_draw_on_top,zc,name,ylen=40.0):
    """y축 관통 Ø8 홀: 윗면에서 -y로 ylen/2 떨어진 기준면에 원을 그리고 +y로 ylen 블라인드 컷(방향 자동 판정)"""
    pn=plane_at(d,"윗면",ylen/2,flip=False)   # 윗면(y=0)에서 -쪽 = y -20
    sketch_sel(d,pn,sk_draw_on_top)
    before=cyl_r(d,4.0); f=cut_blind(d,ylen,False,name); after=cyl_r(d,4.0)
    ok=any(abs(b[2]-(zc-4))<0.6 and b[4]-b[1]>8 for b in after)
    if not ok:
        delete_feat(d,name); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); f=cut_blind(d,ylen,True,name); after=cyl_r(d,4.0)
    print("  hole",name,[b for b in after if abs(b[2]-(zc-4))<0.6])
    return f
def props(d,dct):
    cp=d.Extension.CustomPropertyManager(""); names=list(pv(cp,"GetNames") or [])
    for k,v in dct.items():
        if k in names: cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
def material(d,name="STS 304",db="이텍"):
    try: d.SetMaterialPropertyName2("",db,name)
    except Exception as ex: print("  material fail",ex)
def saveas(d,path):
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saveas",os.path.basename(path),ok,e.value,w.value); return ok
def save(d):
    e=I4(); w=I4(); ok=d.Save3(1,e,w); print("  save",d.GetTitle,ok); return ok
dd=pv(app,"GetFirstDocument")
while dd:
    nx=pv(dd,"GetNext")
    if not pv(dd,"GetPathName") and pv(dd,"GetType")==1: print("close untitled",pv(dd,"GetTitle")); app.CloseDoc(pv(dd,"GetTitle"))
    dd=nx
# ================= 1) TA2 B9e (양단 클레비스 U) =================
P_TA2=Zp("B9e_TiMOTION_TA2-2H-120_24V_clevisU.SLDPRT")
if not os.path.exists(P_TA2):
    d=new_part()
    # 후단 클레비스 U: 바깥 18(y ±9)·x ±9·z +9(R9)~-11, 홈 6(y ±3) 깊이 16(z +9 → -7), 홀 Ø8 @원점
    def tab(sm):
        sm.CreateLine(mm(-9),mm(0),0,mm(-9),mm(11),0); sm.CreateLine(mm(-9),mm(11),0,mm(9),mm(11),0); sm.CreateLine(mm(9),mm(11),0,mm(9),mm(0),0)
        sm.CreateArc(0,0,0,mm(9),0,0,mm(-9),0,0,-1)
    sketch_sel(d,"윗면",tab); extrude(d,REAR_U_OUT,mid=True,name="후단_U")
    bb=partbox(d)
    if bb[5]<8.5:
        delete_feat(d,"후단_U"); delete_feat(d,last_sketch(d))
        def tab2(sm):
            sm.CreateLine(mm(-9),mm(0),0,mm(-9),mm(11),0); sm.CreateLine(mm(-9),mm(11),0,mm(9),mm(11),0); sm.CreateLine(mm(9),mm(11),0,mm(9),mm(0),0)
            sm.CreateArc(0,0,0,mm(9),0,0,mm(-9),0,0,1)
        sketch_sel(d,"윗면",tab2); extrude(d,REAR_U_OUT,mid=True,name="후단_U")
    print("rear U box",partbox(d))
    # 홈 6: 우측면 (sx,sy)->(Y=sy,Z=-sx): 사각 Y ±3, Z -7~+12 → sx -12~7, sy -3~3 ; x 방향 관통(양방향) → 두 번 블라인드
    sketch_sel(d,"우측면",lambda sm: sm.CreateCornerRectangle(mm(-12),mm(-3),0,mm(7),mm(3),0)); cut_blind(d,12.0,False,"후단_홈6_a")
    sketch_sel(d,"우측면",lambda sm: sm.CreateCornerRectangle(mm(-12),mm(-3),0,mm(7),mm(3),0)); cut_blind(d,12.0,True,"후단_홈6_b")
    print("rear U slot bodies",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    sketch_sel(d,"윗면",lambda sm: sm.CreateCornerRectangle(mm(-20),mm(11),0,mm(55),mm(112),0)); extrude(d,40.0,mid=True,name="기어박스_모터")
    tube_end=TA2_RETRACT-11.0   # 228
    pn=plane_at(d,"정면",112.0); sketch_sel(d,pn,lambda sm: sm.CreateCircleByRadius(0,0,0,mm(19))); extrude(d,tube_end-112.0,dir_neg=True,name="튜브")
    bb=partbox(d)
    if bb[2]>-tube_end+1: delete_feat(d,"튜브"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,tube_end-112.0,dir_neg=False,name="튜브")
    print("tube box",partbox(d))
    # 튜브 보어 Ø21 (z -112 → -228)
    d.ClearSelection2(True); d.Extension.SelectByID2(pn,"PLANE",0,0,0,False,0,NOD,0); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(10.5)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); cut_blind(d,tube_end-112.0,True,"튜브_보어_D21")
    # 로드 Ø20: z -160 → 전단 U 바닥 -234 (솔리드) ; 전단 U 팔: z -234 → -244.5, 홀 -239, 별도 바디
    rod_top=-160.0; slot_bot=-(TA2_RETRACT-5.0)   # -234 (홀 -239 위 5)
    tip=slot_bot-10.5   # -244.5
    pn2=plane_at(d,"정면",abs(rod_top)); sketch_sel(d,pn2,lambda sm: sm.CreateCircleByRadius(0,0,0,mm(10))); extrude(d,tip-rod_top if False else abs(tip-rod_top),dir_neg=True,merge=False,name="로드")
    bs=bodies(d)
    if len(bs)!=2 or min(bbox(b)[2] for b in bs)>tip+1:
        delete_feat(d,"로드"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,abs(tip-rod_top),dir_neg=False,merge=False,name="로드")
    print("rod bodies",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    # 전단 홈 6 (y ±3, z tip → slot_bot) x 관통: 우측면 사각 Z tip~slot_bot → sx = -Z
    sketch_sel(d,"우측면",lambda sm: sm.CreateCornerRectangle(mm(-slot_bot),mm(-3),0,mm(-tip+1),mm(3),0)); cut_blind(d,12.0,False,"전단_홈6_a")
    sketch_sel(d,"우측면",lambda sm: sm.CreateCornerRectangle(mm(-slot_bot),mm(-3),0,mm(-tip+1),mm(3),0)); cut_blind(d,12.0,True,"전단_홈6_b")
    print("front slot bodies",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    # 핀 홀 Ø8 y 관통: 후단 @0, 전단 @-239
    hole_y_through(d,lambda sm: sm.CreateCircleByRadius(0,0,0,mm(4)),0.0,"후단_핀홀_D8")
    hole_y_through(d,lambda sm: sm.CreateCircleByRadius(0,mm(TA2_RETRACT),0,mm(4)),-TA2_RETRACT,"전단_핀홀_D8")
    print("B9e bodies",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    for cfg,desc in (("상승","로드 후퇴"),("하강",f"로드 {STROKE:.0f} 신장")): d.AddConfiguration3(cfg,desc,"",0)
    d.ShowConfiguration2("하강"); d.EditRebuild3
    rod=min(bodies(d),key=lambda b:bbox(b)[2]); d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; rod.Select2(False,sd)
    mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(-STROKE),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); mv.Name="로드_하강_이동"; d.EditRebuild3
    mv.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
    for cfg in ("상승","하강"):
        d.ShowConfiguration2(cfg); d.EditRebuild3; print(f" [{cfg}]",[(pv(b,'Name'),bbox(b)) for b in bodies(d)])
    d.ShowConfiguration2("상승"); material(d,"STS 304")
    props(d,{"TITLE":"LINEAR ACTUATOR TiMOTION TA2 (500 N, 양단 클레비스 U)","SPEC":f"TiMOTION TA2-2H-{STROKE:.0f}: 24 V DC, 하중코드 H(500 N 밀기/당기기, 셀프락 500 N, 17/14 mm/s), 스트로크 {STROKE:.0f}, 설치길이(후퇴, 홀-홀) {TA2_RETRACT:.0f}=스트로크+119. 후단 취부 5(AL CNC 클레비스 U, 홈 6·깊이 16·홀 Ø8)·전단 취부 5(AL 주조 클레비스 U, 홈 6·깊이 10.5·홀 Ø8), 후단 방향 0°, 리미트 스위치 1(양단 전류 차단), 출력신호 0, IP66D, 케이블 1000. 사용온도 −25~+65 ℃","MATERIAL":"AL casting/SUS rod","QT'Y":"1","REMARK":"양단이 실린더 자체 클레비스 U라 스테이션 쪽은 굽힘 없는 평판 러그 PL6(J8d·J9d)만 용접 — 별도 브래킷 없음. 로봇 커버 실린더 TA2-2H-200과 같은 제조사·코드. 3D는 데이터시트 근사(클레비스 U 바깥폭 18/20 가정) — 승인도면으로 확정"})
    saveas(d,P_TA2)
# ================= 2) 러그 J8d(고정판 밑면) · J9d(이동판 상면) =================
def make_lug(path,z_lo,z_hi,hole_z,title,spec,remark):
    if os.path.exists(path): return
    d=new_part()
    # 정면(XY) 스케치가 아니라 판 두께가 y: 우측면 (sx,sy)->(Y=sy,Z=-sx). 러그 외곽 Z z_lo~z_hi, Y ±3 → 우측면 사각 sx -z_hi~-z_lo, sy ±3 ... 두께 방향은 x 돌출이 됨 → 대신 정면(XY)에 X ±20 × Y ±3 사각을 그리고 Z로 돌출
    pn=plane_at(d,"정면",abs(z_lo),flip=(z_lo>0)); sketch_sel(d,pn,lambda sm: sm.CreateCornerRectangle(mm(-LUG_W/2),mm(-LUG_T/2),0,mm(LUG_W/2),mm(LUG_T/2),0))
    extrude(d,z_hi-z_lo,dir_neg=False,name="러그_PL6")
    bb=partbox(d)
    if abs(bb[5]-z_hi)>0.5: delete_feat(d,"러그_PL6"); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0); extrude(d,z_hi-z_lo,dir_neg=True,name="러그_PL6"); bb=partbox(d)
    print("  lug box",bb)
    hole_y_through(d,lambda sm: sm.CreateCircleByRadius(0,mm(-hole_z),0,mm(4)),hole_z,"핀홀_D8",ylen=20.0)
    material(d,"STS 304"); props(d,{"TITLE":title,"SPEC":spec,"MATERIAL":"STS304","QT'Y":"1","REMARK":remark})
    saveas(d,path)
make_lug(Zp("J8d_lug_PL6_40x126.SLDPRT"),-10.0,-Z_REAR_PIN-10.0,0.0,"TA2 REAR LUG (FLAT PL6)",
         f"STS304 PL6 × 40 × {(-Z_REAR_PIN-10.0)+10.0:.0f}, 핀홀 Ø8(하단에서 10). TA2 후단 클레비스 U(홈 6·깊이 16)에 삽입",
         "고정판 J1c 밑면 (70,0)에 상단 모서리 양면 필릿 용접. 굽힘 없음(레이저 절단 평판). 두께는 U 홈 6에 맞춰 5.8~6.0 가공")
make_lug(Zp("J9d_lug_PL6_40x31.SLDPRT"),0.0,PIN_ROD_H+6.0,PIN_ROD_H,"TA2 ROD LUG (FLAT PL6)",
         f"STS304 PL6 × 40 × {PIN_ROD_H+6.0:.0f}, 핀홀 Ø8(상단에서 6). TA2 전단 클레비스 U(홈 6·깊이 10.5)에 삽입",
         "이동판 J5e 상면 (70,0)에 하단 모서리 양면 필릿 용접. 굽힘 없음. 홀 위 살 2 mm는 전단 U 홀-바닥 거리(승인도면)로 확정")
# ================= 3) 핀 (E링 홈 위치까지 물림 = U 바깥폭 + 0.35) =================
def make_pin(path,L,title,remark):
    if os.path.exists(path): return
    d=new_part()
    sketch_sel(d,"윗면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(4))); extrude(d,L,name="핀_D8")
    sketch_sel(d,"윗면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(6))); extrude(d,2.0,dir_neg=True,name="헤드_D12")
    material(d,"STS 304")
    props(d,{"TITLE":title,"SPEC":f"MISUMI 힌지핀 플랜지붙이 고정링 타입 SHCCG8-{L:g}: SUS304 Ø8 g6, L {L:g}(0.1 단위 지정), 헤드 H12×T2, 고정링 홈 M0.9·홈경 7·끝에서 N3, E형 고정링 No.7 부속(kr.misumi-ec.com 110300095750 D8 행)","MATERIAL":"SUS304","QT'Y":"1","REMARK":remark})
    saveas(d,path)
make_pin(Zp("G11e_MISUMI_SHCCG8-18.4_pin.SLDPRT"),18.4,"REAR PIN (MISUMI SHCCG8-18.4)","TA2 후단 클레비스 U(바깥 18 가정) + 0.35. 헤드 −y 바깥, E링 +y. U 바깥폭은 승인도면으로 확정 후 L 재지정")
make_pin(Zp("J11d_MISUMI_SHCCG8-20.4_pin.SLDPRT"),20.4,"ROD PIN (MISUMI SHCCG8-20.4)","TA2 전단 클레비스 U(바깥 20 가정) + 0.35. 인스턴스 2(상승/하강)")
# ================= 4) 어셈블리 교체 =================
ASM=Zp("염수주입라인.SLDASM"); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); title=a.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel_comp(n):
    a.ClearSelection2(True); return a.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def set_supp(n,on):
    sel_comp(n)
    if on: a.EditUnsuppress2
    else: a.EditSuppress2
    a.ClearSelection2(True)
def add_comp(fn):
    global a
    p=Zp(fn)
    if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0)
    if not c: raise SystemExit("AddComponent failed "+fn)
    a.EditRebuild3; print("added",c.Name2); return c
I3=[[1,0,0],[0,1,0],[0,0,1]]
NEW={"B9e_TiMOTION_TA2-2H-120_24V_clevisU.SLDPRT":(I3,(AX,0,Z_REAR_PIN),{"상승":1,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),
     "J8d_lug_PL6_40x126.SLDPRT":(I3,(AX,0,Z_REAR_PIN),{"상승":1,"하강":1,"1.상승했을때(해석)":1,"2.하강했을때(해석)":0}),
     "G11e_MISUMI_SHCCG8-18.4_pin.SLDPRT":(I3,(AX,-REAR_U_OUT/2,Z_REAR_PIN),{"상승":1,"하강":1,"1.상승했을때(해석)":1,"2.하강했을때(해석)":1})}
NEW2={"J9d_lug_PL6_40x31.SLDPRT":((I3,(AX,0,ZP_UP),{"상승":1,"하강":0,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),(I3,(AX,0,ZP_DN),{"상승":0,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":1})),
      "J11d_MISUMI_SHCCG8-20.4_pin.SLDPRT":((I3,(AX,-FRONT_U_OUT/2,ZP_UP+PIN_ROD_H),{"상승":1,"하강":0,"1.상승했을때(해석)":1,"2.하강했을때(해석)":0}),(I3,(AX,-FRONT_U_OUT/2,ZP_DN+PIN_ROD_H),{"상승":0,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":1}))}
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
for n in list(cc):
    if n.startswith(("B9d_TiMOTION","J8c_sm","J9c_sm","G11d_MISUMI","J11c_MISUMI")):
        sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
a.EditRebuild3; cc=comps(); added={}
for fn in NEW:
    base=fn[:-7]; ex=[n for n in cc if n.startswith(base+"-")]
    added[fn]=[ex[0]] if ex else [add_comp(fn).Name2]; cc=comps()
for fn in NEW2:
    base=fn[:-7]; ex=sorted([n for n in cc if n.startswith(base+"-")])
    while len(ex)<2: add_comp(fn); cc=comps(); ex=sorted([n for n in cc if n.startswith(base+"-")])
    added[fn]=ex[:2]
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for fn,(R,t,supp) in NEW.items():
        n=added[fn][0]; move_fixed(cc[n],R,t); set_supp(n,supp[cfg])
        if fn.startswith("B9e") and supp[cfg]: cc=comps(); cc[n].ReferencedConfiguration=("하강" if cfg.startswith(("하강","2.")) else "상승")
    for fn,pair in NEW2.items():
        for n,(R,t,supp) in zip(added[fn],pair): move_fixed(cc[n],R,t); set_supp(n,supp[cfg])
    a.ForceRebuild3(False)
rep={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[n for n,c in cc.items() if c.GetSuppression2==2]
    rep[cfg]={"boxes":{n:box(cc[n]) for n in act_}}
    if cfg in ("상승","하강"):
        for n in act_:
            if n.startswith(("B9e","J8d","J9d","G11e","J11d")): print(f"  [{cfg}] {n:40s} {box(cc[n])}")
        a.ClearSelection2(True)
        for n in act_: cc[n].Select4(True,NOD,False)
        idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
        rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True)
        rep[cfg]["interf"]=rows; print(f"[{cfg}] 간섭 {len(rows)}:",rows)
    else: print(f"[{cfg}] active",act_)
a.ShowConfiguration2("상승"); a.EditRebuild3; save(a)
json.dump(rep,open(os.path.join(VER,"ta2_rebuild_lug_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("lug stage done")
