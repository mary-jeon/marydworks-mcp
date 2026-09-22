# 2026-09-09: 탱크 주입구 뚜껑 S30008MU0 열림 구성.
#  - 경첩 C-HHSN65A_hinge 파트: 구성 「열림」 추가 → 리프1_90도장착 바디를 샤프트 축(x축, 로컬 y 4.25·z 15)으로 +90° 회전(MoveCopyBody), 기본에서는 억제.
#  - S30000MU0: 구성 「뚜껑열림」(상승 기준) 추가 → 뚜껑 잠금 메이트 묶기26 억제, 뚜껑·걸쇠를 경첩 축(y 814.25, z 16.75)으로 +90° 회전, 경첩 2개 참조구성 열림.
#  - S00000MU0: 구성 「뚜껑열림」(상승 기준) 추가 → S30000MU0-1 참조구성 뚜껑열림.
# 저장은 sw_save로 별도.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
ANG=math.pi/2
PIN_Y=814.25; PIN_Z=16.75
def rows_apply_Rx90(R):   # 행 = 파트축의 어셈 이미지; Rx(+90): (x,y,z)->(x,-z,y)
    return [[r[0],-r[2],r[1]] for r in R]
def rot_t(t):
    dy=t[1]-PIN_Y; dz=t[2]-PIN_Z
    return [t[0], PIN_Y-dz, PIN_Z+dy]
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
tlb=pythoncom.LoadTypeLib(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\swconst.tlb")
def enum(name):
    for i in range(tlb.GetTypeInfoCount()):
        if tlb.GetDocumentation(i)[0]==name:
            ti=tlb.GetTypeInfo(i); ta=ti.GetTypeAttr(); return {ti.GetNames(ti.GetVarDesc(k).memid)[0]:ti.GetVarDesc(k).value for k in range(ta.cVars)}
    return {}
E_CFG=enum("swInConfigurationOpts_e"); THIS=E_CFG.get("swThisConfiguration",1); SPEC=E_CFG.get("swSpecifyConfiguration",3)
# ---------- 1) 경첩 파트
PH=os.path.join(Z,"C-HHSN65A_hinge.SLDPRT"); h=app.GetOpenDocumentByName(PH)
if h is None: h=open_doc(app,PH,1)
app.ActivateDoc3(PH,False,0,I4()); h=app.ActiveDoc
if "열림" not in list(pv(h,"GetConfigurationNames")):
    c=h.AddConfiguration3("열림","뚜껑 열림(리프1 +90° 회전)","",0); print("hinge config 열림 added",c is not None)
h.ShowConfiguration2("열림"); h.EditRebuild3
if h.FeatureByName("리프1_열림회전") is None:
    body=[b for b in pv(h,"GetBodies2",0,True) if b.Name=="리프1_90도장착"][0]
    h.ClearSelection2(True); sd=h.SelectionManager.CreateSelectData; sd.Mark=1; print("select leaf",body.Select2(False,sd))
    mv=h.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0, 0.0,0.00425,0.015, 1.0,0.0,0.0, ANG, False,1)
    print("rotate feature",mv.Name if mv else None); mv.Name="리프1_열림회전"; h.EditRebuild3
    f=h.FeatureByName("리프1_열림회전")
    print("suppress in 기본 ->",f.SetSuppression2(0,SPEC,VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR,["기본"])))
for cfg in ("기본","열림"):
    h.ShowConfiguration2(cfg); h.EditRebuild3
    print(f" hinge [{cfg}] bodies",[(b.Name,[round(v*1000,1) for v in pv(b,'GetBodyBox')]) for b in pv(h,"GetBodies2",0,True)])
h.ShowConfiguration2("기본"); h.EditRebuild3
cpm=h.Extension.CustomPropertyManager(""); cpm.Set2("REMARK",(cpm.Get("REMARK") or "")+" | 2026-09-09 구성 열림: 리프1 +90° 회전(뚜껑 열림 표현)")
# ---------- 2) S30000MU0
PT=os.path.join(Z,"S30000MU0.SLDASM"); a=app.GetOpenDocumentByName(PT); app.ActivateDoc3(PT,False,0,I4()); a=app.ActiveDoc
cm=a.ConfigurationManager; a.ShowConfiguration2("상승"); a.EditRebuild3
if "뚜껑열림" not in list(pv(a,"GetConfigurationNames")):
    c=a.AddConfiguration3("뚜껑열림","주입구 뚜껑 S30008 90° 열림(라인 상승 상태)","",0); print("tank config 뚜껑열림 added",c is not None)
