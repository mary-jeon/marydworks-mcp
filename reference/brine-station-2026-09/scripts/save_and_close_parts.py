# Save every dirty document under the station folder (never the robot 900000MU1 tree), then close part windows leaving assemblies.
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect(); stop=watchdog()
zl=Z.lower()
saved=[]; failed=[]; skipped=[]
for d in list(app.GetDocuments):
    try: p=d.GetPathName; t=d.GetTitle
    except Exception: continue
    if not p: skipped.append((t,"no path")); continue
    if not p.lower().startswith(zl):
        if pv(d,"GetSaveFlag"): skipped.append((t,"outside station folder"))
        continue
    if not pv(d,"GetSaveFlag"): continue
    if pv(d,"IsOpenedReadOnly"): skipped.append((t,"read-only")); continue
    e=I4(); w_=I4()
    ok=d.Save3(1,e,w_)   # swSaveAsOptions_Silent
    (saved if ok else failed).append((t,e.value,w_.value))
print("saved",len(saved)); [print("  ",s) for s in saved]
print("failed",failed); print("skipped",skipped)
# close part windows (keep assemblies)
fr=app.Frame(); closed=[]; kept=[]
wins=pv(fr,"ModelWindows") or []
for mw in wins:
    md=mw.ModelDoc; t=md.GetTitle; typ=md.GetType   # 1 part, 2 assembly, 3 drawing
    if typ==1:
        if pv(md,"GetSaveFlag"): kept.append((t,"still dirty - not closed")); continue
        app.CloseDoc(t); closed.append(t)
    else: kept.append((t,"assembly" if typ==2 else "drawing"))
print("closed part windows:",closed); print("kept windows:",kept)
still=[d.GetTitle for d in app.GetDocuments if pv(d,"GetSaveFlag") and d.GetPathName.lower().startswith(zl)]
print("still dirty under station folder:",still)
json.dump({"saved":saved,"failed":failed,"skipped":skipped,"closed":closed,"kept":kept,"still_dirty":still},open(os.path.join(VER,"S30000MU0_review","save_close.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set()
