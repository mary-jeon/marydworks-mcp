# 2026-09-10: MISUMI SHFSS16 STEP → 조사(--inspect) 또는 정렬·저장·교체(--apply R t)
#  규약(J23 근사 모델과 동일): 취부면(플랜지 상면) z 0, 보어 축 Z, 몸체 −z(16), 볼트 귀 ±x(피치 40), 클램프 귀 −y
import os, sys, json, math, shutil, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.spatial.transform import Rotation
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
from swdialog import template_clicker
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
DL=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_3D다운로드")
STEP=os.path.join(DL,"J23_SHFSS16.step"); assert os.path.exists(STEP), STEP
OUT=os.path.join(Z,"J23b_shaft_support_MISUMI_SHFSS16_STEP.SLDPRT")
mm=lambda v:v/1000.0
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def bodies(d): return list(pv(d,"GetBodies2",0,False) or [])
def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
def faces_info(bs):
    cyl=[]; pl=[]
    for b in bs:
        for fc in b.GetFaces():
            s=fc.GetSurface; fb=[round(v*1000,2) for v in fc.GetBox]
            if s.IsCylinder:
                p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],2),round(p[4],2),round(p[5],2)],[round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)],fb))
            elif s.IsPlane: pl.append((round(fc.GetArea*1e6,1),[round(v,2) for v in pv(fc,"Normal")],fb))
    return cyl,pl
