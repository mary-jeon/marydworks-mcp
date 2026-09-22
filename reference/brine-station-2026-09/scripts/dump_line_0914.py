# read-only dump of 염수주입라인 per config: comp, suppression, ref config, transform, box
import sys, os, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect()
asm=app.GetOpenDocumentByName(ASM)
cm=asm.ConfigurationManager; cur=cm.ActiveConfiguration.Name
out={"active":cur,"configs":list(asm.GetConfigurationNames),"by_config":{}}
for cfg in ("상승","하강"):
    asm.ShowConfiguration2(cfg)
    r=cm.ActiveConfiguration.GetRootComponent3(True); rows=[]
    for c in pv(r,"GetChildren"):
        rows.append({"comp":c.Name2,"supp":c.GetSuppression2,"refcfg":c.ReferencedConfiguration,"t":(xform(c) or {}).get("t_mm"),"R":(xform(c) or {}).get("R"),"box":box(c)})
    out["by_config"][cfg]=rows
asm.ShowConfiguration2(cur)
json.dump(out,open(sys.argv[1],"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for cfg,rows in out["by_config"].items():
    print("==",cfg)
    for r in rows: print(f"  {r['comp']:44s} s{r['supp']} ref={r['refcfg']:10s} t={r['t']} box={r['box']}")
