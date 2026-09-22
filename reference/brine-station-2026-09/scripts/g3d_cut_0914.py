# G3d 포트 나사부 표현 컷: 정면(z0) 스케치 원 r30.3, 시작조건 오프셋 50 + 깊이 20 → r30.3 원통면 z 범위로 검증
import os, sys, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
mm=lambda v:v/1000
app=connect(); P=os.path.join(Z,"G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT"); d=app.GetOpenDocumentByName(P); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in (pv(d,"GetBodies2",0,True) or []))
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
def r303():
    out=[]
    for b in pv(d,"GetBodies2",0,True):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-30.3)<0.05: fb=[round(v*1000,1) for v in fc.GetBox]; out.append((fb[2],fb[5]))
    return sorted(out)
def sketch():
    d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(30.3)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def delete(n,kind):
    d.ClearSelection2(True); d.Extension.SelectByID2(n,kind,0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
v0=vol(d); print("vol0",round(v0),"r30.3 faces",r303())
targets={"상":(50.0,70.0),"하":(-70.0,-50.0)}
for tag,(z0,z1) in targets.items():
    fn="포트컷_"+tag
    if fn in feat_names(d): print("exists",fn); continue
    done=False
    for dirflag in (True,False):
        for flip in (False,True):
            sk=sketch()
            f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(20.0),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(50.0),flip,False); d.EditRebuild3
            if f is None: delete(sk,"SKETCH"); print("  ",tag,dirflag,flip,"cut None"); continue
            f.Name=fn; faces=r303(); dv=v0-vol(d); print("  ",tag,"dir",dirflag,"flip",flip,"dV",round(dv),"r30.3",faces)
            if any(abs(a-z0)<0.3 and abs(b-z1)<0.3 for a,b in faces) and 3000<dv<25000: done=True; v0=vol(d); break
            delete(fn,"BODYFEATURE")
        if done: break
    assert done, tag
bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("final vol",round(vol(d)),"box",bx,"feats",[n for n in feat_names(d) if n.startswith("포트")])
e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value)
