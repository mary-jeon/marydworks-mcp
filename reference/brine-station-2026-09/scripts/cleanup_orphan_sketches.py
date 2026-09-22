# 고아 스케치 삭제: 어떤 피처에도 흡수/참조되지 않은 ProfileFeature를 지운다. 형상 불변 확인(box·면 수) 후 결과 출력. 저장은 별도.
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
def nfaces(d): return sum(len(b.GetFaces()) for b in (pv(d,"GetBodies2",0,True) or []))
for fn in sys.argv[1:]:
    P=os.path.join(Z,fn); d=app.GetOpenDocumentByName(P)
    if d is None: print("not open",fn); continue
    app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
    b0=[round(v*1000,1) for v in pv(d,"GetPartBox",True)]; f0=nfaces(d)
    orphans=[]; f=pv(d,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature":
            kids=pv(f,"GetChildren") or []
            if len(list(kids))==0: orphans.append(f.Name)
        f=pv(f,"GetNextFeature")
    deleted=[]
    for nm in orphans:
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(nm,"SKETCH",0,0,0,False,0,NOD,0):
            ok=d.Extension.DeleteSelection2(0); deleted.append((nm,bool(ok)))
    d.ClearSelection2(True); d.EditRebuild3
    b1=[round(v*1000,1) for v in pv(d,"GetPartBox",True)]; f1=nfaces(d)
    left=[]; f=pv(d,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": left.append(f.Name)
        f=pv(f,"GetNextFeature")
    print(f"{fn}: deleted {deleted} | sketches left {left} | box same {b0==b1} faces {f0}->{f1}")
