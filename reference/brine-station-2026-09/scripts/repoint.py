import sys, os, time, threading, ctypes, pythoncom, win32com.client as w
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
I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
DEST=r"<CAD_DIR>"
OLD=r"<PROJECT_DIR>\염수주입라인.SLDASM"
NEW=os.path.join(DEST,"염수주입라인.SLDASM"); TANK=os.path.join(DEST,"S30000MU0.SLDASM")
# 1) tank is closed: swap its reference
r=app.ReplaceReferencedDocument(TANK, OLD, NEW); print("ReplaceReferencedDocument ->", r)
# 2) open new line asm and verify part paths
e=I4(); wn=I4(); line=app.OpenDoc6(NEW,2,0,"",e,wn); print("open Z line:", line is not None, e.value, wn.value)
root=line.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
bad=[]
for c in root.GetChildren:
    p=c.GetPathName
    if not p.lower().startswith(DEST.lower()): bad.append((c.Name2,p))
print("line children:", len(list(root.GetChildren)), "non-Z refs:", bad)
print("line configs:", list(line.GetConfigurationNames))
# 3) open tank, verify component path + configs
e=I4(); wn=I4(); tank=app.OpenDoc6(TANK,2,0,"",e,wn); print("open tank:", tank is not None, e.value, wn.value)
def comp():
    r=tank.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    return [c for c in r.GetChildren if c.Name2.split("/")[-1].startswith("염수주입라인")][0]
for nm in ("기본","상승","하강"):
    tank.ShowConfiguration2(nm); tank.EditRebuild3; c=comp()
    print(f"tank {nm}: line path={c.GetPathName} refcfg={c.ReferencedConfiguration} supp={c.GetSuppression2}")
tank.ShowConfiguration2("기본")
print("tank dirty:", tank.GetSaveFlag)
stop.set()
