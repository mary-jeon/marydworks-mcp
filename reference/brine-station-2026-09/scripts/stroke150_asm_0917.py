# 2026-09-17 2단계: SPEC 정리 → B9i 하강 로드 연장 바디 → 어셈블리 교체(구 B10/J23b/J2c/J19i 삭제, 새 B10b/J23d/J2d ×4 + J19j ×2 삽입·기준면 메이트) → 거리_하강 575 → 4구성 검증·간섭
import os, sys, json, math, re
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-17"
STAGE=sys.argv[1] if len(sys.argv)>1 else "all"; rep={"stage":STAGE}
ZP_UP=-425.0; ZP_DN=-575.0; STROKE=150.0; SH_XS=(0.0,90.0); SH_Y=240.0; HOSE_TOP=-154.6
P_B10=Zp("B10b_linear_bushing_MISUMI_LHFRW20_catalog.SLDPRT"); P_J23=Zp("J23d_shaft_support_MISUMI_SHFSS20_catalog.SLDPRT"); P_J2=Zp("J2d_guide_shaft_MISUMI_PSSFAQ20-660-B13_catalog.SLDPRT")
P_UP=Zp("J19j_hose_YASUNG_HSPF-032_up_U190_R46.SLDPRT"); P_DN=Zp("J19j_hose_YASUNG_HSPF-032_dn_bow_R76.SLDPRT")
P_J1C=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); P_J5L=Zp("J5l_moving_plate_180x540_t8.SLDPRT"); P_B9I=Zp("B9i_TiMOTION_TA2-2H-150339-5511-010-1.SLDPRT")
stop=watchdog(); app=connect()
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def set_props(d,props):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
# ---------- A. SPEC 정리(날짜·이력 문구 제거, 정확한 수치) ----------
if STAGE in ("all","spec"):
    d=act(P_J1C)
    set_props(d,{"SPEC":"185(X −75~110)×580(Y ±290) t10 STS304. 유로 구멍 Ø43(0,0): 배럴 니플 G13f R1-1/4(ONDA SFN2-32, 32A)를 10 삽입해 밑면 필릿 용접. 가이드봉 Ø20.5 관통 4개소 @(0|90, ±240) — 봉은 판 밑면의 클램프형 샤프트 서포트 MISUMI SHFSS20 ×4로 고정(L 60 방향 = y), 홀더 취부 M6 탭 8개소 @(0|90, ±240±24)(드릴 Ø5.0 = 모델 구멍, 물림 10). TA2 러그 J8g 밑면 용접 @(85,0). 상면은 호퍼 립 밑면에 둘레 필릿 용접(HANDOFF §1-21 사양).","DATE":DATE})
    print("J1c SPEC set")
    d=act(P_J5L)
    set_props(d,{"SPEC":"PL 8T STS304 180×540(x −45~135, y ±270). 구멍: 소켓 ONDA SFS3-32 Ø49(0,0) 상면 플러시 삽입 양면 필릿 용접 / 리니어 부시 MISUMI LHFRW20 ×4 하우징 Ø32 H7 + 취부 M5 탭 4×4(PCD 43, 0°/90°, 드릴 Ø4.2) @(0|90, ±240) = 앞·뒤 4점. 러그 J9f 밑면 용접 @(85,0). 공차: 별도 속성 TOLERANCE 참조.",
      "TOLERANCE":"부시 하우징 Ø32 H7 +0.025/0 (KS B 0401·JIS B 0401-2 30<d≤50) ↔ LHFRW20 외경 32 0/−0.019 → 틈 0~0.044. 일반공차 KS B ISO 2768-1 m.","DATE":DATE})
    print("J5l SPEC set")
    rep["spec"]=True
