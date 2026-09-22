# 2026-09-09: 로봇 커버 열림 상태에서 하강 이동판 J5d(지상고 1498~1506)가 커버 액추에이터 TA2 로드(1488.8~1508.8)·로드엔드 브래킷(~1506.8)과 겹침.
# 로봇을 앞뒤로 옮겨서는 못 푼다(노즐이 개구 뒤끝 14 mm 앞, 커버는 개구 앞쪽에 주차). → 하강 스트로크 140→120: 하강 이동 그룹 +20(zp -530→-510).
#  1) B9c 하강: D3@로드_하강_이동 140→120 (충전 연장 142는 겹침 병합이라 그대로)
#  2) 어셈블리 전 구성: 하강 인스턴스 7개 z +20, 핀 J11-2 -495→-475
#  3) 하강 호스: 직선 L366 → 같은 자유길이 365.9의 단일 원호(현 -148→(100,-480) 현길이 346.7, +x 쪽 볼록) 새 파트로 교체
# 저장: B9c·새 호스·염수주입라인.SLDASM. S30000/S00000 미저장.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
OX=100.0; ZP_DN=-510.0; NIP_FIX_END=-148.0; STROKE=120.0; L_HOSE=365.9
# ---------- 1) B9c
PB=os.path.join(Z,"B9c_LINAK_LA25_600N_150st_24V.SLDPRT"); d=app.GetOpenDocumentByName(PB); assert d is not None
app.ActivateDoc3(PB,False,0,I4()); d=app.ActiveDoc
d.ShowConfiguration2("하강"); d.EditRebuild3
prm=d.Parameter("D3@로드_하강_이동"); print("B9c D3 before",prm.SystemValue*1000)
try:
    r=prm.SetSystemValue3(mm(STROKE),2,None)   # 2 = swSetValue_InAllConfigurations
except Exception as ex:
    print("  SetSystemValue3 exc",ex); prm.SystemValue=mm(STROKE); r="SystemValue"
d.EditRebuild3
print("B9c D3 set ->",r,d.Parameter("D3@로드_하강_이동").SystemValue*1000)
assert abs(d.Parameter("D3@로드_하강_이동").SystemValue*1000-STROKE)<0.01
for cfg in ("상승","하강"):
    d.ShowConfiguration2(cfg); d.EditRebuild3
    bs=list(pv(d,"GetBodies2",0,True) or []); print(f" B9c [{cfg}] bodies",[(b.Name,[round(v*1000,1) for v in pv(b,'GetBodyBox')]) for b in bs])
    assert len(bs)==2, "B9c body count"
