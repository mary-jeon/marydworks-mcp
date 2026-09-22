# 읽기 전용: 염수주입라인 구성별 컴포넌트(억제·변환·참조구성) + S30015/S30016 피처 목록
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
asm=app.GetOpenDocumentByName(ASM)
cm=asm.ConfigurationManager; cur=cm.ActiveConfiguration.Name
out={"active":cur,"configs":list(asm.GetConfigurationNames),"by_config":{}}
for cfg in out["configs"]:
    asm.ShowConfiguration2(cfg)
    r=cm.ActiveConfiguration.GetRootComponent3(True); rows=[]
    for c in pv(r,"GetChildren"):
        rows.append({"comp":c.Name2,"supp":c.GetSuppression2,"refcfg":c.ReferencedConfiguration,"t":(xform(c) or {}).get("t_mm"),"R":(xform(c) or {}).get("R"),"fixed":c.IsFixed})
    out["by_config"][cfg]=rows
asm.ShowConfiguration2(cur)
for n in ("S30015MU0.SLDPRT","S30016MU0.SLDPRT"):
    d=app.GetOpenDocumentByName(os.path.join(Z,n)); feats=[]
    f=pv(d,'FirstFeature')
    while f is not None:
        feats.append((f.Name,pv(f,'GetTypeName2'))); f=pv(f,'GetNextFeature')
    out[n]=feats
json.dump(out,open(os.path.join(VER,"tank_recheck_2026-09-08","line_dump_before_j4.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("active",cur,"configs",out["configs"])
for cfg,rows in out["by_config"].items():
    print("==",cfg)
    for r in rows: print(f"  {r['comp']:48s} supp{r['supp']} ref={r['refcfg']:8s} t={r['t']}")
for n in ("S30015MU0.SLDPRT","S30016MU0.SLDPRT"): print(n,out[n])