a.ShowConfiguration2("뚜껑열림"); a.EditRebuild3; assert cm.ActiveConfiguration.Name=="뚜껑열림"
title=a.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
cc=comps()
# 메이트 억제(이 구성만)
a.ClearSelection2(True); ok=a.Extension.SelectByID2("묶기26","MATE",0,0,0,False,0,NOD,0); print("select 묶기26",ok); print("suppress mate",a.EditSuppress2); a.ClearSelection2(True); a.EditRebuild3
# 경첩 참조구성
for n in ("C-HHSN65A_hinge-1","C-HHSN65A_hinge-2"):
    cc[n].ReferencedConfiguration="열림"; print(n,"refcfg ->",cc[n].ReferencedConfiguration)
# 뚜껑 회전
lid=cc["S30008MU0-5"]; xf=xform(lid); set_T(lid,rows_apply_Rx90(xf["R"]),rot_t(xf["t_mm"]))
# 걸쇠 회전(고정 → 풀고 이동 후 다시 고정)
latch=cc["C-1170-2S_latch-1"]
a.ClearSelection2(True); latch.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
xf=xform(latch); set_T(latch,rows_apply_Rx90(xf["R"]),rot_t(xf["t_mm"]))
a.ClearSelection2(True); latch.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
a.ForceRebuild3(False); cc=comps()
for n in ("S30008MU0-5","C-1170-2S_latch-1","C-HHSN65A_hinge-1","C-HHSN65A_hinge-2","S30012MU0-1","S30007MU0-2","염수주입라인-1"):
    c=cc[n]; print(f" [뚜껑열림] {n:20s} refcfg={c.ReferencedConfiguration} fixed={c.IsFixed} t={xform(c)['t_mm']} box={box(c)}")
# 다른 구성 불변 확인
for cfg in ("상승","하강","기본"):
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    print(f" [{cfg}] lid t={xform(cc['S30008MU0-5'])['t_mm']} hinge refcfg={cc['C-HHSN65A_hinge-1'].ReferencedConfiguration} latch t={xform(cc['C-1170-2S_latch-1'])['t_mm']}")
# 간섭: 뚜껑열림에서 뚜껑·걸쇠·경첩 vs 탱크 상판·주입구 프레임·가스켓·패드
a.ShowConfiguration2("뚜껑열림"); a.EditRebuild3; cc=comps()
a.ClearSelection2(True)
for n in ("S30008MU0-5","C-1170-2S_latch-1","C-HHSN65A_hinge-1","C-HHSN65A_hinge-2","S30006MU0-1","S30007MU0-2","S30012MU0-1","S30017MU0-1"): cc[n].Select4(True,NOD,False)
idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
ints=pv(idm,"GetInterferences") or []
rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in ints]; idm.Done(); a.ClearSelection2(True)
print(" 뚜껑열림 간섭:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3
# ---------- 3) S00000MU0
PS=os.path.join(Z,"S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PS); app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc
scm=s.ConfigurationManager; s.ShowConfiguration2("상승"); s.EditRebuild3
if "뚜껑열림" not in list(pv(s,"GetConfigurationNames")):
    c=s.AddConfiguration3("뚜껑열림","탱크 뚜껑 열림(S30000MU0 뚜껑열림 참조, 라인 상승)","",0); print("station config 뚜껑열림 added",c is not None)
s.ShowConfiguration2("뚜껑열림"); s.EditRebuild3
sc={c.Name2:c for c in pv(scm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
sc["S30000MU0-1"].ReferencedConfiguration="뚜껑열림"; s.ForceRebuild3(False)
sc={c.Name2:c for c in pv(scm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
print(" station [뚜껑열림] tank refcfg",sc["S30000MU0-1"].ReferencedConfiguration,"tank box",box(sc["S30000MU0-1"]))
for cfg in ("상승","하강"):
    s.ShowConfiguration2(cfg); s.EditRebuild3
    sc={c.Name2:c for c in pv(scm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
    print(f" station [{cfg}] tank refcfg",sc["S30000MU0-1"].ReferencedConfiguration)
s.ShowConfiguration2("하강"); s.EditRebuild3
json.dump({"interference_lid_open":rows},open(os.path.join(VER,"lid_open_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("done; NOT saved: hinge part, S30000MU0, S00000MU0")
stop.set()
