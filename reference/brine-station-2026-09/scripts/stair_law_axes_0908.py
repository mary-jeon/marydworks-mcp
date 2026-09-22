"""09-08 저녁: 계단 난간(S20004 상부 난간대·S20005 지주) 원통 축을 월드 좌표로 뽑고, 디딤판 앞코 대비 높이를 계산.
+ x–z 측면도 PNG (난간·지주·디딤판·스트링거·플랫폼·데크) → 설계 입력.
"""
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
def world(c,p):   # 파트 좌표 → 월드 (행벡터 p'=p·R+t)
    a=list(c.Transform2.ArrayData); R=[a[0:3],a[3:6],a[6:9]]; t=a[9:12]
    return [sum(p[i]*R[i][j] for i in range(3))*1000+t[j]*1000 for j in range(3)]
def worldv(c,v):
    a=list(c.Transform2.ArrayData); R=[a[0:3],a[3:6],a[6:9]]
    return [sum(v[i]*R[i][j] for i in range(3)) for j in range(3)]
axes={}
for pref in ("S20004","S20005"):
    for c in find(root,pref,[]):
        md=c.GetModelDoc2; b=(pv(md,"GetBodies2",0,True) or [])[0]
        # 바깥 원통(r 최대)의 축: 원점·방향 + 그 축 방향으로 바디 박스 투영 범위
        best=None
        for f in (pv(b,"GetFaces") or []):
            s=f.GetSurface
            if s.IsCylinder:
                cp=s.CylinderParams
                if best is None or cp[6]>best[6]: best=cp
        o=world(c,best[0:3]); d=worldv(c,best[3:6]); r=best[6]*1000
        bx=box(c); corners=[[bx[i],bx[j],bx[k]] for i in (0,3) for j in (1,4) for k in (2,5)]
        ts=[sum((q[m]-o[m])*d[m] for m in range(3)) for q in corners]
        t0,t1=min(ts)+r*0.0,max(ts)   # 박스 투영(끝단 근사)
        # 실제 끝: 평면 끝면(축에 수직)의 위치
        ends=[]
        for f in (pv(b,"GetFaces") or []):
            s=f.GetSurface
            if s.IsPlane:
                pp=s.PlaneParams; n=worldv(c,pp[0:3]); p0=world(c,pp[3:6])
                if abs(abs(sum(n[m]*d[m] for m in range(3)))-1)<1e-3: ends.append(sum((p0[m]-o[m])*d[m] for m in range(3)))
        if ends: t0,t1=min(ends),max(ends)
        P0=[o[m]+d[m]*t0 for m in range(3)]; P1=[o[m]+d[m]*t1 for m in range(3)]
        n=c.Name2.split("/")[-1]; axes[n]={"r":r,"P0":[round(v,1) for v in P0],"P1":[round(v,1) for v in P1],"dir":[round(v,4) for v in d],"len":round(t1-t0,1),"box":bx}
        print(n,"r",r,"P0",axes[n]["P0"],"P1",axes[n]["P1"],"L",axes[n]["len"])
dump=json.load(open(os.path.join(OUT,"dump.json"),encoding="utf-8"))
boxes={r["name"]:r["box"] for r in dump}
# 디딤판 앞코: 상면 x_min(위쪽), z_min(오르는 방향 +z 이므로 −z 쪽 모서리)
treads=sorted([(n,b) for n,b in boxes.items() if n.startswith("S20001")],key=lambda nb:nb[1][2])
res={"axes":axes,"tread_nose":[],"rail_height":{}}
for side in ("-y","+y"):
    rail=[k for k,v in axes.items() if k.startswith("S20004") and ((v["P0"][1]>-1200) if side=="-y" else (v["P0"][1]<-1200))][0]
    v=axes[rail]; P0,P1=v["P0"],v["P1"]
    def x_at_z(z):   # 축 위 z→x 보간(직선)
        return P0[0]+(P1[0]-P0[0])*(z-P0[2])/(P1[2]-P0[2])
    hs=[]
    for n,b in treads:
        nose_x=b[0]; nose_z=b[2]
        if min(P0[2],P1[2])<=nose_z<=max(P0[2],P1[2]):
            h=nose_x-x_at_z(nose_z); hs.append((n,round(nose_z,1),round(nose_x,1),round(h,1)))
        else: hs.append((n,round(nose_z,1),round(nose_x,1),None))
    res["rail_height"][side]={"rail":rail,"heights_nose_to_axis":hs,"slope_deg":round(math.degrees(math.atan2(-(P1[0]-P0[0]),(P1[2]-P0[2]))),2)}
    print(side,rail,"slope",res["rail_height"][side]["slope_deg"],hs)
stair_slope=math.degrees(math.atan2(250,145)); print("stair slope",round(stair_slope,2))
res["tread_nose"]=[(n,b[0],b[2]) for n,b in treads]
json.dump(res,open(os.path.join(OUT,"axes.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
# 측면도 (z 가로, x 세로 반전: 위가 -x)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(14,8))
def rect(b,color,lab=None,alpha=0.4):
    ax.add_patch(plt.Rectangle((b[2],b[0]),b[5]-b[2],b[3]-b[0],fill=True,alpha=alpha,color=color,label=lab))
for n,b in boxes.items():
    if b[1]>-1200 and n.startswith("S20"):   # -y 쪽(가까운 쪽) 부재만 + 공통
        pass
for n,b in boxes.items():
    if n.startswith("S20001"): rect(b,"tab:orange")
    elif n.startswith(("S20006","S20008")) and b[1]>-1200: rect(b,"tab:gray")
    elif n.startswith("S20007"): rect(b,"tab:brown")
    elif n.startswith("S20010") or n.startswith("S20011"): rect(b,"tab:red",alpha=0.8)
    elif n.startswith(("S20002","S20003","S20009")) and b[1]>-1200: rect(b,"tab:blue",alpha=0.25)
    elif n.startswith("S10006"): rect(b,"tab:green",alpha=0.5)
    elif n.startswith(("S10007","S10008","S10009")) : rect(b,"tab:cyan",alpha=0.3)
for k,v in axes.items():
    if v["P0"][1]>-1200:
        ax.plot([v["P0"][2],v["P1"][2]],[v["P0"][0],v["P1"][0]],lw=3,color="k" if k.startswith("S20004") else "tab:purple")
        ax.text(v["P0"][2],v["P0"][0],k,fontsize=7)
ax.axhline(1109,color="k",ls="--",lw=0.8); ax.text(-2700,1109,"ground x=1109",fontsize=8)
ax.set_xlim(-2900,100); ax.set_ylim(1200,-2400); ax.set_aspect("equal"); ax.grid(True,lw=0.3)
ax.set_xlabel("z (world)"); ax.set_ylabel("x (world, up = -x)"); ax.set_title("Stair side view (-y side rails), before")
fig.savefig(os.path.join(OUT,"side_before.png"),dpi=110,bbox_inches="tight"); print("png saved")
stop.set()
