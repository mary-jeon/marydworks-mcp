# 2026-09-09 밤: 대공사 4단계 — B9e 보어 방향 수정, J9d 높이 31→30, 라인·스테이션 간섭 검사
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
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def sketch_of(d,featname):
    f=d.FeatureByName(featname); sf=pv(f,"GetFirstSubFeature")
    while sf:
        if pv(sf,"GetTypeName2")=="ProfileFeature": return sf.Name
        sf=pv(sf,"GetNextSubFeature")
def cyl_r(d,r):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05: out.append([round(v*1000,1) for v in fc.GetBox])
    return sorted(out)
def save(d):
    e=I4(); w=I4(); ok=d.Save3(1,e,w); print("  save",d.GetTitle,ok); return ok
# ---- B9e 보어
d=act(Zp("B9e_TiMOTION_TA2-2H-120_24V_clevisU.SLDPRT")); d.ShowConfiguration2("상승"); d.EditRebuild3
bore=cyl_r(d,10.5); print("bore faces before",bore)
if not any(b[2]<=-227 and b[5]>=-113 for b in bore):
    sk=sketch_of(d,"튜브_보어_D21"); d.ClearSelection2(True); d.Extension.SelectByID2("튜브_보어_D21","BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.EditRebuild3
    for dirn in (False,True):
        d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureCut4(True,False,dirn,0,0,mm(116.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
        bore=cyl_r(d,10.5); print("  dir",dirn,"bore faces",bore)
        if any(b[2]<=-227 and b[5]>=-113 for b in bore): f.Name="튜브_보어_D21"; break
        d.ClearSelection2(True); d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.EditRebuild3
print("B9e bodies",[(pv(b,'Name'),[round(v*1000,1) for v in pv(b,'GetBodyBox')]) for b in (pv(d,'GetBodies2',0,True) or [])])
save(d)
# ---- J9d 높이 31 → 30 (전단 U 홈 바닥 = 홀 위 5)
d=act(Zp("J9d_lug_PL6_40x31.SLDPRT"))
prm=d.Parameter("D1@러그_PL6"); print("J9d D1",prm.SystemValue*1000)
if abs(prm.SystemValue*1000-31)<0.1: prm.SystemValue=mm(30.0); d.EditRebuild3
print("J9d box",[round(v*1000,1) for v in pv(d,"GetPartBox",True)],"hole",cyl_r(d,4.0))
cp=d.Extension.CustomPropertyManager(""); cp.Set2("SPEC","STS304 PL6 × 40 × 30, 핀홀 Ø8(상단에서 5). TA2 전단 클레비스 U(홈 6·깊이 10.5)에 삽입"); save(d)
# ---- 라인 간섭
ASM=Zp("염수주입라인.SLDASM"); a=act(ASM,2); cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def interf(doc,items):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
rep={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(a,act_); rep["line_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3; save(a)
# ---- 스테이션: 라인 ↔ 탱크(호퍼벽·박스·상판) ↔ 로봇(210000MU1 커버 그룹 + 상부)
PS=Zp("S00000MU0.SLDASM"); s=act(PS,2); scm=s.ConfigurationManager
LINE=("B9e","J8d","J9d","G11e","J11d","G3b","B4b","J19e","J5e","J1c","J2_","B10","G13","G14","H16","J17")
for cfg in ("상승","하강"):
    s.ShowConfiguration2(cfg); s.ForceRebuild3(False); out=[]
    def walk(c,depth):
        for ch in (pv(c,"GetChildren") or []):
            if ch.GetSuppression2!=2: continue
            out.append((ch.Name2,ch))
            if depth<6: walk(ch,depth+1)
    walk(scm.ActiveConfiguration.GetRootComponent3(True),0)
    line=[(n,c) for n,c in out if n.split("/")[-1].startswith(LINE)]
    robot=[(n,c) for n,c in out if "210000MU1-1/" in n and n.count("/")==3]
    tank=[(n,c) for n,c in out if n.split("/")[-1].startswith(("S30001MU0","S30002MU0","S30006MU0","S30003MU0"))]
    print(f"[station {cfg}] line {len(line)} robot {len(robot)} tank {len(tank)}")
    rows=interf(s,[c for n,c in line+robot+tank]); rows=[r for r in rows if any(x.startswith(LINE) for x in r[0])]
    rows_ext=[r for r in rows if not all(x.startswith(LINE) for x in r[0])]
    rep["station_"+cfg]=rows_ext; print(f"[station {cfg}] 라인↔외부 간섭 {len(rows_ext)}:",rows_ext)
    gl={}
    for n,c in line:
        base=n.split("/")[-1]
        if base.startswith(("J17","J5e","B9e","B4b","J19e","B10")):
            b=box(c); gl[base]={"지상고":[round(1109-b[3],1),round(1109-b[0],1)],"y":[b[1],b[4]],"z":[b[2],b[5]]}
    rep["station_"+cfg+"_gl"]=gl
    for k,v in gl.items(): print("   ",k,v)
s.ShowConfiguration2("상승"); s.EditRebuild3
json.dump(rep,open(os.path.join(VER,"ta2_rebuild_check_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("check done (station NOT saved)")
