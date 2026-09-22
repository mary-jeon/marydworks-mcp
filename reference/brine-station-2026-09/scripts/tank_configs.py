import sys, pythoncom, win32com.client as w
from win32com.client import VARIANT
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
pythoncom.CoInitialize()
ctx=pythoncom.CreateBindCtx(0); rot=pythoncom.GetRunningObjectTable()
for mk in rot:
    if "SolidWorks_PID_25956" in mk.GetDisplayName(ctx,None):
        app=w.Dispatch(rot.GetObject(mk).QueryInterface(pythoncom.IID_IDispatch)); break
I4=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_I4,0)
LINE=r"<PROJECT_DIR>\염수주입라인.SLDASM"
TANK=r"<CAD_DIR>\S30000MU0.SLDASM"
# 1) line: rename configs 기본->상승, 최대하강->하강
line=app.ActivateDoc3(LINE,False,0,I4()); line=app.ActiveDoc
names=list(line.GetConfigurationNames); print("line configs:", names)
if "상승" not in names:
    c=line.GetConfigurationByName("기본"); c.Name="상승"; c.Description="최대상승 (후퇴, 로봇 통과)"
if "하강" not in names and "최대하강" in names:
    c=line.GetConfigurationByName("최대하강"); c.Name="하강"; c.Description="최대하강 (슬리브 140 하강)"
line.ShowConfiguration2("상승"); line.EditRebuild3
print("line configs now:", list(line.GetConfigurationNames), "active:", line.ConfigurationManager.ActiveConfiguration.Name)
# 2) tank: configs 상승/하강 (기본 stays = 상승)
tank=app.ActivateDoc3(TANK,False,0,I4()); tank=app.ActiveDoc
tn=list(tank.GetConfigurationNames); print("tank configs:", tn)
def comp():
    r=tank.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    return [c for c in r.GetChildren if c.Name2.split("/")[-1].startswith("염수주입라인")][0]
tank.ShowConfiguration2("기본"); c=comp(); c.ReferencedConfiguration="상승"; tank.EditRebuild3
print("기본 -> line ref:", comp().ReferencedConfiguration)
for nm,ref,desc in (("상승","상승","주입라인 최대상승(후퇴)"),("하강","하강","주입라인 최대하강(개구 삽입)")):
    if nm not in tn:
        tank.ShowConfiguration2("기본")
        r=tank.AddConfiguration3(nm,desc,"",0); print("added tank config",nm,r is not None)
    tank.ShowConfiguration2(nm); c=comp(); c.ReferencedConfiguration=ref; tank.EditRebuild3
    print(f"{nm} -> line ref:", comp().ReferencedConfiguration)
# verify isolation
for nm in ("기본","상승","하강"):
    tank.ShowConfiguration2(nm); tank.EditRebuild3; print("verify",nm,"->",comp().ReferencedConfiguration)
tank.ShowConfiguration2("기본"); tank.EditRebuild3
print("tank configs now:", list(tank.GetConfigurationNames))
