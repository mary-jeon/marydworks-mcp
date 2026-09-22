# 2026-09-09: 걸쇠 C-1170-2S 받이(키퍼) 정렬
#  사용자: 「LATCH 저부분 홀 맞춰서 정렬해줘」
#  실측: STEP 키퍼 홀(월드 z −483) vs 뚜껑 홀(z −481) 2 mm 어긋남 + 키퍼가 본체와 한 파트라 뚜껑 열림 구성에서 뚜껑을 따라가지 못함.
#  조치: ① 키퍼 바디를 별도 파트 C-1170-2S_keeper.SLDPRT로 분리(원점 = 홀 중심선) ② 래치 파트에서 키퍼 바디 삭제
#        ③ 래치 본체 z −522 → −520, 패드 S30017 탭홀 스케치 제자리 편집(+2) ④ 키퍼 인스턴스 2개(닫힘/열림) 구성별 억제
import os,sys,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
mm=lambda v:v/1000.0
tmpl=app.GetUserPreferenceStringValue(8)
Zp=lambda n: os.path.join(Z,n)
PL=Zp("C-1170-2S_latch.SLDPRT"); PK=Zp("C-1170-2S_keeper.SLDPRT"); PP=Zp("S30017MU0.SLDPRT"); PA=Zp("S30000MU0.SLDASM")
KEEPER_BODY="C-1170-2S_1___-1-solid1"; DZ=2.0
def partbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def cyls(d,r,tol=0.05):
    out=[]
    for b in bodies(d):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<tol: out.append([round(v*1000,1) for v in fc.GetBox])
    return out
def act(p):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,1 if p.lower().endswith("sldprt") else 2)
    app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def save(d):
    e=I4(); w=I4(); ok=d.Save3(1,e,w); print("  save",d.GetTitle,ok); return ok
# ---------- 1) 키퍼 분리
lp=act(PL); lcpm=lp.Extension.CustomPropertyManager("")
lprops={n:lcpm.Get(n) for n in (pv(lcpm,"GetNames") or [])}; print("latch props",lprops)
if not os.path.exists(PK):
    kb=[b for b in bodies(lp) if b.Name==KEEPER_BODY][0]
    print("keeper body box",[round(v*1000,1) for v in pv(kb,"GetBodyBox")])
    bc=kb.Copy()
    k=app.NewDocument(tmpl,0,0,0)
    f=k.CreateFeatureFromBody3(bc,False,0); print("keeper feature",f.Name if f else None)
    k.EditRebuild3; print("keeper box raw",partbox(k))
    # 원점 정렬: 홀 중심선(x 39)을 x 0으로
    b0=bodies(k)[0]; k.ClearSelection2(True); sd=k.SelectionManager.CreateSelectData; sd.Mark=1; print("sel",b0.Select2(False,sd))
    mv=k.FeatureManager.InsertMoveCopyBody2(mm(-39.0),0.0,0.0, 0.0, 0.0,0.0,0.0, 0.0,0.0,0.0, False,1)
    if mv: mv.Name="원점정렬_홀중심"
    k.EditRebuild3; print("keeper box aligned",partbox(k))
    mat=lp.GetMaterialPropertyName2("",None) if False else None
    try:
        db=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BSTR,""); name=lp.GetMaterialPropertyName2("",db); print("latch material",name,db.value)
        k.SetMaterialPropertyName2("",db.value,name)
    except Exception as ex: print("material copy failed",ex)
    kc=k.Extension.CustomPropertyManager("")
    kc.Set2("TITLE","LATCH KEEPER (C-1170-2S)"); kc.Set2("SPEC","TAKIGEN C-1170-2S 받이(키퍼) 12×39×12, 2-Ø3.4 P29 (본체와 세트 구매)")
    for n,v in lprops.items():
        if n in ("MATERIAL","QT'Y","MAKER","VENDOR","UNIT"): kc.Set2(n,v)
    kc.Set2("QT'Y","1"); kc.Set2("REMARK","뚜껑 S30008MU0 −z 테두리 홀 2-Ø3.4에 M3 접시머리 볼트 체결. 본체 C-1170-2S_latch는 패드 S30017 위")
    print("saveas",k.SaveAs3(PK,0,1), os.path.exists(PK))
