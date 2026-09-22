# J9b 내측 32→36 (다리 ±18~24): LA25 외통 r14.5 외피 |y|≤16.5·아이 보스 13.1을 1.5 이상 비껴감. 파트 피처 재작성 + 어셈 2개 인스턴스 t.y=-24. 메모리만.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
T=6.0; G=36.0; H=40.0; W=G+2*T
P=os.path.join(Z,"J9b_rod_clevis_t6_44x40x60.SLDPRT")
d=app.GetOpenDocumentByName(P); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
# 기존 피처 전부 삭제(컷→보스 순, 흡수 스케치 포함)
for nm in ("컷-돌출1","보스-돌출1"):
    d.ClearSelection2(True); ok=d.Extension.SelectByID2(nm,"BODYFEATURE",0,0,0,False,0,NOD,0); print("del",nm,ok,d.Extension.DeleteSelection2(1))
d.ClearSelection2(True); d.EditRebuild3
d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0); d.SketchManager.InsertSketch(True)
pts=[(0,0),(W,0),(W,H),(W-T,H),(W-T,T),(T,T),(T,H),(0,H),(0,0)]
for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
skn=[f for f in ("스케치1","스케치2","스케치3")]
# 방금 만든 스케치 이름: 마지막 ProfileFeature
f=pv(d,"FirstFeature"); last=None
while f is not None:
    if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
    f=pv(f,"GetNextFeature")
d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
fe=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(60.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
d.EditRebuild3; print("box",[round(v*1000,1) for v in d.GetPartBox(True)])
d.Extension.SelectByID2("우측면","PLANE",0,0,0,False,0,NOD,0); d.SketchManager.InsertSketch(True)
d.SketchManager.CreateCircleByRadius(mm(30.0),mm(25.0),0.0,mm(5.25)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
f=pv(d,"FirstFeature"); last=None
while f is not None:
    if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
    f=pv(f,"GetNextFeature")
d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
n0=sum(len(b.GetFaces()) for b in (d.GetBodies2(0,True) or []))
fc=d.FeatureManager.FeatureCut3(True,False,True,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
n1=sum(len(b.GetFaces()) for b in (d.GetBodies2(0,True) or [])); print("pin hole faces",n0,"->",n1)
cpm=d.Extension.CustomPropertyManager("")
cpm.Add3("SPEC",30,"STS304 t6 절곡 U, 내측 36(LA25 외통 Ø29 외피 |y|16.5·아이 보스 13.1 → 여유 1.5), 높이 40, 폭 60, 핀홀 Ø10.5 @25 양측 관통",1)
cpm.Add3("REMARK",30,"이동판 J5d 상면 (-70,0) 용접. 2026-09-08: 내측 30→36 (간섭 40.5 mm³×2 해소). 파일명의 44는 구 치수 — 실제 폭 48",1)
d.EditRebuild3
# assembly: t.y = -W/2
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager; root=cm.ActiveConfiguration.GetRootComponent3(True)
R=[[0,1,0],[0,0,1],[1,0,0]]
for c in pv(root,"GetChildren"):
    if c.Name2.startswith("J9b_"):
        t=xform(c)["t_mm"]; arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,-W/2/1000,t[2]/1000,1.0,0,0,0]
        xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
asm.EditRebuild3
for c in pv(root,"GetChildren"):
    if c.Name2.startswith("J9b_"): print(c.Name2,"supp",c.GetSuppression2,"box",box(c))
stop.set()
