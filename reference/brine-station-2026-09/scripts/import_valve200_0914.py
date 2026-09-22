# 2026-09-14: Tameson BL2SA3-200 STEP → G3d 파트 (파트면 SaveAs, 어셈블리면 자식 기록). 형상 조사: 유로축·포트면·패드면·탭홀·몸통 범위
import os, sys, json, time, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
from swdialog import template_clicker
STEP=r"<PROJECT_DIR>\_원문\50A\bl2sa3-200.step"
OUT=os.path.join(Z,"G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT")
stop=watchdog(); app=connect()
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle)
if os.path.exists(OUT): os.remove(OUT); print("removed old G3d")
evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); t0=time.time(); d=app.LoadFile4(STEP,"r",imp,e); evt.set()
d=app.ActiveDoc; print("LoadFile4",d is not None,"err",e.value,f"{time.time()-t0:.0f}s","title",d.GetTitle,"type",d.GetType)
if d.GetType==2:
    cm=d.ConfigurationManager; kids=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")); print("assembly children",len(kids))
    for c in kids: print("  ",c.Name2,os.path.basename(c.GetPathName),xform(c)["t_mm"],box(c))
    raise SystemExit("assembly import — handle via children route")
pd=d; e=I4(); w=I4(); ok=pd.Extension.SaveAs(OUT,0,1,NOD,e,w); print("SaveAs",ok,e.value,w.value)
bs=list(pv(pd,"GetBodies2",0,True) or []); sh=list(pv(pd,"GetBodies2",1,True) or [])
bx=[round(v*1000,2) for v in pv(pd,"GetPartBox",True)]; print("solid",len(bs),"sheet",len(sh),"box",bx,"dims",[round(bx[3]-bx[0],1),round(bx[4]-bx[1],1),round(bx[5]-bx[2],1)])
vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs); print("vol mm3",round(vol),"→ kg @7.9",round(vol*7.9e-6,3))
cyl=[]; pl=[]
for b in bs:
    for fc in b.GetFaces():
        s=fc.GetSurface; fb=[round(v*1000,1) for v in fc.GetBox]
        if s.IsCylinder:
            p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],3),round(p[4],3),round(p[5],3)],[round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)],fb,round(fc.GetArea*1e6)))
        elif s.IsPlane:
            pl.append((round(fc.GetArea*1e6),[round(v,3) for v in pv(fc,"Normal")],fb))
pl.sort(key=lambda x:-x[0]); print("largest planes:"); [print("  A",p[0],"n",p[1],"box",p[2]) for p in pl[:14]]
big=sorted(cyl,key=lambda c:-c[0])[:14]; print("big cyl:"); [print("  r",c[0],"ax",c[1],"o",c[2],"box",c[3],"A",c[4]) for c in big]
small=[c for c in cyl if 2.0<=c[0]<=4.5]; print("small cyl groups",collections.Counter(tuple(abs(a) for a in c[1]) for c in small).most_common(4))
for c in sorted(small,key=lambda c:(c[1],c[3]))[:20]: print("  r",c[0],"ax",c[1],"o",c[2],"box",c[3])
json.dump({"box":bx,"vol":vol,"planes":pl[:30],"cyl":sorted(cyl,key=lambda c:-c[0])[:40],"small":small},open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("done (G3d saved, left open)")