k=act(PK); print("keeper box",partbox(k),"holes r1.7",cyls(k,1.7))
# 래치 파트에서 키퍼 바디 삭제
lp=act(PL)
if any(b.Name==KEEPER_BODY for b in bodies(lp)):
    lp.ClearSelection2(True); ok=lp.Extension.SelectByID2(KEEPER_BODY,"BODYFEATURE",0,0,0,False,0,NOD,0); print("select keeper feat",ok)
    print("delete",lp.Extension.DeleteSelection2(0)); lp.EditRebuild3
print("latch bodies",[(b.Name,[round(v*1000,1) for v in pv(b,'GetBodyBox')]) for b in bodies(lp)],"box",partbox(lp))
lcpm.Set2("REMARK","받이(키퍼)는 별도 파트 C-1170-2S_keeper(뚜껑 측). 본체 4-M3 34×25는 패드 S30017 탭홀에 체결")
save(lp); save(k)
# ---------- 2) 패드 탭홀 스케치 +2 (제자리 편집)
pd=act(PP)
if pd.SketchManager.ActiveSketch is not None: pd.SketchManager.InsertSketch(True)
pd.EditRebuild3; holes_before=cyls(pd,1.25); print("pad holes before",holes_before)
pd.ClearSelection2(True); print("sel sketch4",pd.Extension.SelectByID2("스케치4","SKETCH",0,0,0,False,0,NOD,0)); pd.EditSketch()
sk=pd.SketchManager.ActiveSketch; segs=list(pv(sk,"GetSketchSegments") or [])
arcs=[s for s in segs if (s.GetType() if callable(s.GetType) else s.GetType)==1]
ctrs=[]
for s in arcs:
    a=s.GetSpecificFeature2 if False else None
    cp=pv(s,"GetCenterPoint2")
    try: cx,cy=cp[0],cp[1]
    except TypeError: cx,cy=pv(cp,"X"),pv(cp,"Y")
    ctrs.append((cx*1000,cy*1000,pv(s,"GetRadius")*1000))
print("arc centers",[(round(x,2),round(y,2),round(r,2)) for x,y,r in ctrs])
zs=sorted(set(round((b[2]+b[5])/2,1) for b in holes_before)); print("hole z(part) before",zs)
sy=1 if all(y>0 for _,y,_ in ctrs) else -1
if abs(zs[0]-11)<0.6:
    pd.ClearSelection2(True)
    for s in arcs: s.Select4(True,NOD)
    pd.Extension.DeleteSelection2(0); sm=pd.SketchManager; sm.AddToDB=True
    for x,y,r in ctrs: sm.CreateCircleByRadius(mm(x),mm(y+sy*DZ),0,mm(r))
    sm.AddToDB=False; pd.SketchManager.InsertSketch(True); pd.EditRebuild3
else:
    pd.SketchManager.InsertSketch(True)
ha=cyls(pd,1.25); print("pad holes after",ha,"z",sorted(set(round((b[2]+b[5])/2,1) for b in ha)))
assert len(ha)==4 and all(any(abs((b[2]+b[5])/2-zz)<0.6 for zz in (13,47)) for b in ha),"pad holes not at 13/47"
pc=pd.Extension.CustomPropertyManager(""); pc.Set2("SPEC","STS 316 40x60x30 블록, 상판 S30006 위 용접(걸쇠 C-1170-2 본체 받침, 상면 = 뚜껑 상면 높이). 4×M3 탭 P1 34×P2 25")
save(pd)
# ---------- 3) 어셈블리
a=act(PA); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); print("cfgs",CFGS)
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def RT(comp):
    A=list(comp.Transform2.ArrayData); return np.array(A[0:9]).reshape(3,3),np.array(A[9:12])*1000
