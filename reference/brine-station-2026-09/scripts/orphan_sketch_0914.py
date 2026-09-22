# 2026-09-14: 라인 참조 파트 + 오늘 생성 파트 전수 — 고아 스케치(최상위 ProfileFeature/3DProfileFeature, 피처 미흡수) 검사·삭제·저장(Station 폴더만)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n)
stop=watchdog(); app=connect()
a=app.GetOpenDocumentByName(ASM); refs=sorted({c.GetPathName for c in pv(a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren")})
today=[Zp(n) for n in os.listdir(Z) if n.endswith(".SLDPRT") and n.split("_")[0] in ("E50","N1","P1","P2","J19g","J5h","K6","J23c","G3d","B4d","G13d","H16c","J1c","J2c","J5e")]
targets=sorted(set(refs+today));
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def top_feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def orphan_sketches(d):
    feats=[]; f=pv(d,"FirstFeature")
    while f is not None: feats.append(f); f=pv(f,"GetNextFeature")
    parents=set()
    for f in feats:
        if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature"): continue
        for pf in (pv(f,"GetParents") or []):
            try: parents.add(pf.Name)
            except Exception: pass
        sf=pv(f,"GetFirstSubFeature")
        while sf is not None:
            try: parents.add(sf.Name)
            except Exception: pass
            sf=pv(sf,"GetNextSubFeature")
    return [f.Name for f in feats if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature") and f.Name not in parents]
DRY="--dry" in sys.argv
rep={}
for p in targets:
    if not p.lower().endswith(".sldprt"): continue
    if not p.lower().startswith(Z.lower()): print("skip(outside Station)",p); continue
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); app.ActivateDoc3(p,False,0,I4()); d=app.ActiveDoc
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    orph=orphan_sketches(d)
    bodies=len(pv(d,"GetBodies2",0,True) or []); v0=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in (pv(d,"GetBodies2",0,True) or []))
    deleted=[]
    if orph and not DRY:
        for n in orph:
            d.ClearSelection2(True)
            if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0):
                ok=d.Extension.DeleteSelection2(0); d.EditRebuild3; deleted.append((n,bool(ok)))
        d.ForceRebuild3(False)
        v1=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in (pv(d,"GetBodies2",0,True) or [])); b1=len(pv(d,"GetBodies2",0,True) or [])
        okgeom=(abs(v1-v0)<1 and b1==bodies and not ww(d))
        if okgeom:
            e=I4(); w=I4(); sv=d.Save3(1,e,w)
        else: sv="NOT SAVED (geometry changed or error)"
        rep[os.path.basename(p)]={"orphans":orph,"deleted":deleted,"vol_before":round(v0),"vol_after":round(v1),"bodies":[bodies,b1],"ww":ww(d),"saved":sv}
        print(f"{os.path.basename(p)[:52]:52s} orphans {orph} → deleted {deleted} vol {round(v0)}→{round(v1)} ww {ww(d)} saved {sv}")
    else:
        rep[os.path.basename(p)]={"orphans":orph,"bodies":bodies}
        print(f"{os.path.basename(p)[:52]:52s} orphans {orph}")
json.dump(rep,open(r"<PROJECT_DIR>\_검증\orphan_sketch_0914.json","w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("targets",len(targets),"dry" if DRY else "applied")
