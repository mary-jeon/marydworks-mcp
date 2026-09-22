# 2026-09-10: TraceParts TiMOTION TA2-2H-140339-5511-010-1 STEP 구조 조사(읽기 전용, 저장 안 함)
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
from swdialog import template_clicker
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
STEP=r"<PROJECT_DIR>\_3D다운로드\B9f_TA2-2H-140339-5511-010-1.step"
stop=watchdog(); app=connect()
already=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.startswith("B9f_TA2")]
if already: d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); print("reuse")
else:
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); print("LoadFile4 err",e.value)
d=app.ActiveDoc; print("doc",d.GetTitle,"type",d.GetType)
rep={"title":d.GetTitle,"type":d.GetType}
def faces_info(bodies_):
    cyl=[]; pl=[]
    for b in bodies_:
        for fc in b.GetFaces():
            s=fc.GetSurface; fb=[round(v*1000,1) for v in fc.GetBox]
            if s.IsCylinder:
                p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],3),round(p[4],3),round(p[5],3)],[round(p[0]*1000,1),round(p[1]*1000,1),round(p[2]*1000,1)],fb))
            elif s.IsPlane: pl.append((round(fc.GetArea*1e6),[round(v,3) for v in pv(fc,"Normal")],fb))
    return cyl,pl
if d.GetType==2:
    cm=d.ConfigurationManager; comps=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"))
    rep["children"]=[]
    for c in comps:
        md=c.GetModelDoc2; so=len(list(pv(md,"GetBodies2",0,False) or [])) if md else None; sh=len(list(pv(md,"GetBodies2",1,False) or [])) if md else None
        xf=xform(c); bb=box(c); rep["children"].append({"name":c.Name2,"solid":so,"sheet":sh,"t":xf["t_mm"],"R":xf["R"],"box":bb})
        print(f"  {c.Name2[:44]:44s} solid {so} sheet {sh} t {xf['t_mm']} box {bb}")
else:
    so=list(pv(d,"GetBodies2",0,False) or []); sh=list(pv(d,"GetBodies2",1,False) or [])
    print("solid",len(so),"sheet",len(sh),"box",[round(v*1000,1) for v in pv(d,"GetPartBox",True)])
    for b in so: print("  body",pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")],round(pv(b,"GetMassProperties",0)[3]*1e9))
    cyl,pl=faces_info(so)
    holes=[c for c in cyl if 3.5<=c[0]<=4.5]; print("Ø8 hole cylinders (r, axis, origin, box):"); [print("   ",h) for h in holes]
    big=sorted([c for c in cyl if c[0]>8],key=lambda c:-c[0])[:8]; print("big cyl:"); [print("   ",h) for h in big]
    pl.sort(key=lambda x:-x[0]); print("planes:"); [print("   ",p) for p in pl[:8]]
    rep.update({"bodies":[(pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")]) for b in so],"holes":holes,"big":big,"planes":pl[:12]})
json.dump(rep,open(os.path.join(VER,"ta2_step_inspect_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("inspect done (left open, not saved)")
