# Design G parts (3/4" gooseneck + sloped hose). Sketch on 정면 → extrude -Z (box z -t..0). Elbow: second extrusion on 윗면.
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
    raise RuntimeError("no plane "+str(names))
def extrude(d,depth,flip=False,merge=True):
    return d.FeatureManager.FeatureExtrusion3(True,flip,True,0,0,depth,0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False)
def circ(d,x,y,r): d.SketchManager.CreateCircleByRadius(x,y,0.0,r)
def rect(d,cx,cy,hx,hy): d.SketchManager.CreateCenterRectangle(cx,cy,0,cx+hx,cy+hy,0)
def props(d,p):
    cpm=d.Extension.CustomPropertyManager(""); p.setdefault("DATE","2026-09-03"); p.setdefault("QT'Y","1")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
    mat=p.get("Material","STS304")
    if mat.startswith("STS"): d.SetMaterialPropertyName2("","이텍","STS 316" if "316" in mat else "STS 304")
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
def build_elbow(name,r,leg,p):
    d=app.NewDocument(tmpl,0,0,0)
    try:
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); circ(d,0,0,mm(r)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); f1=extrude(d,mm(leg))
        sel_plane(d,("윗면","Top Plane")); d.SketchManager.InsertSketch(True); circ(d,0,0,mm(r)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        d.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,0,NOD,0); f2=extrude(d,mm(leg),flip=False)
        b=d.GetPartBox(True); print(name,"feats",f1 is not None,f2 is not None,"box",[round(v*1000,1) for v in b])
        props(d,p); d.EditRebuild3; return save(d,name)
    except Exception as ex:
        print("FAIL",name,ex); app.CloseDoc(d.GetTitle); raise
which=sys.argv[1:]
RX=195; RY=45; ACT_X=380
if "elbow" in which:
    build_elbow("G_elbow_3-4in_L45.SLDPRT",16.0,45.0,{"TITLE":"ELBOW 3/4in 90deg (approx)","SPEC":"3/4in NPT 암나사 엘보 STS304, 다리 45 (근사: 원통 2개)","QT'Y":"6","Material":"STS304","REMARK":"실제 형번 미확인. 다리 길이·나사는 구매품에 맞춰 수정"})
if "fixplate" in which:
    def sk(d):
        rect(d,mm(202.5),0,mm(277.5),mm(75))
        circ(d,0,0,mm(14.0))
        for y in (RY,-RY): circ(d,mm(RX),mm(y),mm(7.0))
    build("G1b_fixed_plate_150x555_t10.SLDPRT",sk,10.0,{"TITLE":"FIXED MOUNT PLATE","SPEC":"150(Y)x555(X)x10 STS304, 호퍼 바닥 용접, 중앙 3/4in 소켓 Ø28, 봉 M16 탭 2 (x195,±45), 뒤쪽 아래 U브래킷 용접","Material":"STS304","REMARK":"좌우(Y) 대칭, 뒤(+X)로 연장. 신규 제작"})
if "movplate" in which:
    def sk(d):
        rect(d,mm(182.5),0,mm(257.5),mm(75))
        circ(d,0,0,mm(21.5))
        for y in (RY,-RY):
            circ(d,mm(RX),mm(y),mm(14.25))
            for a in (45,135,225,315): circ(d,mm(RX+19.5*math.cos(math.radians(a))),mm(y+19.5*math.sin(math.radians(a))),mm(2.75))
        circ(d,mm(ACT_X),0,mm(20.0))
    build("G5c_moving_plate_150x515_t10.SLDPRT",sk,10.0,{"TITLE":"MOVING PLATE","SPEC":"150(Y)x515(X)x10 STS304, 중앙 슬리브 통과 Ø43, 리니어부시 LHFRW16 x2 (x195,±45), LA25 로드 통과 Ø40 (x380)","Material":"STS304","REMARK":"좌우 대칭. 신규 제작"})
if "socket" in which:
    def sk(d): circ(d,0,0,mm(17.0)); circ(d,0,0,mm(13.4))
    build("G13_weld_socket_3-4in_L25.SLDPRT",sk,25.0,{"TITLE":"WELD SOCKET 3/4in","SPEC":"3/4in NPT 하프커플링 상당 Ø34x25 STS304 (근사)","QT'Y":"2","Material":"STS304"})
if "closenip" in which:
    def sk(d): circ(d,0,0,mm(13.35)); circ(d,0,0,mm(9.3))
    build("G14_close_nipple_3-4in_L32.SLDPRT",sk,32.0,{"TITLE":"CLOSE NIPPLE 3/4in","SPEC":"3/4in NPT 클로즈 니플 OD26.7/ID18.6 L32 316L","QT'Y":"4","Material":"STS316L"})
