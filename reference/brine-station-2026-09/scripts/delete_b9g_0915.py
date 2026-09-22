# 2026-09-15: 사용자 승인(「응지워」) 후 B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT 삭제 → 삭제 후 Station 어셈블리 전수 종속 검사(결손 0 확인)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
VER=r"<PROJECT_DIR>\_검증"
T=os.path.join(Z,"B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT")
app=connect()
if app.GetOpenDocumentByName(T) is not None: app.CloseDoc(os.path.basename(T)); print("closed open doc")
asms=[os.path.join(Z,f) for f in os.listdir(Z) if f.lower().endswith(".sldasm") and not f.startswith("~$")]
def refs():
    out={}
    for a in asms:
        dep=app.GetDocumentDependencies2(a,True,False,False)
        out[os.path.basename(a)]=[x for x in (dep or [])[1::2]]
    return out
before=refs(); used=[a for a,l in before.items() if any(os.path.basename(x).lower()==os.path.basename(T).lower() for x in l)]
assert not used, ("still referenced",used)
assert os.path.exists(T); sz=os.path.getsize(T); os.remove(T); print("deleted",os.path.basename(T),sz)
after=refs(); missing={a:[x for x in l if not os.path.exists(x)] for a,l in after.items()}
missing={a:m for a,m in missing.items() if m}
print("missing after delete:",{a:[os.path.basename(x) for x in m] for a,m in missing.items()})
json.dump({"deleted":T,"size":sz,"missing_after":missing},open(os.path.join(VER,"delete_b9g_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("done")
