# Read-only: open 염수주입라인.SLDASM (disk = G안), dump components/configs; open S30000MU0 read-only to read hopper (S30001MU0) footprint and line placement.
import os, json
from swconn import *
app=connect()
asm=open_doc(app,ASM,2)
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
print("asm",asm.GetTitle,"configs",list(asm.GetConfigurationNames),"active",asm.ConfigurationManager.ActiveConfiguration.Name)
res={"configs":list(asm.GetConfigurationNames)}
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    comps=dump_components(asm); res[cfg]=comps
    print(f"--- {cfg}: {len(comps)} components (supp 2=resolved,0=suppressed)")
    for c in comps: print(f"  {c['comp']:48s} supp={c['supp']} box={c['box_mm']} t={c['xform']['t_mm'] if c['xform'] else None}")
asm.ShowConfiguration2("상승")
# hopper footprint from tank assembly (read-only open)
TANK=os.path.join(Z,"S30000MU0.SLDASM")
tank=open_doc(app,TANK,2,readonly=True)
tr=tank.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
hop=[]
for c in tr.GetChildren:
    n=c.Name2
    hop.append({"comp":n,"box_mm":box(c),"xform":xform(c)})
    print(f"  TANK child {n:40s} box={box(c)} t={xform(c)['t_mm'] if xform(c) else None}")
res["tank_children"]=hop
json.dump(res,open(os.path.join(VER,"J_state_before.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("dirty: line",asm.GetSaveFlag,"tank",tank.GetSaveFlag)
print("saved -> _검증/J_state_before.json")
