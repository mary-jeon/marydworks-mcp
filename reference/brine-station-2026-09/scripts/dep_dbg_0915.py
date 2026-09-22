import os, sys
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect()
import time; print("asm mtime",time.ctime(os.path.getmtime(ASM)))
dep=app.GetDocumentDependencies2(ASM,True,False,False)
names=sorted(set(os.path.basename(x) for x in (dep or [])[1::2]))
print(len(names)); [print("  ",n) for n in names if n.startswith(("B9","J8","J5","J23","G3e","B4e"))]
a=app.GetOpenDocumentByName(ASM)
if a is not None:
    cm=a.ConfigurationManager; print("open asm refs:",sorted({os.path.basename(c.GetPathName) for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren") if c.Name2.startswith("B9")}))
