# 읽기 전용: S20002MU0-3 바디 수·정면(z −50) 후보 면 조사
import os, sys
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
PS=os.path.join(Z,"S00000MU0.SLDASM")
app=connect(); s=app.GetOpenDocumentByName(PS); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
def find(name):
    for c in pv(scm.ActiveConfiguration.GetRootComponent3(True),"GetChildren"):
        if c.Name2==name.split("/")[0]:
            for ch in pv(c,"GetChildren"):
                if ch.Name2==name: return ch
c=find("S20000MU0-1/S20002MU0-3"); print("comp",c.Name2,"path",os.path.basename(c.GetPathName),"box",box(c))
md=c.GetModelDoc2; print("part bodies",len(list(pv(md,"GetBodies2",0,True) or [])))
try:
    bs=pv(c,"GetBodies3",0,VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)); print("GetBodies3 ->",len(list(bs or [])))
except Exception as ex: print("GetBodies3 exc",ex); bs=None
b=c.GetBody; print("GetBody faces",len(list(b.GetFaces())))
for bi,bb in enumerate(list(bs or [b])):
    for fc in bb.GetFaces():
        sf=fc.GetSurface; fb=[round(v*1000,1) for v in fc.GetBox]
        if abs(fb[2]+50)<1 and abs(fb[5]+50)<1:
            print(f"  body{bi} plane={sf.IsPlane} n={[round(v,3) for v in pv(fc,'Normal')] if sf.IsPlane else '-'} box={fb} area={round(fc.GetArea*1e6)}")
# 좌표 선택 시험
s.ClearSelection2(True); ok=s.Extension.SelectByID2("","FACE",-0.5,-0.8125,-0.05,False,1,NOD,0); print("SelectByID2 point",ok)
if ok:
    sm=s.SelectionManager; o=sm.GetSelectedObject6(1,-1); comp=sm.GetSelectedObjectsComponent4(1,-1)
    print("  selected comp",comp.Name2 if comp else None,"face box",[round(v*1000,1) for v in o.GetBox],"n",[round(v,3) for v in pv(o,"Normal")])
s.ClearSelection2(True)
