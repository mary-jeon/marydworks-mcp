import sys, os, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
NAT=r"<PROJECT_DIR>\_native"
# close temp re-import doc
for d in list(app.GetDocuments):
    try:
        if d.GetTitle.startswith("_tmp_LA25"): app.CloseDoc(d.GetTitle); print("closed temp doc")
    except Exception: pass
xb=os.path.join(NAT,"_tmp_LA25.x_b")
if os.path.exists(xb): os.remove(xb); print("removed temp x_b")
d=[x for x in app.GetDocuments if x.GetTitle.startswith("B9_LINAK")][0]
app.ActivateDoc3(d.GetPathName,False,0,I4())
def faults():
    b=(d.GetBodies2(0,True) or [])[0]; fe=b.Check3
    try: return fe.Count
    except Exception: return "?"
def feat_err():
    f=d.FirstFeature
    while f is not None:
        if f.GetTypeName2=="BaseBody": return f.GetErrorCode
        f=f.GetNextFeature
print("before: faults", faults(), "feature err", feat_err())
r=d.ImportDiagnosis(True, False, True, 0); print("ImportDiagnosis(CloseAllGaps, FixFaces) ->", r)
d.ForceRebuild3(False)
print("after : faults", faults(), "feature err", feat_err(), "solid bodies", len(d.GetBodies2(0,True) or []))
if faults() not in (0,"?"):
    r2=d.ImportDiagnosis(True, True, True, 0); d.ForceRebuild3(False); print("2nd pass with RemoveFaces ->", r2, "faults", faults(), "feature err", feat_err())
print("box", [round(v*1000,2) for v in d.GetPartBox(True)])
e=I4(); wn=I4(); print("save", d.Save3(1,e,wn), e.value, wn.value)
