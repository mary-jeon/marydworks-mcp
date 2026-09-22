# 2026-09-09: 염수라인 구동 시뮬레이션(운동 스윕). 메이트가 없는 Transform 배치라 SW Motion은 못 쓰고,
# 이동 그룹(하강 인스턴스)을 상승 zp −390 → 하강 −510 사이 7단계로 옮기며 (1) 고정 스택·탱크·로봇(커버 열림) 간섭
# (2) 호스 경로 성립(자유길이 365.9, r≥47, LA25 회피) (3) 노즐 끝 지상고·개구 진입을 기록한다. 끝에 −510으로 복원, 저장 안 함.
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
OX=100.0; NIP_FIX_END=-148.0; L_HOSE=365.9; R_HOSE=47.0
LA25_XMAX=-39.7; HOSE_R=14.1
# ---- 호스 경로 솔버(make_parts_j5와 동일 형식)
def hose_segments(r,a1,a2,R,t,s=20.0):
    segs=[]; x,y,h=0.0,0.0,-math.pi/2
    def st(dd):
        nonlocal x,y
        if dd<=1e-9: return
        x1=x+dd*math.cos(h); y1=y+dd*math.sin(h); segs.append(("line",(x,y),(x1,y1))); x,y=x1,y1
    def arc(rad,ang):
        nonlocal x,y,h
        if abs(ang)<1e-9: return
        side=1 if ang>0 else -1
        cx=x-side*rad*math.sin(h); cy=y+side*rad*math.cos(h)
        h2=h+ang; x1=cx+side*rad*math.sin(h2); y1=cy-side*rad*math.cos(h2)
        segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang,rad)); x,y,h=x1,y1,h2
    st(s); arc(r,a1); st(t); arc(R,-(a1+a2)); st(t); arc(r,a2); st(s)
    return segs,(x,y)
def path_len(segs):
    return sum((math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1]) if sg[0]=="line" else abs(sg[4])*sg[5]) for sg in segs)
def solve_hose(D):
    import random
    def sc(p):
        a1,a2,R,t=p
        if R<R_HOSE or t<0 or a1<0 or a1+a2<=0.02: return 1e6
        segs,(ex,ey)=hose_segments(R_HOSE,a1,a2,R,t); return math.hypot(ex-OX,ey+D)+abs(path_len(segs)-L_HOSE)
    rnd=random.Random(3); best=(1e9,None)
    for _ in range(300):
        p=[rnd.uniform(0.1,2.5),rnd.uniform(-1.0,2.5),R_HOSE*rnd.uniform(1.0,8.0),rnd.uniform(0,D)]
        v=sc(p); step=[0.2,0.2,R_HOSE*0.5,max(10.0,D/8)]
        while step[0]>1e-6:
            imp=False
            for i in range(4):
                for dd in (1,-1):
                    q=list(p); q[i]+=dd*step[i]; vq=sc(q)
                    if vq<v: v,p=vq,q; imp=True
            if not imp: step=[u/2 for u in step]
        if v<best[0]: best=(v,p)
        if best[0]<0.05: break
    return best
def path_xrange(segs):
    xs=[]
    for sg in segs:
        xs+= [sg[1][0],sg[2][0]] if sg[0]=="line" else [sg[2][0],sg[3][0]]
        if sg[0]=="arc":
            cx,cy=sg[1]; rr=sg[5]
            # 원호 극점 근사: 호를 36등분 샘플
            import cmath
            p0=complex(sg[2][0]-cx,sg[2][1]-cy); ang=sg[4]
            for k in range(1,36):
                pk=p0*cmath.exp(1j*ang*k/36); xs.append(cx+pk.real)
    return min(xs),max(xs)
# ---- 어셈블리
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
GROUP={"J5d_moving_plate_220x540_t8-2":(0,0,0),"G13_weld_socket_3-4in_L25-11":(OX,0,0),"H16_hose_nipple_3-4in_short_L30-12":(OX,0,30),
       "J17_pipe_3-4in_L100-4":(OX,0,0),"B10_linear_bushing_MISUMI_LHFRW16-23":(-70,240,0),"B10_linear_bushing_MISUMI_LHFRW16-24":(-70,-240,0),
       "J9b_rod_clevis_t6_44x40x60-2":(-40,-24,0),"J11_clevis_pin_d10_L70-2":(-70,-35,35)}
