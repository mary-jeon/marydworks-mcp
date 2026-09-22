# 읽기 전용: S00000MU0 최상위 메이트 전수(엔티티 컴포넌트·면 위치) + S10001/S10007/S20002/L브라켓 박스
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
PS=os.path.join(Z,"S00000MU0.SLDASM")
app=connect(); s=app.GetOpenDocumentByName(PS); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
MATE_T={0:"COINCIDENT",1:"CONCENTRIC",2:"PERPENDICULAR",3:"PARALLEL",4:"TANGENT",5:"DISTANCE",6:"ANGLE",8:"SYMMETRIC",11:"WIDTH",16:"LINEARCOUPLER",18:"COORDINATE",21:"LOCK"}
out=[]
def walk(c,depth):
    for ch in (pv(c,"GetChildren") or []):
        out.append((ch.Name2,ch))
        if depth<2: walk(ch,depth+1)
walk(scm.ActiveConfiguration.GetRootComponent3(True),0)
print("== boxes (world: -x up, +z front?)")
for n,c in out:
    base=n.split("/")[-1]
    if base.startswith(("S10001MU0","S10007MU0","S20002MU0","L-BRACKET")) or n.count("/")==0 and base.startswith(("S1","S2","S3")):
        print(f"  {n:40s} supp {c.GetSuppression2} box {box(c)}")
print("== top-level mates of S00000MU0")
f=pv(s,"FirstFeature"); mates=[]
while f is not None:
    if pv(f,"GetTypeName2")=="MateGroup":
        sf=f.GetFirstSubFeature
        while sf is not None:
            m=sf.GetSpecificFeature2
            try:
                ents=[]
                for i in range(m.GetMateEntityCount):
                    me=m.MateEntity(i); c=me.ReferenceComponent; t=me.ReferenceType2
                    geo=""
                    try:
                        ref=me.Reference
                        if t==2:  # face
                            fb=[round(v*1000,1) for v in ref.GetBox]; sfc=ref.GetSurface
                            nrm=[round(v,2) for v in pv(ref,"Normal")] if sfc.IsPlane else "cyl"
                            geo=f"box{fb} n{nrm}"
                        elif t==4: geo=ref.Name
                    except Exception as ex: geo=f"?{ex}"[:40]
                    ents.append(f"{c.Name2 if c else '?'}|{t}|{geo}")
                st=sf.GetSuppression2 if hasattr(sf,"GetSuppression2") else "?"
                print(f"  {sf.Name:30s} {MATE_T.get(m.Type,m.Type):12s} align {m.Alignment} supp {pv(sf,"IsSuppressed")} :: "+" || ".join(ents))
            except Exception as ex: print("  ",sf.Name,"exc",ex)
            sf=sf.GetNextSubFeature
    f=pv(f,"GetNextFeature")
print("== L bracket doc props")
for n,c in out:
    if n.startswith("L-BRACKET"):
        md=c.GetModelDoc2
        if md:
            cp=md.Extension.CustomPropertyManager("")
            for k in (pv(cp,"GetNames") or []): print("   ",k,"=",cp.Get(k))
