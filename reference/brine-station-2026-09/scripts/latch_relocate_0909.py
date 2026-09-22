# 2026-09-09: 걸쇠 C-1170-2(표付用角ラッチ = 표면 취부 각 슬라이드 볼트, 카탈로그 20865: L1 50·W1 38·P1 34·P2 25·4×M3 皿穴 / 받이 L2 12·W3 39·P3 29·2×M3 / 스트로크 12.5·H2 11.5·H3 12)
#  사용자: 걸쇠는 뚜껑과 같이 열리면 안 됨 → 본체를 탱크 쪽 패드 S30017에, 받이(키퍼)는 뚜껑에.
#  1) 패드 S30017 40×30×30 → 40×70×30 (z −560~−490, 상면 840 유지)
#  2) 걸쇠 본체: 180° 돌려 볼트가 +z(뚜껑 쪽)로 나가게, 본체 z −560~−510(중심 −535). STEP 볼트 돌출 20 = 후퇴 상태로 가정 → 후퇴 끝 −490(뚜껑 테두리 −487.5에서 2.5 여유), 전진 끝 −477.5
#  3) 패드 상면 4×M3 탭(Ø2.5 깊이 8) @ x 237.5±12.5(P2 25), z −535±17(P1 34)
#  4) 뚜껑 상면 받이 홀 2×Ø3.4 관통 @ x 237.5±14.5(P3 29), z −481 (받이 z −487~−475, 전진 볼트 물림 9.5)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect(); mm=lambda v:v/1000.0
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
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<tol: out.append([round(v*1000,1) for v in fc.GetBox])
    return out
def partbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def dims_of(d,featname):
    f=d.FeatureByName(featname); out=[]
    dd=pv(f,"GetFirstDisplayDimension")
    while dd:
        dim=dd.GetDimension2(0); out.append((dim.FullName,round(dim.SystemValue*1000,3))); dd=pv(f,"GetNextDisplayDimension",dd)
    return out
def sel_face_at(d,x,y,z):
    d.ClearSelection2(True); return d.Extension.SelectByID2("","FACE",mm(x),mm(y),mm(z),False,0,NOD,0)
def cut_on_face(d,face_pt,pts,r,name,through,depth=0.0):
    ok=sel_face_at(d,*face_pt); assert ok,"face select failed"
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    for (x,y) in pts: sm.CreateCircleByRadius(mm(x),mm(y),0.0,mm(r))
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch(d); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    if through: f=d.FeatureManager.FeatureCut4(True,False,False,1,0,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False)
    else: f=d.FeatureManager.FeatureCut4(True,False,False,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False)
    d.EditRebuild3
    if f: f.Name=name
    return f
def delete_feat(d,name):
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0): d.EditDelete(); d.EditRebuild3
# ---------- 1) 패드 S30017 길이 30→70 (z)
P=os.path.join(Z,"S30017MU0.SLDPRT"); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
print("pad box before",partbox(d),"dims",dims_of(d,"보스-돌출1"))
b0=partbox(d)
if abs(b0[5]-b0[2]-70)>0.1:
    changed=False
    for nm,val in dims_of(d,"보스-돌출1"):
        if abs(val-30)<0.01:
            prm=d.Parameter(nm.split("@")[0]+"@"+nm.split("@")[1]); old=prm.SystemValue; prm.SystemValue=mm(70); d.EditRebuild3; b=partbox(d)
            print("  try",nm,"->70 box",b)
            if abs(b[5]-b[2]-70)<0.1 and abs(b[3]-b[0]-40)<0.1 and abs(b[4]-b[1]-30)<0.1: changed=True; break
            prm.SystemValue=old; d.EditRebuild3
    assert changed,"pad length edit failed"
print("pad box after",partbox(d))
bp=partbox(d)   # z 0~70 예상
# 3) 패드 상면 탭홀 4×Ø2.5 깊이 8: 상면 y=30, 로컬 좌표 (x, z): 본체 중심 로컬 z = 35 (월드 −535 = t z −560 + 35 → 컴포넌트 t z를 −560으로 옮길 것)
if d.FeatureByName("걸쇠_4-M3탭_D2.5") is None:
    pts=[(x,zz) for x in (-12.5,12.5) for zz in (35-17,35+17)]
    done=False
    for sy in (1,-1):
        p2=[(x,sy*zz) for x,zz in pts]
        f=cut_on_face(d,(0.0,30.0,35.0),p2,1.25,"걸쇠_4-M3탭_D2.5",False,8.0)
        c=cyls(d,1.25); ok=len(c)==4 and all(abs(b[4]-30)<0.6 and abs(b[1]-22)<0.6 for b in c) and all(any(abs((b[2]+b[5])/2-zz)<0.6 for zz in (18,52)) for b in c)
        print(f"  pad holes sy={sy}: n={len(c)} ok={ok} {c[:2]}")
        if ok: done=True; break
        if f: delete_feat(d,f.Name)
    assert done,"pad holes failed"
cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("SPEC","STS 316 40x70x30 블록, 상판 S30006 위 용접(걸쇠 C-1170-2 본체 받침, 상면 = 뚜껑 상면 높이). 4×M3 탭 P1 34×P2 25")
cpm.Set2("REMARK",(cpm.Get("REMARK") or "")+" | 2026-09-09 걸쇠 본체를 패드에 올리며 길이 30→70, M3 탭 4개")
# ---------- 4) 뚜껑 S30008 받이 홀 2×Ø3.4 관통 @ 로컬 (x ±14.5, z −243.5)
P=os.path.join(Z,"S30008MU0.SLDPRT"); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
if d.FeatureByName("걸쇠받이홀_2-D3.4") is None:
    done=False
    for sz in (-1,1):
        d.ClearSelection2(True); ok=d.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0); assert ok,"top plane"
        d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
        for (x,zz) in ((-14.5,sz*243.5),(14.5,sz*243.5)): sm.CreateCircleByRadius(mm(x),mm(zz),0.0,mm(1.7))
        sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=last_sketch(d); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
        if f: f.Name="걸쇠받이홀_2-D3.4"
        c=cyls(d,1.7); ok=len(c)==2 and all(abs(b[1]-0)<0.6 and abs(b[4]-2)<0.6 and abs((b[2]+b[5])/2+243.5)<0.6 for b in c)
        print(f"  lid keeper holes sz={sz}: n={len(c)} ok={ok} {c}")
        if ok: done=True; break
        if f: delete_feat(d,f.Name)
    assert done,"lid keeper holes failed"
cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("REMARK",(cpm.Get("REMARK") or "")+" | 2026-09-09 걸쇠 C-1170-2 받이 홀 2-Ø3.4 (x ±14.5, 테두리에서 6.5)")
# ---------- 2) 어셈블리: 패드 t z −560, 걸쇠 회전·이동
PT=os.path.join(Z,"S30000MU0.SLDASM"); a=app.GetOpenDocumentByName(PT); app.ActivateDoc3(PT,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
R_PAD=[[1,0,0],[0,1,0],[0,0,1]]; T_PAD=(237.5,810.0,-560.0)
R_LATCH=[[0,0,1],[1,0,0],[0,1,0]]; T_LATCH=(237.5,840.0,-535.0)
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    move_fixed(cc["S30017MU0-1"],R_PAD,T_PAD); move_fixed(cc["C-1170-2S_latch-1"],R_LATCH,T_LATCH); a.ForceRebuild3(False); cc=comps()
    print(f" [{cfg}] pad box={box(cc['S30017MU0-1'])} latch box={box(cc['C-1170-2S_latch-1'])}")
# 검증: 상승(닫힘)·뚜껑열림 간섭
for cfg in ("상승","뚜껑열림"):
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); a.ClearSelection2(True)
    lid=[n for n in cc if n.startswith("S30008MU0-") and cc[n].GetSuppression2==2]
    for n in lid+["C-1170-2S_latch-1","S30017MU0-1","S30006MU0-1","S30007MU0-2","S30012MU0-1","C-HHSN65A_hinge-1","C-HHSN65A_hinge-2"]: cc[n].Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True)
    print(f" [{cfg}] 간섭:",rows)
# 홀 월드 좌표 확인
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
def RT(comp):
    A=list(comp.Transform2.ArrayData); return [A[0:3],A[3:6],A[6:9]],[v*1000 for v in A[9:12]]
def w(R,t,p): return [round(t[i]+p[0]*R[0][i]+p[1]*R[1][i]+p[2]*R[2][i],1) for i in range(3)]
for n,r in (("S30017MU0-1",1.25),("S30008MU0-5",1.7)):
    c=cc[n]; R,t=RT(c); pts=[]
    for fc in c.GetBody.GetFaces():
        s=fc.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05: pts.append(w(R,t,[v*1000 for v in s.CylinderParams[0:3]]))
    print(f" {n} r={r} 홀 축점(월드):",sorted(pts))
stop.set(); print("done; NOT saved (S30017, S30008, S30000MU0)")
