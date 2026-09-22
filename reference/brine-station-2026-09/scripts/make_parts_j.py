# Design J parts: lateral (Y) layout. Sketch on 정면 → extrude -Z (box z -t..0). Torus for the bowed hose (상승).
# usage: python make_parts_j.py fixplate movplate torus hosestraight
import os, math
from swconn import *
app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
RY=240.0; ACT_Y=300.0; OX=80.0
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
    elif mat in ("EPDM","SILICONE","PVC"): d.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber")
def save(d,name):
    p=os.path.join(Z,name)
    if os.path.exists(p): print("EXISTS skip",name); app.CloseDoc(d.GetTitle); return p
    e=I4(); wn=I4(); ok=d.Extension.SaveAs(p,0,1,NOD,e,wn); print("saved",ok,name,"err",e.value,"warn",wn.value); return p
def build(name,sk,thick,p):
    d=app.NewDocument(tmpl,0,0,0)
    try:
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); sk(d); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
        f=extrude(d,mm(thick)); b=d.GetPartBox(True)
        print(name,"feat",f.Name if f else None,"box",[round(v*1000,1) for v in b])
        props(d,p); d.EditRebuild3; return save(d,name)
    except Exception as ex:
        print("FAIL",name,ex); app.CloseDoc(d.GetTitle); raise
def build_torus(name,R,r,angle_deg,p):
    # circle centre (R,0) on 정면(XY), revolve about the Y axis -> arc in XZ plane starting at +X, start tangent -Z
    d=app.NewDocument(tmpl,0,0,0)
    try:
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True)
        circ(d,mm(R),0,mm(r))
        ln=d.SketchManager.CreateLine(0,mm(-R-r-10),0,0,mm(R+r+10),0); ln.ConstructionGeometry=True
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        ok1=d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
        ok2=False
        for nm in ("직선1@스케치1","Line1@Sketch1","직선1@Sketch1"):
            if d.Extension.SelectByID2(nm,"EXTSKETCHSEGMENT",0,0,0,True,16,NOD,0): ok2=True; break
        print("select sketch",ok1,"axis",ok2)
        f=d.FeatureManager.FeatureRevolve2(True,True,False,False,False,False,0,0,math.radians(angle_deg),0.0,False,False,0.0,0.0,0,0.0,0.0,True,True,True)
        b=d.GetPartBox(True); print(name,"revolve",f is not None,"box",[round(v*1000,1) for v in b])
        props(d,p); d.EditRebuild3; return save(d,name)
    except Exception as ex:
        print("FAIL",name,ex); app.CloseDoc(d.GetTitle); raise
which=sys.argv[1:]
if "fixplate" in which:
    def sk(d):
        rect(d,0,mm(65),mm(75),mm(355))            # x ±75, y -290..+420
        circ(d,0,0,mm(14.0))                        # 3/4in socket flow hole Ø28
        for y in (RY,-RY): circ(d,0,mm(y),mm(7.0))  # guide shaft M16 tap (pilot Ø14) at (0,±240)
    build("J1_fixed_plate_150x710_t10.SLDPRT",sk,10.0,{"TITLE":"FIXED MOUNT PLATE (가로배치)","SPEC":"150(X)x710(Y)x10 STS304, 호퍼 바닥 용접, 중앙 3/4in 소켓 Ø28, 가이드봉 M16 탭 2 (y±240), 우측(+Y 256~404) 아래 LA25 U브래킷 용접","Material":"STS304","REMARK":"정면 기준 좌우(Y)로 뻗음: -290(밸브모터측)~+420(실린더측). 신규 제작"})
if "movplate" in which:
    def sk(d):
        rect(d,mm(25),mm(20),mm(100),mm(310))       # x -75..+125, y -290..+330
        circ(d,mm(OX),0,mm(17.0))                   # 3/4in socket through-hole Ø34 at (80,0)
        for y in (RY,-RY):
            circ(d,0,mm(y),mm(14.25))               # LHFRW16 body Ø28.5
            for a in (45,135,225,315): circ(d,mm(19.5*math.cos(math.radians(a))),mm(y+19.5*math.sin(math.radians(a))),mm(2.75))
        circ(d,0,mm(ACT_Y),mm(20.0))                # LA25 rod pass Ø40 at (0,300)
    build("J5_moving_plate_200x620_t10.SLDPRT",sk,10.0,{"TITLE":"MOVING PLATE (가로배치)","SPEC":"200(X)x620(Y)x10 STS304, 소켓 Ø34 (x80,y0), 리니어부시 LHFRW16 x2 (y±240), LA25 로드 Ø40 (y300)","Material":"STS304","REMARK":"정면 기준 좌우(Y) -290~+330. 출구는 뒤(+X)로 80 오프셋(호스 굽힘 공간). 신규 제작"})
if "torus" in which:
    build_torus("J19_hose_3-4in_arc_R59_223deg.SLDPRT",59.0,14.0,223.0,{"TITLE":"HOSE 3/4in (상승 상태 굽힘, 근사)","SPEC":"3/4in ID19/OD28 연질 내염수·내한 호스 — 상승 시 굽힘반경 59, 호 223° (근사)","QT'Y":"0","Material":"EPDM","REMARK":"호스 1본의 상승 상태 형상 근사(양단 각도 근사). 구매 QT'Y는 J19_straight 쪽 1"})
if "hosestraight" in which:
    L=round(math.hypot(OX,214.0))   # chord in 하강: (0,-148)->(80,-362)
    def sk(d): circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5))
    build("J19_hose_3-4in_straight_L%d.SLDPRT"%L,sk,float(L),{"TITLE":"HOSE 3/4in (하강 상태, 직선 근사)","SPEC":"3/4in ID19/OD28 연질 내염수·내한 호스, 자유길이 %d + 니플 삽입 2x20 = 전장 약 %d, 최소 굽힘반경 60 이하 제품(실리콘/연질PVC)"%(L,L+40),"QT'Y":"1","Material":"EPDM","REMARK":"호스밴드 2개 별도"})
