import sys, os, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
NOD=VARIANT(pythoncom.VT_DISPATCH,None); I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
NAT=r"<PROJECT_DIR>\_native"
ASM=r"<PROJECT_DIR>\염수주입라인.SLDASM"
asm=app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc; name=asm.GetTitle.replace(".SLDASM","")
cm=asm.ConfigurationManager
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def box(c):
    b=c.GetBox(False,False); return [round(v*1000,2) for v in b] if b else None
def set_arr(c,a):
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,a); c.Transform2=xf
def sel(names, append=False):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
MOVING=("B7_sleeve","B5c_moving_plate","B10_linear_bushing")
print("show 기본:", asm.ShowConfiguration2("기본"), cm.ActiveConfiguration.Name)
raised=[]; lowered_T={}
for c in root().GetChildren:
    if c.Name2.startswith(MOVING) and not c.Name2.endswith(("-3","-4")):
        a=list(c.Transform2.ArrayData)
        if a[11] < -0.2 or (c.Name2.startswith("B5c") and a[11] < -0.13):   # currently lowered -> raise
            a[11]+=0.140
        lowered=list(a); lowered[11]-=0.140; lowered_T[c.Name2]=lowered
        set_arr(c,a); raised.append(c.Name2)
asm.EditRebuild3
print("raised set:"); [print(f"  {c.Name2:44s} {box(c)}") for c in root().GetChildren if c.Name2 in raised]
# duplicates at lowered position
dups=[]
for n,a in lowered_T.items():
    fn=n.rsplit("-",1)[0]+".SLDPRT"
    c=asm.AddComponent5(os.path.join(NAT,fn),0,"",False,"",a[9],a[10],a[11])
    asm.ClearSelection2(True); asm.Extension.SelectByID2(c.Name2+"@"+name,"COMPONENT",0,0,0,False,0,NOD,0); asm.UnfixComponent(); asm.ClearSelection2(True)
    set_arr(c,a); dups.append(c.Name2)
asm.EditRebuild3
print("lowered duplicates:"); [print(f"  {c.Name2:44s} {box(c)}") for c in root().GetChildren if c.Name2 in dups]
rodext=[c.Name2 for c in root().GetChildren if c.Name2.startswith("B12_")]
# 기본: suppress lowered dups + rod ext
sel(dups+rodext); r=asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
print("기본 suppression:", {c.Name2:c.GetSuppression2 for c in root().GetChildren if c.Name2 in dups+rodext+raised})
# 최대하강: suppress raised originals
print("show 최대하강:", asm.ShowConfiguration2("최대하강"), cm.ActiveConfiguration.Name)
sel(raised); r=asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
print("최대하강 suppression:", {c.Name2:c.GetSuppression2 for c in root().GetChildren if c.Name2 in dups+rodext+raised})
print("최대하강 boxes:"); [print(f"  {c.Name2:44s} {box(c)}") for c in root().GetChildren if c.Name2 in dups+rodext]
asm.ShowConfiguration2("기본"); asm.EditRebuild3
print("back 기본 suppression:", {c.Name2:c.GetSuppression2 for c in root().GetChildren if c.Name2 in dups+rodext+raised})
