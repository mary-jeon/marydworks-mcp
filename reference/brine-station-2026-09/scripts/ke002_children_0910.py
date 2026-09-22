# 2026-09-10: KE002 임포트 어셈블리의 자식 파트 13개를 임시 폴더에 SaveAs + 각 컴포넌트 Transform2 기록 (파트 합성 InsertPart3 경로 준비)
#  + 시스템 옵션 「어셈블리를 파트로 저장」 정수 프리퍼런스 탐색·설정 후 SaveAs3 재시도
import sys, os, json, pythoncom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
from swdialog import template_clicker
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
TMP=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_3D다운로드","KE002_children"); os.makedirs(TMP,exist_ok=True)
STEP=r"<PROJECT_DIR>\_3D다운로드\B4b_KE002-F35C11-DC.step"
OUT=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT")
# ---- 정수 프리퍼런스 탐색
tlb=pythoncom.LoadTypeLib(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\swconst.tlb"); prefs=[]
for i in range(tlb.GetTypeInfoCount()):
    if tlb.GetDocumentation(i)[0]=="swUserPreferenceIntegerValue_e":
        ti=tlb.GetTypeInfo(i); ta=ti.GetTypeAttr()
        for j in range(ta.cVars):
            vd=ti.GetVarDesc(j); nm=ti.GetNames(vd.memid)[0]
            if any(k in nm.lower() for k in ("asmaspart","assemblyaspart","saveasm","aspart")): prefs.append((nm,vd.value))
print("int prefs",prefs)
stop=watchdog(); app=connect()
for nm,v in prefs: print("  ",nm,v,"=",app.GetUserPreferenceIntegerValue(v))
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle)
if os.path.exists(OUT): os.remove(OUT); print("removed surface-only B4c")
already=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.startswith("B4b_KE002") and x.GetType==2]
if already: d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); print("reuse open import asm")
else:
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set()
d=app.ActiveDoc; title=d.GetTitle; print("imported",title)
cm=d.ConfigurationManager; comps=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"))
rec=[]
for k,c in enumerate(comps):
    md=c.GetModelDoc2; base=os.path.basename(c.GetPathName)
    safe=f"c{k:02d}_"+"".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in base)
    p=os.path.join(TMP,safe)
    if not os.path.exists(p):
        app.ActivateDoc3(md.GetTitle,False,0,I4()); e=I4(); w=I4(); ok=md.Extension.SaveAs(p,0,1,NOD,e,w)
    else: ok="exists"
    xf=xform(c); bb=box(c)
    rec.append({"name":c.Name2,"file":p,"saveas":ok,"R":xf["R"],"t_mm":xf["t_mm"],"box":bb})
    print(f"  {k:2d} {c.Name2[:40]:40s} save {ok} t {xf['t_mm']} box {bb}")
app.ActivateDoc3(title,False,0,I4()); d=app.ActiveDoc
json.dump(rec,open(os.path.join(VER,"ke002_children_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
# ---- 시스템 옵션 설정 후 재시도
for nm,v in prefs:
    if "preserve" in nm.lower(): continue
    try: print("set",nm,"->1",app.SetUserPreferenceIntegerValue(v,1),"now",app.GetUserPreferenceIntegerValue(v))
    except Exception as ex: print("set",nm,"exc",ex)
ext=d.Extension; opt=ext.GetAdvancedSaveAsOptions(1); opt.OverrideDefaults=True; opt.GeometryToSave=1
e=I4(); w=I4(); ok=ext.SaveAs3(OUT,0,1,NOD,opt,e,w); print("SaveAs3",ok,e.value,w.value)
kids=[os.path.basename(c.GetPathName) for c in comps]
app.CloseDoc(title)
for p in kids:
    for x in list(pv(app,"GetDocuments") or []):
        if os.path.basename(x.GetPathName)==p: app.CloseDoc(x.GetTitle)
for x in list(pv(app,"GetDocuments") or []):
    if x.GetPathName.startswith(TMP): app.CloseDoc(x.GetTitle)
d=open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
print("result solid",len(list(pv(d,"GetBodies2",0,False) or [])),"sheet",len(list(pv(d,"GetBodies2",1,False) or [])))
print("children files",len(os.listdir(TMP)))
stop.set()
