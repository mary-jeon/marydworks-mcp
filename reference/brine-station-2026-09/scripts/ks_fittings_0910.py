# 2026-09-10: 관이음 3종을 KS B 1533·국내 카탈로그 치수로 재구성(사용자 결정 a) — 나사 표현은 겹침(기존 관례)
#  G13b 소켓 Rp3/4 (KS B 1533 부표3: SUS D≥30.5·L≥36 → OD 32·L36·보어 Ø24.1) · G14b 클로즈 니플 R3/4 (부표1: L≥35 → OD 26.4·L35·보어 20)
#  H16b 호스니플 PT3/4×19 (하이스텐 3/4×20: L 50.5·L1(나사) 27·B 29·D 20·d 14 → 나사 Ø26.4×27 + 육각(Ø31 근사)×6 + 바브 Ø20.5×17.5, 보어 14)
#  스택: 고정 소켓 −10~−46 · 니플 −28.5~−63.5(양쪽 17.5 물림) · 밸브 G3c 상단 −46(하단 −129) · KE002 z −87.5 · 고정 호스니플 나사 −129~−102·바브 끝 −152.5
#        이동: 소켓 판 상면 플러시(ZP~ZP−36), 호스니플 나사 ZP~ZP−27·바브 끝 ZP+23.5 → 호스 낙차 하강 354·상승 214
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
SOCK_L=36.0; NIP_L=35.0; HN_THR=27.0; HN_HEX=6.0; HN_BARB=17.5; VALVE_L=83.0; PAD_H=43.5
Z_SOCK_TOP=-10.0; Z_VALVE_TOP=Z_SOCK_TOP-SOCK_L; Z_NIP_TOP=Z_VALVE_TOP+NIP_L/2; Z_VALVE_BOT=Z_VALVE_TOP-VALVE_L
Z_B4C=Z_VALVE_TOP-VALVE_L/2; Z_HN_FIX=Z_VALVE_BOT; NIP_FIX_END=Z_HN_FIX-HN_HEX-HN_BARB   # −152.5
MOV_END=HN_HEX+HN_BARB   # +23.5
print("stack: socket",Z_SOCK_TOP,"~",Z_VALVE_TOP,"nipple",Z_NIP_TOP,"valve",Z_VALVE_TOP,"~",Z_VALVE_BOT,"B4c z",Z_B4C,"fix hose end",NIP_FIX_END)
# ---------- 호스 해
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
v,(a_dn,t_dn)=climb(sc_dn,[0.03,170.0],[0.01,10.0]); segs_dn,_=segs_from(dn_list([a_dn,t_dn])); L_HOSE=seglen(segs_dn)
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
v2,(R_up,t1,t2)=best; segs_up,_=segs_from(up_list([R_up,t1,t2])); bul=max(abs(p[0]) for s in segs_up for p in (s[1],s[2],s[3]) if s[0]=="arc")
print(f"hose: D_DN {D_DN} D_UP {D_UP} L {L_HOSE:.2f} dn a {math.degrees(a_dn):.2f}° | up R {R_up:.1f} θ {math.degrees(t1):.1f}/{math.degrees(t2):.1f} bulge {bul:.1f} resid {v:.4f}/{v2:.4f}")
assert v<0.5 and v2<0.5
NAME_DN=f"J19e_hose_3-4in_dn_straight_L{round(L_HOSE)}.SLDPRT"; NAME_UP=f"J19e_hose_3-4in_up_bow_R{round(R_up)}.SLDPRT"
OLD_DN="J19e_hose_3-4in_dn_straight_L353.SLDPRT"; OLD_UP="J19e_hose_3-4in_up_bow_R53.SLDPRT"
json.dump({"NIP_FIX_END":NIP_FIX_END,"MOV_END":MOV_END,"D_DN":D_DN,"D_UP":D_UP,"L":L_HOSE,"dn_a_deg":math.degrees(a_dn),"up":{"R":R_up,"t1":math.degrees(t1),"t2":math.degrees(t2),"bulge":bul},"names":[NAME_DN,NAME_UP],"stack":{"socket_top":Z_SOCK_TOP,"valve_top":Z_VALVE_TOP,"nip_top":Z_NIP_TOP,"valve_bot":Z_VALVE_BOT,"b4c_z":Z_B4C}},open(os.path.join(VER,"ks_fittings_hose_0910.json"),"w"),indent=1)
if "--solve-only" in sys.argv: raise SystemExit("solve only")
# ---------- SolidWorks
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
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bodies(d))
def extrude(d,depth,up,name):
    # 실측: Dir=False → +z, Dir=True → −z (원 스케치)
    f=d.FeatureManager.FeatureExtrusion3(True,False,(not up),0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
    assert f is not None, "extrude "+name; f.Name=name; return f
def cut_all(d,name):
    f=d.FeatureManager.FeatureCut4(True,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
    assert f is not None, "cut "+name; f.Name=name; return f
def build_tube(path,steps,bore_r,props):
    """steps: [(r, z0, z1, name)] z0>z1 (아래로) 또는 z0<z1(위로) — 원점 기준 원통 적층"""
    if os.path.exists(path): print("exists",os.path.basename(path)); return
    d=app.NewDocument(tmpl,0,0,0)
    for r,z0,z1,name in steps:
        depth=abs(z1-z0); up=z1>z0
        new_sketch(d,"정면",lambda sm,r=r: sm.CreateCircleByRadius(0,0,0,mm(r)))
        if abs(z0)>1e-9:   # 시작면이 원점이 아니면: 원점에서 z0까지 먼저 채우는 대신 전체를 만들고 확인 — 단순화: z0가 0이 아닌 단은 이전 단이 이미 그 높이까지 있음(연속 적층 전제)
            pass
        extrude(d,depth+abs(z0) if (up and z0>0) or ((not up) and z0<0) else depth,up,name)
    new_sketch(d,"정면",lambda sm: sm.CreateCircleByRadius(0,0,0,mm(bore_r))); cut_all(d,"보어")
    bx=bbox(d); print("  built",os.path.basename(path),"box",bx,"vol",round(vol(d)),"ww",ww(d)); assert not ww(d)
    cp=d.Extension.CustomPropertyManager("")
    for k,v_ in props.items(): cp.Add3(k,30,v_,1)
    try: d.SetMaterialPropertyName2("","이텍","STS 304")
    except Exception: pass
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",ok,e.value); assert ok
    return bx
P_SOCK=Zp("G13b_socket_Rp3-4_KS_L36.SLDPRT"); P_NIP=Zp("G14b_close_nipple_R3-4_KS_L35.SLDPRT"); P_HN=Zp("H16b_hose_nipple_PT3-4x19_L50.SLDPRT")
build_tube(P_SOCK,[(16.0,0,-SOCK_L,"소켓_OD32_L36")],12.05,{"TITLE":"SOCKET Rp3/4 (KS B 1533)","SPEC":"KS B 1533 나사식 관이음쇠 소켓 20A(3/4): 암나사 Rp3/4 양쪽(KS B 0222 평행 암), SUS304, D ≥ 30.5(모델 OD 32)·L ≥ 36(모델 36), 보어 Ø24.1(Rp 골경 근사). 나사 미표현(겹침 관례). 파트 좌표: 상단 z 0, 축 −Z","MATERIAL":"STS304","QT'Y":"3","DATE":"2026-09-10","REMARK":"고정판 J1c 밑면 용접(상단 z −10) 1개 + 이동판 J5e 플러시 삽입 용접 2개(상승/하강 인스턴스). 종전 근사 G13(PF3/4 Ø34×25) 대체 — KS 원문 표(§1-29)"})
build_tube(P_NIP,[(13.2,0,-NIP_L,"니플_OD26.4_L35")],10.0,{"TITLE":"CLOSE NIPPLE R3/4 (KS B 1533)","SPEC":"KS B 1533 클로즈 니플 20A(3/4): 수나사 R3/4 양쪽(KS B 0222 테이퍼), SUS304, L ≥ 35(모델 35), OD 26.4(R 기준경), 보어 20. 나사 미표현. 파트 좌표: 상단 z 0, 축 −Z","MATERIAL":"STS304","QT'Y":"1","DATE":"2026-09-10","REMARK":"고정 소켓(Rp)과 밸브 상단 암나사 사이, 양쪽 17.5 물림. 밸브 나사가 PT(Rc)이면 그대로 맞고, PF(G)면 소켓 쪽만 Rp/R 조합 — 태성 20S3 나사 확인 후 확정. 종전 G14(PF L32) 대체"})
build_tube(P_HN,[(13.2,0,HN_THR,"나사_OD26.4_L27"),(15.5,0,-HN_HEX,"육각_B29_t6"),(10.25,-HN_HEX,-HN_HEX-HN_BARB,"바브_D20.5_L17.5")],7.0,{"TITLE":"HOSE NIPPLE PT3/4 x 19 (L50.5)","SPEC":"스테인리스 호스니플 PT3/4 × 호스 내경 19(20호칭): 하이스텐 카탈로그 3/4×20 — L 50.5·L1(나사) 27·B(육각) 29·D(바브) 20·d(보어) 14. 모델: 나사 Ø26.4×27 + 육각(Ø31 원통 근사)×6 + 바브 Ø20.5×17.5, 보어 14. 나사·바브 링 미표현. 파트 좌표: 육각/나사 경계 z 0, 나사 +z, 바브 −z","MATERIAL":"STS304","QT'Y":"3","DATE":"2026-09-10","REMARK":"고정 1(밸브 하단 암나사, 바브 아래) + 이동 2(소켓 상단, 바브 위; 상승/하강 인스턴스, 뒤집어 배치). 호스 do88 F19 ID19 바브 삽입 + T볼트 클램프. 종전 근사 H16(PF L30) 대체 — 카탈로그 원문 URL은 _3D다운로드/README 3차"})
# ---------- 호스 스케치 제자리 편집
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
    h.ForceRebuild3(False); bs=list(pv(h,"GetBodies2",0,True) or []); v_=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs)
    sw=h.FeatureByName("스윕1"); parents=[p.Name for p in (pv(sw,"GetParents") or [])]; sks=[n for n,t in feats(h) if t=="ProfileFeature"]; orphan=[s for s in sks if s not in parents]
    print(f"  {os.path.basename(path)} len {Ls:.2f} vol {v_:.0f} (A·L {math.pi*(14.1**2-9.5**2)*target_len:.0f}) ww {ww(h)} orphan {orphan}"); assert len(bs)==1 and not ww(h) and not orphan; return h
# 재실행 안전: 새 이름이 이미 있으면(앞 실행에서 SaveAs 완료) 그 파일을 쓰고, 새 이름이 잔여 파일과 충돌하면 현재 이름 유지
if os.path.exists(Zp(NAME_DN)) and NAME_DN!=OLD_DN: OLD_DN=NAME_DN
if NAME_UP!=OLD_UP and os.path.exists(Zp(NAME_UP)): print("name clash → keep",OLD_UP); NAME_UP=OLD_UP
hd=redraw_path(Zp(OLD_DN),segs_dn,L_HOSE); hu=redraw_path(Zp(OLD_UP),segs_up,seglen(segs_up))
spec_common=f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 최소 굽힘반경 47, 자유길이 {L_HOSE:.1f} + 바브 삽입 2×17.5 = 절단 약 {round(L_HOSE)+35}"
hd.Extension.CustomPropertyManager("").Set2("SPEC",spec_common+f". 하강(스트로크 140, 낙차 {D_DN:.0f}, 편심 {OY:g}) 경로: r47 {math.degrees(a_dn):.1f}° + 직선 {2*t_dn:.1f} + r47 −{math.degrees(a_dn):.1f}°(일직선)")
hu.Extension.CustomPropertyManager("").Set2("SPEC",spec_common+f". 상승(낙차 {D_UP:.0f}) 경로: R{R_up:.1f} {math.degrees(t1):.1f}°/−{math.degrees(t1):.1f}°/−{math.degrees(t2):.1f}°/{math.degrees(t2):.1f}° 4원호 활, +y로 {bul:.0f} 불룩")
for h,old,new in ((hd,OLD_DN,NAME_DN),(hu,OLD_UP,NAME_UP)):
    app.ActivateDoc3(Zp(old),False,0,I4()); h=app.ActiveDoc
    if new!=old: assert not os.path.exists(Zp(new)), new; e=I4(); w=I4(); ok=h.Extension.SaveAs(Zp(new),0,1,NOD,e,w); print("SaveAs",new,ok,e.value)
    else: e=I4(); w=I4(); ok=h.Save3(1,e,w); print("Save",new,ok,e.value)
    assert ok
# ---------- J5e 소켓 구멍 Ø34 → Ø32 (제자리)
d=act(Zp("J5e_moving_plate_180x540_t8.SLDPRT"))
if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0
for s in list(pv(sk,"GetSketchSegments") or []):
    ty=s.GetType() if callable(s.GetType) else s.GetType
    if ty==1:
        cp=pv(s,"GetCenterPoint2")
        try: cx,cy=cp[0]*1000,cp[1]*1000
        except TypeError: cx,cy=pv(cp,"X")*1000,pv(cp,"Y")*1000
        r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
        if abs(cx)<0.5 and abs(cy-OY)<0.5 and abs(r-17)<0.1: s.Select4(True,NOD); n+=1
if n: d.Extension.DeleteSelection2(0); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,mm(OY),0,mm(16.0)); d.SketchManager.AddToDB=False
d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); print("J5e socket hole edited",n,"ww",ww(d)); assert not ww(d)
cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("SPEC") or ""; cp.Set2("SPEC",s_.replace("소켓 Ø34","소켓 Ø32(KS Rp 소켓 OD)")); e=I4(); w=I4(); print("save J5e",d.Save3(1,e,w),e.value)
# ---------- 어셈블리
a=act(ASM,2); cm=a.ConfigurationManager; CFGS=list(pv(a,"GetConfigurationNames"))
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
REPL={"G13_weld_socket_3-4in_L25":P_SOCK,"G14_close_nipple_3-4in_L32":P_NIP,"H16_hose_nipple_3-4in_short_L30":P_HN}
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
state={}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3
    for n,c in comps().items():
        if any(n.startswith(k) for k in REPL): state.setdefault(n,{})[cfg]=c.GetSuppression2
