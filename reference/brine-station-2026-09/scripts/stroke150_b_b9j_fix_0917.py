# 2026-09-17: B9j 대용 형상 보정 — 슬롯 깊이(러그 여유), 핀홀 양방향(Sd=False) 재컷. 평면 코드.
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
RL_NEW=274.0; STROKE=150.0; TIP=-(RL_NEW+10.0)
P=Zp("B9j_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT")
app=connect(); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc; print("doc",d.GetTitle)
def feats():
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def bodies(): return list(pv(d,"GetBodies2",0,True) or [])
def bboxes(): return [[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies()]
def vol(): return d.Extension.CreateMassProperty.Volume*1e9
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    d.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def last_sketch(): return [n for n,t in feats() if t=="ProfileFeature"][-1]
def hole_cyl_count():
    n=0
    for b in bodies():
        for fc in list(pv(b,"GetFaces") or []):
            sf=fc.GetSurface; isc=sf.IsCylinder
            if callable(isc): isc=isc()
            if isc:
                pr=sf.CylinderParams
                if abs(pr[6]*1000-4.0)<0.01: n+=1
    return n
def setdim(fname,dname,val):
    f=d.FeatureByName(fname); assert f is not None,fname; dim=f.Parameter(dname); assert dim is not None,(fname,dname)
    before=dim.SystemValue*1000; r=dim.SetSystemValue3(mm(val),2,None); d.ForceRebuild3(False); print(f"  {dname}@{fname} {before:.1f} -> {dim.SystemValue*1000:.1f} (ret {r})")
d.ShowConfiguration2("상승"); d.ForceRebuild3(False); print("before",bboxes(),"Ø8 faces",hole_cyl_count())
v0=vol()
# 1) 후단 슬롯 15 → 19 (러그 J8g 하단 part z −7 → 슬롯 바닥 −8)
setdim("후단슬롯_6","D1",19.0)
# 2) 전단 요크 22 → 26 (z −284 ~ −258), 전단 슬롯 14 → 20 (→ −264; 러그 J9f 상단 −265)
setdim("전단요크","D1",26.0); setdim("전단슬롯_6","D1",20.0)
bb=bboxes(); print("after dims",bb,"ww",ww()); assert not ww()
assert any(abs(b[2]-TIP)<0.06 and abs(b[5]+16.0)<0.06 for b in bb), bb
# 3) 핀홀 양방향 재컷: 기존 단방향 컷 삭제(+스케치) 후 Sd=False 로 재생성
for nm in ("전단핀홀_Ø8","후단핀홀_Ø8"):
    f=d.FeatureByName(nm)
    if f is not None: d.ClearSelection2(True); f.Select2(False,0); d.EditDelete(); d.ForceRebuild3(False); print("  deleted",nm)
# 고아 스케치 정리
def orphans():
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
for n in orphans():
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); print("  orphan deleted",n)
d.ForceRebuild3(False); print("holes removed: Ø8 faces",hole_cyl_count())
def pin_cut_both(yc,name):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,mm(yc),0,mm(4.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch(); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0); n0=hole_cyl_count()
    c=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.ForceRebuild3(False)
    if c is None:
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); d.ForceRebuild3(False)
        return None,0
    c.Name=name; return c,hole_cyl_count()-n0
c,dn=pin_cut_both(0.0,"후단핀홀_Ø8"); print("  rear cut",c is not None,"new Ø8 faces",dn); assert c and dn>=2
ok=False
for yc in (-RL_NEW,RL_NEW):
    c,dn=pin_cut_both(yc,"전단핀홀_Ø8"); print("  front cut yc",yc,c is not None,"new Ø8 faces",dn)
    if c is not None and dn>=2: ok=True; break
    if c is not None: c.Select2(False,0); d.EditDelete(); d.ForceRebuild3(False)
assert ok
for n in orphans():
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
d.ForceRebuild3(False); assert not orphans()
rep={}
for cfg in ("상승","하강","기본"):
    d.ShowConfiguration2(cfg); d.ForceRebuild3(False); rep[cfg]=bboxes(); print(f"[{cfg}]",rep[cfg],"ww",ww()); assert not ww() and len(rep[cfg])==2
assert any(abs(b[2]-(TIP-STROKE))<0.1 for b in rep["하강"]), rep["하강"]
d.ShowConfiguration2("상승"); d.ForceRebuild3(False)
e=I4(); w=I4(); assert d.Save3(1,e,w); print("saved B9j",e.value,w.value)
json.dump(rep,open(os.path.join(DESK,"_검증","stroke150b_b9j_fix_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
app.ActivateDoc3(ASM,False,0,I4()); print("DONE fix")
