# Parent assemblies: S30000MU0 — set 염수주입라인 referenced config per config (기본/상승→상승, 하강→하강);
# S00000MU0 — add configs 상승/하강, set S30000MU0 referenced config per config, move S30000MU0 up 140 (world -x). Memory only.
import os, json
from swconn import *
from swpv import pv
app=connect()
H=140.0
def set_ref(doc,child_prefix,cfg,refcfg):
    doc.ShowConfiguration2(cfg); doc.EditRebuild3
    for c in doc.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren:
        if c.Name2.startswith(child_prefix):
            b=c.ReferencedConfiguration; c.ReferencedConfiguration=refcfg; doc.EditRebuild3
            print(f"  {doc.GetTitle} [{cfg}] {c.Name2}: {b} -> {c.ReferencedConfiguration}")
# ---- S30000MU0
tank=open_doc(app,os.path.join(Z,"S30000MU0.SLDASM"),2); app.ActivateDoc3(tank.GetPathName,False,0,I4()); tank=app.ActiveDoc
print("S30000MU0 configs:",list(tank.GetConfigurationNames))
for cfg,ref in (("기본","상승"),("상승","상승"),("하강","하강")):
    if cfg in list(tank.GetConfigurationNames): set_ref(tank,"염수주입라인",cfg,ref)
tank.ShowConfiguration2("기본"); tank.EditRebuild3
# ---- S00000MU0
top=open_doc(app,os.path.join(Z,"S00000MU0.SLDASM"),2); app.ActivateDoc3(top.GetPathName,False,0,I4()); top=app.ActiveDoc
print("S00000MU0 configs before:",list(top.GetConfigurationNames))
for cfg,desc in (("상승","염수주입라인 상승(로봇 통과)"),("하강","염수주입라인 하강(개구 삽입)")):
    if cfg not in list(top.GetConfigurationNames):
        c=top.AddConfiguration3(cfg,desc,"",0); print("  config added:",cfg,c is not None)
# move tank up 140: Transform2 is shared across configs
top.ShowConfiguration2("기본"); top.EditRebuild3
for c in top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren:
    if c.Name2.startswith("S30000MU0"):
        a=list(c.Transform2.ArrayData); tx=a[9]*1000
        if abs(tx-(-1106.0))<0.5:
            a[9]=(tx-H)/1000.0
            xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,a); c.Transform2=xf; top.EditRebuild3
            print(f"  S30000MU0 moved: t.x {tx:.1f} -> {c.Transform2.ArrayData[9]*1000:.1f} (위로 {H:.0f})")
        else: print("  S30000MU0 t.x already",tx,"— not moved")
for cfg,ref in (("기본","상승"),("상승","상승"),("하강","하강")):
    set_ref(top,"S30000MU0",cfg,ref)
# ---- verify: world heights of the line's nozzle pipe in 상승/하강 (height = 1109 - x_w)
def walk_find(c,pfx,depth=0,acc=None):
    acc=acc if acc is not None else []
    n=c.Name2.split("/")[-1]
    if n.startswith(pfx): acc.append(c)
    try: kids=list(c.GetChildren)
    except Exception: kids=[]
    if depth<6:
        for k in kids: walk_find(k,pfx,depth+1,acc)
    return acc
for cfg in ("상승","하강"):
    top.ShowConfiguration2(cfg); top.EditRebuild3
    r=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    pipes=[c for c in walk_find(r,"J17_pipe") if c.GetSuppression2==2]; plates=[c for c in walk_find(r,"J1b_fixed") if c.GetSuppression2==2]
    for c in pipes+plates:
        b=box(c); print(f"  [{cfg}] {c.Name2.split('/')[-1]}: bottom height {1109-b[3]:.1f} top height {1109-b[0]:.1f}")
top.ShowConfiguration2("기본"); top.EditRebuild3
print("S00000MU0 configs after:",list(top.GetConfigurationNames),"dirty",top.GetSaveFlag,"| S30000MU0 dirty",tank.GetSaveFlag,"(not saved)")
