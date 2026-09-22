# 2026-09-17: 사용자 승인(「1,2 둘다 ok」) 미참조 파일 11개 삭제 — 열림 확인 → 참조 재확인 → 삭제 → 모든 어셈블리 결손 검사
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect(); rep={}
cands=[l.strip() for l in open(os.path.join(DESK,"_검증","unused_candidates_0917.txt"),encoding="utf-8") if l.strip()]
open_paths={}
for x in list(pv(app,"GetDocuments") or []):
    try: open_paths[os.path.basename(x.GetPathName).lower()]=x
    except Exception: pass
asms=[os.path.join(Z,f) for f in os.listdir(Z) if f.lower().endswith(".sldasm") and not f.startswith("~$")]
refs={}
for p in asms:
    dep=app.GetDocumentDependencies2(p,True,False,False); refs[os.path.basename(p)]=set(os.path.basename(x).lower() for x in (dep or [])[1::2]) if dep else set()
deleted=[]; skipped=[]
for c in cands:
    fn=c+".SLDPRT"; full=os.path.join(Z,fn); who=[k for k,s in refs.items() if fn.lower() in s]
    if fn.lower() in open_paths: app.CloseDoc(open_paths[fn.lower()].GetTitle); print("  closed",fn)
    if who: skipped.append((fn,who)); print("  SKIP referenced",fn,who); continue
    if not os.path.exists(full): skipped.append((fn,"missing")); print("  missing",fn); continue
    os.remove(full); deleted.append(fn); print("  deleted",fn)
rep["deleted"]=deleted; rep["skipped"]=skipped
# 결손 검사(모든 어셈블리)
missing={}
for p in asms:
    dep=app.GetDocumentDependencies2(p,True,False,False); m=[x for x in (dep or [])[1::2] if not os.path.exists(x)]
    if m: missing[os.path.basename(p)]=m
print("missing refs after delete:",missing); rep["missing_after"]=missing
json.dump(rep,open(os.path.join(DESK,"_검증","delete_unused_0917b.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("DONE deleted",len(deleted))
