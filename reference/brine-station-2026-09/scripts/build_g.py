# Design G: 3/4" gooseneck + sloped hose, actuator at back (+X), plates symmetric in Y. Rebuild 염수주입라인.SLDASM (Z:) with configs 상승/하강.
import sys, os, re, json, math, time, threading, ctypes, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
user32=ctypes.windll.user32
def watchdog(stop):
    P=ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    while not stop.is_set():
        found=[]
        def cb(h,l):
            buf=ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h,buf,256)
            if buf.value=="FeatureWorks" and user32.IsWindowVisible(h): found.append(h)
            return True
        user32.EnumWindows(P(cb),0)
        for h in found: user32.PostMessageW(h,0x0010,0,0); print("watchdog closed FeatureWorks", flush=True)
        time.sleep(0.5)
stop=threading.Event(); threading.Thread(target=watchdog,args=(stop,),daemon=True).start()
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
NOD=VARIANT(pythoncom.VT_DISPATCH,None); I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
Z=r"<CAD_DIR>"
ASM=os.path.join(Z,"염수주입라인.SLDASM")
# ---- valve 034 geometry from import log
log=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"import_valve034.log"),encoding="utf-8",errors="replace").read()
m=re.search(r"box \[([-\d., ]+)\]",log); vb=[float(v) for v in m.group(1).split(",")]
ends=re.findall(r"\((-?[\d.]+), (\d+), \[([-\d., ]+)\]\)",log)
xs=sorted(set(round(float(e[0]),1) for e in ends)); print("valve port end x:",xs, "box",vb)
XT,XB=xs[0],xs[-1]                       # top/bottom port faces along part X
fb=[float(v) for v in ends[0][2].split(",")]; YC=(fb[1]+fb[4])/2; ZC=(fb[2]+fb[5])/2   # axis centre y,z (part)
PAD=abs(vb[2]-ZC) if abs(vb[2]-ZC)>abs(vb[5]-ZC) else abs(vb[5]-ZC)                  # pad extends -z side? pick larger
pad_neg = abs(vb[2]-ZC)>abs(vb[5]-ZC)
print("valve L=%.1f axis(y,z)=(%.2f,%.2f) pad offset=%.2f pad on -z: %s"%(XB-XT,YC,ZC,PAD,pad_neg))
# ---- layout constants (line coords, mm)
VT=-35.0; VB=VT-(XB-XT)                  # valve top/bottom port z
HY=95.0                                  # hose/gooseneck side offset (+Y)
ZP_UP=-240.0; STROKE=140.0               # moving plate top (retracted)
ZE_UP=ZP_UP+45.0                         # inlet elbow corner z (retracted) = -195
RX,RY,ACT_X=160.0,45.0,380.0
asm=app.ActivateDoc3(ASM,False,0,I4())
if asm is None:
    e=I4(); wn=I4(); asm=app.OpenDoc6(ASM,2,0,"",e,wn)
asm=app.ActiveDoc; name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
print("asm",asm.GetTitle,"configs",list(asm.GetConfigurationNames))
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def box(c):
    b=c.GetBox(False,False); return [round(v*1000,1) for v in b] if b else None
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
def ensure_open(p):
    for d in (app.GetDocuments or []):
        try:
            if d.GetPathName.lower()==p.lower(): return
        except Exception: pass
    e=I4(); wn=I4(); app.OpenDoc6(p,1,1,"",e,wn); app.ActivateDoc3(ASM,False,0,I4())
