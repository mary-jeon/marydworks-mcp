# G3e(정렬 완료) → 고아 스케치 정리, 양단 트림(면간 100), 포트 나사부 컷, 속성, 저장. 검증은 바디 상자(GetBodyBox)로.
import os, sys, math, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
OUT=os.path.join(Z,"G3e_valve_3PC_32A_TAESUNG_S3_alt_Tameson_BL2SA3-114.SLDPRT")
mm=lambda v:v/1000.0; DATE="2026-09-15"; L_TS=100.0; ENG=15.0; R_BORE=21.4
stop=watchdog(); app=connect(); d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def bodies(): return list(pv(d,"GetBodies2",0,True) or [])
def bbox():
    bs=bodies(); assert len(bs)==1, len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def feat_names():
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
def delete(n,kind="BODYFEATURE"):
    d.ClearSelection2(True); d.Extension.SelectByID2(n,kind,0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
def orphan_sketches():
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
def clean():
    for n in orphan_sketches():
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3
def sketch_circle(r):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(r)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n in feat_names() if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def offset_cut(r,start,depth,name,check):
    for dirflag in (True,False):
        for flip in (False,True):
            sk=sketch_circle(r)
            f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(start),flip,False); d.EditRebuild3
            if f is None: delete(sk,"SKETCH"); continue
            f.Name=name
            ok=False
            try: ok=check()
            except AssertionError: ok=False
            if ok: return True
            delete(name)
    return False
def zplanes():
    out=[]
    for fc in bodies()[0].GetFaces():
        s=fc.GetSurface
        if s.IsPlane:
            n=pv(fc,"Normal")
            if abs(abs(n[2])-1)<1e-3: fb=[round(v*1000,2) for v in fc.GetBox]; out.append(round(fb[2],2))
    return out
def zmax_exact(): return max(zplanes())
def zmin_exact(): return min(zplanes())
def r_faces():
    out=[]
    for fc in bodies()[0].GetFaces():
        s=fc.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000-R_BORE)<0.05: fb=[round(v*1000,2) for v in fc.GetBox]; out.append((fb[2],fb[5]))
    return out
clean(); print("feats",[n for n in feat_names() if n.startswith(("정렬","트림","포트","스케치"))]); b0=bbox(); print("body box",b0)
L0=b0[5]-b0[2]; trim=L0/2-L_TS/2; print("L0",round(L0,2),"trim each",round(trim,2))
if "트림_상" not in feat_names():
    assert offset_cut(60.0,L_TS/2,trim+1.0,"트림_상",lambda: len(bodies())==1 and abs(zmax_exact()-L_TS/2)<0.05 and zmin_exact()<-L_TS/2-1), "trim top"
if "트림_하" not in feat_names():
    assert offset_cut(60.0,L_TS/2,trim+1.0,"트림_하",lambda: len(bodies())==1 and abs(zmin_exact()+L_TS/2)<0.05 and abs(zmax_exact()-L_TS/2)<0.05), "trim bot"
print("trimmed z planes",zmin_exact(),zmax_exact())
if "포트컷_상" not in feat_names():
    assert offset_cut(R_BORE,L_TS/2-ENG,ENG,"포트컷_상",lambda: any(abs(a-(L_TS/2-ENG))<0.3 and abs(b-L_TS/2)<0.3 for a,b in r_faces()) and len(bodies())==1), "port top"
if "포트컷_하" not in feat_names():
    assert offset_cut(R_BORE,L_TS/2-ENG,ENG,"포트컷_하",lambda: any(abs(a+L_TS/2)<0.3 and abs(b+(L_TS/2-ENG))<0.3 for a,b in r_faces()) and len(bodies())==1), "port bot"
clean(); print("final body box",bbox(),"orphans",orphan_sketches(),"ww",ww(d),"feats",[n for n in feat_names() if n.startswith(("정렬","트림","포트"))])
cp=d.Extension.CustomPropertyManager("")
for k,v in {"TITLE":"BALL VALVE 3PC 32A (태성자동밸브 S3, 형상 대용: Tameson BL2SA3-114 STEP 면간 100 트림)",
 "SPEC":"태성자동밸브 3PC 나사식 볼밸브 32A(1-1/4) 자동장착형(S3): 면간 L 100·보어 Ø32·Body/Ball SUS304(SUS316)·Seat PTFE·10 kgf/cm²·−10~90 ℃(카탈로그 2013-36 p.12·도면 A110117-01-04·2012판 p.17 일치). 단품 형번·ISO 패드·스템 각형·나사(PT/PF)·토크 원문 미기재 → 태성 문의. 형상 대용 Tameson BL2SA3-114(G1-1/4, DN32, L110, F04/F05/F07-VK11, 패드 63, 2.1 kg)를 양단 트림해 면간 100으로 맞춤. 포트컷 = 나사부 표현(Ø42.8×15).",
 "Material":"STS316","QT'Y":"1","DATE":DATE,
 "REMARK":"로봇과 동일 제조사(태성) 지정(사용자 09-14). 대용 STEP: tameson.com bl2sa3-114.zip. 액추에이터 코사 KE005(□14 표준/□11 옵션) — 태성 스템 확정 전 옵션 미정."}.items():
    if cp.Get(k): cp.Set2(k,v)
    else: cp.Add3(k,30,v,1)
try: d.SetMaterialPropertyName2("","이텍","STS 316")
except Exception as ex: print("mat exc",ex)
e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value)
json.dump({"box":bbox()},open(os.path.join(VER,"valve114_0915.json"),"w"),indent=1)
stop.set(); print("done")
