# 2026-09-08: (1) 계단 옆판 S20006·S20008 벽두께 2.3→3.2 (스케치1 치수 D4·D3 제자리 편집) (2) 탱크 통기구: 상판 S30006에 Ø35 구멍(새 스케치+컷) + 구스넥 파트 S30018MU0 삽입
# (3) 디딤판↔옆판 거리 측정(읽기). 메모리 작업만, 저장은 sw_save.
import os, json, math, sys
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
rep={}
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
# ---------- (3) 측정
s=app.GetOpenDocumentByName(os.path.join(Z,"S00000MU0.SLDASM")); app.ActivateDoc3(os.path.join(Z,"S00000MU0.SLDASM"),False,0,I4()); s=app.ActiveDoc
name=s.GetTitle.replace(".SLDASM","")
try:
    m=pv(s.Extension,"CreateMeasure"); dist={}
    for a,b in (("S20001MU0-10","S20006MU0-2"),("S20001MU0-10","S20008MU0-3"),("S20001MU0-13","S20006MU0-2"),("S20001MU0-13","S20008MU0-3")):
        s.ClearSelection2(True)
        s.Extension.SelectByID2(f"{a}@S20000MU0-1@{name}","COMPONENT",0,0,0,False,0,NOD,0); s.Extension.SelectByID2(f"{b}@S20000MU0-1@{name}","COMPONENT",0,0,0,True,0,NOD,0)
        ok=pv(m,"Calculate",None); d_=round(pv(m,"Distance")*1000,2) if ok else None; dist[f"{a}↔{b}"]=d_; print("  dist",a,b,ok,d_)
    s.ClearSelection2(True); rep["tread_gap"]=dist
except Exception as ex: print("measure failed:",ex); rep["tread_gap"]="measure failed"
# ---------- (1) 옆판 벽두께
for fn in ("S20006MU0.SLDPRT","S20008MU0.SLDPRT"):
    P=os.path.join(Z,fn); d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
    v0=pv(d.Extension,"CreateMassProperty").Volume*1e9
    f=pv(d,"FirstFeature")
    while f is not None:
        if f.Name=="스케치1":
            dd=pv(f,"GetFirstDisplayDimension")
            while dd is not None:
                nm=pv(dd,"GetNameForSelection").split("@")[0]; dm=pv(dd,"GetDimension2",0)
                if nm=="D4": dm.SystemValue=0.0032
                if nm=="D3": dm.SystemValue=0.0064
                dd=pv(f,"GetNextDisplayDimension",dd)
        f=pv(f,"GetNextFeature")
    d.EditRebuild3; v1=pv(d.Extension,"CreateMassProperty").Volume*1e9
    cpm=d.Extension.CustomPropertyManager(""); cpm.Add3("SPEC",30,"75x75x3.2T",1); cpm.Add3("REMARK",30,"2026-09-08 벽두께 2.3→3.2: 산안규칙 제26조(500 kg/m², SF4) 스트링거 58→42 MPa(허용 51). 스케치1 D4/D3 치수 편집",1)
    print(fn,"volume",round(v0),"->",round(v1),"(비 %.2f, 2.3→3.2 기대 ≈1.37)"%(v1/v0),"whatswrong",ww(d))
    rep[fn]={"vol_before":v0,"vol_after":v1}
# ---------- (2) 통기구
# 2a. 상판 Ø35 구멍: 상면(윗면 방향 +Z? 파트 Z -30..0, 판 두께 방향 Z)에 새 스케치 → 관통 컷. 위치 파트 (X 300, Y -300) = 탱크 (X -300, Z -300)
SP=os.path.join(Z,"S30006MU0.SLDPRT"); s6=app.GetOpenDocumentByName(SP); app.ActivateDoc3(SP,False,0,I4()); s6=app.ActiveDoc
have=False
f=pv(s6,"FirstFeature")
while f is not None:
    if f.Name=="통기구_D35": have=True
    f=pv(f,"GetNextFeature")
if not have:
    s6.ClearSelection2(True); s6.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or s6.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    s6.SketchManager.InsertSketch(True); s6.SketchManager.AddToDB=True; s6.SketchManager.CreateCircleByRadius(mm(300),mm(-300),0,mm(17.5)); s6.SketchManager.AddToDB=False
    skn=s6.SketchManager.ActiveSketch.Name; s6.SketchManager.InsertSketch(True); s6.ClearSelection2(True)
    s6.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
    fc=s6.FeatureManager.FeatureCut3(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
    s6.ClearSelection2(True); s6.EditRebuild3
    if fc is None:
        s6.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
        fc=s6.FeatureManager.FeatureCut3(True,False,True,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False); s6.ClearSelection2(True); s6.EditRebuild3
    if fc is None: raise SystemExit("vent hole cut failed")
    fc.Name="통기구_D35"
    holes=[]
    for b in (pv(s6,"GetBodies2",0,True) or []):
        for face in b.GetFaces():
            sf=face.GetSurface
            if sf.IsCylinder and abs(sf.CylinderParams[6]*1000-17.5)<0.05: bx=[round(v*1000,1) for v in face.GetBox]; holes.append(bx)
    print("S30006 vent hole faces:",holes,"whatswrong",ww(s6))
    cpm=s6.Extension.CustomPropertyManager(""); v=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""); r=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""); cpm.Get4("REMARK",False,v,r)
    cpm.Add3("REMARK",30,(v.value or "")+" · 2026-09-08 통기구 Ø35 관통(탱크좌표 X-300,Z-300) 추가, 주입구 개구는 D1 편집으로 X+237.5(왼쪽)로 이동",1)
