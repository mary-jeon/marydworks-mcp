# 2026-09-14: 50A 텔레스코픽 라인 — 파트 마무리(G3d 포트 컷·속성, B4d 속성, J1c 구멍, J5f 판) + 어셈블리 재구성 + 간섭
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
DATE="2026-09-14"
# ---- 배치 상수(라인 좌표, 고정판 상면 z 0)
ENG=20.0; BN_L=58.0; VALVE_L=140.0; PAD=78.0
Z_VALVE_TOP=-BN_L+ENG; Z_VALVE_C=Z_VALVE_TOP-VALVE_L/2; Z_VALVE_BOT=Z_VALVE_TOP-VALVE_L   # -38 / -108 / -178
Z_K1=Z_VALVE_BOT+ENG            # -158 플런저 상단
CAP_TOP=-190.0; CAP_L=45.0; K2_TOP=CAP_TOP-CAP_L+8.0   # -227
K4_1=CAP_TOP-10.9; K4_2=CAP_TOP-25.9
ZP_UP=-390.0; ZP_DN=-530.0; STROKE=ZP_UP-ZP_DN
TA2_X_OLD=70.0; TA2_X=85.0
I3=[[1,0,0],[0,1,0],[0,0,1]]
R_G3D=[[0,1,0],[-1,0,0],[0,0,1]]     # 파트 z(유로)→라인 z, 파트 y(스템)→라인 -x, 파트 x→라인 +y
R_B4D=[[0,0,1],[0,1,0],[-1,0,0]]     # 파트 z(스템, 몸체 +z)→라인 -x, 파트 x→라인 +z, 파트 y→라인 +y
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in (pv(d,"GetBodies2",0,True) or []))
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}.get(nm,nm)
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def sketch_circle_on(d,plane,cx,cy,r):
    assert sel_plane(d,plane),plane; d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(mm(cx),mm(cy),0,mm(r)); d.SketchManager.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def del_feat(d,name):
    d.ClearSelection2(True); assert d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(name,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(name,"SKETCH",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
def set_props(d,props):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
def circ_xy(s):
    cpt=pv(s,"GetCenterPoint2")
    try: cx,cy=cpt[0]*1000,cpt[1]*1000
    except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
    r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
    return cx,cy,r
stage=sys.argv[1] if len(sys.argv)>1 else "parts"
rep={}
if stage=="parts":
    # ---------- G3d: 포트 나사부 표현 컷 D60.6 x 20 (양단 z ±70), 속성, 재질
    P=Zp("G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT"); d=act(P); v0=vol(d); print("G3d vol0",round(v0),"box",partbox(d))
    EXP=math.pi/4*(60.6**2-49**2)*ENG
    for tag,zoff in (("상",70.0),("하",-70.0)):
        fn="포트컷_"+tag
        if fn in feat_names(d): continue
        done=False
        for pl_sign in (1,-1):
            assert sel_plane(d,"정면"); pl=d.FeatureManager.InsertRefPlane(8,mm(pl_sign*zoff),0,0,0,0); assert pl,"plane"; pl.Name="포트면_"+tag
            for dirflag in (True,False):
                sk=sketch_circle_on(d,"포트면_"+tag,0,0,30.3)
                f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(ENG),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
                if f is None:
                    del_feat(d,sk); continue
                f.Name=fn; v1=vol(d); dv=v0-v1; bx=partbox(d)
                print(f"  {fn} plane {pl_sign*zoff} dir {dirflag}: dV {dv:.0f} (exp {EXP:.0f}) box z {bx[2]}..{bx[5]}")
                if abs(dv-EXP)<EXP*0.15 and abs(bx[5]-70.99)<0.2 and abs(bx[2]+71.03)<0.2: done=True; v0=v1; break
                del_feat(d,fn)
            if done: break
            del_feat(d,"포트면_"+tag)
        assert done, fn
    print("G3d after cuts vol",round(vol(d)),"ww",ww(d)); assert not ww(d)
    set_props(d,{"TITLE":"BALL VALVE 3PC 2in ISO5211 (Tameson BL2SA3-200)",
      "SPEC":"Tameson BL2SA3-200: 3PC 볼밸브 G2(BSPP 암나사) DN50 풀보어, 면간 140(DIN 3202-M3), ISO 5211 F05/F07 패드(축→패드면 78), 스템 □14(끝 93.2), PN63, 몸체·볼 1.4408(CF8M/STS316 상당), 시트 PTFE 15%GF, 스템 2차 실 FKM, -20~+180 ℃, Kv 265. 질량 4.4 kg(매뉴얼) / 4.2 kg(웹) 상충. 작동 토크 원문 미기재(미확인).",
      "Material":"STS316","QT'Y":"1","DATE":DATE,
      "REMARK":"3D: tameson.com CAD zip bl2sa3-200.step(Landefeld KH 203 F ES 원본) 임포트, 유로축 Z·스템 +Y로 정렬(이동/회전 피처). 포트컷_상/하 = G2 암나사부 표현(D60.6x20, 니플 겹침 제거용 표현 컷)."})
    try: d.SetMaterialPropertyName2("","이텍","STS 316")
    except Exception as ex: print("mat exc",ex)
    e=I4(); w=I4(); print("save G3d",d.Save3(1,e,w),e.value)
    # ---------- B4d 속성
    P=Zp("B4d_actuator_KOSAPLUS_KE008-F357C14-DC.SLDPRT"); d=act(P); print("B4d box",partbox(d),"bodies",len(pv(d,"GetBodies2",0,True) or []))
    set_props(d,{"TITLE":"ELECTRIC ACTUATOR KOSAPLUS KE008 (24 VDC, ISO5211 F05/F07 sq14)",
      "SPEC":"코사플러스 KE008 F357C14, 24 VDC(모델코드 2D), MAX 토크 80 N·m, 작동시간 17/14 s, 정격전류 2.5 A, ISO 5211 F03/F05/F07(M5/M6/M8 TAP DP12), 스템 □14(홈 깊이 16 데이터북 / 19 도면 / 15 별지 — 상충·미확인), IP67, -20~+60 ℃, Duty 40 %, 질량 2.6 kg, 외형 155.5(스템축)x125.3x122.3, 케이블 2-PF1/2. 선정: 코사 데이터북 v5.4 선정표 2인치 볼밸브 → KE008. 밸브 자체 토크 미확인이라 여유율 미기재.",
      "Material":"미확인(카탈로그 미기재)","QT'Y":"1","DATE":DATE,
      "REMARK":"3D: kosaplus.com Drawing 게시판 KE008_F357C14_2013.step(20파트) → InsertPart3 합성(스템축 Z, 패드면 z 0). 히터는 AC 전용(DC 없음). 로봇 밸브 KE002와 같은 제조사."})
    e=I4(); w=I4(); print("save B4d",d.Save3(1,e,w),e.value)
    # ---------- J1c 구멍 D27 → D61 (스케치3 제자리)
    P=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); d=act(P)
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치3","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
    for s in list(pv(sk,"GetSketchSegments") or []):
        ty=s.GetType() if callable(s.GetType) else s.GetType
        if ty==1:
            cx,cy,r=circ_xy(s)
            if abs(cx)<0.5 and abs(cy)<0.5 and 13<r<14: s.Select4(True,NOD); n+=1
    if n: d.Extension.DeleteSelection2(0); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(30.5)); d.SketchManager.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); print("J1c hole edited",n,"ww",ww(d),"box",partbox(d)); assert not ww(d)
    cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("SPEC") or ""; cp.Set2("SPEC",s_.replace("유로 구멍 Ø27(0,0): 배럴 니플 G13c R3/4를 10 삽입해 밑면 필릿 용접","유로 구멍 Ø61(0,0): 배럴 니플 G13d R2(50A)를 10 삽입해 밑면 필릿 용접"))
    e=I4(); w=I4(); print("save J1c",d.Save3(1,e,w),e.value)
    # ---------- J5e → J5f: 폭 180→210(x -75~135), 소켓 구멍 (0,10) D32 → (0,0) D76.5
    P5=Zp("J5e_moving_plate_180x540_t8.SLDPRT"); P5f=Zp("J5f_moving_plate_210x540_t8.SLDPRT")
    if not os.path.exists(P5f):
        d=act(P5); e=I4(); w=I4(); ok=d.Extension.SaveAs(P5f,0,1,NOD,e,w); print("SaveAs J5f",ok,e.value); assert ok
        d=act(P5f)
        if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0; lines=[]
        for s in list(pv(sk,"GetSketchSegments") or []):
            ty=s.GetType() if callable(s.GetType) else s.GetType
            if ty==0:
                sp_=pv(s,"GetStartPoint2"); ep_=pv(s,"GetEndPoint2")
                try: x0,y0,x1,y1=sp_[0]*1000,sp_[1]*1000,ep_[0]*1000,ep_[1]*1000
                except TypeError: x0,y0,x1,y1=pv(sp_,"X")*1000,pv(sp_,"Y")*1000,pv(ep_,"X")*1000,pv(ep_,"Y")*1000
                lines.append((round(x0,1),round(y0,1),round(x1,1),round(y1,1)))
                cg=s.ConstructionGeometry
                if callable(cg): cg=cg()
                if cg: continue
                s.Select4(True,NOD); n+=1
            elif ty==1:
                cx,cy,r=circ_xy(s)
                if abs(cx)<0.5 and abs(cy-10)<0.5 and 15<r<18: s.Select4(True,NOD); n+=1
        print("J5f sketch lines",lines,"selected",n)
        if n: d.Extension.DeleteSelection2(0)
        sm=d.SketchManager; sm.AddToDB=True; sm.CreateCornerRectangle(mm(-75),mm(-270),0,mm(135),mm(270),0); sm.CreateCircleByRadius(0,0,0,mm(38.25)); sm.AddToDB=False
        try:
            rm=d.SketchManager.ActiveSketch.RelationManager; dang=list(pv(rm,"GetRelations",1) or [])
            for rel in dang: rm.DeleteRelation(rel)
            if dang: print("  dangling relations removed",len(dang))
        except Exception as ex: print("  relation cleanup skipped",ex)
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); bx=partbox(d); print("J5f box",bx,"ww",ww(d)); assert not ww(d) and abs(bx[0]+75)<0.1 and abs(bx[3]-135)<0.1 and abs(bx[1]+270)<0.1, bx
        cp=d.Extension.CustomPropertyManager("")
        for k in ("TITLE","SPEC"):
            s_=cp.Get(k) or ""; s_=s_.replace("180x540","210x540").replace("180×540","210×540").replace("소켓 Ø32(KS Rp 소켓 OD)","슬리브 관 K2 Ø76.5 관통 구멍(0,0), 양면 필릿 용접").replace("소켓 Ø32","슬리브 관 Ø76.5")
            cp.Set2(k,s_)
        cp.Set2("DATE",DATE); e=I4(); w=I4(); print("save J5f",d.Save3(1,e,w),e.value)
    else: print("J5f exists")
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
    # 1) 구성별 구 부품 억제 상태 기록
    states={}
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); cc=comps()
        states[cfg]={"fix":[cc[n].GetSuppression2 for n in cc if n.startswith("G3c_")][0],
                     "up":[cc[n].GetSuppression2 for n in cc if n.startswith("G13b_socket_Rp3-4_KS_L36-10")][0],
                     "dn":[cc[n].GetSuppression2 for n in cc if n.startswith("G13b_socket_Rp3-4_KS_L36-11")][0]}
        print("old states",cfg,states[cfg])
    rep["old_states"]=states
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    # 2) 구 부품 삭제
    for n in list(cc):
        if n.startswith(("G13c_","G3c_","B4c_","G13b_","H16b_","J17b_","J19e_")):
            sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    # 3) J5e → J5f 교체(전 인스턴스)
    P5f=Zp("J5f_moving_plate_210x540_t8.SLDPRT")
    olds=[n for n in cc if n.startswith("J5e_")]
    if olds:
        if app.GetOpenDocumentByName(P5f) is None: open_doc(app,P5f,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P5f,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J5e→J5f",ok); assert ok; cc=comps()
    # 4) 신규 부품 추가
    NEW={"G13d":("G13d_barrel_nipple_R2_KS_L58.SLDPRT",1),"G3d":("G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT",1),"B4d":("B4d_actuator_KOSAPLUS_KE008-F357C14-DC.SLDPRT",1),
         "K1":("K1_plunger_pipe_50A_Sch40_L227.SLDPRT",1),"K2":("K2_sleeve_pipe_65A_Sch10S_L263.SLDPRT",2),"K3":("K3_seal_cap_D90_L45.SLDPRT",2),"K4":("K4_oring_P60.SLDPRT",4)}
    added={}
    for key,(fn,cnt) in NEW.items():
        p=Zp(fn); pre=fn.replace(".SLDPRT","")
        have=[n for n in comps() if n.startswith(pre+"-")]
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        for i in range(cnt-len(have)):
            c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0); assert c, fn
        a.EditRebuild3; added[key]=sorted([n for n in comps() if n.startswith(pre+"-")],key=lambda n:int(n.rsplit("-",1)[1])); print("added",key,added[key])
    cc=comps()
    # 5) 배치표: (R, t, group)  group: fix / up / dn
    PLACE={}
    PLACE[added["G13d"][0]]=(I3,(0,0,0),"fix"); PLACE[added["G3d"][0]]=(R_G3D,(0,0,Z_VALVE_C),"fix"); PLACE[added["B4d"][0]]=(R_B4D,(-PAD,0,Z_VALVE_C),"fix"); PLACE[added["K1"][0]]=(I3,(0,0,Z_K1),"fix")
    for i,(zp,grp) in enumerate(((ZP_UP,"up"),(ZP_DN,"dn"))):
        dz=zp-ZP_UP
        PLACE[added["K2"][i]]=(I3,(0,0,K2_TOP+dz),grp); PLACE[added["K3"][i]]=(I3,(0,0,CAP_TOP+dz),grp)
        PLACE[added["K4"][2*i]]=(I3,(0,0,K4_1+dz),grp); PLACE[added["K4"][2*i+1]]=(I3,(0,0,K4_2+dz),grp)
    TA2=[n for n in cc if n.startswith(("B9g_","J8e_","J9d_","G11f_","J11e_"))]; print("TA2 group",TA2)
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); st=states[cfg]
        for n,(R,t,grp) in PLACE.items():
            c=cc[n]
            if cfg=="상승": want=2 if grp in ("fix","up") else 0
            elif cfg=="하강": want=2 if grp in ("fix","dn") else 0
            else: want=st["fix"] if grp=="fix" else (st["up"] if grp=="up" else st["dn"])
            set_supp(c,True); move_fixed(c,R,t); set_supp(c,want==2)
        for n in TA2:
            c=cc[n]; xf=xform(c); t=xf["t_mm"]; R=xf["R"]
            if abs(t[0]-TA2_X_OLD)<0.01:
                sup=c.GetSuppression2; set_supp(c,True); move_fixed(c,R,(TA2_X,t[1],t[2])); set_supp(c,sup==2)
        a.ForceRebuild3(False); cc=comps()
        info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(list(PLACE)+TA2)}
        rep.setdefault("cfg",{})[cfg]={"ww":ww(a),"info":info}; print(f"[{cfg}] ww {ww(a)}")
        for n,v_ in info.items(): print("   ",n[:46],v_)
    a.ShowConfiguration2("상승"); a.EditRebuild3
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs); rep["refs"]=refs
    assert not any(r.startswith(("G13b_","G13c_","G3c_","B4c_","H16b_","J17b_","J19e_","J5e_")) for r in refs), refs
    json.dump(rep,open(os.path.join(VER,"asm50_0914.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
    print("asm stage done (not saved)")
stop.set()
