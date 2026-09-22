"""09-08 저녁: 절곡 파트를 판금 피처로 변환(솔리드 → InsertConvertToSheetMetal2).
사용자 지시 "판금이면 판금으로 해줘. 솔리드로 하지말고". 스케치·기존 피처는 손대지 않고 뒤에 변환 피처만 추가.
실측 규칙(J9b): 고정면 mark 1 + **바깥쪽** 모서리(고정면의 긴 변) mark 2 + FindBends=True 조합만 성공.
안쪽 모서리 mark 2, mark 4, FindBends=False 는 None. 모서리 없이 FindBends만 주면 벽이 잘려 나감(부피 47,921→17,280).
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
stop=watchdog(); app=connect()
SKIP=("RefPlane","OriginProfileFeature","MaterialFolder","CommentsFolder","FavoriteFolder","HistoryFolder","SelectionSetFolder","SensorFolder","DocsFolder","DetailCabinet","InkMarkupFolder","SurfaceBodyFolder","SolidBodyFolder","EnvFolder","EqnFolder","CutListFolder")
OUT=r"<PROJECT_DIR>\_검증\tank_recheck_2026-09-08\sheetmetal_convert.json"
log={}
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None:
        t=pv(f,"GetTypeName2")
        if t not in SKIP: out.append((f.Name,t))
        f=pv(f,"GetNextFeature")
    return out
def vol(d): return round(pv(d.Extension,"CreateMassProperty").Volume*1e9)
def ww(d):
    a,b,c=[VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None) for _ in range(3)]; d.Extension.GetWhatsWrong(a,b,c); return [(x.Name,y) for x,y in zip(a.value or [],b.value or [])]
def cyls(d):
    b=(pv(d,"GetBodies2",0,True) or [])[0]; out=[]
    for f in b.GetFaces():
        s=f.GetSurface
        if s.IsCylinder: out.append(round(s.CylinderParams[6]*1000,2))
    return sorted(out)
def rename(d, mapping):
    for old,new in mapping.items():
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(old,"BODYFEATURE",0,0,0,False,0,NOD,0):
            f=d.SelectionManager.GetSelectedObject6(1,-1); f.Name=new
    d.ClearSelection2(True)
def edges_of_face(face):
    """face의 모서리 중, 이웃 면이 평면이고 face와 수직인 것(=절곡 바깥 모서리) / 직선 판정"""
    out=[]
    n=[round(v,3) for v in face.GetSurface.PlaneParams[0:3]]
    for e in (pv(face,"GetEdges") or []):
        try:
            fa=pv(e,"GetTwoAdjacentFaces2")
        except Exception: continue
        other=None
        for f2 in fa:
            if f2 is not None and not f2.IsSame(face): other=f2
        if other is None: continue
        s2=other.GetSurface
        if not s2.IsPlane: continue
        n2=[round(v,3) for v in s2.PlaneParams[0:3]]
        if abs(sum(a*b for a,b in zip(n,n2)))<1e-3:
            p0=[v*1000 for v in pv(pv(e,"GetStartVertex"),"GetPoint")]; p1=[v*1000 for v in pv(pv(e,"GetEndVertex"),"GetPoint")]
            out.append((e, round(math.dist(p0,p1),1), [round(v,1) for v in p0],[round(v,1) for v in p1]))
    return out
def largest_planar(d, normal):
    b=(pv(d,"GetBodies2",0,True) or [])[0]; best=None
    for f in b.GetFaces():
        s=f.GetSurface
        if s.IsPlane and [round(v,2) for v in f.Normal]==normal and (best is None or f.GetArea>best.GetArea): best=f
    return best
def convert(d, fixed, bend_edges, rip_edges, t, r, expect, find=True, gap=0.0002):
    d.ClearSelection2(True)
    sd=d.SelectionManager.CreateSelectData; sd.Mark=1; ok=fixed.Select4(False,sd)
    for e in bend_edges:
        s2=d.SelectionManager.CreateSelectData; s2.Mark=2; ok=ok and e.Select4(True,s2)
    for e in rip_edges:
        s4=d.SelectionManager.CreateSelectData; s4.Mark=4; ok=ok and e.Select4(True,s4)
    v0=vol(d)
    f=d.FeatureManager.InsertConvertToSheetMetal2(t/1000.0,False,find,r/1000.0,gap,0,0.5,0,0.5,False); d.EditRebuild3
    v1=vol(d); res={"sel":ok,"feat":f.Name if f else None,"vol_before":v0,"vol_after":v1,"vol_expect":expect,"feats":feats(d),"whatswrong":ww(d),"cyl_r":cyls(d),"box":[round(v*1000,1) for v in pv(d,"GetPartBox",True)]}
    return f,res
def save(d,name):
    e=I4(); w_=I4(); ok=d.Save3(1,e,w_); print("SAVE",name,ok,e.value,w_.value); return ok

# ---------- J9b: 이미 변환됨(판금9/솔리드-변환4/전개도9) → 이름 정리 + 검증
P=os.path.join(Z,"J9b_rod_clevis_t6_44x40x60.SLDPRT"); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
rename(d,{"판금9":"판금1","솔리드-변환4":"솔리드-변환1","전개도9":"전개도1"}); d.EditRebuild3
log["J9b"]={"vol":vol(d),"vol_expect":45138,"feats":feats(d),"whatswrong":ww(d),"cyl_r":cyls(d),"box":[round(v*1000,1) for v in pv(d,"GetPartBox",True)]}
print("J9b",log["J9b"])
okJ9=(abs(log["J9b"]["vol"]-45138)<800 and not log["J9b"]["whatswrong"] and any(t=="SolidToSheetMetal" for _,t in log["J9b"]["feats"]))

# ---------- J8b: U 브래킷 t6, 박스 x0~136 y0~194 z-60~0. 고정면 = 바깥쪽 가장 큰 평면(어느 방향인지 탐색)
P=os.path.join(Z,"J8b_bent_U_bracket_t6_136x194x60.SLDPRT"); dd=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
b=(pv(d,"GetBodies2",0,True) or [])[0]; planes=[]
for f in b.GetFaces():
    s=f.GetSurface
    if s.IsPlane: planes.append((round(f.GetArea*1e6),[round(v,2) for v in f.Normal],[round(v*1000,1) for v in f.GetBox]))
planes.sort(reverse=True); print("J8b planes (top6)",planes[:6])
# 고정면 후보: 절곡 바깥 모서리가 정확히 2개 나오는 큰 평면
fixed=largest_planar(d,[0.0,1.0,0.0]); bends=None
if fixed is not None:
    E=edges_of_face(fixed); bends=[x for x in E if x[1]>=59 and abs(x[2][2]-x[3][2])>50]   # z방향 변
    if len(bends)!=2: bends=None
print("J8b fixed",[round(v*1000,1) for v in fixed.GetBox] if fixed else None,"bend edges",[(L,p0,p1) for _,L,p0,p1 in (bends or [])])
if fixed and bends:
    Lb=bends[0][1]; expect=183281-2*round((108-math.pi/4*108)*Lb)   # 날카로운 모서리→r6 굽힘 2곳
    f,res=convert(d,fixed,[x[0] for x in bends],[],6,6,expect); log["J8b"]=res; print("J8b",res)
    made=any(tt=="SolidToSheetMetal" for _,tt in res["feats"])
    if not made or abs(res["vol_after"]-expect)>1000 or res["whatswrong"]:
        print("J8b FAILED — 되돌림")
        for nm in [n for n,t in feats(d) if t=="SolidToSheetMetal"]:
            d.ClearSelection2(True); d.Extension.SelectByID2(nm,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0)
        d.EditRebuild3; log["J8b"]["reverted_vol"]=vol(d); okJ8=False
    else:
        sm=[n for n,t in feats(d) if t in ("SheetMetal","SolidToSheetMetal","FlatPattern")]
        rename(d,{n:{"SheetMetal":"판금1","SolidToSheetMetal":"솔리드-변환1","FlatPattern":"전개도1"}[t] for n,t in feats(d) if t in ("SheetMetal","SolidToSheetMetal","FlatPattern")}); d.EditRebuild3
        log["J8b"]["feats_renamed"]=feats(d); okJ8=True
else: okJ8=False

# ---------- S30008: 뚜껑 2T 500각, 테두리 25 아래로 4벽(모서리 겹침). 고정면 = 상면(y=2), 굽힘 = 상면 바깥 4변, 립 = 수직 모서리 4개
P=os.path.join(Z,"S30008MU0.SLDPRT"); dd=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
top=largest_planar(d,[0.0,1.0,0.0]); print("S30008 top box",[round(v*1000,1) for v in top.GetBox],"area",round(top.GetArea*1e6))
E=edges_of_face(top); print("S30008 top perpendicular edges",[(L,p0,p1) for _,L,p0,p1 in E])
bendE=[x[0] for x in E if x[1]>=499]
# 립 모서리: 수직(y방향) 길이 25~27, 바깥 코너(|x|=250,|z|=250)
b=(pv(d,"GetBodies2",0,True) or [])[0]; rips=[]
for e in b.GetEdges():
    try: p0=[v*1000 for v in pv(pv(e,"GetStartVertex"),"GetPoint")]; p1=[v*1000 for v in pv(pv(e,"GetEndVertex"),"GetPoint")]
    except Exception: continue
    if abs(p0[0]-p1[0])<0.01 and abs(p0[2]-p1[2])<0.01 and abs(p0[1]-p1[1])>20 and abs(abs(p0[0])-250)<0.05 and abs(abs(p0[2])-250)<0.05: rips.append((e,[round(v,1) for v in p0],[round(v,1) for v in p1]))
print("S30008 rip edges",[(p0,p1) for _,p0,p1 in rips])
okS8=False
if len(bendE)==4 and len(rips)==4:
    expect=599600-4*round((12-math.pi/4*12)*500)   # r2 굽힘 4곳(립·모서리 여유는 ±)
    ripE=[x[0] for x in rips]
    for label,be,re_,find,gap in (("bends+rips",bendE,ripE,True,0.0002),("bends only",bendE,[],True,0.0002),("bends+rips nofind",bendE,ripE,False,0.0002),("rips only find",[],ripE,True,0.0002),("bends+rips gap0.5",bendE,ripE,True,0.0005)):
        f,res=convert(d,top,be,re_,2,2,expect,find,gap); res["variant"]=label; log["S30008"]=res; print("S30008",label,res["vol_after"],[n for n,tt in res["feats"] if tt in ("SheetMetal","SolidToSheetMetal","FlatPattern")],res["whatswrong"],res["cyl_r"][:6])
        if any(tt=="SolidToSheetMetal" for _,tt in res["feats"]) and abs(res["vol_after"]-expect)<=3000 and not res["whatswrong"]: break
        for nm in [n for n,tt in feats(d) if tt=="SolidToSheetMetal"]:
            d.ClearSelection2(True); d.Extension.SelectByID2(nm,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0)
        d.EditRebuild3
    made=any(tt=="SolidToSheetMetal" for _,tt in res["feats"])
    if not made or abs(res["vol_after"]-expect)>3000 or res["whatswrong"]:
        print("S30008 FAILED — 되돌림")
        for nm in [n for n,t in feats(d) if t=="SolidToSheetMetal"]:
            d.ClearSelection2(True); d.Extension.SelectByID2(nm,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0)
        d.EditRebuild3; log["S30008"]["reverted_vol"]=vol(d)
    else:
        rename(d,{n:{"SheetMetal":"판금1","SolidToSheetMetal":"솔리드-변환1","FlatPattern":"전개도1"}[t] for n,t in feats(d) if t in ("SheetMetal","SolidToSheetMetal","FlatPattern")}); d.EditRebuild3
        log["S30008"]["feats_renamed"]=feats(d); okS8=True
log["ok"]={"J9b":okJ9,"J8b":okJ8,"S30008":okS8}
print("OK",log["ok"])
# ---------- 저장 (성공한 것만)
print("J9b already saved")
if okJ8: save(app.GetOpenDocumentByName(os.path.join(Z,"J8b_bent_U_bracket_t6_136x194x60.SLDPRT")),"J8b")
if okS8: save(app.GetOpenDocumentByName(os.path.join(Z,"S30008MU0.SLDPRT")),"S30008")
json.dump(log,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set()
