import sys, os, json, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
NOD=VARIANT(pythoncom.VT_DISPATCH,None); I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
Z=r"<CAD_DIR>"
ASM=os.path.join(Z,"염수주입라인.SLDASM")
asm=app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc; name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
asm.ShowConfiguration2("상승")
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def box(c):
    b=c.GetBox(False,False); return [round(v*1000,1) for v in b] if b else None
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
def add(fn,R,t):
    p=os.path.join(Z,fn)
    if not any(((d.GetPathName or "").lower()==p.lower()) for d in (app.GetDocuments or [])):
        e=I4(); wn=I4(); app.OpenDoc6(p,1,1,"",e,wn); app.ActivateDoc3(ASM,False,0,I4())
    c=asm.AddComponent5(p,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    asm.ClearSelection2(True); asm.Extension.SelectByID2(c.Name2+"@"+name,"COMPONENT",0,0,0,False,0,NOD,0); asm.UnfixComponent(); asm.ClearSelection2(True)
    set_T(c,R,t); return c
I=[[1,0,0],[0,1,0],[0,0,1]]
# delete gooseneck + moving-side fittings (all configs share components)
kill=[c.Name2 for c in root().GetChildren if c.Name2.startswith(("G_elbow","G15_pipe","G16_hose","G19_hose","G17_nozzle")) or c.Name2.startswith("G13_weld_socket") and not c.Name2.endswith("-1")]
sel(kill); asm.Extension.DeleteSelection2(0); asm.ClearSelection2(True); print("deleted",len(kill))
VB=-118.0
hn=add("G16_hose_nipple_3-4in_L55.SLDPRT",I,(0,0,VB)); print("hose nipple",box(hn))
hs=add("G19b_hose_3-4in_L167.SLDPRT",I,(0,0,VB-55)); print("hose",box(hs))
su=add("G7_sleeve_32A_Sch10S_L115.SLDPRT",I,(0,0,-230)); sd=add("G7_sleeve_32A_Sch10S_L115.SLDPRT",I,(0,0,-370))
asm.EditRebuild3; print("sleeve up",box(su),"dn",box(sd))
sel([sd.Name2]); asm.EditSuppress2; asm.ClearSelection2(True)
asm.ShowConfiguration2("하강"); asm.EditRebuild3; sel([su.Name2]); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
print("하강 sleeves:", {c.Name2:c.GetSuppression2 for c in root().GetChildren if c.Name2.startswith("G7_")})
asm.ShowConfiguration2("상승"); asm.EditRebuild3
final=[{"comp":c.Name2,"box_mm":box(c),"supp":c.GetSuppression2} for c in root().GetChildren]
for r in final: print(f"  {r['comp']:44s} {r['box_mm']} supp={r['supp']}")
json.dump({"components":final},open(r"<PROJECT_DIR>\_검증\G_rebuild_boxes.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
# close & remove superseded part files (mine)
for d in list(app.GetDocuments):
    try: t=d.GetTitle
    except Exception: continue
    if t.startswith(("G_elbow","G15_pipe","G19_hose_3-4in_diag","G19_hose_3-4in_end","G17_nozzle")): app.CloseDoc(t)
for f in os.listdir(Z):
    if f.startswith(("G_elbow","G15_pipe","G19_hose_3-4in_diag","G19_hose_3-4in_end","G17_nozzle")) and f.lower().endswith(".sldprt"):
        try: os.remove(os.path.join(Z,f)); print("removed",f)
        except Exception as ex: print("could not remove",f)
