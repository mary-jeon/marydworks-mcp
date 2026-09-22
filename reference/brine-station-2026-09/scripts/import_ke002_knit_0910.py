# 2026-09-10: KE002 파트(어셈블리→파트 저장 결과가 곡면(sheet) 바디 13개) → 바디별 니트(InsertSewRefSurface, 솔리드 형성) → 솔리드 수·체적·탭 구멍 축(스템 축) 조사
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
OUT=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT")
stop=watchdog(); app=connect()
d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
def sheets(): return list(pv(d,"GetBodies2",1,False) or [])
def solids(): return list(pv(d,"GetBodies2",0,False) or [])
print("before: sheet",len(sheets()),"solid",len(solids()))
rep={"knit":[]}
for i in range(20):
    ss=sheets()
    if not ss: break
    b=ss[0]; name=pv(b,"Name"); nf=len(b.GetFaces())
    d.ClearSelection2(True)
    try: ok=b.Select2(False,None)
    except Exception as ex:
        ok=None
        for fc in b.GetFaces(): fc.Select4(True,NOD)
    f=None
    try: f=d.FeatureManager.InsertSewRefSurface(False,True,True,0.0001,0.0)   # UseGapFilters, TryToFormSolid, MergeEntities, KnitTolerance(m), MaxGap
    except Exception as ex: print("  knit exc",name,ex)
    d.EditRebuild3
    print(f"  knit {name} faces {nf} sel {ok} feat {f.Name if f else None} -> sheet {len(sheets())} solid {len(solids())}")
    rep["knit"].append((name,nf,bool(f),len(sheets()),len(solids())))
    if len(sheets())>=len(ss):   # 줄지 않으면 면 선택으로 재시도
        d.ClearSelection2(True)
        for fc in b.GetFaces(): fc.Select4(True,NOD)
        try: f=d.FeatureManager.InsertSewRefSurface(False,True,True,0.0001,0.0)
        except Exception as ex: print("  knit(faces) exc",ex)
        d.EditRebuild3; print(f"   retry faces -> sheet {len(sheets())} solid {len(solids())}")
        if len(sheets())>=len(ss): print("   giving up on",name); break
sol=solids(); print("solids",len(sol))
info=[(pv(b,"Name"),[round(v*1000,1) for v in pv(b,"GetBodyBox")],round(pv(b,"GetMassProperties",0)[3]*1e9)) for b in sol]
for x in info: print("  ",x)
rep["solids"]=info; rep["sheets_left"]=len(sheets())
bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("box",bx)
cyl=[]
for b in sol:
    for fc in b.GetFaces():
        s=fc.GetSurface
        if s.IsCylinder:
            p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],3),round(p[4],3),round(p[5],3)],[round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)],[round(v*1000,1) for v in fc.GetBox]))
small=[c for c in cyl if 1.5<=c[0]<=3.3]
print("small cyl groups",collections.Counter(tuple(abs(a) for a in c[1]) for c in small).most_common(4))
for c in sorted(small,key=lambda c:(c[1],c[3]))[:30]: print("  r",c[0],"ax",c[1],"origin",c[2],"box",c[3])
big=sorted([c for c in cyl if c[0]>3.3],key=lambda c:-c[0])[:12]; print("big cyl:"); [print("  r",c[0],"ax",c[1],"origin",c[2],"box",c[3]) for c in big]
rep["box"]=bx; rep["small"]=small; rep["big"]=big
json.dump(rep,open(os.path.join(VER,"ke002_knit_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("knit stage done (not saved)")
