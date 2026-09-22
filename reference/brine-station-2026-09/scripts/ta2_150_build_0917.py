# 2026-09-17: TraceParts TA2-2H-150274-5511-010-1 STEP → 같은 규약(후단 핀 원점, 축 −Z, 핀 축 Y, 모터 +X) → 구성 상승/하강(로드 −150) → B9k 저장·닫기 (ta2_85_build_0915 기반)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from scipy.spatial.transform import Rotation
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
from swdialog import template_clicker
BASE=r"<PROJECT_DIR>"; VER=os.path.join(BASE,"_검증")
STEP=os.path.join(BASE,r"_원문\32A\timotion\actuator_ta2-2h-150274-5511-010-1_-_hubst0.stp")
OUT=os.path.join(Z,"B9k_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT"); assert not os.path.exists(OUT), OUT
STROKE=150.0; RL=274.0; mm=lambda v:v/1000.0
stop=watchdog(); app=connect()
already=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.startswith("actuator_ta2-2h-150274")]
if already: d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); print("reuse open doc")
else:
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); print("LoadFile4 err",e.value)
d=app.ActiveDoc; print("doc",d.GetTitle,"type",d.GetType); assert d.GetType==1, "expected part"
def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
def sel_bodies(bs):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
    for b in bs: b.Select2(True,sd)
AXI=5  # STEP 좌표 핀축 Z(index 5); 정렬 후 Y(index 4)
def holes_raw(bs):
    out=[]
    for b in bs:
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder:
                p=s.CylinderParams; r=p[6]*1000
                if abs(r-4.0)<0.05 and abs(p[AXI])>0.99: out.append(([round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)],[round(p[3],3),round(p[4],3),round(p[5],3)],[round(v*1000,1) for v in fc.GetBox]))
    return out
bs=bodies(); print("bodies",len(bs),[(pv(b,"Name"),bbox(b).round(1).tolist()) for b in bs])
h0=holes_raw(bs); print("Ø8 holes (STEP coords) origin/axis/box:"); [print("   ",h) for h in h0]
# STEP 규약 확인(09-10과 동일 가정): 축 X, 후단 핀홀 x +15, 전단 x −324, 핀 축 Z
xs=sorted(set(h[0][0] for h in h0)); assert h0, "no Z-axis Ø8 holes"
assert abs(max(xs)-15)<0.1 and abs(min(xs)+(RL-15))<0.1, ("hole x differs from 09-10 convention",xs)
R=np.array([[0,0,1],[1,0,0],[0,1,0]],float); T=np.array([0,0,-15.0])
c0=[centroid(b) for b in bs]; exp=[c@R+T for c in c0]
ang=Rotation.from_matrix(R.T).as_euler("xyz"); SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}
for axis,val in zip("xyz",ang):
    if abs(val)<1e-9: continue
    s=SLOT[axis]; sel_bodies(bodies()); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3
    assert mv is not None, ("rot failed",axis); mv.Name=f"정렬_회전_{axis.upper()}"
