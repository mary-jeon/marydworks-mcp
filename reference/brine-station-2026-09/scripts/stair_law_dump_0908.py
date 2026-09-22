"""09-08 저녁: 계단(S20000)·프레임/데크(S10000) 부품 실측 덤프 — 법규(제13조 안전난간) 저스트 보완 설계 입력.
출력: _검증\stair_law_0908\dump.json  (월드 좌표 = S00000MU0, -X 상방, 지면 x≈+1109)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
stop=watchdog(); app=connect()
OUT=r"<PROJECT_DIR>\_검증\stair_law_0908"; os.makedirs(OUT,exist_ok=True)
A=os.path.join(Z,"S00000MU0.SLDASM"); asm=app.GetOpenDocumentByName(A)
cm=asm.ConfigurationManager; root=cm.ActiveConfiguration.GetRootComponent3(True)
def props(c):
    try:
        md=c.GetModelDoc2; cpm=md.Extension.CustomPropertyManager(""); out={}
        for k in ("TITLE","SPEC","Material","QT'Y","REMARK"):
            v=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""); r=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""); wr=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BOOL,False)
            try: cpm.Get5(k,False,v,r,wr); out[k]=r.value
            except Exception: pass
        return out
    except Exception as ex: return {"err":str(ex)}
def cyl_radii(c):
    try:
        md=c.GetModelDoc2; b=(pv(md,"GetBodies2",0,True) or [])
        rs=set()
        for bb in b:
            for f in (pv(bb,"GetFaces") or []):
                s=f.GetSurface
                if s.IsCylinder: rs.add(round(s.CylinderParams[6]*1000,2))
        return sorted(rs)
    except Exception: return []
rows=[]
def walk(c,path,depth):
    for ch in (pv(c,"GetChildren") or []):
        n=ch.Name2.split("/")[-1]; p=path+"/"+n
        if pv(ch,"IsSuppressed"): continue
        if n.startswith(("S20","S10")) or path.endswith(("S20000MU0-1","S10000MU0-1")) or "/S20000MU0-1/" in p or "/S10000MU0-1/" in p:
            rows.append({"path":p,"name":n,"box":box(ch),"xform":xform(ch),"props":props(ch) if depth>=1 else {},"cyl_r":cyl_radii(ch) if depth>=1 else []})
        walk(ch,p,depth+1)
walk(root,"",0)
json.dump(rows,open(os.path.join(OUT,"dump.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
seen=set()
for r in rows:
    key=r["name"].split("-")[0]
    b=r["box"]; pr=r["props"]
    print(f'{r["name"]:16s} box x[{b[0]:8.1f},{b[3]:8.1f}] y[{b[1]:8.1f},{b[4]:8.1f}] z[{b[2]:8.1f},{b[5]:8.1f}]  r={r["cyl_r"][:4]}  {pr.get("TITLE","")} | {str(pr.get("SPEC",""))[:60]} | {pr.get("Material","")}')
stop.set()
