# Design H parts: in-line socket→hose nipple→hose→hose nipple→socket→plate→pipe, moving outlet offset 80 back, hose bows.
import sys, os, math, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
NOD=VARIANT(pythoncom.VT_DISPATCH,None); I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
OUT=r"<CAD_DIR>"
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
def sel_plane(d,names):
    for nm in names:
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def extrude(d,depth):
    return d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,depth,0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
def circ(d,x,y,r): d.SketchManager.CreateCircleByRadius(x,y,0.0,r)
def rect(d,cx,cy,hx,hy): d.SketchManager.CreateCenterRectangle(cx,cy,0,cx+hx,cy+hy,0)
def props(d,p):
    cpm=d.Extension.CustomPropertyManager(""); p.setdefault("DATE","2026-09-03"); p.setdefault("QT'Y","1")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
    mat=p.get("Material","STS304")
    if mat.startswith("STS"): d.SetMaterialPropertyName2("","이텍","STS 316" if "316" in mat else "STS 304")
    elif mat in ("EPDM","SILICONE","PVC"): d.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber")
def save(d,name):
    p=os.path.join(OUT,name)
    if os.path.exists(p): print("EXISTS skip",name); return p
    e=I4(); wn=I4(); ok=d.Extension.SaveAs(p,0,1,NOD,e,wn); print("saved",ok,name); return p
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
    # sketch on 정면 (XY): circle centre (R,0) radius r ; revolve about the Y axis (construction line x=0) by angle -> arc in XZ plane starting at +X
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
RX=300; RY=60; ACT_X=380; OX=80
if "torus" in which:
    build_torus("H19_hose_3-4in_arc_R59_223deg.SLDPRT",59.0,14.0,223.0,{"TITLE":"HOSE 3/4in (상승 상태 굽힘, 근사)","SPEC":"3/4in ID19/OD28 연질 내염수 호스 — 상승 시 굽힘반경 59, 호 223°","QT'Y":"0","Material":"EPDM","REMARK":"호스 1본(전장 약 300)의 상승 상태 형상 근사. 구매 QT'Y는 H19_straight 쪽 1"})
if "hosestraight" in which:
    def sk(d): circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5))
    build("H19_hose_3-4in_straight_L230.SLDPRT",sk,230.0,{"TITLE":"HOSE 3/4in (하강 상태, 직선 근사)","SPEC":"3/4in ID19/OD28 연질 내염수·내한 호스, 자유길이 230 + 니플 삽입 2x20 = 전장 약 270, 최소 굽힘반경 60 이하 제품(실리콘/연질PVC)","QT'Y":"1","Material":"EPDM","REMARK":"호스밴드 2개 별도"})
if "hosenip" in which:
    def sk(d): circ(d,0,0,mm(12.0)); circ(d,0,0,mm(9.0))
    build("H16_hose_nipple_3-4in_short_L30.SLDPRT",sk,30.0,{"TITLE":"HOSE NIPPLE 3/4in SHORT","SPEC":"3/4in NPT x 3/4in 바브 짧은 호스니플 L30 304 (근사 원통 Ø24)","QT'Y":"2","Material":"STS304","REMARK":"형번 미확인 — 짧은 타입(전장 30) 지정"})
if "pipe40" in which:
    def sk(d): circ(d,0,0,mm(13.35)); circ(d,0,0,mm(9.3))
    build("H17_pipe_3-4in_L68.SLDPRT",sk,68.0,{"TITLE":"PIPE 3/4in L68 (노즐)","SPEC":"3/4in 파이프 니플 L68 316L","Material":"STS316L"})
if "movplate" in which:
    def sk(d):
        rect(d,mm(182.5),0,mm(257.5),mm(85))
        circ(d,mm(OX),0,mm(17.0))
        for y in (RY,-RY):
            circ(d,mm(RX),mm(y),mm(14.25))
            for a in (45,135,225,315): circ(d,mm(RX+19.5*math.cos(math.radians(a))),mm(y+19.5*math.sin(math.radians(a))),mm(2.75))
        circ(d,mm(ACT_X),0,mm(20.0))
    build("H5_moving_plate_170x515_t10.SLDPRT",sk,10.0,{"TITLE":"MOVING PLATE","SPEC":"170(Y)x515(X)x10 STS304, 소켓 Ø34 (x80), 리니어부시 LHFRW16 x2 (x300,±60), LA25 로드 Ø40 (x380)","Material":"STS304","REMARK":"좌우 대칭. 신규 제작"})
if "fixplate" in which:
    def sk(d):
        rect(d,mm(202.5),0,mm(277.5),mm(75))
        circ(d,0,0,mm(14.0))
        for y in (RY,-RY): circ(d,mm(RX),mm(y),mm(7.0))
    build("H1_fixed_plate_150x555_t10.SLDPRT",sk,10.0,{"TITLE":"FIXED MOUNT PLATE","SPEC":"150(Y)x555(X)x10 STS304, 호퍼 바닥 용접, 중앙 3/4in 소켓 Ø28, 봉 M16 탭 2 (x300,±60), 뒤쪽 아래 U브래킷 용접","Material":"STS304","REMARK":"좌우 대칭. 신규 제작"})
if "rod510" in which:
    def sk(d): circ(d,0,0,mm(8.0))
    build("H2_guide_shaft_MISUMI_PSSFAQ16-470-B10.SLDPRT",sk,480.0,{"TITLE":"GUIDE SHAFT","SPEC":"미스미 PSSFAQ16-470-B10 SUS440C Ø16 g6, L470 + M16x10 (전장 480)","QT'Y":"2","Material":"SUS440C","REMARK":"가격 미확인"})
if "bracket155" in which:
    def sk(d):
        pts=[(0,0),(12,0),(12,143),(136,143),(136,0),(148,0),(148,155),(0,155),(0,0)]
        for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
    build("H8_bent_U_bracket_t12_148x155x60.SLDPRT",sk,60.0,{"TITLE":"ACTUATOR U-BRACKET (절곡 1장)","SPEC":"STS304 t12 절곡, 폭 60, 다리 내측 124, 높이 155, 핀홀 Ø10.4 @v124 (도면 지시)","Material":"STS304","REMARK":"고정판 밑면에 매달림"})
