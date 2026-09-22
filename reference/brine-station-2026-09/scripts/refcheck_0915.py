# 읽기 전용: Station 폴더의 모든 .SLDASM(디스크)의 종속 파일 집합 → 후보 파일이 어디에도 참조되지 않는지 확인
import os, sys
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
app=connect()
asms=[os.path.join(Z,f) for f in os.listdir(Z) if f.lower().endswith(".sldasm") and not f.startswith("~$")]
refs={}
for a in asms:
    try:
        dep=app.GetDocumentDependencies2(a,True,False,False)   # traverse, no search, no add read-only
        names=[os.path.basename(x).lower() for x in (dep or [])[1::2]] if dep else []
    except Exception as ex: names=[]; print("dep exc",os.path.basename(a),ex)
    refs[os.path.basename(a)]=set(names)
allref=set().union(*refs.values())
cands=[l.strip() for l in open(sys.argv[1],encoding="utf-8") if l.strip()]
print("assemblies",len(asms),"total referenced files",len(allref))
for c in cands:
    fn=(c+".SLDPRT").lower(); who=[a for a,s in refs.items() if fn in s]
    print(("USED  " if who else "free  ")+c, who)
