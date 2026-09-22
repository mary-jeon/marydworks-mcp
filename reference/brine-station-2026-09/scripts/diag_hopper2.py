# Read-only: S30001MU0 sketches (23, 27, 28) segments, bodies, DeleteBody data, and instance transforms in tank
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
def pv(o,n):
    v=getattr(o,n)
    try: return v() if callable(v) else v
    except TypeError: return v

app=connect()
docs={d.GetTitle.upper():d for d in app.GetDocuments}
hop=docs["S30001MU0.SLDPRT"]; tank=docs["S30000MU0.SLDASM"]
def feat(doc,name):
    f=doc.FirstFeature
    while f is not None:
        if f.Name==name: return f
        s=f.GetFirstSubFeature
        while s is not None:
            if s.Name==name: return s
            s=s.GetNextSubFeature
        f=f.GetNextFeature
def sketch_segs(doc,name):
    f=feat(doc,name); sk=f.GetSpecificFeature2
    out={"plane_xform":None,"segs":[]}
    try:
        xf=sk.ModelToSketchTransform; a=list(xf.ArrayData); out["plane_xform"]={"R":[round(v,4) for v in a[0:9]],"t_mm":[round(v*1000,2) for v in a[9:12]]}
    except Exception as e: out["plane_xform"]=repr(e)
    segs=pv(sk,'GetSketchSegments') or []
    for s in segs:
        t=pv(s,'GetType')
        row={"type":t,"construction":s.ConstructionGeometry}
        if t==0:
            st=s.GetStartPoint2; en=s.GetEndPoint2
            row["start"]=[round(st.X*1000,2),round(st.Y*1000,2),round(st.Z*1000,2)]; row["end"]=[round(en.X*1000,2),round(en.Y*1000,2),round(en.Z*1000,2)]
        elif t==1:
            st=s.GetStartPoint2; en=s.GetEndPoint2; c=s.GetCenterPoint2
            row["start"]=[round(st.X*1000,2),round(st.Y*1000,2)]; row["end"]=[round(en.X*1000,2),round(en.Y*1000,2)]; row["center"]=[round(c.X*1000,2),round(c.Y*1000,2)]; row["r"]=round(s.GetRadius*1000,2)
        out["segs"].append(row)
    pts=pv(sk,'GetSketchPoints2') or []
    out["points"]=[[round(p.X*1000,2),round(p.Y*1000,2)] for p in pts]
    return out
rep={}
for nm in ("스케치4","스케치23","스케치27","스케치28"):
    try: rep[nm]=sketch_segs(hop,nm); print(nm, json.dumps(rep[nm],ensure_ascii=False))
    except Exception as e: print(nm,"ERR",repr(e))
# cut-extrude3 data
f=feat(hop,"컷-돌출3"); d=f.GetDefinition
try:
    print("컷-돌출3: dir1 type",d.GetEndCondition(True),"depth",round(d.GetDepth(True)*1000,3),"flip",d.FlipSideToCut,"reverse",d.ReverseDirection, "bothdir",d.BothDirections)
except Exception as e: print("cut3 def err",repr(e))
f=feat(hop,"컷-돌출-얇게1"); d=f.GetDefinition
try: print("컷-돌출-얇게1: end",d.GetEndCondition(True),"depth",round(d.GetDepth(True)*1000,3),"thin",d.ThinFeature, "flip",d.FlipSideToCut)
except Exception as e: print("cutthin err",repr(e))
# bodies
bods=hop.GetBodies2(0,False) or []
print("solid bodies:",len(bods))
for b in bods:
    print("  ",b.Name, [round(v*1000,1) for v in b.GetBodyBox()], "visible",b.Visible)
f=feat(hop,"바디-삭제/보존 1"); d=f.GetDefinition
try:
    print("DeleteBody: error", f.GetErrorCode2(False), "keep", getattr(d,"KeepBodies",None))
    bb=pv(d,'Bodies')
    print("  bodies:", None if bb is None else [ (x.Name if x is not None else None) for x in bb])
except Exception as e: print("deletebody err",repr(e))
# what's wrong on hop after? no.
# instance transforms and mates in tank
root=tank.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
for c in root.GetChildren:
    n=c.Name2.split("/")[-1]
    if n.startswith("S30001MU0"):
        x=xform(c); print(n,"R",x["R"],"t",x["t_mm"],"fixed",c.IsFixed)
        mates=pv(c,'GetMates') or []
        for m in mates:
            try:
                ents=m.GetMateEntityCount; names=[]
                for i in range(ents):
                    me=m.MateEntity(i); cc=me.ReferenceComponent
                    names.append((cc.Name2.split('/')[-1] if cc else None, me.ReferenceType2))
                print("    mate",m.Type,"align",m.Alignment,names)
            except Exception as e: print("    mate err",repr(e))
json.dump(rep,open(os.path.join(VER,"S30000MU0_review","diag_hopper2.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
