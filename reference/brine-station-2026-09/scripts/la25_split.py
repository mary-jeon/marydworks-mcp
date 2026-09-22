# B9b LA25: split imported body into housing + rod at z=-83, add part configs 상승/하강; in 하강 move the rod body -140 (z) and fill the gap with a Ø29 extrusion.
import os, sys, json
from swconn import *
from swpv import pv
stop=watchdog()
app=connect()
P=os.path.join(Z,"B9b_LINAK_LA25_900N_150st_24V.SLDPRT")
d=open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
ZSPLIT=-83.0; STROKE=140.0; R_ROD=14.5   # -83: 하우징 벌지 최하단(-81.8) 아래 → 로드 튜브만 절단, 바디 2개
def sel_body(b,append,mark):
    sd=d.SelectionManager.CreateSelectData; sd.Mark=mark; return b.Select2(append,sd)
def bodies():
    return list(pv(d,"GetBodies2",0,True) or [])
def bbox(b): return [round(v*1000,1) for v in pv(b,"GetBodyBox")]
def feat_names():
    f=d.FirstFeature; out=[]
    while f:
        out.append((f.Name,f.GetTypeName2)); f=f.GetNextFeature
    return out
print("configs before:",list(d.GetConfigurationNames)); print("bodies before:",[(pv(b,"Name"),bbox(b)) for b in bodies()])
# enum lookups from swconst.tlb
tlb=pythoncom.LoadTypeLib(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\swconst.tlb")
def enum(name):
    for i in range(tlb.GetTypeInfoCount()):
        if tlb.GetDocumentation(i)[0]==name:
            ti=tlb.GetTypeInfo(i); ta=ti.GetTypeAttr(); return {ti.GetNames(ti.GetVarDesc(k).memid)[0]:ti.GetVarDesc(k).value for k in range(ta.cVars)}
    return {}
E_RP=enum("swRefPlaneReferenceConstraints_e"); E_CFG=enum("swInConfigurationOpts_e")
print("RefPlane consts:",{k:v for k,v in E_RP.items() if "Distance" in k or "Coincident" in k}, "| cfg opts:",E_CFG)
DIST=E_RP.get("swRefPlaneReferenceConstraint_Distance",8)
THIS=E_CFG.get("swThisConfiguration",1); SPEC=E_CFG.get("swSpecifyConfiguration",3); ALL=E_CFG.get("swAllConfiguration",2)
# ---- 1. reference plane at z=ZSPLIT (offset from Front Plane toward -z). Distance|OptionFlip flips the offset side.
FLIP=E_RP.get("swRefPlaneReferenceConstraint_OptionFlip",0)
def plane_z(nm):
    rp=d.FeatureByName(nm)
    if not rp: return None
    a=list(pv(pv(rp,"GetSpecificFeature2"),"Transform").ArrayData); return a[11]*1000
pz=plane_z("분할면")
if pz is not None and abs(pz-ZSPLIT)>0.5:
    d.ClearSelection2(True); d.Extension.SelectByID2("분할면","PLANE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3; print("deleted wrong-side plane at z",pz); pz=None
if pz is None:
    for flags in (DIST|FLIP, DIST):
        d.ClearSelection2(True)
        ok=d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0)
        rp=d.FeatureManager.InsertRefPlane(flags,abs(ZSPLIT)/1000.0,0,0,0,0)
        rp.Name="분할면"; z=plane_z("분할면"); print("ref plane flags",flags,"-> z",z)
        if abs(z-ZSPLIT)<0.5: break
        d.ClearSelection2(True); d.Extension.SelectByID2("분할면","PLANE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3
    d.ClearSelection2(True)
# ---- 2. split body at 분할면
def already_split():
    bs=bodies(); return len(bs)==2 and any(bbox(b)[5]<=ZSPLIT+0.5 for b in bs) and any(bbox(b)[2]>=ZSPLIT-0.5 for b in bs)
if not already_split():
    d.ClearSelection2(True)
    ok=d.Extension.SelectByID2("분할면","PLANE",0,0,0,False,1,NOD,0)
    done=False
    for variant in ([] if len(bodies())==2 else ["bool_nodorig"]):
        d.ClearSelection2(True); d.Extension.SelectByID2("분할면","PLANE",0,0,0,False,1,NOD,0)
        r=d.FeatureManager.PreSplitBody
        if callable(r): r=r()
        sec=list(r) if isinstance(r,tuple) else []
        n=len(sec)
        if n<2: raise SystemExit("plane does not split the body")
        vt=pythoncom.VT_BOOL if variant.startswith("bool") else pythoncom.VT_VARIANT
        marks=VARIANT(pythoncom.VT_ARRAY|vt,[True]*n); paths=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,[""]*n)
        origins=NOD if "nodorig" in variant else VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_VARIANT,[None]*n)
        consume="consume" in variant
        try: f2=d.FeatureManager.PostSplitBody(marks,consume,origins,paths)
        except Exception as ex: f2=None; print("  PostSplitBody",variant,"exc:",ex)
        d.EditRebuild3; print("  post-split",variant,"->",f2.Name if f2 else None,"bodies:",len(bodies()))
        if f2 and len(bodies())>=2: done=True; break
    if not done:
        # ---- fallback: copy body, then cut each copy on one side of 분할면 (feature scope = one body)
        print("fallback: copy body + box-combine cuts")
        if len(bodies())<2:
            d.ClearSelection2(True); sel_body(bodies()[0],False,1)
            cp=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,True,1); d.EditRebuild3
            print("  copy feature:",cp.Name if cp else None,"bodies:",[(pv(b,"Name"),bbox(b)) for b in bodies()])
        if len(bodies())!=2: raise SystemExit("copy failed")
        def box_body(direction,label):
            """extrude a big rectangle from 분할면 as a separate body (Merge=False); direction +1 => +z side, -1 => -z side"""
            for flip,dirn in ((False,True),(False,False),(True,False),(True,True)):
                d.ClearSelection2(True); d.Extension.SelectByID2("분할면","PLANE",0,0,0,False,0,NOD,0)
                d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
                sm.CreateCenterRectangle(0,0,0,0.2,0.2,0); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
                sk=[n for n,t in feat_names() if t=="ProfileFeature"][-1]
                d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
                before={pv(x,"Name") for x in bodies()}
                f=d.FeatureManager.FeatureExtrusion3(True,flip,dirn,0,0,0.3,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,0,0.0,False)
                d.EditRebuild3
                newb=[x for x in bodies() if pv(x,"Name") not in before]
                if f and newb:
                    bb=bbox(newb[0]); ok=(bb[2]>=ZSPLIT-0.5) if direction>0 else (bb[5]<=ZSPLIT+0.5)
                    print(f"  box {label} flip={flip} dir={dirn}: {f.Name} box {bb} ok={ok}")
                    if ok: f.Name=label; return newb[0]
                    d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3
                else:
                    print("  box extrude failed",label,flip)
            raise SystemExit("box body failed "+label)
        def combine_cut(main,tool,label):
            f=d.FeatureManager.InsertCombineFeature(15902,main,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_VARIANT,[tool]))
            d.EditRebuild3; print(f"  combine cut {label}: {f.Name if f else None} bodies {[(pv(x,'Name'),bbox(x)) for x in bodies()]}")
            if f: f.Name=label
            return f
        bs=bodies(); orig=[x for x in bs if pv(x,"Name")=="불러온 피처8"][0]; copy=[x for x in bs if pv(x,"Name")!="불러온 피처8"][0]
        box_up=box_body(+1,"절단박스_상"); combine_cut(copy,box_up,"로드_분리")            # copy minus upper box -> rod (z<=-83)
        bs=bodies(); orig=[x for x in bs if pv(x,"Name")=="불러온 피처8"][0]
        box_dn=box_body(-1,"절단박스_하"); combine_cut(orig,box_dn,"하우징_분리")           # orig minus lower box -> housing (z>=-83)
