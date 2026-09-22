# LA25 핀 이음 견고화 (사용자: 액추에이터가 흔들릴 것 같다 → 더 견고하게)
#  실측: LA25 후단 고정구·로드 아이 모두 폭 25.4(y ±12.7) 포크, 슬롯 Ø10.32. 브래킷 J8b 안폭 124(핀 지지 스팬 124 → 600 N에서 핀 굽힘 190 MPa, 액추에이터 y 방향 유동 ±49) · 클레비스 J9b 안폭 36(유동 ±5.3) · 구멍 Ø10.5 vs 핀 Ø10.
#  조치: ① J8b 안폭 124 → 26(포크 밀착, 편측 0.3), 높이 194 → 140(핀 아래 15), 구멍 Ø10 H7 · 핀 G11 L160 → L50(파일 G11b) ② J9b 구멍 Ø10 H7 + 핀 양쪽 스페이서 슬리브 Ø18×Ø10.2×5 ×2(J22, 안폭 36은 로드 외통 Ø29 회피용이라 유지) ③ 핀 E링 홈(속성 명기, 미모델)
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect(); mm=lambda v:v/1000.0
tmpl=app.GetUserPreferenceStringValue(8)
def partbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def redraw_lines(d,skname,pts):
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2(skname,"SKETCH",0,0,0,False,0,NOD,0); d.EditSketch()
    sk=d.SketchManager.ActiveSketch; segs=list(pv(sk,"GetSketchSegments") or [])
    lines=[s_ for s_ in segs if (s_.GetType() if callable(s_.GetType) else s_.GetType)==0]
    d.ClearSelection2(True)
    for s_ in lines: s_.Select4(True,NOD)
    d.Extension.DeleteSelection2(0); sm=d.SketchManager; sm.AddToDB=True
    for (a,b) in zip(pts,pts[1:]+pts[:1]): sm.CreateLine(mm(a[0]),mm(a[1]),0,mm(b[0]),mm(b[1]),0)
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.EditRebuild3
def set_circle(d,skname,center,r):
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2(skname,"SKETCH",0,0,0,False,0,NOD,0); d.EditSketch()
    sk=d.SketchManager.ActiveSketch; segs=list(pv(sk,"GetSketchSegments") or [])
    arcs=[s_ for s_ in segs if (s_.GetType() if callable(s_.GetType) else s_.GetType)==1]
    d.ClearSelection2(True)
    for s_ in arcs: s_.Select4(True,NOD)
    d.Extension.DeleteSelection2(0); sm=d.SketchManager; sm.AddToDB=True
    sm.CreateCircleByRadius(mm(center[0]),mm(center[1]),0,mm(r)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.EditRebuild3
def cyls(d,r,tol=0.05):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<tol: out.append([round(v*1000,1) for v in fc.GetBox])
    return out
# ---------- 1) J8b: 38×140×60, 구멍 Ø10 @ (z30, y15)
PJ=os.path.join(Z,"J8b_bent_U_bracket_t6_136x194x60.SLDPRT"); d=app.GetOpenDocumentByName(PJ); app.ActivateDoc3(PJ,False,0,I4()); d=app.ActiveDoc
b0=partbox(d)
if abs(b0[3]-b0[0]-38)>0.1:
    redraw_lines(d,"스케치1",[(0,0),(6,0),(6,134),(32,134),(32,0),(38,0),(38,140),(0,140)])
    set_circle(d,"스케치2",(30,15),5.0)
b=partbox(d); print("J8b box",b,"Ø10 holes",len(cyls(d,5.0)),"Ø10.5",len(cyls(d,5.25)))
assert abs(b[3]-b[0]-38)<0.1 and abs(b[4]-b[1]-140)<0.1 and len(cyls(d,5.0))==2
cpm=d.Extension.CustomPropertyManager("")
cpm.Set2("SPEC","STS304 6T 절곡 U브래킷 38x140x60 (안폭 26 = LA25 후단 포크 25.4 밀착), 핀홀 2-Ø10 H7 @ 하단 15")
cpm.Set2("REMARK","LA25 후단 고정구 받침. 고정판 J1c 밑면(x −100~−40, y ±19)에 둘레 필릿 용접. 종전 안폭 124(핀 스팬 124, 액추에이터 y 유동 ±49)를 포크 폭에 맞춰 26으로 줄이고 핀 Ø10 h7·E링. 파일명 136x194는 구치수")
# ---------- 2) J9b: 구멍 Ø10 (안폭 36 유지 — 로드 외통 회피)
PK=os.path.join(Z,"J9b_rod_clevis_t6_44x40x60.SLDPRT"); d=app.GetOpenDocumentByName(PK); app.ActivateDoc3(PK,False,0,I4()); d=app.ActiveDoc
if len(cyls(d,5.0))<2: set_circle(d,"스케치6",(30,35),5.0)
print("J9b box",partbox(d),"Ø10 holes",len(cyls(d,5.0)))
cpm=d.Extension.CustomPropertyManager("")
cpm.Set2("SPEC","STS304 6T 클레비스 48x50x60, 안폭 36(로드 외통 Ø29 회피), 핀홀 2-Ø10 H7 @ 35, 핀 양쪽 스페이서 슬리브 J22 ×2")
# ---------- 3) 핀 G11 L160 → L50 (파트 깊이 편집), J11 속성
PG=os.path.join(Z,"G11_clevis_pin_d10_L160.SLDPRT"); d=app.GetOpenDocumentByName(PG); app.ActivateDoc3(PG,False,0,I4()); d=app.ActiveDoc
f=pv(d,"FirstFeature"); ext=None
while f is not None:
    if pv(f,"GetTypeName2")=="Extrusion": ext=f
    f=pv(f,"GetNextFeature")
dd=pv(ext,"GetFirstDisplayDimension"); done=False
while dd and not done:
    dim=dd.GetDimension2(0)
    if abs(dim.SystemValue*1000-160)<0.01: dim.SystemValue=mm(50); d.EditRebuild3; done=True
    dd=pv(ext,"GetNextDisplayDimension",dd)
print("G11 box",partbox(d),"len edited",done); assert done
cpm=d.Extension.CustomPropertyManager("")
cpm.Set2("SPEC","STS304 클레비스 핀 Ø10 h7 L50, 양단 E링 홈(E-9) — LA25 후단 포크(25.4) + 브래킷 J8b 6T×2"); cpm.Set2("TITLE","CLEVIS PIN D10 L50")
PJ11=os.path.join(Z,"J11_clevis_pin_d10_L70.SLDPRT"); d=app.GetOpenDocumentByName(PJ11)
if d is not None:
    cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("SPEC","STS304 클레비스 핀 Ø10 h7 L70, 양단 E링 홈(E-9) — 로드 아이 포크(25.4) + 스페이서 J22 ×2 + 클레비스 J9b 6T×2")
# ---------- 4) 스페이서 J22 Ø18×Ø10.2×5
PSp=os.path.join(Z,"J22_pin_spacer_d18xd10.2_L5.SLDPRT")
if not os.path.exists(PSp):
    p=app.NewDocument(tmpl,0,0,0); p.ClearSelection2(True)
    p.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or p.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    p.SketchManager.InsertSketch(True); sm=p.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(9)); sm.CreateCircleByRadius(0,0,0,mm(5.1)); sm.AddToDB=False
    p.SketchManager.InsertSketch(True); p.ClearSelection2(True); p.Extension.SelectByID2(last_sketch(p),"SKETCH",0,0,0,False,0,NOD,0)
    p.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(5),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); p.EditRebuild3
    bx=partbox(p)
    if bx[5]<0:
        f=d.FeatureByName if False else None
    cpm=p.Extension.CustomPropertyManager("")
    for k,v in {"TITLE":"PIN SPACER","SPEC":"STS304 슬리브 Ø18×Ø10.2×L5 (로드 아이 포크 ↔ 클레비스 J9b 안폭 36 사이 편측 5.3 채움)","Material":"STS 304","QT'Y":"2","DATE":"2026-09-09","REMARK":"클레비스 핀 J11에 끼워 로드 아이의 y 유동을 없앤다"}.items(): cpm.Add3(k,30,v,1)
    p.SetMaterialPropertyName2("","SOLIDWORKS Materials","AISI 304"); p.EditRebuild3
    e=I4(); w=I4(); print("save J22",p.Extension.SaveAs(PSp,0,1,NOD,e,w),e.value,w.value,"box",partbox(p))
