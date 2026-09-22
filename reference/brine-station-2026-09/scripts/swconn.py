# Shared: connect to the running SolidWorks (any PID) via ROT; common helpers. Read-only unless caller changes things.
import sys, os, json, time, threading, ctypes, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
NOD=VARIANT(pythoncom.VT_DISPATCH,None)
def I4(): return VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
Z=r"<CAD_DIR>"
ASM=os.path.join(Z,"염수주입라인.SLDASM")
DESK=r"<PROJECT_DIR>"
VER=os.path.join(DESK,"_검증")
def connect():
    pythoncom.CoInitialize()
    ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
    cands=[]
    for mk in rot:
        nm=mk.GetDisplayName(ctx,None)
        if "SolidWorks_PID_" in nm:
            app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); cands.append((nm,app))
    if not cands: raise SystemExit("SolidWorks not running (no SolidWorks_PID_ in ROT)")
    want=os.environ.get("SW_PID")
    for nm,app in cands:
        if want and nm.endswith("_"+want):
            print("connected",nm,"(SW_PID)","rev",app.RevisionNumber,flush=True); return app
    # 우리 어셈블리(염수주입라인/S00000MU0)가 열린 인스턴스를 우선 — 다른 프로젝트 인스턴스가 같이 떠 있을 수 있음
    for nm,app in cands:
        try:
            titles={d.GetTitle for d in app.GetDocuments}
        except Exception: titles=set()
        if "염수주입라인.SLDASM" in titles or "S00000MU0.SLDASM" in titles:
            print("connected",nm,"(has station docs; instances:",len(cands),") rev",app.RevisionNumber,flush=True); return app
    nm,app=cands[0]; print("connected",nm,"(first of",len(cands),") rev",app.RevisionNumber,flush=True); return app
def watchdog():
    # closes the FeatureWorks modal if it pops up while importing/rebuilding
    user32=ctypes.windll.user32; stop=threading.Event()
    def run():
        P=ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        while not stop.is_set():
            found=[]
            def cb(h,l):
                buf=ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h,buf,256)
                if buf.value=="FeatureWorks" and user32.IsWindowVisible(h): found.append(h)
                return True
            user32.EnumWindows(P(cb),0)
            for h in found: user32.PostMessageW(h,0x0010,0,0); print("watchdog closed FeatureWorks",flush=True)
            # Simulation 알림(#32770 'Simulation', 버튼 1개 '확인' — 예: 메시 정보 최신 아님) → 확인 클릭
            sim=[]
            def cb2(h,l):
                buf=ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h,buf,256)
                cls=ctypes.create_unicode_buffer(64); user32.GetClassNameW(h,cls,64)
                if buf.value=="Simulation" and cls.value=="#32770" and user32.IsWindowVisible(h): sim.append(h)
                return True
            user32.EnumWindows(P(cb2),0)
            for h in sim:
                btns=[]
                def cb3(c,l):
                    cls=ctypes.create_unicode_buffer(64); user32.GetClassNameW(c,cls,64)
                    if cls.value=="Button": btns.append(c)
                    return True
                user32.EnumChildWindows(h,P(cb3),0)
                if len(btns)==1: user32.SendMessageW(btns[0],0x00F5,0,0); print("watchdog clicked Simulation notice",flush=True)
            time.sleep(0.5)
    threading.Thread(target=run,daemon=True).start(); return stop
def box(c):
    try:
        b=c.GetBox(False,False); return [round(v*1000,1) for v in b] if b else None
    except Exception: return None
def xform(c):
    try:
        a=list(c.Transform2.ArrayData); return {"R":[[round(v,6) for v in a[0:3]],[round(v,6) for v in a[3:6]],[round(v,6) for v in a[6:9]]],"t_mm":[round(v*1000,3) for v in a[9:12]]}
    except Exception: return None
def open_doc(app,path,typ,readonly=False):
    e=I4(); wn=I4(); opt=1|(2 if readonly else 0)   # silent (+readonly)
    d=app.OpenDoc6(path,typ,opt,"",e,wn)
    if d is None: raise SystemExit(f"OpenDoc6 failed {path} err={e.value} warn={wn.value}")
    return d
def dump_components(asm):
    cm=asm.ConfigurationManager; root=cm.ActiveConfiguration.GetRootComponent3(True)
    out=[]
    for c in root.GetChildren:
        out.append({"comp":c.Name2,"path":c.GetPathName,"box_mm":box(c),"supp":c.GetSuppression2,"xform":xform(c)})
    return out
