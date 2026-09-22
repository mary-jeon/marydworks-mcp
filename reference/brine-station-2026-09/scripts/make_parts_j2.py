# Design J2 parts (H=140 raise, soft hose r=40). Sketch on 정면 → extrude -Z (box z -t..0). Hose 상승 = sweep along arc path.
# usage: python make_parts_j2.py fixplate movplate rod600 bracket240 pipe100 hoseup hosestraight
import os, math, json
from swconn import *
import hose_solve as hs
app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
RY=240.0; RX=60.0; ACT_Y=300.0; OX=80.0
D_UP=187.0; STROKE=140.0; L_HOSE=math.hypot(OX,D_UP+STROKE)   # 336.6
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
# ---- hose path (part XY: x lateral(+ = line +x 뒤), y up(= line z)); start (0,0) heading -y
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
def solve_hose(r=40.0):
    D,X,L=D_UP,OX,L_HOSE
    best=None
    def tr(a1,a2,R,t):
        segs,(ex,ey)=hose_segments(r,a1,a2,R,t)
        Ls=sum((math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1]) if sg[0]=="line" else abs(sg[4])*math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1])) for sg in segs)
        return ex,ey,Ls
    def sc(a1,a2,R,t):
        ex,ey,Ls=tr(a1,a2,R,t); return math.sqrt((ex-X)**2+(ey+D)**2+(Ls-L)**2)
    for i1 in range(10,181,10):
        for i2 in range(-60,181,10):
            a1=math.radians(i1); a2=math.radians(i2)
            if a1+a2<=0.05: continue
            for R in (r,r*1.5,r*2.5):
                for t in (0,30,60,100):
                    v=sc(a1,a2,R,t)
                    if best is None or v<best[0]: best=(v,a1,a2,R,t)
    v,a1,a2,R,t=best; step=[0.05,0.05,10.0,10.0]
    while step[0]>1e-6:
        imp=False
        for i in range(4):
            for sg in (1,-1):
                q=[a1,a2,R,t]; q[i]+=sg*step[i]
                if q[2]<r or q[3]<0 or q[0]+q[1]<=0.02: continue
                vq=sc(*q)
                if vq<v: v,a1,a2,R,t=vq,*q; imp=True
        if not imp: step=[u/2 for u in step]
    return v,a1,a2,R,t
