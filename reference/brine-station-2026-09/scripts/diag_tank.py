# Read-only diagnosis: What's Wrong errors on station/tank/line docs + hopper wall geometry (S30001MU0 instances)
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
app=connect()
docs={d.GetTitle.upper():d for d in app.GetDocuments}
def ww(doc):
    out=[]
    try:
        ext=doc.Extension
        feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
        ok=ext.GetWhatsWrong(feats,codes,warns)
        fl=feats.value or []; cl=codes.value or []; wl=warns.value or []
        for i,f in enumerate(fl):
            try: nm=f.Name
            except Exception: nm=str(f)
            out.append({"feature":nm,"code":cl[i] if i<len(cl) else None,"warning":bool(wl[i]) if i<len(wl) else None})
    except Exception as e:
        out.append({"error":repr(e)})
    return out
targets=["S00000MU0.SLDASM","S30000MU0.SLDASM","염수주입라인.SLDASM","S10000MU0.SLDASM","S20000MU0.SLDASM"]
report={"whats_wrong":{}}
for t in targets:
    d=docs.get(t.upper())
    if d is None: report["whats_wrong"][t]="not open"; continue
    report["whats_wrong"][t]=ww(d)
    print(t, json.dumps(report["whats_wrong"][t],ensure_ascii=False))
# also every part/asm in the station folder
zl=Z.lower()
for title,d in docs.items():
    try: p=d.GetPathName
    except Exception: p=""
    if p.lower().startswith(zl) and title not in [x.upper() for x in targets]:
        r=ww(d)
        if r: report["whats_wrong"][title]=r; print(title, json.dumps(r,ensure_ascii=False))
# hopper geometry
tank=docs["S30000MU0.SLDASM"]
root=tank.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
comps=[]
for c in root.GetChildren:
    n=c.Name2.split("/")[-1]
    comps.append({"comp":n,"path":os.path.basename(c.GetPathName),"supp":c.GetSuppression2,"refcfg":c.ReferencedConfiguration,"box":box(c),"xform":xform(c)})
report["tank_components"]=comps
for c in comps: print(c["comp"],c["path"],c["supp"],c["box"],c["xform"]["t_mm"] if c["xform"] else None)
# S30001MU0 part: feature tree + sketch dims
hop=docs.get("S30001MU0.SLDPRT")
if hop:
    ft=[]; f=hop.FirstFeature
    while f is not None:
        row={"name":f.Name,"type":f.GetTypeName2,"supp":f.IsSuppressed2(1,None) if False else None}
        dd=f.GetFirstDisplayDimension
        dims=[]
        while dd is not None:
            dm=dd.GetDimension2(0)
            try: dims.append({"name":dm.FullName,"val":round(dm.GetSystemValue3(1,None)[0]*1000,3) if False else round(dm.SystemValue*1000,3)})
            except Exception as e: dims.append({"name":dm.FullName,"err":repr(e)})
            dd=f.GetNextDisplayDimension(dd)
        row["dims"]=dims; ft.append(row)
        sub=f.GetFirstSubFeature
        while sub is not None:
            srow={"name":"  "+sub.Name,"type":sub.GetTypeName2}
            dd=sub.GetFirstDisplayDimension; dims=[]
            while dd is not None:
                dm=dd.GetDimension2(0)
                try: dims.append({"name":dm.FullName,"val":round(dm.SystemValue*1000,3)})
                except Exception as e: dims.append({"name":dm.FullName,"err":repr(e)})
                dd=sub.GetNextDisplayDimension(dd)
            srow["dims"]=dims; ft.append(srow)
            sub=sub.GetNextSubFeature
        f=f.GetNextFeature
    report["S30001MU0_features"]=ft
    for r in ft: print(r["name"],r["type"],r.get("dims"))
    # planar faces of the part body
    faces=[]
    for b in hop.GetBodies2(0,True):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsPlane:
                pp=s.PlaneParams
                faces.append({"n":[round(v,4) for v in pp[0:3]],"p":[round(v*1000,2) for v in pp[3:6]],"area":round(fc.GetArea*1e6,1),"box":[round(v*1000,1) for v in fc.GetBox]})
    faces.sort(key=lambda x:-x["area"])
    report["S30001MU0_faces"]=faces
    print("hopper wall planar faces:")
    for fc in faces: print("  ",fc)
    print("part box:",[round(v*1000,1) for v in hop.GetPartBox(True)] if hasattr(hop,"GetPartBox") else None)
json.dump(report,open(os.path.join(VER,"S30000MU0_review","diag_tank.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("saved diag_tank.json")
