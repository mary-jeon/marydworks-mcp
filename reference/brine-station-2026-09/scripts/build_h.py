# Design H: socket→hose nipple→hose→hose nipple→socket→plate→pipe (moving outlet offset +80 back), LA25 back, plates symmetric.
import sys, os, json, math, time, threading, ctypes, pythoncom, win32com.client as w
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
        for h in found: user32.PostMessageW(h,0x0010,0,0)
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
asm=app.ActivateDoc3(ASM,False,0,I4())
if asm is None:
    e=I4(); wn=I4(); asm=app.OpenDoc6(ASM,2,0,"",e,wn)
asm=app.ActiveDoc; name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
asm.ShowConfiguration2("상승")
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
            if (d.GetPathName or "").lower()==p.lower(): return
        except Exception: pass
    e=I4(); wn=I4(); app.OpenDoc6(p,1,1,"",e,wn); app.ActivateDoc3(ASM,False,0,I4())
def add(fn,R,t):
    p=os.path.join(Z,fn); ensure_open(p)
    c=asm.AddComponent5(p,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    if c is None: print("INSERT FAIL",fn); return None
    asm.ClearSelection2(True); asm.Extension.SelectByID2(c.Name2+"@"+name,"COMPONENT",0,0,0,False,0,NOD,0); asm.UnfixComponent(); asm.ClearSelection2(True)
    set_T(c,R,t); return c
I=[[1,0,0],[0,1,0],[0,0,1]]
R_BUSH=[[0,0,-1],[0,1,0],[1,0,0]]
R_LA25=[[0,-1,0],[1,0,0],[0,0,1]]
R_UH=[[1,0,0],[0,0,1],[0,-1,0]]
R_PIN=[[0,1,0],[0,0,1],[-1,0,0]]
def R_dir(u):
    r3=[-u[0],0.0,-u[2]]; r2=[0.0,1.0,0.0]
    r1=[r2[1]*r3[2]-r2[2]*r3[1], r2[2]*r3[0]-r2[0]*r3[2], r2[0]*r3[1]-r2[1]*r3[0]]
    return [r1,r2,r3]
def Ry(phi):  # rotation about Y, row convention
    c,s=math.cos(phi),math.sin(phi); return [[c,0,-s],[0,1,0],[s,0,c]]
def img(p,R): return [sum(p[k]*R[k][j] for k in range(3)) for j in range(3)]
# ---- layout
VB=-118.0; OX=80.0; RX=300.0; RY=60.0; ACT_X=380.0; STROKE=140.0
ZP_UP=-262.0                      # moving plate top (up)
NIP_FIX_END=VB-30.0               # fixed short hose nipple tip (-148)
# ---- remove old moving/fixed items being replaced
kill=[c.Name2 for c in root().GetChildren if c.Name2.startswith(("G7_","G5c_","G2_","G1b_","G16_","B12_","B10_"))]
sel(kill); asm.Extension.DeleteSelection2(0); asm.ClearSelection2(True); print("deleted",len(kill))
fixed=[]
def F(fn,R,t):
    c=add(fn,R,t)
    if c: fixed.append(c.Name2); print(f"  {c.Name2:46s} {box(c)}")
    return c
F("H1_fixed_plate_150x555_t10.SLDPRT",I,(0,0,0))
F("H16_hose_nipple_3-4in_short_L30.SLDPRT",I,(0,0,VB))
F("H2_guide_shaft_MISUMI_PSSFAQ16-470-B10.SLDPRT",I,(RX,RY,0)); F("H2_guide_shaft_MISUMI_PSSFAQ16-470-B10.SLDPRT",I,(RX,-RY,0))
ZEYE=ZP_UP-21.0; tz_la=ZEYE+161.5; ZBACK=58.5+tz_la
for c in root().GetChildren:
    if c.Name2.startswith("B9_LINAK"): set_T(c,R_LA25,(ACT_X,0,tz_la)); print("  LA25 moved", box(c), "back eye z", ZBACK, "housing", -90+tz_la, 50+tz_la)
    if c.Name2.startswith("G8_bent"): set_T(c,R_UH,(ACT_X-87.85-4-12,-30,-110)); print("  bracket", box(c))
    if c.Name2.startswith("G11_clevis"): set_T(c,R_PIN,(270,0,ZBACK)); print("  pin", box(c))
asm.EditRebuild3
# ---- hose fit (up): arc part: start S0=(59,0,0) tangent -z ; end E0=(59cos223°, 0, -59 sin223°)
Rr=59.0; th=math.radians(223.0)
S0=[Rr,0.0,0.0]; E0=[Rr*math.cos(th),0.0,-Rr*math.sin(th)]
def moving(tag,dz):
    zp=ZP_UP-dz; names=[]
    def M(fn,R,t):
        c=add(fn,R,t)
        if c: names.append(c.Name2); print(f"  [{tag}] {c.Name2:46s} {box(c)}")
    M("H5_moving_plate_170x515_t10.SLDPRT",I,(0,0,zp))
    M("G13_weld_socket_3-4in_L25.SLDPRT",I,(OX,0,zp+10))          # through plate: zp-15..zp+10
    M("H16_hose_nipple_3-4in_short_L30.SLDPRT",I,(OX,0,zp+40))    # zp+10..zp+40
    M("H17_pipe_3-4in_L68.SLDPRT",I,(OX,0,zp-15))                  # zp-83..zp-15  (tip -345 up)
    M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(RX,RY,zp)); M("B10_linear_bushing_MISUMI_LHFRW16.SLDPRT",R_BUSH,(RX,-RY,zp))
    P1=[0.0,0.0,NIP_FIX_END]; P2=[OX,0.0,zp+40]
    if tag=="up":
        v1=[P2[0]-P1[0],0,P2[2]-P1[2]]; best=None
        for k in range(0,3600):
            phi=math.radians(k/10); R=Ry(phi); a=img(S0,R); b=img(E0,R); d=[b[0]-a[0],b[2]-a[2]]
            err=math.hypot(d[0]-v1[0],d[1]-v1[2])
            if best is None or err<best[0]: best=(err,phi,R,a)
        err,phi,R,a=best; t=(P1[0]-a[0],0,P1[2]-a[2]); print("  hose arc fit: phi=%.1f° err=%.1f mm"%(math.degrees(phi),err))
        M("H19_hose_3-4in_arc_R59_223deg.SLDPRT",R,t)
    else:
        L=math.hypot(P2[0]-P1[0],P2[2]-P1[2]); u=[(P2[0]-P1[0])/L,0,(P2[2]-P1[2])/L]; print("  hose straight chord %.1f"%L)
        M("H19_hose_3-4in_straight_L230.SLDPRT",R_dir(u),(P1[0],0,P1[2]))
        M("B12_LA25_rod_extension_d20_L140.SLDPRT",I,(ACT_X,0,ZEYE))
    return names
