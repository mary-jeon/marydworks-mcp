# 읽기 전용: S00000MU0 트리에서 S20002MU0-3·S10007MU0-3·S10001MU0-1·L 브라켓 컴포넌트 위치와 관련 메이트 조사
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
from swconn import *
from swpv import pv
PS=os.path.join(Z,"S00000MU0.SLDASM")
app=connect(); s=app.GetOpenDocumentByName(PS); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager
print("active cfg",scm.ActiveConfiguration.Name)
out=[]
def walk(c,depth):
    for ch in (pv(c,"GetChildren") or []):
        out.append((ch.Name2,ch))
        if depth<3: walk(ch,depth+1)
walk(scm.ActiveConfiguration.GetRootComponent3(True),0)
KEY=("S20002MU0","S10007MU0","S10001MU0","L-BRACKET","L_BRACKET","L브라켓","BRACKET")
MATE_T={0:"COINCIDENT",1:"CONCENTRIC",2:"PERPENDICULAR",3:"PARALLEL",4:"TANGENT",5:"DISTANCE",6:"ANGLE",7:"UNKNOWN",8:"SYMMETRIC",9:"CAMFOLLOWER",10:"GEAR",11:"WIDTH",12:"LOCKTOLOCK",13:"RACKPINION",14:"MAXMATES",15:"SCREW",16:"LINEARCOUPLER",17:"UNIVERSALJOINT",18:"COORDINATE",19:"SLOT",20:"HINGE",21:"LOCK",22:"PROFILECENTER",23:"MAGNETIC"}
def ent_desc(me):
    try:
        c=me.ReferenceComponent; ref=me.Reference
        t=me.ReferenceType2; nm=""
        try: nm=ref.Name
        except Exception: pass
        return f"{c.Name2 if c else '?'}:{t}:{nm}"
    except Exception as ex: return f"?{ex}"
for n,c in out:
    base=n.split("/")[-1]
    if base.upper().startswith(KEY) or "BRACKET" in base.upper():
        print(f"\n== {n}  supp {c.GetSuppression2} fixed {c.IsFixed} path {os.path.basename(c.GetPathName)} box {box(c)}")
        try:
            for m in (pv(c,"GetMates") or []):
                f=m.GetFeature if hasattr(m,"GetFeature") else None
                fname=f.Name if f else "?"
                ents=[ent_desc(m.MateEntity(i)) for i in range(m.GetMateEntityCount)]
                al=m.Alignment;
                print(f"   mate {fname} type {MATE_T.get(m.Type,m.Type)} align {al} flip {m.Flipped} ents {ents}")
        except Exception as ex: print("   mates exc",ex)
