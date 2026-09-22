# G3d 정렬 2차: 유로축(면적 최대 원통 축) → Z, 스템축 = Y 유지. 유로축 → x=y=0, 면간 중앙 → z=0
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from swconn import *
from swpv import pv
OUT=os.path.join(Z,"G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT")
stop=watchdog(); app=connect()
d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
mm=lambda v:v/1000
def body(): return list(pv(d,"GetBodies2",0,False))[0]
def sel_body(b):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
def probe():
    cyl=[]; pl=[]
    for fc in body().GetFaces():
        s=fc.GetSurface; fb=[round(v*1000,2) for v in fc.GetBox]; A=fc.GetArea*1e6
        if s.IsCylinder:
            p=s.CylinderParams; cyl.append(((p[3],p[4],p[5]),p[6]*1000,A,(p[0]*1000,p[1]*1000,p[2]*1000),fb))
        elif s.IsPlane: pl.append((tuple(pv(fc,"Normal")),A,fb))
    return cyl,pl
def flow_axis(cyl):
    acc={}
    for ax,r,A,o,fb in cyl:
        k=tuple(round(abs(v),2) for v in ax); acc[k]=acc.get(k,0)+A
    return max(acc.items(),key=lambda kv:kv[1])
def delete_feat(name):
    d.ClearSelection2(True); assert d.Extension.SelectByID2(name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.EditRebuild3
cyl,pl=probe(); ax,A=flow_axis(cyl); print("flow axis now",ax,round(A))
if ax!=(0.0,0.0,1.0):
    a=math.atan2(ax[0],ax[2])
    for sgn in (1,-1):
        sel_body(body()); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,sgn*a,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_회전Y2"
        cyl,pl=probe(); ax2,_=flow_axis(cyl); print(" try sign",sgn,"→ flow axis",ax2)
        if ax2==(0.0,0.0,1.0): break
        delete_feat("정렬_회전Y2")
    else: raise SystemExit("rotation failed")
cyl,pl=probe()
zc=[c for c in cyl if abs(abs(c[0][2])-1)<1e-3]
big=sorted(zc,key=lambda c:-c[2])[:6]; print("Z-axis big cyl (r,A,o):",[(round(c[1],1),round(c[2]),[round(v,2) for v in c[3]]) for c in big])
fx=float(np.median([c[3][0] for c in big])); fy=float(np.median([c[3][1] for c in big]))
bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]
zpl=[p for p in pl if abs(abs(p[0][2])-1)<1e-3]; zmin=min(p[2][2] for p in zpl); zmax=max(p[2][5] for p in zpl); print("Z-normal planes z range",round(zmin,2),round(zmax,2),"box z",bx[2],bx[5])
zmid=(zmin+zmax)/2
if abs(fx)>0.01 or abs(fy)>0.01 or abs(zmid)>0.01:
    sel_body(body()); mv=d.FeatureManager.InsertMoveCopyBody2(mm(-fx),mm(-fy),mm(-zmid),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_이동2"
cyl,pl=probe(); bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("box after",bx)
zc=sorted([(round(c[1],2),round(c[3][0],2),round(c[3][1],2),round(c[2])) for c in cyl if abs(abs(c[0][2])-1)<1e-3],key=lambda x:-x[3])[:8]; print("Z cyl (r,x,y,A):",zc)
ends=sorted([(round(p[1]),[round(v,2) for v in p[0]],[round(v,1) for v in p[2]]) for p in pl if abs(abs(p[0][2])-1)<1e-3 and (abs(p[2][2]-bx[2])<0.5 or abs(p[2][5]-bx[5])<0.5)],key=lambda x:-x[0])[:4]; print("port end faces:",ends)
pad=sorted([(round(p[1]),[round(v,2) for v in p[0]],[round(v,1) for v in p[2]]) for p in pl if abs(p[0][1]-1)<1e-3],key=lambda x:-x[0])[:3]; print("+Y planes (pad):",pad)
taps=sorted(set((round(c[1],2),round(c[3][0],1),round(c[3][2],1),round(math.hypot(c[3][0],c[3][2]),1)) for c in cyl if abs(abs(c[0][1])-1)<1e-3 and 2<=c[1]<=4.6)); print("Y-axis small cyl (r,x,z,PCD/2):",taps)
ytop=[p for p in pl if abs(p[0][1]-1)<1e-3]; print("max +Y plane y:",max(p[2][4] for p in ytop),"box y",bx[1],bx[4])
sq=[(round(p[1]),[round(v,1) for v in p[2]]) for p in pl if abs(p[0][1])<1e-3 and p[2][1]>60]; print("stem side planes y>60:",sq[:8])
feats=[]; f=pv(d,"FirstFeature")
while f is not None: feats.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
print("feats",[n for n,t in feats if t in ("MoveCopyBody","ImportedFeature","Imported")])
json.dump({"box":bx,"zcyl":zc,"ends":ends,"pad":pad,"taps":taps},open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value); stop.set()
