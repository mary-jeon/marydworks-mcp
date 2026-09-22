# J5b (2026-09-08): J5의 고정 스택 +10이 OM-1 모터↔고정판 간섭(17,955 mm³)을 만들어 철회.
# 대신 세로여유 +10은 이동 그룹 전체를 10 내려서 확보(zp 상승 -390 / 하강 -530). LA25·브래킷·핀은 그대로 두고
# 클레비스 J9b 높이 40→50(핀 @35)으로 로드 아이(-355/-495)와 맞춘다. 고정판 J1c 구멍은 Ø34→Ø28 원복(소켓은 판 밑 용접 원안).
import os, json, math, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
OX=100.0; ZP_UP=-390.0; ZP_DN=-530.0; NIP_FIX_END=-148.0
AX=-70.0; RY=240.0
def sel_plane(d,names):
    for nm in names:
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def circ(d,x,y,r): d.SketchManager.CreateCircleByRadius(x,y,0.0,r)
def rect(d,cx,cy,hx,hy): d.SketchManager.CreateCenterRectangle(cx,cy,0,cx+hx,cy+hy,0)
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def cyls(d,r):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
                bx=[round(v*1000,1) for v in fc.GetBox]; out.append((round((bx[0]+bx[3])/2,1),round((bx[1]+bx[4])/2,1)))
    return sorted(out)
def del_feats(d,names):
    for nm in names:
        d.ClearSelection2(True); ok=d.Extension.SelectByID2(nm,"BODYFEATURE",0,0,0,False,0,NOD,0)
        if ok: print("  del",nm,d.Extension.DeleteSelection2(1))
    d.ClearSelection2(True); d.EditRebuild3
