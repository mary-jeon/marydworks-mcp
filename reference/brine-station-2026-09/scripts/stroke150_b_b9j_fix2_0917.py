# 2026-09-17: B9j 보정 2 — 요크 구간(z −284~−258)에서 로드 Ø20의 |y|>8.8 살 제거(핀 머리 간섭)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
TIP=-284.0
P=Zp("B9j_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT")
app=connect(); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
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
def sel_face_at(z,pt):
    d.ClearSelection2(True)
    for b in bodies():
        for fc in list(pv(b,"GetFaces") or []):
            sf=fc.GetSurface; isp=sf.IsPlane
            if callable(isp): isp=isp()
            if not isp: continue
            gb=fc.GetBox; gb=gb() if callable(gb) else gb; bx=[v*1000 for v in gb]
            if abs(bx[2]-z)>0.05 or abs(bx[5]-z)>0.05: continue
            if bx[0]-0.01<=pt[0]<=bx[3]+0.01 and bx[1]-0.01<=pt[1]<=bx[4]+0.01:
                sd=d.SelectionManager.CreateSelectData
                if fc.Select4(False,sd) and d.SelectionManager.GetSelectedObjectCount2(-1)==1: return True
    return False
d.ShowConfiguration2("상승"); d.ForceRebuild3(False); print("before",bboxes())
if d.FeatureByName("요크구간_로드트림") is None:
    assert sel_face_at(TIP,(11,7)),"tip face"
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    sm.CreateCornerRectangle(mm(-13),mm(8.8),0,mm(13),mm(12),0); sm.CreateCornerRectangle(mm(-13),mm(-12),0,mm(13),mm(-8.8),0)
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch(); v0=vol(); c=None
    for dirn in (False,True):
        d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
        c=d.FeatureManager.FeatureCut4(True,False,dirn,0,0,mm(26.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.ForceRebuild3(False)
        dv=(v0-vol()) if c is not None else None; bb=bboxes(); print("trim dirn",dirn,"dv",dv,bb)
        if c is not None and 250<=dv<=550 and len(bb)==2 and not ww(): c.Name="요크구간_로드트림"; break
        if c is not None: c.Select2(False,0); d.EditDelete(); d.ForceRebuild3(False); c=None
    assert c is not None,"trim"
    # 요크 구간 y 폭 확인: z −284~−258 에서 바디 y 범위 ±8.8
    ymax=0
    for b in bodies():
        for fc in list(pv(b,"GetFaces") or []):
            gb=fc.GetBox; gb=gb() if callable(gb) else gb; bx=[v*1000 for v in gb]
            if bx[5]<=-258.05: ymax=max(ymax,abs(bx[1]),abs(bx[4]))
    print("yoke zone |y| max",round(ymax,2)); assert ymax<=8.85, ymax
rep={}
for cfg in ("상승","하강","기본"):
    d.ShowConfiguration2(cfg); d.ForceRebuild3(False); rep[cfg]=bboxes(); print(f"[{cfg}]",rep[cfg],"ww",ww()); assert not ww()
d.ShowConfiguration2("상승"); d.ForceRebuild3(False)
e=I4(); w=I4(); assert d.Save3(1,e,w); print("saved B9j",e.value,w.value)
app.ActivateDoc3(ASM,False,0,I4()); print("DONE fix2")
