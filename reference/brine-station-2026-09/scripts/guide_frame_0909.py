# 가이드 프레임(닫힌 프레임): 고정판 J1c 185×580 → 185×640(y ±320), 스트럿 J20 □25×25×2 L590 ×2 @(x −70, y ±307.5) z −10→−600,
# 하단 바 J21 PL 40(x)×10(z)×640(y) @ z −600~−590, Ø16 관통 ×2 @ y ±240(봉 끝 10 mm 물림, M6 세트스크류 2개는 미모델).
# 이동판 J5d(y ±270)와 스트럿 내면(295) 여유 25. 하강 부시 하단 −574 ↔ 바 상면 −590 여유 16. 저장은 sw_save.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect(); mm=lambda v:v/1000.0
tmpl=app.GetUserPreferenceStringValue(8)
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def partbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def sel_plane(d):
    d.ClearSelection2(True)
    return d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
def props(d,p):
    cpm=d.Extension.CustomPropertyManager("")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
# ---------- 1) J1c 폭 580 → 640
PJ=os.path.join(Z,"J1c_fixed_plate_185x580_t10.SLDPRT"); d=app.GetOpenDocumentByName(PJ); app.ActivateDoc3(PJ,False,0,I4()); d=app.ActiveDoc
b0=partbox(d); print("J1c before",b0)
if abs(b0[4]-b0[1]-640)>0.1:
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2("스케치3","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch()
    sk=d.SketchManager.ActiveSketch; segs=list(pv(sk,"GetSketchSegments") or [])
    lines=[s_ for s_ in segs if (s_.GetType() if callable(s_.GetType) else s_.GetType)==0]
    d.ClearSelection2(True)
    for s_ in lines: s_.Select4(True,NOD)
    print("  delete lines",len(lines),d.Extension.DeleteSelection2(0))
    sm=d.SketchManager; sm.AddToDB=True
    sm.CreateLine(mm(-110),mm(-320),0,mm(75),mm(-320),0); sm.CreateLine(mm(75),mm(-320),0,mm(75),mm(320),0)
    sm.CreateLine(mm(75),mm(320),0,mm(-110),mm(320),0); sm.CreateLine(mm(-110),mm(320),0,mm(-110),mm(-320),0)
    l1=sm.CreateLine(mm(-110),mm(-320),0,mm(75),mm(320),0); l2=sm.CreateLine(mm(-110),mm(320),0,mm(75),mm(-320),0)
    for l in (l1,l2):
        try: l.ConstructionGeometry=True
        except Exception: pass
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.EditRebuild3
    b=partbox(d); print("  J1c box",b)
    assert abs(b[4]-b[1]-640)<0.1 and abs(b[3]-b[0]-185)<0.1 and abs(b[5]-b[2]-10)<0.1, "J1c width edit failed"
print("J1c after",partbox(d))
cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("SPEC","STS304 185x640 t10, 중앙 Ø28(소켓 용접), 2-M16 탭 @(-70, ±240)(가이드봉), 상면 호퍼 립(140각) 밑면 둘레 용접, 밑면 양끝에 가이드 스트럿 J20 용접")
# ---------- 2) 스트럿 J20 (□25×25×2, L590, 파트 z 0~590)
name_st="J20_guide_strut_sq25x2_L590.SLDPRT"; PS_=os.path.join(Z,name_st)
if not os.path.exists(PS_):
    p=app.NewDocument(tmpl,0,0,0); sel_plane(p); p.SketchManager.InsertSketch(True); sm=p.SketchManager; sm.AddToDB=True
    sm.CreateCenterRectangle(0,0,0,mm(12.5),mm(12.5),0); sm.CreateCenterRectangle(0,0,0,mm(10.5),mm(10.5),0); sm.AddToDB=False
    p.SketchManager.InsertSketch(True); p.ClearSelection2(True); p.Extension.SelectByID2(last_sketch(p),"SKETCH",0,0,0,False,0,NOD,0)
    f=p.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(590),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    p.EditRebuild3; bx=partbox(p); print("strut box",bx)
    if bx[5]<0:  # 방향 반대면 뒤집기
        p.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); p.EditDelete(); p.EditRebuild3
        p.Extension.SelectByID2(last_sketch(p),"SKETCH",0,0,0,False,0,NOD,0)
        f=p.FeatureManager.FeatureExtrusion3(True,True,False,0,0,mm(590),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); p.EditRebuild3; bx=partbox(p); print("strut box flipped",bx)
    f.Name="각관"
    props(p,{"TITLE":"GUIDE STRUT","SPEC":"STS304 각관 25x25x2.0T L590","Material":"STS 304","QT'Y":"2","DATE":"2026-09-09","REMARK":"가이드봉 프레임 스트럿. 상단은 고정판 J1c 밑면(y ±307.5 중심, x −70)에 둘레 필릿 용접, 하단은 하단 바 J21 상면에 용접. 이동판(y ±270)과 내면 여유 25"})
    p.SetMaterialPropertyName2("","SOLIDWORKS Materials","AISI 304"); p.EditRebuild3
    e=I4(); w=I4(); print("save strut",p.Extension.SaveAs(PS_,0,1,NOD,e,w),e.value,w.value)