sel_bodies(bodies()); mv=d.FeatureManager.InsertMoveCopyBody2(mm(T[0]),mm(T[1]),mm(T[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv is not None; mv.Name="정렬_이동"
bs=bodies(); got=sorted([centroid(b) for b in bs],key=lambda c:c[2]); expS=sorted(exp,key=lambda c:c[2])
assert all(np.all(np.abs(g-e)<0.05) for g,e in zip(got,expS)), ("alignment mismatch",got,expS)
AXI=4; h1=holes_raw(bs); print("holes after align:"); [print("   ",h) for h in h1]
zs=sorted(set(h[0][2] for h in h1)); assert all(abs(h[0][0])<0.05 for h in h1) and abs(min(zs)+RL)<0.05 and abs(max(zs))<0.05, zs
rear_w=[fb for (o,a_,fb) in h1 if abs(o[2])<0.05]; front_w=[fb for (o,a_,fb) in h1 if abs(o[2]+RL)<0.05]
U_rear=max(max(f[4] for f in rear_w),-min(f[1] for f in rear_w))*2; U_front=max(max(f[4] for f in front_w),-min(f[1] for f in front_w))*2
print(f"U outer width: rear {U_rear:.1f} front {U_front:.1f} (B9g 실측 22.4/17.6)")
motor=[bbox(b) for b in bs]; print("boxes after align",[b.round(1).tolist() for b in motor])
for cfg,desc in (("상승","로드 후퇴"),("하강",f"로드 {STROKE:.0f} 신장")): d.AddConfiguration3(cfg,desc,"",0)
d.ShowConfiguration2("하강"); d.EditRebuild3
rodb=[b for b in bodies() if any(abs(o[2]+RL)<0.05 for (o,a_,fb) in holes_raw([b]))]; assert len(rodb)==1, len(rodb)
sel_bodies(rodb); mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(-STROKE),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); assert mv is not None; mv.Name="로드_하강_이동"; d.EditRebuild3
mv.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
rep={"U_rear":U_rear,"U_front":U_front,"holes":h1,"cfg":{}}
for cfg in ("상승","하강"):
    d.ShowConfiguration2(cfg); d.EditRebuild3; info=[(pv(b,"Name"),bbox(b).round(1).tolist()) for b in bodies()]; hz=sorted(set(h[0][2] for h in holes_raw(bodies()))); rep["cfg"][cfg]={"bodies":info,"hole_z":hz}; print(f" [{cfg}] hole z {hz}",info)
assert abs(min(rep["cfg"]["하강"]["hole_z"])-(-RL-STROKE))<0.05, rep["cfg"]["하강"]["hole_z"]
d.ShowConfiguration2("상승"); d.EditRebuild3
cp=d.Extension.CustomPropertyManager("")
props={"TITLE":"LINEAR ACTUATOR TiMOTION TA2 (500 N, 스트로크 150, 설치길이 274, 양단 클레비스 U)",
 "SPEC":f"TiMOTION TA2-2H-150274-5511-010-1: 24 V DC, 하중코드 H(500 N 밀기/당기기, 셀프락 500 N, 17/14 mm/s, 1.3/0.8 A — TraceParts 속성 원문), 스트로크 150(표준 범위 20~150), 설치길이(후퇴, 홀-홀) 274 지정(≥150+119, 데이터시트 20160711-M p.6), 후단 취부 5·전단 취부 5(클레비스 U, 홈 6·홀 Ø8), 리미트 스위치 1, 출력신호 0, IP 없음(코드 0), 케이블 100. 3D = TraceParts 제조사 구성 STEP(REFERENCE TA2-2H-150274-5511-010-1) 원형 — 클레비스 U 바깥폭 실측 후단 {U_rear:.1f}·전단 {U_front:.1f}(승인도면 확인). 파트 좌표: 후단 핀 원점, 축 −Z, 핀 축 Y, 모터 +X",
 "MATERIAL":"AL casting/SUS rod","QT'Y":"1","DATE":"2026-09-17",
 "REMARK":"구매품. B9j(원시 형상 대용)를 TraceParts 제조사 STEP으로 교체. 구성 하강 = 로드 바디 −150 이동(STEP은 후퇴 상태만 제공). 주문 표기: TA2-2H-150, Retracted Length 274, 후단 5·전단 5, 방향 0°, 리미트 1, 신호 0.",
 "TOLERANCE":"TiMOTION 데이터시트: 전단 클레비스 U 슬롯 6.0·구멍 8.0, 후단 CNC 슬롯 6.0·구멍 8.0 — 공차 미기재(승인도면 요청). 핀 SHCCG8 g6 ↔ 구멍 8.0 공차 미확인."}
for k_,v_ in props.items(): cp.Add3(k_,30,v_,1)
try: d.SetMaterialPropertyName2("","이텍","STS 304")
except Exception: pass
e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved",ok,e.value,w.value,os.path.basename(OUT)); assert ok
app.CloseDoc(d.GetTitle)
json.dump(rep,open(os.path.join(VER,"ta2_b9k_build_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("B9k build done")
