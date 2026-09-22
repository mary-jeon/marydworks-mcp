# 읽기 전용: S00000MU0 활성 구성·dirty 여부, 로봇 뚜껑 관련 컴포넌트 위치(지상고 = 1109 − world x)
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
PS=os.path.join(Z,"S00000MU0.SLDASM")
app=connect(); s=app.GetOpenDocumentByName(PS); assert s is not None, "S00000MU0 not open"
app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
print("active cfg",scm.ActiveConfiguration.Name,"dirty",s.GetSaveFlag,"cfgs",list(pv(s,"GetConfigurationNames")))
def gl(b): return None if b is None else {"지상고":[round(1109-b[3],1),round(1109-b[0],1)],"y":[b[1],b[4]],"z":[b[2],b[5]]}
out=[]
def walk(c,depth):
    for ch in (pv(c,"GetChildren") or []):
        out.append((ch.Name2,ch))
        if depth<6: walk(ch,depth+1)
walk(scm.ActiveConfiguration.GetRootComponent3(True),0)
KEY=("TA2-2H-200","212003","212001","210004","210000MU1","212000MU1","B9h","G13f","G13g","J5l")
for n,c in out:
    base=n.split("/")[-1]
    if base.startswith(KEY) and c.GetSuppression2==2: print(f"  {n[:70]:70s} {gl(box(c))}")
