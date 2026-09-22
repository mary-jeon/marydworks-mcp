# 사용자 승인(09-15) 후 미참조 파일 삭제: 열린 문서 닫기 → 참조 재검사 → 삭제 → 어셈블리 종속성에 결손 없음 확인
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect()
lst=[l.strip() for l in open(sys.argv[1],encoding="utf-8") if l.strip()]
asms=[os.path.join(Z,f) for f in os.listdir(Z) if f.lower().endswith(".sldasm") and not f.startswith("~$")]
def refset():
    s=set()
    for a in asms:
        dep=app.GetDocumentDependencies2(a,True,False,False)
        if dep: s|=set(os.path.basename(x).lower() for x in dep[1::2])
    return s
refs=refset(); protect=[c for c in lst if (c+".sldprt").lower() in refs]
assert not protect, ("still referenced",protect)
# 열린 문서 닫기
for x in list(pv(app,"GetDocuments") or []):
    try: pn=x.GetPathName; tt=x.GetTitle
    except Exception: continue
    if os.path.basename(pn).replace(".SLDPRT","") in lst: app.CloseDoc(tt); print("closed",tt)
deleted=[]; failed=[]
for c in lst:
    p=os.path.join(Z,c+".SLDPRT")
    if not os.path.exists(p): continue
    try: os.remove(p); deleted.append(c)
    except Exception as ex: failed.append((c,str(ex)))
print("deleted",len(deleted),"failed",failed)
# 어셈블리 종속성 결손 확인(파일 존재 여부)
missing=[]
for a in asms:
    dep=app.GetDocumentDependencies2(a,True,False,False)
    for x in (dep[1::2] if dep else []):
        if not os.path.exists(x): missing.append((os.path.basename(a),os.path.basename(x)))
print("missing refs after delete:",missing)
json.dump({"deleted":deleted,"failed":failed,"missing":missing},open(r"<PROJECT_DIR>\_검증\delete_unused_0915.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