print("bodies after split:",[(pv(b,"Name"),bbox(b)) for b in bodies()])
bs=bodies()
if len(bs)!=2: raise SystemExit("split did not yield 2 bodies")
rod=min(bs,key=lambda b:bbox(b)[2]); housing=max(bs,key=lambda b:bbox(b)[2])
print("rod body:",pv(rod,"Name"),bbox(rod)," housing:",pv(housing,"Name"),bbox(housing))
if bbox(rod)[5]>ZSPLIT+1 or bbox(housing)[2]<ZSPLIT-1: raise SystemExit("split plane on wrong side — check offset direction")
# ---- 3. configurations
for cfg,desc in (("상승","로드 후퇴(스트로크 0)"),("하강","로드 140 신장")):
    if cfg not in list(d.GetConfigurationNames):
        c=d.AddConfiguration3(cfg,desc,"",0); print("config added:",cfg,c is not None)
d.ShowConfiguration2("하강"); d.EditRebuild3
# ---- 4. 하강: move rod body -140 z
if not any(n=="로드_하강_이동" for n,t in feat_names()):
    d.ClearSelection2(True); sel_body(rod,False,1)
    mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,-STROKE/1000.0,0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1)
    print("move/copy:",mv.Name if mv else None); mv.Name="로드_하강_이동"
    d.EditRebuild3
    print("bodies after move (하강):",[(pv(b,"Name"),bbox(b)) for b in bodies()])
