# 2026-09-09 밤: 대공사 2.5단계 — 핀홀 양방향 관통(T1=9 ThroughAllBoth)으로 재컷, TA2 튜브 보어(로드 자체 겹침 제거), 라인 간섭 재검
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
Zp=lambda n: os.path.join(Z,n)
def act(p):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def sketch_of(d,featname):
    f=d.FeatureByName(featname); sf=pv(f,"GetFirstSubFeature")
    while sf:
        if pv(sf,"GetTypeName2")=="ProfileFeature": return sf.Name
        sf=pv(sf,"GetNextSubFeature")
def cyl4(d):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-4.0)<0.05: out.append([round(v*1000,1) for v in fc.GetBox])
    return sorted(out)
def recut_both(d,featname):
    sk=sketch_of(d,featname); print("  ",featname,"sketch",sk,"before",cyl4(d))
    d.ClearSelection2(True); d.Extension.SelectByID2(featname,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.EditRebuild3
    d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureCut4(True,False,False,9,0,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    if f: f.Name=featname
    print("  ",featname,"after",cyl4(d),"feat",f.Name if f else None)
def save(d):
    e=I4(); w=I4(); ok=d.Save3(1,e,w); print("  save",d.GetTitle,ok); return ok
# B9d: 핀홀 2개 재컷 + 튜브 보어 Ø21 (전단 캡 -214에서 위로 100)
d=act(Zp("B9d_TiMOTION_TA2-2H-120_24V.SLDPRT")); d.ShowConfiguration2("상승"); d.EditRebuild3
for fn in ("후단_핀홀_D8","로드_핀홀_D8"): recut_both(d,fn)
if d.FeatureByName("튜브_보어_D21") is None:
    d.ClearSelection2(True); d.Extension.SelectByID2("평면1","PLANE",0,0,0,False,0,NOD,0)   # 평면1 = z -112
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(10.5)); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    skn=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
    # 보어: 튜브 내부 z -112 → -214 (Dir=True → -z 방향 102) ; 로드 바디는 피처 범위에서 빠지도록 하우징 바디만 선택 불가 → 결과로 검증
    n0=[( pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")]) for b in (pv(d,"GetBodies2",0,True) or [])]
    f=d.FeatureManager.FeatureCut4(True,False,True,0,0,mm(102.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    n1=[( pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")]) for b in (pv(d,"GetBodies2",0,True) or [])]
    print("  bore feat",f.Name if f else None,"bodies",n0,"->",n1)
    if f: f.Name="튜브_보어_D21"
    if len(n1)!=2 or any(bb[2]>-230 for nm,bb in n1 if "로드" in nm or bb[5]<-140):   # 로드 바디가 잘렸는지 확인
        print("  !! bore may have cut the rod; check")
for cfg in ("상승","하강","기본"):
    d.ShowConfiguration2(cfg); d.EditRebuild3; print(f"  [{cfg}]",[(pv(b,'Name'),[round(v*1000,1) for v in pv(b,'GetBodyBox')]) for b in (pv(d,'GetBodies2',0,True) or [])])
d.ShowConfiguration2("상승"); d.EditRebuild3; save(d)
for fn in ("J8c_sm_U_bracket_t3.2_25x140x40.SLDPRT","J9c_sm_U_clevis_t3.2_27x33x40.SLDPRT"):
    d=act(Zp(fn)); recut_both(d,"핀홀_D8"); print("  feats tail",feats(d)[-5:]); save(d)
# 라인 간섭 재검
ASM=Zp("염수주입라인.SLDASM"); a=act(ASM); cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
rep={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); a.ClearSelection2(True)
    act_=[n for n,c in cc.items() if c.GetSuppression2==2]
    for n in act_: cc[n].Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True)
    rep[cfg]=rows; print(f"[{cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3; save(a)
json.dump(rep,open(os.path.join(VER,"ta2_rebuild_line_interf2_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("fix done")
