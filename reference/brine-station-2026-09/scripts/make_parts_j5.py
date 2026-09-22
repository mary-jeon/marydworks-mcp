# J5 parts (2026-09-08 오후): 호스를 do88 F19(19 mm, 최소 굽힘반경 47)로 확정 → 세로여유 확보를 위해
#  (1) 소켓 2개를 판 구멍(Ø34)에 삽입해 상면 플러시 (고정판 J1c 구멍 Ø28→Ø34, 이동판 J5d는 이미 Ø34)
#  (2) 출구 오프셋 OX 80→100 (J5d 소켓 구멍 (100,0), 판 X -110~+130)
#  (3) 호스 J19c: 상승 스윕(r47, G 212, OX 100, L 365.9) + 하강 직선 L366. 단면 OD 28.2 / ID 19 (do88 벽 4.6).
# J1c·J5d는 열려 있는 파트의 피처를 지우고 같은 파일에 다시 만든다(어셈 참조 유지). usage: python make_parts_j5.py plates hoses
import os, math, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
AX=-70.0; RY=240.0; OX=100.0; G_UP=212.0; STROKE=140.0; R_HOSE=47.0
L_HOSE=math.hypot(OX,G_UP+STROKE)   # 365.9
def sel_plane(d,names):
    for nm in names:
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def circ(d,x,y,r): d.SketchManager.CreateCircleByRadius(x,y,0.0,r)
def rect(d,cx,cy,hx,hy): d.SketchManager.CreateCenterRectangle(cx,cy,0,cx+hx,cy+hy,0)
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def cyls(d,r):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
                bx=[round(v*1000,1) for v in fc.GetBox]; out.append((round((bx[0]+bx[3])/2,1),round((bx[1]+bx[4])/2,1)))
    return sorted(out)
def props(d,p):
    cpm=d.Extension.CustomPropertyManager("")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
def rebuild_plate(path,sk,thick,p,check):
    d=app.GetOpenDocumentByName(path); app.ActivateDoc3(path,False,0,I4()); d=app.ActiveDoc
    d.ClearSelection2(True)
    ok=d.Extension.SelectByID2("보스-돌출1","BODYFEATURE",0,0,0,False,0,NOD,0); print(os.path.basename(path),"del boss",ok,d.Extension.DeleteSelection2(1))
    d.ClearSelection2(True); d.EditRebuild3
    sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; sk(d); d.SketchManager.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(thick),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    d.EditRebuild3; b=[round(v*1000,1) for v in pv(d,"GetPartBox",True)]; print("  box",b)
    for r,expect in check:
        got=cyls(d,r); exp=sorted(expect); ok=len(got)==len(exp) and all(abs(a[0]-b_[0])<0.2 and abs(a[1]-b_[1])<0.2 for a,b_ in zip(got,exp))
        print(f"  Ø{2*r} {got} {'OK' if ok else 'MISMATCH '+str(exp)}")
        if not ok: raise RuntimeError("hole check failed "+path)
    props(d,p); d.EditRebuild3
