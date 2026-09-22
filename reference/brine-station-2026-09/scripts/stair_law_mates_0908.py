"""09-08 저녁: 설계 전 확인 — S20000MU0 안 S20004/S20005/S20002 메이트·고정 여부, S20005 스케치 평면 위치,
S20000MU0-1 / S10000MU0-1 변환(로컬↔월드), S10006 데크 바닥판 립 형상, S20004 스케치3 치수 이름."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
stop=watchdog(); app=connect()
OUT=r"<PROJECT_DIR>\_검증\stair_law_0908"
A=os.path.join(Z,"S00000MU0.SLDASM"); top=app.GetOpenDocumentByName(A)
root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
res={}
for ch in (pv(root,"GetChildren") or []):
    n=ch.Name2.split("/")[-1]
    if n.startswith(("S20000","S10000","S30000")):
        res[n+"_xform"]=xform(ch); print(n,"xform",xform(ch),"fixed",pv(ch,"IsFixed"))
# S20000MU0 서브어셈블리 문서
S2=os.path.join(Z,"S20000MU0.SLDASM"); a2=app.GetOpenDocumentByName(S2)
r2=a2.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
comps={c.Name2.split("/")[-1]:c for c in (pv(r2,"GetChildren") or [])}
print("S20000 comps fixed:",{n:pv(c,"IsFixed") for n,c in comps.items() if n.startswith(("S20004","S20005","S20002","S20006","S20001"))})
# 메이트 목록
mates=[]; f=pv(a2,"FirstFeature")
while f is not None:
    ty=pv(f,"GetTypeName2")
    if ty=="MateGroup":
        sub=pv(f,"GetFirstSubFeature")
        while sub is not None:
            m=sub.GetSpecificFeature2
            try:
                ents=[]
                for i in range(m.GetMateEntityCount):
                    me=m.MateEntity(i); ents.append(me.ReferenceComponent.Name2.split("/")[-1]+":"+str(me.ReferenceType2))
                mates.append((sub.Name,m.Type,ents))
            except Exception as ex: mates.append((sub.Name,"?",str(ex)))
            sub=pv(sub,"GetNextSubFeature")
    f=pv(f,"GetNextFeature")
sel=[m for m in mates if any(e.startswith(("S20004","S20005")) for e in (m[2] if isinstance(m[2],list) else []))]
print("mates total",len(mates),"involving S20004/S20005:",len(sel))
for m in sel: print("  ",m)
res["mates_S20004_5"]=sel
# S20005 파트: 스케치1 평면 위치 vs 바디 박스, 보스-돌출1 깊이 치수 이름
d5=comps["S20005MU0-1"].GetModelDoc2
print("S20005 part box",[round(v*1000,1) for v in pv(d5,"GetPartBox",True)])
f=pv(d5,"FirstFeature")
while f is not None:
    ty=pv(f,"GetTypeName2")
    if ty in ("Extrusion","ICE","ProfileFeature"):
        dd=pv(f,"GetFirstDisplayDimension"); dims=[]
        while dd is not None:
            dm=dd.GetDimension2(0); dims.append((dm.FullName,round(dm.SystemValue*1000,3))); dd=pv(f,"GetNextDisplayDimension",dd)
        print("  S20005",f.Name,ty,dims)
        if ty=="ProfileFeature":
            sk=f.GetSpecificFeature2
            try:
                pl=pv(sk,"ModelToSketchTransform"); a=list(pl.ArrayData); print("    sketch->model t",[round(v*1000,1) for v in a[9:12]],"R",[round(v,3) for v in a[0:9]])
            except Exception as ex: print("    xf err",ex)
    f=pv(f,"GetNextFeature")
# S20004 스케치3 치수
d4=comps["S20004MU0-7"].GetModelDoc2
f=pv(d4,"FirstFeature")
while f is not None:
    ty=pv(f,"GetTypeName2")
    if ty in ("ProfileFeature","Sweep"):
        dd=pv(f,"GetFirstDisplayDimension"); dims=[]
        while dd is not None:
            dm=dd.GetDimension2(0); dims.append((dm.FullName,round(dm.SystemValue*1000,3))); dd=pv(f,"GetNextDisplayDimension",dd)
        print("  S20004",f.Name,ty,dims)
        if f.Name=="스케치3":
            sk=f.GetSpecificFeature2; pl=pv(sk,"ModelToSketchTransform"); a=list(pl.ArrayData); print("    sketch xf t",[round(v*1000,1) for v in a[9:12]],"R",[round(v,3) for v in a[0:9]])
    f=pv(f,"GetNextFeature")
print("S20004 part box",[round(v*1000,1) for v in pv(d4,"GetPartBox",True)])
# S10000: 데크 바닥판 S10006 형상(평면 목록), 고정 여부
S1=os.path.join(Z,"S10000MU0.SLDASM"); a1=app.GetOpenDocumentByName(S1)
r1=a1.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
c1={c.Name2.split("/")[-1]:c for c in (pv(r1,"GetChildren") or [])}
print("S10000 fixed:",{n:pv(c,"IsFixed") for n,c in c1.items() if n.startswith(("S10006","S10007","S10002","S10009"))})
d6=c1["S10006MU0-2"].GetModelDoc2; b=(pv(d6,"GetBodies2",0,True) or [])[0]
pls=[]
for fc in (pv(b,"GetFaces") or []):
    s=fc.GetSurface
    if s.IsPlane and fc.GetArea*1e6>5000: pls.append((round(fc.GetArea*1e6),[round(v,2) for v in fc.Normal],[round(v*1000,1) for v in fc.GetBox]))
pls.sort(reverse=True); print("S10006 planes (part coords):",pls[:12]); print("S10006 xform",xform(c1["S10006MU0-2"]))
print("S10002-2 xform",xform(c1["S10002MU0-2"]),"S10007-4",xform(c1["S10007MU0-4"]),"S10007-5",xform(c1["S10007MU0-5"]))
json.dump(res,open(os.path.join(OUT,"mates.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set()
