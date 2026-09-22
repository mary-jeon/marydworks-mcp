import os, sys, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0
OUT=os.path.join(Z,"B4e_actuator_KOSAPLUS_KE005-F357C14-DC.SLDPRT")
stop=watchdog(); app=connect(); d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
def pad_holes():
    holes=[]
    for b in list(pv(d,"GetBodies2",0,False) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder:
                p=s.CylinderParams; rr=p[6]*1000; fb=[v*1000 for v in fc.GetBox]
                if 2.0<=rr<=3.5 and abs(abs(p[5])-1)<1e-3 and fb[2]<3: holes.append((round(rr,2),round(p[0]*1000,2),round(p[1]*1000,2)))
    return sorted(set(holes))
h=pad_holes(); print("holes before",h)
xs=[x for r,x,y in h]; ys=[y for r,x,y in h]; cx=(min(xs)+max(xs))/2; cy=(min(ys)+max(ys))/2; print("pattern center",cx,cy)
d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
for b in list(pv(d,"GetBodies2",0,False) or []): b.Select2(True,sd)
mv=d.FeatureManager.InsertMoveCopyBody2(mm(-cx),mm(-cy),0,0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_스템중심"
h2=pad_holes(); print("holes after",[(r,x,y,round(math.hypot(x,y),1)) for r,x,y in h2])
pb=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("box",pb)
cp=d.Extension.CustomPropertyManager("")
for k,v in {"TITLE":"ELECTRIC ACTUATOR KOSAPLUS KE005 (24 VDC, ISO5211 F03/F05/F07 sq14)",
 "SPEC":"코사플러스 KE005 F357C14, 24 VDC(2 A), MAX 토크 50 N·m, 작동 13 s, ISO 5211 F03/F05/F07(M5/M6/M8 TAP DP12), 스템 □14 표준(옵션 □11 — Tameson 대용 밸브 VK11 기준, 태성 32A 스템 미확인), IP67, −20~+60 ℃, Duty 40 %, 질량 1.3 kg, 외형 99.1×123.1×126.4(데이터북 v5.4 p.3·p.4, 도면 KE005-0001 Ver.2). 선정: 코사 선정표 1-1/4\" 볼밸브 → KE005.",
 "Material":"미확인(카탈로그 미기재)","QT'Y":"1","DATE":"2026-09-15",
 "REMARK":"3D: kosaplus.com Drawing 게시판 KE005_F357C14.step(20파트 InsertPart3 합성, 패드면 z 0·스템축 = 패드 탭홀 패턴 중심). 로봇 밸브 KE002와 같은 제조사. 밸브 토크 미확인이라 여유율 미기재."}.items():
    if cp.Get(k): cp.Set2(k,v)
    else: cp.Add3(k,30,v,1)
e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value); stop.set()
