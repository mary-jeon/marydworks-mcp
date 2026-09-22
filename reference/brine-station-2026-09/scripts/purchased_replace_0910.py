# 2026-09-10: 구매품 3D 교체 2차 — 염수주입라인.SLDASM
#  J2→J2c(×2), G11e→G11f, J11d→J11e(×2), G3b→G3c(Tameson 형상 대용, 면간 83·패드 43.5)
#  스택 조정: H16-10(고정 니플) z −114→−117, 호스 고정단 NIP_FIX_END −144→−147, B4c(KE002) (0,−48,−74.5)→(0,−43.5,−76)
#  호스: 하강 일직선 L356→L353(스케치 제자리 편집 후 SaveAs), 상승 활 재해(뉴턴법) 후 저장
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
Zp=lambda n: os.path.join(Z,n); mm=lambda v:v/1000.0
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_G=[[0,0,1],[-1,0,0],[0,-1,0]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
AX=70.0; OX=0.0; OY=10.0; ZP_UP=-390.0; ZP_DN=-530.0; HOSE_R=47.0
VALVE_TOP=-34.5; VALVE_L=83.0; PAD_H=43.5
NIP_FIX_TOP=VALVE_TOP-VALVE_L+0.5   # −117
NIP_FIX_END=NIP_FIX_TOP-30.0        # −147
REPL={ # 구 접두어: (새 파일, 참조구성)
 "J2_guide_shaft_MISUMI_PSSFAQ16-590-B10":("J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT",""),
 "G11e_MISUMI_SHCCG8-18.4_pin":("G11f_MISUMI_SHCCG8-22.8_pin.SLDPRT",""),
 "J11d_MISUMI_SHCCG8-20.4_pin":("J11e_MISUMI_SHCCG8-18_pin.SLDPRT",""),
 "G3b_valve_3PC_3-4in_ISO_F03F04_SUS":("G3c_valve_3PC_3-4in_ISO_Tameson_BL2SA3-034.SLDPRT",""),
}
for v in REPL.values(): assert os.path.exists(Zp(v[0])), v[0]
# ---------- 호스 해 (stroke140_0910.py와 동일 규약)
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
D_DN=NIP_FIX_END-(ZP_DN+30.0); D_UP=NIP_FIX_END-(ZP_UP+30.0)   # 353, 213
def dn_list(p): a,t=p; return [("arc",HOSE_R,a),("line",2*t),("arc",HOSE_R,-a)]
def sc_dn(p):
    if p[0]<0 or p[1]<0: return 1e6
    s,(ex,ey)=segs_from(dn_list(p)); return math.hypot(ex-OY,ey+D_DN)
v,(a_dn,t_dn)=climb(sc_dn,[0.03,170.0],[0.01,10.0]); segs_dn,end_dn=segs_from(dn_list([a_dn,t_dn])); L_HOSE=seglen(segs_dn)
def up_list(p): R,t1,t2=p; return [("arc",R,t1),("arc",R,-t1),("arc",R,-t2),("arc",R,t2)]
def sc_vec(p):
    s,(ex,ey)=segs_from(up_list(p)); return (ex-OY, ey+D_UP, seglen(s)-L_HOSE)
best=(1e9,None)
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
v2,(R_up,t1,t2)=best; segs_up,end_up=segs_from(up_list([R_up,t1,t2])); bul=max(abs(p[0]) for s in segs_up for p in (s[1],s[2],s[3]) if s[0]=="arc")
print(f"dn: resid {v:.4f} a {math.degrees(a_dn):.2f}° line {2*t_dn:.1f} L {L_HOSE:.2f} | up: resid {v2:.4f} R {R_up:.1f} θ1 {math.degrees(t1):.1f} θ2 {math.degrees(t2):.1f} bulge {bul:.1f}")
assert v<0.5 and v2<0.5
NAME_DN=f"J19e_hose_3-4in_dn_straight_L{round(L_HOSE)}.SLDPRT"; NAME_UP=f"J19e_hose_3-4in_up_bow_R{round(R_up)}.SLDPRT"
OLD_DN="J19e_hose_3-4in_dn_straight_L356.SLDPRT"; OLD_UP="J19e_hose_3-4in_up_bow_R54.SLDPRT"
json.dump({"NIP_FIX_END":NIP_FIX_END,"D_DN":D_DN,"D_UP":D_UP,"L":L_HOSE,"dn":{"a_deg":math.degrees(a_dn),"line":2*t_dn},"up":{"R":R_up,"t1_deg":math.degrees(t1),"t2_deg":math.degrees(t2),"bulge":bul},"names":[NAME_DN,NAME_UP],"segs_dn":segs_dn,"segs_up":segs_up},open(os.path.join(VER,"purchased_hose_paths_0910.json"),"w"),indent=1)
if "--solve-only" in sys.argv: raise SystemExit("solve only")
# ---------- SolidWorks
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    feats=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); codes=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); warns=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(feats,codes,warns); return [(f.Name,c) for f,c in zip(feats.value or [],codes.value or [])]
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
        sm.AddToDB=False; sk=h.SketchManager.ActiveSketch
        Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in pv(sk,"GetSketchSegments"))*1000
        h.SketchManager.InsertSketch(True); h.ClearSelection2(True); h.EditRebuild3
        print(f"  {os.path.basename(path)} direction={direction}: sketch length {Ls:.2f} (target {target_len:.2f})")
        if abs(Ls-target_len)<1.0: break
    else: raise SystemExit("hose sketch length mismatch "+path)
    h.ForceRebuild3(False); bx=[round(v_*1000,1) for v_ in pv(h,"GetPartBox",True)]; bs=list(pv(h,"GetBodies2",0,True) or []); vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs)
    sw=h.FeatureByName("스윕1"); parents=[p.Name for p in (pv(sw,"GetParents") or [])]
    f=pv(h,"FirstFeature"); sks=[]
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": sks.append(f.Name)
        f=pv(f,"GetNextFeature")
    orphan=[s for s in sks if s not in parents]; wwl=ww(h)
    print(f"  box {bx} bodies {len(bs)} vol {vol:.0f} (A·L {math.pi*(14.1**2-9.5**2)*target_len:.0f}) ww {wwl} orphan {orphan}")
    assert len(bs)==1 and not wwl and not orphan; return h
