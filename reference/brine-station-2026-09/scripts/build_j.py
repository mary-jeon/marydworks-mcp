# Design J: lateral (Y) layout per user sketch 2026-09-03. Keeps fixed stack (G13 socket, G14 nipple, G3 valve, B4 OM-1 at -Y),
# deletes everything else, rebuilds: J1 fixed plate (Y -290..+420), H16 short nipple, H2 rods (0,±240), LA25 at (0,+300) bulge +Y,
# G8 bracket + G11 pin along Y, moving set at ZP_UP=-262 / -402: J5 plate, G13 socket, H16 nipple, H17 pipe (outlet x=+80), B10 bushings,
# hose J19 arc (상승) / straight (하강), B12 rod extension (하강). Memory only — no save.
import os, json, math
from swconn import *
stop=watchdog()
app=connect()
asm=open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
print("asm",asm.GetTitle,"configs",list(asm.GetConfigurationNames))
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
def ensure_open(p):
    for d in (app.GetDocuments or []):
        try:
            if (d.GetPathName or "").lower()==p.lower(): return
        except Exception: pass
    e=I4(); wn=I4(); app.OpenDoc6(p,1,1,"",e,wn); app.ActivateDoc3(ASM,False,0,I4())
def add(fn,R,t):
    p=os.path.join(Z,fn); ensure_open(p)
    c=asm.AddComponent5(p,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    if c is None: print("INSERT FAIL",fn); return None
    asm.ClearSelection2(True); asm.Extension.SelectByID2(c.Name2+"@"+name,"COMPONENT",0,0,0,False,0,NOD,0); asm.UnfixComponent(); asm.ClearSelection2(True)
    set_T(c,R,t); return c
def img(p,R): return [sum(p[k]*R[k][j] for k in range(3)) for j in range(3)]
def Ry(phi):
    c,s=math.cos(phi),math.sin(phi); return [[c,0,-s],[0,1,0],[s,0,c]]
def R_dir(u):   # part -z axis along unit vector u (xz-plane), part y stays +y
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
# ---- rotations (row-vector: rows = images of part x,y,z)
I=[[1,0,0],[0,1,0],[0,0,1]]
R_BUSH=[[0,0,-1],[0,1,0],[1,0,0]]
R_LA25_J=[[-1,0,0],[0,-1,0],[0,0,1]]     # housing bulge (part -y) -> +y (outward, away from hose)
R_UH_J=[[0,1,0],[0,0,1],[1,0,0]]         # bracket: u->y, v->+z (bridge up under plate), depth(part -z)->x
R_PIN_J=[[1,0,0],[0,0,1],[0,-1,0]]       # pin: part -z -> +y
# ---- layout (line coords: x=뒤, y=좌우, z=위; origin = 호퍼 출구 중심, 고정판 상면 z=0)
VB=-118.0; NIP_FIX_END=VB-30.0           # fixed short hose nipple tip (-148)
RY=240.0; ACT_Y=300.0; OX=80.0; STROKE=140.0
ZP_UP=-262.0
ZEYE=ZP_UP-21.0; tz_la=ZEYE+161.5; ZBACK=58.5+tz_la
asm.ShowConfiguration2("상승"); asm.EditRebuild3
# ---- delete everything except the fixed stack
KEEP=("G13_weld_socket_3-4in_L25-1","G14_close_nipple_3-4in_L32-1","G3_valve_body_Tameson_BL2SA3-034-1","B4_actuator_SunYeh_OM-1_simplified-2")
kill=[c.Name2 for c in root().GetChildren if c.Name2 not in KEEP]
sel(kill); ok=asm.Extension.DeleteSelection2(0); asm.ClearSelection2(True)
left=[c.Name2 for c in root().GetChildren]; print("deleted",len(kill),"ok",ok,"remaining",left)
assert sorted(left)==sorted(KEEP), "unexpected remaining components"
# ---- fixed side
fixed=[]
def F(fn,R,t):
    c=add(fn,R,t)
    if c: fixed.append(c.Name2); print(f"  {c.Name2:46s} {box(c)}")
    return c
F("J1_fixed_plate_150x710_t10.SLDPRT",I,(0,0,0))
F("H16_hose_nipple_3-4in_short_L30.SLDPRT",I,(0,0,VB))
F("H2_guide_shaft_MISUMI_PSSFAQ16-470-B10.SLDPRT",I,(0,RY,0)); F("H2_guide_shaft_MISUMI_PSSFAQ16-470-B10.SLDPRT",I,(0,-RY,0))
la=F("B9_LINAK_LA25_2500N_150st_24V.SLDPRT",R_LA25_J,(0,ACT_Y,tz_la)); print("  LA25 back eye z",ZBACK,"housing z",-90+tz_la,"..",50+tz_la)
F("G8_bent_U_bracket_t12_148x100x60.SLDPRT",R_UH_J,(30,ACT_Y-44,-110))
F("G11_clevis_pin_d10_L160.SLDPRT",R_PIN_J,(0,ACT_Y-50,ZBACK))
asm.EditRebuild3
# ---- hose (상승): arc R59 223° in XZ plane; S0 start tangent -z at +X; pick the fit that bulges to +X (뒤)
Rr=59.0; th=math.radians(223.0)
S0=[Rr,0.0,0.0]; E0=[Rr*math.cos(th),0.0,-Rr*math.sin(th)]; M0=[Rr*math.cos(th/2),0.0,-Rr*math.sin(th/2)]
straight=[f for f in os.listdir(Z) if f.startswith("J19_hose_3-4in_straight_")][0]
def moving(tag,dz):
    zp=ZP_UP-dz; names=[]
    def M(fn,R,t):
        c=add(fn,R,t)
        if c: names.append(c.Name2); print(f"  [{tag}] {c.Name2:46s} {box(c)}")
    M("J5_moving_plate_200x620_t10.SLDPRT",I,(0,0,zp))
    M("G13_weld_socket_3-4in_L25.SLDPRT",I,(OX,0,zp+10))          # zp-15..zp+10 (through plate, 10 above)
    M("H16_hose_nipple_3-4in_short_L30.SLDPRT",I,(OX,0,zp+40))    # zp+10..zp+40
    M("H17_pipe_3-4in_L68.SLDPRT",I,(OX,0,zp-15))                  # zp-83..zp-15
    M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(0,RY,zp)); M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(0,-RY,zp))
    P1=[0.0,0.0,NIP_FIX_END]; P2=[OX,0.0,zp+40]
    if tag=="up":
        v1=[P2[0]-P1[0],0,P2[2]-P1[2]]; cands=[]
        for k in range(0,3600):
            phi=math.radians(k/10); R=Ry(phi); a=img(S0,R); b=img(E0,R); d=[b[0]-a[0],b[2]-a[2]]
            err=math.hypot(d[0]-v1[0],d[1]-v1[2])
            if err<1.5: cands.append((img(M0,R)[0]-a[0],err,phi,R,a))
        bulge,err,phi,R,a=max(cands)      # arc midpoint furthest toward +x
        t=(P1[0]-a[0],0,P1[2]-a[2]); print("  hose arc fit: phi=%.1f° err=%.2f mm, mid-arc x offset %+.1f (candidates %d)"%(math.degrees(phi),err,bulge,len(cands)))
        M("J19_hose_3-4in_arc_R59_223deg.SLDPRT",R,t)
    else:
        L=math.hypot(P2[0]-P1[0],P2[2]-P1[2]); u=[(P2[0]-P1[0])/L,0,(P2[2]-P1[2])/L]; print("  hose straight chord %.1f (part %s)"%(L,straight))
        M(straight,R_dir(u),(P1[0],0,P1[2]))
        M("B12_LA25_rod_extension_d20_L140.SLDPRT",I,(0,ACT_Y,ZEYE))
    return names
up=moving("up",0.0); dn=moving("dn",STROKE); asm.EditRebuild3
# ---- per-config suppression
sel(dn); asm.EditSuppress2; asm.ClearSelection2(True)
asm.ShowConfiguration2("하강"); asm.EditRebuild3; sel(up); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
ok_dn=all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in up) and all(c.GetSuppression2==2 for c in root().GetChildren if c.Name2 in dn)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
ok_up=all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in dn) and all(c.GetSuppression2==2 for c in root().GetChildren if c.Name2 in up)
print("suppression 하강 ok:",ok_dn," 상승 ok:",ok_up)
res={"params":{"VB":VB,"RY":RY,"ACT_Y":ACT_Y,"OX":OX,"ZP_UP":ZP_UP,"STROKE":STROKE,"ZEYE":ZEYE,"ZBACK":ZBACK,"tz_la":tz_la},"fixed":fixed,"up":up,"dn":dn}
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    res[cfg]=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in root().GetChildren]
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump(res,open(os.path.join(VER,"J_rebuild_boxes.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("components:",len(res["상승"]),"-> _검증/J_rebuild_boxes.json ; NOT SAVED (dirty=%s)"%asm.GetSaveFlag)
stop.set()
