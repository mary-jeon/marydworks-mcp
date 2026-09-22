# 2026-09-10: KE002 자식 파트 13개 → 새 파트에 InsertPart3(솔리드, 링크 끊기) + 바디별 회전·이동(원 STEP 어셈블리 변환 그대로) → B4c 단일 다중바디 파트
#  파트 좌표 = STEP 좌표를 평행이동만: 스템 축 = 파트 Z축(x −12.391·y 26.265 → 0), 취부(패드) 면 z 0(원 −23.18 → 0), 몸체 +z. 어셈블리에서 R_g로 회전 배치.
#  「어셈블리를 파트로 저장」은 COM 옵션(전 컴포넌트)을 줘도 곡면 13개만 남겨(3회 실측) 이 경로로 대체.
import sys, os, json, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.spatial.transform import Rotation
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
rec=json.load(open(os.path.join(VER,"ke002_children_0910.json"),encoding="utf-8"))
OUT=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT")
TG=np.array([12.391,-26.265,23.18])   # STEP → 파트 평행이동(mm)
mm=lambda v:v/1000.0
stop=watchdog(); app=connect()
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle)
if os.path.exists(OUT): os.remove(OUT); print("removed old B4c")
for x in list(pv(app,"GetDocuments") or []):
    tt=x.GetTitle
    if re.fullmatch(r"파트4[1-9]",tt) and not x.GetPathName: app.CloseDoc(tt); print("closed",tt); break
tmpl=app.GetUserPreferenceStringValue(8); d=app.NewDocument(tmpl,0,0,0); print("new part",d.GetTitle)
def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
def feats():
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f); f=pv(f,"GetNextFeature")
    return out
def sel_body(b):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1   # MoveCopyBody는 Mark 1 선택 필요(09-09 실측)
    return b.Select2(False,sd)
def delete_last_feature(name):
    d.ClearSelection2(True); d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.EditRebuild3
def box_close(a,b,tol=0.3): return np.all(np.abs(np.array(a)-np.array(b))<tol)
report=[]; final=[]
def target():
    c=[b for b in bodies() if not any(box_close(bbox(b),fb,0.05) for fb in final)]
    assert len(c)==1, ("target ambiguous",len(c)); return c[0]