a.ShowConfiguration2("상승"); a.EditRebuild3; cc=comps()
for k,newf in REPL.items():
    olds=[n for n in cc if n.startswith(k)]; assert olds,k
    if app.GetOpenDocumentByName(newf) is None: open_doc(app,newf,1); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
    a.ClearSelection2(True); cc[olds[0]].Select4(False,NOD,False); ok=a.ReplaceComponents2(newf,"",True,True,True); a.ClearSelection2(True); a.EditRebuild3; print("replace",k,ok); assert ok; cc=comps()
cc=comps()
def inst(n): return n.rsplit("-",1)[1]
PLACE={}
for n in cc:
    if n.startswith("G13b_"): PLACE[n]=(I3,{"1":(0,0,Z_SOCK_TOP),"10":(0,OY,ZP_UP),"11":(0,OY,ZP_DN)}[inst(n)])
    elif n.startswith("G14b_"): PLACE[n]=(I3,(0,0,Z_NIP_TOP))
    elif n.startswith("H16b_"): PLACE[n]=({"10":I3,"11":R_FLIP,"12":R_FLIP}[inst(n)],{"10":(0,0,Z_HN_FIX),"11":(0,OY,ZP_UP),"12":(0,OY,ZP_DN)}[inst(n)])
    elif n.startswith("G3c_"): PLACE[n]=(I3,(0,0,Z_VALVE_TOP))
    elif n.startswith("B4c_"): PLACE[n]=(R_G,(0,-PAD_H,Z_B4C))
    elif n.startswith("J19e_hose"): PLACE[n]=(R_HOSE,(0,0,NIP_FIX_END))
