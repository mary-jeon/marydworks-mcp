# 2026-09-10: J23 홀더 수정 — 첫 빌드에서 귀 돌출·보어·볼트홀·슬릿 컷이 안 만들어지고 스케치 3개가 고아로 남음(박스가 스케치를 포함해 검증이 새 나감). 고아 스케치 삭제 후 바디 박스로 검증하며 재생성.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
mm=lambda v:v/1000.0; PITCH=40.0
OUT=os.path.join(Z,"J23_shaft_support_MISUMI_SHFSS16.SLDPRT")
stop=watchdog(); app=connect()
d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
def sel_plane(nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def feats():
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def bodies(): return list(pv(d,"GetBodies2",0,True) or [])
def bbox():
    bs=bodies(); assert len(bs)==1, len(bs); return [round(v*1000,1) for v in pv(bs[0],"GetBodyBox")]
def vol(): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bodies())
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    d.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def new_sketch(plane,draw):
    assert sel_plane(plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    nm=d.SketchManager.ActiveSketch; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n,t in feats() if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def delete_feature(name,absorbed=1):
    d.ClearSelection2(True); ok=d.Extension.SelectByID2(name,"SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0)
    assert ok, name; d.Extension.DeleteSelection2(absorbed); d.EditRebuild3
def extrude(depth,dir_flag,name):
    f=d.FeatureManager.FeatureExtrusion3(True,False,dir_flag,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
    assert f is not None, "extrude failed "+name; f.Name=name; return f
def cut_all(name):
    f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    assert f is not None, "cut failed "+name; f.Name=name; return f
print("features before",feats()[-8:]); print("bodies",len(bodies()),"vol",round(vol()))
# 1) 고아 스케치 삭제(스윕/돌출에 흡수되지 않은 것)
absorbed=set()
for n,t in feats():
    if t!="ProfileFeature":
        ft=d.FeatureByName(n)
        try:
            for p in (pv(ft,"GetParents") or []): absorbed.add(p.Name)
        except Exception: pass
for n,tp in feats():
    if n.startswith("보스-돌출"): delete_feature(n,1); print("deleted debug feature",n)
absorbed=set()
for n,tp in feats():
    if tp!="ProfileFeature":
        ft=d.FeatureByName(n)
        try:
            for p_ in (pv(ft,"GetParents") or []): absorbed.add(p_.Name)
        except Exception: pass
orphans=[n for n,t in feats() if t=="ProfileFeature" and n not in absorbed]
print("orphan sketches",orphans)
for n in orphans: delete_feature(n,0)
print("after cleanup",feats()[-5:],"box",bbox())
v0=vol()
# 2) 클램프 귀: 정면 스케치 사각형 (−10..10, −14..−31) → 16 돌출(−z)
sk=new_sketch("정면",lambda sm: sm.CreateCornerRectangle(mm(-10),mm(-13),0,mm(10),mm(-31),0))   # 플랜지와 1 mm 겹침(경계 일치 시 Dir=True 돌출 실패 실측)
f=extrude(16.0,True,"클램프귀_B20"); bx=bbox(); print("lug",bx,"vol",round(vol()))
if bx[5]>0.5 or bx[1]>-30.9:
    delete_feature("클램프귀_B20",1); sk=new_sketch("정면",lambda sm: sm.CreateCornerRectangle(mm(-10),mm(-13),0,mm(10),mm(-31),0)); f=extrude(16.0,False,"클램프귀_B20"); bx=bbox(); print("lug(flip)",bx)
assert abs(bx[1]+31)<0.1 and abs(bx[2]+16)<0.1 and abs(bx[5])<0.1, bx
assert vol()>v0+16*17*16*0.9
# 3) 보어 Ø16 관통
v1=vol(); new_sketch("정면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(8))); cut_all("보어_D16"); print("bore vol",round(v1),"->",round(vol())); assert vol()<v1-3000
# 4) 볼트홀 Ø5.5 ×2
v2=vol(); new_sketch("정면",lambda sm: (sm.CreateCircleByRadius(mm(PITCH/2),0,0,mm(2.75)),sm.CreateCircleByRadius(mm(-PITCH/2),0,0,mm(2.75)))); cut_all("볼트홀_D5.5x2"); print("bolt vol",round(v2),"->",round(vol())); assert vol()<v2-300
# 5) 슬릿 2 (보어 안쪽 y −6 에서 귀 끝 −31.5 까지)
v3=vol(); new_sketch("정면",lambda sm: sm.CreateCornerRectangle(mm(-1),mm(-6),0,mm(1),mm(-31.5),0)); cut_all("슬릿_C2"); print("slit vol",round(v3),"->",round(vol())); assert vol()<v3-300
# 6) 클램프 볼트 M4 (x 방향 관통, 귀 중앙 y −22.5, z −8): 우측면 스케치 좌표 검증 후 컷
v4=vol(); new_sketch("우측면",lambda sm: sm.CreateCircleByRadius(mm(-22.5),mm(-8),0,mm(2.25))); cut_all("클램프볼트_M4"); dv=v4-vol(); print("M4 vol removed",round(dv))
if dv<50:   # 좌표축 뒤바뀜이면 다른 배치로 재시도
    delete_feature("클램프볼트_M4",1); new_sketch("우측면",lambda sm: sm.CreateCircleByRadius(mm(-8),mm(-22.5),0,mm(2.25))); cut_all("클램프볼트_M4"); dv=v4-vol(); print("M4 vol removed(retry)",round(dv))
bs=bodies(); print("final bodies",len(bs),"box",bbox(),"vol",round(vol()),"ww",ww())
cyl=sorted(set((round(s.CylinderParams[6]*1000,2),tuple(round(v,2) for v in s.CylinderParams[3:6])) for b in bs for fc in b.GetFaces() for s in [fc.GetSurface] if s.IsCylinder)); print("cyl",cyl)
assert len(bs)==1 and not ww() and any(abs(c[0]-8.0)<0.05 for c in cyl)
orphans=[n for n,t in feats() if t=="ProfileFeature" and n not in {p.Name for n2,t2 in feats() if t2!="ProfileFeature" for p in (pv(d.FeatureByName(n2),"GetParents") or [])}]
print("orphans now",orphans); assert not orphans
e=I4(); w=I4(); print("save J23",d.Save3(1,e,w),e.value)
# ---- 어셈블리 간섭 재확인
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
rep={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_={n:c for n,c in cc.items() if c.GetSuppression2==2}
    rows=interf(list(act_.values())); rows=[r for r in rows if any(x.startswith(("J23","J2c","J1c")) for x in r[0])]
    rep[cfg]=rows; print(f"[{cfg}] 홀더·봉·판 관련 간섭 {len(rows)}:",rows)
    for n in sorted(act_):
        if n.startswith("J23"): print("   ",n,box(act_[n]))
a.ShowConfiguration2("상승"); a.EditRebuild3; e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
json.dump(rep,open(os.path.join(VER,"shaft_holder_fix_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("fix done")
