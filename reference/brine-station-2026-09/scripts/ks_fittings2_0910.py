# 2026-09-10: 관이음 재구성 2차 — 나사 물림을 ISO 7-1 기준(R3/4 손조임 9.5 + 조립여유 ≤5 → 13 가정)으로 모델링하면 상승 호스 R 45 < 47.
#  → 고정판 쪽 소켓(Rp L36)+클로즈니플(L35)을 **배럴 니플 R3/4 L38(KS B 1533 부표1, 한쪽 판에 10 삽입 용접)** 하나로 교체(이음 1곳 감소, 스택 −21).
#  물림 13 반영: 호스니플 노출 나사 14, J17은 소켓 바닥에서 13 물림(상단 ZP−23, L77로 단축), 밸브 상단 −25(니플 노출 15).
#  호스: 고정단 −145.5, 이동단 ZP+37.5 → 낙차 하강 347/상승 207 → 상승 활 R ≈ 52.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
Zp=lambda n: os.path.join(Z,n); mm=lambda v:v/1000.0
I3=[[1,0,0],[0,1,0],[0,0,1]]; R_FLIP=[[1,0,0],[0,-1,0],[0,0,-1]]; R_G=[[0,0,1],[-1,0,0],[0,-1,0]]; R_HOSE=[[0,1,0],[0,0,1],[1,0,0]]
OY=10.0; ZP_UP=-390.0; ZP_DN=-530.0; HOSE_R=47.0
ENG=13.0                     # R/Rc 물림 가정(ISO 7-1: 손조임 9.5, 유효 최소 14.5)
BN_L=38.0; BN_IN=10.0        # 배럴 니플 L38, 판(t10) 안으로 10 삽입
HN_THR=27.0; HN_HEX=6.0; HN_BARB=17.5; SOCK_L=36.0; VALVE_L=83.0; PAD_H=43.5; J17_L=77.0
Z_VALVE_TOP=-(BN_L-BN_IN-ENG)-10.0+0.0   # 판 상면 0, 니플 상단 0 → 니플 하단 −38, 밸브 상단 = 니플 하단 + 13 = −25
Z_VALVE_TOP=-BN_L+ENG                      # −25
Z_VALVE_BOT=Z_VALVE_TOP-VALVE_L            # −108
Z_B4C=Z_VALVE_TOP-VALVE_L/2                # −66.5
Z_HN_FIX=Z_VALVE_BOT+ENG-HN_THR            # 호스니플 원점(육각 상면) = 밸브 하단 + 13 − 27 = −122
NIP_FIX_END=Z_HN_FIX-HN_HEX-HN_BARB        # −145.5
MOV_ORG=HN_THR-ENG                         # 이동 호스니플 원점 ZP+14
MOV_END=MOV_ORG+HN_HEX+HN_BARB             # ZP+37.5
J17_TOP=-SOCK_L+ENG                        # ZP−23
print("stack: barrel nipple 0~-38, valve",Z_VALVE_TOP,"~",Z_VALVE_BOT,"B4c z",Z_B4C,"HN fix org",Z_HN_FIX,"fix end",NIP_FIX_END,"mov org/end ZP+",MOV_ORG,MOV_END,"J17 top ZP",J17_TOP)
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
D_DN=NIP_FIX_END-(ZP_DN+MOV_END); D_UP=NIP_FIX_END-(ZP_UP+MOV_END)
def dn_list(p): a,t=p; return [("arc",HOSE_R,a),("line",2*t),("arc",HOSE_R,-a)]
def sc_dn(p):
    if p[0]<0 or p[1]<0: return 1e6
    s,(ex,ey)=segs_from(dn_list(p)); return math.hypot(ex-OY,ey+D_DN)
v,(a_dn,t_dn)=climb(sc_dn,[0.03,165.0],[0.01,10.0]); segs_dn,_=segs_from(dn_list([a_dn,t_dn])); L_HOSE=seglen(segs_dn)
def up_list(p): R,t1,t2=p; return [("arc",R,t1),("arc",R,-t1),("arc",R,-t2),("arc",R,t2)]
def sc_vec(p):
    s,(ex,ey)=segs_from(up_list(p)); return (ex-OY, ey+D_UP, seglen(s)-L_HOSE)
