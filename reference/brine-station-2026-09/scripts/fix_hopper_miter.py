# Fix S30001MU0 hopper wall corner cut: replace 컷-돌출3 / 컷-돌출-얇게1 / 바디-삭제 with one vertical 45° (plan-view diagonal) cut.
# Diagonal planes in part coords: X + Z = 595 (right), -X + Z = 595 (left)  [asm center is at part Z=595; top flange outer corner (600,-5)]
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect(); stop=watchdog()
HOP=os.path.join(Z,"S30001MU0.SLDPRT")
d=app.ActivateDoc3(HOP,False,0,I4()); d=app.ActiveDoc
print("active:",d.GetTitle)
def feat(doc,name):
    f=doc.FirstFeature
    while f is not None:
        if f.Name==name: return f
        s=f.GetFirstSubFeature
        while s is not None:
            if s.Name==name: return s
            s=s.GetNextSubFeature
        f=f.GetNextFeature
def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
def whats_wrong(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns)
    return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
print("before: bodies",len(bodies()),"whatswrong",whats_wrong(d))
# 1) delete old corner features (absorbed sketches go with them)
for nm in ("바디-삭제/보존 1","컷-돌출-얇게1","컷-돌출3"):
    d.ClearSelection2(True)
    ok=d.Extension.SelectByID2(nm,"BODYFEATURE",0,0,0,False,0,NOD,0)
    r=d.Extension.DeleteSelection2(1)  # swDelete_Absorbed
    print("delete",nm,"selected",ok,"deleted",r)
d.ClearSelection2(True); d.EditRebuild3
print("after delete: bodies",len(bodies()),[ [round(v*1000,1) for v in b.GetBodyBox()] for b in bodies()])
# 2) new sketch on 윗면 (sx=X, sy=-Z): two closed triangles covering X+Z>=595 and -X+Z>=595
d.ClearSelection2(True)
ok=d.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
print("plane selected",ok)
sm=d.SketchManager; sm.InsertSketch(True); sm.AddToDB=True
mm=lambda v:v/1000.0
def tri(pts):
    for i in range(3):
        a=pts[i]; b=pts[(i+1)%3]; sm.CreateLine(mm(a[0]),mm(a[1]),0,mm(b[0]),mm(b[1]),0)
C=595.0
tri([(1200.0,605.0),(35.0,-560.0),(1200.0,-560.0)])      # right: X+Z=595 -> sx - sy = 595
tri([(-1200.0,605.0),(-35.0,-560.0),(-1200.0,-560.0)])   # left: -X+Z=595 -> -sx - sy = 595
sm.AddToDB=False
sk=d.SketchManager.ActiveSketch; skname=sk.Name if sk is not None else None
sm.InsertSketch(True); d.ClearSelection2(True)
print("sketch",skname)
# 3) cut through all both directions
d.Extension.SelectByID2(skname,"SKETCH",0,0,0,False,0,NOD,0)
f=d.FeatureManager.FeatureCut3(True,False,False,9,0,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
print("cut feature:",None if f is None else f.Name)
if f is not None: f.Name="모서리컷_45도"
d.ClearSelection2(True); d.EditRebuild3
bl=bodies()
print("after cut: bodies",len(bl),[ [round(v*1000,1) for v in b.GetBodyBox()] for b in bl])
# 4) verify: planar faces with normal ~ (±1,0,1)/√2 and their plane constants
res=[]
for b in bl:
    for fc in b.GetFaces():
        s=fc.GetSurface
        if s.IsPlane:
            pp=s.PlaneParams; n=[pp[0],pp[1],pp[2]]; p=[v*1000 for v in pp[3:6]]
            if abs(abs(n[0])-0.7071)<0.01 and abs(n[1])<0.01:
                c=sum(n[i]*p[i] for i in range(3))
                res.append({"n":[round(v,4) for v in n],"c_mm":round(c,3),"area":round(fc.GetArea*1e6,1),"box":[round(v*1000,1) for v in fc.GetBox]})
print("diagonal faces (expect |c|=595/sqrt2=420.73):")
for r in res: print("  ",r)
print("whatswrong after:",whats_wrong(d))
print("part box:",[round(v*1000,1) for v in pv(d,"GetPartBox",True)])
json.dump({"diag_faces":res,"bodies":len(bl),"whats_wrong":whats_wrong(d)},open(os.path.join(VER,"S30000MU0_review","fix_hopper_miter.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set()