rep={"hose":{"L":L_HOSE,"R_up":R_up,"names":[NAME_DN,NAME_UP]}}
# ---------- 1) 호스 파트 제자리 편집 + 이름
hd=redraw_path(Zp(OLD_DN),segs_dn,L_HOSE); hu=redraw_path(Zp(OLD_UP),segs_up,seglen(segs_up))
spec_common=f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 최소 굽힘반경 47, 자유길이 {L_HOSE:.1f} + 니플 삽입 2×20 = 절단 약 {round(L_HOSE)+40}"
cp=hd.Extension.CustomPropertyManager(""); cp.Set2("SPEC",spec_common+f". 하강(스트로크 140, 낙차 {D_DN:.0f}, 편심 {OY:g}) 경로: r47 {math.degrees(a_dn):.1f}° + 직선 {2*t_dn:.1f} + r47 −{math.degrees(a_dn):.1f}° (사실상 일직선, 기울기 {math.degrees(a_dn):.1f}°)")
cp=hu.Extension.CustomPropertyManager(""); cp.Set2("SPEC",spec_common+f". 상승(낙차 {D_UP:.0f}) 경로: R{R_up:.1f} {math.degrees(t1):.1f}°/−{math.degrees(t1):.1f}°/−{math.degrees(t2):.1f}°/{math.degrees(t2):.1f}° 4원호 활, +y로 {bul:.0f} 불룩 (최소 굽힘반경 47 대비 R{R_up:.1f})")
for h,old,new in ((hd,OLD_DN,NAME_DN),(hu,OLD_UP,NAME_UP)):
    app.ActivateDoc3(Zp(old),False,0,I4()); h=app.ActiveDoc
    if new!=old:
        assert not os.path.exists(Zp(new)), new
        e=I4(); w=I4(); ok=h.Extension.SaveAs(Zp(new),0,1,NOD,e,w); print("SaveAs",new,ok,e.value)
    else:
        e=I4(); w=I4(); ok=h.Save3(1,e,w); print("Save",new,ok,e.value)
    assert ok
# ---------- 2) 어셈블리
a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def interf(doc,items):
    doc.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=doc.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); doc.ClearSelection2(True); return rows
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
# 2a) 교체(전 인스턴스) — 변환은 유지됨
state={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,c in cc.items():
        if any(n.startswith(k) for k in REPL): state.setdefault(n,{})[cfg]=(c.GetSuppression2,xform(c)["R"],xform(c)["t_mm"])
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
for k,(newf,refcfg) in REPL.items():
    olds=[n for n in cc if n.startswith(k)]; assert olds, k
    if app.GetOpenDocumentByName(Zp(newf)) is None: open_doc(app,Zp(newf),1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False)
    ok=a.ReplaceComponents2(Zp(newf),refcfg,True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace",k,"->",newf,ok); assert ok
    cc=comps()
cc=comps(); newnames={n for n in cc if n.startswith(("J2c_","G11f_","J11e_","G3c_"))}; print("new comps",sorted(newnames))
# 2b) 위치: 교체된 것은 원 위치 복원(안전), 스택 조정
old_by_new={}
for n in newnames:
    base=n.rsplit("-",1)[0]; inst=n.rsplit("-",1)[1]
    for k in REPL:
        if REPL[k][0].startswith(base): old_by_new[n]=k+"-"+inst
MOVES={"H16_hose_nipple_3-4in_short_L30-10":(I3,(0,0,NIP_FIX_TOP)),"B4c_actuator_KOSAPLUS_KE002-F35C11-DC-1":(R_G,(0,-PAD_H,VALVE_TOP-VALVE_L/2))}
rep["cfg"]={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n in newnames:
        oldn=old_by_new.get(n); st=state.get(oldn,{}).get(cfg)
        if st: move_fixed(cc[n],st[1],st[2])
    for n,(R,t) in MOVES.items():
        if n in cc: move_fixed(cc[n],R,t)
    for n,c in cc.items():
        if n.startswith("J19e_hose"): move_fixed(c,R_HOSE,(0,0,NIP_FIX_END))
    a.ForceRebuild3(False); cc=comps()
    # 억제 상태 복원
    for n in newnames:
        oldn=old_by_new.get(n); st=state.get(oldn,{}).get(cfg)
        if st and st[0]==2 and cc[n].GetSuppression2!=2: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
        if st and st[0]!=2 and cc[n].GetSuppression2==2: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps()
    info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(newnames|set(MOVES)|{n for n in cc if n.startswith("J19e_hose")}) if n in cc}
    rep["cfg"][cfg]={"whatswrong":ww(a),"info":info}; print(f"[{cfg}] ww {ww(a)}")
    for n,v in info.items(): print("   ",n,v)
# 2c) 검증
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(a,act_); rep["interf_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs); rep["refs"]=refs
assert not any(r.startswith(("J2_","G11e_","J11d_","G3b_")) or "L356" in r for r in refs), refs
e=I4(); w=I4(); ok=a.Save3(1,e,w); print("save asm",ok,e.value,w.value); rep["save"]=ok
json.dump(rep,open(os.path.join(VER,"purchased_replace_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("replace done")