best=(1e9,None)
for R0 in (45,50,55,60,70,100):
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
v2,(R_up,t1,t2)=best; segs_up,_=segs_from(up_list([R_up,t1,t2])); bul=max(abs(p[0]) for s in segs_up for p in (s[1],s[2],s[3]) if s[0]=="arc")
print(f"hose: D_DN {D_DN} D_UP {D_UP} L {L_HOSE:.2f} | up R {R_up:.1f} bulge {bul:.1f} resid {v:.4f}/{v2:.4f}")
assert v<0.5 and v2<0.5 and R_up>=HOSE_R
NAME_DN=f"J19e_hose_3-4in_dn_straight_L{round(L_HOSE)}.SLDPRT"; NAME_UP=f"J19e_hose_3-4in_up_bow_R{round(R_up)}.SLDPRT"
OLD_DN="J19e_hose_3-4in_dn_straight_L354.SLDPRT"; OLD_UP="J19e_hose_3-4in_up_bow_R53.SLDPRT"
json.dump({"ENG":ENG,"NIP_FIX_END":NIP_FIX_END,"MOV_END":MOV_END,"D_DN":D_DN,"D_UP":D_UP,"L":L_HOSE,"up":{"R":R_up,"t1":math.degrees(t1),"t2":math.degrees(t2),"bulge":bul},"stack":{"valve_top":Z_VALVE_TOP,"valve_bot":Z_VALVE_BOT,"b4c_z":Z_B4C,"hn_fix_org":Z_HN_FIX,"j17_top":J17_TOP},"names":[NAME_DN,NAME_UP]},open(os.path.join(VER,"ks_fittings2_hose_0910.json"),"w"),indent=1)
if "--solve-only" in sys.argv: raise SystemExit("solve only")
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def extrude(d,depth,up,name):
    f=d.FeatureManager.FeatureExtrusion3(True,False,(not up),0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
    assert f is not None, "extrude "+name; f.Name=name; return f
def cut_all(d,name):
    f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    assert f is not None, "cut "+name; f.Name=name; return f
# ---- 배럴 니플 G13c
P_BN=Zp("G13c_barrel_nipple_R3-4_KS_L38.SLDPRT")
if not os.path.exists(P_BN):
    d=app.NewDocument(tmpl,0,0,0)
    new_sketch(d,"정면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(13.2))); extrude(d,BN_L,False,"니플_OD26.4_L38")
    new_sketch(d,"정면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(10.0))); cut_all(d,"보어_D20")
    bx=bbox(d); print("G13c box",bx,"ww",ww(d)); assert abs(bx[2]+BN_L)<0.1 and not ww(d)
    cp=d.Extension.CustomPropertyManager("")
    for k,v_ in {"TITLE":"BARREL NIPPLE R3/4 (KS B 1533) — 고정판 용접","SPEC":"KS B 1533 배럴 니플 20A(3/4): 수나사 R3/4 양쪽(KS B 0222), SUS304, L ≥ 38(모델 38), OD 26.4, 보어 20. 한쪽 끝을 고정판 J1c 구멍(Ø27)에 10 삽입해 밑면 둘레 필릿 용접(그쪽 나사는 용접으로 소멸), 반대쪽을 밸브 상단 암나사에 물림 13(ISO 7-1: 손조임 9.5 + 조립여유 ≤5). 나사 미표현. 파트 좌표: 판 상면 = 상단 z 0, 축 −Z","MATERIAL":"STS304","QT'Y":"1","DATE":"2026-09-10","REMARK":"종전 「용접 소켓(Rp) + 클로즈 니플(R)」 2점을 1점으로: 이음 1곳 감소, 고정 스택 21 단축 → 상승 호스 굽힘반경 45→52 확보. 밸브 상단이 Rc(PT)이면 그대로, G(PF)면 니플을 PF 수나사 배럴로(태성 20S3 나사 확인 후)"}.items(): cp.Add3(k,30,v_,1)
    try: d.SetMaterialPropertyName2("","이텍","STS 304")
    except Exception: pass
    e=I4(); w=I4(); ok=d.Extension.SaveAs(P_BN,0,1,NOD,e,w); print("saved G13c",ok); assert ok
# ---- J17 → L77 (제자리 치수 변경 후 SaveAs)
P17=Zp("J17_pipe_3-4in_L100.SLDPRT"); P17b=Zp("J17b_pipe_3-4in_L77.SLDPRT")
if not os.path.exists(P17b):
    d=act(P17); print("J17 feats",[f for f in feats(d) if f[1] in ("Extrusion","ICE","ProfileFeature")],"box",bbox(d))
    done=False
    for n,t in feats(d):
        if t in ("Extrusion","ICE"):
            ft=d.FeatureByName(n); dd=pv(ft,"GetFirstDisplayDimension")
            while dd:
                dim=dd.GetDimension2(0); val=dim.SystemValue*1000
                if abs(val-100.0)<0.05:
                    try: dim.SetSystemValue3(mm(J17_L),2,None)
                    except Exception: dim.SystemValue=mm(J17_L)
                    d.EditRebuild3; print("  J17",dim.FullName,"100 ->",dim.SystemValue*1000); done=True; break
                dd=pv(ft,"GetNextDisplayDimension",dd)
            if done: break
    bx=bbox(d); assert done and abs((bx[5]-bx[2])-J17_L)<0.1, bx
    cp=d.Extension.CustomPropertyManager(""); s=cp.Get("SPEC") or ""; cp.Set2("SPEC",s.replace("L100","L77").replace("100","77") if "L100" in s else s+" | L77(소켓 바닥에서 13 물림, 노즐 끝 위치 불변)")
    e=I4(); w=I4(); ok=d.Extension.SaveAs(P17b,0,1,NOD,e,w); print("SaveAs J17b",ok,e.value); assert ok
# ---- J1c 유로 구멍 Ø28 → Ø27
d=act(Zp("J1c_fixed_plate_185x580_t10.SLDPRT"))
if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치3","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
for s in list(pv(sk,"GetSketchSegments") or []):
    ty=s.GetType() if callable(s.GetType) else s.GetType
    if ty==1:
        cp_=pv(s,"GetCenterPoint2")
        try: cx,cy=cp_[0]*1000,cp_[1]*1000
        except TypeError: cx,cy=pv(cp_,"X")*1000,pv(cp_,"Y")*1000
        r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
        if abs(cx)<0.5 and abs(cy)<0.5 and abs(r-14)<0.1: s.Select4(True,NOD); n+=1
if n: d.Extension.DeleteSelection2(0); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(13.5)); d.SketchManager.AddToDB=False
d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); print("J1c hole edited",n,"ww",ww(d)); assert not ww(d)
cp=d.Extension.CustomPropertyManager(""); s=cp.Get("SPEC") or ""; cp.Set2("SPEC",s.replace("소켓 Ø28(0,0: 용접소켓 G13 판 밑 용접)","유로 구멍 Ø27(0,0): 배럴 니플 G13c R3/4를 10 삽입해 밑면 필릿 용접")); e=I4(); w=I4(); print("save J1c",d.Save3(1,e,w))
# ---- 호스
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
        if abs(Ls-target_len)<1.0: break
    else: raise SystemExit("hose sketch length mismatch "+path)
    h.ForceRebuild3(False); bs=list(pv(h,"GetBodies2",0,True) or []); sw=h.FeatureByName("스윕1"); parents=[p.Name for p in (pv(sw,"GetParents") or [])]
    orphan=[n_ for n_,t_ in feats(h) if t_=="ProfileFeature" and n_ not in parents]; print(f"  {os.path.basename(path)} len {Ls:.2f} ww {ww(h)} orphan {orphan}"); assert len(bs)==1 and not ww(h) and not orphan; return h
if os.path.exists(Zp(NAME_DN)) and NAME_DN!=OLD_DN: OLD_DN=NAME_DN
if NAME_UP!=OLD_UP and os.path.exists(Zp(NAME_UP)): print("name clash → keep",OLD_UP); NAME_UP=OLD_UP
hd=redraw_path(Zp(OLD_DN),segs_dn,L_HOSE); hu=redraw_path(Zp(OLD_UP),segs_up,seglen(segs_up))
spec_common=f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 최소 굽힘반경 47, 자유길이 {L_HOSE:.1f} + 바브 삽입 2×17.5 = 절단 약 {round(L_HOSE)+35}"
hd.Extension.CustomPropertyManager("").Set2("SPEC",spec_common+f". 하강(스트로크 140, 낙차 {D_DN:.0f}, 편심 {OY:g}) 경로: r47 {math.degrees(a_dn):.1f}° + 직선 {2*t_dn:.1f} + r47 −{math.degrees(a_dn):.1f}°(일직선). 나사 물림 13 가정(ISO 7-1)")
hu.Extension.CustomPropertyManager("").Set2("SPEC",spec_common+f". 상승(낙차 {D_UP:.0f}) 경로: R{R_up:.1f} {math.degrees(t1):.1f}°/−{math.degrees(t1):.1f}°/−{math.degrees(t2):.1f}°/{math.degrees(t2):.1f}° 4원호 활, +y로 {bul:.0f} 불룩. 나사 물림 13 가정(ISO 7-1)")
for h,old,new in ((hd,OLD_DN,NAME_DN),(hu,OLD_UP,NAME_UP)):
    app.ActivateDoc3(Zp(old),False,0,I4()); h=app.ActiveDoc
    if new!=old: assert not os.path.exists(Zp(new)), new; e=I4(); w=I4(); ok=h.Extension.SaveAs(Zp(new),0,1,NOD,e,w); print("SaveAs",new,ok,e.value)
    else: e=I4(); w=I4(); ok=h.Save3(1,e,w); print("Save",new,ok,e.value)
    assert ok
# ---- 어셈블리
a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames")); title=a.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def move_fixed(c,R,t):
    a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    set_T(c,R,t); a.ClearSelection2(True); c.Select4(False,NOD,False); a.FixComponent(); a.ClearSelection2(True)
def sel_comp(n): a.ClearSelection2(True); return a.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
def interf(items):
    a.ClearSelection2(True)
    for c in items: c.Select4(True,NOD,False)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); a.ClearSelection2(True); return rows
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
# 1) 고정 소켓·클로즈 니플 삭제, 배럴 니플 추가
for n in list(cc):
    if n.startswith(("G13b_socket_Rp3-4_KS_L36-1","G14b_")) and not n.startswith(("G13b_socket_Rp3-4_KS_L36-10","G13b_socket_Rp3-4_KS_L36-11")):
        sel_comp(n); print("delete",n,a.Extension.DeleteSelection2(1))