# 2b. 구스넥 파트 S30018MU0: 25A(OD34, t2.8) 상판 아래 10 → 위 150 → 180° r50 → 아래 60. 경로 정면(XY) 스케치 + 윗면 원 프로파일 스윕
VP=os.path.join(Z,"S30018MU0.SLDPRT")
if not os.path.exists(VP):
    tmpl=app.GetUserPreferenceStringValue(8); p=app.NewDocument(tmpl,0,0,0)
    p.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or p.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    sm=p.SketchManager; sm.InsertSketch(True); sm.AddToDB=True
    sm.CreateLine(0,mm(-10),0,0,mm(150),0)
    sm.CreateArc(mm(-50),mm(150),0, 0,mm(150),0, mm(-100),mm(150),0, 1)
    sm.CreateLine(mm(-100),mm(150),0,mm(-100),mm(90),0)
    sm.AddToDB=False; sm.InsertSketch(True); p.ClearSelection2(True)
    p.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or p.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
    sm.InsertSketch(True); sm.CreateCircleByRadius(0,0,0,mm(17.0)); sm.CreateCircleByRadius(0,0,0,mm(14.2)); sm.InsertSketch(True); p.ClearSelection2(True)
    okp=p.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or p.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
    okq=p.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or p.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
    f=None
    for attempt in ("swept3","swept4"):
        try:
            if attempt=="swept3": f=p.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
            else: f=p.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
            if f: break
        except Exception as ex: print("  ",attempt,"exception",ex)
    p.EditRebuild3; bx=[round(v*1000,1) for v in pv(p,"GetPartBox",True)]; print("vent part box",bx,"feat",f.Name if f else None,"sel",okp,okq)
    if not f: raise SystemExit("vent sweep failed")
    cpm=p.Extension.CustomPropertyManager("")
    for k,v in {"RELATION NO.":"S30018MU0","PROJECT NO.":"S00000MU0","TITLE":"VENT GOOSENECK 25A","SPEC":"STS 316 25A Sch10S(OD34.0 t2.8) 구스넥: 상판 관통 상향 150 + 180° 굽힘 r50 + 하향 60, 개구 하향, 40mesh SUS 방충망(별도)","Material":"STS 316","QT'Y":"1","DATE":"2026-09-08","REMARK":"산안·요구 SR-TK-08 통기구(제작정보-탱크 §3: 25A STS316 구스넥+40mesh). 상판 Ø35 구멍에 삽입·둘레 용접. 릴리프 겸용 아님. 2026-09-08 신설"}.items(): cpm.Add3(k,30,v,1)
    p.SetMaterialPropertyName2("","이텍","STS 316"); p.EditRebuild3
    e=I4(); wn=I4(); print("vent saved",p.Extension.SaveAs(VP,0,1,NOD,e,wn),e.value,wn.value)
# 2c. 탱크에 삽입: 파트 원점(스터브 시작 y=-10) → 탱크 (X -300, Y 810, Z -300)  → 스터브 800~960, 굽힘 -X 쪽
TP=os.path.join(Z,"S30000MU0.SLDASM"); t=app.GetOpenDocumentByName(TP); app.ActivateDoc3(TP,False,0,I4()); t=app.ActiveDoc
tname=t.GetTitle.replace(".SLDASM",""); cm=t.ConfigurationManager; cur=cm.ActiveConfiguration.Name
def comps(): return {c.Name2.split("/")[-1]:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
if not any(n.startswith("S30018") for n in comps()):
    for dd in (app.GetDocuments or []):
        pass
    e=I4(); wn=I4(); app.OpenDoc6(VP,1,1,"",e,wn); app.ActivateDoc3(TP,False,0,I4()); t=app.ActiveDoc
    c=t.AddComponent5(VP,0,"",False,"",-0.300,0.810,-0.300)
    cn=c.Name2.split("/")[-1]; t.ClearSelection2(True); t.Extension.SelectByID2(cn+"@"+tname,"COMPONENT",0,0,0,False,0,NOD,0); t.UnfixComponent(); t.ClearSelection2(True)
    for cfg in list(t.GetConfigurationNames):
        t.ShowConfiguration2(cfg); t.EditRebuild3; cc=comps()
        arr=[1,0,0,0,1,0,0,0,1,-0.300,0.810,-0.300,1.0,0,0,0]; xf=cc[cn].Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); cc[cn].Transform2=xf; t.EditRebuild3
    t.ShowConfiguration2(cur); t.EditRebuild3; t.ClearSelection2(True); t.Extension.SelectByID2(cn+"@"+tname,"COMPONENT",0,0,0,False,0,NOD,0); t.FixComponent(); t.ClearSelection2(True)
t.ForceRebuild3(False); cc=comps()
for n,c in cc.items():
    if n.startswith(("S30018","S30006","S30008")): print("  ",n,box(c))
rep["tank_whatswrong"]=ww(t); print("tank whatswrong",rep["tank_whatswrong"])
json.dump(rep,open(os.path.join(VER,"tank_recheck_2026-09-08","stringer_vent.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set()
