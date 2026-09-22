# J4 parts (2026-09-08, 사용자 승인 「순서대로 진행」): 실린더 앞중앙 배치용 고정판 J1c·이동판 J5d.
# 정면 스케치 (sx,sy) -> 모델 (X,Y), 돌출은 z -depth..0 (make_parts_j3 실측 규약 그대로).
# usage: python make_parts_j4.py fixplate movplate
import os, math, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
AX=-70.0; RY=240.0; OX=80.0     # 실린더·가이드봉 x = -70 (앞), 가이드봉 y ±240, 출구 소켓 x +80
def sel_plane(d,names):
    for nm in names:
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def extrude(d,depth):
    return d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,depth,0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
def circ(d,x,y,r): d.SketchManager.CreateCircleByRadius(x,y,0.0,r)
def rect(d,cx,cy,hx,hy): d.SketchManager.CreateCenterRectangle(cx,cy,0,cx+hx,cy+hy,0)
def props(d,p):
    cpm=d.Extension.CustomPropertyManager(""); p.setdefault("DATE","2026-09-08"); p.setdefault("QT'Y","1")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
    mat=p.get("Material","STS304")
    if mat.startswith("STS"): d.SetMaterialPropertyName2("","이텍","STS 316" if "316" in mat else "STS 304")
def save(d,name):
    p=os.path.join(Z,name)
    if os.path.exists(p): print("EXISTS skip",name); app.CloseDoc(d.GetTitle); return p
    e=I4(); wn=I4(); ok=d.Extension.SaveAs(p,0,1,NOD,e,wn); print("saved",ok,name,"err",e.value,"warn",wn.value); return p
def cyls(d,r):
    out=[]
    for b in (d.GetBodies2(0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
                bx=[round(v*1000,1) for v in fc.GetBox]; out.append((round((bx[0]+bx[3])/2,1),round((bx[1]+bx[4])/2,1)))
    return sorted(out)
def build(name,sk,thick,p,check):
    d=app.NewDocument(tmpl,0,0,0)
    try:
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; sk(d); d.SketchManager.AddToDB=False
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
        f=extrude(d,mm(thick)); d.EditRebuild3; b=[round(v*1000,1) for v in d.GetPartBox(True)]
        print(name,"feat",f.Name if f else None,"box",b)
        for r,expect in check:
            got=cyls(d,r); exp=sorted(expect); ok=len(got)==len(exp) and all(abs(a[0]-b[0])<0.2 and abs(a[1]-b[1])<0.2 for a,b in zip(got,exp)); print(f"  Ø{2*r} holes {got} {'OK' if ok else 'MISMATCH expected '+str(sorted(expect))}")
            if not ok: raise RuntimeError("hole check failed")
        props(d,p); d.EditRebuild3; return save(d,name)
    except Exception as ex:
        print("FAIL",name,ex); app.CloseDoc(d.GetTitle); raise
which=sys.argv[1:]
if "fixplate" in which:
    # 185(X: -110~75) x 580(Y: ±290) t10. Ø28 소켓(0,0) · 4-Ø9 볼트(±55,±25) · 2-Ø14 가이드봉(-70,±240)
    BOLTS=[(55,25),(-55,25),(55,-25),(-55,-25)]
    def sk(d):
        rect(d,mm(-17.5),0,mm(92.5),mm(290))
        circ(d,0,0,mm(14.0))
        for (x,y) in BOLTS: circ(d,mm(x),mm(y),mm(4.5))
        for y in (RY,-RY): circ(d,mm(AX),mm(y),mm(7.0))
    build("J1c_fixed_plate_185x580_t10.SLDPRT",sk,10.0,
          {"TITLE":"FIXED PLATE (J4 앞중앙 실린더)","SPEC":"185(X -110~75)x580(Y ±290)x10 STS304. 소켓 Ø28(0,0), 볼트 4-Ø9 @(±55,±25) [S30015 탭과 라인좌표 일치], 가이드봉 2-Ø14 @(-70,±240)",
           "Material":"STS304","REMARK":"2026-09-08 J4: LA25·가이드봉을 앞(x -70) 중앙으로. 상면이 EPDM 가스켓 S30016 아래, M8x25+PW+SW 4본. 가이드봉 상단 고정(PSSFAQ16 단부)은 미정의 — 형번 확인 후 구멍 확정"},
          check=[(14.0,[(0,0)]),(4.5,BOLTS),(7.0,[(AX,RY),(AX,-RY)])])
if "movplate" in which:
    # 220(X ±110) x 540(Y ±270) t8. 소켓 Ø34(80,0) · 부시 Ø28.5(-70,±240) + M4 탭 4개소 십자 PCD38(탭 드릴 Ø3.3) · 클레비스 J9는 (-70,0) 상면 용접
    bore=[(AX,RY),(AX,-RY)]; taps=[]
    for y in (RY,-RY):
        for (dx,dy) in ((19,0),(-19,0),(0,19),(0,-19)): taps.append((AX+dx,y+dy))
    def sk(d):
        rect(d,0,0,mm(110),mm(270))
        circ(d,mm(OX),0,mm(17.0))
        for (x,y) in bore: circ(d,mm(x),mm(y),mm(14.25))
        for (x,y) in taps: circ(d,mm(x),mm(y),mm(1.65))
    build("J5d_moving_plate_220x540_t8.SLDPRT",sk,8.0,
          {"TITLE":"MOVING PLATE (J4 앞중앙 실린더)","SPEC":"220(X ±110)x540(Y ±270)x8 STS304. 소켓 Ø34 (80,0), 리니어부시 LHFRW16 x2 (-70,±240) 보어 Ø28.5 + M4 탭 4개소 십자 PCD38(MISUMI STEP 실측 Ø4.5/카운터보어 Ø7.5), 상면 (-70,0) 로드 클레비스 J9 용접",
           "Material":"STS304","REMARK":"2026-09-08 J4: 실린더가 가이드봉 사이 중앙(-70,0) → 비틀림 0. t8 근거: 900N 걸림 시 480 스팬 중앙하중 M 108 N·m, 단면 186x8 → 54 MPa(허용 124, 가정 손계산; FEA 재실행 전 t6 미채택)"},
          check=[(17.0,[(OX,0)]),(14.25,bore),(1.65,taps)])
