# Design J2 (final lateral layout, H=140 raise assumed): keep fixed stack (G13-1, G14-1, G3-1, B4-2), delete the rest, rebuild.
import os, json, math
from swconn import *
stop=watchdog()
app=connect()
asm=open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
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
def R_dir(u):
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
I=[[1,0,0],[0,1,0],[0,0,1]]
R_BUSH=[[0,0,-1],[0,1,0],[1,0,0]]
R_LA25_J=[[-1,0,0],[0,-1,0],[0,0,1]]     # housing bulge -> +y (outward)
R_UH_J=[[0,1,0],[0,0,1],[1,0,0]]         # bracket u->y, v->+z, depth->x
R_PIN_J=[[1,0,0],[0,0,1],[0,-1,0]]       # pin along +y
R_HOSEUP=[[1,0,0],[0,0,1],[0,-1,0]]      # hose part: x->x, y(up)->z, z->-y
# ---- layout (line coords; fixed plate top z=0 = 지상고 2,050)
H_RAISE=140.0
VB=-118.0; NIP_FIX_END=VB-30.0           # -148
RX=60.0; RY=240.0; ACT_Y=300.0; OX=80.0; STROKE=140.0
ZP_UP=-380.0                             # moving plate top (상승); 하강 -520 -> bottom 1,520
ZEYE=ZP_UP-21.0; tz_la=ZEYE+161.5; ZBACK=58.5+tz_la     # -401 / -239.5 / -181
BR_H=240.0
asm.ShowConfiguration2("상승"); asm.EditRebuild3
KEEP=("G13_weld_socket_3-4in_L25-1","G14_close_nipple_3-4in_L32-1","G3_valve_body_Tameson_BL2SA3-034-1","B4_actuator_SunYeh_OM-1_simplified-2")
kill=[c.Name2 for c in root().GetChildren if c.Name2 not in KEEP]
if kill: sel(kill); print("delete",len(kill),asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True)
left=sorted(c.Name2 for c in root().GetChildren); assert left==sorted(KEEP), left
fixed=[]
def F(fn,R,t):
    c=add(fn,R,t)
    if c: fixed.append(c.Name2); print(f"  {c.Name2:46s} {box(c)}")
    return c
F("J1b_fixed_plate_150x710_t10.SLDPRT",I,(0,0,0))
F("H16_hose_nipple_3-4in_short_L30.SLDPRT",I,(0,0,VB))
F("J2_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT",I,(RX,RY,0)); F("J2_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT",I,(RX,-RY,0))
F("B9_LINAK_LA25_2500N_150st_24V.SLDPRT",R_LA25_J,(0,ACT_Y,tz_la)); print("  LA25 back eye z",ZBACK)
F("J8_bent_U_bracket_t12_148x240x60.SLDPRT",R_UH_J,(30,ACT_Y-44,-10-BR_H))
F("G11_clevis_pin_d10_L160.SLDPRT",R_PIN_J,(0,ACT_Y-50,ZBACK))
asm.EditRebuild3
straight=[f for f in os.listdir(Z) if f.startswith("J19b_hose_3-4in_straight_")][0]
def moving(tag,dz):
    zp=ZP_UP-dz; names=[]
    def M(fn,R,t):
        c=add(fn,R,t)
        if c: names.append(c.Name2); print(f"  [{tag}] {c.Name2:46s} {box(c)}")
    M("J5b_moving_plate_200x620_t10.SLDPRT",I,(0,0,zp))
    M("G13_weld_socket_3-4in_L25.SLDPRT",I,(OX,0,zp+15))          # zp-10..zp+15 (flush with plate bottom)
    M("H16_hose_nipple_3-4in_short_L30.SLDPRT",I,(OX,0,zp+45))    # zp+15..zp+45
    M("J17_pipe_3-4in_L100.SLDPRT",I,(OX,0,zp))                    # zp-100..zp (10 into socket)
    M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(RX,RY,zp)); M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(RX,-RY,zp))
    P1=[0.0,0.0,NIP_FIX_END]; P2=[OX,0.0,zp+45]
    if tag=="up":
        M("J19b_hose_3-4in_up_r40.SLDPRT",R_HOSEUP,(0,0,NIP_FIX_END)); print("  hose up: D=%.0f"%(P1[2]-P2[2]))
    else:
        L=math.hypot(P2[0]-P1[0],P2[2]-P1[2]); u=[(P2[0]-P1[0])/L,0,(P2[2]-P1[2])/L]; print("  hose straight chord %.1f (%s)"%(L,straight))
        M(straight,R_dir(u),(P1[0],0,P1[2]))
        M("B12_LA25_rod_extension_d20_L140.SLDPRT",I,(0,ACT_Y,ZEYE))
    return names
up=moving("up",0.0); dn=moving("dn",STROKE); asm.EditRebuild3
sel(dn); asm.EditSuppress2; asm.ClearSelection2(True)
asm.ShowConfiguration2("하강"); asm.EditRebuild3; sel(up); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
ok_dn=all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in up) and all(c.GetSuppression2==2 for c in root().GetChildren if c.Name2 in dn)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
ok_up=all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in dn) and all(c.GetSuppression2==2 for c in root().GetChildren if c.Name2 in up)
print("suppression 하강 ok:",ok_dn," 상승 ok:",ok_up)
res={"params":{"H_RAISE":H_RAISE,"VB":VB,"RX":RX,"RY":RY,"ACT_Y":ACT_Y,"OX":OX,"ZP_UP":ZP_UP,"STROKE":STROKE,"ZEYE":ZEYE,"ZBACK":ZBACK,"tz_la":tz_la,"BR_H":BR_H},"fixed":fixed,"up":up,"dn":dn}
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    res[cfg]=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in root().GetChildren]
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump(res,open(os.path.join(VER,"J2_rebuild_boxes.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("components:",len(res["상승"]),"-> _검증/J2_rebuild_boxes.json ; NOT SAVED (dirty=%s)"%asm.GetSaveFlag)
stop.set()
