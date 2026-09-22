# 2026-09-15: 사용자 지시 「호스는 직선으로, 일직선으로 내려」 — 밸브 밑 수직 호스 + 직선 승강(가이드봉·부시·이동판·TA2) 유지
#  고정: J1c → G13d → G3d(밸브) → H16c(고정, 바브 아래) → 호스(하강: 직선 L318 / 상승: 4원호 활 R≈45, +y 불룩 107) → H16c(뒤집음) → G13e 소켓(판 플러시) → J17c 노즐관
#  ※ 상승 활 R45 < 호스 외경 62 → 실물 접힘 위험(미확인). 사용자 결정으로 진행, SPEC·HANDOFF 표기.
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-15"
ENG=20.0; Z_VALVE_BOT=-178.0; HN_THR=29.0; HN_HEX=8.0; HN_BARB=60.0
Z_HN_TOP=Z_VALVE_BOT+ENG; HOSE_TOP=Z_HN_TOP-HN_THR-HN_HEX          # −158 / −195
ZP_UP=-390.0; ZP_DN=-530.0; SOCK_L=56.0
Z_HN_BOT=lambda zp: zp-ENG                                             # 뒤집힌 니플 원점
HOSE_BOT=lambda zp: Z_HN_BOT(zp)+HN_THR+HN_HEX                         # zp+17
L_HOSE=HOSE_TOP-HOSE_BOT(ZP_DN); D_UP=HOSE_TOP-HOSE_BOT(ZP_UP)          # 318 / 178
J17_TOP=lambda zp: zp-SOCK_L+ENG
TA2_X=85.0; TA2_Y=0.0
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_FLIP=[[1,0,0],[0,-1,0],[0,0,-1]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
# ---- 상승 활 해: 4원호 대칭 (+t,-t,-t,+t), 4R sin t = D_UP, 4R t = L
STUB=HN_BARB   # 바브 위 60은 직선(호스가 니플에 끼워진 구간)
def solve_bow():
    f=lambda t: math.sin(t)/t-(D_UP-2*STUB)/(L_HOSE-2*STUB)
    lo,hi=0.5,3.0
    for _ in range(80):
        mid=(lo+hi)/2
        if f(lo)*f(mid)<=0: hi=mid
        else: lo=mid
    t=(lo+hi)/2; R=(L_HOSE-2*STUB)/(4*t); return R,t
R_BOW,T_BOW=solve_bow(); BULGE=2*R_BOW*(1-math.cos(T_BOW))
print(f"hose: L {L_HOSE} D_UP {D_UP} → bow R {R_BOW:.2f} t {math.degrees(T_BOW):.1f}° bulge {BULGE:.1f}")
def segs_from(list_):
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    for it in list_:
        if it[0]=="line":
            dd=it[1]; x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1; continue
        rad,ang=it[1],it[2]
        if abs(ang)<1e-9: continue
        side=1 if ang>0 else -1
        cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
        h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
        segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    return segs,(x,y)
segs_up,end_up=segs_from([("line",STUB),("arc",R_BOW,T_BOW),("arc",R_BOW,-T_BOW),("arc",R_BOW,-T_BOW),("arc",R_BOW,T_BOW),("line",STUB)])
print("bow end",[round(v,2) for v in end_up],"(expect 0,",-D_UP,")")
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
def orphan_sketches(d):
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
def clean_orphans(d):
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3; return orphan_sketches(d)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def set_props(d,props,mat=None):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    if mat:
        try: d.SetMaterialPropertyName2("","이텍",mat)
        except Exception as ex: print("  mat exc",ex)
def save_new(d,path):
    orph=clean_orphans(d); assert not orph, ("orphans remain",orph)
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d),"orphans 0"); assert ok
HOSE_SPEC="야성하이텍 슈퍼스프링호스(무독) HSPF-050: 내경 50.0±1.5·외경 62.0±1.5·0.4/1.6 MPa·강선+무독 특수수지·0~60 ℃(카탈로그 2025-11 p.28). 3D 내경은 바브 위 52.5 표현. 절단 = 자유길이 318 + 바브 2×60 ≈ 438. 최소 굽힘반경 카탈로그 미기재."
P_DN=Zp(f"J19h_hose_YASUNG_HSPF-050_dn_straight_L{L_HOSE:g}.SLDPRT"); P_UP=Zp(f"J19h_hose_YASUNG_HSPF-050_up_bow_R{R_BOW:.0f}.SLDPRT")
P5=Zp("J5e_moving_plate_180x540_t8.SLDPRT"); P5i=Zp("J5i_moving_plate_180x540_t8.SLDPRT")
stage=sys.argv[1] if len(sys.argv)>1 else "parts"
if stage=="parts":
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith("파트"): app.CloseDoc(tt); print("closed unsaved",tt)
    # ---- 직선 호스(하강)
    if not os.path.exists(P_DN):
        d=app.NewDocument(tmpl,0,0,0)
        assert sel_plane(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(31.0)); sm.CreateCircleByRadius(0,0,0,mm(26.25)); sm.AddToDB=False
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(L_HOSE),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f; f.Name="호스_직선"
        bx=partbox(d); assert abs(bx[2]+L_HOSE)<0.1 and abs(bx[5])<0.1, bx
        set_props(d,{"TITLE":"HOSE 50A (하강 상태, 직선) — YASUNG HSPF-050","SPEC":HOSE_SPEC+f" 하강(스트로크 140): 직선, 낙차 {L_HOSE:g}.","Material":"PVC","QT'Y":"1","DATE":DATE,
          "REMARK":"구매품(야성판매). 사용자 지시(09-15) 「호스는 직선으로 일직선 승강」. −30 ℃·염수 적합성 원문 없음."},mat="PVC 경질"); save_new(d,P_DN)
    # ---- 활 호스(상승): 경로 정면(XY, 원점에서 −Y 시작) 4원호, 프로파일 윗면
    if not os.path.exists(P_UP):
        done=False
        for direction in (1,-1):
            dh=app.NewDocument(tmpl,0,0,0)
            assert sel_plane(dh,"정면"); dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
            for sg in segs_up:
                if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0); continue
                cc_,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]; sm.CreateArc(mm(cc_[0]),mm(cc_[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
            sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
            Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
            print(f"  bow direction {direction}: sketch length {Ls:.1f} (target {L_HOSE:g})")
            if abs(Ls-L_HOSE)>2.0: app.CloseDoc(dh.GetTitle); continue
            assert sel_plane(dh,"윗면"); dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(31.0)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(26.25)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
            dh.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or dh.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
            dh.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or dh.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
            f=None
            for attempt in ("swept3","swept4"):
                try:
                    if attempt=="swept3": f=dh.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                    else: f=dh.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                    if f: break
                except Exception as ex: print("  ",attempt,"exc",ex)
            if not f: print("  sweep failed dir",direction); app.CloseDoc(dh.GetTitle); continue
            dh.EditRebuild3; bx=partbox(dh); print("  bow box",bx,"bodies",len(bodies(dh)))
            # 기대: y −D_UP−31 ~ +31, x −31 ~ bulge+31 (부호는 direction에 따라 반대일 수 있음 → |x| 최대 검사)
            if not (len(bodies(dh))==1 and abs(bx[1]+D_UP)<1.0 and (abs(bx[3]-(BULGE+31))<1.5 or abs(bx[0]+(BULGE+31))<1.5)): app.CloseDoc(dh.GetTitle); continue
            set_props(dh,{"TITLE":"HOSE 50A (상승 상태, 활 굽힘) — YASUNG HSPF-050","SPEC":HOSE_SPEC+f" 상승(낙차 {D_UP:g}): 바브 구간 60×2 직선 + 4원호 활 R{R_BOW:.1f} ±{math.degrees(T_BOW):.1f}°, 옆으로 {BULGE:.0f} 불룩. **R{R_BOW:.0f} < 호스 외경 62 → 실물 접힘(킹크) 위험, 굽힘반경 미확인** — 실물 확인 전 미확정.","Material":"PVC","QT'Y":"1","DATE":DATE,
              "REMARK":"구매품(야성판매). 사용자 지시(09-15) 「호스는 직선으로」에 따라 세로 직선 배치. 상승 상태 굽힘은 물리적 성립 여부 미확인(2\" 스프링호스 통례 R≥127)."},mat="PVC 경질")
            save_new(dh,P_UP); done=True; break
        assert done, "bow hose"
    # ---- J5i 이동판: J5e SaveAs → 구멍 (0,10)Ø32 → (0,0)Ø65.5 (소켓 플러시)
    if not os.path.exists(P5i):
        d=act(P5); e=I4(); w=I4(); ok=d.Extension.SaveAs(P5i,0,1,NOD,e,w); print("SaveAs J5i",ok); assert ok
        d=act(P5i)
        if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
        for s in list(pv(sk,"GetSketchSegments") or []):
            ty=s.GetType() if callable(s.GetType) else s.GetType
            if ty==1:
                cpt=pv(s,"GetCenterPoint2")
                try: cx,cy=cpt[0]*1000,cpt[1]*1000
                except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
                r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
                if abs(cx)<0.5 and abs(cy-10)<0.5 and 15<r<18: s.Select4(True,NOD); n+=1
        if n: d.Extension.DeleteSelection2(0); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(32.75)); d.SketchManager.AddToDB=False
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); bx=partbox(d); print("J5i hole",n,"box",bx,"ww",ww(d)); assert not ww(d) and n==1
        cp=d.Extension.CustomPropertyManager("")
        for k in ("TITLE","SPEC"):
            s_=cp.Get(k) or ""; s_=s_.replace("소켓 Ø32(KS Rp 소켓 OD)","소켓 G13e(Rp2, OD 65) Ø65.5 플러시 삽입 구멍(0,0), 양면 필릿 용접(앞 가장자리 여유 12.25)").replace("소켓 Ø32","소켓 Ø65.5"); cp.Set2(k,s_)
        cp.Set2("DATE",DATE); orph=clean_orphans(d); assert not orph; e=I4(); w=I4(); print("save J5i",d.Save3(1,e,w))
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
        a.ShowConfiguration2(cfg); cc=comps(); states[cfg]=[cc[n].GetSuppression2 for n in cc if n.startswith("G3d_")][0]
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    for n in list(cc):
        if n.startswith(("E50_","N1_","P1_","P2_","J19g_")): sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    olds=[n for n in cc if n.startswith("J5h_")]
    if olds:
        if app.GetOpenDocumentByName(P5i) is None: open_doc(app,P5i,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P5i,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J5h→J5i",ok); assert ok; cc=comps()
    for n in list(cc):
        if n.startswith("J19h_hose_YASUNG_HSPF-050_up_bow_R45"): sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    NEW={"G13e":("G13e_socket_Rp2_KS_L56.SLDPRT",2),"J17c":("J17c_nozzle_pipe_50A_Sch40_L64.SLDPRT",2),"HDN":(os.path.basename(P_DN),1),"HUP":(os.path.basename(P_UP),1),"H16c":("H16c_hose_nipple_PT2x52.5_L97.SLDPRT",3)}
    added={}
    for key,(fn,cnt) in NEW.items():
        p=Zp(fn); pre=fn.replace(".SLDPRT","")
        have=[n for n in comps() if n.startswith(pre+"-")]
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        for i in range(cnt-len(have)):
            c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0); assert c, fn
        a.EditRebuild3; added[key]=sorted([n for n in comps() if n.startswith(pre+"-")],key=lambda n:int(n.rsplit("-",1)[1])); print("added",key,added[key])
    cc=comps()
    PLACE={}
    PLACE[added["H16c"][0]]=(I3,(0,0,Z_HN_TOP),"fix")
    for i,(zp,grp) in enumerate(((ZP_UP,"up"),(ZP_DN,"dn"))):
        PLACE[added["H16c"][1+i]]=(R_FLIP,(0,0,Z_HN_BOT(zp)),grp); PLACE[added["G13e"][i]]=(I3,(0,0,zp),grp); PLACE[added["J17c"][i]]=(I3,(0,0,J17_TOP(zp)),grp)
    PLACE[added["HDN"][0]]=(I3,(0,0,HOSE_TOP),"dn"); PLACE[added["HUP"][0]]=(R_HOSE,(0,0,HOSE_TOP),"up")
    # TA2 그룹 y −80 → 0, x 85
    for n in cc:
        if n.startswith(("B9g_","J8e_")): PLACE[n]=(I3,(TA2_X,TA2_Y,-26.0),"fix")
        elif n.startswith("G11f_"): PLACE[n]=(I3,(TA2_X,TA2_Y-11.2,-26.0),"fix")
        elif n.startswith("J9d_"): PLACE[n]=(I3,(TA2_X,TA2_Y,ZP_UP if n.endswith("-1") else ZP_DN),"up" if n.endswith("-1") else "dn")
        elif n.startswith("J11e_"): PLACE[n]=(I3,(TA2_X,TA2_Y-8.8,(ZP_UP if n.endswith("-1") else ZP_DN)+25.0),"up" if n.endswith("-1") else "dn")
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,(R,t,grp) in PLACE.items():
            c=cc[n]; tt=t
            STRUCT=n.startswith(("J9d","J8e"))
            if cfg=="상승": want=grp in ("fix","up")
            elif cfg=="하강": want=grp in ("fix","dn")
            elif STRUCT: want=(grp=="fix") or (grp=="up" and cfg.startswith("1.")) or (grp=="dn" and cfg.startswith("2."))
            else: want=(states[cfg]==2)
            set_supp(c,True); move_fixed(c,R,tt)
            if n.startswith("B9g_") and cfg in ("상승","하강"):
                try: c.ReferencedConfiguration=cfg
                except Exception as ex: print("  refcfg exc",ex)
            set_supp(c,bool(want))
        a.ForceRebuild3(False); cc=comps()
        info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(PLACE)}
        print(f"[{cfg}] ww {ww(a)}")
        for n,v_ in info.items(): print("   ",n[:48],v_)
    a.ShowConfiguration2("상승"); a.EditRebuild3
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs)
    assert not any(r.startswith(("E50_","N1_","P1_","P2_","J19g_","J5h_")) for r in refs), refs
    json.dump({"refs":refs,"hose":{"L":L_HOSE,"D_UP":D_UP,"R_bow":R_BOW,"bulge":BULGE}},open(os.path.join(VER,"straight50_asm_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    print("asm stage done (not saved)")
stop.set()
