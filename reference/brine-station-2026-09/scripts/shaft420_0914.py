# 2026-09-14: 가이드봉 PSSFAQ16-590 → 420 (J2c SaveAs J2d + 길이 컷), 어셈블리 전 인스턴스 교체, 라인 간섭·박스 확인, 저장
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
L_NEW=430.0   # 전장 = L420 + 나사 B10
P_OLD=Zp("J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT"); P_NEW=Zp("J2d_guide_shaft_MISUMI_PSSFAQ16-420-B10.SLDPRT")
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def delete(d,n,kind):
    d.ClearSelection2(True); d.Extension.SelectByID2(n,kind,0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
if not os.path.exists(P_NEW):
    d=act(P_OLD); e=I4(); w=I4(); ok=d.Extension.SaveAs(P_NEW,0,1,NOD,e,w); print("SaveAs J2d",ok,e.value); assert ok
d=act(P_NEW); bx=partbox(d); print("J2d box",bx)
if "길이_420_컷" not in feat_names(d):
    # 봉 축 = 파트 z(0~−590 로 가정, 박스로 확인). 정면(z0) 스케치 원 r9, 시작 오프셋 L_NEW, 깊이 200 → 하단 170 제거
    axis_z=abs(bx[2]+600)<0.5 and abs(bx[5])<0.5
    assert axis_z, ("shaft axis not z 0..-600",bx)
    done=False
    for dirflag in (True,False):
        for flip in (False,True):
            d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
            d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(9.0)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            sk=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
            f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(200.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(L_NEW),flip,False); d.EditRebuild3
            if f is None: delete(d,sk,"SKETCH"); continue
            f.Name="길이_420_컷"; b2=partbox(d); print("  try",dirflag,flip,"box",b2)
            if abs(b2[2]+L_NEW)<0.1 and abs(b2[5])<0.1 and len(pv(d,"GetBodies2",0,True))==1: done=True; break
            delete(d,"길이_420_컷","BODYFEATURE")
        if done: break
    assert done and not ww(d), "shaft cut"
    cp=d.Extension.CustomPropertyManager("")
    for k in ("TITLE","SPEC","REMARK"):
        s=cp.Get(k) or ""; s=s.replace("PSSFAQ16-590-B10","PSSFAQ16-420-B10").replace("L590","L420").replace("L 590","L 420").replace("590","420"); cp.Set2(k,s)
    sp_=cp.Get("SPEC") or ""
    if "길이 420" not in sp_: cp.Set2("SPEC",sp_+" | 길이 L420 + 나사 B10 = 전장 430(노즐판 홀더 하단 −412 아래 18, 승강 폐지로 590→420 단축, MISUMI 1 mm 단위 지정). 3D = 590 STEP에 길이 컷.")
    cp.Set2("DATE","2026-09-14")
    e=I4(); w=I4(); print("save J2d",d.Save3(1,e,w),e.value)
# ---- 어셈블리 교체
a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); olds=[n for n in cc if n.startswith("J2c_")]
if olds:
    if app.GetOpenDocumentByName(P_NEW) is None: open_doc(app,P_NEW,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P_NEW,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J2c→J2d",ok); assert ok
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
rep={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    bb=[box(c) for c in act_]; zmin=min(b[2] for b in bb); rows=interf(act_)
    sh=[(n,box(c)) for n,c in cc.items() if n.startswith("J2d_")]
    print(f"[{cfg}] ww {ww(a)} zmin {zmin} 간섭 {len(rows)} {rows[:8]} shafts {sh}"); rep[cfg]={"zmin":zmin,"interf":rows,"shafts":sh}
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); assert not any(r.startswith("J2c_") for r in refs); print("refs",refs)
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
json.dump(rep,open(r"<PROJECT_DIR>\_검증\shaft420_0914.json","w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("done")
