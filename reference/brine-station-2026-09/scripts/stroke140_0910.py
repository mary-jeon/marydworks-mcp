# 2026-09-10: 하강 스트로크 120 → 140 복귀(사용자 결정 — HANDOFF §1-25 대기 항목 2).
#  근거: §1-24 배치에서 이동판(x −45~135)이 로봇 커버 실린더 TA2-2H-200 로드 위를 지나지 않음 → §1-16의 120 축소 사유 소멸.
#  1) B9f: D3@로드_하강_이동 120→140 (설치길이 339 ≥ 140+119 = 259 OK, 형상 불변)
#  2) 어셈블리 전 구성: 하강 인스턴스 8개 z −20 (zp −510 → −530), 로드 핀 J11d-2 −485 → −505
#  3) 호스 두 파트의 경로 스케치(스케치1)를 제자리 편집: 하강 일직선 L336→L356, 상승 활 R54→R(재해)
#  저장: 여기서는 Save3 하지 않음 — 검증 후 sw_rename_document(파일명 140/L356/R..)·sw_save로.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
Zp=lambda n: os.path.join(Z,n)
AX=70.0; RY=240.0; OX=0.0; OY=10.0; ZP_UP=-390.0; ZP_DN_OLD=-510.0; ZP_DN=-530.0; STROKE=140.0
NIP_FIX_END=-144.0; HOSE_R=47.0; PIN_ROD_H=25.0
# ---------- 호스 경로 해 (rebuild_ta2_parts_0909.py와 같은 규약)
def segs_from(list_):
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    for it in list_:
        if it[0]=="line":
            dd=it[1]
            if dd<=1e-9: continue
            x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1
        else:
            rad,ang=it[1],it[2]
            if abs(ang)<1e-9: continue
            side=1 if ang>0 else -1
            cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
            h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
            segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    return segs,(x,y)
def seglen(segs): return sum((math.hypot(s[2][0]-s[1][0],s[2][1]-s[1][1]) if s[0]=="line" else abs(s[4])*math.hypot(s[2][0]-s[1][0],s[2][1]-s[1][1])) for s in segs)
def climb(sc,p0,steps,iters=3000):
    p=list(p0); v=sc(p); st=list(steps)
    while max(st)>1e-7 and iters>0:
        imp=False; iters-=1
        for i in range(len(p)):
            for dd in (1,-1):
                q=list(p); q[i]+=dd*st[i]; vq=sc(q)
                if vq<v: v,p=vq,q; imp=True
        if not imp: st=[u/2 for u in st]
    return v,p
D_DN=NIP_FIX_END-(ZP_DN+30.0); D_UP=NIP_FIX_END-(ZP_UP+30.0)   # 356, 216
def dn_list(p): a,t=p; return [("arc",HOSE_R,a),("line",2*t),("arc",HOSE_R,-a)]
def sc_dn(p):
    if p[0]<0 or p[1]<0: return 1e6
    s,(ex,ey)=segs_from(dn_list(p)); return math.hypot(ex-OY,ey+D_DN)
v,(a_dn,t_dn)=climb(sc_dn,[0.03,170.0],[0.01,10.0]); segs_dn,end_dn=segs_from(dn_list([a_dn,t_dn])); L_HOSE=seglen(segs_dn)
print(f"dn path: resid {v:.4f} a {math.degrees(a_dn):.2f}° line {2*t_dn:.1f} end {end_dn} L {L_HOSE:.2f}")
def up_list(p): R,t1,t2=p; return [("arc",R,t1),("arc",R,-t1),("arc",R,-t2),("arc",R,t2)]
def sc_up(p):
    R,t1,t2=p
    if R<HOSE_R or t1<0 or t2<0 or t1>math.pi or t2>math.pi: return 1e6
    s,(ex,ey)=segs_from(up_list(p)); return math.hypot(ex-OY,ey+D_UP)+abs(seglen(s)-L_HOSE)
import numpy as np
def sc_vec(p):
    s,(ex,ey)=segs_from(up_list(p)); return (ex-OY, ey+D_UP, seglen(s)-L_HOSE)
