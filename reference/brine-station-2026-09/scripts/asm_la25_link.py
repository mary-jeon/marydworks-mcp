# 염수주입라인: link B9b part configs to assembly configs (상승→상승, 하강→하강), delete B12 rod-extension component, re-dump boxes.
import os, json
from swconn import *
from swpv import pv
app=connect()
asm=open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return list(root().GetChildren)
# delete B12 (all configs share components)
asm.ShowConfiguration2("하강"); asm.EditRebuild3
b12=[c.Name2 for c in comps() if c.Name2.startswith("B12_")]
if b12:
    asm.ClearSelection2(True)
    for n in b12: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
    print("delete B12:",b12,asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True); asm.EditRebuild3
for cfg,pcfg in (("상승","상승"),("하강","하강"),("1.상승했을때(해석)","상승"),("2.하강했을때(해석)","하강")):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    for c in comps():
        if c.Name2.startswith("B9b_"):
            before=c.ReferencedConfiguration
            c.ReferencedConfiguration=pcfg; asm.EditRebuild3
            print(f"[{cfg}] B9b refcfg {before} -> {c.ReferencedConfiguration} box {box(c)} supp {c.GetSuppression2}")
# verify rod eye position: 상승 box zmin should be ~-368 (eye -355-13), 하강 ~-508
J=json.load(open(os.path.join(VER,"J3_rebuild_boxes.json"),encoding="utf-8"))
J["dn"]=[n for n in J["dn"] if not n.startswith("B12_")]
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    J[cfg]=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in comps()]
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump(J,open(os.path.join(VER,"J3_rebuild_boxes.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("components:",len(J["상승"]),"dirty",asm.GetSaveFlag,"(not saved)")
