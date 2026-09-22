# 2026-09-09: 경첩 C-HHSN65A 취부 홀을 뚜껑 S30008(+z 플랜지, 리프1 홀 Ø4.5 ×3/경첩 → 6개 관통)과 상판 S30006(리프2 자리, M4 탭 = Ø3.3 ×6)에 뚫는다.
# 위치(월드, 탱크 좌표): 리프1 홀 x 142/165/188 · 287/310/333, y 829.25 (STEP 실측). 리프2 홀은 STEP에 없어 핀축(y 814.25·z 16.75)에서 리프1과 같은 15 → z 31.75 (가정).
# 제자리 편집: 기존 파트에 컷 피처 추가(스케치 삭제·재생성 없음). 저장은 sw_save.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect(); mm=lambda v:v/1000.0
HX=[142.0,165.0,188.0,287.0,310.0,333.0]; HY=829.25; HZ2=31.75
def sel_plane(d,names):
    for nm in names:
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def cyls(d,r,tol=0.05):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<tol:
                bx=[round(v*1000,1) for v in fc.GetBox]; out.append(bx)
    return out
def cut_circles(d,plane_names,pts,r,name,flip,dirn=False):
    sel_plane(d,plane_names); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    for (x,y) in pts: sm.CreateCircleByRadius(mm(x),mm(y),0.0,mm(r))
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch(d); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    # FeatureCut4(Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2, OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2, NormalCut, UseFeatScope, UseAutoSelect, AssemblyFeatureScope, AutoSelectComponents, PropagateFeatureToParts, T0, StartOffset, FlipStartOffset, OptimizeGeometry)
    f=d.FeatureManager.FeatureCut4(True,flip,dirn,1,0,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False)  # T1=1 ThroughAll
    d.EditRebuild3
    if f: f.Name=name
    return f
# ---------- 뚜껑 S30008: 정면(XY) 스케치, +z 방향 관통 → +z 플랜지(z 248~250)만
P=os.path.join(Z,"S30008MU0.SLDPRT"); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
bad=d.FeatureByName("경첩홀_6-D4.5")
if bad is not None and not all(abs(b[5]-250)<0.6 for b in cyls(d,2.25)):
    d.ClearSelection2(True); d.Extension.SelectByID2("경첩홀_6-D4.5","BODYFEATURE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3; print(" S30008 잘못된 홀 피처 삭제")
if d.FeatureByName("경첩홀_6-D4.5") is None:
    pts=[(x-237.5, HY-838.0) for x in HX]
    for flip,dirn in ((False,True),(True,True),(False,False)):
        f=cut_circles(d,("정면","Front Plane"),pts,2.25,"경첩홀_6-D4.5",flip,dirn)
        c=cyls(d,2.25); ok=len(c)==6 and all(abs(b[2]-248)<0.6 and abs(b[5]-250)<0.6 for b in c)
        print(f" S30008 flip={flip} dir={dirn}: cut {f.Name if f else None} cyl r2.25 n={len(c)} ok={ok} {c[:2]}")
        if ok: break
        if f: d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3
    assert ok, "lid holes wrong side"
else: print(" S30008 홀 이미 있음")
cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("REMARK",(cpm.Get("REMARK") or "")+" | 2026-09-09 경첩 C-HHSN65A 리프1 취부홀 6-Ø4.5 (+z 플랜지, 뚜껑 상면 아래 10.75)")
print(" S30008 body box",[round(v*1000,1) for v in pv(d,"GetPartBox",True)])
# ---------- 상판 S30006: 정면(XY) 스케치(z=0 상면), -z 방향 관통 → 5T 판. 로컬 x = -월드x, 로컬 y = 월드z
P=os.path.join(Z,"S30006MU0.SLDPRT"); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
if d.FeatureByName("경첩홀_6-M4탭_D3.3") is None:
    pts=[(-x, HZ2) for x in HX]
    for flip,dirn in ((False,False),(False,True),(True,False)):
        f=cut_circles(d,("정면","Front Plane"),pts,1.65,"경첩홀_6-M4탭_D3.3",flip,dirn)
        c=cyls(d,1.65); ok=len(c)==6 and all(abs(b[2]+5)<0.6 and abs(b[5]-0)<0.6 for b in c)
        print(f" S30006 flip={flip} dir={dirn}: cut {f.Name if f else None} cyl r1.65 n={len(c)} ok={ok} {c[:2]}")
        if ok: break
        if f: d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3
    assert ok, "top plate holes wrong"
else: print(" S30006 홀 이미 있음")
cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("REMARK",(cpm.Get("REMARK") or "")+" | 2026-09-09 경첩 리프2 취부 M4 탭 6개(Ø3.3, 핀축에서 15 = z 31.75 가정)")
# ---------- 어셈블리 확인
PT=os.path.join(Z,"S30000MU0.SLDASM"); a=app.GetOpenDocumentByName(PT); app.ActivateDoc3(PT,False,0,I4()); a=app.ActiveDoc; a.ForceRebuild3(False)
cm=a.ConfigurationManager; cc={c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def RT(comp):
    A=list(comp.Transform2.ArrayData); return [A[0:3],A[3:6],A[6:9]],[v*1000 for v in A[9:12]]
def w(R,t,p): return [round(t[i]+p[0]*R[0][i]+p[1]*R[1][i]+p[2]*R[2][i],2) for i in range(3)]
for n,r in (("S30008MU0-5",2.25),("S30006MU0-1",1.65)):
    c=cc[n]; R,t=RT(c); pts=[]
    for fc in c.GetBody.GetFaces():
        s=fc.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
            o=[v*1000 for v in s.CylinderParams[0:3]]; pts.append(w(R,t,o))
    print(f" {n} 홀 r={r} 월드 축점(축 방향 성분 무시):",sorted([(round(p[0],1),round(p[1],1),round(p[2],1)) for p in pts]))
stop.set(); print("done; NOT saved")