best=(1e9,None)   # 뉴턴법(수치 야코비안) 다중 시작 — 좌표 하강(climb)은 L 356에서 잔차 0.6에 멈춤
for R0 in (50,55,60,70,80,100):
    for t0 in (1.2,1.5,1.7,2.0):
        p=[R0,t0,t0]
        for it in range(60):
            f=sc_vec(p); n=math.sqrt(sum(q*q for q in f))
            if n<1e-6: break
            J=[]
            for i in range(3):
                q=list(p); h=1e-5*max(1,abs(p[i])); q[i]+=h; fq=sc_vec(q); J.append([(fq[k]-f[k])/h for k in range(3)])
            M=[[J[j][i] for j in range(3)] for i in range(3)]
            try: dx=[float(x_) for x_ in np.linalg.solve(np.array(M),-np.array(f))]
            except Exception: break
            lam=1.0
            while lam>1e-4:
                q=[p[i]+lam*dx[i] for i in range(3)]
                if q[0]>=HOSE_R and 0<q[1]<math.pi and 0<q[2]<math.pi and math.sqrt(sum(x_*x_ for x_ in sc_vec(q)))<n: p=q; break
                lam/=2
            else: break
        n=math.sqrt(sum(q*q for q in sc_vec(p)))
        if n<best[0]: best=(n,p)
v2,(R_up,t1,t2)=best; segs_up,end_up=segs_from(up_list([R_up,t1,t2]))
bul=max(abs(p[0]) for s in segs_up for p in (s[1],s[2],s[3]) if s[0]=="arc")
print(f"up bow: resid {v2:.4f} R {R_up:.1f} θ1 {math.degrees(t1):.1f}° θ2 {math.degrees(t2):.1f}° end {end_up} L {seglen(segs_up):.2f} bulge(x) ≈ {bul:.1f}")
if v>0.5 or v2>0.5: raise SystemExit("hose solver residual too large")
NAME_DN=f"J19e_hose_3-4in_dn_straight_L{round(L_HOSE)}"; NAME_UP=f"J19e_hose_3-4in_up_bow_R{round(R_up)}"
json.dump({"stroke":STROKE,"ZP_DN":ZP_DN,"NIP_FIX_END":NIP_FIX_END,"OY":OY,"D_DN":D_DN,"D_UP":D_UP,"L":L_HOSE,"dn":{"a_deg":math.degrees(a_dn),"line":2*t_dn},"up":{"R":R_up,"t1_deg":math.degrees(t1),"t2_deg":math.degrees(t2),"bulge":bul,"resid":v2},"names":[NAME_DN,NAME_UP],"segs_dn":segs_dn,"segs_up":segs_up},open(os.path.join(VER,"stroke140_hose_paths_0910.json"),"w"),indent=1)
if "--solve-only" in sys.argv: raise SystemExit("solve only")
# ---------- SolidWorks
stop=watchdog(); app=connect()
def act(p):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
rep={"stroke":STROKE,"zp_dn":ZP_DN}
# ---------- 1) B9f
PB=Zp("B9f_TiMOTION_TA2-2H-120_RL339_clevisU.SLDPRT"); d=act(PB)
prm=d.Parameter("D3@로드_하강_이동"); print("B9f D3 before",prm.SystemValue*1000)
try: r=prm.SetSystemValue3(mm(STROKE),2,None)
except Exception as ex: print("  SetSystemValue3 exc",ex); prm.SystemValue=mm(STROKE); r="SystemValue"
d.EditRebuild3; val=d.Parameter("D3@로드_하강_이동").SystemValue*1000; print("B9f D3 ->",r,val); assert abs(val-STROKE)<0.01
rep["b9f"]={}
for cfg in ("상승","하강"):
    d.ShowConfiguration2(cfg); d.EditRebuild3
    bs=[(pv(b,'Name'),[round(v_*1000,1) for v_ in pv(b,'GetBodyBox')]) for b in (pv(d,"GetBodies2",0,True) or [])]
    rep["b9f"][cfg]=bs; print(f" B9f [{cfg}]",bs); assert len(bs)==2
