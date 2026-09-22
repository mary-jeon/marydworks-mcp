# 읽기 전용(파트 표시 구성만 잠시 전환 후 복원): B9b 상승 구성에서 r14.5 외통·r10.9 로드·아이 면의 z 범위 → 어셈 z = -193.5 + z_part
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
d=app.GetOpenDocumentByName(os.path.join(Z,"B9b_LINAK_LA25_900N_150st_24V.SLDPRT"))
cur=d.ConfigurationManager.ActiveConfiguration.Name; print("part cfg was",cur)
d.ShowConfiguration2("상승"); d.EditRebuild3
rows=[]
for body in (pv(d,"GetBodies2",0,True) or []):
    for fc in body.GetFaces():
        s=fc.GetSurface
        if not s.IsCylinder: continue
        r=s.CylinderParams[6]*1000
        if abs(r-14.5)<0.2 or abs(r-10.9)<0.2 or abs(r-7.5)<0.1:
            bx=[round(v*1000,2) for v in fc.GetBox]; rows.append((round(r,2),bx,[round(-193.5+bx[2],1),round(-193.5+bx[5],1)]))
d.ShowConfiguration2(cur); d.EditRebuild3
for r in sorted(rows,key=lambda r:r[1][2]): print(" r",r[0],"part box",r[1],"asm z",r[2])
