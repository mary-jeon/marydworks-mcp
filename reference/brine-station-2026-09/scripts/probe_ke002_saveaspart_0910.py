# 2026-09-10: KE002 STEP 임포트 자식 파트가 솔리드인지, 「어셈블리를 파트로 저장」 옵션이 왜 곡면만 남기는지 조사
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
from swdialog import template_clicker
stop=watchdog(); app=connect()
STEP=r"<PROJECT_DIR>\_3D다운로드\B4b_KE002-F35C11-DC.step"
OUT=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT")
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle)
if os.path.exists(OUT): os.remove(OUT); print("removed surface-only B4c")
already=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.startswith("B4b_KE002") and x.GetType==2]
if already: d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); print("reuse open import asm")
else:
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set()
d=app.ActiveDoc; title=d.GetTitle; print("imported",title,d.GetType)
cm=d.ConfigurationManager; comps=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"))
for c in comps:
    md=c.GetModelDoc2
    if md is None: print("  ",c.Name2[:40],"no doc"); continue
    so=len(list(pv(md,"GetBodies2",0,False) or [])); sh=len(list(pv(md,"GetBodies2",1,False) or []))
    print("  ",c.Name2[:44],"solid",so,"sheet",sh)
ext=d.Extension; opt=ext.GetAdvancedSaveAsOptions(1)
print("opt type",type(opt))
opt.OverrideDefaults=True          # 시스템 옵션(기본: 외부 면만) 대신 아래 값 사용
opt.GeometryToSave=1               # swSaveAsmAsPart_AllComponents
opt.PreserveGeometryReferences=False
print("set OverrideDefaults/GeometryToSave=1")
e=I4(); w=I4(); ok=ext.SaveAs3(OUT,0,1,NOD,opt,e,w); print("SaveAs3",ok,e.value,w.value)
kids=[os.path.basename(c.GetPathName) for c in comps]
app.CloseDoc(title)
for p in kids:
    for x in list(pv(app,"GetDocuments") or []):
        if os.path.basename(x.GetPathName)==p: app.CloseDoc(x.GetTitle)
d=open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
print("result solid",len(list(pv(d,"GetBodies2",0,False) or [])),"sheet",len(list(pv(d,"GetBodies2",1,False) or [])))
stop.set()