d.ShowConfiguration2("상승"); d.EditRebuild3
cpm=d.Extension.CustomPropertyManager("")
cpm.Set2("REMARK",cpm.Get("REMARK")+" | 2026-09-09 하강 스트로크 140→120(D3@로드_하강_이동): 로봇 커버 열림 시 TA2 로드와 이동판 간섭 회피(HANDOFF §1-16)")
# ---------- 2) 어셈블리 변환
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager; CFGS=list(pv(asm,"GetConfigurationNames")); print("cfgs",CFGS)
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return {c.Name2:c for c in pv(root(),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
TARGET={"J5d_moving_plate_220x540_t8-2":(0,0,ZP_DN),"G13_weld_socket_3-4in_L25-11":(OX,0,ZP_DN),"H16_hose_nipple_3-4in_short_L30-12":(OX,0,ZP_DN+30),
        "J17_pipe_3-4in_L100-4":(OX,0,ZP_DN),"B10_linear_bushing_MISUMI_LHFRW16-23":(-70,240,ZP_DN),"B10_linear_bushing_MISUMI_LHFRW16-24":(-70,-240,ZP_DN),
        "J9b_rod_clevis_t6_44x40x60-2":(-40,-24,ZP_DN),"J11_clevis_pin_d10_L70-2":(-70,-35,ZP_DN+35)}
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps()
    for n,nt in TARGET.items():
        c=cc[n]; set_T(c,xform(c)["R"],nt)
    asm.ForceRebuild3(False); cc=comps()
    bad=[(n,xform(cc[n])["t_mm"]) for n,nt in TARGET.items() if any(abs(a-b)>0.05 for a,b in zip(xform(cc[n])["t_mm"],nt))]
    print(f"[{cfg}] transform mismatches: {bad}")
# ---------- 3) 하강 호스: 단일 원호 파트
A=(0.0,0.0); B=(OX, ZP_DN+30-NIP_FIX_END)   # 파트 좌표(정면 스케치 x, y): y 아래가 어셈 -z
c=math.hypot(B[0]-A[0],B[1]-A[1]); k=c/L_HOSE
lo,hi=1e-4,math.pi*2-1e-4
for _ in range(200):
    th=(lo+hi)/2
    if math.sin(th/2)/(th/2)>k: lo=th
    else: hi=th
th=(lo+hi)/2; R=L_HOSE/th; sag=R*(1-math.cos(th/2))
ux,uy=(B[0]-A[0])/c,(B[1]-A[1])/c; nx,ny=-uy,ux    # 현에 수직(+x 쪽으로 볼록: nx>0 확인)
if nx<0: nx,ny=-nx,-ny
Mx,My=(A[0]+B[0])/2,(A[1]+B[1])/2
Cx,Cy=Mx-(R-sag)*nx, My-(R-sag)*ny; Px,Py=Mx+sag*nx,My+sag*ny
print(f"hose dn arc: chord {c:.1f} L {L_HOSE} theta {math.degrees(th):.1f} deg R {R:.1f} sagitta {sag:.1f} center ({Cx:.1f},{Cy:.1f}) bow point ({Px:.1f},{Py:.1f})")
name_dn="J19c_hose_3-4in_dn_arc_L366.SLDPRT"; PD=os.path.join(Z,name_dn)
if os.path.exists(PD): raise SystemExit("exists: "+PD)
done=False
for direction in (1,-1):
    dh=app.NewDocument(tmpl,0,0,0)
    try:
        ok=dh.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or dh.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
        dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
        sm.CreateArc(mm(Cx),mm(Cy),0,mm(A[0]),mm(A[1]),0,mm(B[0]),mm(B[1]),0,direction)
        sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
        skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
        segs_sw=pv(sk,"GetSketchSegments"); Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in segs_sw)*1000
        print(f"  direction={direction}: sketch length {Ls:.1f} (target {L_HOSE})")
        if abs(Ls-L_HOSE)>2.0: app.CloseDoc(dh.GetTitle); continue
        ok=dh.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or dh.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
        dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(14.1)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(9.5)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
        dh.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or dh.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
        dh.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or dh.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
        f=None
        for attempt in ("swept3","swept4"):
            try:
                if attempt=="swept3": f=dh.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                else: f=dh.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                if f: break
            except Exception as ex: print("  ",attempt,"exception",ex)
        if not f: raise RuntimeError("sweep failed")
        dh.EditRebuild3; bx=[round(v_*1000,1) for v_ in dh.GetPartBox(True)]; print("  hose dn box",bx)
        cp=dh.Extension.CustomPropertyManager("")
        for k_,v_ in {"TITLE":"HOSE 3/4in (하강 상태, 완만한 원호)","SPEC":f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 자유길이 {L_HOSE} + 니플 삽입 2x20 = 절단 약 {round(L_HOSE)+40}, 최소 굽힘반경 47. 하강(스트로크 120) 현길이 {c:.1f} → 단일 원호 R {R:.0f}·처짐 {sag:.0f} 근사(+x 쪽 볼록)","QT'Y":"1","Material":"SILICONE","DATE":"2026-09-09","REMARK":"상승 J19c_up_r47과 같은 호스 1본. 2026-09-09 하강 스트로크 140→120으로 직선 L366 파트 대체(HANDOFF §1-16)"}.items(): cp.Add3(k_,30,v_,1)
        dh.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber"); dh.EditRebuild3
        e=I4(); wn=I4(); ok=dh.Extension.SaveAs(PD,0,1,NOD,e,wn); print("  saved",ok,name_dn,e.value,wn.value); done=True; break
    except Exception as ex:
        print("FAIL dn hose",ex); app.CloseDoc(dh.GetTitle); raise
if not done: raise SystemExit("dn hose sketch length mismatch")
# ---------- 3b) 어셈블리에서 직선 호스 교체
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
asm.ShowConfiguration2("하강"); asm.EditRebuild3; cc=comps()
old=[n for n in cc if n.startswith("J19c_hose_3-4in_straight")][0]
R_up=xform(cc["J19c_hose_3-4in_up_r47-1"])["R"]
asm.ClearSelection2(True); asm.Extension.SelectByID2(old+"@"+asm.GetTitle.replace(".SLDASM",""),"COMPONENT",0,0,0,False,0,NOD,0)
print("delete",old,asm.Extension.DeleteSelection2(1)); asm.EditRebuild3
newc=asm.AddComponent5(PD,0,"",False,"",0.0,0.0,0.0)
print("added",newc.Name2 if newc else None)
set_T(newc,R_up,(0,0,NIP_FIX_END)); asm.ForceRebuild3(False)
newname=newc.Name2
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps(); c=cc[newname]
    set_T(c,R_up,(0,0,NIP_FIX_END))
    asm.ClearSelection2(True); asm.Extension.SelectByID2(newname+"@"+asm.GetTitle.replace(".SLDASM",""),"COMPONENT",0,0,0,False,0,NOD,0)
    if cfg in ("하강","2.하강했을때(해석)") and cfg=="하강": asm.EditUnsuppress2
    else: asm.EditSuppress2
    asm.ClearSelection2(True); asm.ForceRebuild3(False); cc=comps()
    print(f"[{cfg}] {newname} supp={cc[newname].GetSuppression2} t={xform(cc[newname])['t_mm']}")
# ---------- 4) 검증: 하강 박스
asm.ShowConfiguration2("하강"); asm.ForceRebuild3(False); cc=comps()
rep={}
for n in list(TARGET)+[newname,"B9c_LINAK_LA25_600N_150st_24V-5"]:
    rep[n]=box(cc[n]); print("  하강",n,rep[n])
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump({"stroke_dn":STROKE,"zp_dn":ZP_DN,"hose_dn":{"chord":c,"R":R,"sag":sag,"theta_deg":math.degrees(th)},"boxes_dn":rep},open(os.path.join(VER,"J5c_dn120_build.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("saved _검증/J5c_dn120_build.json ; NOT saved: B9c, asm (sw_save로 저장)")
stop.set()
