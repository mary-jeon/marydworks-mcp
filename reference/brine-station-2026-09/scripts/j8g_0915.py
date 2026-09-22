# J8e(고정 러그 PL6, 치수 피처 미발견) → J8g PL5.8 40×23 핀 Ø8 @상면 아래 16 신규 생성·교체·저장·닫기
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-15"
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
P=Zp("J8g_lug_PL5.8_40x23_pin16.SLDPRT")
if not os.path.exists(P):
    d=app.NewDocument(tmpl,0,0,0)
    d.ClearSelection2(True); assert d.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCornerRectangle(mm(-20),0,0,mm(20),mm(23),0); sm.CreateCircleByRadius(0,mm(16),0,mm(4.0)); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(5.8),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f; f.Name="러그_t5.8"
    bx=[round(v*1000,2) for v in pv(list(pv(d,"GetBodies2",0,True))[0],"GetBodyBox")]; print("J8g box",bx)
    cp=d.Extension.CustomPropertyManager("")
    for k,v in {"TITLE":"LUG PL5.8 40x23 (고정판 밑, TA2 후단 클레비스 핀 @16)","SPEC":"PL 6T STS304 → 두께 5.8 ±0.05 기계가공(TA2 후단 CNC 슬롯 6.0 삽입 틈 0.15~0.25), 40(x)×23(z), 핀 구멍 Ø8 H7(+0.015/0) 중심 판 밑면 아래 16. 고정판 J1c 밑면 (85,0)에 필릿 용접.",
      "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. J8e(PL6, 두께 치수 편집 불가)를 공차 반영본으로 대체.","TOLERANCE":"두께 5.8 ±0.05(f급) — TA2 슬롯 6.0. 핀 구멍 Ø8 H7 — 핀 SHCCG8-22.8 g6 틈 0.005~0.029. 일반공차 KS B ISO 2768-1 m(JIS B 0405 m 원문)."}.items(): cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍","STS 304")
    except Exception: pass
    e=I4(); w=I4(); ok=d.Extension.SaveAs(P,0,1,NOD,e,w); print("saved J8g",ok); app.CloseDoc(d.GetTitle)
    json.dump({"box":bx},open(r"<PROJECT_DIR>\_검증\j8g_build_0915.json","w"))
bx=json.load(open(r"<PROJECT_DIR>\_검증\j8g_build_0915.json"))["box"]
zsign=1 if bx[5]>1 else -1; ysign=1 if bx[4]>1 else -1
# 라인: 판 밑(−10)에서 아래(−z)로 23. 파트 z 범위가 +면 뒤집기(y·z 부호 반전 → 행렬식 +1)
R=[[1,0,0],[0,1,0],[0,0,1]] if zsign<0 else [[1,0,0],[0,-1,0],[0,0,-1]]
yoff=-2.9 if (ysign*R[1][1])>0 else 2.9
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); old=[n for n in cc if n.startswith("J8e_")]
if old:
    if app.GetOpenDocumentByName(P) is None: open_doc(app,P,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    a.ClearSelection2(True); cc[old[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J8e→J8g",ok)
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,c in cc.items():
        if n.startswith("J8g_"):
            sup=c.GetSuppression2
            if sup!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
            a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
            arr=list(R[0])+list(R[1])+list(R[2])+[0.085,yoff/1000,-0.010,1.0,0,0,0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
            a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
            if sup!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps(); print(f"[{cfg}] ww {ww(a)}",[box(cc[n]) for n in cc if n.startswith("J8g_") and cc[n].GetSuppression2==2])
a.ShowConfiguration2("상승"); a.EditRebuild3
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
x=app.GetOpenDocumentByName(P)
if x is not None: app.CloseDoc(x.GetTitle)
stop.set(); print("done")
