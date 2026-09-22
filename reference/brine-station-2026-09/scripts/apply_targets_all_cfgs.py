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

asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager; CFGS=list(asm.GetConfigurationNames)
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return {c.Name2:c for c in pv(root(),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def R_dir(u):
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
P2=[OX,0.0,ZP_DN+30]; L=math.hypot(P2[0],P2[2]-NIP_FIX_END); u=[P2[0]/L,0,(P2[2]-NIP_FIX_END)/L]
asm.ShowConfiguration2("상승"); asm.EditRebuild3; cc=comps()
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

for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps()
    for n,nt in TARGET.items():
        c=cc[n]; R=R_dir(u) if n==straight else xform(c)["R"]; set_T(c,R,nt)
    asm.ForceRebuild3(False)
    bad=[(n,xform(cc[n])["t_mm"]) for n,nt in TARGET.items() if any(abs(a-b)>0.05 for a,b in zip(xform(cc[n])["t_mm"],nt))]
    print(f"[{cfg}] mismatches after set: {bad}")
asm.ShowConfiguration2("하강"); asm.ForceRebuild3(False); cc=comps()
for n in ("G13_weld_socket_3-4in_L25-1","H16_hose_nipple_3-4in_short_L30-10","J5d_moving_plate_220x540_t8-2","G13_weld_socket_3-4in_L25-11","J17_pipe_3-4in_L100-4","J9b_rod_clevis_t6_44x40x60-2","J19c_hose_3-4in_straight_L366-1"):
    print("  하강",n,box(cc[n]))
asm.ShowConfiguration2("상승"); asm.EditRebuild3
stop.set()