for k,r in enumerate(rec):
    Rc=np.array(r["R"]); tc=np.array(r["t_mm"]); exp_box=np.array(r["box"])   # 어셈블리 좌표 박스
    before={pv(b,"Name") for b in bodies()}
    f=d.InsertPart3(r["file"],1|512|262144,"")   # 솔리드만 · 링크 끊기 · 줌 안 함
    d.EditRebuild3
    new=[b for b in bodies() if pv(b,"Name") not in before]
    assert f is not None and len(new)==1, (k,r["name"],f,len(new))
    b=new[0]; name=pv(b,"Name"); b0=bbox(b)
    # 로컬 박스 → 회전만 적용한 기대 박스 = 어셈블리 박스 − tc
    exp_rot=exp_box-np.concatenate([tc,tc])
    def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
    c_loc=centroid(b); c_rot_exp=c_loc@Rc            # 행벡터 규약 p'=p·Rc
    if not np.allclose(Rc,np.eye(3),atol=1e-6):
        ang=Rotation.from_matrix(Rc.T).as_euler("xyz")   # 외재적 x→y→z: M = Rz(c)·Ry(b)·Rx(a)
        SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}      # 실측: 8번째 인수=Z축, 9번째=Y축, 10번째=X축 회전
        for axis,val in zip("xyz",ang):
            if abs(val)<1e-9: continue
            s=SLOT[axis]; sel_body(b)
            mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3
            assert mv is not None, ("rot feature failed",axis); b=target()
        c_got=centroid(b); ok=np.all(np.abs(c_got-c_rot_exp)<0.05)
        print(f"  [{k}] rot xyz {np.degrees(ang).round(2)} centroid {c_got.round(2)} expected {c_rot_exp.round(2)} {'OK' if ok else 'NO'}")
        assert ok, "rotation mismatch "+r["name"]
    t=tc+TG
    sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(mm(t[0]),mm(t[1]),mm(t[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3
    assert mv is not None, "translate failed"
    b=target(); got=bbox(b); exp=exp_box+np.concatenate([TG,TG]); c_got=centroid(b); c_exp=c_rot_exp+t
    ok=np.all(np.abs(c_got-c_exp)<0.05); okb=box_close(got,exp,0.5)
    print(f"  [{k}] {r['name'][:36]:36s} translate -> box {got.round(1)} {'boxOK' if okb else 'box≠'+str(exp.round(1))} centroid {c_got.round(2)} {'OK' if ok else 'NO '+str(c_exp.round(2))}")
    assert ok
    final.append(got); report.append({"name":r["name"],"body":pv(b,"Name"),"box":got.tolist()})
bs=bodies(); pb=np.array([v*1000 for v in pv(d,"GetPartBox",True)])
vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs)
print("bodies",len(bs),"part box",pb.round(2),"vol",round(vol))
exp_pb=np.array([-93.14,-6.44,-23.18,13.6,67.16,95.75])+np.concatenate([TG,TG]); print("expected part box",exp_pb.round(2))
assert box_close(pb,exp_pb,0.5)
# 스템 축 확인: 취부면(z≈0)의 탭 구멍 원통 중심이 (0,0) 주변 PCD 36/50에 있어야
holes=[]
for b in bs:
    for fc in b.GetFaces():
        s=fc.GetSurface
        if s.IsCylinder:
            p=s.CylinderParams; rr=p[6]*1000; fb=[v*1000 for v in fc.GetBox]
            if 1.8<=rr<=3.3 and abs(p[5])>0.99 and fb[2]<3: holes.append((round(rr,2),round(p[0]*1000,2),round(p[1]*1000,2),round(math.hypot(p[0]*1000,p[1]*1000),2)))
print("mount-face tapped holes (r, cx, cy, dist from Z axis):",sorted(set(holes)))
cp=d.Extension.CustomPropertyManager("")
props={"TITLE":"ELECTRIC ACTUATOR KOSAPLUS KE002 (24 VDC, ISO5211 F03/F05)",
 "SPEC":"코사플러스 KE002 F35C11 DC 24 VDC 쿼터턴 전동 액추에이터. 제조사 도면 KE002-0001: 118.9(스템축) × 92.1(59.4+32.7) × 105.3(80.6+24.7), 취부 ISO5211 F03(M5 TAP DP12)/F05(M6 TAP DP12), 스템 11각(STAR) DP15, 케이블 PG11 1000. 카탈로그(kosa_electric_2018.pdf): 20 N·m, 1.5 A, IP67, −20~+60 ℃, 0.9 kg. 3D = 제조사 STEP(kosaplus.com 다운로드, 13파트 → 단일 파트 합성). 파트 좌표: Z = 스템 축, z 0 = 취부면, 몸체 +z",
 "MATERIAL":"미확인(카탈로그 미기재)","QT'Y":"1","DATE":"2026-09-10",
 "REMARK":"로봇 밸브 KE002-10S3(C2)와 같은 제조사·모델. 3D 참고용, 치수는 2D 도면 우선(제조사 주기). 종전 근사 모델 B4b를 대체. 케이블 글랜드는 STEP에 없음(도면 폭 92.1 vs STEP 73.6)"}
for k_,v_ in props.items(): cp.Add3(k_,30,v_,1)
e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved",ok,e.value,w.value,os.path.basename(OUT))
json.dump({"bodies":report,"part_box":pb.tolist(),"vol":vol,"holes":sorted(set(holes)),"TG":TG.tolist()},open(os.path.join(VER,"ke002_b4c_build_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("B4c build done")
