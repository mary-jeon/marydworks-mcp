# 읽기 전용: B9b 로드 아이 주변 면(원통·구·평면) y 범위 — 클레비스 내측 폭 결정용. 라인좌표(상승 구성).
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
asm=app.GetOpenDocumentByName(ASM)
root=asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
b9=[c for c in pv(root,"GetChildren") if c.Name2.startswith("B9b_")][0]
print("cfg",asm.ConfigurationManager.ActiveConfiguration.Name,"B9b box",box(b9))
rows=[]
for body in (pv(b9,"GetBody") and [pv(b9,"GetBody")] or []):
    pass
bodies=pv(b9,"GetBodies3",0,None) or []
for body in bodies:
    for fc in body.GetFaces():
        bx=[round(v*1000,2) for v in fc.GetBox]
        # 아이 근처: z -372..-338, y 280..320 (파트→어셈 변환 전 좌표일 수 있어 두 후보 다 봄)
        s=fc.GetSurface
        typ="cyl" if s.IsCylinder else ("sph" if s.IsSphere else ("pln" if s.IsPlane else ("tor" if s.IsTorus else "other")))
        rows.append((typ,bx))
# 어셈 좌표로 변환: comp.Transform2 적용 여부는 GetBox 결과가 파트좌표인지 확인 → 박스 범위로 판단
import math
def near(bx,lo,hi): return bx[2]>=lo-1 and bx[5]<=hi+1
cand=[r for r in rows if (r[1][2]>=-375 and r[1][5]<=-335) or (r[1][2]>=-190 and r[1][5]<=-150)]
print("faces near eye (z window):",len(cand))
for r in sorted(cand,key=lambda r:(r[1][1],r[1][4]))[:60]: print(" ",r)
print("all y-extremes:",min(r[1][1] for r in rows),max(r[1][4] for r in rows))