a.EditRebuild3; cc=comps()
if not any(n.startswith("G13c_") for n in cc):
    if app.GetOpenDocumentByName(P_BN) is None: open_doc(app,P_BN,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    c=a.AddComponent5(P_BN,0,"",False,"",0.0,0.0,0.0); assert c; a.EditRebuild3; cc=comps()
bn=[n for n in cc if n.startswith("G13c_")][0]
# 2) J17 → J17b 교체(전 인스턴스)
olds=[n for n in cc if n.startswith("J17_pipe")]
if olds:
    if app.GetOpenDocumentByName(P17b) is None: open_doc(app,P17b,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(P17b,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace J17",ok); assert ok; cc=comps()
def inst(n): return n.rsplit("-",1)[1]
PLACE={}
for n in cc:
    if n.startswith("G13c_"): PLACE[n]=(I3,(0,0,0.0))
    elif n.startswith("G3c_"): PLACE[n]=(I3,(0,0,Z_VALVE_TOP))
    elif n.startswith("B4c_"): PLACE[n]=(R_G,(0,-PAD_H,Z_B4C))
    elif n.startswith("H16b_"): PLACE[n]=({"10":I3,"11":R_FLIP,"12":R_FLIP}[inst(n)],{"10":(0,0,Z_HN_FIX),"11":(0,OY,ZP_UP+MOV_ORG),"12":(0,OY,ZP_DN+MOV_ORG)}[inst(n)])
    elif n.startswith("J17b_"): PLACE[n]=(I3,{"3":(0,OY,ZP_UP+J17_TOP),"4":(0,OY,ZP_DN+J17_TOP)}[inst(n)])
    elif n.startswith("J19e_hose"): PLACE[n]=(R_HOSE,(0,0,NIP_FIX_END))
print("place",{n:t for n,(R,t) in PLACE.items()})
rep={"hose":{"L":L_HOSE,"R":R_up,"D_DN":D_DN,"D_UP":D_UP,"ENG":ENG},"cfg":{}}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,(R,t) in PLACE.items():
        if n in cc: move_fixed(cc[n],R,t)
    c=cc[bn]
    if c.GetSuppression2!=2: a.ClearSelection2(True); c.Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
    if cfg.startswith(("1.","2.")): a.ClearSelection2(True); cc[bn].Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)   # 해석 구성은 배관 억제(기존 관례)
    a.ForceRebuild3(False); cc=comps()
    info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(PLACE) if n in cc}
    rep["cfg"][cfg]={"ww":ww(a),"info":info}; print(f"[{cfg}] ww {ww(a)}")
    for n,v_ in info.items(): print("   ",n,v_)
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(act_); rep["interf_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",[r for r in rows if not (r[0][0]==r[0][1])][:14])
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); print("refs",refs)
assert not any(r.startswith(("G14b_","J17_pipe")) for r in refs), refs
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value); rep["refs"]=refs
json.dump(rep,open(os.path.join(VER,"ks_fittings2_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("ks fittings 2 done")
