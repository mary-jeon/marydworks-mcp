# 2026-09-15: 사용자 확인안 — TA2 뒤(x 85)·이동판 180×540(x −45~135)·샤프트 판 중앙(45,±240)·홀더 SHFSS16(J23b) 복귀(K6·J23c 제거)·J1c 봉 구멍/탭 복귀
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-15"
ZP_UP=-425.0; ZP_DN=-510.0; TA2_X=85.0; TA2_Y=0.0; PIN_H=60.0; SH_X=45.0; SH_Y=240.0
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_B10=[[0,0,-1],[0,1,0],[1,0,0]]; R_J23B1=[[-1,0,0],[0,-1,0],[0,0,1]]
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
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
def clean(d):
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3; return orphan_sketches(d)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def set_props(d,props,mat=None):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    if mat:
        try: d.SetMaterialPropertyName2("","이텍",mat)
        except Exception as ex: print("  mat exc",ex)
def circ_xy(s):
    cpt=pv(s,"GetCenterPoint2")
    try: cx,cy=cpt[0]*1000,cpt[1]*1000
    except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
    r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
    return cx,cy,r
def edit_circles(d,sketch,rule,new_circles):
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); assert d.Extension.SelectByID2(sketch,"SKETCH",0,0,0,False,0,NOD,0), sketch; d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
    for s in list(pv(sk,"GetSketchSegments") or []):
        ty=s.GetType() if callable(s.GetType) else s.GetType
        if ty==1:
            cx,cy,r=circ_xy(s)
            if rule(cx,cy,r): s.Select4(True,NOD); n+=1
    if n: d.Extension.DeleteSelection2(0)
    sm=d.SketchManager; sm.AddToDB=True
    for cx,cy,r in new_circles: sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(r))
    sm.AddToDB=False
    try:
        rm=d.SketchManager.ActiveSketch.RelationManager; dang=list(pv(rm,"GetRelations",1) or [])
        for rel in dang: rm.DeleteRelation(rel)
    except Exception as ex: print("  relation cleanup skipped",ex)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); return n