up=moving("up",0.0); dn=moving("dn",STROKE); asm.EditRebuild3
sel(dn); asm.EditSuppress2; asm.ClearSelection2(True)
asm.ShowConfiguration2("하강"); asm.EditRebuild3; sel(up); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
print("하강 ok:", all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in up) and all(c.GetSuppression2==2 for c in root().GetChildren if c.Name2 in dn))
asm.ShowConfiguration2("상승"); asm.EditRebuild3
print("상승 ok:", all(c.GetSuppression2==0 for c in root().GetChildren if c.Name2 in dn) and all(c.GetSuppression2==2 for c in root().GetChildren if c.Name2 in up))
final=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in root().GetChildren]
json.dump({"components":final,"params":{"ZP_UP":ZP_UP,"OX":OX,"RX":RX,"RY":RY,"ZEYE":ZEYE,"ZBACK":ZBACK}},open(r"<PROJECT_DIR>\_검증\H_rebuild_boxes.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("components:",len(final))
# cleanup superseded files
for d in list(app.GetDocuments):
    try: t=d.GetTitle
    except Exception: continue
    if t.startswith(("G7_","G5c_","G2_","G1b_","G16_","G19b_")): app.CloseDoc(t)
for f in os.listdir(Z):
    if f.startswith(("G7_","G5c_","G2_","G1b_","G16_","G19b_")) and f.lower().endswith(".sldprt"):
        try: os.remove(os.path.join(Z,f)); print("removed",f)
        except Exception: print("could not remove",f)
stop.set()
