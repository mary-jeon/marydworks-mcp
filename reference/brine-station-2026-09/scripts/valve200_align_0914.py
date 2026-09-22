# G3d 정렬: 스템축(0.833,0,0.553) → +X 로 Y축 회전, 유로축(Y방향 원통 축) → x=z=0, 면간 중앙 → y=0
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from swconn import *
from swpv import pv
OUT=os.path.join(Z,"G3d_valve_3PC_2in_ISO_Tameson_BL2SA3-200.SLDPRT")
stop=watchdog(); app=connect()
d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
def sel_body(b):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
def probe():
    cyl=[]; pl=[]
    for b in bodies():
        for fc in b.GetFaces():
            s=fc.GetSurface; fb=[round(v*1000,2) for v in fc.GetBox]
            if s.IsCylinder:
                p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],3),round(p[4],3),round(p[5],3)],[round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)],fb,round(fc.GetArea*1e6)))
            elif s.IsPlane: pl.append((round(fc.GetArea*1e6),[round(v,3) for v in pv(fc,"Normal")],fb))
    return cyl,pl
mm=lambda v:v/1000
bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("box before",bx)
feats=[f.Name for f in [] ]
if len([1 for b in bodies()])==1 and abs(bx[0]+67.14)<0.2:
    ang=-math.atan2(0.553,0.833)   # 스템축을 +X로: Y축 둘레 회전
    b=bodies()[0]; sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,ang,0, False,1); d.EditRebuild3; assert mv, "rot"; mv.Name="정렬_회전Y"
    cyl,pl=probe(); ycyl=[c for c in cyl if abs(abs(c[1][1])-1)<1e-3 and 20<=c[0]<=40]; print("Y-axis cyl r20-40:",sorted(set((c[0],c[2][0],c[2][2]) for c in ycyl))[:10])
    stem=[c for c in cyl if abs(abs(c[1][0])-1)<1e-3 and c[0]>40]; print("X-axis cyl r>40:",sorted(set((c[0],c[2][1],c[2][2]) for c in stem))[:6])
    # 유로축 (x,z): Y축 원통 축 원점의 중앙값
    xs=[c[2][0] for c in ycyl]; zs=[c[2][2] for c in ycyl]; fx=float(np.median(xs)); fz=float(np.median(zs))
    ymin=min(c[3][1] for c in cyl); ymax=max(c[3][4] for c in cyl); ymid=(bx[1]+bx[4])/2
    print("flow axis x,z",round(fx,3),round(fz,3),"y range",bx[1],bx[4],"mid",ymid)
    b=bodies()[0]; sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(mm(-fx),mm(-ymid),mm(-fz),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv, "trn"; mv.Name="정렬_이동"
cyl,pl=probe(); bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("box after",bx)
ycyl=sorted(set((c[0],c[2][0],c[2][2]) for c in cyl if abs(abs(c[1][1])-1)<1e-3 and 20<=c[0]<=40)); print("Y-axis cyl r20-40 (r,x,z):",ycyl[:10])
xpl=sorted([p for p in pl if abs(abs(p[1][0])-1)<1e-3],key=lambda p:-p[0])[:8]; print("X-normal planes (A,n,box):"); [print("  ",p) for p in xpl]
ypl=sorted([p for p in pl if abs(abs(p[1][1])-1)<1e-3 and (abs(p[2][1]-bx[1])<0.5 or abs(p[2][1]-bx[4])<0.5)],key=lambda p:-p[0])[:6]; print("port end planes:"); [print("  ",p) for p in ypl]
holes=sorted(set((c[0],round(c[2][1],1),round(c[2][2],1),round(math.hypot(c[2][1],c[2][2]),1)) for c in cyl if abs(abs(c[1][0])-1)<1e-3 and 2<=c[0]<=4.5)); print("X-axis small cyl (pad taps? r,y,z,PCD/2):",holes[:12])
stemsq=[p for p in pl if abs(p[1][0])<1e-3 and p[2][0]>80]; print("stem top-ish planes x>80:",sorted(stemsq,key=lambda p:-p[0])[:4])
print("body extents: x",bx[0],bx[3]," y",bx[1],bx[4]," z",bx[2],bx[5])
json.dump({"box":bx,"ycyl":ycyl,"xpl":xpl,"ypl":ypl,"holes":holes},open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value)
stop.set()
