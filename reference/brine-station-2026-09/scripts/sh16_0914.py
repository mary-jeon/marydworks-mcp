# 2026-09-14: Ø16 샤프트 서포트 SK16/SHA16(Motedis SH16 STEP) 임포트 → J23c 파트(보어축 Z, 베이스면 +X, 보어 중심 원점) + L브래킷 K6 → J23b 교체
import os, sys, json, math, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
from swdialog import template_clicker
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
STEP=os.path.join(DESK,r"_원문\50A\sh25\Motedis_SH16.stp")
OUT=os.path.join(Z,"J23c_shaft_support_SK16_SHA16type_Motedis_STEP.SLDPRT")
BR=os.path.join(Z,"K6_bracket_L_PL6_60x32x30.SLDPRT")
mm=lambda v:v/1000.0; DATE="2026-09-14"
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def sel_body(d,b):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
def probe(d):
    cyl=[]; pl=[]
    for b in bodies(d):
        for fc in b.GetFaces():
            s=fc.GetSurface; fb=[round(v*1000,2) for v in fc.GetBox]; A=fc.GetArea*1e6
            if s.IsCylinder:
                p=s.CylinderParams; cyl.append((tuple(round(v,3) for v in p[3:6]),round(p[6]*1000,2),round(A),tuple(round(v*1000,2) for v in p[0:3]),fb))
            elif s.IsPlane: pl.append((tuple(round(v,3) for v in pv(fc,"Normal")),round(A),fb))
    return cyl,pl
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
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
def set_props(d,props,mat=None):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    if mat:
        try: d.SetMaterialPropertyName2("","이텍",mat)
        except Exception as ex: print("  mat exc",ex)
