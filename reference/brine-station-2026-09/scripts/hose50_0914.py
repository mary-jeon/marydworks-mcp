# 2026-09-14 저녁: 50A 호스 라인(A안, 고정 노즐 + 직선 호스) — 파트 생성 + 어셈블리 재구성
#  스택(라인 z): 밸브 −38~−178 → 상부 호스니플(−158, 물림 20) → 호스 HSPF-050 −195~−373 → 하부 호스니플(뒤집음, 소켓 물림 20) → 소켓 Rp2 −390~−446(노즐판 플러시) → 노즐관 −426~−490
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
DATE="2026-09-14"
ENG=20.0; Z_VALVE_BOT=-178.0
HN_THR=29.0; HN_HEX=8.0; HN_BARB=60.0; HN_L=HN_THR+HN_HEX+HN_BARB   # 97 (배관몰 바자 50A: L 97, L1 60, D 52.5, d 41, B 62)
Z_HN_TOP=Z_VALVE_BOT+ENG                 # −158
HOSE_TOP=Z_HN_TOP-HN_THR-HN_HEX          # −195
ZPL=-390.0; SOCK_L=56.0; PL_T=6.0
Z_HN_BOT=ZPL-ENG                         # −410 (뒤집힌 니플 원점 = 나사 끝)
HOSE_BOT=Z_HN_BOT+HN_THR+HN_HEX          # −373
HOSE_L=HOSE_TOP-HOSE_BOT                 # 178
J17_TOP=ZPL-SOCK_L+ENG                   # −426
J17_END=-490.0; J17_L=J17_TOP-J17_END    # 64
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_FLIP=[[1,0,0],[0,-1,0],[0,0,-1]]
print("stack: HN top",Z_HN_TOP,"hose",HOSE_TOP,"~",HOSE_BOT,"L",HOSE_L,"| HN bot org",Z_HN_BOT,"| socket",ZPL,"~",ZPL-SOCK_L,"| J17",J17_TOP,"~",J17_END,"L",J17_L)
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def extrude(d,depth,name,start_off=0.0,flip=False):
    if start_off: f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,3,mm(start_off),flip)
    else: f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    d.EditRebuild3; assert f is not None, "extrude "+name; f.Name=name; return f
def del_feat(d,name):
    d.ClearSelection2(True); d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
def stack_extrude(d,z0,z1,draw,name):
    # z0<z1 (양수 깊이 좌표, 파트 −z 방향). 결과 바디가 하나이고 최저 z가 −z1인지 검증, 아니면 flip 재시도
    first=(z0==0)
    for flip in (False,True):
        new_sketch(d,"정면",draw); f=extrude(d,z1-z0,name,start_off=(0.0 if first else z0),flip=flip)
        bs=bodies(d); zr=[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bs]
        ok=len(bs)==1 and abs(min(b[2] for b in zr)+z1)<0.05 and abs(max(b[5] for b in zr))<0.05
        if ok: return
        del_feat(d,f.Name)
        if first: break
    raise SystemExit("stack seg failed "+name)
def ring(sm,ro,ri):
    sm.CreateCircleByRadius(0,0,0,mm(ro))
    if ri: sm.CreateCircleByRadius(0,0,0,mm(ri))
def hexring(sm,af,ri):
    try: sm.CreatePolygon(0,0,0,mm(af/math.sqrt(3)),0,0,6,True)
    except Exception as ex: print("  polygon exc",ex); sm.CreateCircleByRadius(0,0,0,mm(af/2))
    sm.CreateCircleByRadius(0,0,0,mm(ri))
def set_props(d,props,mat="STS 304"):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍",mat)
    except Exception as ex: print("  mat exc",ex)