# ---------- 3) 하단 바 J21 (PL 40×10×640, 파트 x ±20, y ±320, z 0~10, Ø16 @ (0, ±240))
name_bar="J21_guide_end_bar_40x10x640.SLDPRT"; PB_=os.path.join(Z,name_bar)
if not os.path.exists(PB_):
    p=app.NewDocument(tmpl,0,0,0); sel_plane(p); p.SketchManager.InsertSketch(True); sm=p.SketchManager; sm.AddToDB=True
    sm.CreateCenterRectangle(0,0,0,mm(20),mm(320),0); sm.CreateCircleByRadius(0,mm(240),0,mm(8)); sm.CreateCircleByRadius(0,mm(-240),0,mm(8)); sm.AddToDB=False
    p.SketchManager.InsertSketch(True); p.ClearSelection2(True); p.Extension.SelectByID2(last_sketch(p),"SKETCH",0,0,0,False,0,NOD,0)
    f=p.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(10),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    p.EditRebuild3; bx=partbox(p); print("bar box",bx)
    if bx[5]<0:
        p.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); p.EditDelete(); p.EditRebuild3
        p.Extension.SelectByID2(last_sketch(p),"SKETCH",0,0,0,False,0,NOD,0)
        f=p.FeatureManager.FeatureExtrusion3(True,True,False,0,0,mm(10),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); p.EditRebuild3; bx=partbox(p); print("bar box flipped",bx)
    f.Name="바"
    props(p,{"TITLE":"GUIDE END BAR","SPEC":"STS304 PL 40x10 L640, 2-Ø16 H7 @ ±240 (가이드봉 끝 10 물림), 측면 M6 세트스크류 2개(미모델)","Material":"STS 304","QT'Y":"1","DATE":"2026-09-09","REMARK":"가이드봉 하단을 잇는 바. 스트럿 J20 ×2 하단에 용접, 봉은 세트스크류로 고정(봉 하단은 나사 없음). 상면 z −590, 하강 부시 하단 −574와 여유 16"})
    p.SetMaterialPropertyName2("","SOLIDWORKS Materials","AISI 304"); p.EditRebuild3
    e=I4(); w=I4(); print("save bar",p.Extension.SaveAs(PB_,0,1,NOD,e,w),e.value,w.value)
# ---------- 4) 어셈블리 삽입
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager; CFGS=list(pv(asm,"GetConfigurationNames")); title=asm.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
asm.ShowConfiguration2("상승"); asm.EditRebuild3; cc=comps()
new=[]
if not any(n.startswith("J20_") for n in cc):
    for y in (307.5,-307.5):
        c=asm.AddComponent5(PS_,0,"",False,"",0.0,0.0,0.0); new.append((c.Name2,[[1,0,0],[0,-1,0],[0,0,-1]],(-70.0,y,-10.0)))
if not any(n.startswith("J21_") for n in cc):
    c=asm.AddComponent5(PB_,0,"",False,"",0.0,0.0,0.0); new.append((c.Name2,[[1,0,0],[0,1,0],[0,0,1]],(-70.0,0.0,-600.0)))
print("added",[n for n,_,_ in new])
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps()
    for n,R,t in new:
        c=cc[n]; asm.ClearSelection2(True); c.Select4(False,NOD,False); asm.UnfixComponent(); asm.ClearSelection2(True); set_T(c,R,t)
        asm.ClearSelection2(True); asm.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0); asm.EditUnsuppress2; asm.ClearSelection2(True)
        c.Select4(False,NOD,False); asm.FixComponent(); asm.ClearSelection2(True)
    asm.ForceRebuild3(False); cc=comps()
    for n,_,_ in new: print(f" [{cfg}] {n} supp={cc[n].GetSuppression2} box={box(cc[n])}")
    # 간섭: 신규 3 + 봉 + 고정판 + 이동 그룹 + LA25 + 호스
    asm.ClearSelection2(True)
    for n in cc:
        if cc[n].GetSuppression2==2 and n.startswith(("J20_","J21_","J2_","J1c","J5d","B10","J9b","B9c","J19c","J17","G13","H16","J8b")): cc[n].Select4(True,NOD,False)
    idm=asm.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); asm.ClearSelection2(True)
    print(f" [{cfg}] 간섭(신규 관련):",[r for r in rows if any(x.startswith(("J20_","J21_")) for x in r[0])])
asm.ShowConfiguration2("상승"); asm.EditRebuild3
# ---------- 5) 스테이션: 프레임 vs 로봇·호퍼
PSm=os.path.join(Z,"S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PSm); app.ActivateDoc3(PSm,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
for cfg in ("하강","상승"):
    s.ShowConfiguration2(cfg); s.ForceRebuild3(False); out=[]
    def walk(c,depth):
        for ch in (pv(c,"GetChildren") or []):
            if ch.GetSuppression2!=2: continue
            out.append((ch.Name2,ch))
            if depth<6: walk(ch,depth+1)
    walk(scm.ActiveConfiguration.GetRootComponent3(True),0)
    fr=[(n,c) for n,c in out if n.split("/")[-1].startswith(("J20_","J21_","J2_","J1c"))]
    robot=[(n,c) for n,c in out if n.startswith("/900000MU1-1") or (n.count("/")==2 and "900000MU1-1/" in n)]
    robot=[(n,c) for n,c in out if "900000MU1-1/" in n and n.count("/")==2]
    tank=[(n,c) for n,c in out if n.split("/")[-1].startswith(("S30001MU0","S30002MU0"))]
    for n,c in fr:
        if n.split("/")[-1].startswith("J21"): b=box(c); print(f"  [{cfg}] J21 지상고 {round(1109-b[3],1)}~{round(1109-b[0],1)} y {b[1]}~{b[4]} z {b[2]}~{b[5]}")
    s.ClearSelection2(True)
    for n,c in fr+robot+tank: c.Select4(True,NOD,False)
    idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
    print(f"  [{cfg}] 프레임↔로봇/호퍼 간섭:",[r for r in rows if any(x.startswith(("J20_","J21_","J2_","J1c")) for x in r[0])])
s.ShowConfiguration2("하강"); s.EditRebuild3
stop.set(); print("done; NOT saved (J1c, asm; J20/J21 저장됨)")
