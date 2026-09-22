# 2026-09-10: 가이드봉 x 70 → 45(이동판 중앙) 이동 + 고정판 봉 구멍을 M16 탭(Ø14) → Ø16.5 관통(클램프 홀더 방식)으로 변경
#  J5e 스케치1: 부시 Ø28.5 + M4 탭 Ø3.3×4(PCD38) 두 조를 x 45로 (제자리 편집: 해당 원만 삭제·재생성)
#  J1c 스케치3: 봉 구멍 Ø14@(70,±240) → Ø16.5@(45,±240)
#  어셈블리: J2c-3/4 (45,±240,0), B10-21~24 (45,±240,ZP) 전 구성. 홀더(SHFSS16) 볼트 구멍은 규격 확인 후 별도.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
mm=lambda v:v/1000.0
AX_OLD=70.0; AX=45.0; RY=240.0; ZP_UP=-390.0; ZP_DN=-530.0; I3=[[1,0,0],[0,1,0],[0,0,1]]
stop=watchdog(); app=connect()
def act(p):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
def circles(d):
    out=[]
    for b in (pv(d,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder:
                p=s.CylinderParams; out.append((round(p[0]*1000,1),round(p[1]*1000,1),round(p[6]*1000,2)))
    return sorted(set(out))
def edit_sketch(d,skname,pick,new_circles):
    """pick(cx,cy,r)->True인 원을 지우고 new_circles [(cx,cy,r)]를 같은 스케치에 그린다"""
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); assert d.Extension.SelectByID2(skname,"SKETCH",0,0,0,False,0,NOD,0); d.EditSketch()
    sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
    for s in list(pv(sk,"GetSketchSegments") or []):
        ty=s.GetType() if callable(s.GetType) else s.GetType
        if ty==1:
            cp=pv(s,"GetCenterPoint2")
            try: cx,cy=cp[0]*1000,cp[1]*1000
            except TypeError: cx,cy=pv(cp,"X")*1000,pv(cp,"Y")*1000
            r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
            if pick(cx,cy,r): s.Select4(True,NOD); n+=1
    if n: d.Extension.DeleteSelection2(0)
    sm=d.SketchManager; sm.AddToDB=True
    for cx,cy,r in new_circles: sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(r))
    sm.AddToDB=False
    # 매달린 구속 정리
    try:
        rm=d.SketchManager.ActiveSketch.RelationManager; dang=list(pv(rm,"GetRelations",1) or [])
        for rel in dang: rm.DeleteRelation(rel)
        if dang: print("  dangling relations removed",len(dang))
    except Exception as ex: print("  relation cleanup skipped",ex)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False)
    return n
rep={}
# ---- J5e
P5=os.path.join(Z,"J5e_moving_plate_180x540_t8.SLDPRT"); d=act(P5)
before=circles(d)
new=[]
for sy in (RY,-RY):
    new.append((AX,sy,14.25))
    for dx,dy in ((19,0),(-19,0),(0,19),(0,-19)): new.append((AX+dx,sy+dy,1.65))
n=edit_sketch(d,"스케치1",lambda cx,cy,r: abs(abs(cy)-RY)<20 and r<15 and abs(cx-AX_OLD)<20, new)
after=circles(d); print("J5e deleted",n,"cyl after",[c for c in after if abs(abs(c[1])-RY)<20],"ww",ww(d))
assert not ww(d) and any(abs(c[0]-AX)<0.05 and abs(c[2]-14.25)<0.05 for c in after) and not any(abs(c[0]-AX_OLD)<0.05 and abs(c[2]-14.25)<0.05 for c in after)
cp=d.Extension.CustomPropertyManager(""); s=cp.Get("SPEC") or ""; cp.Set2("SPEC",s.replace(f"@({AX_OLD:g},±{RY:g})",f"@({AX:g},±{RY:g})").replace("부시 MISUMI LHFRW16 Ø28.5 + M4 탭 십자 PCD38 @(70,±240)","부시 MISUMI LHFRW16 Ø28.5 + M4 탭 십자 PCD38 @(45,±240)"))
e=I4(); w=I4(); print("save J5e",d.Save3(1,e,w),e.value); rep["J5e"]={"before":before,"after":after}
# ---- J1c
P1=os.path.join(Z,"J1c_fixed_plate_185x580_t10.SLDPRT"); d=act(P1)
before=circles(d)
n=edit_sketch(d,"스케치3",lambda cx,cy,r: abs(abs(cy)-RY)<1 and abs(cx-AX_OLD)<1, [(AX,RY,8.25),(AX,-RY,8.25)])
after=circles(d); print("J1c deleted",n,"cyl after",after,"ww",ww(d))
assert not ww(d) and any(abs(c[0]-AX)<0.05 and abs(c[2]-8.25)<0.05 for c in after)
cp=d.Extension.CustomPropertyManager(""); s=cp.Get("SPEC") or ""
cp.Set2("SPEC",s.replace("가이드봉 M16 탭 관통 2개소 @(70,±240)(드릴 Ø14 = 모델 구멍)","가이드봉 Ø16.5 관통 2개소 @(45,±240) — 봉은 판 밑면의 클램프형 샤프트 서포트(MISUMI SHFSS16)로 고정, 홀더 취부 탭은 규격 확인 후 추가"))
e=I4(); w=I4(); print("save J1c",d.Save3(1,e,w),e.value); rep["J1c"]={"before":before,"after":after}
# ---- 어셈블리
a=act(ASM); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
TARGET={"J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-3":(AX,RY,0),"J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-4":(AX,-RY,0),
        "B10_linear_bushing_MISUMI_LHFRW16-21":(AX,RY,ZP_UP),"B10_linear_bushing_MISUMI_LHFRW16-22":(AX,-RY,ZP_UP),
        "B10_linear_bushing_MISUMI_LHFRW16-23":(AX,RY,ZP_DN),"B10_linear_bushing_MISUMI_LHFRW16-24":(AX,-RY,ZP_DN)}
rep["asm"]={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,t in TARGET.items():
        c=cc[n]; t0=xform(c)["t_mm"]
        if abs(t0[0]-t[0])<0.05: continue
        assert abs(t0[0]-AX_OLD)<0.05, (n,t0); move_fixed(c,xform(c)["R"],t)
    a.ForceRebuild3(False); cc=comps()
    bad=[(n,xform(cc[n])["t_mm"]) for n,t in TARGET.items() if any(abs(p-q)>0.05 for p,q in zip(xform(cc[n])["t_mm"],t))]
    print(f"[{cfg}] mismatches {bad} ww {ww(a)}"); assert not bad; rep["asm"][cfg]={"ww":ww(a)}
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_={n:c for n,c in cc.items() if c.GetSuppression2==2}
    rows=interf(list(act_.values())); rows=[r for r in rows if any(x.startswith(("J2c","B10","J1c","J5e")) for x in r[0])]
    rep["asm"][cfg]["interf_guide"]=rows; print(f"[{cfg}] 봉·부시·판 관련 간섭 {len(rows)}:",rows)
    for n in ("J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10-3","B10_linear_bushing_MISUMI_LHFRW16-21","B10_linear_bushing_MISUMI_LHFRW16-23"):
        if n in act_: print("   ",n,box(act_[n]))
a.ShowConfiguration2("상승"); a.EditRebuild3; e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value)
json.dump(rep,open(os.path.join(VER,"shaft_center_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("shaft center done")
