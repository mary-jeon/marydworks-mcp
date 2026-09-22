# 2026-09-17 계단 마무리: 고아 스케치 검사(새 파트 5) → S20000MU0·파트 저장 → 파트 창 닫기 → S00000MU0에서 계단 vs 나머지 간섭·지면 접촉·월드 범위
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n); rep={}
app=connect()
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def orphan_sketches(d):
    fl=[]; f=pv(d,"FirstFeature")
    while f is not None: fl.append(f); f=pv(f,"GetNextFeature")
    parents=set()
    for f in fl:
        if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature"): continue
        for pf in (pv(f,"GetParents") or []):
            try: parents.add(pf.Name)
            except Exception: pass
        sf=pv(f,"GetFirstSubFeature")
        while sf is not None:
            try: parents.add(sf.Name)
            except Exception: pass
            sf=pv(sf,"GetNextSubFeature")
    return [f.Name for f in fl if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature") and f.Name not in parents]
PARTS=["S20014MU0","S20015MU0","S20016MU0","S20017MU0","S20018MU0","S20019MU0"]
for n in PARTS:
    p=Zp(n+".SLDPRT"); d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); o=orphan_sketches(d); print(f"  orphan {n}: {o} ww {ww(d)} dirty {d.GetSaveFlag}"); assert not o
    if d.GetSaveFlag: e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved",n)
A=Zp("S20000MU0.SLDASM"); a=app.GetOpenDocumentByName(A); app.ActivateDoc3(A,False,0,I4()); a=app.ActiveDoc; a.ForceRebuild3(False); print("S20000 ww",ww(a))
e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved S20000MU0",e.value,w.value); rep["saved"]=PARTS+["S20000MU0.SLDASM"]
for x in list(pv(app,"GetDocuments") or []):
    try:
        if x.GetType==1: app.CloseDoc(x.GetTitle)
    except Exception: pass
print("part windows closed")
# 스테이션: 계단 하위 vs 나머지 최상위
PS=Zp("S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PS); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
s.ShowConfiguration2("기본"); s.ForceRebuild3(False); print("S00000 ww",ww(s)[:5])
root=scm.ActiveConfiguration.GetRootComponent3(True); top=[c for c in pv(root,"GetChildren") if c.GetSuppression2==2]
stair=[c for c in top if c.Name2.startswith("S20000")][0]; others=[c for c in top if not c.Name2.startswith("S20000")]
kids=[c for c in (pv(stair,"GetChildren") or []) if c.GetSuppression2==2]
print("stair kids",len(kids),"others",len(others))
s.ClearSelection2(True)
for c in kids+others: c.Select4(True,NOD,False)
idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
ext=[r for r in rows if not all(x.startswith("S200") for x in r[0])]
print("stair↔외부 간섭",len(ext),ext[:10]); rep["station_ext"]=ext
# 월드 범위·지면(x=1109) 접촉
wb={}
for c in kids:
    b=box(c)
    if b: wb[c.Name2.split("/")[-1]]=b
xmax=max(b[3] for b in wb.values()); zmin=min(b[2] for b in wb.values()); print("stair world x max(지면 1109)",xmax,"z min",zmin)
for n,b in sorted(wb.items()):
    if n.startswith(("S20014","S20019","S20015MU0-8","S20016MU0-9","S20017MU0-5","S20018")): print("  ",n,b)
rep["stair_world"]={"xmax":xmax,"zmin":zmin,"boxes":wb}
s.ShowConfiguration2("기본"); app.ActivateDoc3(ASM,False,0,I4())
json.dump(rep,open(os.path.join(DESK,"_검증","stair_finalize_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE")