# ---- 5. 하강: fill extrusion Ø29 from 분할면 toward -z, length STROKE+2, merge
if not any(n=="로드_하강_연장" for n,t in feat_names()):
    d.ClearSelection2(True); d.Extension.SelectByID2("분할면","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
    sm.CreateCircleByRadius(0.0,0.0,0.0,R_ROD/1000.0); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    skname=[n for n,t in feat_names() if t=="ProfileFeature"][-1]
    d.Extension.SelectByID2(skname,"SKETCH",0,0,0,False,0,NOD,0)
    nb=len(bodies())
    ex=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,(STROKE+2.0)/1000.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    d.EditRebuild3
    bb=[bbox(b) for b in bodies()]
    print("extrude:",ex.Name if ex else None,"bodies now",len(bb),bb)
    if ex and (len(bb)!=2 or min(b[2] for b in bb)>-300):   # wrong direction (went +z) -> flip
        ex.GetDefinition  # noop
        d.Extension.SelectByID2(ex.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.EditDelete(); d.EditRebuild3
        d.Extension.SelectByID2(skname,"SKETCH",0,0,0,False,0,NOD,0)
        ex=d.FeatureManager.FeatureExtrusion3(True,True,True,0,0,(STROKE+2.0)/1000.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
        d.EditRebuild3; bb=[bbox(b) for b in bodies()]; print("extrude flipped:",ex.Name if ex else None,"bodies",len(bb),bb)
    ex.Name="로드_하강_연장"
# ---- 6. suppress the two 하강 features in 상승 and Default
names=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["상승","Default"])
for fn in ("로드_하강_이동","로드_하강_연장"):
    f=d.FeatureByName(fn)
    if f: print("suppress",fn,"in 상승/Default ->",f.SetSuppression2(0,SPEC,names))
for cfg in ("상승","하강","Default"):
    d.ShowConfiguration2(cfg); d.EditRebuild3
    print(f"[{cfg}] bodies:",[(pv(b,"Name"),bbox(b)) for b in bodies()])
d.ShowConfiguration2("상승"); d.EditRebuild3
cpm=d.Extension.CustomPropertyManager(""); cpm.Set2("REMARK",cpm.Get("REMARK")+" | 2026-09-07 바디 분할(하우징/로드, z=-83) + 파트 구성 상승/하강(하강=로드 -140 이동+연장). 로드 연장 파트 B12 폐기")
print("features tail:",[n for n,t in feat_names()][-6:],"dirty",d.GetSaveFlag,"(not saved)")
