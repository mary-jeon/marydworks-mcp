# J3 parts: 6T LA25 U-bracket with pin holes, 6T clevis on the moving plate, clevis pin, moving plate without Ø40 hole.
# 우측면 sketch mapping (실측 2026-09-07): sketch (sx,sy) -> model (Y=sy, Z=-sx); 정면-extruded parts occupy z -depth..0.
# usage: python make_parts_j3.py bracket clevis pin movplate
import os, math
from swconn import *
app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
RY=240.0; RX=60.0; ACT_Y=300.0; OX=80.0
def sel_plane(d,names):
    for nm in names:
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def extrude(d,depth):
    return d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,depth,0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
def circ(d,x,y,r): d.SketchManager.CreateCircleByRadius(x,y,0.0,r)
def rect(d,cx,cy,hx,hy): d.SketchManager.CreateCenterRectangle(cx,cy,0,cx+hx,cy+hy,0)
def props(d,p):
    cpm=d.Extension.CustomPropertyManager(""); p.setdefault("DATE","2026-09-07"); p.setdefault("QT'Y","1")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
    mat=p.get("Material","STS304")
    if mat.startswith("STS"): d.SetMaterialPropertyName2("","이텍","STS 316" if "316" in mat else "STS 304")
def save(d,name):
    p=os.path.join(Z,name)
    if os.path.exists(p): print("EXISTS skip",name); app.CloseDoc(d.GetTitle); return p
    e=I4(); wn=I4(); ok=d.Extension.SaveAs(p,0,1,NOD,e,wn); print("saved",ok,name,"err",e.value,"warn",wn.value); return p
def nfaces(d):
    return sum(len(b.GetFaces()) for b in (d.GetBodies2(0,True) or []))
def cut_hole_x(d,z_model,y_model,r,sketch_name):
    """Through-all hole along model X: circle on 우측면 at (sx=-z, sy=y)."""
    sel_plane(d,("우측면","Right Plane")); d.SketchManager.InsertSketch(True)
    circ(d,mm(-z_model),mm(y_model),mm(r)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    ok=d.Extension.SelectByID2(sketch_name,"SKETCH",0,0,0,False,0,NOD,0)
    n0=nfaces(d)
    # FeatureCut3: Sd, Flip, Dir(both), T1=ThroughAll(1), T2=ThroughAll(1), ...
    f=d.FeatureManager.FeatureCut3(True,False,True,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
    n1=nfaces(d); print(f"  cut {sketch_name}: sel={ok} feat={f.Name if f else None} faces {n0}->{n1}")
    if not f or n1<=n0: raise RuntimeError("pin hole cut failed")
def build(name,sk,thick,p,holes=()):
    d=app.NewDocument(tmpl,0,0,0)
    try:
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); sk(d); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
        f=extrude(d,mm(thick)); b=d.GetPartBox(True)
        print(name,"feat",f.Name if f else None,"box",[round(v*1000,1) for v in b])
        for i,(zc,yc,r) in enumerate(holes): cut_hole_x(d,zc,yc,r,"스케치%d"%(i+2))
        props(d,p); d.EditRebuild3; return save(d,name)
    except Exception as ex:
        print("FAIL",name,ex); app.CloseDoc(d.GetTitle); raise
which=sys.argv[1:]
if "bracket" in which:
    T=6.0; HB=194.0; W=136.0
    def sk(d):
        pts=[(0,0),(T,0),(T,HB-T),(W-T,HB-T),(W-T,0),(W,0),(W,HB),(0,HB),(0,0)]
        for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
    build("J8b_bent_U_bracket_t6_136x194x60.SLDPRT",sk,60.0,{"TITLE":"LA25 REAR U-BRACKET (절곡 1장)","SPEC":"STS304 t6 절곡, 폭 60, 다리 내측 124(LA25 하우징 116 + 4/4), 높이 194, 핀홀 Ø10.5 @69 양측 관통","Material":"STS304","REMARK":"고정판 밑면 용접. 핀 지압응력 2,500N/(2×10×6)=21 MPa (STS304 항복 205) — 12T→6T 변경 근거"},holes=[(-30.0,69.0,5.25)])
if "clevis" in which:
    T=6.0; G=30.0; H=40.0; W=G+2*T
    def sk(d):
        pts=[(0,0),(W,0),(W,H),(W-T,H),(W-T,T),(T,T),(T,H),(0,H),(0,0)]
        for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
    build("J9_rod_clevis_t6_42x40x60.SLDPRT",sk,60.0,{"TITLE":"LA25 ROD CLEVIS (절곡 1장)","SPEC":"STS304 t6 절곡 U, 내측 30(로드 아이 폭 가정 ≤28 — LINAK 도면 확인), 높이 40, 폭 60, 핀홀 Ø10.5 @25 양측 관통","Material":"STS304","REMARK":"이동판 상면(x0,y300) 용접. LA25 로드 아이 핀 결합"},holes=[(-30.0,25.0,5.25)])
if "pin" in which:
    def sk(d): circ(d,0,0,mm(5.0))
    build("J11_clevis_pin_d10_L70.SLDPRT",sk,70.0,{"TITLE":"CLEVIS PIN (로드측)","SPEC":"Ø10 x 70 STS304, 스냅링 홈 양단(미모델)","Material":"STS304"})
if "movplate" in which:
    def sk(d):
        rect(d,mm(25),mm(20),mm(100),mm(310))
        circ(d,mm(OX),0,mm(17.0))
        for y in (RY,-RY):
            circ(d,mm(RX),mm(y),mm(14.25))
            for a in (45,135,225,315): circ(d,mm(RX+19.5*math.cos(math.radians(a))),mm(y+19.5*math.sin(math.radians(a))),mm(2.75))
    build("J5c_moving_plate_200x620_t10.SLDPRT",sk,10.0,{"TITLE":"MOVING PLATE (가로배치)","SPEC":"200(X)x620(Y)x10 STS304, 소켓 Ø34 (x80,y0), 리니어부시 LHFRW16 x2 (x60,y±240), 상면 (x0,y300) 로드 클레비스 용접","Material":"STS304","REMARK":"정면 기준 좌우(Y) -290~+330. 출구 뒤(+X) 80 오프셋. 신규 제작"})
