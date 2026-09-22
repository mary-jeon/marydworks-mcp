# 읽기 전용: 로봇 커버판 210003MU0의 개구(구멍) 윤곽을 월드좌표로. 로봇 모델은 열기·수정·저장 안 함(이미 스테이션에 로드된 문서만 읽음).
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
app=connect()
ST=os.path.join(Z,"S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(ST)
def walk(c,acc,depth=0):
    n=c.Name2.split("/")[-1]
    if n.split("-")[0] in ("210003MU0","210004MU0","210002MU0","211202MU1","TA2-2H-200_ROD","TA2-2H-200_BODY"): acc.append(c)
    if depth<6:
        for k in (pv(c,"GetChildren") or []): walk(k,acc,depth+1)
acc=[]; walk(s.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),acc)
out={}
for c in acc:
    n=c.Name2.split("/")[-1]; xf=xform(c); b=box(c)
    rec={"world_box":b,"xform":xf,"faces":[]}
    try:
        body=pv(c,"GetBody")
        faces=body.GetFaces() if body else []
        R=xf["R"]; t=xf["t_mm"]
        def tow(p): return [round(p[0]*R[0][i]+p[1]*R[1][i]+p[2]*R[2][i]+t[i],1) for i in range(3)]
        for fc in faces:
            sf=fc.GetSurface; bx=[v*1000 for v in fc.GetBox]
            typ="cyl r%.1f"%(sf.CylinderParams[6]*1000) if sf.IsCylinder else ("pln" if sf.IsPlane else "oth")
            lo=tow(bx[:3]); hi=tow(bx[3:]); wb=[min(a,b_) for a,b_ in zip(lo,hi)]+[max(a,b_) for a,b_ in zip(lo,hi)]
            rec["faces"].append((typ,wb,round(fc.GetArea*1e6,0)))
    except Exception as ex: rec["err"]=str(ex)
    out[n]=rec
    print("##",n,"height top",None if not b else round(1109-b[0],1),"world box",b,"faces",len(rec["faces"]),rec.get("err",""))
    # 개구 후보: 판 두께 방향(x) 이외의 작은 평면/원통 = 구멍 벽
    for f in sorted(rec["faces"],key=lambda f:-f[2])[:40]:
        print("   ",f)
json.dump(out,open(os.path.join(VER,"tank_recheck_2026-09-08","robot_opening.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
