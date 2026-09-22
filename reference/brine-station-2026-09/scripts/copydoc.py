import sys, os, glob, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
SRC=r"<PROJECT_DIR>"
NAT=os.path.join(SRC,"_native")
DEST=r"<CAD_DIR>"
# close all open docs (only my line docs are open now)
app.CloseAllDocuments(True); print("closed all; open now:", len(app.GetDocuments or []))
parts=sorted(glob.glob(os.path.join(NAT,"*.SLDPRT")))
parts=[p for p in parts if not os.path.basename(p).startswith("~$")]
print("parts:", len(parts)); [print("  ", os.path.basename(p)) for p in parts]
conflicts=[p for p in parts if os.path.exists(os.path.join(DEST,os.path.basename(p)))]+([os.path.join(SRC,"염수주입라인.SLDASM")] if os.path.exists(os.path.join(DEST,"염수주입라인.SLDASM")) else [])
print("conflicts at dest:", [os.path.basename(c) for c in conflicts])
if conflicts: sys.exit("stop: conflicts")
frm=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, parts)
to =VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(DEST,os.path.basename(p)) for p in parts])
r=app.CopyDocument(os.path.join(SRC,"염수주입라인.SLDASM"), os.path.join(DEST,"염수주입라인.SLDASM"), frm, to, 0)
print("CopyDocument ->", r)
for p in parts+[os.path.join(SRC,"염수주입라인.SLDASM")]:
    t=os.path.join(DEST,os.path.basename(p)); print("  dest", os.path.basename(t), "exists", os.path.exists(t), os.path.getsize(t) if os.path.exists(t) else 0)
