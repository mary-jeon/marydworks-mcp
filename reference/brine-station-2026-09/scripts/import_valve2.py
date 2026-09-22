import sys, os, time, threading, pythoncom, win32com.client as w, ctypes
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
        time.sleep(0.7)
stop=threading.Event(); threading.Thread(target=watchdog,args=(stop,),daemon=True).start()
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
step=r"<PROJECT_DIR>\08_밸브바디_Tameson\bl2sa3-100.step"
out=r"<PROJECT_DIR>\_native\B3_valve_body_Tameson_BL2SA3-100.SLDPRT"
t0=time.time(); imp=app.GetImportFileData(step)
err=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
doc=app.LoadFile4(step,"r",imp,err); print("LoadFile4", doc is not None, err.value, round(time.time()-t0,1),"s", flush=True)
print("type", doc.GetType, doc.GetTitle, flush=True)
e=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0); wn=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
NOD=VARIANT(pythoncom.VT_DISPATCH,None)
if doc.GetType==2:
    root=doc.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    kids=list(root.GetChildren); print("children", [k.Name2 for k in kids], flush=True)
    pd=kids[0].GetModelDoc2; print("child doc", pd.GetTitle, pd.GetType, flush=True)
    ok=pd.Extension.SaveAs(out,0,1,NOD,e,wn); print("saved child part", ok, e.value, wn.value, flush=True)
    cpm=pd.Extension.CustomPropertyManager("")
    for k,v in {"TITLE":"BALL VALVE BODY","SPEC":"Tameson BL2SA3-100 G1\" 3PC SS316 Full bore ISO5211 F04/F05 VK11 L90","QT'Y":"1","Material":"STS316","DATE":"2026-09-03","REMARK":"3D: tameson.com CAD zip (bl2sa3-100.step). 씰 PTFE/FKM, 매체 -20~180°C (원문 기재값)"}.items(): cpm.Add3(k,30,v,1)
    print("resave", pd.Save3(1,e,wn), e.value, flush=True)
    b=pd.GetBodies2(0,True); print("solid bodies", len(b), flush=True)
    cyl=[]
    for f in b[0].GetFaces():
        s=f.GetSurface
        if s.IsCylinder:
            p=s.CylinderParams; bx=[round(v*1000,1) for v in f.GetBox]
            cyl.append((round(p[6]*1000,2),[round(v,2) for v in p[3:6]],bx,round(f.GetArea*1e6)))
    cyl.sort(key=lambda c:-c[3])
    for c in cyl[:16]: print("  ",c, flush=True)
    print("part box:", [round(v*1000,1) for v in pd.GetPartBox(True)], flush=True)
    app.CloseDoc(doc.GetTitle); print("closed temp assembly; part file:", os.path.exists(out), flush=True)
else:
    ok=doc.Extension.SaveAs(out,0,1,NOD,e,wn); print("saved part", ok, e.value, wn.value, flush=True)
stop.set()
