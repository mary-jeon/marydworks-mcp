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
NOD=VARIANT(pythoncom.VT_DISPATCH,None); I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
step=r"<PROJECT_DIR>\08_밸브바디_Tameson\bl2sa3-034.step"
out=r"<CAD_DIR>\G3_valve_body_Tameson_BL2SA3-034.SLDPRT"
t0=time.time(); imp=app.GetImportFileData(step); err=I4()
doc=app.LoadFile4(step,"r",imp,err); print("LoadFile4",doc is not None,err.value,round(time.time()-t0,1),"s",flush=True)
pd=doc
if doc.GetType==2:
    root=doc.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True); pd=list(root.GetChildren)[0].GetModelDoc2
e=I4(); wn=I4(); print("saved",pd.Extension.SaveAs(out,0,1,NOD,e,wn),e.value,wn.value,flush=True)
cpm=pd.Extension.CustomPropertyManager("")
for k,v in {"TITLE":"BALL VALVE BODY 3/4in","SPEC":"Tameson BL2SA3-034 G3/4in 3PC SS316 Full bore ISO5211 F03/F04/F05 VK9 L80, 0.85 kg","QT'Y":"1","Material":"STS316","DATE":"2026-09-03","REMARK":"3D: tameson.com CAD zip (bl2sa3-034.step). 씰 PTFE/FKM, 매체 -20~180°C (원문 기재값)"}.items(): cpm.Add3(k,30,v,1)
pd.SetMaterialPropertyName2("","이텍","STS 316"); pd.Save3(1,e,wn)
b=pd.GetBodies2(0,True); print("solid bodies",len(b),"box",[round(v*1000,2) for v in pd.GetPartBox(True)],flush=True)
# port end faces (planar, normal X) to find flow axis & centre
n=0; ends=[]
for f in b[0].GetFaces():
    n+=1
    if n>2500: break
    s=f.GetSurface
    if s.IsPlane:
        pp=s.PlaneParams; bx=[round(v*1000,1) for v in f.GetBox]
        if abs(pp[0])>0.99 and f.GetArea*1e6>200: ends.append((bx[0],round(f.GetArea*1e6),bx))
ends.sort(); print("X-normal planar faces:", ends[:3], ends[-3:], flush=True)
if doc.GetType==2: app.CloseDoc(doc.GetTitle)
stop.set()
