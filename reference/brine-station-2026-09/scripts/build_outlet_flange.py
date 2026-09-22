# Build hopper outlet flange S30015MU0 (150x150x t12, opening 80 sq, 4x M8 blind tapped from below @ (±55,±25))
# and EPDM gasket S30016MU0 (150x150x t2, opening 80 sq, 4x Ø9). Part coords: plate top at Y=0, plate below (−Y). sx=X, sy=−Z on 윗면.
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect(); stop=watchdog()
mm=lambda v:v/1000.0
BOLTS=[(55,25),(-55,25),(55,-25),(-55,-25)]
def sel_plane(d,names):
    for nm in names:
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def bodies(d): return list(pv(d,"GetBodies2",0,False) or [])
def bbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def cyls(d):
    out=[]
    for b in bodies(d):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder:
                cp=s.CylinderParams; out.append({"r":round(cp[6]*1000,2),"box":[round(v*1000,1) for v in fc.GetBox]})
    return out
def new_part():
    tpl=app.GetDocumentTemplate(1,"",0,0,0); d=app.NewDocument(tpl,0,0,0); return d
def ring(d,outer,inner,thick):
    sel_plane(d,("윗면","Top Plane")); sm=d.SketchManager; sm.InsertSketch(True); sm.AddToDB=True
    sm.CreateCenterRectangle(0,0,0,mm(outer/2),mm(outer/2),0); sm.CreateCenterRectangle(0,0,0,mm(inner/2),mm(inner/2),0)
    sm.AddToDB=False; sk=sm.ActiveSketch; name=sk.Name; sm.InsertSketch(True); d.ClearSelection2(True)
    for dirn in (False,True):
        d.Extension.SelectByID2(name,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(thick),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
        d.ClearSelection2(True); d.EditRebuild3; bx=bbox(d)
        if f is not None and bx[4]<=0.01 and bx[1]<-thick+0.5: return f,bx
        if f is not None: d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.ClearSelection2(True); d.EditRebuild3
    raise RuntimeError("extrude direction failed "+str(bx))
def holes(d,pts,dia,depth,thick,blind):
    # sketch on plane Y=-thick (offset from 윗면), cut toward +Y
    sel_plane(d,("윗면","Top Plane"))
    pl=d.FeatureManager.InsertRefPlane(8|256,mm(thick),0,0,0,0); d.ClearSelection2(True)
    plname=pl.Name
    d.Extension.SelectByID2(plname,"PLANE",0,0,0,False,0,NOD,0)
    sm=d.SketchManager; sm.InsertSketch(True); sm.AddToDB=True
    for (x,y) in pts: sm.CreateCircleByRadius(mm(x),mm(-y),0,mm(dia/2))  # sy=-Z: hole at (X=x, Z=y)
    sm.AddToDB=False; sk=sm.ActiveSketch; name=sk.Name; sm.InsertSketch(True); d.ClearSelection2(True)
    for dirn in (False,True):
        d.Extension.SelectByID2(name,"SKETCH",0,0,0,False,0,NOD,0)
        if blind: f=d.FeatureManager.FeatureCut3(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
        else: f=d.FeatureManager.FeatureCut3(False,False,dirn,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
        d.ClearSelection2(True); d.EditRebuild3
        cy=[c for c in cyls(d) if abs(c["r"]-dia/2)<0.05]
        ok=len(cy)==len(pts) and all(c["box"][1]>=-thick-0.01 and c["box"][4]<=0.01 for c in cy)
        if blind: ok=ok and all(abs((c["box"][4]-c["box"][1])-depth)<0.1 for c in cy)
        print("  holes try dirn",dirn,"->",len(cy),"faces", cy[:2], "ok",ok)
        if f is not None and ok: return f
        if f is not None: d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0); d.ClearSelection2(True); d.EditRebuild3
    raise RuntimeError("hole cut failed")
def props(d,kv):
    cpm=d.Extension.CustomPropertyManager("")
    for k,v in kv.items(): cpm.Add3(k,30,str(v),1)
def save_as(d,path):
    e=I4(); w_=I4(); ok=d.Extension.SaveAs3(path,0,1,NOD,NOD,e,w_); print("saveas",os.path.basename(path),ok,e.value,w_.value); return ok
report={}
# --- flange S30015MU0
d=new_part(); f,bx=ring(d,150,80,12); print("flange ring box",bx)
holes(d,BOLTS,6.8,10,12,True)
props(d,{"RELATION NO.":"S30015MU0","PROJECT NO.":"S00000MU0","TITLE":"HOPPER OUTLET FLANGE","SPEC":"STS 304 150x150 t12, 개구 80각, 4-M8 탭(깊이 10, 밑면에서) @(±55,±25)","Material":"STS 304","QT'Y":"1","DATE":"2026-09-07",
  "REMARK":"호퍼 립(140각·t5) 밑면에 둘레 필릿 용접(탱크 제작 시). 고정판 J1b와 EPDM 가스켓 S30016MU0 사이에 두고 밑에서 M8x25 STS304 4본 체결. t12 = M8 탭 깊이 10 확보용"})
report["S30015MU0"]={"box":bbox(d),"cyl":cyls(d),"bodies":len(bodies(d))}
save_as(d,os.path.join(Z,"S30015MU0.SLDPRT"))
# --- gasket S30016MU0
g=new_part(); f,bx=ring(g,150,80,2); print("gasket ring box",bx)
holes(g,BOLTS,9.0,0,2,False)
props(g,{"RELATION NO.":"S30016MU0","PROJECT NO.":"S00000MU0","TITLE":"GASKET EPDM","SPEC":"EPDM 시트 t2 150x150, 개구 80각, 4-Ø9 @(±55,±25)","Material":"EPDM","QT'Y":"1","DATE":"2026-09-07","REMARK":"호퍼 배출구 플랜지 S30015MU0 ↔ 고정판 J1b 사이. 접속 3원칙 ③(플랜지+EPDM)"})
report["S30016MU0"]={"box":bbox(g),"cyl":cyls(g),"bodies":len(bodies(g))}
save_as(g,os.path.join(Z,"S30016MU0.SLDPRT"))
print(json.dumps(report,ensure_ascii=False,indent=1))
json.dump(report,open(os.path.join(VER,"S30000MU0_review","outlet_flange_parts.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set()
