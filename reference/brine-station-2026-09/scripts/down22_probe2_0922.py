# 2026-09-22 읽기 전용: 라인 어셈블리(상승) 러그·핀·TA2 배치와 J9f·J8g 파트 피처
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
app=connect()
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
a.ShowConfiguration2("상승"); a.EditRebuild3
cc={c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
for n,c in sorted(cc.items()):
    if n.startswith(("J8g","J9f","G11f","J11e","B9k","J5p","J1d","J2d","J25a","B10b","F4")):
        x=xform(c); print(f"{n[:52]:52s} supp {c.GetSuppression2} t={x['t_mm']} box={box(c)}")
for pn in ("J9f","J8g","J11e","G11f"):
    p=[c.GetPathName for n,c in cc.items() if n.startswith(pn)][0]; d=app.GetOpenDocumentByName(p) or open_doc(app,p,1)
    print("\n==",os.path.basename(p))
    f=pv(d,"FirstFeature"); names=[]
    while f is not None:
        t=pv(f,"GetTypeName2")
        if t not in ("OriginProfileFeature","RefPlane","RefAxis","MaterialFolder","HistoryFolder","SensorFolder","CommentsFolder","DetailCabinet","DocsFolder","SelectionSetFolder","SolidBodyFolder","SurfaceBodyFolder","EnvFolder","BlockFolder","FavoriteFolder","MateReferenceGroupFolder","MarkupFolder"): names.append((f.Name,t))
        f=pv(f,"GetNextFeature")
    print("  feats",names)
    bs=list(pv(d,"GetBodies2",0,True) or []); print("  bodies",len(bs),[[round(v*1000,2) for v in pv(b,"GetBodyBox")] for b in bs])
    cp=d.Extension.CustomPropertyManager(""); print("  props",{k:cp.Get(k) for k in (pv(cp,"GetNames") or [])})
    # 스케치 치수
    f=pv(d,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2") in ("ProfileFeature",):
            dd=pv(f,"GetFirstDisplayDimension"); dims=[]
            while dd is not None:
                dm=dd.GetDimension2(0); dims.append((dm.FullName,round(dm.GetSystemValue3(1,None)[0]*1000,3) if False else round(dm.SystemValue*1000,3))); dd=pv(f,"GetNextDisplayDimension",dd)
            print("  ",f.Name,dims)
        f=pv(f,"GetNextFeature")
print("DONE")
