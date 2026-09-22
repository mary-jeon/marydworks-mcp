# Read-only: dump 염수주입라인 components (both configs): bbox, transform, mass/CG, plate thickness, cylindrical faces (holes/shafts)
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect(); stop=watchdog()
line=app.ActivateDoc3(ASM,False,0,I4()); line=app.ActiveDoc
out={"configs":{}}
def part_mass(doc):
    try:
        mp=doc.Extension.CreateMassProperty;
        return {"mass_kg":round(mp.Mass,4),"cg_mm":[round(v*1000,2) for v in mp.CenterOfMass],"vol_mm3":round(mp.Volume*1e9,1)}
    except Exception as e: return {"err":repr(e)}
def cyl_faces(comp,R,t):
    res=[]
    b=comp.GetBody
    if b is None: return res
    for fc in b.GetFaces():
        s=fc.GetSurface
        if s.IsCylinder:
            cp=s.CylinderParams; c=[v*1000 for v in cp[0:3]]; ax=list(cp[3:6]); r=cp[6]*1000
            cw=[sum(c[k]*R[k][j] for k in range(3))+t[j] for j in range(3)]; aw=[sum(ax[k]*R[k][j] for k in range(3)) for j in range(3)]
            bx=[round(v*1000,1) for v in fc.GetBox]
            res.append({"r":round(r,2),"center":[round(v,1) for v in cw],"axis":[round(v,3) for v in aw],"area":round(fc.GetArea*1e6,1),"box_local":bx})
    return res
def plane_faces(comp,R,t,minarea=2000):
    res=[]; b=comp.GetBody
    if b is None: return res
    for fc in b.GetFaces():
        s=fc.GetSurface
        if s.IsPlane and fc.GetArea*1e6>=minarea:
            pp=s.PlaneParams; n=list(pp[0:3]); p=[v*1000 for v in pp[3:6]]
            nw=[sum(n[k]*R[k][j] for k in range(3)) for j in range(3)]; pw=[sum(p[k]*R[k][j] for k in range(3))+t[j] for j in range(3)]
            res.append({"n":[round(v,3) for v in nw],"d":round(sum(nw[i]*pw[i] for i in range(3)),2),"area":round(fc.GetArea*1e6,0)})
    return res
docs={d.GetTitle.upper():d for d in app.GetDocuments}
for cfg in ("상승","하강"):
    line.ShowConfiguration2(cfg); line.EditRebuild3
    root=line.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    comps=[]
    for c in root.GetChildren:
        n=c.Name2.split("/")[-1]; sup=c.GetSuppression2
        row={"comp":n,"supp":sup,"refcfg":c.ReferencedConfiguration}
        if sup==0: comps.append(row); continue
        a=list(c.Transform2.ArrayData); R=[a[0:3],a[3:6],a[6:9]]; t=[a[9]*1000,a[10]*1000,a[11]*1000]
        row["t"]=[round(v,2) for v in t]; row["box"]=box(c)
        try:
            b=c.GetBody
            if b is not None:
                mp=b.GetMassProperties(1.0)  # density 1 -> volume-based
                if mp: row["vol_mm3"]=round(mp[3]*1e9,1); row["cg_line"]=[round(v*1000,1) for v in mp[0:3]]
        except Exception as e: row["mp_err"]=repr(e)
        key=n.rsplit("-",1)[0]
        if key.startswith(("J1b","J5c","J8b","J9","J11","G11","J2","B10","G13","J17","H16","G14","G3","B4","B9b")):
            row["cyl"]=cyl_faces(c,R,t)
            if key.startswith(("J1b","J5c","J8b","J9")): row["planes"]=plane_faces(c,R,t)
        comps.append(row)
    out["configs"][cfg]={"components":comps}
    # total mass props of assembly in this config
    try:
        mp=line.Extension.CreateMassProperty
        out["configs"][cfg]["asm_mass"]={"mass_kg":round(mp.Mass,3),"cg_mm":[round(v*1000,1) for v in mp.CenterOfMass]}
    except Exception as e: out["configs"][cfg]["asm_mass"]=repr(e)
line.ShowConfiguration2("상승"); line.EditRebuild3
# per-part mass with material
parts={}
for title,d in docs.items():
    p=d.GetPathName
    if p.lower().startswith(Z.lower()) and title.endswith(".SLDPRT") and title.split("_")[0] in ("J1B","J5C","J8B","J9","J11","G11","J2","B10","G13","J17","H16","G14","G3","B4","B9B","J19B"):
        m=part_mass(d)
        try: mat=d.GetMaterialPropertyName2("",VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""))
        except Exception: mat=None
        try: dens=d.Extension.CreateMassProperty.Density
        except Exception: dens=None
        parts[title]={"mass":m,"material":str(mat),"density":dens,"box":[round(v*1000,1) for v in pv(d,"GetPartBox",True)]}
out["parts"]=parts
json.dump(out,open(os.path.join(VER,"S30000MU0_review","line_review.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for cfg in out["configs"]:
    print("==",cfg, out["configs"][cfg]["asm_mass"])
    for r in out["configs"][cfg]["components"]:
        print(" ",r["comp"],"supp",r["supp"],"t",r.get("t"),"box",r.get("box"),"vol",r.get("vol_mm3"),"cg",r.get("cg_line"))
        for cy in r.get("cyl",[]): print("      cyl r",cy["r"],"c",cy["center"],"ax",cy["axis"],"A",cy["area"])
        for pl in r.get("planes",[]): print("      pln n",pl["n"],"d",pl["d"],"A",pl["area"])
print("== parts")
for k,v in parts.items(): print(" ",k,v)
stop.set()