def add(fn,R,t):
    p=os.path.join(Z,fn); ensure_open(p)
    c=asm.AddComponent5(p,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    if c is None: print("INSERT FAIL",fn); return None
    asm.ClearSelection2(True); asm.Extension.SelectByID2(c.Name2+"@"+name,"COMPONENT",0,0,0,False,0,NOD,0); asm.UnfixComponent(); asm.ClearSelection2(True)
    set_T(c,R,t); return c
# ---- rotations (row-vector convention: rows = images of part x,y,z)
I=[[1,0,0],[0,1,0],[0,0,1]]
R_VALVE=[[0,0,-1],[-1,0,0],[0,1,0]]      # part x->-z, z->+y  (pad at part -z -> line -y)
if not pad_neg: R_VALVE=[[0,0,-1],[1,0,0],[0,-1,0]]   # pad at part +z -> line -y
R_OM1=[[1,0,0],[0,0,-1],[0,1,0]]          # part z->+y : body(part -z) points -y
R_E1=[[1,0,0],[0,-1,0],[0,0,-1]]          # elbow legs: A = part -z, B = part -y ; E1: A->+z, B->+y
R_E1B=[[0,0,-1],[-1,0,0],[0,1,0]]         # A->-y, B->+x
R_NIPX=[[0,1,0],[0,0,1],[1,0,0]]          # part -z -> -x (cylinder extends from t_x toward -x)
R_E2=[[0,-1,0],[1,0,0],[0,0,1]]           # A->-z, B->-x
R_E3=[[0,1,0],[1,0,0],[0,0,-1]]           # A->+z, B->-x
R_E4=R_E1B                                # leg A(-z)->-y, leg B(+y)->+x
R_E5=[[-1,0,0],[0,-1,0],[0,0,1]]          # A->-z, B->+y
R_BUSH=[[0,0,-1],[0,1,0],[1,0,0]]
R_LA25=[[0,-1,0],[1,0,0],[0,0,1]]         # housing bulge (part -y) -> -x
R_U=[[0,1,0],[0,0,1],[1,0,0]]             # bracket profile: u->y, v->z, depth->x  (v up)
R_U_DOWN=[[0,1,0],[0,0,-1],[-1,0,0]]      # bracket hanging: v -> -z
R_PIN=[[0,0,1],[0,1,0],[-1,0,0]]          # part -z -> +x ... pin along X: cylinder from t_x-? ; part z->-x: rows z->(-1,0,0)
R_PIN=[[0,1,0],[0,0,1],[-1,0,0]]          # x->y, y->z, z->-x  (det +1)
def R_dir(u):   # part -z axis along unit vector u (in xz-plane), part y stays +y
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
# ---- clear assembly (all configs share components)
asm.ShowConfiguration2("상승")
sel([c.Name2 for c in root().GetChildren]); asm.Extension.DeleteSelection2(0); asm.ClearSelection2(True)
print("cleared:", len(list(root().GetChildren)))
# ---- fixed parts
fixed=[]
def F(fn,R,t):
    c=add(fn,R,t)
    if c: fixed.append(c.Name2); print(f"  {c.Name2:44s} {box(c)}")
    return c
F("G1_fixed_plate_150x555_t10.SLDPRT",I,(0,0,0))
F("G13_weld_socket_3-4in_L25.SLDPRT",I,(0,0,-10))
F("G14_close_nipple_3-4in_L32.SLDPRT",I,(0,0,VT+16))
# valve: part point (XT, YC, ZC) -> (0,0,VT)
R=R_VALVE
def img(p,R): return [sum(p[k]*R[k][j] for k in range(3)) for j in range(3)]
pv=img([XT,YC,ZC],R); tv=(0-pv[0],0-pv[1],VT-pv[2])
c=F("G3_valve_body_Tameson_BL2SA3-034.SLDPRT",R,tv)
F("B4_actuator_SunYeh_OM-1_simplified.SLDPRT",R_OM1,(0,-PAD,(VT+VB)/2))
F("G14_close_nipple_3-4in_L32.SLDPRT",I,(0,0,VB+16))
ZE1=VB-45.0                               # elbow1 corner
F("G_elbow_3-4in_L45.SLDPRT",R_E1,(0,0,ZE1))
F("G_elbow_3-4in_L45.SLDPRT",R_E1B,(0,HY,ZE1))
F("G15_pipe_nipple_3-4in_L370.SLDPRT",R_NIPX,(415,HY,ZE1))
F("G_elbow_3-4in_L45.SLDPRT",R_E2,(460,HY,ZE1))
ZE3=ZE1-90.0
F("G_elbow_3-4in_L45.SLDPRT",R_E3,(460,HY,ZE3))
F("G16_hose_nipple_3-4in_L55.SLDPRT",R_NIPX,(415,HY,ZE3))
F("G19_hose_3-4in_end_L40.SLDPRT",R_NIPX,(360,HY,ZE3))
F("G2_guide_shaft_MISUMI_PSSFAQ16-445-B10.SLDPRT",I,(RX,RY,0))
F("G2_guide_shaft_MISUMI_PSSFAQ16-445-B10.SLDPRT",I,(RX,-RY,0))
# LA25: rod eye at plate top - 25
ZEYE=ZP_UP-21.0; tz_la=ZEYE+161.5
F("B9_LINAK_LA25_2500N_150st_24V.SLDPRT",R_LA25,(ACT_X,0,tz_la))
ZBACK=58.5+tz_la; print("LA25 back eye z=",ZBACK,"housing z",-90+tz_la,"..",50+tz_la)
# hanging bracket: profile v axis -> -z: bridge at v 88..100 -> z -(88..100)?? we want bridge at top (under plate, z -10..-22) and pin at ZBACK.
# use R_U_DOWN with t_z so that v=100 (bridge outer) -> z=-10 : z=-v+t -> t=90 ; pin hole at v=69 -> z=21?? mismatch; instead scale by placing so hole v=69 -> ZBACK: t_z=ZBACK+69
R_UH=[[1,0,0],[0,0,1],[0,-1,0]]           # hanging bracket: u->x, v->+z (bridge at top), depth->-y
HX0=ACT_X-87.85-4-12                      # legs outside LA25 housing (x 292..408): 276..288 / 412..424
F("G8_bent_U_bracket_t12_148x100x60.SLDPRT",R_UH,(HX0,-30,ZBACK-69))
F("G11_clevis_pin_d10_L160.SLDPRT",R_PIN,(HX0+154,0,ZBACK))
# ---- moving sets (up / dn)
def moving(tag,dz):
    zp=ZP_UP-dz; ze=ZE_UP-dz; names=[]
    def M(fn,R,t):
        c=add(fn,R,t)
        if c: names.append(c.Name2); print(f"  [{tag}] {c.Name2:44s} {box(c)}")
    L=math.hypot(320-140, ze-ZE3); u=[(140-320)/L,0,(ze-ZE3)/L]
    diag=[f for f in os.listdir(Z) if f.startswith("G19_hose_3-4in_diag_"+tag)]
    if diag: M(diag[0],R_dir(u),(320,HY,ZE3))
    M("G19_hose_3-4in_end_L40.SLDPRT",R_NIPX,(140,HY,ze))
    M("G16_hose_nipple_3-4in_L55.SLDPRT",R_NIPX,(100,HY,ze))
    M("G_elbow_3-4in_L45.SLDPRT",R_E4,(0,HY,ze))
    M("G_elbow_3-4in_L45.SLDPRT",R_E5,(0,0,ze))
    M("G5_moving_plate_150x515_t10.SLDPRT",I,(0,0,zp))
    M("G13_weld_socket_3-4in_L25.SLDPRT",I,(0,0,zp-10))
    M("G17_nozzle_pipe_3-4in_L70.SLDPRT",I,(0,0,zp-35))
    M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(RX,RY,zp))
    M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(RX,-RY,zp))
    if tag=="dn": M("B12_LA25_rod_extension_d20_L140.SLDPRT",I,(ACT_X,0,ZEYE))
    return names
up=moving("up",0.0); dn=moving("dn",STROKE)
asm.EditRebuild3
# suppression per config
sel(dn); asm.EditSuppress2; asm.ClearSelection2(True)
asm.ShowConfiguration2("하강"); sel(up); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
print("하강 suppressed up-set:", all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in up))
asm.ShowConfiguration2("상승"); asm.EditRebuild3
print("상승 suppressed dn-set:", all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in dn))
final=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in root().GetChildren]
json.dump({"components":final,"params":{"VT":VT,"VB":VB,"HY":HY,"ZP_UP":ZP_UP,"ZE_UP":ZE_UP,"ZE1":ZE1,"ZE3":ZE3,"ZEYE":ZEYE,"ZBACK":ZBACK}},open(r"<PROJECT_DIR>\_검증\G_rebuild_boxes.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("components:",len(final))
stop.set()