# ---------- B. B9i 하강 로드 연장(STEP 로드 바디 121 → 150 이동 시 몸체와 62 빈틈) ----------
if STAGE in ("all","ta2fix"):
    d=act(P_B9I)
    if d.FeatureByName("로드_연장_하강") is None:
        d.ShowConfiguration2("하강"); d.EditRebuild3
        bb=[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies(d)]; print("  하강 bodies",bb)
        body=[b for b in bb if b[3]>40][0]; rod=[b for b in bb if b[3]<=40][0]     # 몸체(x 넓음) / 로드(Ø20)
        z_body_end=body[2]; z_rod_top=rod[5]; gap=z_body_end-z_rod_top; print("  body end",z_body_end,"rod top",z_rod_top,"gap",gap)
        assert gap>0, "no gap"
        z0=z_rod_top-5.0; depth=gap+10.0     # 시작 z −383.4(로드 안 5 겹침) → +z로 72.2(몸체 안 5 겹침)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
        d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(10.0)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=None; f=pv(d,"FirstFeature")
        while f is not None:
            if pv(f,"GetTypeName2")=="ProfileFeature": sk=f.Name
            f=pv(f,"GetNextFeature")
        ok=False
        for dirn,flip in ((False,True),(True,True),(True,False),(False,False)):
            if True:
                d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
                ext=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,3,mm(abs(z0)),flip); d.EditRebuild3
                if ext is None: print("   ext None",dirn,flip); continue
                bb2=[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies(d)]; print("   try dir",dirn,"flip",flip,"bodies",bb2)
                good=any(b[2]<=z_rod_top+0.1 and b[5]>=z_body_end-0.1 for b in bb2)
                if good and not ww(d): ext.Name="로드_연장_하강"; ok=True; break
                ext.Select2(False,0); d.EditDelete(); d.EditRebuild3
            if ok: break
        assert ok, "rod extension"
        # 실패 시도에서 남은 고아 스케치 정리
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
        for n in orphan_sketches(d):
            d.ClearSelection2(True)
            if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); print("  orphan sketch deleted",n)
        d.EditRebuild3; assert not orphan_sketches(d)
        f=d.FeatureByName("로드_연장_하강"); f.SetSuppression2(0,3,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","기본"]))
        for cfg in ("상승","하강","기본"):
            d.ShowConfiguration2(cfg); d.EditRebuild3; print(f"  [{cfg}]",[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies(d)],"ww",ww(d))
        d.ShowConfiguration2("상승"); d.EditRebuild3
        e=I4(); w=I4(); assert d.Save3(1,e,w); print("  B9i saved",e.value,w.value)
    rep["ta2fix"]=True
# ---------- C. 어셈블리 교체 ----------
def asm_open():
    a=app.GetOpenDocumentByName(ASM) or open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); return app.ActiveDoc
