# (1) remove the wrong 상승 hose arc from the J assembly (memory only), re-dump boxes; (2) robot clearance check vs S00000MU0 (read-only open).
import os, json
from swconn import *
app=connect()
asm=open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
arc=[c.Name2 for c in root().GetChildren if c.Name2.startswith("J19_hose_3-4in_arc")]
if arc:
    asm.ClearSelection2(True)
    for n in arc: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
    print("delete arc hose:",arc,asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True); asm.EditRebuild3
J=json.load(open(os.path.join(VER,"J_rebuild_boxes.json"),encoding="utf-8"))
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    J[cfg]=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in root().GetChildren]
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump(J,open(os.path.join(VER,"J_rebuild_boxes.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
# ---- robot clearance: line -> world: x_w=-z-801, y_w=-y, z_w=-x-2056 ; height above ground = 1109 - x_w
def l2w(b):
    xs=[-b[5]-801,-b[2]-801]; ys=[-b[4],-b[1]]; zs=[-b[3]-2056,-b[0]-2056]
    return [min(xs),min(ys),min(zs),max(xs),max(ys),max(zs)]
TOP=os.path.join(Z,"S00000MU0.SLDASM")
top=open_doc(app,TOP,2,readonly=True)
r0=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
leaves=[]
def walk(c,depth,ur):
    n=c.Name2.split("/")[-1]
    try: kids=list(c.GetChildren)
    except Exception: kids=[]
    ur=ur or n.startswith("900000MU1")
    if ur and not kids:
        b=box(c)
        if b: leaves.append((n,b))
    if depth<14:
        for k in kids: walk(k,depth+1,ur)
for c in r0.GetChildren: walk(c,1,False)
print("robot leaf parts:",len(leaves))
def ov(a0,a1,b0,b1): return min(a1,b1)-max(a0,b0)
out={}
for cfg in ("상승","하강"):
    rows=[]
    for r in J[cfg]:
        if r["supp"]!=2 or not r["box_mm"]: continue
        b=l2w(r["box_mm"])
        hits=[(rb[0],rn) for rn,rb in leaves if ov(b[1],b[4],rb[1],rb[4])>0 and ov(b[2],b[5],rb[2],rb[5])>0]
        bottom_h=round(1109-b[3],1)
        if hits:
            top_x,rn=min(hits); rows.append((r["comp"],bottom_h,rn,round(1109-top_x,1),round(top_x-b[3],1)))
        else: rows.append((r["comp"],bottom_h,"-",None,None))
    rows.sort(key=lambda t:t[1])
    out[cfg]=rows
    print(f"--- {cfg}: part | bottom height | robot part directly below | its top height | gap (neg = 침범)")
    for t in rows: print(f"  {t[0]:46s} {t[1]:7.1f}  {t[2]:24s} {str(t[3]):>7}  gap {t[4]}")
json.dump(out,open(os.path.join(VER,"J_station_check.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
app.ActivateDoc3(ASM,False,0,I4())
print("done; line dirty",asm.GetSaveFlag,"(not saved)")
