# Read-only: list robot (900000MU1) leaf parts whose top is above 1380 and that lie under the J line footprint (world y ±450, z -2400..-1700).
import os, json
from swconn import *
app=connect()
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
rows=[]
for n,b in leaves:
    top_h=1109-b[0]
    if top_h>1380 and b[4]>-450 and b[1]<450 and b[5]>-2400 and b[2]<-1700:
        rows.append((round(top_h,1),n,[round(v) for v in b]))
rows.sort(reverse=True)
print("robot parts near line footprint (top height, name, world box [x0,y0,z0,x1,y1,z1]; height=1109-x; line y=-y_w, line x=-z_w-2056):")
for r in rows: print(f"  {r[0]:7.1f}  {r[1]:28s} y_w[{r[2][1]},{r[2][4]}] -> line y[{-r[2][4]},{-r[2][1]}]  z_w[{r[2][2]},{r[2][5]}] -> line x[{-r[2][5]-2056},{-r[2][2]-2056}]")
json.dump(rows,open(os.path.join(VER,"J_robot_under_line.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
