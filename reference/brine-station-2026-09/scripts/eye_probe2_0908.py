# 읽기 전용: B9b(상승 구성) 파트좌표 z -190..-140 (어셈 -383..-333 = 클레비스 구간) 면 목록 — 어느 형상이 클레비스 다리(|y| 15~22)에 닿는지
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
d=app.GetOpenDocumentByName(os.path.join(Z,"B9b_LINAK_LA25_900N_150st_24V.SLDPRT")); print("cfg",d.ConfigurationManager.ActiveConfiguration.Name)
rows=[]
for body in (pv(d,"GetBodies2",0,True) or []):
    for fc in body.GetFaces():
        bx=fc.GetBox
        if bx[5]*1000< -192 or bx[2]*1000> -138: continue
        s=fc.GetSurface; bxm=[round(v*1000,2) for v in bx]
        typ=("cyl r%.2f"%(s.CylinderParams[6]*1000)) if s.IsCylinder else ("pln" if s.IsPlane else ("sph" if s.IsSphere else ("tor" if s.IsTorus else "oth")))
        rows.append((typ,bxm))
print("faces in window:",len(rows))
for r in sorted(rows,key=lambda r:(max(abs(r[1][1]),abs(r[1][4])))): print(" ",r)
