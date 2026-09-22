# 2026-09-14: 50A 텔레스코픽 라인 검사 — 라인 자체 간섭(상승/하강) + 스테이션 S00000MU0 라인↔로봇(커버군)↔탱크 간섭·지상고. 읽기 전용(저장 안 함)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
Zp=lambda n: os.path.join(Z,n)
stop=watchdog(); app=connect()
def act(p,typ=2):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def interf(doc,items,sub_as_comp=False):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=sub_as_comp; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
rep={}
LINE=("B9g","J23","J8e","J9d","G11f","J11e","G3d","B4d","G13d","K1_","K2_","K3_","K4_","J5f","J1c","J2c","B10")
# ---- 라인
a=act(ASM); cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(a,act_,False); rep["line_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:")
    for r in rows: print("    ",r)
    bb={n:box(c) for n,c in cc.items() if c.GetSuppression2==2}
    zmin=min(b[2] for b in bb.values()); zmax=max(b[5] for b in bb.values()); xmin=min(b[0] for b in bb.values()); xmax=max(b[3] for b in bb.values())
    print(f"   line bbox x {xmin}..{xmax} z {zmin}..{zmax}")
    rep["line_bbox_"+cfg]=[xmin,xmax,zmin,zmax]
a.ShowConfiguration2("상승"); a.EditRebuild3
ctrl=any(any(x.startswith("J2c") for x in r[0]) and any(x.startswith("J1c") for x in r[0]) for r in rep["line_상승"])
print("양성 대조(봉↔J1c 나사 겹침 471 검출):",ctrl); rep["positive_control"]=ctrl
# ---- 스테이션
PS=Zp("S00000MU0.SLDASM"); s=act(PS,2); scm=s.ConfigurationManager
print("station cfgs",list(pv(s,"GetConfigurationNames")),"active",scm.ActiveConfiguration.Name)
def gl(b): return {"지상고":[round(1109-b[3],1),round(1109-b[0],1)],"y":[b[1],b[4]],"z":[b[2],b[5]]}
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
    frame=[(n,c) for n,c in out if n.split("/")[-1].startswith(("S10","S20")) and n.count("/")<=2]
    print(f"[station {cfg}] line {len(line)} robot {len(robot)} tank {len(tank)} frame {len(frame)}")
    rows=interf(s,[c for n,c in line+robot+tank+frame],False)
    rows_line=[r for r in rows if any(x.startswith(LINE) for x in r[0])]
    rows_ext=[r for r in rows_line if not all(x.startswith(LINE) for x in r[0])]
    rows_int=[r for r in rows_line if all(x.startswith(LINE) for x in r[0])]
    rep["station_"+cfg]={"ext":rows_ext,"int":rows_int,"all_count":len(rows)}
    print(f"[station {cfg}] 라인↔외부 간섭 {len(rows_ext)}: {rows_ext}  | 라인 내부 {len(rows_int)}: {rows_int}")
    g={}
    for n,c in line:
        base=n.split("/")[-1]
        if base.startswith(("K2_","K3_","J5f","B9g","B4d","G3d","J9d","J11e","K1_")): g[base]=gl(box(c))
    for n,c in out:
        base=n.split("/")[-1]
        if base.startswith(("TA2-2H-200_ROD","212003","210004","H1E000010")): g["ROBOT/"+base]=gl(box(c))
    rep["station_"+cfg+"_gl"]=g
    for k,v in g.items(): print("   ",k,v)
s.ShowConfiguration2("기본"); s.EditRebuild3
json.dump(rep,open(os.path.join(VER,"check50_0914.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("check done (nothing saved)")