def save_new(d,path):
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value); assert ok
stage=sys.argv[1] if len(sys.argv)>1 else "parts"
if stage=="parts":
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith("파트"): app.CloseDoc(tt); print("closed unsaved",tt)
    # ---- H16c 호스니플 PT2 × Ø52.5 (배관몰 「스텐호스니플(KS)」 바자 50A 치수표: D 52.5 · d 41 · L 97 · L1 60 · B 62)
    P=Zp("H16c_hose_nipple_PT2x52.5_L97.SLDPRT")
    if not os.path.exists(P):
        d=app.NewDocument(tmpl,0,0,0)
        stack_extrude(d,0,HN_THR,lambda sm: ring(sm,30.25,20.5),"나사부_OD60.5")
        stack_extrude(d,HN_THR,HN_THR+HN_HEX,lambda sm: hexring(sm,62.0,20.5),"육각_B62")
        stack_extrude(d,HN_THR+HN_HEX,HN_L,lambda sm: ring(sm,26.25,20.5),"바브_OD52.5")
        bx=bbox(d); print("H16c box",bx,"ww",ww(d)); assert abs(bx[2]+HN_L)<0.1 and not ww(d)
        set_props(d,{"TITLE":"HOSE NIPPLE PT2 x HOSE ID50 (SUS304)",
          "SPEC":"스텐 호스니플 50A × Ø52.5(바자 수입품, 배관몰 치수표): 수나사 PT(R)2 L 29(전장 97 − 바브 60 − 육각 8 가정), 육각 B62, 바브 OD 52.5 L 60, 보어 d 41. 상부: 밸브 G2 하단에 20 물림 / 하부: 소켓 Rp2에 20 물림(뒤집어 설치). 나사·바브 요철 미표현.",
          "Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"구매품(배관몰 baegwan.net 2918 「50A×Φ53」 옵션). 제조사 3D 없음 → 치수표로 자작 모델. 나사 길이 29·육각 두께 8은 표에 없는 값(가정)."})
        save_new(d,P)
    # ---- G13e 소켓 Rp2 KS B 1533 (D 65 SUS · L 56, 보어 60.6 = 수나사 OD 기준 겹침 없는 표현)
    P=Zp("G13e_socket_Rp2_KS_L56.SLDPRT")
    if not os.path.exists(P):
        d=app.NewDocument(tmpl,0,0,0)
        stack_extrude(d,0,SOCK_L,lambda sm: ring(sm,32.5,30.3),"소켓_OD65_L56")
        bx=bbox(d); print("G13e box",bx,"ww",ww(d)); assert abs(bx[2]+SOCK_L)<0.1 and not ww(d)
        set_props(d,{"TITLE":"SOCKET Rp2 (KS B 1533 50A) — 노즐판 플러시 용접",
          "SPEC":"KS B 1533 소켓 50A(2): 평행 암나사 Rp2 양쪽(KS B 0222), SUS304, D 65(SUS 최소)·L 56(최소). 보어 Ø60.6(수나사 바깥지름 기준, 겹침 없는 나사 표현). 노즐판 J5g 구멍 Ø65.5에 상면 플러시 삽입 후 양면 필릿 용접. 위: 호스니플 20 물림, 아래: 노즐관 R2 20 물림.",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"규격품(KS B 1533, standard.go.kr 원문 50A 행). 시판 실물 예: 하이스텐 소켓 50A D 70.5·L 60."})
        save_new(d,P)
    # ---- J17c 노즐관 50A Sch40 L64 (상단 R2 나사 미표현)
    P=Zp("J17c_nozzle_pipe_50A_Sch40_L64.SLDPRT")
    if not os.path.exists(P):
        d=app.NewDocument(tmpl,0,0,0)
        stack_extrude(d,0,J17_L,lambda sm: ring(sm,30.25,26.35),"노즐관_OD60.5_L64")
        bx=bbox(d); print("J17c box",bx,"ww",ww(d)); assert abs(bx[2]+J17_L)<0.1 and not ww(d)
        set_props(d,{"TITLE":"NOZZLE PIPE 50A (고정, 낙하 주입)",
          "SPEC":"STS304 50A Sch40 관(KS D 3576, OD 60.5 t3.9 — JIS G 3459 표8 원문값), L 64. 상단 20: 수나사 R2(KS B 0222, 소켓 G13e 하단 물림, 나사 미표현). 노즐 끝 지상고 1,560(로봇 커버 액추에이터 로드 상면 1,509 위 51, 개구면 1,474 위 86 낙하). 하단 모서리 C1.",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 요구사항정의 SR-NZ-01 낙하 주입·SR-NZ-02 승강 액추에이터 불채택과 일치."})
        save_new(d,P)
    # ---- J19f 호스 야성 HSPF-050 직선 L178 (ID 50 → 바브 위 52.5로 늘어난 상태 표현, OD 62)
    P=Zp(f"J19f_hose_YASUNG_HSPF-050_straight_L{HOSE_L:g}.SLDPRT")
    if not os.path.exists(P):
        d=app.NewDocument(tmpl,0,0,0)
        stack_extrude(d,0,HOSE_L,lambda sm: ring(sm,31.0,26.25),"호스_OD62_ID52.5")
        bx=bbox(d); print("J19f box",bx,"ww",ww(d)); assert abs(bx[2]+HOSE_L)<0.1 and not ww(d)
        set_props(d,{"TITLE":"HOSE 50A — YASUNG Hi-TECH SUPER SPRING HOSE (HSPF-050)",
          "SPEC":"야성하이텍 슈퍼스프링호스(무독) HSPF-050: 내경 50.0±1.5, 외경 62.0±1.5, 상용 0.4 MPa / 파열 1.6 MPa, 특수강선 + 무독 특수수지(PVC계), 사용온도 0~60 ℃(카탈로그 2025-11판 p.28), 롤 40 m. 직선 설치, 자유길이 178 + 바브 삽입 2×60 = 절단 약 298. 3D는 바브 위 늘어난 내경 52.5로 표현. 최소 굽힘반경 카탈로그 미기재(직선 설치라 무관). 클램프: 스텐 호스밴드 2개(형번 미정).",
          "Material":"PVC","QT'Y":"1","DATE":DATE,"REMARK":"구매품(야성판매 www.yasung.com, 제조 야성하이텍 054-972-2456). 저온 −30 ℃ 적합성은 원문 범위(0~60 ℃) 밖 — 제조사 확인 필요. 염수 내약품 원문 언급 없음."},mat="PVC 경질")
        save_new(d,P)
    # ---- J5g 노즐판 130×540 t6: x −40~90, 구멍 Ø65.5(0,0) · Ø16.5(45,±240) · M5 탭(Ø4.2) @(25|65, ±240)
    P=Zp("J5g_nozzle_plate_130x540_t6.SLDPRT")
    if not os.path.exists(P):
        d=app.NewDocument(tmpl,0,0,0)
        def draw(sm):
            sm.CreateCornerRectangle(mm(-40),mm(-270),0,mm(90),mm(270),0); sm.CreateCircleByRadius(0,0,0,mm(32.75))
            for sy in (240,-240):
                sm.CreateCircleByRadius(mm(45),mm(sy),0,mm(8.25))
                for sx in (25,65): sm.CreateCircleByRadius(mm(sx),mm(sy),0,mm(2.1))
        stack_extrude(d,0,PL_T,draw,"판_t6")
        bx=bbox(d); print("J5g box",bx,"ww",ww(d)); assert abs(bx[0]+40)<0.1 and abs(bx[3]-90)<0.1 and abs(bx[2]+PL_T)<0.1 and not ww(d)
        set_props(d,{"TITLE":"NOZZLE PLATE 130x540 t6 (고정, 가이드봉 2개에 홀더 고정)",
          "SPEC":"PL 6T STS304 130×540(x −40~90, y ±270). 구멍: 소켓 Ø65.5(0,0) 플러시 삽입 양면 필릿 용접 / 가이드봉 Ø16.5 관통 2개소 @(45,±240) / 샤프트 홀더 SHFSS16 M5 탭 4개 @(25|65, ±240)(밑면 취부). 고정판 J1c 밑 390에 봉 2개(PSSFAQ16-590)로 매달림 — 이동 없음.",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 종전 이동판(J5e/J5f)·부시·실린더 폐지(낙하 주입, 승강 없음). 판 두께 6은 자중·노즐 반력만 받는 저스트값(하중 계산 미실시)."})
        save_new(d,P)
elif stage=="asm":
    a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); title=a.GetTitle.replace(".SLDASM","")
    def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
    def set_T(c,R,t):
        arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
        xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
    def move_fixed(c,R,t):
        a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
        set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
    def sel_comp(n): a.ClearSelection2(True); return a.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
    def set_supp(c,active):
        if (c.GetSuppression2==2)==active: return
        a.ClearSelection2(True); c.Select4(False,NOD,False)
        if active: a.EditUnsuppress2
        else: a.EditSuppress2
        a.ClearSelection2(True)
    states={}
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); cc=comps(); states[cfg]=[cc[n].GetSuppression2 for n in cc if n.startswith("G3d_")][0]; print("old fix state",cfg,states[cfg])
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    for n in list(cc):
        if n.startswith(("K1_","K2_","K3_","K4_","B9g_","J8e_","J9d_","G11f_","J11e_","B10_","J5f_")):
            sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    NEW={"H16c":("H16c_hose_nipple_PT2x52.5_L97.SLDPRT",2),"G13e":("G13e_socket_Rp2_KS_L56.SLDPRT",1),"J17c":("J17c_nozzle_pipe_50A_Sch40_L64.SLDPRT",1),
         "J19f":(f"J19f_hose_YASUNG_HSPF-050_straight_L{HOSE_L:g}.SLDPRT",1),"J5g":("J5g_nozzle_plate_130x540_t6.SLDPRT",1),"J23b":("J23b_shaft_support_MISUMI_SHFSS16_STEP.SLDPRT",4)}
    added={}
    for key,(fn,cnt) in NEW.items():
        p=Zp(fn); pre=fn.replace(".SLDPRT","")
        have=[n for n in comps() if n.startswith(pre+"-")]
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        for i in range(cnt-len(have)):
            c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0); assert c, fn
        a.EditRebuild3; added[key]=sorted([n for n in comps() if n.startswith(pre+"-")],key=lambda n:int(n.rsplit("-",1)[1])); print("added",key,added[key])
    PLACE={added["H16c"][0]:(I3,(0,0,Z_HN_TOP)), added["H16c"][1]:(R_FLIP,(0,0,Z_HN_BOT)), added["J19f"][0]:(I3,(0,0,HOSE_TOP)),
           added["G13e"][0]:(I3,(0,0,ZPL)), added["J5g"][0]:(I3,(0,0,ZPL)), added["J17c"][0]:(I3,(0,0,J17_TOP))}
    # J23b: 기존 2개(-1,-2)는 J1c 밑(45,±240,−10) 유지, 새 2개는 J5g 밑(45,±240,−396)
    j23=added["J23b"]; PLACE[j23[2]]=(I3,(45,240,ZPL-PL_T)); PLACE[j23[3]]=(I3,(45,-240,ZPL-PL_T))
    PIPING=[n for n in PLACE if not n.startswith(("J5g","J23b"))]
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,(R,t) in PLACE.items():
            c=cc[n]; set_supp(c,True); move_fixed(c,R,t)
            want=2 if cfg in ("상승","하강") else (states[cfg] if n in PIPING else 2)
            set_supp(c,want==2)
        a.ForceRebuild3(False); cc=comps()
        info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(PLACE)}
        print(f"[{cfg}] ww {ww(a)}")
        for n,v_ in info.items(): print("   ",n[:46],v_)
    a.ShowConfiguration2("상승"); a.EditRebuild3
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs)
    assert not any(r.startswith(("K1_","K2_","K3_","K4_","B9g_","J8e_","J9d_","G11f_","J11e_","B10_","J5f_")) for r in refs), refs
    json.dump({"refs":refs,"stack":{"HN_top":Z_HN_TOP,"hose":[HOSE_TOP,HOSE_BOT],"HN_bot":Z_HN_BOT,"socket":ZPL,"J17":[J17_TOP,J17_END]}},open(os.path.join(VER,"hose50_asm_0914.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("asm stage done (not saved)")
stop.set()
