# 읽기 전용: 탱크 안 라인 배치 변환으로 J1b 볼트구멍(라인좌표 ±55,±25)을 탱크좌표로 옮겨 S30015 탭(파트좌표 X±55,Z±25)과 대조. 화면 활성 문서 안 바꿈.
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
TANK=os.path.join(Z,"S30000MU0.SLDASM")
t=app.GetOpenDocumentByName(TANK)
if t is None: raise SystemExit("S30000MU0 not open")
cm=t.ConfigurationManager; print("tank active cfg:",cm.ActiveConfiguration.Name)
root=cm.ActiveConfiguration.GetRootComponent3(True)
kids={c.Name2.split("/")[-1]:c for c in pv(root,"GetChildren")}
def apply(xf,p):
    R=xf["R"]; tt=xf["t_mm"]
    # SolidWorks ArrayData: row-vector convention p' = p·R + t
    return [round(p[0]*R[0][i]+p[1]*R[1][i]+p[2]*R[2][i]+tt[i],1) for i in range(3)]
line=[c for n,c in kids.items() if n.startswith("염수주입라인")][0]
lx=xform(line); print("line xform:",json.dumps(lx))
J1B=[(55,25,0),(-55,25,0),(55,-25,0),(-55,-25,0)]
print("J1b holes -> tank coords:",[apply(lx,p) for p in J1B])
for pre in ("S30015","S30016"):
    c=[c for n,c in kids.items() if n.startswith(pre)][0]; fx=xform(c)
    print(pre,"xform:",json.dumps(fx))
    print(pre,"holes(part X±55,Z±25) -> tank:",[apply(fx,p) for p in [(55,-6,25),(-55,-6,25),(55,-6,-25),(-55,-6,-25)]])
# 라인 안 LA25·가이드봉·소켓 위치(라인좌표) 재확인
lroot=line
sub={c.Name2.split("/")[-1]:c for c in pv(line,"GetChildren")}
for k in ("B9b","J2_","G13","B4_","G3_","J5c","J8b","J9_"):
    for n,c in sub.items():
        if n.startswith(k) and c.GetSuppression2!=0:
            print("  ",n,"box(world of tank?)",box(c))