which=sys.argv[1:]
if "plates" in which:
    BOLTS=[(55,25),(-55,25),(55,-25),(-55,-25)]
    def sk1(d):
        rect(d,mm(-17.5),0,mm(92.5),mm(290)); circ(d,0,0,mm(17.0))
        for (x,y) in BOLTS: circ(d,mm(x),mm(y),mm(4.5))
        for y in (RY,-RY): circ(d,mm(AX),mm(y),mm(7.0))
    rebuild_plate(os.path.join(Z,"J1c_fixed_plate_185x580_t10.SLDPRT"),sk1,10.0,
        {"SPEC":"185(X -110~75)x580(Y ±290)x10 STS304. 소켓 삽입구멍 Ø34(0,0: 용접소켓 G13 OD34 삽입, 상면 플러시, 밑면 필릿용접), 볼트 4-Ø9 @(±55,±25), 가이드봉 M16 탭 관통 2개소 @(-70,±240) (드릴 Ø14 = 모델 구멍)",
         "REMARK":"2026-09-08 J5: 소켓 플러시 삽입(고정 스택 +10). 가이드봉 MISUMI PSSFAQ16-590-B10 = 한쪽 수나사·나사경=축경(M16)·나사길이 B10 → 판 두께 10에 M16 탭으로 체결(나사풀림 방지제). 상면은 EPDM 가스켓 S30016 아래, M8x25+PW+SW 4본"},
        check=[(17.0,[(0,0)]),(4.5,BOLTS),(7.0,[(AX,RY),(AX,-RY)])])
    bore=[(AX,RY),(AX,-RY)]; taps=[(AX+dx,y+dy) for y in (RY,-RY) for (dx,dy) in ((19,0),(-19,0),(0,19),(0,-19))]
    def sk2(d):
        rect(d,mm(10),0,mm(120),mm(270)); circ(d,mm(OX),0,mm(17.0))
        for (x,y) in bore: circ(d,mm(x),mm(y),mm(14.25))
        for (x,y) in taps: circ(d,mm(x),mm(y),mm(1.65))
    rebuild_plate(os.path.join(Z,"J5d_moving_plate_220x540_t8.SLDPRT"),sk2,8.0,
        {"SPEC":"240(X -110~130)x540(Y ±270)x8 STS304. 소켓 삽입구멍 Ø34 (100,0: 용접소켓 삽입 상면 플러시), 리니어부시 LHFRW16 x2 (-70,±240) 보어 Ø28.5 + M4 탭 4개소 십자 PCD38, 상면 (-70,0) 로드 클레비스 J9b 용접",
         "REMARK":"2026-09-08 J5: 출구 오프셋 80→100(호스 r47 여유), 소켓 플러시(이동 스택 -15). 파일명의 220은 구치수 — 실제 폭 240. t8 근거: 900N 걸림 M 108 N·m/단면 206x8 → 49 MPa(가정 손계산)"},
        check=[(17.0,[(OX,0)]),(14.25,bore),(1.65,taps)])
# ---------------- hoses
def hose_segments(r,a1,a2,R,t,s=20.0):
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    def st(dd):
        nonlocal x,y
        if dd<=1e-9: return
        x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1
    def arc(rad,ang):
        nonlocal x,y,h
        if abs(ang)<1e-9: return
        side=1 if ang>0 else -1
        cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
        h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
        segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    st(s); arc(r,a1); st(t); arc(R,-(a1+a2)); st(t); arc(r,a2); st(s)
    return segs,(x,y)
def path_len(segs):
    return sum((math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1]) if sg[0]=="line" else abs(sg[4])*math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1])) for sg in segs)
def solve_hose(r):
    import random
    D,X,L=G_UP,OX,L_HOSE
    def sc(p):
        a1,a2,R,t=p
        if R<r or t<0 or a1<0 or a1+a2<=0.02: return 1e6
        segs,(ex,ey)=hose_segments(r,a1,a2,R,t); return math.hypot(ex-X,ey+D)+abs(path_len(segs)-L)
    rnd=random.Random(3); best=(1e9,None)
    for _ in range(300):
        p=[rnd.uniform(0.3,3.0),rnd.uniform(-1.0,3.0),r*rnd.uniform(1.0,3.0),rnd.uniform(0,D)]
        v=sc(p); step=[0.2,0.2,r*0.3,max(10.0,D/8)]
        while step[0]>1e-6:
            imp=False
            for i in range(4):
                for dd in (1,-1):
                    q=list(p); q[i]+=dd*step[i]; vq=sc(q)
                    if vq<v: v,p=vq,q; imp=True
            if not imp: step=[u/2 for u in step]
        if v<best[0]: best=(v,p)
        if best[0]<0.05: break
    return best
def save_new(d,name):
    p=os.path.join(Z,name)
    if os.path.exists(p): print("EXISTS skip",name); app.CloseDoc(d.GetTitle); return p
    e=I4(); wn=I4(); ok=d.Extension.SaveAs(p,0,1,NOD,e,wn); print("saved",ok,name,e.value,wn.value); return p
