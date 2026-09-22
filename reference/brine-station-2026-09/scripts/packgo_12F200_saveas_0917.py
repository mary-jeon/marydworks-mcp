# 12F200M61이 참조하는 공유 파트 12F002·004·005·006·007 → 12F202·204·205·206·207 복사(SaveAs, 열린 상위 12F200M61만 참조 갱신). 원본·12F000M61·12F100M61 불변. 인스턴스 23636.
import os, sys, json, re, shutil
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
os.environ["SW_PID"]="23636"; app=connect()
FOLDER=r"Z:\29. 소방펌프차_육군\1_Modeling\2_UPPER PART\F_산소통보관함"; A200=os.path.join(FOLDER,"12F200M61.SLDASM")
BK=os.path.join(os.environ["USERPROFILE"],"Documents","solidworks","sw-mcp","_backup","20260917-12F200"); os.makedirs(BK,exist_ok=True)
for f in os.listdir(FOLDER):
    if f.lower().endswith((".sldasm",".sldprt")) and not f.startswith("~$"): shutil.copy2(os.path.join(FOLDER,f),os.path.join(BK,f))
print("backup ->",BK)
def deps(p):
    dep=app.GetDocumentDependencies2(p,True,False,False); return [x for x in (dep or [])[1::2]] if dep else []
docs={d.GetPathName:d for d in (pv(app,"GetDocuments") or []) if d.GetPathName}
print("open:",[os.path.basename(p) for p in docs])
# 안전: 12F000M61·120000M61·900000M61이 열려 있으면 안 됨(그 참조까지 바뀌므로)
bad=[os.path.basename(p) for p in docs if os.path.basename(p).upper() in ("12F000M61.SLDASM","120000M61.SLDASM","900000M61.SLDASM")]
assert not bad, ("close first:",bad)
a=docs.get(A200) or open_doc(app,A200,2); app.ActivateDoc3(A200,False,0,I4()); a=app.ActiveDoc; print("active",a.GetTitle)
before=[os.path.basename(x) for x in deps(A200)]; print("12F200M61 deps before:",before)
MAP={2:"12F202M61",4:"12F204M61",5:"12F205M61",6:"12F206M61",7:"12F207M61"}
for k,newn in MAP.items():
    src=os.path.join(FOLDER,f"12F00{k}M61.SLDPRT"); dst=os.path.join(FOLDER,newn+".SLDPRT"); assert not os.path.exists(dst), dst
    d=app.GetOpenDocumentByName(src) or open_doc(app,src,1); app.ActivateDoc3(src,False,0,I4()); d=app.ActiveDoc
    e=I4(); w=I4(); ok=d.Extension.SaveAs(dst,0,1,NOD,e,w); print(f"  SaveAs 12F00{k} -> {newn}",ok,e.value,w.value); assert ok and os.path.exists(dst)
app.ActivateDoc3(A200,False,0,I4()); a=app.ActiveDoc; a.ForceRebuild3(False); e=I4(); w=I4(); ok=a.Save3(1,e,w); print("Save 12F200M61",ok,e.value,w.value)
after=[os.path.basename(x) for x in deps(A200)]; print("12F200M61 deps after:",after)
assert not any(re.match(r"12F00[1-7]M61",n,flags=re.I) for n in after), after
for asm in ("12F000M61.SLDASM","12F100M61.SLDASM"):
    print(asm,"deps:",[os.path.basename(x) for x in deps(os.path.join(FOLDER,asm))])
for asm in (os.path.join(os.path.dirname(FOLDER),"120000M61.SLDASM"),os.path.join(os.path.dirname(os.path.dirname(FOLDER)),"0_Assembly","900000M61.SLDASM")):
    dep=app.GetDocumentDependencies2(asm,True,False,False); refs=[os.path.basename(x) for x in (dep or [])[1::2] if os.path.basename(x).upper().startswith("12F")] if dep else None; print(os.path.basename(asm),"12F refs:",sorted(set(refs)) if refs else refs)
print("folder now:",sorted(f for f in os.listdir(FOLDER) if f.lower().endswith((".sldasm",".sldprt")) and not f.startswith("~$")))
print("DONE")
