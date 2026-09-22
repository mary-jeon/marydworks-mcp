# 2026-09-10: MISUMI STEP 3종(J2 PSSFAQ16-590-B10 · G11e SHCCG8-22.8 · J11d SHCCG8-18) 구조·방향 조사 + 현재 파트(J2·G11e·J11d)의 박스·어셈블리 변환 (읽기 전용)
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
from swdialog import template_clicker
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
DL=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_3D다운로드")
STEPS={"J2":"J2_PSSFAQ16-590-B10.step","G11e":"G11e_SHCCG8-22.8.step","J11d":"J11d_SHCCG8-18.0.step"}
stop=watchdog(); app=connect()
rep={}
for code,fn in STEPS.items():
    p=os.path.join(DL,fn); assert os.path.exists(p),p
    evt=template_clicker(); imp=app.GetImportFileData(p); e=I4(); d=app.LoadFile4(p,"r",imp,e); evt.set(); d=app.ActiveDoc
    if d.GetType==2:
        cm0=d.ConfigurationManager; kids=list(pv(cm0.ActiveConfiguration.GetRootComponent3(True),"GetChildren")); info=[]
        for c in kids:
            md=c.GetModelDoc2; so_=len(list(pv(md,"GetBodies2",0,False) or [])) if md else None
            cylk=[]
            for b in (pv(md,"GetBodies2",0,False) or []):
                for fc in b.GetFaces():
                    s=fc.GetSurface
                    if s.IsCylinder:
                        q=s.CylinderParams; cylk.append((round(q[6]*1000,3),[round(q[3],2),round(q[4],2),round(q[5],2)],[round(q[0]*1000,2),round(q[1]*1000,2),round(q[2]*1000,2)],[round(v*1000,2) for v in fc.GetBox]))
            cylk.sort(key=lambda c:-c[0]); xf=xform(c)
            info.append({"name":c.Name2,"path":c.GetPathName,"solid":so_,"R":xf["R"],"t":xf["t_mm"],"box":box(c),"cyl":cylk[:8]})
            print(f"   child {c.Name2[:40]} solid {so_} t {xf['t_mm']} R {xf['R']} box {box(c)}")
            for cy in cylk[:6]: print("      cyl",cy)
        rep[code]={"title":d.GetTitle,"type":2,"children":info}; print(f"== {code} {d.GetTitle} ASSEMBLY children {len(kids)}")
        paths=[c.GetPathName for c in kids]; app.CloseDoc(d.GetTitle)
        for pth in paths:
            for x in list(pv(app,"GetDocuments") or []):
                if x.GetPathName==pth: app.CloseDoc(x.GetTitle)
        continue
    so=list(pv(d,"GetBodies2",0,False) or []); sh=list(pv(d,"GetBodies2",1,False) or [])
    bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]
    cyl=[]
    for b in so:
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder:
                q=s.CylinderParams; cyl.append((round(q[6]*1000,3),[round(q[3],2),round(q[4],2),round(q[5],2)],[round(q[0]*1000,2),round(q[1]*1000,2),round(q[2]*1000,2)],[round(v*1000,2) for v in fc.GetBox]))
    cyl.sort(key=lambda c:-c[0])
    print(f"== {code} {d.GetTitle} type {d.GetType} solid {len(so)} sheet {len(sh)} box {bx}")
    for c in cyl[:8]: print("   cyl",c)
    rep[code]={"title":d.GetTitle,"solid":len(so),"sheet":len(sh),"box":bx,"cyl":cyl[:12]}
    app.CloseDoc(d.GetTitle)
# 현재 파트·어셈블리 변환
a=app.GetOpenDocumentByName(ASM); cm=a.ConfigurationManager; a.ShowConfiguration2("상승"); a.EditRebuild3
cc={c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
for n in ("J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-3","G11e_MISUMI_SHCCG8-18.4_pin-1","J11d_MISUMI_SHCCG8-20.4_pin-1"):
    c=cc[n]; xf=xform(c); md=c.GetModelDoc2; pb=[round(v*1000,2) for v in pv(md,"GetPartBox",True)]
    print("cur",n,"R",xf["R"],"t",xf["t_mm"],"partbox",pb,"asmbox",box(c)); rep["cur_"+n]={"R":xf["R"],"t":xf["t_mm"],"partbox":pb,"asmbox":box(c)}
json.dump(rep,open(os.path.join(VER,"misumi_steps_inspect_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("inspect done")