if "hoses" in which:
    v,(a1,a2,R,t)=solve_hose(R_HOSE); segs,end=hose_segments(R_HOSE,a1,a2,R,t)
    print(f"hose up: resid {v:.3f} a1 {math.degrees(a1):.1f} a2 {math.degrees(a2):.1f} R {R:.1f} t {t:.1f} end {end} L {L_HOSE:.1f}")
    json.dump({"r":R_HOSE,"a1":a1,"a2":a2,"R":R,"t":t,"resid":v,"L":L_HOSE,"G":G_UP,"OX":OX,"end":end,"segments":segs},open(os.path.join(VER,"J5_hose_path.json"),"w"),indent=1)
    name_up="J19c_hose_3-4in_up_r47.SLDPRT"
    if not os.path.exists(os.path.join(Z,name_up)):
        done=False
        for direction in (1,-1):
            d=app.NewDocument(tmpl,0,0,0)
            try:
                sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
                for sg in segs:
                    if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0)
                    else:
                        c,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]
                        sm.CreateArc(mm(c[0]),mm(c[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
                sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
                skf=d.FeatureByName("스케치1") or d.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
                segs_sw=sk.GetSketchSegments
                if callable(segs_sw): segs_sw=segs_sw()
                Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in segs_sw)*1000
                print(f"  direction={direction}: sketch length {Ls:.1f} (target {L_HOSE:.1f})")
                if abs(Ls-L_HOSE)>2.0: app.CloseDoc(d.GetTitle); continue
                sel_plane(d,("윗면","Top Plane")); d.SketchManager.InsertSketch(True); circ(d,0,0,mm(14.1)); circ(d,0,0,mm(9.5)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
                d.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or d.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
                d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
                f=None
                for attempt in ("swept3","swept4"):
                    try:
                        if attempt=="swept3": f=d.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                        else: f=d.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                        if f: break
                    except Exception as ex: print("  ",attempt,"exception",ex)
                b=[round(v_*1000,1) for v_ in d.GetPartBox(True)]; print("  hose up box",b)
                if not f: raise RuntimeError("sweep failed")
                props(d,{"TITLE":"HOSE 3/4in (상승 상태 굽힘)","SPEC":f"do88 F19 Silicone Hose Blue Flexible 3/4\" (ID19, 벽 4.6, 최소 굽힘반경 47, -40~+180 ℃, 3겹 와이어 보강) — 상승 시 굽힘 {R_HOSE:.0f}/{R:.0f}, 자유길이 {L_HOSE:.0f}","QT'Y":"0","Material":"SILICONE","DATE":"2026-09-08","REMARK":"호스 1본의 상승 상태 형상(양단 수직, 경로 추적 해 _검증\\J5_hose_path.json). 구매 QT'Y는 straight 쪽 1. 원문: do88performance.com Article nr F19 (2026-09-08 확인)"})
                d.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber"); d.EditRebuild3
                save_new(d,name_up); done=True; break
            except Exception as ex:
                print("FAIL up hose",ex); app.CloseDoc(d.GetTitle); raise
        if not done: raise SystemExit("hose up sketch length mismatch both directions")
    else: print("exists",name_up)
    L=round(L_HOSE); name_st=f"J19c_hose_3-4in_straight_L{L}.SLDPRT"
    if not os.path.exists(os.path.join(Z,name_st)):
        d=app.NewDocument(tmpl,0,0,0)
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); circ(d,0,0,mm(14.1)); circ(d,0,0,mm(9.5)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(float(L)),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
        d.EditRebuild3; print("straight box",[round(v_*1000,1) for v_ in d.GetPartBox(True)])
        props(d,{"TITLE":"HOSE 3/4in (하강 상태, 직선)","SPEC":f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 자유길이 {L} + 니플 삽입 2x20 = 절단 약 {L+40}, 최소 굽힘반경 47, -40~+180 ℃","QT'Y":"1","Material":"SILICONE","DATE":"2026-09-08","REMARK":"호스밴드 2개 별도(ID19용). 원문: do88performance.com Article nr F19, USD 85.83/1000 mm (2026-09-08 확인)"})
        d.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber"); d.EditRebuild3
        save_new(d,name_st)
    else: print("exists",name_st)
stop.set()
