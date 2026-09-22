# 1) J1b: 4x Ø9 through holes @(±55,±25)  2) tank: add S30015 flange (y -165) + S30016 gasket (y -177), fix  3) line -> y -179 in 3 configs  4) checks
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect(); stop=watchdog()
mm=lambda v:v/1000.0
BOLTS=[(55,25),(-55,25),(55,-25),(-55,-25)]
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
def cyls(d,r):
    out=[]
    for b in (pv(d,"GetBodies2",0,False) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
                bx=[round(v*1000,1) for v in fc.GetBox]; out.append(((bx[0]+bx[3])/2,(bx[1]+bx[4])/2,bx[2],bx[5]))
    return out
rep={}
# ---- 1) J1b holes
J1B=os.path.join(Z,"J1b_fixed_plate_150x710_t10.SLDPRT")
d=app.ActivateDoc3(J1B,False,0,I4()); d=app.ActiveDoc
d.ClearSelection2(True)
ok=d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
sm=d.SketchManager; sm.InsertSketch(True); sm.AddToDB=True
for (x,y) in BOLTS: sm.CreateCircleByRadius(mm(x),mm(y),0,mm(4.5))
sm.AddToDB=False; skn=sm.ActiveSketch.Name; sm.InsertSketch(True); d.ClearSelection2(True)
d.Extension.SelectByID2(skn,"SKETCH",0,0,0,False,0,NOD,0)
f=d.FeatureManager.FeatureCut3(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False)
if f is not None: f.Name="볼트구멍_4-M8"
d.ClearSelection2(True); d.EditRebuild3
h=cyls(d,4.5); print("J1b Ø9 holes:",h); rep["J1b_holes"]=h
assert len(h)==4 and all(abs(a[2]+10)<0.1 and abs(a[3])<0.1 for a in h), "J1b holes wrong"
cpm=d.Extension.CustomPropertyManager(""); cpm.Add3("REMARK",30,"2026-09-07 호퍼 배출구 플랜지 S30015MU0(용접)에 EPDM 가스켓 S30016MU0 끼고 밑에서 M8x25 STS304 4본 체결 — 볼트구멍 4-Ø9 @(±55,±25)",1)
e=I4(); w_=I4(); print("save J1b",d.Save3(1,e,w_))
# ---- 2) tank: add flange + gasket
TANK=os.path.join(Z,"S30000MU0.SLDASM")
t=app.ActivateDoc3(TANK,False,0,I4()); t=app.ActiveDoc
t.ShowConfiguration2("기본"); t.EditRebuild3
def root(): return t.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
def comp(prefix):
    return [c for c in pv(root(),"GetChildren") if c.Name2.split("/")[-1].startswith(prefix)]
for path,y in ((os.path.join(Z,"S30015MU0.SLDPRT"),-0.165),(os.path.join(Z,"S30016MU0.SLDPRT"),-0.177)):
    nm=os.path.basename(path).split(".")[0]
    if comp(nm): print("already in tank:",nm); continue
    app.OpenDoc6(path,1,1|32,"",I4(),I4())   # ensure loaded
    c=t.AddComponent5(path,0,"",False,"",0.0,y,0.0)
    print("added",nm,None if c is None else c.Name2)
    t.ClearSelection2(True)
    if c is not None:
        c.Select4(False,NOD,False); t.FixComponent(); t.ClearSelection2(True)
t.EditRebuild3
for c in comp("S30015")+comp("S30016"):
    print(" ",c.Name2.split("/")[-1],"fixed",c.IsFixed,"t",xform(c)["t_mm"],"box",box(c))
# ---- 3) line -> y -179 in 3 configs
for cfg in ("기본","상승","하강"):
    t.ShowConfiguration2(cfg); t.EditRebuild3
    lc=comp("염수주입라인")[0]
    m=pv(lc,"GetMates"); print(cfg,"line mates:",0 if not m else len(m),"fixed",lc.IsFixed,"t before",xform(lc)["t_mm"])
    xf=lc.Transform2; a=list(xf.ArrayData); a[10]=-0.179
    xf.ArrayData=a; lc.Transform2=xf; t.EditRebuild3
    print("   t after",xform(comp("염수주입라인")[0])["t_mm"])
t.ShowConfiguration2("기본"); t.EditRebuild3
# ---- 4) checks: gaps between lip / flange / gasket / J1b along y at the outlet
rep["tank_layout"]={c.Name2.split("/")[-1]:{"t":xform(c)["t_mm"],"box":box(c)} for c in comp("S30015")+comp("S30016")+comp("염수주입라인")+comp("S30001MU0-1")}
print(json.dumps(rep["tank_layout"],ensure_ascii=False))
print("tank whatswrong",ww(t))
ST=os.path.join(Z,"S00000MU0.SLDASM"); s=app.ActivateDoc3(ST,False,0,I4()); s=app.ActiveDoc
gz={}
for cfg in ("상승","하강"):
    s.ShowConfiguration2(cfg); s.ForceRebuild3(False)
    r=s.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    tank=[c for c in pv(r,"GetChildren") if c.Name2.split("/")[-1].startswith("S30000MU0")][0]
    line=[c for c in pv(tank,"GetChildren") if c.Name2.split("/")[-1].startswith("염수주입라인")][0]
    out={}
    for c in pv(line,"GetChildren"):
        n=c.Name2.split("/")[-1]
        if c.GetSuppression2!=0 and n.split("-")[0] in ("J17_pipe_3-4in_L100","J1b_fixed_plate_150x710_t10","J5c_moving_plate_200x620_t10"):
            b=box(c); out[n]={"world_box":b,"지상고_min":round(1109-b[3],1),"지상고_max":round(1109-b[0],1)}
    gz[cfg]=out; print(cfg,json.dumps(out,ensure_ascii=False))
    print(cfg,"station whatswrong",ww(s))
rep["ground_clearance"]=gz
s.ShowConfiguration2("하강"); s.EditRebuild3
json.dump(rep,open(os.path.join(VER,"S30000MU0_review","asm_outlet_flange.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set()