asm.ShowConfiguration2("하강"); asm.EditRebuild3; cc=comps()
R0={n:xform(cc[n])["R"] for n in GROUP}
PS=os.path.join(Z,"S00000MU0.SLDASM"); st=app.GetOpenDocumentByName(PS)
report=[]
STEPS=[-390,-410,-430,-450,-470,-490,-510]
for zp in STEPS:
    app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc; asm.ShowConfiguration2("하강"); asm.EditRebuild3; cc=comps()
    for n,(dx,dy,dz) in GROUP.items(): set_T(cc[n],R0[n],(dx,dy,zp+dz))
    # 하강 호스는 −510 전용 형상이라 스윕 중 억제
    asm.ClearSelection2(True); asm.Extension.SelectByID2("J19c_hose_3-4in_dn_s_L366-1@"+asm.GetTitle.replace(".SLDASM",""),"COMPONENT",0,0,0,False,0,NOD,0); asm.EditSuppress2; asm.ClearSelection2(True)
    # LA25 로드 신장도 맞춤: B9c 파트 구성은 두 상태뿐이라 스윕 중 LA25는 상승 구성(로드 후퇴) 참조로 두고 간섭 대상에서 제외
    asm.ForceRebuild3(False); cc=comps()
    # 라인 내부 간섭: 이동 그룹 vs 고정 스택(J1c·J8b·G13-1·G14·G3·B4·H16-10·J2·G11)
    asm.ClearSelection2(True)
    fixed=["J1c_fixed_plate_185x580_t10-1","J8b_bent_U_bracket_t6_136x194x60-1","G13_weld_socket_3-4in_L25-1","G14_close_nipple_3-4in_L32-1","G3_valve_body_Tameson_BL2SA3-034-1","B4_actuator_SunYeh_OM-1_simplified-2","H16_hose_nipple_3-4in_short_L30-10","J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-3","J2_guide_shaft_MISUMI_PSSFAQ16-590-B10-4","G11_clevis_pin_d10_L160-4","J19c_hose_3-4in_up_r47-1"]
    for n in list(GROUP)+fixed:
        if n in cc and cc[n].GetSuppression2==2: cc[n].Select4(True,NOD,False)
    idm=asm.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); asm.ClearSelection2(True)
    rows=[r for r in rows if any(n in GROUP for n in r[0])]
    # 스테이션: 이동 그룹 vs 탱크 호퍼·로봇 커버(열림)·로봇 상부
    app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; s.ShowConfiguration2("하강"); s.ForceRebuild3(False)
    scm=s.ConfigurationManager; out=[]
    def walk(c,depth):
        for ch in (pv(c,"GetChildren") or []):
            if ch.GetSuppression2!=2: continue
            out.append((ch.Name2,ch))
            if depth<6: walk(ch,depth+1)
    walk(scm.ActiveConfiguration.GetRootComponent3(True),0)
    grp=[(n,c) for n,c in out if n.split("/")[-1] in GROUP]
    robot=[(n,c) for n,c in out if "210000MU1-1/" in n and n.count("/")==3]
    tank=[(n,c) for n,c in out if n.split("/")[-1].startswith(("S30001MU0","S30015MU0","S30016MU0","S30002MU0"))]
    s.ClearSelection2(True)
    for n,c in grp+robot+tank: c.Select4(True,NOD,False)
    idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=True; idm.IncludeMultibodyPartInterferences=True; idm.MakeInterferingPartsTransparent=False
    rows2=[([c_.Name2.split("/")[-1] for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
    rows2=[r for r in rows2 if any(n in GROUP for n in r[0])]
    noz=[c for n,c in grp if n.split("/")[-1].startswith("J17")][0]; b=box(noz); noz_gl=round(1109-b[3],1)
    plate=[c for n,c in grp if n.split("/")[-1].startswith("J5d")][0]; bp=box(plate); plate_gl=round(1109-bp[3],1)
    # 호스
    D=(zp+30)-NIP_FIX_END; D=-D
    v,(a1,a2,R,t)=solve_hose(D); segs,end=hose_segments(R_HOSE,a1,a2,R,t); xmin,xmax=path_xrange(segs)
    la25_clear=round((xmin-HOSE_R)-LA25_XMAX,1)
    rec={"zp":zp,"stroke_from_up":-390-zp,"nozzle_bottom_gl":noz_gl,"plate_bottom_gl":plate_gl,"line_interf":rows,"station_interf":rows2,
         "hose":{"D":D,"resid":round(v,3),"a1_deg":round(math.degrees(a1),1),"a2_deg":round(math.degrees(a2),1),"R":round(R,1),"t":round(t,1),"path_x":[round(xmin,1),round(xmax,1)],"LA25_clearance":la25_clear}}
    report.append(rec)
    print(f"zp {zp:5.0f} 스트로크 {-390-zp:3.0f} | 노즐끝 {noz_gl} 판밑 {plate_gl} | 라인간섭 {rows} | 스테이션간섭 {rows2} | 호스 D {D:.0f} resid {v:.2f} R {R:.0f} x {xmin:.0f}~{xmax:.0f} LA25여유 {la25_clear}")
# 복원
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc; asm.ShowConfiguration2("하강"); asm.EditRebuild3; cc=comps()
for n,(dx,dy,dz) in GROUP.items(): set_T(cc[n],R0[n],(dx,dy,-510+dz))
asm.ClearSelection2(True); asm.Extension.SelectByID2("J19c_hose_3-4in_dn_s_L366-1@"+asm.GetTitle.replace(".SLDASM",""),"COMPONENT",0,0,0,False,0,NOD,0); asm.EditUnsuppress2; asm.ClearSelection2(True); asm.ForceRebuild3(False); cc=comps()
print("restored:",{n:xform(cc[n])["t_mm"] for n in ("J5d_moving_plate_220x540_t8-2","J11_clevis_pin_d10_L70-2")},"hose supp",cc["J19c_hose_3-4in_dn_s_L366-1"].GetSuppression2)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump(report,open(os.path.join(VER,"line_sweep_0909.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("saved _검증/line_sweep_0909.json ; assembly NOT saved"); stop.set()
