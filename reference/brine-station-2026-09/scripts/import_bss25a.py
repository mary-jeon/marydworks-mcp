# Import the 25A manual ball valve STEP (MISUMI BSS-01-25RC, SUS316) as a candidate body geometry for KITZ 10UTM-25A; report bbox, planar/cylindrical port faces. Read-only except creating the imported part in memory (not saved unless 'save' arg).
import os, sys, json
from swconn import *
stop=watchdog()
app=connect()
STEP=r"<HOME>\Desktop\P282-제작정보-2026-08-21\BSS-01-25RC_볼밸브_SUS316_25A.stp"
imp=app.GetImportFileData(STEP)
try: imp.ImportSurfaceBodies=False
except Exception: pass
e=I4(); d=app.LoadFile4(STEP,"r",imp,e)
if d is None:
    # fallback: OpenDoc6 with STEP type
    e=I4(); wn=I4(); d=app.OpenDoc6(STEP,1,1,"",e,wn)
print("imported:",d.GetTitle if d else None,"err",e.value)
is_asm=d.GetTitle.upper().endswith(".SLDASM")
if is_asm:
    root=d.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    comps=list(root.GetChildren); print("assembly with",len(comps),"components")
    bodies=[]
    for c in comps:
        print("  comp",c.Name2,box(c))
        try: bodies+=list(c.GetBody and [c.GetBody] or [])
        except Exception: pass
        try:
            md=c.GetModelDoc2
            if md: bodies+=list(md.GetBodies2(0,True) or [])
        except Exception: pass
    bb=[box(c) for c in comps if box(c)]
    b=[min(x[i] for x in bb) for i in range(3)]+[max(x[i] for x in bb) for i in range(3,6)]
else:
    b=[round(v*1000,2) for v in d.GetPartBox(True)]; bodies=d.GetBodies2(0,True) or []
print("bbox mm",b,"size",[round(b[i+3]-b[i],2) for i in range(3)])
print("bodies",len(bodies))
faces=[]
for bd in bodies:
    for f in bd.GetFaces():
        s=f.GetSurface
        if s.IsPlane and f.GetArea>0.0003:
            pp=s.PlaneParams; fb=[round(v*1000,1) for v in f.GetBox]
            faces.append(("plane",[round(v,3) for v in pp[0:3]],[round(v*1000,1) for v in pp[3:6]],round(f.GetArea*1e6),fb))
        elif s.IsCylinder and f.GetArea>0.0005:
            cp=s.CylinderParams; faces.append(("cyl",[round(v*1000,1) for v in cp[0:3]],[round(v,3) for v in cp[3:6]],round(cp[6]*1000,2),round(f.GetArea*1e6)))
faces.sort(key=lambda t:-t[3] if t[0]=="plane" else -t[4])
for f in faces[:25]: print("  ",f)
json.dump({"bbox":b,"faces":faces},open(os.path.join(VER,"BSS25A_import.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
if "save" in sys.argv:
    p=os.path.join(Z,"K3_valve_body_25A_BSS-01-25RC_asKITZ10UTM.SLDPRT"); ee=I4(); wn=I4()
    print("saved",d.Extension.SaveAs(p,0,1,NOD,ee,wn),p)
else:
    app.CloseDoc(d.GetTitle); print("closed (not saved)")
stop.set()
