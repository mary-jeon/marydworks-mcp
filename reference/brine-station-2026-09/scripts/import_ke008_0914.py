# 2026-09-14: KOSAPLUS KE008 STEP(제조사, SW2015 어셈블리) → 임포트 → 자식 파트 임시 저장 + Transform 기록 → 새 파트에 InsertPart3 합성(B4d)
#  파트 좌표 규약(B4c와 동일): 스템축 = 파트 Z, 취부(패드) 면 z=0, 몸체 +z, 스템축 x=y=0
import os, sys, json, math, re, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from scipy.spatial.transform import Rotation
from swconn import *
from swpv import pv
from swdialog import template_clicker
DESK=r"<PROJECT_DIR>"
STEP=os.path.join(DESK,r"_원문\50A\kosaplus_KE008_F357C14_2013.step")
TMP=os.path.join(DESK,"_3D다운로드","KE008_children"); os.makedirs(TMP,exist_ok=True)
OUT=os.path.join(Z,"B4d_actuator_KOSAPLUS_KE008-F357C14-DC.SLDPRT")
REC=os.path.join(DESK,"_검증","ke008_children_0914.json")
mm=lambda v:v/1000.0
stop=watchdog(); app=connect()
stage=sys.argv[1] if len(sys.argv)>1 else "children"
if stage=="children":
    already=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.lower().startswith("kosaplus_ke008") and x.GetType==2]
    if already: d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); print("reuse open import asm")
    else:
        evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); print("LoadFile4 err",e.value)
    d=app.ActiveDoc; title=d.GetTitle; print("imported",title,d.GetType)
    cm=d.ConfigurationManager
    def walk(c,depth,acc):
        for k in (pv(c,"GetChildren") or []):
            kids=pv(k,"GetChildren") or []
            if kids and depth<8: walk(k,depth+1,acc)
            else: acc.append(k)
    leaves=[]; walk(cm.ActiveConfiguration.GetRootComponent3(True),0,leaves); print("leaf components",len(leaves))
    rec=[]
    for k,c in enumerate(leaves):
        if c.GetSuppression2!=2: continue
        md=c.GetModelDoc2; base=os.path.basename(c.GetPathName)
        safe=f"c{k:02d}_"+"".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in base)
        p=os.path.join(TMP,safe)
        if not os.path.exists(p):
            app.ActivateDoc3(md.GetTitle,False,0,I4()); e=I4(); w=I4(); ok=md.Extension.SaveAs(p,0,1,NOD,e,w)
        else: ok="exists"
        xf=xform(c); bb=box(c); rec.append({"name":c.Name2,"file":p,"saveas":ok,"R":xf["R"],"t_mm":xf["t_mm"],"box":bb})
        print(f"  {k:2d} {c.Name2[-44:]:44s} save {ok} t {xf['t_mm']} box {bb}")
    app.ActivateDoc3(title,False,0,I4()); d=app.ActiveDoc
    root_box=box(cm.ActiveConfiguration.GetRootComponent3(True)); print("asm box",root_box)
    json.dump({"rec":rec,"title":title},open(REC,"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
    app.CloseDoc(title)
    for x in list(pv(app,"GetDocuments") or []):
        pn=x.GetPathName or ""
        if pn.startswith(TMP) or x.GetTitle.lower().startswith("kosaplus_ke008") or (not pn and x.GetType==1 and x.GetTitle.startswith("파트")): 
            try: app.CloseDoc(x.GetTitle)
            except Exception: pass
    print("children stage done", len(rec))
elif stage=="compose":
    rec=json.load(open(REC,encoding="utf-8"))["rec"]
    TG=np.array([-7.441,-42.088,40.75])   # 스템축 (7.441,42.088) → 0, 패드면 z −40.75 → 0
    dd=app.GetOpenDocumentByName(OUT)
    if dd is not None: app.CloseDoc(dd.GetTitle)
    if os.path.exists(OUT): os.remove(OUT); print("removed old B4d")
    tmpl=app.GetUserPreferenceStringValue(8); d=app.NewDocument(tmpl,0,0,0); print("new part",d.GetTitle)
    def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
    def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
    def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
    def sel_body(b):
        d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
    def box_close(a,b,tol=0.3): return np.all(np.abs(np.array(a)-np.array(b))<tol)
    final=[]
    def target():
        c=[b for b in bodies() if not any(box_close(bbox(b),fb,0.05) for fb in final)]
        assert len(c)==1, ("target ambiguous",len(c)); return c[0]
    SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}
    for k,r in enumerate(rec):
        Rc=np.array(r["R"]); tc=np.array(r["t_mm"]); exp_box=np.array(r["box"])
        before={pv(b,"Name") for b in bodies()}
        f=d.InsertPart3(r["file"],1|512|262144,""); d.EditRebuild3
        new=[b for b in bodies() if pv(b,"Name") not in before]
        if f is None or len(new)!=1: print("  skip",k,r["name"][-40:],"f",f is not None,"new",len(new)); 
        if not new: continue
        if len(new)>1:
            # 다중바디 파트: 전부 동일 변환 적용
            pass
        for b in new:
            c_loc=centroid(b); c_rot_exp=c_loc@Rc
            if not np.allclose(Rc,np.eye(3),atol=1e-6):
                ang=Rotation.from_matrix(Rc.T).as_euler("xyz")
                for axis,val in zip("xyz",ang):
                    if abs(val)<1e-9: continue
                    s=SLOT[axis]; sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3; assert mv; b=target()
                c_got=centroid(b); assert np.all(np.abs(c_got-c_rot_exp)<0.1), ("rot mismatch",r["name"],c_got,c_rot_exp)
            t=tc+TG; sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(mm(t[0]),mm(t[1]),mm(t[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv
            b=target(); got=bbox(b); final.append(got)
        print(f"  [{k}] {r['name'][-40:]:40s} bodies {len(new)} box {got.round(1)} exp {exp_box.round(1)}")
    bs=bodies(); pb=np.array([v*1000 for v in pv(d,"GetPartBox",True)]); vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs)
    print("bodies",len(bs),"part box (asm coords)",pb.round(2),"vol",round(vol))
    e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved raw B4d",ok,e.value)
    json.dump({"part_box":pb.tolist(),"vol":vol,"bodies":len(bs)},open(os.path.join(DESK,"_검증","ke008_b4d_raw_0914.json"),"w",encoding="utf-8"),indent=1)
stop.set(); print("stage",stage,"done")