if STAGE in ("all","replace","verify","interf","dist","hosecfg"):
    a=asm_open(); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
    def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
    def mates_iter():
        f=pv(a,"FirstFeature")
        while f is not None:
            if pv(f,"GetTypeName2")=="MateGroup":
                sf=f.GetFirstSubFeature
                while sf is not None: yield sf; sf=sf.GetNextSubFeature
            f=pv(f,"GetNextFeature")
    def mate_names(): return [m.Name for m in mates_iter()]
    def find_mate(name):
        for m in mates_iter():
            if m.Name==name: return m
    def del_mate(name):
        a.ClearSelection2(True)
        if a.Extension.SelectByID2(name,"MATE",0,0,0,False,0,NOD,0): a.EditDelete()
        a.ClearSelection2(True)
    KO=("우측면","윗면","정면"); EN=("Right Plane","Top Plane","Front Plane")
    def sel_plane(comp,axis,append):
        for nm in (KO[axis],EN[axis]):
            if a.Extension.SelectByID2(f"{nm}@{comp}@염수주입라인","PLANE",0,0,0,append,1,NOD,0): return True
        return False
    def add_mate(mtype,align,flip=False,dist=0.0,name=None):
        err=I4(); m=a.AddMate5(mtype,align,flip,dist,0.0,0.0,0,0,0,0,0,False,False,0,err); a.ClearSelection2(True)
        ok=(m is not None); f=None
        if ok:
            f=list(mates_iter())[-1]
            if name:
                try: f.Name=name
                except Exception as ex: print("  rename exc",ex)
        return ok,err.value,f
    def xf_ok(comp,R_exp,t_exp):
        a.EditRebuild3; x=xform(comps()[comp]); dR=max(abs(x["R"][i][j]-R_exp[i][j]) for i in range(3) for j in range(3)); dt=max(abs(p-q) for p,q in zip(x["t_mm"],t_exp))
        return dR<1e-3 and dt<0.02, x
    def plane_mate(base,part,R,t_rel,t_exp,tag):
        """part 기준면 k(법선 = R[k] 월드) ↔ base 기준면 j. 축정렬 R만."""
        made=[]; c=comps()[part]
        if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
        for k in range(3):
            n=R[k]; j=max(range(3),key=lambda i:abs(n[i])); assert abs(n[j])>0.999,(part,R); sign=1 if n[j]>0 else -1
            off=t_rel[j]; name=f"{tag}_{'xyz'[j]}"
            if name in EXIST: print("   skip",name); continue
            variants=[(0 if sign>0 else 1,False),(1 if sign>0 else 0,False)] if abs(off)<1e-6 else [(0 if sign>0 else 1,False),(0 if sign>0 else 1,True),(1 if sign>0 else 0,False),(1 if sign>0 else 0,True)]
            done=False
            for al,fl in variants:
                a.ClearSelection2(True); assert sel_plane(part,k,False),(part,k); assert sel_plane(base,j,True),(base,j)
                if abs(off)<1e-6: ok,e,f=add_mate(0,al,False,0,name)
                else: ok,e,f=add_mate(5,al,fl,abs(off)/1000,name)
                if not ok:
                    print("   mate fail",name,e); nm=mate_names()
                    if nm and nm[-1] not in EXIST and re.fullmatch(r"(거리|일치|동심|각도)\d+",nm[-1]): del_mate(nm[-1])
                    continue
                # 마지막 축까지 걸리기 전엔 위치가 미정이므로 k<2 에서는 경고만 검사
                good,x=xf_ok(part,R,t_exp)
                if good and not ww(a): made.append(name); done=True; break
                print("   retry",name,al,fl,x["t_mm"],ww(a)); del_mate(name)
            assert done,("plane mate failed",name)
        g,x=xf_ok(part,R,t_exp); print(f"  {part[:44]:44s} {made} ok={g} t={x['t_mm']}"); return g
    I3=[[1,0,0],[0,1,0],[0,0,1]]; R_ROT90=[[0,1,0],[-1,0,0],[0,0,1]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
    J1C="J1c_fixed_plate_185x580_t10-2"; J5L="J5l_moving_plate_180x540_t8-1"
if STAGE in ("all","replace"):
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    print("components",len(cc)); b9=[n for n in cc if n.startswith("B9")]; print("TA2 comp",b9,[os.path.basename(cc[n].GetPathName) for n in b9])
    # 1) 구 부품 삭제(종속 메이트 자동 삭제)
    old=[n for n in cc if n.startswith(("B10_","J23b_","J2c_","J19i_","B10b_","J23d_","J2d_","J19j_"))]; print("delete",old)
    for n in old:
        a.ClearSelection2(True); cc[n].Select4(False,NOD,False); r=a.DeleteSelection(False) if False else a.Extension.DeleteSelection2(0); print("  deleted",n,r)
    a.EditRebuild3; cc=comps(); assert not any(n.startswith(("B10_","J23b_","J2c_","J19i_","B10b_","J23d_","J2d_","J19j_")) for n in cc)
    print("mates after delete",len(mate_names()),"ww",ww(a))
    # 2) 새 부품 삽입
    for p in (P_B10,P_J23,P_J2,P_UP,P_DN):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    plan=[]   # (path, R, t_world, base, tag)
    for x in SH_XS:
        for s in (1,-1):
            ys=s*SH_Y
            plan.append((P_B10,I3,[x,ys,ZP_UP+8.0],J5L,"이동_B10b"))
            plan.append((P_J23,R_ROT90,[x,ys,-10.0],J1C,"고정_J23d"))
            plan.append((P_J2,I3,[x,ys,3.0],J1C,"고정_J2d"))
    plan.append((P_UP,R_HOSE,[0.0,0.0,HOSE_TOP],J1C,"고정_J19jup")); plan.append((P_DN,R_HOSE,[0.0,0.0,HOSE_TOP],J1C,"고정_J19jdn"))
    inserted=[]
    for path,R,t,base,tag in plan:
        c=a.AddComponent5(path,0,"",False,"",mm(t[0]),mm(t[1]),mm(t[2])); assert c is not None, path
        arr=[float(v) for v in R[0]+R[1]+R[2]]+[mm(t[0]),mm(t[1]),mm(t[2]),1.0,0.0,0.0,0.0]
        xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
        x=xform(comps()[c.Name2]); print("  inserted",c.Name2,"R",x["R"],"t",x["t_mm"])
        assert max(abs(x["R"][i][j]-R[i][j]) for i in range(3) for j in range(3))<1e-3 and max(abs(p-q) for p,q in zip(x["t_mm"],t))<0.02, ("transform",c.Name2,x)
        inserted.append((c.Name2,R,t,base,tag))
    a.EditRebuild3; EXIST=set(mate_names())
    # 3) 메이트 (이동측은 J5l 기준 상대 오프셋)
    tj=xform(comps()[J5L])["t_mm"]; assert abs(tj[2]-ZP_UP)<0.02, tj
    for name,R,t,base,tag in inserted:
        c=comps()[name]
        if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
        trel=[t[i]-tj[i] for i in range(3)] if base==J5L else list(t)
        g=plane_mate(base,name,R,trel,t,f"{tag}-{name.rsplit('-',1)[1]}"); assert g, name
        EXIST=set(mate_names())
    # 4) 호스 구성 억제: up = 상승·1., dn = 하강·2.
    up=[n for n,_,_,_,_ in inserted if "up_U190" in n][0]; dn=[n for n,_,_,_,_ in inserted if "dn_bow" in n][0]
    rep["inserted"]=[i[0] for i in inserted]
if STAGE in ("all","replace","hosecfg"):
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    up=[n for n in cc if "up_U190" in n][0]; dn=[n for n in cc if "dn_bow" in n][0]
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        want_up = cfg in ("상승","1.상승했을때(해석)")
        for n,on in ((up,want_up),(dn,not want_up)):
            c=cc[n]; st=c.GetSuppression2
            if on and st!=2: r=c.SetSuppression2(2)
            if (not on) and st!=0: r=c.SetSuppression2(0)
        a.EditRebuild3; cc=comps(); print(f"  [{cfg}] up supp {cc[up].GetSuppression2} dn supp {cc[dn].GetSuppression2}")
        assert cc[up].GetSuppression2==(2 if want_up else 0) and cc[dn].GetSuppression2==(0 if want_up else 2)
    a.ShowConfiguration2("상승"); a.EditRebuild3
if STAGE in ("all","replace","dist"):
    fd=find_mate("거리_하강"); dim=fd.Parameter("D1"); print("거리_하강 D1 before",dim.SystemValue*1000)
    r=dim.SetSystemValue3(mm(-ZP_DN),2,None); print("  set all cfg ret",r,"now",dim.SystemValue*1000)
    for cfg in ("하강","2.하강했을때(해석)"):
        a.ShowConfiguration2(cfg); a.EditRebuild3; v=dim.SystemValue*1000
        if abs(v+ZP_DN)>0.01: r=dim.SetSystemValue3(mm(-ZP_DN),1,None); a.EditRebuild3; print("  ",cfg,"set this cfg",r,dim.SystemValue*1000)
    a.ShowConfiguration2("상승"); a.EditRebuild3
if STAGE in ("all","replace","verify"):
    out={}
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps()
        row={n:(xform(c)["t_mm"],box(c),c.GetSuppression2) for n,c in cc.items()}
        out[cfg]=row; zj=row[J5L][0][2]
        print(f"[{cfg}] ww {ww(a)} J5l z {zj} | fixed {[n for n,c in cc.items() if c.IsFixed]}")
        for n,(t,b,s) in row.items():
            if n.startswith(("B10b","J23d","J2d","J19j","B9i","B9h","J5l","G13f","F4")): print(f"   {n[:48]:48s} t={t} box={b} supp={s}")
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
    json.dump(out,open(os.path.join(VER,"stroke150_asm_positions_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
if STAGE in ("all","interf"):
    idm=a.InterferenceDetectionManager
    for cfg in ("상승","하강"):
        a.ShowConfiguration2(cfg); a.ForceRebuild3(False)
        idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False; idm.CreateFastenersFolder=False
        a.ClearSelection2(True)
        try: idm.UseTransform=True
        except Exception: pass
        n=idm.GetInterferenceCount; res=[]
        ints=list(pv(idm,"GetInterferences") or [])
        for it in ints:
            cs=[c.Name2 for c in list(pv(it,"Components") or [])]; res.append((cs,round(it.Volume*1e9,1)))
        res.sort(key=lambda r:-r[1]); print(f"[{cfg}] interferences {len(res)}");
        for cs,v in res: print("   ",v,cs)
        rep[f"interf_{cfg}"]=res
        idm.Done()
    a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
json.dump(rep,open(os.path.join(VER,f"stroke150_asm_0917_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("DONE",STAGE)
