# 2026-09-09 밤: 대공사 2단계 — 염수주입라인.SLDASM 교체/재배치 (1단계 rebuild_ta2_parts_0909.py 이후)
#  LA25/J8b/J9b/핀/와셔/호스/Tameson+OM-1/J5d 삭제 → TA2/J8c/J9c/SHCCG8/J19e/KE002+3PC/J5e 추가, 봉·부시·이동 스택 재배치
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
Zp=lambda n: os.path.join(Z,n)
AX=70.0; RY=240.0; OX=0.0; OY=10.0; ZP_UP=-390.0; ZP_DN=-510.0
VALVE_TOP=-34.5; NIP_FIX_TOP=-114.0; NIP_FIX_END=-144.0; Z_REAR_PIN=-140.0; PIN_ROD_H=25.0
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
NEW={ # 파일명: (R, t, {구성: 활성?})
 "B9d_TiMOTION_TA2-2H-120_24V.SLDPRT":            (I3,(AX,0,Z_REAR_PIN),{"상승":1,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),
 "J8c_sm_U_bracket_t3.2_25x140x40.SLDPRT":        (I3,(AX,0,Z_REAR_PIN),{"상승":1,"하강":1,"1.상승했을때(해석)":1,"2.하강했을때(해석)":0}),
 "G11d_MISUMI_SHCCG8-25.3_pin.SLDPRT":            (I3,(AX,-12.45,Z_REAR_PIN),{"상승":1,"하강":1,"1.상승했을때(해석)":1,"2.하강했을때(해석)":1}),
 "G3b_valve_3PC_3-4in_ISO_F03F04_SUS.SLDPRT":     (I3,(0,0,VALVE_TOP),{"상승":1,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),
 "B4b_actuator_KOSAPLUS_KE002_24VDC.SLDPRT":      (I3,(0,-48.0,VALVE_TOP-40.0),{"상승":1,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),
 "J19e_hose_3-4in_dn_straight_L336.SLDPRT":       (R_HOSE,(0,0,NIP_FIX_END),{"상승":0,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),
 "J19e_hose_3-4in_up_bow_R54.SLDPRT":             (R_HOSE,(0,0,NIP_FIX_END),{"상승":1,"하강":0,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),
}
NEW2={ # 상승/하강 인스턴스 쌍
 "J9c_sm_U_clevis_t3.2_27x33x40.SLDPRT":  ((I3,(AX,0,ZP_UP),{"상승":1,"하강":0,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),(I3,(AX,0,ZP_DN),{"상승":0,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":1})),
 "J11c_MISUMI_SHCCG8-27.3_pin.SLDPRT":    ((I3,(AX,-13.45,ZP_UP+PIN_ROD_H),{"상승":1,"하강":0,"1.상승했을때(해석)":1,"2.하강했을때(해석)":0}),(I3,(AX,-13.45,ZP_DN+PIN_ROD_H),{"상승":0,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":1})),
 "J5e_moving_plate_180x540_t8.SLDPRT":    ((I3,(0,0,ZP_UP),{"상승":1,"하강":0,"1.상승했을때(해석)":0,"2.하강했을때(해석)":0}),(I3,(0,0,ZP_DN),{"상승":0,"하강":1,"1.상승했을때(해석)":0,"2.하강했을때(해석)":1})),
}
DELETE_PREFIX=("B9c_LINAK","J8b_bent","J9b_rod","G11c_MISUMI","J11b_MISUMI","J22_MISUMI","J19c_hose","G3_valve_body_Tameson","B4_actuator_SunYeh","J5d_moving")
MOVE={ # 기존 인스턴스 t 재설정(R 유지)
 "J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-3":(AX,RY,0),"J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-4":(AX,-RY,0),
 "B10_linear_bushing_MISUMI_LHFRW16-21":(AX,RY,ZP_UP),"B10_linear_bushing_MISUMI_LHFRW16-22":(AX,-RY,ZP_UP),
 "B10_linear_bushing_MISUMI_LHFRW16-23":(AX,RY,ZP_DN),"B10_linear_bushing_MISUMI_LHFRW16-24":(AX,-RY,ZP_DN),
 "G13_weld_socket_3-4in_L25-10":(OX,OY,ZP_UP),"G13_weld_socket_3-4in_L25-11":(OX,OY,ZP_DN),
 "H16_hose_nipple_3-4in_short_L30-11":(OX,OY,ZP_UP+30),"H16_hose_nipple_3-4in_short_L30-12":(OX,OY,ZP_DN+30),
 "J17_pipe_3-4in_L100-3":(OX,OY,ZP_UP),"J17_pipe_3-4in_L100-4":(OX,OY,ZP_DN),
 "H16_hose_nipple_3-4in_short_L30-10":(0,0,NIP_FIX_TOP),
}
# ---------- 0) J1c 외곽 재수정 (−82 → −75)
P1=Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); d=app.GetOpenDocumentByName(P1) or open_doc(app,P1,1); app.ActivateDoc3(P1,False,0,I4()); d=app.ActiveDoc
bb=[round(v*1000,1) for v in pv(d,"GetPartBox",True)]
if abs(bb[0]+75)>0.2:
    if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2("스케치3","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch()
    sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
    for s in list(pv(sk,"GetSketchSegments") or []):
        if (s.GetType() if callable(s.GetType) else s.GetType)==0: s.Select4(True,NOD); n+=1
    d.Extension.DeleteSelection2(0); sm=d.SketchManager; sm.AddToDB=True
    sm.CreateCornerRectangle(mm(-75),mm(-290),0,mm(110),mm(290),0); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.EditRebuild3
    bb=[round(v*1000,1) for v in pv(d,"GetPartBox",True)]; print("J1c fixed:",n,"lines ->",bb)
    e=I4(); w=I4(); print("  save J1c",d.Save3(1,e,w))
assert abs(bb[0]+75)<0.2 and abs(bb[3]-110)<0.2,"J1c outline wrong"
# ---------- 1) 어셈블리
ASM=Zp("염수주입라인.SLDASM"); a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); title=a.GetTitle.replace(".SLDASM",""); print("cfgs",CFGS)
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def sel_comp(n):
    a.ClearSelection2(True); return a.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def set_supp(n,on):
    sel_comp(n)
    if on: a.EditUnsuppress2
    else: a.EditSuppress2
    a.ClearSelection2(True)
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
# 1a) 삭제
for n in list(cc):
    if n.startswith(DELETE_PREFIX):
        sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
a.EditRebuild3; cc=comps()
# 1b) 기존 이동 (전 구성)
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,t in MOVE.items():
        if n in cc: move_fixed(cc[n],xform(cc[n])["R"],t)
    a.EditRebuild3
# 1c) 추가
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
def add_comp(fn):
    global a
    p=Zp(fn)
    if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    cfgs=list(pv(app.GetOpenDocumentByName(p),"GetConfigurationNames"))
    tries=[(0,"",False)]+([(0,"상승",True)] if "상승" in cfgs else [])+[(0,cfgs[0],True)]
    for opt,cn,use in tries:
        c=a.AddComponent5(p,opt,cn,use,"",0.0,0.0,0.0)
        if c: a.EditRebuild3; print("added",c.Name2,"via",opt,cn,use); return c
    c=a.AddComponent4(p,"",0.0,0.0,0.0)
    if c: a.EditRebuild3; print("added",c.Name2,"via AddComponent4"); return c
    raise SystemExit("AddComponent failed "+fn)
added={}
for fn,(R,t,supp) in NEW.items():
    base=fn[:-7]
    ex=[n for n in cc if n.startswith(base+"-")]
    if ex: added[fn]=[ex[0]]; continue
    c=add_comp(fn); cc=comps(); added[fn]=[c.Name2]
for fn,pair in NEW2.items():
    base=fn[:-7]; ex=sorted([n for n in cc if n.startswith(base+"-")])
    while len(ex)<2:
        c=add_comp(fn); cc=comps(); ex=sorted([n for n in cc if n.startswith(base+"-")])
    added[fn]=ex[:2]
# 1d) 전 구성: 변환·고정·억제·참조구성
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for fn,(R,t,supp) in NEW.items():
        n=added[fn][0]; c=cc[n]; move_fixed(c,R,t); set_supp(n,supp[cfg])
        if fn.startswith("B9d") and supp[cfg]:
            cc=comps(); cc[n].ReferencedConfiguration=("하강" if cfg.startswith(("하강","2.")) else "상승")
    for fn,pair in NEW2.items():
        for n,(R,t,supp) in zip(added[fn],pair):
            move_fixed(cc[n],R,t); set_supp(n,supp[cfg])
    a.ForceRebuild3(False)
# ---------- 2) 검증
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
rep={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); rep[cfg]={"whatswrong":ww(a),"boxes":{},"interf":None}
    act=[n for n,c in cc.items() if c.GetSuppression2==2]
    for n in act:
        b=box(cc[n]); rep[cfg]["boxes"][n]=b
    print(f"[{cfg}] whatswrong {rep[cfg]['whatswrong']} active {len(act)}")
    if cfg in ("상승","하강"):
        for n in act: print(f"   {n:46s} {rep[cfg]['boxes'][n]}")
        a.ClearSelection2(True)
        for n in act: cc[n].Select4(True,NOD,False)
        idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
        rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True)
        rep[cfg]["interf"]=rows; print(f"   간섭 {len(rows)}:",rows)
    if cfg=="상승":
        c=cc[added["B9d_TiMOTION_TA2-2H-120_24V.SLDPRT"][0]]; print("   TA2 refcfg",c.ReferencedConfiguration)
    if cfg=="하강":
        c=cc[added["B9d_TiMOTION_TA2-2H-120_24V.SLDPRT"][0]]; print("   TA2 refcfg",c.ReferencedConfiguration)
a.ShowConfiguration2("상승"); a.EditRebuild3
json.dump(rep,open(os.path.join(VER,"ta2_rebuild_line_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value,w.value)
stop.set(); print("stage2 done")
