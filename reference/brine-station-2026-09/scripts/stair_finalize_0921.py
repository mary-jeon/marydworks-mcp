# 2026-09-21 stair shorten finalize: save S20000MU0 -> open S00000MU0 READ-ONLY in this instance -> stair vs others interference, world extents (no save of S00000)
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n); rep={}
app=connect()
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
A=Zp("S20000MU0.SLDASM"); a=app.GetOpenDocumentByName(A); app.ActivateDoc3(A,False,0,I4()); a=app.ActiveDoc; a.ForceRebuild3(False); print("S20000 ww",ww(a))
if a.GetSaveFlag:
    e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved S20000MU0",e.value,w.value)
for x in list(pv(app,"GetDocuments") or []):
    try:
        if x.GetType==1 and x.Visible: app.CloseDoc(x.GetTitle)
    except Exception: pass
PS=Zp("S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PS) or open_doc(app,PS,2,True); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
print("S00000 cfg",scm.ActiveConfiguration.Name,"readonly",s.IsOpenedReadOnly); s.ForceRebuild3(False); print("S00000 ww",ww(s)[:5])
root=scm.ActiveConfiguration.GetRootComponent3(True); top=[c for c in pv(root,"GetChildren") if c.GetSuppression2==2]
stair=[c for c in top if c.Name2.startswith("S20000")][0]; others=[c for c in top if not c.Name2.startswith("S20000")]
kids=[c for c in (pv(stair,"GetChildren") or []) if c.GetSuppression2==2]
print("stair kids",len(kids),"others",len(others))
s.ClearSelection2(True)
for c in kids+others: c.Select4(True,NOD,False)
idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
ext=[r for r in rows if not all(x.startswith("S200") for x in r[0])]
print("stair vs external interferences",len(ext),ext[:10]); rep["station_ext"]=ext
wb={}
for c in kids:
    b=box(c)
    if b: wb[c.Name2.split("/")[-1]]=b
xmax=max(b[3] for b in wb.values()); zmin=min(b[2] for b in wb.values()); print("stair world x max (ground 1109)",xmax,"z min",zmin)
fr=[c for c in top if c.Name2.startswith("S10000")][0]; fb=box(fr); print("frame S10000 box",fb)
for n,b in sorted(wb.items()):
    if n.startswith(("S20014","S20019")): print("  ",n,b)
rep["stair_world"]={"xmax":xmax,"zmin":zmin,"frame_box":fb,"boxes":wb}
json.dump(rep,open(os.path.join(DESK,"_검증","stair_finalize_0921.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE")