stage=sys.argv[1] if len(sys.argv)>1 else "import"
if stage=="import":
    dd=app.GetOpenDocumentByName(OUT)
    if dd is not None: app.CloseDoc(dd.GetTitle)
    if os.path.exists(OUT): os.remove(OUT)
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); d=app.ActiveDoc; print("import",d.GetTitle,d.GetType,"err",e.value)
    if d.GetType==2:
        kids=list(pv(d.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren")); print("asm children",len(kids))
        def ext(c):
            b=box(c); return (b[3]-b[0])*(b[4]-b[1])*(b[5]-b[2]) if b else 0
        for c in kids: print("  child",c.Name2,box(c),xform(c)["t_mm"])
        big=max(kids,key=ext); print("pick",big.Name2)
        pd=big.GetModelDoc2; app.ActivateDoc3(pd.GetTitle,False,0,I4()); pd=app.ActiveDoc; t=d.GetTitle
        e=I4(); w=I4(); ok=pd.Extension.SaveAs(OUT,0,1,NOD,e,w); print("SaveAs",ok); app.CloseDoc(t)
        for x in list(pv(app,"GetDocuments") or []):
            try:
                if x.GetTitle.lower().startswith("motedis_sh16"): app.CloseDoc(x.GetTitle)
            except Exception: pass
    else:
        e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("SaveAs",ok)
    d=act(OUT); bx=partbox(d); print("box",bx,"bodies",len(bodies(d)))
    cyl,pl=probe(d)
    big=sorted([c for c in cyl if 7.5<=c[1]<=8.5],key=lambda c:-c[2]); print("bore r8 cyl:",[(c[0],c[1],c[2],c[3]) for c in big[:4]])
    small=sorted([c for c in cyl if 2.5<=c[1]<=3.0],key=lambda c:-c[2]); print("bolt holes r2.75:",[(c[0],c[1],c[2],c[3]) for c in small[:6]])
    pls=sorted(pl,key=lambda p:-p[1]); print("planes:",[(p[0],p[1],p[2]) for p in pls[:8]])
    json.dump({"box":bx,"bore":big[:4],"holes":small[:6],"planes":pls[:12]},open(os.path.join(VER,"sh16_import_0914.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
    e=I4(); w=I4(); print("save",d.Save3(1,e,w))

elif stage=="bracket":
    d=act(OUT)
    set_props(d,{"TITLE":"SHAFT SUPPORT SK16 / SHA16 type (로봇 SH25H 동형, Ø16)",
      "SPEC":"T형 샤프트 서포트 Ø16(SK16/SH16 = MISUMI SHA16 동치수): 48(폭)×44(높이)×16(두께), 보어 Ø16 H7, 중심높이 27, 취부 볼트 2-Ø5.5 피치 38(M5), 상부 슬릿 + 조임볼트 M4, Al 합금(MISUMI AC7A) 40 g — Her Shin·삼익정공·MISUMI SHA16 카탈로그 일치. 축이 취부면과 평행 → 수직 봉은 L브래킷 K6의 수직면에 취부, 봉이 J1c 구멍 Ø16.5 관통 후 보어에 물림.",
      "Material":"AL(미확정)","QT'Y":"2","DATE":DATE,
      "REMARK":"로봇 SH25H(70×60×24, Ø25, 2-Ø6.6 = SK25/SHA25)와 같은 형식의 Ø16 판(사용자 지시 09-14). 3D: motedis.com Motedis_SH16.stp(본체만, 조임볼트 M4×20 별도 파트 미포함). 구매 후보: MISUMI SHA16 ₩7,963(API 표준단가), THK SK16, 삼익 SK16. 종전 플랜지형 SHFSS16(J23b) 대체."},mat="AL 6061")
    e=I4(); w=I4(); print("save J23c props",d.Save3(1,e,w))
    if not os.path.exists(BR):
        d=app.NewDocument(tmpl,0,0,0)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
        d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
        pts=[(0,0),(38,0),(38,-6),(6,-6),(6,-36),(0,-36)]
        for i in range(len(pts)):
            x0,z0=pts[i]; x1,z1=pts[(i+1)%len(pts)]; sm.CreateLine(mm(x0),mm(z0),0,mm(x1),mm(z1),0)
        sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(60.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3; assert f; f.Name="브래킷_L"
        bx=partbox(d); print("K6 box",bx)
        ydir=1 if bx[4]>1 else -1; zsign=1 if bx[5]>1 else -1
        print("K6 ydir",ydir,"zsign",zsign)
        print("K6: M5 tap holes not modeled (우측면 스케치 좌표 불확실) — SPEC에 미표현 기재")
        assert not ww(d) and len(bodies(d))==1
        set_props(d,{"TITLE":"L-BRACKET PL6 (샤프트 서포트 SK16 취부)","SPEC":"PL 6T STS304 L형: 수직판 36(z)×60(y), 수평판 38(x)×60(y). 수평판을 고정판 J1c 밑면에 필릿 용접, 수직판(봉 축에서 27 = SK16 중심높이)에 M5 탭 2개 @(y ±19, 상단 아래 8) — 3D 미표현. 서포트 베이스가 수직판에 볼트 2개(M5×12, 미표현).",
          "Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"자작. 서포트 축이 취부면과 평행이라 수직 봉에는 이 브래킷이 필요(플랜지형 SHFSS16은 불필요했음)."},mat="STS 304")
        orph=orphan_sketches(d); assert not orph, orph
        e=I4(); w=I4(); ok=d.Extension.SaveAs(BR,0,1,NOD,e,w); print("saved K6",ok)
        json.dump({"ydir":ydir,"zsign":zsign,"box":bx},open(os.path.join(VER,"k6_build_0914.json"),"w"))
elif stage=="asm":
    k6=json.load(open(os.path.join(VER,"k6_build_0914.json"))); ydir=k6["ydir"]; zsign=k6["zsign"]
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
        if n.startswith("J23b_"): sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
    a.EditRebuild3
    R_J=[[0,1,0],[-1,0,0],[0,0,1]]
    # K6: 파트 y 폭 방향 부호 ydir, z 부호 zsign → 라인 +y 폭·-z 높이. 회전 후보 중 행렬식 +1 인 것
    cand=[[1,0,0],[0,ydir if zsign<0 else -ydir,0],[0,0,1 if zsign<0 else -1]]
    if np.linalg.det(np.array(cand))<0: cand=[[-1,0,0],[0,cand[1][1],0],[0,0,cand[2][2]]]
    R_K=cand; print("R_K",R_K,"det",np.linalg.det(np.array(R_K)))
    NEW={"J23c":(os.path.basename(OUT),2),"K6":(os.path.basename(BR),2)}; added={}
    for key,(fn,cnt) in NEW.items():
        p=os.path.join(Z,fn); pre=fn.replace(".SLDPRT","")
        have=[n for n in comps() if n.startswith(pre+"-")]
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
        for i in range(cnt-len(have)):
            c=a.AddComponent5(p,0,"",False,"",0.0,0.0,0.0); assert c
        a.EditRebuild3; added[key]=sorted([n for n in comps() if n.startswith(pre+"-")],key=lambda n:int(n.rsplit("-",1)[1])); print("added",key,added[key])
    PLACE={added["J23c"][0]:(R_J,(72,240,-26)),added["J23c"][1]:(R_J,(72,-240,-26))}
    yflip=R_K[1][1]<0; xflip=R_K[0][0]<0
    for i,yc in enumerate((240,-240)): PLACE[added["K6"][i]]=(R_K,(72+(38 if xflip else 0),yc+30 if yflip else yc-30,-10))
    for cfg in CFGS:
        a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
        for n,(R,t) in PLACE.items():
            c=cc[n]; set_supp(c,True); move_fixed(c,R,t)
        a.ForceRebuild3(False); cc=comps()
        print(f"[{cfg}] ww {ww(a)}",[(n[:22],box(cc[n])) for n in PLACE])
    a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
    a.ClearSelection2(True)
    for n,c in cc.items():
        if c.GetSuppression2==2: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True)
    rel=[r for r in rows if any(x.startswith(("J23c","K6_")) for x in r[0])]; print("간섭(J23c/K6 관련)",rel,"| 전체",len(rows))
    refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); assert not any(r.startswith("J23b_") for r in refs)
    e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)

stop.set(); print("stage",stage,"done")
