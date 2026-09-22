# 읽기 전용: S30000MU0 고정(f) 부품별 변환·박스·호스트 후보(박스 겹침/근접) 및 구성별 억제 상태
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from swconn import *
from swpv import pv
P=os.path.join(Z,"S30000MU0.SLDASM"); app=connect(); s=app.GetOpenDocumentByName(P); app.ActivateDoc3(P,False,0,I4()); s=app.ActiveDoc; cm=s.ConfigurationManager
CFGS=list(pv(s,"GetConfigurationNames")); print("cfgs",CFGS,"active",cm.ActiveConfiguration.Name)
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
snap={}
for cfg in CFGS:
    s.ShowConfiguration2(cfg); s.EditRebuild3; snap[cfg]={n:c.GetSuppression2 for n,c in comps().items()}
s.ShowConfiguration2("상승"); s.EditRebuild3; cc=comps()
info={}
for n,c in cc.items():
    x=xform(c); b=box(c) if c.GetSuppression2==2 else None
    info[n]={"fixed":c.IsFixed,"R":x["R"],"t":x["t_mm"],"box":b,"path":os.path.basename(c.GetPathName),"supp":{cfg:snap[cfg][n] for cfg in CFGS}}
def gap(b1,b2):
    g=[max(b1[i]-b2[i+3],b2[i]-b1[i+3]) for i in range(3)]; return max(g)  # <=0 → 겹침/접촉
for n,i in info.items():
    if not i["fixed"]: continue
    print(f"\n(f) {n}  path {i['path']}  R {i['R']}  t {i['t']}  box {i['box']}  supp {i['supp']}")
    if i["box"] is None: print("   (suppressed in 상승 — box unknown)"); continue
    cands=[]
    for m,j in info.items():
        if m==n or j["box"] is None: continue
        cands.append((round(gap(i["box"],j["box"]),1),m,j["fixed"]))
    cands.sort(); print("   nearest:",cands[:5])
json.dump(info,open(r"<PROJECT_DIR>\_검증\s30_probe_0915.json","w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