def build_hose_sweep(name,r,p):
    v,a1,a2,R,t=solve_hose(r); segs,end=hose_segments(r,a1,a2,R,t)
    print(f"hose fit resid={v:.3f} a1={math.degrees(a1):.1f} a2={math.degrees(a2):.1f} R={R:.1f} t={t:.1f} end=({end[0]:.1f},{end[1]:.1f}) L={L_HOSE:.1f}")
    for direction in (1,-1):
        d=app.NewDocument(tmpl,0,0,0)
        try:
            sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True)
            sm=d.SketchManager; sm.AddToDB=True
            for sg in segs:
                if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0)
                else:
                    c,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]
                    sm.CreateArc(mm(c[0]),mm(c[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
            sm.AddToDB=False
            d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            # measure path length
            skf=d.FeatureByName("스케치1") or d.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
            segs_sw=sk.GetSketchSegments
            if callable(segs_sw): segs_sw=segs_sw()
            def seglen(s_):
                v=s_.GetLength
                return v() if callable(v) else v
            Ls=sum(seglen(s_) for s_ in segs_sw)*1000
            print(f"  direction={direction}: sketch path length {Ls:.1f} (target {L_HOSE:.1f})")
            if abs(Ls-L_HOSE)>2.0:
                app.CloseDoc(d.GetTitle); continue
            # profile on 윗면 (XZ plane) at origin: tube OD28/ID19
            sel_plane(d,("윗면","Top Plane")); d.SketchManager.InsertSketch(True); circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5)); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            okp=d.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or d.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
            okq=d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or d.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
            print("  select profile",okp,"path",okq)
            f=None
            for attempt in ("swept3","swept4"):
                try:
                    # signatures read from sldworks.tlb: Swept3 = 17 params, Swept4 = 20 params
                    if attempt=="swept3": f=d.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                    else: f=d.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                    print("  ",attempt,"->",f.Name if f else None)
                    if f: break
                except Exception as ex: print("  ",attempt,"exception",ex)
            b=d.GetPartBox(True); print(name,"box",[round(v_*1000,1) for v_ in b])
            if not f: raise RuntimeError("sweep failed")
            p["SPEC"]=p["SPEC"]%(R,round(L_HOSE)); props(d,p); d.EditRebuild3
            json.dump({"r":r,"a1":a1,"a2":a2,"R":R,"t":t,"resid":v,"L":L_HOSE,"end":end,"segments":segs},open(os.path.join(VER,"J2_hose_path.json"),"w"),indent=1)
            return save(d,name)
        except Exception as ex:
            print("FAIL",name,ex); app.CloseDoc(d.GetTitle); raise
    raise RuntimeError("hose sketch length mismatch in both arc directions")
which=sys.argv[1:]
if "fixplate" in which:
    def sk(d):
        rect(d,0,mm(65),mm(75),mm(355))
        circ(d,0,0,mm(14.0))
        for y in (RY,-RY): circ(d,mm(RX),mm(y),mm(7.0))
    build("J1b_fixed_plate_150x710_t10.SLDPRT",sk,10.0,{"TITLE":"FIXED MOUNT PLATE (가로배치)","SPEC":"150(X)x710(Y)x10 STS304, 호퍼 바닥 용접(상면 지상고 2,050 = 기존 1,910+140 전제), 중앙 3/4in 소켓 Ø28, 가이드봉 M16 탭 2 (x60,y±240), 우측(+Y 256~404) 아래 LA25 U브래킷 용접","Material":"STS304","REMARK":"정면 기준 좌우(Y) -290(밸브모터측)~+420(실린더측). 신규 제작"})
if "movplate" in which:
    def sk(d):
        rect(d,mm(25),mm(20),mm(100),mm(310))
        circ(d,mm(OX),0,mm(17.0))
        for y in (RY,-RY):
            circ(d,mm(RX),mm(y),mm(14.25))
            for a in (45,135,225,315): circ(d,mm(RX+19.5*math.cos(math.radians(a))),mm(y+19.5*math.sin(math.radians(a))),mm(2.75))
        circ(d,0,mm(ACT_Y),mm(20.0))
    build("J5b_moving_plate_200x620_t10.SLDPRT",sk,10.0,{"TITLE":"MOVING PLATE (가로배치)","SPEC":"200(X)x620(Y)x10 STS304, 소켓 Ø34 (x80,y0), 리니어부시 LHFRW16 x2 (x60,y±240), LA25 로드 Ø40 (x0,y300)","Material":"STS304","REMARK":"정면 기준 좌우(Y) -290~+330. 출구 뒤(+X) 80 오프셋. 신규 제작"})
if "rod600" in which:
    def sk(d): circ(d,0,0,mm(8.0))
    build("J2_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT",sk,600.0,{"TITLE":"GUIDE SHAFT","SPEC":"미스미 PSSFAQ16-590-B10 SUS440C Ø16 g6, L590 + 편단 M16x10 (전장 600)","QT'Y":"2","Material":"SUS440C","REMARK":"고정판 탭홀에 상면 플러시. 형번 길이 590 재고 여부·가격 미확인"})
if "bracket240" in which:
    def sk(d):
        pts=[(0,0),(12,0),(12,228),(136,228),(136,0),(148,0),(148,240),(0,240),(0,0)]
        for i in range(len(pts)-1): d.SketchManager.CreateLine(mm(pts[i][0]),mm(pts[i][1]),0,mm(pts[i+1][0]),mm(pts[i+1][1]),0)
    build("J8_bent_U_bracket_t12_148x240x60.SLDPRT",sk,60.0,{"TITLE":"ACTUATOR U-BRACKET (절곡 1장)","SPEC":"STS304 t12 절곡, 폭 60, 다리 내측 124, 높이 240, 핀홀 Ø10.4 @v69 (도면 지시)","Material":"STS304","REMARK":"고정판 밑면에 매달림, LA25 후단 아이 핀 결합"})
if "pipe100" in which:
    def sk(d): circ(d,0,0,mm(13.35)); circ(d,0,0,mm(9.3))
    build("J17_pipe_3-4in_L100.SLDPRT",sk,100.0,{"TITLE":"PIPE 3/4in L100 (노즐)","SPEC":"3/4in 파이프 니플 L100 316L, 상단 10 소켓 체결","Material":"STS316L"})
if "hoseup" in which:
    build_hose_sweep("J19b_hose_3-4in_up_r40.SLDPRT",40.0,{"TITLE":"HOSE 3/4in (상승 상태 굽힘)","SPEC":"3/4in ID19/OD28 연질 실리콘 호스(최소 굽힘반경 ≤40, 내한 -30℃) — 상승 시 굽힘 40/%.0f, 자유길이 %d","QT'Y":"0","Material":"SILICONE","REMARK":"호스 1본의 상승 상태 형상(양단 수직, 경로 추적 해). 구매 QT'Y는 straight 쪽 1"})
if "hosestraight" in which:
    L=round(L_HOSE)
    def sk(d): circ(d,0,0,mm(14.0)); circ(d,0,0,mm(9.5))
    build("J19b_hose_3-4in_straight_L%d.SLDPRT"%L,sk,float(L),{"TITLE":"HOSE 3/4in (하강 상태, 직선)","SPEC":"3/4in ID19/OD28 연질 실리콘 호스, 자유길이 %d + 니플 삽입 2x20 = 전장 약 %d, 최소 굽힘반경 40 이하·내한 -30℃ 제품(형번 미확정)"%(L,L+40),"QT'Y":"1","Material":"SILICONE","REMARK":"호스밴드 2개 별도"})
