# 2026-09-10: 가이드봉 상단 클램프 홀더 J23 = MISUMI SHFSS16(플랜지형 슬릿 샤프트 서포트, SUS304) — STEP 미수신(로그인 벽)이라 규격표 치수로 근사 모델링 후 배치
#  규격표 D16 행(원문): L 50 · L1 40(볼트 피치) · T 16(축방향 두께) · t 8(플랜지 두께) · H 31 · A 28 · B 20 · C 2 · h 12.5 · d 5.5 · d1 9 · 클램프 M4
#  근사 가정: 플랜지 폭 28(A) 장공형, 보스 Ø28, 클램프 귀 폭 20(B)·축중심에서 31(H)까지, 슬릿 2(C). STEP 수신 시 교체.
#  파트 좌표: 취부면(플랜지 상면) z 0, 보어 축 Z, 몸체 −z(판 밑으로 16), 볼트 귀 ±x, 클램프 귀 −y
#  배치: (45, +240, −10) 귀 +y(바깥) → R=diag(−1,−1,1) / (45, −240, −10) I3.  J1c 스케치3에 M5 탭 Ø4.2 @(25|65, ±240) 추가(제자리 편집)
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
mm=lambda v:v/1000.0
AX=45.0; RY=240.0; Z_PLATE_BOT=-10.0; PITCH=40.0
OUT=os.path.join(Z,"J23_shaft_support_MISUMI_SHFSS16.SLDPRT")
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def sketch_on(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    nm=last_sketch(d); d.Extension.SelectByID2(nm,"SKETCH",0,0,0,False,0,NOD,0); return nm
def extrude(d,depth,dir_neg,merge=True,name=None):
    f=d.FeatureManager.FeatureExtrusion3(True,False,dir_neg,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False); d.EditRebuild3
    if f and name: f.Name=name
    return f
def cut_through(d,name=None):
    f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    if f and name: f.Name=name
    return f
def pbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
rep={}
if not os.path.exists(OUT):
    d=app.NewDocument(tmpl,0,0,0)
    # 1) 플랜지 장공형 50×28 t8, 정면(XY) 스케치 → −z 8
    def flange(sm):
        sm.CreateLine(mm(-11),mm(14),0,mm(11),mm(14),0); sm.CreateArc(mm(11),0,0,mm(11),mm(14),0,mm(11),mm(-14),0,-1)
        sm.CreateLine(mm(11),mm(-14),0,mm(-11),mm(-14),0); sm.CreateArc(mm(-11),0,0,mm(-11),mm(-14),0,mm(-11),mm(14),0,-1)
    sketch_on(d,"정면",flange); f=extrude(d,8.0,True,name="플랜지_t8"); assert f, "flange"
    bx=pbox(d); print("flange box",bx)
    if bx[5]>0.5:   # 방향 반대면 지우고 반대로
        d.ClearSelection2(True); d.Extension.SelectByID2("플랜지_t8","BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
        sketch_on(d,"정면",flange); f=extrude(d,8.0,False,name="플랜지_t8"); bx=pbox(d); print("flange box(flip)",bx)
    assert abs(bx[2]+8)<0.1 and abs(bx[5])<0.1, bx
    neg = True if True else False
    # 2) 보스 Ø28 (z −8 → −16): 정면 스케치를 z −8 면에 그리기 어려우니 같은 방향으로 16 돌출 후 병합
    sketch_on(d,"정면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(14)))
    f=extrude(d,16.0,bx[2]<0,name="보스_Ø28"); bx=pbox(d); print("boss box",bx); assert abs(bx[2]+16)<0.1, bx
    # 3) 클램프 귀 20×(14→31) z 0~−16
    sketch_on(d,"정면",lambda sm: sm.CreateCornerRectangle(mm(-10),mm(-14),0,mm(10),mm(-31),0))
    f=extrude(d,16.0,True,name="클램프귀_B20"); bx=pbox(d); print("lug box",bx); assert abs(bx[1]+31)<0.1, bx
    # 4) 보어 Ø16 관통 + 볼트홀 Ø5.5 ×2 + 슬릿 2
    sketch_on(d,"정면",lambda sm: (sm.CreateCircleByRadius(0,0,0,mm(8)),sm.CreateCircleByRadius(mm(PITCH/2),0,0,mm(2.75)),sm.CreateCircleByRadius(mm(-PITCH/2),0,0,mm(2.75)),sm.CreateCornerRectangle(mm(-1),mm(-8),0,mm(1),mm(-31.5),0)))
    cut_through(d,"보어_볼트홀_슬릿")
    # 5) 클램프 볼트 M4 관통(귀 가로, x 방향) — 우측면(YZ) 스케치: (y,z) 원 @(y −22.5, z −8) 표현
    sketch_on(d,"우측면",lambda sm: sm.CreateCircleByRadius(mm(-22.5),mm(-8),0,mm(2.25)))
    cut_through(d,"클램프볼트_M4")
    bs=list(pv(d,"GetBodies2",0,True) or []); print("bodies",len(bs),"box",pbox(d),"ww",ww(d)); assert len(bs)==1 and not ww(d)
    cp=d.Extension.CustomPropertyManager("")
    for k,v in {"TITLE":"SHAFT SUPPORT FLANGE SLIT (MISUMI SHFSS16)","SPEC":"MISUMI SHFSS16 샤프트 서포트 플랜지형 슬릿, 홀 D16 H7(슬릿 가공 후 H8 정도), SUS304 상당, 무처리. 규격표 D16 행: L50·L1(볼트 피치)40·T16·t8·H31·A28·B20·C2·h12.5·취부홀 d5.5(자리파기 d1 9)·클램프 볼트 M4(별매). 근사형상(카탈로그 표·외형도 판독: 플랜지 폭 28 장공형·보스 Ø28·귀 폭 20 가정) — MISUMI STEP 수신 시 교체. 파트 좌표: 취부면 z 0, 보어 축 Z, 몸체 −z 16, 클램프 귀 −y","MATERIAL":"SUS304","QT'Y":"2","DATE":"2026-09-10","REMARK":"가이드봉 PSSFAQ16 상단을 고정판 J1c 밑면에서 클램프 고정(M5 볼트 2 → J1c M5 탭). 종전 M16 탭 10 mm 체결(횡력 시 나사 골 굽힘 121 MPa/50 N) 대체. 클램프 허용하중은 카탈로그 미기재(미확인)"}.items(): cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍","STS 304")
    except Exception: pass
    e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved J23",ok,e.value); assert ok
    rep["J23_box"]=pbox(d)
else: print("J23 exists")
# ---- J1c: M5 탭(Ø4.2) 4개소 추가 (스케치3 제자리 편집: 추가만)
P1=os.path.join(Z,"J1c_fixed_plate_185x580_t10.SLDPRT"); d=app.GetOpenDocumentByName(P1) or open_doc(app,P1,1); app.ActivateDoc3(P1,False,0,I4()); d=app.ActiveDoc
def cyls(d): return sorted(set((round(s.CylinderParams[0]*1000,1),round(s.CylinderParams[1]*1000,1),round(s.CylinderParams[6]*1000,2)) for b in (pv(d,"GetBodies2",0,True) or []) for fc in b.GetFaces() for s in [fc.GetSurface] if s.IsCylinder))
if not any(abs(c[2]-2.1)<0.05 for c in cyls(d)):
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치3","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sm=d.SketchManager; sm.AddToDB=True
    for sy in (RY,-RY):
        for sx in (AX-PITCH/2,AX+PITCH/2): sm.CreateCircleByRadius(mm(sx),mm(sy),0,mm(2.1))
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False)
    print("J1c cyl",cyls(d),"ww",ww(d)); assert not ww(d)
    cp=d.Extension.CustomPropertyManager(""); s=cp.Get("SPEC") or ""; cp.Set2("SPEC",s.replace("홀더 취부 탭은 규격 확인 후 추가","홀더 SHFSS16 취부 M5 탭 4개소 @(25|65, ±240)(드릴 Ø4.2 = 모델 구멍, 물림 10 = 2d)"))
    e=I4(); w=I4(); print("save J1c",d.Save3(1,e,w),e.value)
else: print("J1c taps exist")
# ---- 어셈블리 배치 ×2 (전 구성 활성)
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
ex=sorted([n for n in cc if n.startswith("J23_")])
if app.GetOpenDocumentByName(OUT) is None: open_doc(app,OUT,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
while len(ex)<2:
    c=a.AddComponent5(OUT,0,"",False,"",0.0,0.0,0.0); assert c; a.EditRebuild3; cc=comps(); ex=sorted([n for n in cc if n.startswith("J23_")])
PL={ex[0]:([[-1,0,0],[0,-1,0],[0,0,1]],(AX,RY,Z_PLATE_BOT)), ex[1]:([[1,0,0],[0,1,0],[0,0,1]],(AX,-RY,Z_PLATE_BOT))}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,(R,t) in PL.items():
        move_fixed(cc[n],R,t)
        if cc[n].GetSuppression2!=2: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps(); print(f"[{cfg}]",[(n,box(cc[n])) for n in PL],"ww",ww(a))
rep["asm"]={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_={n:c for n,c in cc.items() if c.GetSuppression2==2}
    rows=interf(list(act_.values())); rows=[r for r in rows if any(x.startswith(("J23","J2c","J1c")) for x in r[0])]
    rep["asm"][cfg]=rows; print(f"[{cfg}] 홀더·봉·판 관련 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3; e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
json.dump(rep,open(os.path.join(VER,"shaft_holder_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("holder done")
