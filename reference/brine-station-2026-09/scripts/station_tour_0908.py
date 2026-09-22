# 읽기 전용: 스테이션 S00000MU0 직계·S20000(계단)·S30000(탱크) 하위 컴포넌트 이름/월드박스/지상고. 로봇 트리는 건너뜀.
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect(); s=app.GetOpenDocumentByName(os.path.join(Z,"S00000MU0.SLDASM"))
print("station cfg",s.ConfigurationManager.ActiveConfiguration.Name)
rows=[]
def walk(c,depth,path):
    n=c.Name2.split("/")[-1]
    if n.startswith("900000MU1"): return
    b=box(c)
    if b: rows.append((depth,path+"/"+n,c.GetSuppression2,b,round(1109-b[3],1),round(1109-b[0],1)))
    if depth<3:
        for k in (pv(c,"GetChildren") or []): walk(k,depth+1,path+"/"+n)
for k in pv(s.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren"): walk(k,0,"")
json.dump(rows,open(os.path.join(VER,"tank_recheck_2026-09-08","station_tour.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
for d,p,sup,b,zlo,zhi in rows:
    if d<=1 or "S30006" in p or "S30007" in p or "S30008" in p or "S30009" in p or "S3001" in p or "S2000" in p:
        print(f"{'  '*d}{p.split('/')[-1]:40s} supp{sup} 지상고 {zlo:7.1f}~{zhi:7.1f}  y {b[1]:7.1f}~{b[4]:7.1f}  z {b[2]:8.1f}~{b[5]:8.1f}")
