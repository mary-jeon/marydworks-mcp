# Robot clearance check for J2 with the fixed side raised H_RAISE (line placed 140 higher than the current S00000MU0 position).
import os, json
from swconn import *
app=connect()
import sys
TAG=sys.argv[1] if len(sys.argv)>1 else "J2"
J=json.load(open(os.path.join(VER,f"{TAG}_rebuild_boxes.json"),encoding="utf-8")); H=J["params"]["H_RAISE"]
def l2w(b):   # line->world at current station position, then raise: x_w -= H (x_w increases downward)
    xs=[-b[5]-801-H,-b[2]-801-H]; ys=[-b[4],-b[1]]; zs=[-b[3]-2056,-b[0]-2056]
    return [min(xs),min(ys),min(zs),max(xs),max(ys),max(zs)]
top=open_doc(app,os.path.join(Z,"S00000MU0.SLDASM"),2,readonly=True)
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
def ov(a0,a1,b0,b1): return min(a1,b1)-max(a0,b0)
out={"H_RAISE":H}
for cfg in ("상승","하강"):
    rows=[]
    for r in J[cfg]:
        if r["supp"]!=2 or not r["box_mm"]: continue
        b=l2w(r["box_mm"])
        hits=[(rb[0],rn) for rn,rb in leaves if ov(b[1],b[4],rb[1],rb[4])>0 and ov(b[2],b[5],rb[2],rb[5])>0]
        bottom_h=round(1109-b[3],1)
        if hits: top_x,rn=min(hits); rows.append((r["comp"],bottom_h,rn,round(1109-top_x,1),round(top_x-b[3],1)))
        else: rows.append((r["comp"],bottom_h,"-",None,None))
    rows.sort(key=lambda t:t[1]); out[cfg]=rows
    print(f"--- {cfg} (고정판 +{H:.0f}): part | bottom height | robot part below | its top | gap")
    for t in rows: print(f"  {t[0]:46s} {t[1]:7.1f}  {t[2]:24s} {str(t[3]):>7}  gap {t[4]}")
json.dump(out,open(os.path.join(VER,f"{TAG}_station_check.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
app.ActivateDoc3(ASM,False,0,I4())