print("place",{n:t for n,(R,t) in PLACE.items()})
old_of={n:[o for o in state if o.rsplit("-",1)[1]==inst(n) and o.split("_")[0][:3]==n.split("_")[0][:3]] for n in cc if n.startswith(("G13b_","G14b_","H16b_"))}
rep={"hose":{"L":L_HOSE,"R":R_up,"D_DN":D_DN,"D_UP":D_UP},"cfg":{}}
for cfg in CFGS:
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc=comps()
    for n,(R,t) in PLACE.items():
        if n in cc: move_fixed(cc[n],R,t)
    a.ForceRebuild3(False); cc=comps()
    for n,olds in old_of.items():
        if not olds or n not in cc: continue
        want=state[olds[0]][cfg]; st=cc[n].GetSuppression2
        if want==2 and st!=2: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.EditUnsuppress2; a.ClearSelection2(True)
        if want!=2 and st==2: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.EditSuppress2; a.ClearSelection2(True)
    a.ForceRebuild3(False); cc=comps()
    info={n:(cc[n].GetSuppression2,xform(cc[n])["t_mm"],box(cc[n]) if cc[n].GetSuppression2==2 else None) for n in sorted(PLACE) if n in cc}
    rep["cfg"][cfg]={"ww":ww(a),"info":info}; print(f"[{cfg}] ww {ww(a)}")
    for n,v_ in info.items(): print("   ",n,v_)
for cfg in ("상승","하강"):
    a.ShowConfiguration2(cfg); a.ForceRebuild3(False); cc=comps(); act_=[c for n,c in cc.items() if c.GetSuppression2==2]
    rows=interf(act_); rep["interf_"+cfg]=rows; print(f"[line {cfg}] 간섭 {len(rows)}:",rows)
a.ShowConfiguration2("상승"); a.EditRebuild3
refs=sorted({os.path.basename(c.GetPathName) for c in comps().values()}); assert not any(r.startswith(("G13_","G14_","H16_")) for r in refs), refs
e=I4(); w=I4(); print("save asm",a.Save3(1,e,w),e.value); rep["refs"]=refs
json.dump(rep,open(os.path.join(VER,"ks_fittings_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("ks fittings done")
