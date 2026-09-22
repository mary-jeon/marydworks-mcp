# 2026-09-10: TraceParts TiMOTION TA2-2H-140339-5511-010-1 STEP(파트, 솔리드 2: 몸체+후단 클레비스 / 로드+전단 클레비스) → 우리 B9f 규약으로 정렬 → 구성 상승/하강(로드 −140) → B9g 저장
#  STEP 좌표: 액추에이터 축 X(후단 핀홀 x +15, 전단 핀홀 x −324, 홀-홀 339), 핀 축 Z, 모터 +y.  우리 규약(B9f): 축 −Z(후단 핀 z 0, 전단 z −339), 핀 축 Y, 모터 +X.
#  변환(행벡터): p_our = p_step·R + (0,0,−15), R: e_x→(0,0,1), e_y→(1,0,0), e_z→(0,1,0)
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.spatial.transform import Rotation
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
OUT=os.path.join(Z,"B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT"); assert not os.path.exists(OUT), OUT
STROKE=140.0; mm=lambda v:v/1000.0
stop=watchdog(); app=connect()
docs=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.startswith("B9f_TA2-2H-140339")]
assert docs, "imported TA2 doc not open — run inspect_ta2_step_0910.py first"
d=docs[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); d=app.ActiveDoc; print("doc",d.GetTitle)
def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
def sel_bodies(bs):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
    for b in bs: b.Select2(True,sd)
R=np.array([[0,0,1],[1,0,0],[0,1,0]],float); T=np.array([0,0,-15.0])
bs=bodies(); assert len(bs)==2, len(bs)
c0=[centroid(b) for b in bs]; exp=[c@R+T for c in c0]; print("centroids before",[c.round(2) for c in c0])
ang=Rotation.from_matrix(R.T).as_euler("xyz"); SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}
for axis,val in zip("xyz",ang):
    if abs(val)<1e-9: continue
    s=SLOT[axis]; sel_bodies(bodies()); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3
    assert mv is not None, ("rot failed",axis); mv.Name=f"정렬_회전_{axis.upper()}"
sel_bodies(bodies()); mv=d.FeatureManager.InsertMoveCopyBody2(mm(T[0]),mm(T[1]),mm(T[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv is not None; mv.Name="정렬_이동"
bs=bodies(); got=sorted([centroid(b) for b in bs],key=lambda c:c[2]); expS=sorted(exp,key=lambda c:c[2])
print("centroids after",[c.round(2) for c in got],"expected",[c.round(2) for c in expS])
assert all(np.all(np.abs(g-e)<0.05) for g,e in zip(got,expS)), "alignment mismatch"
for b in bs: print("  body",pv(b,"Name"),bbox(b).round(1))
# ---- 핀홀·슬롯 검증(정렬 후)
holes=[]; slot_planes=[]
for b in bs:
    for fc in b.GetFaces():
        s=fc.GetSurface; fb=np.array([v*1000 for v in fc.GetBox])
        if s.IsCylinder:
            p=s.CylinderParams; r=p[6]*1000
            if abs(r-4.0)<0.05 and abs(p[4])>0.99: holes.append((round(p[0]*1000,2),round(p[2]*1000,2),fb.round(1).tolist()))
        elif s.IsPlane:
            n=[round(v,3) for v in pv(fc,"Normal")]
            if abs(n[2])>0.99 and abs(fb[1])<=3.05 and abs(fb[4])<=3.05 and fb[4]-fb[1]>4: slot_planes.append((n[2],round(fb[2],2),fb.round(1).tolist()))
print("Ø8 pin holes (x, z, box):"); [print("   ",h) for h in sorted(set((h[0],h[1]) for h in holes))]
print("slot bottom candidates (normal z, z, box):"); [print("   ",p) for p in sorted(slot_planes,key=lambda p:p[1])]
xs=sorted(set(h[0] for h in holes)); zs=sorted(set(h[1] for h in holes)); assert all(abs(x)<0.05 for x in xs) and abs(min(zs)+339)<0.05 and abs(max(zs))<0.05, (xs,zs)
rear=[b for b in bs if bbox(b)[5]>0][0]; rod=[b for b in bs if b is not rear][0]
rear_w=[fb for (x_,z_,fb) in holes if abs(z_)<0.05]; front_w=[fb for (x_,z_,fb) in holes if abs(z_+339)<0.05]
U_rear=max(max(f[4] for f in rear_w),-min(f[1] for f in rear_w))*2; U_front=max(max(f[4] for f in front_w),-min(f[1] for f in front_w))*2
print(f"U outer width: rear {U_rear:.1f} front {U_front:.1f} (종전 가정 18/20)")
# ---- 구성: 하강 = 로드 −140
for cfg,desc in (("상승","로드 후퇴"),("하강",f"로드 {STROKE:.0f} 신장")): d.AddConfiguration3(cfg,desc,"",0)
d.ShowConfiguration2("하강"); d.EditRebuild3
rod=[b for b in bodies() if bbox(b)[5]<=0][0]; sel_bodies([rod])
mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(-STROKE),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); assert mv is not None; mv.Name="로드_하강_이동"; d.EditRebuild3
mv.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
rep={"U_rear":U_rear,"U_front":U_front,"holes":holes,"slot_planes":slot_planes,"cfg":{}}
for cfg in ("상승","하강"):
    d.ShowConfiguration2(cfg); d.EditRebuild3; info=[(pv(b,"Name"),bbox(b).round(1).tolist()) for b in bodies()]; rep["cfg"][cfg]=info; print(f" [{cfg}]",info)
d.ShowConfiguration2("상승"); d.EditRebuild3
lo=min(b[1][2] for b in rep["cfg"]["하강"]); assert abs(lo-(-334-15-STROKE))<0.5 or abs(lo-(min(b[1][2] for b in rep["cfg"]["상승"])-STROKE))<0.5, "rod move check"
cp=d.Extension.CustomPropertyManager("")
props={"TITLE":"LINEAR ACTUATOR TiMOTION TA2 (500 N, 스트로크 140, 설치길이 339, 양단 클레비스 U)",
 "SPEC":f"TiMOTION TA2-2H-140339-5511-010-1: 24 V DC, 하중코드 H(500 N 밀기/당기기, 셀프락 500 N, 17/14 mm/s, 1.3/0.8 A), 스트로크 140, 설치길이(후퇴, 홀-홀) 339 지정, 후단 취부 5·전단 취부 5(클레비스 U, 홈 6·홀 Ø8), 리미트 스위치 1, 출력신호 0, IP66D, 케이블 1000. 3D = TraceParts 제조사 구성 STEP(REFERENCE TA2-2H-140339-5511-010-1) 원형 그대로 — 클레비스 U 바깥폭 실측 후단 {U_rear:.1f}·전단 {U_front:.1f}(TraceParts 3D 기준, 승인도면 확인). 파트 좌표: 후단 핀 원점, 축 −Z, 핀 축 Y, 모터 +X",
 "MATERIAL":"AL casting/SUS rod","QT'Y":"1","DATE":"2026-09-10",
 "REMARK":"종전 데이터시트 근사 모델 B9f를 대체. 구성 하강 = 로드 바디 −140 이동(STEP은 후퇴 상태만 제공). 핀 길이는 U 바깥폭 실측값으로 재지정 필요(G11e/J11d)"}
for k_,v_ in props.items(): cp.Add3(k_,30,v_,1)
try: d.SetMaterialPropertyName2("","이텍","STS 304")
except Exception: pass
e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved",ok,e.value,w.value,os.path.basename(OUT))
json.dump(rep,open(os.path.join(VER,"ta2_b9g_build_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("B9g build done")