assert abs(rep["b9f"]["하강"][0][1][2]-(-464.5-20.0))<0.2, "rod 하강 box"
d.ShowConfiguration2("상승"); d.EditRebuild3; rep["b9f"]["whatswrong"]=ww(d)
cpm=d.Extension.CustomPropertyManager("")
cpm.Set2("TITLE","LINEAR ACTUATOR TiMOTION TA2 (500 N, 스트로크 140, 설치길이 339 지정)")
cpm.Set2("SPEC",cpm.Get("SPEC").replace("TA2-2H-120","TA2-2H-140").replace("스트로크 120,","스트로크 140,").replace("최소 스트로크+119=239","최소 스트로크+119=259"))
cpm.Set2("REMARK",cpm.Get("REMARK").replace("스트로크는 실사용 120 그대로라","스트로크 140(노즐 하강 1,420, 로봇 개구 상단 아래 54)이라"))
print("B9f props",cpm.Get("TITLE"),"|",cpm.Get("SPEC")[:80])
# ---------- 2) 호스 스케치 제자리 편집
def redraw_path(path,segs,target_len):
    h=act(path)
    if h.SketchManager.ActiveSketch is not None: h.SketchManager.InsertSketch(True)
    for direction in (1,-1):
        h.ClearSelection2(True); assert h.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); h.EditSketch()
        sk=h.SketchManager.ActiveSketch; h.ClearSelection2(True); n=0
        for s in list(pv(sk,"GetSketchSegments") or []): s.Select4(True,NOD); n+=1
        if n: h.Extension.DeleteSelection2(0)
        sm=h.SketchManager; sm.AddToDB=True
        for sg in segs:
            if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0)
            else:
                cc_,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]
                sm.CreateArc(mm(cc_[0]),mm(cc_[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
        sm.AddToDB=False
        sk=h.SketchManager.ActiveSketch
        Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
        h.SketchManager.InsertSketch(True); h.ClearSelection2(True); h.EditRebuild3
        print(f"  {os.path.basename(path)} direction={direction}: deleted {n}, sketch length {Ls:.2f} (target {target_len:.2f})")
        if abs(Ls-target_len)<1.0: break
    else: raise SystemExit("hose sketch length mismatch "+path)
    h.ForceRebuild3(False); bx=[round(v_*1000,1) for v_ in pv(h,"GetPartBox",True)]; wwl=ww(h)
    bs=list(pv(h,"GetBodies2",0,True) or []); vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs)
    # 고아 스케치 점검: ProfileFeature 중 스윕의 부모가 아닌 것
    sw=h.FeatureByName("스윕1"); parents=[p.Name for p in (pv(sw,"GetParents") or [])]
    f=pv(h,"FirstFeature"); sks=[]
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": sks.append(f.Name)
        f=pv(f,"GetNextFeature")
    orphan=[s for s in sks if s not in parents]
    print(f"  box {bx} bodies {len(bs)} vol {vol:.0f} whatswrong {wwl} sketches {sks} orphan {orphan}")
    assert len(bs)==1 and not wwl and not orphan, "hose rebuild problem"
    return {"box":bx,"vol":vol,"len":Ls}
rep["hose_dn"]=redraw_path(Zp("J19e_hose_3-4in_dn_straight_L336.SLDPRT"),segs_dn,L_HOSE)
rep["hose_up"]=redraw_path(Zp("J19e_hose_3-4in_up_bow_R54.SLDPRT"),segs_up,seglen(segs_up))
# 기대 길이 검증: 튜브 단면 π(14.1²−9.5²)=341.0 mm² × L
A_sec=math.pi*(14.1**2-9.5**2)
for k in ("hose_dn","hose_up"):
    est=A_sec*L_HOSE; print(f"  {k} vol {rep[k]['vol']:.0f} vs A·L {est:.0f} ({rep[k]['vol']/est*100:.1f} %)")
spec_common=f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 최소 굽힘반경 47, 자유길이 {L_HOSE:.1f} + 니플 삽입 2×20 = 절단 약 {round(L_HOSE)+40}"
hd=app.GetOpenDocumentByName(Zp("J19e_hose_3-4in_dn_straight_L336.SLDPRT")); cp=hd.Extension.CustomPropertyManager("")
cp.Set2("SPEC",spec_common+f". 하강(스트로크 {STROKE:.0f}, 낙차 {D_DN:.0f}, 편심 {OY:g}) 경로: r47 {math.degrees(a_dn):.1f}° + 직선 {2*t_dn:.1f} + r47 −{math.degrees(a_dn):.1f}° (사실상 일직선, 기울기 {math.degrees(a_dn):.1f}°)")
hu=app.GetOpenDocumentByName(Zp("J19e_hose_3-4in_up_bow_R54.SLDPRT")); cp=hu.Extension.CustomPropertyManager("")
cp.Set2("SPEC",spec_common+f". 상승(낙차 {D_UP:.0f}) 경로: R{R_up:.1f} {math.degrees(t1):.1f}°/−{math.degrees(t1):.1f}°/−{math.degrees(t2):.1f}°/{math.degrees(t2):.1f}° 4원호 활, +y로 {bul:.0f} 불룩 (최소 굽힘반경 47 대비 R{R_up:.1f})")
# ---------- 3) 어셈블리: 하강 인스턴스 z −20 (전 구성)
a=act(ASM); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); print("cfgs",CFGS)
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
TARGET={"J5e_moving_plate_180x540_t8-2":(0,0,ZP_DN),"J9d_lug_PL6_40x31-2":(AX,0,ZP_DN),"J11d_MISUMI_SHCCG8-20.4_pin-2":(AX,-10.0,ZP_DN+PIN_ROD_H),
        "G13_weld_socket_3-4in_L25-11":(OX,OY,ZP_DN),"H16_hose_nipple_3-4in_short_L30-12":(OX,OY,ZP_DN+30),"J17_pipe_3-4in_L100-4":(OX,OY,ZP_DN),
        "B10_linear_bushing_MISUMI_LHFRW16-23":(AX,RY,ZP_DN),"B10_linear_bushing_MISUMI_LHFRW16-24":(AX,-RY,ZP_DN)}
rep["asm"]={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,nt in TARGET.items():
        c=cc[n]; t0=xform(c)["t_mm"]
        if abs(t0[2]-nt[2])<0.05: continue   # 고정 컴포넌트 Transform2는 전 구성 공통 — 이미 새 위치면 건너뜀
        assert abs(t0[2]-(nt[2]+20.0))<0.05, f"{n} unexpected z {t0} in {cfg}"   # 구 위치(−510 기준)에서만 이동
        move_fixed(c,xform(c)["R"],nt)
    a.ForceRebuild3(False); cc=comps()
    bad=[(n,xform(cc[n])["t_mm"]) for n,nt in TARGET.items() if any(abs(p-q)>0.05 for p,q in zip(xform(cc[n])["t_mm"],nt))]
    print(f"[{cfg}] mismatches {bad} whatswrong {ww(a)}"); assert not bad
    rep["asm"][cfg]={"whatswrong":ww(a)}
# ---------- 4) 검증: 상승/하강 박스·간섭
def interf(doc,items):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_={n:c for n,c in cc.items() if c.GetSuppression2==2}
    boxes={n:box(c) for n,c in act_.items()}; rows=interf(a,list(act_.values()))
    rep["asm"][cfg].update({"boxes":boxes,"interf":rows})
    print(f"[{cfg}] active {len(act_)} 간섭 {len(rows)}:",rows)
    for n in ("J5e_moving_plate_180x540_t8-1","J5e_moving_plate_180x540_t8-2","J17_pipe_3-4in_L100-3","J17_pipe_3-4in_L100-4","B9f_TiMOTION_TA2-2H-120_RL339_clevisU-1","J19e_hose_3-4in_dn_straight_L336-1","J19e_hose_3-4in_up_bow_R54-1"):
        if n in boxes: print("   ",n,boxes[n])
a.ShowConfiguration2("상승"); a.EditRebuild3
json.dump(rep,open(os.path.join(VER,"stroke140_build_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("stroke140 build done (NOT saved) — next: sw_rename_document ×3 → sw_save")
