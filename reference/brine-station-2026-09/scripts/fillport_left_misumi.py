# 2026-09-08 주입구 뚜껑 검토 반영: (1) 주입구를 사용자 기준 왼쪽(탱크 X +237.5)으로 미러 이동 (2) 자작 경첩 S30009×2 → MISUMI C-HHSN65A×2
# (3) 자작 손잡이 S30011 → Takigen C-1170-2S 걸쇠(겸 손잡이) + 받침 패드 S30017 (4) 상판 S30006 개구 스케치는 제자리 이동(스케치 삭제·재생성 없음)
# 메모리 작업만. 저장은 sw_save로 별도.
import os, json, math, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
rep={}
def bodies_boxes(d):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        bb=[round(v*1000,2) for v in pv(b,"GetBodyBox")]; out.append((b,bb))
    return out
# ---------- 1) 경첩 파트: 리프1 바디를 핀축(X, Y4.25 Z15) 둘레로 90° 회전 → 90° 장착 상태(뚜껑 테두리 수직면 + 상판 수평면)
HP=os.path.join(Z,"C-HHSN65A_hinge.SLDPRT"); h=app.GetOpenDocumentByName(HP) or open_doc(app,HP,1); app.ActivateDoc3(HP,False,0,I4()); h=app.ActiveDoc
bb=bodies_boxes(h); print("hinge bodies:",[b for _,b in bb])
already=any(b[4]>20 for _,b in bb)   # 이미 회전된 바디가 있으면(Y>20) 건너뜀
if not already:
    leaf1=[b for b,bx in bb if bx[2]<-5]
    if len(leaf1)!=1: raise SystemExit("leaf1 body not identified: "+str([bx for _,bx in bb]))
    h.ClearSelection2(True); sd=h.SelectionManager.CreateSelectData; sd.Mark=1; leaf1[0].Select2(False,sd)
    f=None
    for ang in (-math.pi/2, math.pi/2):
        f=h.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0, 0.0, 0.0,0.00425,0.015, float(ang),0.0,0.0, False,1)
        h.EditRebuild3; bb2=bodies_boxes(h); ok=any(bx[1]>3.5 and bx[4]>28 and bx[2]>10 for _,bx in bb2)
        print("  rotate",round(math.degrees(ang)),"->",f.Name if f else None,[bx for _,bx in bb2],"ok",ok)
        if f is not None and ok: break
        if f is not None:
            h.ClearSelection2(True); h.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); h.Extension.DeleteSelection2(0); h.ClearSelection2(True); h.EditRebuild3; f=None
            h.ClearSelection2(True); sd=h.SelectionManager.CreateSelectData; sd.Mark=1; leaf1[0].Select2(False,sd)
    if f is None: raise SystemExit("hinge leaf rotate failed")
    f.Name="리프1_90도장착"
    cpm=h.Extension.CustomPropertyManager(""); cpm.Add3("REMARK",30,"주입구 뚜껑 S30008 경첩. 90° 장착: 리프1 = 뚜껑 뒤쪽 테두리 수직면(Y 814~839), 리프2 = 상판 위(Z 16.75~41.75), 핀축 Y 814.25/Z 16.75 → 뚜껑이 뒤로 젖혀 열림. 원 STEP: P282-제작정보/C-HHSN65A_STEP.zip",1)
