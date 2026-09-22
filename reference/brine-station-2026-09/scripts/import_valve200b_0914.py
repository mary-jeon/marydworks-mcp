import os, sys, json, time, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
OUT=os.path.join(Z,"G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT")
stop=watchdog(); app=connect()
asm=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.startswith("bl2sa3-200") and x.GetType==2][0]
app.ActivateDoc3(asm.GetTitle,False,0,I4()); asm=app.ActiveDoc
kids=list(pv(asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren")); c=kids[0]; pd=c.GetModelDoc2
app.ActivateDoc3(pd.GetTitle,False,0,I4()); pd=app.ActiveDoc; print("child part",pd.GetTitle)
e=I4(); w=I4(); ok=pd.Extension.SaveAs(OUT,0,1,NOD,e,w); print("SaveAs",ok,e.value,w.value)
app.CloseDoc(asm.GetTitle)
for x in list(pv(app,"GetDocuments") or []):
    if x.GetTitle.startswith("bl2sa3-200") : app.CloseDoc(x.GetTitle)
pd=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); pd=app.ActiveDoc; print("open",pd.GetTitle)
bs=list(pv(pd,"GetBodies2",0,True) or []); sh=list(pv(pd,"GetBodies2",1,True) or [])
bx=[round(v*1000,2) for v in pv(pd,"GetPartBox",True)]; print("solid",len(bs),"sheet",len(sh),"box",bx,"dims",[round(bx[3]-bx[0],1),round(bx[4]-bx[1],1),round(bx[5]-bx[2],1)])
vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs); print("vol mm3",round(vol),"→ kg @7.9",round(vol*7.9e-6,3))
for b in bs: print("  body",pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")],round(pv(b,"GetMassProperties",0)[3]*1e9))
cyl=[]; pl=[]
for b in bs:
    for fc in b.GetFaces():
        s=fc.GetSurface; fb=[round(v*1000,1) for v in fc.GetBox]
        if s.IsCylinder:
            p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],3),round(p[4],3),round(p[5],3)],[round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)],fb,round(fc.GetArea*1e6)))
        elif s.IsPlane:
            pl.append((round(fc.GetArea*1e6),[round(v,3) for v in pv(fc,"Normal")],fb))
pl.sort(key=lambda x:-x[0]); print("largest planes:"); [print("  A",p[0],"n",p[1],"box",p[2]) for p in pl[:16]]
big=sorted(cyl,key=lambda c:-c[0])[:16]; print("big cyl:"); [print("  r",c[0],"ax",c[1],"o",c[2],"box",c[3],"A",c[4]) for c in big]
small=[c for c in cyl if 2.0<=c[0]<=4.5]; print("small cyl groups",collections.Counter(tuple(abs(a) for a in c[1]) for c in small).most_common(4))
for c in sorted(small,key=lambda c:(c[1],c[3]))[:20]: print("  r",c[0],"ax",c[1],"o",c[2],"box",c[3])
json.dump({"box":bx,"vol":vol,"planes":pl[:30],"cyl":sorted(cyl,key=lambda c:-c[0])[:40],"small":small},open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("done")
