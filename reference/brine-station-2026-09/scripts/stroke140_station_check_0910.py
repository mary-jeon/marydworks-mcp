# 2026-09-10: 스트로크 140 — 라인 자체 간섭(TreatSubAssembliesAsComponents=False, 양성 대조) + 스테이션 S00000MU0 상승/하강 라인↔로봇 커버군↔탱크 간섭·지상고
#  읽기 전용: S00000MU0·900000MU1 저장 안 함.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n)
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
stop=watchdog(); app=connect()
def act(p,typ=2):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def interf(doc,items,sub_as_comp=False):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=sub_as_comp; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
rep={}
# ---- 라인 (양성 대조: G14↔G3b·봉↔J1c 나사 겹침이 잡혀야 함)
a=act(ASM); cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(a,act_,False); rep["line_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3
ctrl=any(any(x.startswith(("G13","G14","H16")) for x in r[0]) and any(x.startswith(("G3b","G3c")) for x in r[0]) for r in rep["line_상승"])
print("양성 대조(G14↔G3b 나사 겹침 검출):",ctrl); rep["positive_control"]=ctrl
# ---- 스테이션
PS=Zp("S00000MU0.SLDASM"); s=act(PS,2); scm=s.ConfigurationManager
print("station cfgs",list(pv(s,"GetConfigurationNames")))
LINE=("B9f","B9g","J23","J8e","J9d","G11e","G11f","J11d","J11e","G3b","G3c","B4b","B4c","J19e","J5e","J1c","J2_","J2c","B10","G13","G14","H16","J17")
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
    print(f"[station {cfg}] line {len(line)} robot {len(robot)} tank {len(tank)}")
    rows=interf(s,[c for n,c in line+robot+tank],False)
    rows_line=[r for r in rows if any(x.startswith(LINE) for x in r[0])]
    rows_ext=[r for r in rows_line if not all(x.startswith(LINE) for x in r[0])]
    rows_int=[r for r in rows_line if all(x.startswith(LINE) for x in r[0])]
    rep["station_"+cfg]={"ext":rows_ext,"int":rows_int,"all_count":len(rows)}
    print(f"[station {cfg}] 라인↔외부 간섭 {len(rows_ext)}: {rows_ext}  | 라인 내부(나사 겹침) {len(rows_int)}: {rows_int}")
    g={}
    for n,c in line:
        base=n.split("/")[-1]
        if base.startswith(("J17","J5e","B9f","B9g","B4b","B4c","J19e","J9d","J11d","J11e","G3c")): g[base]=gl(box(c))
    # 로봇 커버 실린더 로드·브래킷 위치(커버 열림/닫힘 판정용)
    for n,c in out:
        base=n.split("/")[-1]
        if base.startswith(("TA2-2H-200_ROD","212003")) or "TA2-2H-200" in base: g["ROBOT/"+base]=gl(box(c))
    rep["station_"+cfg+"_gl"]=g
    for k,v in g.items(): print("   ",k,v)
s.ShowConfiguration2("상승"); s.EditRebuild3
json.dump(rep,open(os.path.join(VER,"station_check_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("check done (station NOT saved)")