def sel_comp(name):
    a.ClearSelection2(True); return a.Extension.SelectByID2(name+"@"+a.GetTitle.replace(".SLDASM",""),"COMPONENT",0,0,0,False,0,NOD,0)
R_L=np.array([[0,0,1],[1,0,0],[0,1,0]],float); T_L=np.array([237.5,840.0,-520.0])
T_K=np.array([237.5,840.0,-481.0])
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
R5,t5=RT(cc["S30008MU0-5"])
a.ShowConfiguration2("뚜껑열림"); a.EditRebuild3; cc=comps()
R6,t6=RT(cc["S30008MU0-6"]); print("lid closed",t5,"open",t6,R6.tolist())
R_KO=R_L@R6; T_KO=(T_K-t5)@R6+t6; print("keeper open R",R_KO.round(3).tolist(),"t",T_KO.round(2))
# 래치 이동(모든 구성)
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps(); move_fixed(cc["C-1170-2S_latch-1"],R_L.tolist(),T_L.tolist())
# 키퍼 인스턴스
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
names=[n for n in cc if n.startswith("C-1170-2S_keeper-")]
if len(names)<2:
    for i in range(2-len(names)):
        c=a.AddComponent5(PK,0,"",False,"",0.0,0.0,0.0); print("added",c.Name2)
    a.ForceRebuild3(False); cc=comps(); names=sorted([n for n in cc if n.startswith("C-1170-2S_keeper-")])
kc_,ko_=names[0],names[1]; print("keeper closed/open =",kc_,ko_)
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    move_fixed(cc[kc_],R_L.tolist(),T_K.tolist()); move_fixed(cc[ko_],R_KO.tolist(),T_KO.tolist())
    for n,on in ((kc_,cfg!="뚜껑열림"),(ko_,cfg=="뚜껑열림")):
        sel_comp(n)
        if on: a.EditUnsuppress2
        else: a.EditSuppress2
    a.ClearSelection2(True); a.ForceRebuild3(False); cc=comps()
    print(f"[{cfg}] latch t={RT(cc['C-1170-2S_latch-1'])[1].round(1)} {kc_} supp={cc[kc_].GetSuppression2} {ko_} supp={cc[ko_].GetSuppression2}")
# ---------- 4) 검증
def w(R,t,p): return (np.array(p)@R+t).round(1).tolist()
def holes(comp,r):
    R,t=RT(comp); out=[]
    part=comp.GetModelDoc2
    for b in (pv(part,"GetBodies2",0,True) or []):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<0.05:
                fb=[v*1000 for v in fc.GetBox]; out.append(w(R,t,[(fb[0]+fb[3])/2,(fb[1]+fb[4])/2,(fb[2]+fb[5])/2]))
    return sorted(out)
res={}
for cfg,lid,kp in (("상승","S30008MU0-5",kc_),("뚜껑열림","S30008MU0-6",ko_)):
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    print(f"[{cfg}] lid holes",holes(cc[lid],1.7)); print(f"[{cfg}] keeper holes",holes(cc[kp],1.7))
    print(f"[{cfg}] keeper box",box(cc[kp]),"latch box",box(cc["C-1170-2S_latch-1"]),"pad holes",holes(cc["S30017MU0-1"],1.25))
    a.ClearSelection2(True)
    for n in [lid,kp,"C-1170-2S_latch-1","S30017MU0-1","S30006MU0-1","S30007MU0-2","S30012MU0-1","C-HHSN65A_hinge-1","C-HHSN65A_hinge-2"]: cc[n].Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True)
    print(f"[{cfg}] 간섭:",rows); res[cfg]={"lid_holes":holes(cc[lid],1.7),"keeper_holes":holes(cc[kp],1.7),"keeper_box":box(cc[kp]),"latch_box":box(cc["C-1170-2S_latch-1"]),"interf":rows}
a.ShowConfiguration2("상승"); a.EditRebuild3
save(a)
json.dump(res,open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증","latch_keeper_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("done")
