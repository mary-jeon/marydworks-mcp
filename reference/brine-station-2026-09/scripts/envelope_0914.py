# read-only: station components whose world bbox intersects the region around the line (ground 1450~2300, y ±800, z -2800~-1300)
import sys, os, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect()
ST=os.path.join(Z,"S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(ST)
cm=s.ConfigurationManager; print("station cfg",cm.ActiveConfiguration.Name)
G0,G1=1450,2300; Y0,Y1=-800,800; Z0,Z1=-2800,-1300
LINE=("B9f","B9g","J23","J8e","J9d","G11e","G11f","J11d","J11e","G3b","G3c","B4b","B4c","J19e","J5e","J1c","J2_","J2c","B10","G13","G14","H16","J17")
rows=[]
def walk(c,depth):
    for ch in (pv(c,"GetChildren") or []):
        if ch.GetSuppression2!=2: continue
        n=ch.Name2; base=n.split("/")[-1]
        kids=pv(ch,"GetChildren") or []
        if kids and depth<6: walk(ch,depth+1); continue
        b=box(ch)
        if not b: continue
        g0,g1=1109-b[3],1109-b[0]
        if g1<G0 or g0>G1 or b[4]<Y0 or b[1]>Y1 or b[5]<Z0 or b[2]>Z1: continue
        rows.append({"name":n,"ground":[round(g0,1),round(g1,1)],"y":[b[1],b[4]],"z":[b[2],b[5]],"line":base.startswith(LINE),"robot":"900000MU1" in n or "210000MU1" in n})
walk(cm.ActiveConfiguration.GetRootComponent3(True),0)
json.dump(rows,open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for r in sorted(rows,key=lambda r:(r["line"],r["robot"],r["ground"][0])):
    if r["line"]: continue
    print(("ROBOT " if r["robot"] else "      ")+f"{r['name'][-60:]:60s} g={r['ground']} y={r['y']} z={r['z']}")