# ---------- 5) 어셈블리: J8b t_y −19, G11 t_y −25, 스페이서 4개(상승 2·하강 2)
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager; CFGS=list(pv(asm,"GetConfigurationNames")); title=asm.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
asm.ShowConfiguration2("상승"); asm.EditRebuild3; cc=comps()
R_sp=[[1,0,0],[0,0,1],[0,-1,0]]   # 파트 z(두께) → 어셈 −y? 확인 후 조정: 파트 z 0~5 → 어셈 y
new=[]
if not any(n.startswith("J22_") for n in cc):
    for zp,cfgname in ((-390,"상승"),(-530,"하강")):
        zpin=zp+35
        for ysign in (1,-1):
            c=asm.AddComponent5(PSp,0,"",False,"",0.0,0.0,0.0)
            # 파트 z(0~5) → 어셈 y: y = t_y + z*R[2]; +y쪽 스페이서 y 13~18 → R rows: part Z→(0,1,0), part Y→(0,0,1)?  det: X→X, Y→Z, Z→Y는 det −1 → Y→−Z 사용
            R=[[1,0,0],[0,0,-1],[0,1,0]]
            t=(-70.0, 13.0 if ysign>0 else -18.0, zpin)
            new.append((c.Name2,R,t,cfgname))
print("added",[n for n,_,_,_ in new])
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps()
    j8=cc["J8b_bent_U_bracket_t6_136x194x60-1"]; set_T(j8,xform(j8)["R"],(-40.0,-19.0,-150.0))
    g11=cc["G11_clevis_pin_d10_L160-4"]; set_T(g11,xform(g11)["R"],(-70.0,-25.0,-135.0))
    for n,R,t,cfgname in new:
        c=cc[n]; asm.ClearSelection2(True); c.Select4(False,NOD,False); asm.UnfixComponent(); asm.ClearSelection2(True); set_T(c,R,t)
        asm.ClearSelection2(True); asm.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
        want = (cfg=="상승" and cfgname=="상승") or (cfg=="하강" and cfgname=="하강")
        (asm.EditUnsuppress2 if want else asm.EditSuppress2); asm.ClearSelection2(True)
        c.Select4(False,NOD,False); asm.FixComponent(); asm.ClearSelection2(True)
    asm.ForceRebuild3(False); cc=comps()
    print(f" [{cfg}] J8b box={box(j8)} G11 box={box(g11)}",[(n,cc[n].GetSuppression2,box(cc[n])) for n,_,_,_ in new if cc[n].GetSuppression2==2])
    asm.ClearSelection2(True)
    for n in cc:
        if cc[n].GetSuppression2==2 and n.startswith(("J8b","G11","J9b","J11","J22","B9c","J1c","J5d","B10","J2_")): cc[n].Select4(True,NOD,False)
    idm=asm.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); asm.ClearSelection2(True)
    print(f" [{cfg}] 간섭:",[r for r in rows if not (set(x[:3] for x in r[0])=={"J2_","J1c"})])
asm.ShowConfiguration2("상승"); asm.EditRebuild3
stop.set(); print("done; NOT saved")