# ---- 1) J1c: Ø34 → Ø28
P1=os.path.join(Z,"J1c_fixed_plate_185x580_t10.SLDPRT"); d=app.GetOpenDocumentByName(P1); app.ActivateDoc3(P1,False,0,I4()); d=app.ActiveDoc
del_feats(d,["보스-돌출1","보스-돌출2"])
BOLTS=[(55,25),(-55,25),(55,-25),(-55,-25)]
sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True
rect(d,mm(-17.5),0,mm(92.5),mm(290)); circ(d,0,0,mm(14.0))
for (x,y) in BOLTS: circ(d,mm(x),mm(y),mm(4.5))
for y in (RY,-RY): circ(d,mm(AX),mm(y),mm(7.0))
d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(10.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
d.EditRebuild3; print("J1c box",[round(v*1000,1) for v in pv(d,"GetPartBox",True)],"Ø28",cyls(d,14.0),"Ø9",cyls(d,4.5),"Ø14",cyls(d,7.0))
cpm=d.Extension.CustomPropertyManager("")
cpm.Add3("SPEC",30,"185(X -110~75)x580(Y ±290)x10 STS304. 소켓 Ø28(0,0: 용접소켓 G13 판 밑 용접), 볼트 4-Ø9 @(±55,±25), 가이드봉 M16 탭 관통 2개소 @(-70,±240) (드릴 Ø14 = 모델 구멍)",1)
cpm.Add3("REMARK",30,"2026-09-08 J5b: 소켓 플러시안은 OM-1 모터↔판 간섭으로 철회, 원안(판 밑 용접) 유지. 가이드봉 MISUMI PSSFAQ16-590-B10 = 한쪽 M16 수나사 길이 10 → 판 M16 탭 체결(풀림방지제). 상면은 EPDM 가스켓 S30016 아래, M8x25+PW+SW 4본",1)
d.EditRebuild3
# ---- 2) J9b: H 40→50, 핀 @35 (내측 36 유지)
T=6.0; G=36.0; H=50.0; W=G+2*T; PIN=35.0
P9=os.path.join(Z,"J9b_rod_clevis_t6_44x40x60.SLDPRT"); d=app.GetOpenDocumentByName(P9); app.ActivateDoc3(P9,False,0,I4()); d=app.ActiveDoc
del_feats(d,["컷-돌출1","컷-돌출2","보스-돌출1","보스-돌출2"])
sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True)
pts=[(0,0),(W,0),(W,H),(W-T,H),(W-T,T),(T,T),(T,H),(0,H),(0,0)]
for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(60.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
sel_plane(d,("우측면","Right Plane")); d.SketchManager.InsertSketch(True); circ(d,mm(30.0),mm(PIN),mm(5.25)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
n0=sum(len(b.GetFaces()) for b in (d.GetBodies2(0,True) or []))
d.FeatureManager.FeatureCut3(True,False,True,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False); d.EditRebuild3
n1=sum(len(b.GetFaces()) for b in (d.GetBodies2(0,True) or [])); print("J9b box",[round(v*1000,1) for v in pv(d,"GetPartBox",True)],"pin faces",n0,"->",n1)
cpm=d.Extension.CustomPropertyManager("")
cpm.Add3("SPEC",30,"STS304 t6 절곡 U, 내측 36, 높이 50, 폭 60, 핀홀 Ø10.5 @35 양측 관통",1)
cpm.Add3("REMARK",30,"이동판 J5d 상면 (-70,0) 용접. 2026-09-08 J5b: 높이 40→50(핀 @35) — 이동 그룹을 10 내려 호스 세로여유 212 확보하면서 LA25 로드 아이(-355/-495)는 그대로. 파일명 44x40은 구치수(실제 48x50)",1)
d.EditRebuild3
# ---- 3) assembly
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return {c.Name2:c for c in pv(root(),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def R_dir(u):
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
asm.ShowConfiguration2("상승"); asm.EditRebuild3; cc=comps()
P2=[OX,0.0,ZP_DN+30]; L=math.hypot(P2[0],P2[2]-NIP_FIX_END); u=[P2[0]/L,0,(P2[2]-NIP_FIX_END)/L]
straight=[n for n in cc if n.startswith("J19c_hose_3-4in_straight")][0]
TARGET={ # 고정 스택 원복
 "G13_weld_socket_3-4in_L25-1":(0,0,-10),"G14_close_nipple_3-4in_L32-1":(0,0,-19),"G3_valve_body_Tameson_BL2SA3-034-1":(-118.55,-91.2,22.4),
 "B4_actuator_SunYeh_OM-1_simplified-2":(0,-57.49,-76.5),"H16_hose_nipple_3-4in_short_L30-10":(0,0,-118),
 # 이동 그룹 -10
 "J5d_moving_plate_220x540_t8-1":(0,0,ZP_UP),"J5d_moving_plate_220x540_t8-2":(0,0,ZP_DN),
 "G13_weld_socket_3-4in_L25-10":(OX,0,ZP_UP),"H16_hose_nipple_3-4in_short_L30-11":(OX,0,ZP_UP+30),"J17_pipe_3-4in_L100-3":(OX,0,ZP_UP),
 "G13_weld_socket_3-4in_L25-11":(OX,0,ZP_DN),"H16_hose_nipple_3-4in_short_L30-12":(OX,0,ZP_DN+30),"J17_pipe_3-4in_L100-4":(OX,0,ZP_DN),
 "B10_linear_bushing_MISUMI_LHFRW16-21":(-70,240,ZP_UP),"B10_linear_bushing_MISUMI_LHFRW16-22":(-70,-240,ZP_UP),
 "B10_linear_bushing_MISUMI_LHFRW16-23":(-70,240,ZP_DN),"B10_linear_bushing_MISUMI_LHFRW16-24":(-70,-240,ZP_DN),
 "J9b_rod_clevis_t6_44x40x60-1":(-40,-24,ZP_UP),"J9b_rod_clevis_t6_44x40x60-2":(-40,-24,ZP_DN),
 # 핀 J11 (-355/-495) 불변. 호스
 "J19c_hose_3-4in_up_r47-1":(0,0,NIP_FIX_END), straight:(0,0,NIP_FIX_END)}
for n,nt in TARGET.items():
    c=cc[n]; R=R_dir(u) if n==straight else xform(c)["R"]; set_T(c,R,nt)
asm.EditRebuild3; print("straight L",round(L,1))
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
rep={}
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.ForceRebuild3(False); c3=comps(); rep[cfg]={"whatswrong":ww(asm),"boxes":{}}
    print(f"[{cfg}] whatswrong {rep[cfg]['whatswrong']}")
    for n,c in c3.items():
        if c.GetSuppression2==2 and n.startswith(("J5d","J9b","J11","B9b","H16","G13","J17","J19c","B4","G3","B10")):
            b=box(c); rep[cfg]["boxes"][n]=b; print(f"   {n:44s} {b}")
asm.ShowConfiguration2("상승"); asm.EditRebuild3
s=app.GetOpenDocumentByName(os.path.join(Z,"S00000MU0.SLDASM")); cur=s.ConfigurationManager.ActiveConfiguration.Name; gz={}
def walk(c,acc,depth=0):
    n=c.Name2.split("/")[-1]
    if n.startswith(("J17_","J5d","J19c")) and c.GetSuppression2==2:
        b=box(c); acc[n]={"지상고":[round(1109-b[3],1),round(1109-b[0],1)],"y":[b[1],b[4]],"z":[b[2],b[5]]}
    if depth<5:
        for k in (pv(c,"GetChildren") or []): walk(k,acc,depth+1)
for cfg in ("상승","하강"):
    s.ShowConfiguration2(cfg); s.EditRebuild3; acc={}; walk(s.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),acc); gz[cfg]=acc; print(f"[station {cfg}]",json.dumps(acc,ensure_ascii=False))
s.ShowConfiguration2(cur); s.EditRebuild3; rep["station"]=gz
json.dump(rep,open(os.path.join(VER,"J5b_build.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("-> _검증/J5b_build.json (NOT SAVED)")
stop.set()