rep["hinge_bodies"]=[bx for _,bx in bodies_boxes(h)]
# ---------- 2) 받침 패드 S30017 (걸쇠 키퍼용) 40(X)x30(Y)x30(Z) STS316
PAD=os.path.join(Z,"S30017MU0.SLDPRT")
if not os.path.exists(PAD):
    tmpl=app.GetUserPreferenceStringValue(8); p=app.NewDocument(tmpl,0,0,0)
    p.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or p.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    p.SketchManager.InsertSketch(True); p.SketchManager.CreateCenterRectangle(0,mm(15),0,mm(20),mm(30),0); p.SketchManager.InsertSketch(True); p.ClearSelection2(True)
    p.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0) or p.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,False,0,NOD,0)
    p.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(30),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); p.EditRebuild3
    print("pad box",[round(v*1000,1) for v in pv(p,"GetPartBox",True)])
    cpm=p.Extension.CustomPropertyManager("")
    for k,v in {"RELATION NO.":"S30017MU0","PROJECT NO.":"S00000MU0","TITLE":"LATCH PAD","SPEC":"STS 316 40x30x30 블록, 상판 S30006 위 용접(걸쇠 C-1170-2S 키퍼 받침, 상면 = 뚜껑 상면 높이)","Material":"STS 316","QT'Y":"1","DATE":"2026-09-08","REMARK":"2026-09-08 주입구 뚜껑 걸쇠 교체 시 신설"}.items(): cpm.Add3(k,30,v,1)
    p.SetMaterialPropertyName2("","이텍","STS 316"); p.EditRebuild3
    e=I4(); wn=I4(); print("pad saved",p.Extension.SaveAs(PAD,0,1,NOD,e,wn),e.value,wn.value)
# ---------- 3) 상판 S30006 개구 스케치18 제자리 이동 (X +237.5 → −237.5)
SP=os.path.join(Z,"S30006MU0.SLDPRT"); s6=app.GetOpenDocumentByName(SP); app.ActivateDoc3(SP,False,0,I4()); s6=app.ActiveDoc
def opening_x(d):
    xs=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            sf=fc.GetSurface
            if sf.IsPlane:
                n=sf.PlaneParams[0:3]; bx=[v*1000 for v in fc.GetBox]
                if abs(n[0])>0.99 and abs(bx[4]-bx[1])>400 and abs(bx[4]-bx[1])<460 and abs(bx[5]-bx[2])<35: xs.append(round(bx[0],1))
    return sorted(set(xs))
print("opening X faces before:",opening_x(s6))
if not any(x<-400 for x in opening_x(s6)):
    s6.ClearSelection2(True)
    for dn in ("D1@스케치18","D2@스케치18"):
        if s6.Extension.SelectByID2(dn,"DIMENSION",0,0,0,True,0,NOD,0): pass
    print("  delete position dims:",s6.EditDelete()); s6.ClearSelection2(True)
    s6.Extension.SelectByID2("스케치18","SKETCH",0,0,0,False,0,NOD,0); s6.EditSketch(); s6.ClearSelection2(True)
    for nm in ("선1","선2","선3","선4","선5","선6"): s6.Extension.SelectByID2(nm+"@스케치18","SKETCHSEGMENT",0,0,0,True,0,NOD,0)
    ok=s6.Extension.MoveOrCopy(False,1,False,0,0,0,mm(-475),0,0); print("  move segments -475:",ok)
    s6.ClearSelection2(True)
    # 위치 치수 다시: 선2(x=-462.5 수직선)↔원점 462.5, 선1(y=-12.5 수평선)↔원점 12.5
    s6.Extension.SelectByID2("선2@스케치18","SKETCHSEGMENT",0,0,0,False,0,NOD,0); s6.Extension.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,True,0,NOD,0)
    d1=s6.AddDimension2(mm(-500),mm(-250),0); print("  dim1",d1 is not None); s6.ClearSelection2(True)
    s6.Extension.SelectByID2("선1@스케치18","SKETCHSEGMENT",0,0,0,False,0,NOD,0); s6.Extension.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,True,0,NOD,0)
    d2=s6.AddDimension2(mm(-250),mm(30),0); print("  dim2",d2 is not None); s6.ClearSelection2(True)
    s6.SketchManager.InsertSketch(True); s6.EditRebuild3
