# 읽기 전용: S00000MU0 최상위·S30000MU0·염수주입라인 컴포넌트의 고정(f) 여부·메이트 수
import os, sys
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect()
for name in ("S00000MU0.SLDASM","S30000MU0.SLDASM","염수주입라인.SLDASM"):
    p=os.path.join(Z,name); d=app.GetOpenDocumentByName(p)
    if d is None: print(name,"not open"); continue
    cm=d.ConfigurationManager; print(f"== {name} cfg {cm.ActiveConfiguration.Name}")
    for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"):
        nm=len(list(pv(c,"GetMates") or []))
        print(f"   {'(f)' if c.IsFixed else '   '} {c.Name2:52s} supp {c.GetSuppression2} mates {nm} t {xform(c)['t_mm'] if xform(c) else None}")
