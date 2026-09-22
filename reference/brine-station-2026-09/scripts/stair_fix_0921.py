# 2026-09-21 계단 단축(RUN 205) 후 보정 — stair_fix_0917.py 사본: 지주 길이(난간대 하면 = 축 − r/cosθ) · 난간대 끝 플랫폼 기둥 앞면(z 980) 수직 절단 → 간섭 재검
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"stair_rebuild_0921.py"),encoding="utf-8").read().split("# ---------- 0.")[0])
z1,y1=nos(1); Z_S=z1-RAIL_START_EXT; RAIL_L=(PLAT_Z-Z_S)/COS
# 1) 지주: D1@지주_Ø48.6 = 150 + 900 − r/cosθ
POST_L2=POST_BOT_BELOW+RAIL_H-(RAIL_D/2)/COS
d=app.GetOpenDocumentByName(P_PO) or open_doc(app,P_PO,1); app.ActivateDoc3(P_PO,False,0,I4()); d=app.ActiveDoc
f=d.FeatureByName("지주_Ø48.6"); dim=f.Parameter("D1"); print("post D1",dim.SystemValue*1000,"->",POST_L2); dim.SetSystemValue3(mm(POST_L2),2,None); d.ForceRebuild3(False)
bx=bbox(d); assert abs(bx[4]-POST_L2)<0.05, bx
cp=d.Extension.CustomPropertyManager(""); import re as _re; sp=_re.sub(r"L\d{3,4}\.\d",f"L{POST_L2:.1f}",cp.Get("SPEC"),count=1); cp.Set2("SPEC",sp)
e=I4(); w=I4(); assert d.Save3(1,e,w); print("post saved"); app.CloseDoc(d.GetTitle)
# 2) 난간대 끝 수직 절단(로컬 z ≥ 1950 제거): S20017·S20018
ZEND=PLAT_Z-Z_S
for P in (P_RA,P_MR):
    d=app.GetOpenDocumentByName(P) or open_doc(app,P,1); app.ActivateDoc3(P,False,0,I4()); d=app.ActiveDoc
    if d.FeatureByName("끝단_수직컷") is None:
        nb0=len(bodies(d)); v0=volume(d); ok=False
        for conv in (0,1):
            assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); skobj=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
            pts=[(0,-100,ZEND),(0,2100,ZEND),(0,2100,ZEND+100),(0,-100,ZEND+100)]; spp=[sketch_xy(skobj,mm(q[0]),mm(q[1]),mm(q[2]),conv) for q in pts]
            for i in range(4): sm.CreateLine(spp[i][0],spp[i][1],0,spp[(i+1)%4][0],spp[(i+1)%4][1],0)
            sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            skc=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(skc,"SKETCH",0,0,0,False,0,NOD,0)
            c=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
            zmax=max([v*1000 for b in bodies(d) for v in [pv(b,"GetBodyBox")[5]]]) if bodies(d) else None
            print(f"  {os.path.basename(P)} end cut conv {conv}: dv {round(v0-volume(d)) if c else None} zmax {zmax} bodies {len(bodies(d))}")
            if c is not None and zmax is not None and abs(zmax-ZEND)<0.05 and len(bodies(d))==nb0: c.Name="끝단_수직컷"; ok=True; break
            if c is not None: c.Select2(False,0); d.EditDelete()
            clean_orphans(d)
        assert ok, P
        assert not clean_orphans(d); e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved",os.path.basename(P))
    app.CloseDoc(d.GetTitle)
# 3) 어셈블리 재검
a=app.GetOpenDocumentByName(ASM20); app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; a.ForceRebuild3(False); print("S20000 ww",ww(a)); a.ClearSelection2(True)
idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
print("S20000 interferences",len(res)); [print("   ",v,[c[:20] for c in cs]) for cs,v in res[:20]]
json.dump({"post_L":POST_L2,"interf":res},open(os.path.join(VER,"stair_fix_0921.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE fix")