print("opening X faces after:",opening_x(s6),"box",[round(v*1000,1) for v in pv(s6,"GetPartBox",True)])
rep["S30006_opening_x"]=opening_x(s6)
# ---------- 4) 탱크 어셈블리: 미러 이동 + 부품 교체
TP=os.path.join(Z,"S30000MU0.SLDASM"); t=app.GetOpenDocumentByName(TP); app.ActivateDoc3(TP,False,0,I4()); t=app.ActiveDoc
name=t.GetTitle.replace(".SLDASM",""); cm=t.ConfigurationManager; CFGS=list(t.GetConfigurationNames); cur=cm.ActiveConfiguration.Name
def comps(): return {c.Name2.split("/")[-1]:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,tt):
    arr=list(R[0])+list(R[1])+list(R[2])+[tt[0]/1000,tt[1]/1000,tt[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names):
    t.ClearSelection2(True)
    for n in names: t.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
def ensure_open(p):
    for d in (app.GetDocuments or []):
        try:
            if (d.GetPathName or "").lower()==p.lower(): return
        except Exception: pass
    e=I4(); wn=I4(); app.OpenDoc6(p,1,1,"",e,wn); app.ActivateDoc3(TP,False,0,I4())
def add(fn,R,tt,fix=True):
    p=os.path.join(Z,fn); ensure_open(p)
    c=t.AddComponent5(p,0,"",False,"",tt[0]/1000,tt[1]/1000,tt[2]/1000)
    if c is None: raise RuntimeError("INSERT FAIL "+fn)
    sel([c.Name2.split("/")[-1]]); t.UnfixComponent(); t.ClearSelection2(True); set_T(c,R,tt)
    if fix: sel([c.Name2.split("/")[-1]]); t.FixComponent(); t.ClearSelection2(True)
    return c.Name2.split("/")[-1]
I=[[1,0,0],[0,1,0],[0,0,1]]
R_LATCH=[[0,0,-1],[-1,0,0],[0,1,0]]
MOVE={"S30007MU0-2":(237.5,810,-237.5),"S30008MU0-5":(237.5,838,-237.5),"S30012MU0-1":(237.5,835,-237.5)}
new=[]
for cfg in CFGS:
    t.ShowConfiguration2(cfg); t.EditRebuild3; cc=comps()
    for n,tt in MOVE.items():
        if n in cc: set_T(cc[n],I,tt)
    t.EditRebuild3
t.ShowConfiguration2(cur); t.EditRebuild3; cc=comps()
if not any(n.startswith("C-HHSN65A") for n in cc):
    new.append(add("C-HHSN65A_hinge.SLDPRT",I,(142,810,1.75)))
    new.append(add("C-HHSN65A_hinge.SLDPRT",I,(287,810,1.75)))
    new.append(add("C-1170-2S_latch.SLDPRT",R_LATCH,(237.5,840,-460)))
    new.append(add("S30017MU0.SLDPRT",I,(237.5,810,-505)))
    t.EditRebuild3
    for cfg in CFGS:   # 신규 부품 변환을 모든 구성에 (Transform2 구성별 실측 09-08)
        t.ShowConfiguration2(cfg); t.EditRebuild3; cc=comps()
        for n,(R,tt) in zip(new,[(I,(142,810,1.75)),(I,(287,810,1.75)),(R_LATCH,(237.5,840,-460)),(I,(237.5,810,-505))]): set_T(cc[n],R,tt)
        t.EditRebuild3
    t.ShowConfiguration2(cur); t.EditRebuild3
old=[n for n in comps() if n.startswith(("S30009MU0","S30011MU0"))]
if old: sel(old); print("delete old hinge/handle:",old,t.Extension.DeleteSelection2(0)); t.ClearSelection2(True); t.EditRebuild3
t.ForceRebuild3(False); cc=comps()
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
rep["tank_whatswrong"]=ww(t); print("tank whatswrong",rep["tank_whatswrong"])
rep["fillport"]={}
for n,c in cc.items():
    if n.split("-")[0] in ("S30006MU0","S30007MU0","S30008MU0","S30012MU0","S30017MU0") or n.startswith(("C-HHSN","C-1170")):
        rep["fillport"][n]=box(c); print(f"  {n:24s} t {xform(c)['t_mm']} box {box(c)}")
json.dump(rep,open(os.path.join(VER,"tank_recheck_2026-09-08","fillport_left.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("dirty:",[d.GetTitle for d in app.GetDocuments if pv(d,"GetSaveFlag") and d.GetTitle.startswith(("S30006","S30000","C-HHSN","C-1170","S30017"))],"(NOT SAVED)")
stop.set()
