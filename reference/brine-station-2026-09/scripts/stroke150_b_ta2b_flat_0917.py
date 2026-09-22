# 2026-09-17: TA2-2H-150274 대용 파트(B9j) phase B — 미저장 파트(후단 요크+슬롯까지 만든 상태)에 붙어 나머지를 평면 코드로 완성
# (중첩 함수 경로에서 FeatureExtrusion3가 None을 반환하는 재현 불가 현상 때문에 act_diag와 같은 평면 구조로 작성)
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-17"
RL_NEW=274.0; STROKE=150.0; TUBE_END=-(RL_NEW-22.8); TIP=-(RL_NEW+10.0)
P_B9J=Zp("B9j_TiMOTION_TA2-2H-150274-5511-010-1.SLDPRT")
app=connect()
docs=[x for x in list(pv(app,"GetDocuments") or []) if x.GetType==1 and not x.GetPathName]; assert docs,"no unsaved part"
app.ActivateDoc3(docs[-1].GetTitle,False,0,I4()); d=app.ActiveDoc; print("attached",d.GetTitle)
def feats():
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def bodies(): return list(pv(d,"GetBodies2",0,True) or [])
def bboxes(): return [[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies()]
def vol(): return d.Extension.CreateMassProperty.Volume*1e9
def ww():
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    d.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def last_sketch(): return [n for n,t in feats() if t=="ProfileFeature"][-1]
def orphans():
    fl=[]; f=pv(d,"FirstFeature")
    while f is not None: fl.append(f); f=pv(f,"GetNextFeature")
    parents=set()
    for f in fl:
        if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature"): continue
        for pf in (pv(f,"GetParents") or []):
            try: parents.add(pf.Name)
            except Exception: pass
        sf=pv(f,"GetFirstSubFeature")
        while sf is not None:
            try: parents.add(sf.Name)
            except Exception: pass
            sf=pv(sf,"GetNextSubFeature")
    return [f.Name for f in fl if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature") and f.Name not in parents]
for n in orphans():
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); print("orphan deleted",n)
d.EditRebuild3
# 재실행 가능: 후단슬롯_6 이후 피처 전부 삭제(요크+슬롯 상태로 복귀)
names=[n for n,t in feats()]; i=names.index("후단슬롯_6")
for n in reversed(names[i+1:]):
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(n,"BODYFEATURE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); print("reset: deleted",n)
d.EditRebuild3
for n in orphans():
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
d.ForceRebuild3(False); d.GraphicsRedraw2(); print("start bodies",bboxes(),"feats",[n for n,t in feats()][-4:])
bb=bboxes(); assert len(bb)==1 and abs(bb[0][2]+15)<0.05 and abs(bb[0][5]-11)<0.05, bb
def sel_face_any(pts):
    """평면 z = pt.z 이고 bbox가 (x,y)를 포함하는 면을 지오메트리로 찾아 Select4 (점 선택 불안정 회피)"""
    d.ClearSelection2(True)
    for pt in pts:
        for b in bodies():
            for fc in list(pv(b,"GetFaces") or []):
                sf=fc.GetSurface
                isp=sf.IsPlane
                if callable(isp): isp=isp()
                if not isp: continue
                gb=fc.GetBox
                if callable(gb): gb=gb()
                bx=[v*1000 for v in gb]
                if abs(bx[2]-pt[2])>0.05 or abs(bx[5]-pt[2])>0.05: continue
                if bx[0]-0.01<=pt[0]<=bx[3]+0.01 and bx[1]-0.01<=pt[1]<=bx[4]+0.01:
                    sd=d.SelectionManager.CreateSelectData; ok=fc.Select4(False,sd)
                    if ok and d.SelectionManager.GetSelectedObjectCount2(-1)==1: return True
    return False

# ---- 3) 튜브 Ø42(보어 r10.5): 요크 밑면(8,8,−15) 위 스케치 → z −15 ~ −251.2
assert sel_face_any([(8,8,-15),(-8,8,-15),(8,-8,-15),(-8,-8,-15)]),"yoke bottom face"
d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(21.0)); sm.CreateCircleByRadius(0,0,0,mm(10.5)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
sk=last_sketch(); f=None
for dirn in (False,True):
    d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(-TUBE_END-15.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
    print("tube dirn",dirn,"->",None if f is None else bboxes())
    if f is not None and any(abs(b[2]-TUBE_END)<0.06 for b in bboxes()): f.Name="튜브_Ø42"; break
    if f is not None: f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
assert f is not None,"tube"

# ---- 4) 모터 하우징 박스 x 15~64.1, y −29.1~20.0, z −15 ~ −115.5 (요크 밑면 보어 안 점 (0,6,−15)); 면 스케치 좌표가 반전될 수 있어 x 부호 2가지 시도
f=None
for xs in (1,-1):
    assert sel_face_any([(0,6,-15),(0,-6,-15),(5,6,-15)]),"bore face"
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCornerRectangle(mm(15.0*xs),mm(-29.1),0,mm(64.1*xs),mm(20.0),0); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch()
    for dirn in (False,True):
        d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(100.5),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
        bb=bboxes(); print("housing xs",xs,"dirn",dirn,"->",None if f is None else bb)
        if f is not None and len(bb)==1 and abs(bb[0][3]-64.1)<0.06 and abs(bb[0][0]+21.0)<0.06 and abs(bb[0][5]-11.0)<0.06: f.Name="모터하우징_실측박스"; break
        if f is not None: f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
    if f is not None: break
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); d.EditRebuild3
assert f is not None,"housing"
# y 방향도 반전됐을 수 있음: bbox y 확인(−29.1~20.0 기대, 반전이면 −20.0~29.1 → 대용이라 허용하되 기록)
print("housing y range",bboxes()[0][1],bboxes()[0][4])

# ---- 5) 로드 Ø20: 튜브 끝면 평면(z −251.2) 스케치 원 → 양방향(위 235.2 → −16, 아래 32.8 → −284), 병합 없음(어디에도 안 닿음)
assert sel_face_any([(16,0,TUBE_END),(0,16,TUBE_END),(-16,0,TUBE_END)]),"tube end face"
d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(10.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
sk=last_sketch(); f=None
for dirn in (False,True):
    d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    d1,d2=((-TUBE_END-16.0),(TUBE_END-TIP)) if not dirn else ((TUBE_END-TIP),(-TUBE_END-16.0))
    f=d.FeatureManager.FeatureExtrusion3(False,False,False,0,0,mm(d1),mm(d2),False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,0,0.0,False); d.EditRebuild3
    bb=bboxes(); print("rod both-dir",dirn,"->",None if f is None else bb)
    if f is not None and len(bb)==2 and any(abs(b[2]-TIP)<0.06 and abs(b[5]+16.0)<0.06 and b[3]<=10.01 for b in bb): f.Name="로드_Ø20"; break
    if f is not None: f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
assert f is not None,"rod"

# ---- 6) 전단 요크 24×17.6: 로드 팁면(0,6,−284) → +z 22 (z −284 ~ −262), 로드와 병합(튜브 끝 −251.2와 10.8 이격)
assert sel_face_any([(0,6,TIP),(0,-6,TIP),(5,5,TIP)]),"rod tip face"
d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCornerRectangle(mm(-12),mm(-8.8),0,mm(12),mm(8.8),0); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
sk=last_sketch(); f=None
for dirn in (False,True):
    d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(22.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
    bb=bboxes(); print("front yoke dirn",dirn,"->",None if f is None else bb)
    if f is not None and len(bb)==2 and any(abs(b[2]-TIP)<0.06 and abs(b[5]+16.0)<0.06 and abs(b[3]-12.0)<0.06 for b in bb): f.Name="전단요크"; break
    if f is not None: f.Select2(False,0); d.EditDelete(); d.EditRebuild3; f=None
assert f is not None,"front yoke"

# ---- 7) 전단 슬롯 y ±3: 팁면(11,7,−284) → +z 14 컷
assert sel_face_any([(11,7,TIP),(-11,7,TIP),(11,-7,TIP)]),"yoke tip face"
d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCornerRectangle(mm(-13),mm(-3),0,mm(13),mm(3),0); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
sk=last_sketch(); v0=vol(); c=None
for dirn in (False,True):
    d.ClearSelection2(True); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    c=d.FeatureManager.FeatureCut4(True,False,dirn,0,0,mm(14.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    dv=v0-vol() if c is not None else None; print("front slot dirn",dirn,"dv",dv)
    if c is not None and 1400<=dv<=2100 and len(bboxes())==2: c.Name="전단슬롯_6"; break
    if c is not None: c.Select2(False,0); d.EditDelete(); d.EditRebuild3; c=None
assert c is not None,"front slot"

# ---- 8) 핀홀 Ø8 (y축): 윗면 스케치 원 → 양방향 관통. 후단(0,0) 1개 → 전단은 스케치 y −274 / +274 중 실체를 뚫는 쪽
def hole_z_list():
    out=[]
    for b in bodies():
        for fc in list(pv(b,"GetFaces") or []):
            sf=fc.GetSurface
            isc=sf.IsCylinder
            if callable(isc): isc=isc()
            if isc:
                pr=sf.CylinderParams
                if abs(pr[6]*1000-4.0)<0.01: out.append(round(pr[2]*1000,1))
    return sorted(set(out))
def pin_cut(yc,name):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,mm(yc),0,mm(4.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    sk=last_sketch(); d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    c=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    if c is None:
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); d.EditRebuild3
        return None
    c.Name=name; return c
c=pin_cut(0.0,"후단핀홀_Ø8"); assert c,"rear pin hole"; print("rear hole z",hole_z_list())
c=None
for yc in (-RL_NEW,RL_NEW):
    c=pin_cut(yc,"전단핀홀_Ø8")
    if c is not None and any(abs(z+RL_NEW)<0.5 for z in hole_z_list()): break
    if c is not None: c.Select2(False,0); d.EditDelete(); d.EditRebuild3; c=None
assert c,"front pin hole"; print("hole z positions",hole_z_list(),"bodies",bboxes(),"ww",ww()); assert not ww() and len(bboxes())==2
for n in orphans():
    d.ClearSelection2(True)
    if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
d.EditRebuild3

# ---- 9) 구성 + 하강 로드 이동
for cfg,desc in (("상승","로드 후퇴, 핀 간격 274"),("하강","로드 150 신장, 핀 간격 424")): d.AddConfiguration3(cfg,desc,"",0)
d.ShowConfiguration2("하강"); d.EditRebuild3
rb=[b for b in bodies() if abs([round(v*1000,1) for v in pv(b,"GetBodyBox")][2]-TIP)<0.06]; assert len(rb)==1
d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; rb[0].Select2(True,sd)
mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,mm(-STROKE),0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1); d.EditRebuild3; assert mv is not None; mv.Name="로드_하강_이동"
bb=bboxes(); print("하강 bodies",bb); assert any(abs(b[2]-(TIP-STROKE))<0.1 for b in bb), bb
mv.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
rep={}
for cfg in ("상승","하강","기본"):
    d.ShowConfiguration2(cfg); d.EditRebuild3; rep[cfg]=bboxes(); print(f"[{cfg}]",rep[cfg],"ww",ww()); assert not ww()
d.ShowConfiguration2("상승"); d.EditRebuild3
assert not orphans(), orphans()
cp=d.Extension.CustomPropertyManager("")
props={"TITLE":"LINEAR ACTUATOR TA2-2H stroke 150 / retracted 274 — TiMOTION TA2-2H-150274-5511-010-1",
  "SPEC":"TiMOTION TA2-2H-150274-5511-010-1: 코드 H 500 N(push/pull)·17/14 mm/s·셀프락 500 N·24 V DC, 스트로크 150(표준 범위 20~150), Retracted Length 274 ≥ 150+119(후단 5·전단 5 클레비스 U, 데이터시트 20160711-M p.6), 리미트 스위치 1(양단 차단), IP66D, −25~+65 ℃, 케이블 1000. 구성 상승 = 로드 후퇴(핀 간격 274) / 하강 = 로드 −150 신장(424). **3D 형상: 원시 형상 대용 — 튜브 Ø42·로드 Ø20·모터 하우징 박스(x 15~64.1, y −29.1~20.0, z −15~−115.5)·요크 폭 22.4/17.6·슬롯 6·홀 Ø8은 085339 TraceParts STEP 실측값, 튜브 길이 = 설치길이 −22.8. 150274 STEP 교체 대기.** 파트 좌표: 후단 핀 원점, 축 −Z, 핀 축 Y, 모터 +X.",
  "MATERIAL":"AL casting/SUS rod","QT'Y":"1","DATE":DATE,"TOLERANCE":"TiMOTION 데이터시트: 전단 클레비스 U 슬롯 6.0·구멍 8.0, 후단 슬롯 6.0·구멍 8.0 — 공차 미기재(승인도면 요청). 핀 SHCCG8 g6 ↔ 구멍 8.0 공차 미확인.",
  "REMARK":"구매품. 사용자 지시 스트로크 85→150(B안: 상승 위치 65 상향, 하강 유지). 주문 표기: TA2-2H-150, Retracted Length 274, 후단 5·전단 5(홀 Ø8), 방향 0°, 리미트 스위치 1, 출력신호 0."}
for k,v in props.items():
    if cp.Get(k): cp.Set2(k,v)
    else: cp.Add3(k,30,v,1)
e=I4(); w=I4(); ok=d.Extension.SaveAs(P_B9J,0,1,NOD,e,w); print("saved B9j",ok,e.value,w.value); assert ok
app.CloseDoc(d.GetTitle)
json.dump(rep,open(os.path.join(DESK,"_검증","stroke150b_b9j_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("DONE flat")