P5L=Zp("J5l_moving_plate_180x540_t8.SLDPRT")
stage=sys.argv[1] if len(sys.argv)>1 else "parts"
if stage=="parts":
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith("파트"): app.CloseDoc(tt); print("closed unsaved",tt)
    # ---- J5l 이동판 180×540 t8: 소켓 Ø49 @(0,0), 부시 @(45,±240)
    if not os.path.exists(P5L):
        d=app.NewDocument(tmpl,0,0,0)
        def draw(sm):
            sm.CreateCornerRectangle(mm(-45),mm(-270),0,mm(135),mm(270),0); sm.CreateCircleByRadius(0,0,0,mm(24.5))
            for sy in (SH_Y,-SH_Y):
                sm.CreateCircleByRadius(mm(SH_X),mm(sy),0,mm(14.25))
                for dx,dy in ((19,0),(-19,0),(0,19),(0,-19)): sm.CreateCircleByRadius(mm(SH_X+dx),mm(sy+dy),0,mm(1.65))
        new_sketch(d,"정면",draw)
        f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(8.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f; f.Name="판_t8"
        bx=bbox(d); assert abs(bx[0]+45)<0.1 and abs(bx[3]-135)<0.1 and abs(bx[2]+8)<0.1, bx
        set_props(d,{"TITLE":"MOVING PLATE 180x540 t8 (32A 라인)","SPEC":"PL 8T STS304 180×540(x −45~135, y ±270). 구멍: 소켓 ONDA SFS3-32 Ø49(0,0) 상면 플러시 삽입 양면 필릿 용접 / 부시 LHFRW16 Ø28.5 + M4 탭 4(PCD 38) @(45,±240) = 판 중앙. 러그 J9f 밑면 용접 @(85,0). 공차: 별도 속성 TOLERANCE 참조.",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 사용자 09-15: 실린더 뒤(x 85)·샤프트 판 중앙(45). 하중 검토·Simulation 미실시."},mat="STS 304")
        orph=clean(d); assert not orph; e=I4(); w=I4(); ok=d.Extension.SaveAs(P5L,0,1,NOD,e,w); print("saved J5l",ok); app.CloseDoc(d.GetTitle)
    # ---- J1c: 봉 구멍 (0,±240)→(45,±240), 홀더 탭 M5(Ø4.2) @(25|65,±240) 복귀
    P1=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); d=act(P1)
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    n=edit_circles(d,"스케치3",lambda cx,cy,r: abs(cx)<0.5 and abs(abs(cy)-240)<0.5 and 8<r<8.5,[(SH_X,SH_Y,8.25),(SH_X,-SH_Y,8.25),(25,SH_Y,2.1),(65,SH_Y,2.1),(25,-SH_Y,2.1),(65,-SH_Y,2.1)])
    print("J1c edited",n,"ww",ww(d)); assert not ww(d)
    cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("SPEC") or ""
    s_=s_.replace("가이드봉 Ø16.5 관통 2개소 @(0,±240)","가이드봉 Ø16.5 관통 2개소 @(45,±240)").replace(" | 09-15: 봉 (0,±240)로 이동, 홀더 탭 삭제(SK16 서포트는 L브래킷 K6 용접), TA2 러그 J8e @(0,−110)."," | 09-15: 봉 (45,±240)=이동판 중앙 복귀, 홀더 SHFSS16 M5 탭 @(25|65,±240) 복귀, TA2 러그 J8e @(85,0).")
    cp.Set2("SPEC",s_); orph=clean(d); assert not orph; e=I4(); w=I4(); print("save J1c",d.Save3(1,e,w),e.value)
elif stage=="asm":
    j9=json.load(open(os.path.join(VER,"j9f_build_0915.json")))["box"]
    ysign=1 if j9[4]>1 else -1; zsign=1 if j9[5]>1 else -1
    R_J9=[[1,0,0],[0,ysign*(1 if zsign>0 else -1),0],[0,0,zsign]]
    if np.linalg.det(np.array(R_J9))<0: R_J9=[[-1,0,0],[0,R_J9[1][1],0],[0,0,R_J9[2][2]]]
    yoff=-3.0 if (ysign*R_J9[1][1])>0 else 3.0
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
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    for n in list(cc):
        if n.startswith(("K6_","J23c_")): sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3; cc=comps()
    olds=[n for n in cc if n.startswith("J5k_")]
    if olds:
        if app.GetOpenDocumentByName(P5L) is None: open_doc(app,P5L,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P5L,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J5k→J5l",ok); assert ok; cc=comps()
    PJ=Zp("J23b_shaft_support_MISUMI_SHFSS16_STEP.SLDPRT")
    have=[n for n in cc if n.startswith("J23b_")]
    if app.GetOpenDocumentByName(PJ) is None: open_doc(app,PJ,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    for i in range(2-len(have)):
        c=a.AddComponent5(PJ,0,"",False,"",0.0,0.0,0.0); assert c
    a.EditRebuild3; cc=comps(); j23=sorted([n for n in cc if n.startswith("J23b_")],key=lambda n:int(n.rsplit("-",1)[1])); print("J23b",j23)
    PLACE={}
    PLACE[j23[0]]=(R_J23B1,(SH_X,SH_Y,-10),"fix"); PLACE[j23[1]]=(I3,(SH_X,-SH_Y,-10),"fix")
    for n in cc:
        if n.startswith(("B9g_","J8e_")): PLACE[n]=(I3,(TA2_X,TA2_Y,-26.0),"fix")
        elif n.startswith("G11f_"): PLACE[n]=(I3,(TA2_X,TA2_Y-11.2,-26.0),"fix")
        elif n.startswith("J11e_"):
            up=n.endswith("-1"); PLACE[n]=(I3,(TA2_X,TA2_Y-8.8,(ZP_UP if up else ZP_DN)+PIN_H),"up" if up else "dn")
        elif n.startswith("J9f_"):
            up=n.endswith("-1"); PLACE[n]=(R_J9,(TA2_X,TA2_Y+yoff,ZP_UP if up else ZP_DN),"up" if up else "dn")
        elif n.startswith("J5l_"):
            up=n.endswith("-1"); PLACE[n]=(I3,(0,0,ZP_UP if up else ZP_DN),"up" if up else "dn")
        elif n.startswith("J2c_"): pass
        elif n.startswith("B10_"):
            i=int(n.rsplit("-",1)[1]); PLACE[n]=(R_B10,(SH_X,SH_Y if i in (1,3) else -SH_Y,ZP_UP if i in (1,2) else ZP_DN),"up" if i in (1,2) else "dn")
    sh=sorted([n for n in cc if n.startswith("J2c_")],key=lambda n:int(n.rsplit("-",1)[1]))
    for i,n in enumerate(sh): PLACE[n]=(I3,(SH_X,SH_Y if i==0 else -SH_Y,0),"fix")
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,(R,t,grp) in PLACE.items():
            c=cc[n]; STRUCT=n.startswith(("J5l","J9f","J8e","B10"))
            if cfg=="상승": want=grp in ("fix","up")
            elif cfg=="하강": want=grp in ("fix","dn")
            elif STRUCT: want=(grp=="fix") or (grp=="up" and cfg.startswith("1.")) or (grp=="dn" and cfg.startswith("2."))
            else: want=(grp=="fix") and not n.startswith(("B9g","G11f"))
            set_supp(c,True); move_fixed(c,R,t)
            if n.startswith("B9g_") and cfg in ("상승","하강"):
                try: c.ReferencedConfiguration=cfg
                except Exception as ex: print("  refcfg exc",ex)
            set_supp(c,bool(want))
        a.ForceRebuild3(False); cc=comps()
        print(f"[{cfg}] ww {ww(a)}",[(n[:14],xform(cc[n])["t_mm"]) for n in sorted(PLACE) if n.startswith(("J23b","B9g","J2c","J5l"))])
    a.ShowConfiguration2("상승"); a.EditRebuild3
    def interf(items):
        a.ClearSelection2(True)
        for c in items: c.Select4(True,NOD,False)
        idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
        rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
    rep={}
    for cfg in ("상승","하강"):
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
        rows=interf(act_); rep[cfg]=rows; print(f"[{cfg}] 간섭 {len(rows)}",[r for r in rows if r[1]>1.0][:8])
    a.ShowConfiguration2("상승"); a.EditRebuild3
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); assert not any(r.startswith(("K6_","J23c_","J5k_")) for r in refs), refs
    e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value); rep["refs"]=refs
    json.dump(rep,open(os.path.join(VER,"line32_layout_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
    # ---- 열린 파트 문서 닫기(어셈블리·스테이션 제외)
    closed=[]
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and pn.lower().startswith(Z.lower()) and not os.path.basename(pn).upper().startswith(("S0","S1","S2","S3","4","1","9")):
            app.CloseDoc(tt); closed.append(os.path.basename(pn))
    print("closed part docs",len(closed))
stop.set(); print("stage",stage,"done")
