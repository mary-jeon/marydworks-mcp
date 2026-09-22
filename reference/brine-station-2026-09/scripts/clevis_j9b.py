# J9b: 로드 클레비스 내측 30→32 (LA25 로드 아이 측면 보스 Ø15가 각 1.73 돌출 → 간섭 40.5 mm³×2 해소). 나머지 치수 동일(t6, H40, 폭 60, 핀홀 Ø10.5 @25).
# 어셈블리에서 J9-1/-2를 J9b로 교체(구성별 억제 복제). 메모리 작업만.
import os, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
tmpl=app.GetUserPreferenceStringValue(8)
T=6.0; G=32.0; H=40.0; W=G+2*T   # 44
NAME="J9b_rod_clevis_t6_44x40x60.SLDPRT"; P=os.path.join(Z,NAME)
def nfaces(d): return sum(len(b.GetFaces()) for b in (d.GetBodies2(0,True) or []))
if not os.path.exists(P):
    d=app.NewDocument(tmpl,0,0,0)
    d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True)
    pts=[(0,0),(W,0),(W,H),(W-T,H),(W-T,T),(T,T),(T,H),(0,H),(0,0)]
    for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(60.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    d.EditRebuild3; print("clevis box",[round(v*1000,1) for v in d.GetPartBox(True)])
    # 핀홀: 우측면 스케치 (sx,sy)->(Y=sy, Z=-sx); 관통 X. 위치 z_model=-30(폭 중앙), y=25
    d.Extension.SelectByID2("우측면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Right Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.CreateCircleByRadius(mm(30.0),mm(25.0),0.0,mm(5.25)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    d.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,0,NOD,0); n0=nfaces(d)
    f=d.FeatureManager.FeatureCut3(True,False,True,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
    n1=nfaces(d); print("pin hole faces",n0,"->",n1)
    if not f or n1<=n0: raise SystemExit("pin hole failed")
    cpm=d.Extension.CustomPropertyManager("")
    for k,v in {"TITLE":"LA25 ROD CLEVIS (절곡 1장)","SPEC":"STS304 t6 절곡 U, 내측 32(로드 아이 27 + 측면 보스 Ø15 각 1.73 실측 → 여유 0.77/측), 높이 40, 폭 60, 핀홀 Ø10.5 @25 양측 관통","Material":"STS304","QT'Y":"1","DATE":"2026-09-08","REMARK":"이동판 J5d 상면 (-70,0) 용접. 2026-09-08 J9(내측 30) 간섭 40.5 mm³×2 해소용"}.items(): cpm.Add3(k,30,v,1)
    d.SetMaterialPropertyName2("","이텍","STS 304"); d.EditRebuild3
    e=I4(); wn=I4(); print("saved",d.Extension.SaveAs(P,0,1,NOD,e,wn),e.value,wn.value)
else: print("exists",NAME)
# ---- swap in assembly
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager; CFGS=list(asm.GetConfigurationNames)
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return {c.Name2:c for c in pv(root(),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
R_UH_J=[[0,1,0],[0,0,1],[1,0,0]]
old_state={}
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps(); old_state[cfg]={k:cc[k].GetSuppression2 for k in cc if k.startswith("J9_")}
asm.ShowConfiguration2("상승"); asm.EditRebuild3
for d_ in (app.GetDocuments or []):
    pass
e=I4(); wn=I4(); app.OpenDoc6(P,1,1,"",e,wn); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
new={}
for old,zp in (("J9_rod_clevis_t6_42x40x60-1",-380.0),("J9_rod_clevis_t6_42x40x60-2",-520.0)):
    t=(-40.0,-W/2,zp)
    c=asm.AddComponent5(P,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    sel([c.Name2]); asm.UnfixComponent(); asm.ClearSelection2(True); set_T(c,R_UH_J,t); new[c.Name2]=old
asm.EditRebuild3
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    for n,old in new.items():
        sel([n]); pv(asm,'EditSuppress2') if old_state[cfg][old]==0 else pv(asm,'EditUnsuppress2'); asm.ClearSelection2(True)
    asm.EditRebuild3; print(f"[{cfg}]",{n:comps()[n].GetSuppression2 for n in new},"boxes",{n:box(comps()[n]) for n in new if comps()[n].GetSuppression2==2})
asm.ShowConfiguration2("상승"); asm.EditRebuild3
sel(list(new.values())); print("delete J9:",asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True); asm.EditRebuild3
print("done; dirty",asm.GetSaveFlag)
stop.set()
