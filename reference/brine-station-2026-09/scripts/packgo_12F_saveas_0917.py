# 12F000M61 → 12F100M61 복사·개명(옵션 ①): SaveAs 방식. 원본 파일 불변. 인스턴스 23636.
import os, sys, json, re, shutil
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
os.environ["SW_PID"]="23636"; app=connect()
FOLDER=r"Z:\29. 소방펌프차_육군\1_Modeling\2_UPPER PART\F_산소통보관함"; SRC=os.path.join(FOLDER,"12F000M61.SLDASM"); NEW=os.path.join(FOLDER,"12F100M61.SLDASM")
BK=os.path.join(os.environ["USERPROFILE"],"Documents","solidworks","sw-mcp","_backup","20260917-12F"); os.makedirs(BK,exist_ok=True)
for f in os.listdir(FOLDER):
    if f.lower().endswith((".sldasm",".sldprt")) and not f.startswith("~$"): shutil.copy2(os.path.join(FOLDER,f),os.path.join(BK,f))
print("backup ->",BK)
def deps(p):
    dep=app.GetDocumentDependencies2(p,True,False,False); return [x for x in (dep or [])[1::2]] if dep else []
old_asm_deps=[os.path.basename(x) for x in deps(SRC)]; old_200=[os.path.basename(x) for x in deps(os.path.join(FOLDER,"12F200M61.SLDASM"))]
assert not os.path.exists(NEW), NEW
# 열린 문서 확인
docs={d.GetPathName:d for d in (pv(app,"GetDocuments") or []) if d.GetPathName}
print("open:",[os.path.basename(p) for p in docs])
a=docs.get(SRC) or open_doc(app,SRC,2); app.ActivateDoc3(SRC,False,0,I4()); a=app.ActiveDoc
# 1) 어셈블리 → 12F100M61 (12F000M61 디스크 불변)
e=I4(); w=I4(); ok=a.Extension.SaveAs(NEW,0,1,NOD,e,w); print("SaveAs asm",ok,e.value,w.value); assert ok and os.path.exists(NEW)
# 2) 파트 7개 → 12F10k (열린 상위 = 12F100M61 → 참조 갱신)
for k in range(1,8):
    src=os.path.join(FOLDER,f"12F00{k}M61.SLDPRT"); dst=os.path.join(FOLDER,f"12F10{k}M61.SLDPRT"); assert not os.path.exists(dst), dst
    d=app.GetOpenDocumentByName(src) or open_doc(app,src,1); app.ActivateDoc3(src,False,0,I4()); d=app.ActiveDoc
    e=I4(); w=I4(); ok=d.Extension.SaveAs(dst,0,1,NOD,e,w); print(f"  SaveAs 12F00{k} -> 12F10{k}",ok,e.value,w.value); assert ok and os.path.exists(dst)
# 3) 새 어셈블리 저장
app.ActivateDoc3(NEW,False,0,I4()); a=app.ActiveDoc; a.ForceRebuild3(False); e=I4(); w=I4(); ok=a.Save3(1,e,w); print("Save 12F100M61",ok,e.value,w.value)
# 4) 검증
new_deps=[os.path.basename(x) for x in deps(NEW)]; print("12F100M61 deps:",new_deps)
assert all(re.match(r"12F10[1-7]M61",n,flags=re.I) or not n.upper().startswith("12F") for n in new_deps), new_deps
assert sorted(n for n in new_deps if n.upper().startswith("12F"))==[f"12F10{k}M61.SLDPRT" for k in range(1,8)], new_deps
print("12F000M61 deps(디스크):",[os.path.basename(x) for x in deps(SRC)]); assert [os.path.basename(x) for x in deps(SRC)]==old_asm_deps
print("12F200M61 deps:",[os.path.basename(x) for x in deps(os.path.join(FOLDER,"12F200M61.SLDASM"))]); assert [os.path.basename(x) for x in deps(os.path.join(FOLDER,"12F200M61.SLDASM"))]==old_200
lib=[x for x in deps(NEW) if not os.path.basename(x).upper().startswith("12F")]; print("library refs (unchanged path?):",[os.path.relpath(x,FOLDER) for x in lib])
print("folder now:",sorted(f for f in os.listdir(FOLDER) if f.lower().endswith((".sldasm",".sldprt")) and not f.startswith("~$")))
print("DONE")
