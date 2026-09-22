# 2026-09-10: 저장된 KE002 자식 파트 13개로 새 어셈블리를 만들어(변환 그대로) 「파트로 저장」 재시도 → 솔리드가 나오면 B4c
import sys, os, json, pythoncom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
rec=json.load(open(os.path.join(VER,"ke002_children_0910.json"),encoding="utf-8"))
OUT=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT")
TMPASM=os.path.join(os.path.dirname(rec[0]["file"]),"KE002_compose.SLDASM")
stop=watchdog(); app=connect()
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle)
if os.path.exists(OUT): os.remove(OUT); print("removed surface-only B4c")
atmpl=app.GetUserPreferenceStringValue(9)   # swDefaultTemplateAssembly
a=app.NewDocument(atmpl,0,0,0); print("new asm",a.GetTitle)
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
for r in rec:
    p=r["file"]
    if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(a.GetTitle,False,0,I4())
    c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0)
    if c is None: raise SystemExit("AddComponent failed "+p)
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,r["R"],r["t_mm"]); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
a.ForceRebuild3(False)
cm=a.ConfigurationManager; comps=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"))
bad=[(c.Name2,xform(c)["t_mm"]) for c,r in zip(comps,rec) if any(abs(p-q)>0.05 for p,q in zip(xform(c)["t_mm"],r["t_mm"]))]
print("components",len(comps),"transform mismatches",bad)
e=I4(); w=I4(); print("save tmp asm",a.Extension.SaveAs(TMPASM,0,1,NOD,e,w),e.value,w.value)
ext=a.Extension; opt=ext.GetAdvancedSaveAsOptions(1); opt.OverrideDefaults=True; opt.GeometryToSave=1; opt.PreserveGeometryReferences=False
e=I4(); w=I4(); ok=ext.SaveAs3(OUT,0,1,NOD,opt,e,w); print("SaveAs3 part",ok,e.value,w.value)
app.CloseDoc(a.GetTitle)
for r in rec:
    x=app.GetOpenDocumentByName(r["file"])
    if x is not None: app.CloseDoc(x.GetTitle)
d=open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
so=list(pv(d,"GetBodies2",0,False) or []); sh=list(pv(d,"GetBodies2",1,False) or [])
print("result solid",len(so),"sheet",len(sh))
for b in so: print("  ",pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")],round(pv(b,"GetMassProperties",0)[3]*1e9))
stop.set()
