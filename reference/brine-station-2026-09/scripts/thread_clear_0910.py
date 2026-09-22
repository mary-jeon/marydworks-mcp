# 2026-09-10: 사용자 「간섭 2개 보임」 → 나사 겹침 표현(암나사 보어를 골경으로 그린 것)을 없앤다.
#  암나사 보어를 수나사 바깥지름(26.4~26.7)보다 조금 큰 Ø26.5로: G13b 소켓 보어 24.1→26.5(제자리), G3c 밸브 양단 포트 Ø26.5×깊이 14 컷(형상 대용 파트에 표현 컷, REMARK 기재).
#  남는 것: 밸브 스템↔KE002 소켓(스템 각형 삽입 표현), 밸브 패드 보스↔KE002 베이스(대용 밸브 기하), 핀↔클레비스(미세) — 보고.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
mm=lambda v:v/1000.0; R_BORE=13.25; PORT_DEPTH=14.0; VALVE_L=83.0
stop=watchdog(); app=connect()
def act(p):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def cyls(d): return sorted(set((round(s.CylinderParams[6]*1000,2),round(s.CylinderParams[2]*1000,1)) for b in (pv(d,"GetBodies2",0,True) or []) for fc in b.GetFaces() for s in [fc.GetSurface] if s.IsCylinder))
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in (pv(d,"GetBodies2",0,True) or []))
# ---- G13b 보어 제자리 확대
P=os.path.join(Z,"G13b_socket_Rp3-4_KS_L36.SLDPRT"); d=act(P)
f=d.FeatureByName("보어"); sk=None; sf=pv(f,"GetFirstSubFeature")
while sf:
    if pv(sf,"GetTypeName2")=="ProfileFeature": sk=sf.Name; break
    sf=pv(sf,"GetNextSubFeature")
assert sk, "bore sketch"
if not any(abs(c[0]-R_BORE)<0.05 for c in cyls(d)):
    d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); s_=d.SketchManager.ActiveSketch; d.ClearSelection2(True)
    for seg in list(pv(s_,"GetSketchSegments") or []): seg.Select4(True,NOD)
    d.Extension.DeleteSelection2(0); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(R_BORE)); d.SketchManager.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False)
print("G13b cyl",cyls(d),"ww",ww(d)); assert not ww(d) and any(abs(c[0]-R_BORE)<0.05 for c in cyls(d))
cp=d.Extension.CustomPropertyManager(""); s=cp.Get("SPEC") or ""; cp.Set2("SPEC",s.replace("보어 Ø24.1(Rp 골경 근사)","보어 Ø26.5(수나사 바깥지름 기준 — 겹침 없는 나사 표현)")); e=I4(); w=I4(); print("save G13b",d.Save3(1,e,w))
# ---- G3c 포트 컷 (상단 z 0 → −14, 하단 −83 → −69)
P3=os.path.join(Z,"G3c_valve_3PC_3-4in_ISO_Tameson_BL2SA3-034.SLDPRT"); d=act(P3); v0=vol(d)
names=[f.Name for f in []]
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
if "포트컷_상" not in feat_names(d):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(R_BORE)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
    # 블라인드 컷: 정면(XY, z=0)에서 −z로 14. Dir 플래그는 원 스케치 실측(True=−z)
    f=d.FeatureManager.FeatureCut4(True,False,True,0,0,mm(PORT_DEPTH),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    assert f, "top port cut"; f.Name="포트컷_상"; v1=vol(d); print("top port cut vol",round(v0),"->",round(v1))
    if v1>=v0-10:   # 방향 반대면 지우고 뒤집기
        d.ClearSelection2(True); d.Extension.SelectByID2("포트컷_상","BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
        d.ClearSelection2(True); d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0); d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(R_BORE)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureCut4(True,False,False,0,0,mm(PORT_DEPTH),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert f; f.Name="포트컷_상"; v1=vol(d); print("top port cut(flip) vol",round(v1))
    assert v1<v0-10
    # 하단: 정면에서 −83 오프셋 기준면 → 위로 14 컷
    d.ClearSelection2(True); d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    pl=d.FeatureManager.InsertRefPlane(8,mm(VALVE_L),0,0,0,0); assert pl, "ref plane"; pl.Name="포트면_하"
    pbx=[round(v*1000,1) for v in pv(d,"GetPartBox",True)]
    d.ClearSelection2(True); assert d.Extension.SelectByID2("포트면_하","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(R_BORE)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
    v2=vol(d); f=d.FeatureManager.FeatureCut4(True,False,False,0,0,mm(PORT_DEPTH),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    if f is None or vol(d)>=v2-10:
        if f: d.ClearSelection2(True); d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
        d.ClearSelection2(True); d.Extension.SelectByID2("포트면_하","PLANE",0,0,0,False,0,NOD,0); d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(R_BORE)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureCut4(True,False,True,0,0,mm(PORT_DEPTH),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    assert f and vol(d)<v2-10, "bottom port cut"; f.Name="포트컷_하"; print("bottom port cut vol",round(v2),"->",round(vol(d)))
    # 기준면이 −83인지 확인(컷 위치): 실린더 z 위치로
    zs=[c for c in cyls(d) if abs(c[0]-R_BORE)<0.05]; print("port cyl (r,z0)",zs)
    assert any(abs(c[1]-0)<0.5 or abs(c[1]+83)<0.5 or abs(c[1]+69)<0.5 for c in zs)
print("G3c ww",ww(d)); assert not ww(d)
cp=d.Extension.CustomPropertyManager(""); r=cp.Get("REMARK") or ""
if "포트 보어 Ø26.5" not in r: cp.Set2("REMARK",r+" | 양단 포트 보어를 Ø26.5×깊이 14로 컷(수나사 바깥지름 기준 겹침 없는 나사 표현 — 형상 대용 파트에 추가한 표현 컷)")
e=I4(); w=I4(); print("save G3c",d.Save3(1,e,w))
# ---- 어셈블리 간섭 재검
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
rep={}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); rows=interf([c for c in cc.values() if c.GetSuppression2==2]); rep[cfg]=rows
    print(f"[{cfg}] 간섭 {len(rows)}:"); [print(f"   {v:8.1f} {n[0]} ↔ {n[1]}") for n,v in sorted(rows,key=lambda r:-r[1]) if v>=1.0]
a.ShowConfiguration2("상승"); a.EditRebuild3; e=I4(); w=I4(); print("save asm",a.Save3(1,e,w))
json.dump(rep,open(os.path.join(VER,"interf_after_thread_clear_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("done")
