"""09-08 저녁: 난간 파이프(S20004 상부 난간대, S20005 지주)의 모든 바깥 원통면 축을 월드로 뽑고(굽힘 파이프 대응),
피처 트리·경로 스케치 세그먼트를 덤프. 측면도 재작성."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
stop=watchdog(); app=connect()
OUT=r"<PROJECT_DIR>\_검증\stair_law_0908"
A=os.path.join(Z,"S00000MU0.SLDASM"); asm=app.GetOpenDocumentByName(A)
cm=asm.ConfigurationManager; root=cm.ActiveConfiguration.GetRootComponent3(True)
def find(c,pref,out):
    for ch in (pv(c,"GetChildren") or []):
        n=ch.Name2.split("/")[-1]
        if n.startswith(pref): out.append(ch)
        find(ch,pref,out)
    return out
def RT(c):
    a=list(c.Transform2.ArrayData); return [a[0:3],a[3:6],a[6:9]],a[9:12]
def world(R,t,p): return [sum(p[i]*R[i][j] for i in range(3))*1000+t[j]*1000 for j in range(3)]
def worldv(R,v): return [sum(v[i]*R[i][j] for i in range(3)) for j in range(3)]
SKIP=("RefPlane","OriginProfileFeature","MaterialFolder","CommentsFolder","FavoriteFolder","HistoryFolder","SelectionSetFolder","SensorFolder","DocsFolder","DetailCabinet","InkMarkupFolder","SurfaceBodyFolder","SolidBodyFolder","EnvFolder","EqnFolder","CutListFolder")
out={}
done_docs=set()
for pref in ("S20004","S20005","S20002","S20003"):
    for c in find(root,pref,[]):
        n=c.Name2.split("/")[-1]; md=c.GetModelDoc2; R,t=RT(c)
        # 루트 컴포넌트가 아니라 S20000 내부 것만 (Transform2가 월드 기준인지 확인: 박스와 대조)
        segs=[]
        b=(pv(md,"GetBodies2",0,True) or [])[0]
        for f in (pv(b,"GetFaces") or []):
            s=f.GetSurface
            if s.IsCylinder:
                cp=s.CylinderParams; r=cp[6]*1000
                if r<15: continue
                o=world(R,t,cp[0:3]); d=worldv(R,cp[3:6])
                fb=[v for v in f.GetBox]; corners=[[fb[i],fb[j],fb[k]] for i in (0,3) for j in (1,4) for k in (2,5)]
                ws=[world(R,t,q) for q in corners]
                ts=[sum((q[m]-o[m])*d[m] for m in range(3)) for q in ws]
                P0=[round(o[m]+d[m]*min(ts),1) for m in range(3)]; P1=[round(o[m]+d[m]*max(ts),1) for m in range(3)]
                segs.append({"r":round(r,2),"P0":P0,"P1":P1,"L":round(max(ts)-min(ts),1),"area":round(f.GetArea*1e6)})
        out[n]={"box":box(c),"segs":segs}
        if pref in ("S20004","S20005") and md.GetPathName not in done_docs:
            done_docs.add(md.GetPathName); fl=[]; f=pv(md,"FirstFeature")
            while f is not None:
                ty=pv(f,"GetTypeName2")
                if ty not in SKIP:
                    row=[f.Name,ty]
                    if ty=="ProfileFeature":
                        sk=f.GetSpecificFeature2; ss=[]
                        for sg in (pv(sk,"GetSketchSegments") or []):
                            if pv(sg,"GetType")==0:
                                a=pv(sg,"GetStartPoint2"); bq=pv(sg,"GetEndPoint2"); ss.append(("line",[round(a.X*1000,1),round(a.Y*1000,1),round(a.Z*1000,1)],[round(bq.X*1000,1),round(bq.Y*1000,1),round(bq.Z*1000,1)]))
                            elif pv(sg,"GetType")==1:
                                ss.append(("arc",round(sg.GetRadius*1000,1)))
                            else: ss.append((pv(sg,"GetType"),))
                        row.append(ss)
                    fl.append(row)
                f=pv(f,"GetNextFeature")
            out[n]["features"]=fl
        print(n,"segs:",[(s["r"],s["P0"],s["P1"],s["L"]) for s in segs if s["L"]>30])
        if "features" in out[n]: print("   feats:",out[n]["features"])
json.dump(out,open(os.path.join(OUT,"axes2.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set()