if "pipenip" in which:
    def sk(d): circ(d,0,0,mm(13.35)); circ(d,0,0,mm(9.3))
    build("G15_pipe_nipple_3-4in_L370.SLDPRT",sk,370.0,{"TITLE":"PIPE NIPPLE 3/4in","SPEC":"3/4in NPT 양단 나사 파이프 L370 316L (구스넥 수평구간)","QT'Y":"1","Material":"STS316L"})
if "hosenip" in which:
    def sk(d): circ(d,0,0,mm(13.35)); circ(d,0,0,mm(9.3))
    build("G16_hose_nipple_3-4in_L55.SLDPRT",sk,55.0,{"TITLE":"HOSE NIPPLE 3/4in","SPEC":"3/4in NPT x 3/4in 바브 호스니플 304 (근사 원통) — McMaster 5361K 계열","QT'Y":"2","Material":"STS304"})
if "nozzle" in which:
    def sk(d): circ(d,0,0,mm(13.35)); circ(d,0,0,mm(9.3))
    build("G17_nozzle_pipe_3-4in_L70.SLDPRT",sk,70.0,{"TITLE":"NOZZLE PIPE 3/4in","SPEC":"3/4in 파이프 니플 L70 316L (이동판 아래 노즐)","QT'Y":"1","Material":"STS316L"})
if "hoseseg" in which:
    for tag,z_e in (("up",-195.0),("dn",-335.0)):
        L=math.hypot(320-140, z_e+250)
        def sk(d): circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5))
        state="상승" if tag=="up" else "하강"
        build("G19_hose_3-4in_diag_%s_L%d.SLDPRT"%(tag,round(L)),sk,L,{"TITLE":"HOSE 3/4in (중간 직선 근사)","SPEC":"3/4in ID19 내염수·내한 강화호스, 구간 길이 %d — %s 상태"%(round(L),state),"QT'Y":"0","Material":"EPDM","REMARK":"호스 전체 길이 약 290 (양단 직선 40 + 중간). 실제는 완만한 S자, 모델은 직선 근사"})
    def sk(d): circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5))
    build("G19_hose_3-4in_end_L40.SLDPRT",sk,40.0,{"TITLE":"HOSE 3/4in (단부 직선 근사)","SPEC":"3/4in ID19 호스 단부 40","QT'Y":"0","Material":"EPDM"})
if "bracket" in which:
    def sk(d):
        pts=[(0,0),(12,0),(12,88),(136,88),(136,0),(148,0),(148,100),(0,100),(0,0)]
        for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
    build("G8_bent_U_bracket_t12_148x100x60.SLDPRT",sk,60.0,{"TITLE":"ACTUATOR U-BRACKET (절곡 1장)","SPEC":"STS304 t12 절곡, 폭 60, 다리 내측 124, 높이 100, 핀홀 Ø10.4 @z69 (도면 지시)","Material":"STS304","REMARK":"폭 100→60 (구스넥 배관 통과 공간)"})
if "pin" in which:
    def sk(d): circ(d,0,0,mm(5.0))
    build("G11_clevis_pin_d10_L160.SLDPRT",sk,160.0,{"TITLE":"CLEVIS PIN","SPEC":"Ø10 x 160 STS304","Material":"STS304"})

if "rod455" in which:
    def sk(d): circ(d,0,0,mm(8.0))
    build("G2_guide_shaft_MISUMI_PSSFAQ16-445-B10.SLDPRT",sk,455.0,{"TITLE":"GUIDE SHAFT","SPEC":"미스미 PSSFAQ16-445-B10 SUS440C 경질크롬 Ø16 g6, L445 + 편단 M16x10 (전장 455)","QT'Y":"2","Material":"SUS440C","REMARK":"고정 플레이트 탭홀에 상면 플러시. 가격 미확인"})

if "hose167" in which:
    def sk(d): circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5))
    build("G19b_hose_3-4in_L167.SLDPRT",sk,167.0,{"TITLE":"HOSE 3/4in (수직 자유낙하)","SPEC":"3/4in ID19/OD28 내염수·내한 강화호스 L167 — 밸브 아래 호스니플에 수직으로 매달림, 끝은 이동 슬리브 안","QT'Y":"1","Material":"EPDM","REMARK":"호스 밴드 2개 별도. 실제 길이는 현장에서 슬리브 하강 위치 확인 후 조정"})
if "sleeve115" in which:
    def sk(d): circ(d,0,0,mm(21.35)); circ(d,0,0,mm(18.6))
    build("G7_sleeve_32A_Sch10S_L115.SLDPRT",sk,115.0,{"TITLE":"GUIDE SLEEVE 32A","SPEC":"32A Sch10S STS304 튜브 OD42.7/ID37.2 L115 — 이동 플레이트 중앙 용접, 호스(OD28) 끝을 감싸 자유낙하 유도","QT'Y":"1","Material":"STS304","REMARK":"상단 깔때기 확장은 미모델(권장)"})