# ---- 임포트(파트 또는 어셈블리 → 합성)
def import_step():
    for x in list(pv(app,"GetDocuments") or []):
        try:
            if x.GetTitle.startswith("J23_SHFSS16") and not x.GetPathName.lower().endswith(".sldprt"): app.CloseDoc(x.GetTitle); print("closed previous import")
        except Exception: pass
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); d=app.ActiveDoc; title=d.GetTitle
    print("imported:",title,"type",d.GetType,"err",e.value); assert title.startswith("J23_SHFSS16"), title
    if d.GetType==2:
        TMP=os.path.join(DL,"_children_tmp"); shutil.rmtree(TMP,ignore_errors=True); os.makedirs(TMP,exist_ok=True)
        cm=d.ConfigurationManager; kids=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")); rec=[]
        RUN=str(int(time.time())%100000)
        for k,c in enumerate(kids):
            md=c.GetModelDoc2; pth=os.path.join(TMP,f"J23_{RUN}_c{k}.SLDPRT"); app.ActivateDoc3(md.GetTitle,False,0,I4()); e=I4(); w=I4(); ok=md.Extension.SaveAs(pth,0,1,NOD,e,w); assert ok,(k,e.value)
            xf=xform(c); rec.append({"file":pth,"R":xf["R"],"t":xf["t_mm"]})
        kid_paths=[c.GetPathName for c in kids]; app.CloseDoc(title)
        for pth in kid_paths+[r["file"] for r in rec]:
            for x in list(pv(app,"GetDocuments") or []):
                try:
                    if x.GetPathName==pth: app.CloseDoc(x.GetTitle)
                except Exception: pass
        d=app.NewDocument(tmpl,0,0,0); final=[]
        def target():
            c_=[b for b in bodies(d) if not any(np.all(np.abs(bbox(b)-fb)<0.05) for fb in final)]; assert len(c_)==1,len(c_); return c_[0]
        SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}
        def sel(bs):
            d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
            for b in bs: b.Select2(True,sd)
        for r in rec:
            f=d.InsertPart3(r["file"],1|512|262144,""); d.EditRebuild3; assert f
            b=target(); c_loc=centroid(b); Rc=np.array(r["R"]); tc=np.array(r["t"]); c_exp=c_loc@Rc+tc
            if not np.allclose(Rc,np.eye(3),atol=1e-6):
                ang=Rotation.from_matrix(Rc.T).as_euler("xyz")
                for axis,val in zip("xyz",ang):
                    if abs(val)<1e-9: continue
                    s=SLOT[axis]; sel([target()]); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3; assert mv
            if not np.allclose(tc,0): sel([target()]); mv=d.FeatureManager.InsertMoveCopyBody2(mm(tc[0]),mm(tc[1]),mm(tc[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv
            b=target(); assert np.all(np.abs(centroid(b)-c_exp)<0.05); final.append(bbox(b))
        shutil.rmtree(TMP,ignore_errors=True)
    return d
d=import_step()
bs=bodies(d); cyl,pl=faces_info(bs); pl.sort(key=lambda x:-x[0])
print("bodies",len(bs),"box",[round(v*1000,2) for v in pv(d,"GetPartBox",True)])
print("bore r8 cyl:",[c for c in cyl if abs(c[0]-8)<0.2][:4]); print("bolt r2.75/4.5 cyl:",[c for c in cyl if abs(c[0]-2.75)<0.2 or abs(c[0]-4.5)<0.2][:6]); print("big cyl:",sorted([c for c in cyl if c[0]>9],key=lambda c:-c[0])[:6])
print("planes:",pl[:8])
json.dump({"cyl":cyl,"planes":pl[:20]},open(os.path.join(VER,"holder_step_inspect_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
if "--inspect" in sys.argv: stop.set(); raise SystemExit("inspect only (doc left open)")
# ---- 정렬(--apply 다음 인수: R 9개, t 3개)
i=sys.argv.index("--apply"); vals=[float(v) for v in sys.argv[i+1:i+13]]; R=np.array(vals[:9]).reshape(3,3); t=np.array(vals[9:12])
SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}
def sel_all():
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
    for b in bodies(d): b.Select2(True,sd)
exp=sorted([centroid(b)@R+t for b in bodies(d)],key=lambda c:(round(c[2],1),round(c[1],1),round(c[0],1)))
ang=Rotation.from_matrix(R.T).as_euler("xyz")
for axis,val in zip("xyz",ang):
    if abs(val)<1e-9: continue
    s=SLOT[axis]; sel_all(); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3; assert mv; mv.Name=f"정렬회전_{axis.upper()}"
if not np.allclose(t,0): sel_all(); mv=d.FeatureManager.InsertMoveCopyBody2(mm(t[0]),mm(t[1]),mm(t[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬이동"
got=sorted([centroid(b) for b in bodies(d)],key=lambda c:(round(c[2],1),round(c[1],1),round(c[0],1)))
assert all(np.all(np.abs(g-e)<0.05) for g,e in zip(got,exp)), (got,exp)
bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; cyl,pl=faces_info(bodies(d)); bore=[c for c in cyl if abs(c[0]-8)<0.2]
print("aligned box",bx,"bore",bore[:2]); assert abs(bx[5])<0.3 and all(abs(c[1][2])>0.99 and abs(c[2][0])<0.1 and abs(c[2][1])<0.1 for c in bore)
cp=d.Extension.CustomPropertyManager("")
for k,v in {"TITLE":"SHAFT SUPPORT FLANGE SLIT (MISUMI SHFSS16)","SPEC":"MISUMI SHFSS16 샤프트 서포트 플랜지형 슬릿, 홀 D16 H7(슬릿 가공 후 H8 정도), SUS304 상당, 무처리. 규격표 D16: L50·L1(볼트 피치)40·T16·t8·H31·A28·B20·C2·h12.5·취부홀 d5.5(자리파기 9)·클램프 볼트 M4(별매). 3D = MISUMI 생성 STEP 원형. 파트 좌표: 취부면 z 0, 보어 축 Z, 몸체 −z, 클램프 귀 −y","MATERIAL":"SUS304","QT'Y":"2","DATE":"2026-09-10","REMARK":"가이드봉 PSSFAQ16 상단을 고정판 J1c 밑면에서 클램프 고정(M5 볼트 2 → J1c M5 탭). 종전 카탈로그 근사 모델 J23 대체"}.items(): cp.Add3(k,30,v,1)
e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved",ok,e.value,os.path.basename(OUT)); assert ok
# ---- 교체
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R_,t_):
    arr=list(R_[0])+list(R_[1])+list(R_[2])+[t_[0]/1000,t_[1]/1000,t_[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R_,t_):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True); set_T(c,R_,t_); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps(); olds=sorted([n for n in cc if n.startswith("J23_")]); assert len(olds)==2
st={n:{cfg:None for cfg in CFGS} for n in olds}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; c2=comps()
    for n in olds: st[n][cfg]=(xform(c2[n])["R"],xform(c2[n])["t_mm"],c2[n].GetSuppression2)
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
if app.GetOpenDocumentByName(OUT) is None: open_doc(app,OUT,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(OUT,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace",ok); assert ok
cc=comps(); news=sorted([n for n in cc if n.startswith("J23b_")]); assert len(news)==2
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for o,n in zip(olds,news):
        R_,t_,sp=st[o][cfg]; move_fixed(cc[n],R_,t_)
    a.ForceRebuild3(False); cc=comps(); print(f"[{cfg}]",[(n,box(cc[n])) for n in news])
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); rows=interf([c for c in cc.values() if c.GetSuppression2==2]); rows=[r for r in rows if any(x.startswith(("J23","J2c","J1c")) for x in r[0])]; print(f"[{cfg}] 홀더 관련 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3; e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
stop.set(); print("holder step apply done")
