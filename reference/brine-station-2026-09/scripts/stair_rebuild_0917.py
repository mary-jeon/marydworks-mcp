# 2026-09-17 계단 재설계(사용자 지시 ②③④, 「제작」): S20000MU0 로컬(x 폭, y 높이, z 진행) 좌표로 새 부품 생성 → 구 계단(스트링거 □75·디딤판 220·경사 지주·난간대) 삭제 → 삽입·기준면 메이트
#  ② 디딤판 깊이 300(단너비 270 + 코 30), 챌판 245.25 ×8(총 높이 1,962 유지, 단수 유지), 경사 42.25°(60° → 42°)
#  ③ 수직 지주 Ø48.6×3.7 ×4/측(디딤판 1·3·5·7 앞코), 상부 난간대 앞코 위 900·중간 450(제13조), 시작 = 첫 단 지주에서 60 앞
#  ④ 측판 PL 6T×250 STS304 ×2(□75 파이프 대체), 디딤판 4.5T 절곡(600×300×40)
import os, sys, json, math, re, shutil
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n); DATE="2026-09-17"
STAGE=sys.argv[1] if len(sys.argv)>1 else "all"; rep={"stage":STAGE}
ASM_HELPERS='''def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def mates_iter():
    f=pv(a,"FirstFeature")
    while f is not None:
        if pv(f,"GetTypeName2")=="MateGroup":
            sf=f.GetFirstSubFeature
            while sf is not None: yield sf; sf=sf.GetNextSubFeature
        f=pv(f,"GetNextFeature")
def mate_names(): return [m.Name for m in mates_iter()]
def del_mate(name):
    a.ClearSelection2(True)
    if a.Extension.SelectByID2(name,"MATE",0,0,0,False,0,NOD,0): a.EditDelete()
    a.ClearSelection2(True)
KO=("우측면","윗면","정면"); EN=("Right Plane","Top Plane","Front Plane")
def sel_plane_c(comp,axis,append):
    for nm in (KO[axis],EN[axis]):
        if a.Extension.SelectByID2(f"{nm}@{comp}@S20000MU0","PLANE",0,0,0,append,1,NOD,0): return True
    return False
def sel_plane_a(axis,append):
    for nm in (KO[axis],EN[axis]):
        if a.Extension.SelectByID2(nm,"PLANE",0,0,0,append,1,NOD,0): return True
    return False
def add_mate(mtype,align,flip=False,dist=0.0,name=None):
    err=I4(); m=a.AddMate5(mtype,align,flip,dist,0.0,0.0,0,0,0,0,0,False,False,0,err); a.ClearSelection2(True)
    ok=(m is not None); f=None
    if ok:
        f=list(mates_iter())[-1]
        if name:
            try: f.Name=name
            except Exception as ex: print("  rename exc",ex)
    return ok,err.value,f
def t_ok(comp,t_exp):
    a.EditRebuild3; x=xform(comps()[comp]); return max(abs(p-q) for p,q in zip(x["t_mm"],t_exp))<0.02 and max(abs(x["R"][i][j]-(1.0 if i==j else 0.0)) for i in range(3) for j in range(3))<1e-3, x
def mate_to_asm(comp,t,tag):
    made=[]
    for j in range(3):
        off=t[j]; name=f"{tag}_{'xyz'[j]}"; done=False
        variants=[(0,False),(1,False)] if abs(off)<1e-6 else [(0,False),(0,True),(1,False),(1,True)]
        for al,fl in variants:
            a.ClearSelection2(True); assert sel_plane_c(comp,j,False),(comp,j); assert sel_plane_a(j,True),j
            ok,e,f=add_mate(0,al,False,0,name) if abs(off)<1e-6 else add_mate(5,al,fl,abs(off)/1000,name)
            if not ok:
                nm=mate_names()
                if nm and re.fullmatch(r"(거리|일치|동심|각도)\d+",nm[-1]): del_mate(nm[-1])
                continue
            g,x=t_ok(comp,t)
            if g and not ww(a): made.append(name); done=True; break
            del_mate(name)
        assert done,("mate failed",comp,name)
    return made
def insert(path,t):
    c=a.AddComponent5(path,0,"",False,"",mm(t[0]),mm(t[1]),mm(t[2])); assert c is not None,path
    arr=[1.0,0,0,0,1.0,0,0,0,1.0]+[mm(t[0]),mm(t[1]),mm(t[2]),1.0,0.0,0.0,0.0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
    if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
    return c.Name2
'''
ASM20=Zp("S20000MU0.SLDASM"); BK=r"<MCP_DIR>\_backup\20260917-stair"
GROUND=-9.0; PLAT_Y=1953.0; PLAT_Z=980.0; N=8; RUN=270.0; RISE=(PLAT_Y-GROUND)/N; TH=math.atan2(RISE,RUN)
TAN=math.tan(TH); COS=math.cos(TH); SIN=math.sin(TH)
def nos(k): return (PLAT_Z-RUN*(N-k), PLAT_Y-RISE*(N-k))       # k=1..8 (8 = 플랫폼) → (z,y)
PL_T=4.5; PL_H=250.0; PL_TOP_OFF=20.0; X_IN=300.0; FL_W=50.0      # 측판 = 절곡 ㄷ채널 250×50×4.5T, 안쪽 면 x ±300, 플랜지 안쪽
TR_D=300.0; TR_T=4.5; TR_LIP=40.0                                # 디딤판
POST_D=48.6; POST_T=3.7; RAIL_D=42.7; RAIL_T=2.3
RAIL_H=900.0; MID_H=450.0; RAIL_START_EXT=60.0
POST_X=X_IN+PL_T+POST_D/2                                        # 327.3 (판 바깥면에 접함)
POST_BOT_BELOW=150.0                                             # 지주 하단 = 앞코 −150 (판 밴드 안)
P_PL=Zp("S20014MU0.SLDPRT"); P_PLL=Zp("S20019MU0.SLDPRT"); P_TR=Zp("S20015MU0.SLDPRT"); P_PO=Zp("S20016MU0.SLDPRT"); P_RA=Zp("S20017MU0.SLDPRT"); P_MR=Zp("S20018MU0.SLDPRT")
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def sel_plane_p(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def orphan_sketches(d):
    fl=[]; f=pv(d,"FirstFeature")
    while f is not None: fl.append(f); f=pv(f,"GetNextFeature")
    parents=set()
    for f in fl:
        if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature"): continue
        for pf in (pv(f,"GetParents") or []):
            try: parents.add(pf.Name)
            except Exception: pass
        sf=pv(f,"GetFirstSubFeature")
        while sf is not None:
            try: parents.add(sf.Name)
            except Exception: pass
            sf=pv(sf,"GetNextSubFeature")
    return [f.Name for f in fl if pv(f,"GetTypeName2") in ("ProfileFeature","3DProfileFeature") and f.Name not in parents]
def clean_orphans(d):
    for n in orphan_sketches(d):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
    d.EditRebuild3; return orphan_sketches(d)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def volume(d): return d.Extension.CreateMassProperty.Volume*1e9
def set_props(d,props,mat=None):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    if mat:
        try: d.SetMaterialPropertyName2("","이텍",mat)
        except Exception as ex: print("  mat exc",ex)
def save_new(d,path):
    assert not clean_orphans(d); e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",os.path.basename(path),ok,e.value,"ww",ww(d)); assert ok
def close_unsaved_new():
    for x in list(pv(app,"GetDocuments") or []):
        try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
        except Exception: continue
        if ty==1 and not pn and tt.startswith(("파트","Part")): app.CloseDoc(tt); print("closed unsaved",tt)
def sketch_xy(sk,px,py,pz,conv=0):
    a=list(sk.ModelToSketchTransform.ArrayData); R=[a[0:3],a[3:6],a[6:9]]; t=a[9:12]; sc=a[12] if len(a)>12 and a[12] else 1.0
    if conv==0: o=[sc*(R[i][0]*px+R[i][1]*py+R[i][2]*pz)+t[i] for i in range(3)]
    else: o=[sc*(R[0][i]*px+R[1][i]*py+R[2][i]*pz)+t[i] for i in range(3)]
    return o[0],o[1]
def poly_on_plane(d,plane,pts_model,conv=0):
    """모델 좌표 점열(닫힌 다각형)을 기준면 스케치에 선으로 그림"""
    assert sel_plane_p(d,plane); d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
    sp=[sketch_xy(sk,mm(p[0]),mm(p[1]),mm(p[2]),conv) for p in pts_model]
    for i in range(len(sp)):
        a=sp[i]; b=sp[(i+1)%len(sp)]; sm.CreateLine(a[0],a[1],0,b[0],b[1],0)
    sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); return [n for n,t in feats(d) if t=="ProfileFeature"][-1]
def extrude(d,sk,d1,d2=None,name="",merge=True):
    """d2 None: 단방향(d1, 방향은 bbox로 결정 못 하므로 호출자가 검증) / d2: 양방향"""
    d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
    if d2 is None: f=d.FeatureManager.FeatureExtrusion3(True,False,False,0,0,mm(d1),0.0,False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False)
    else: f=d.FeatureManager.FeatureExtrusion3(False,False,False,0,0,mm(d1),mm(d2),False,False,False,False,0.0,0.0,False,False,False,False,merge,True,True,0,0.0,False)
    d.EditRebuild3; assert f,name; f.Name=name; return f
def extrude_dir(d,sk,depth,name,want_box):
    """단방향 돌출 두 방향 시도 → bbox(want_box: 인덱스→값 dict) 검증"""
    for dirn in (False,True):
        d.ClearSelection2(True); assert d.Extension.SelectByID2(sk,"SKETCH",0,0,0,False,0,NOD,0)
        f=d.FeatureManager.FeatureExtrusion3(True,False,dirn,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
        if f is None: continue
        bx=bbox(d); ok=all(abs(bx[i]-v)<0.05 for i,v in want_box.items())
        print(f"   {name} dirn={dirn} box={bx} {'OK' if ok else ''}")
        if ok: f.Name=name; return f
        f.Select2(False,0); d.EditDelete(); d.EditRebuild3
    raise AssertionError(name)
# ---------- 0. 백업 ----------
if STAGE in ("all","backup"):
    os.makedirs(BK,exist_ok=True)
    for n in ("S20000MU0.SLDASM",):
        dst=os.path.join(BK,n)
        if not os.path.exists(dst): shutil.copy2(Zp(n),dst); print("backup",n)
# ---------- 1. 파트 ----------
if STAGE in ("all","parts"):
    close_unsaved_new()
    # (a) 측판 S20014(우)·S20019(좌): 절곡 ㄷ채널 250×50×4.5T. 파트 원점 = 웹 바깥면 × 웹 상단 모서리 × z 980 지점. 정면 C 프로파일 → −z 돌출 3,000 → x축 −θ 회전 → 상단 z>0 컷·하단 지면 컷
    def build_channel(path,inward,title_side):
        if os.path.exists(path): return
        d=app.NewDocument(tmpl,0,0,0); sgn=-1.0 if inward=="-x" else 1.0
        # 웹: x (0 ~ −t) for R(바깥면 x=0, 안쪽 −x) → 일반화: 웹 x 범위 [0, sgn*t], 플랜지 x 범위 [0, sgn*FL_W]
        def draw(sm):
            xw=sgn*PL_T; xf=sgn*FL_W
            pts=[(0,0),(xf,0),(xf,-PL_T),(xw,-PL_T),(xw,-(PL_H-PL_T)),(xf,-(PL_H-PL_T)),(xf,-PL_H),(0,-PL_H)]
            for i in range(len(pts)):
                a_=pts[i]; b_=pts[(i+1)%len(pts)]; sm.CreateLine(mm(a_[0]),mm(a_[1]),0,mm(b_[0]),mm(b_[1]),0)
        assert sel_plane_p(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; LEN=3000.0
        extrude_dir(d,sk,LEN,"채널_직선",{2:-LEN,5:0.0})
        bx=bbox(d); assert abs(bx[1]+PL_H)<0.05 and abs(bx[4])<0.05, bx
        area=PL_H*PL_T+2*(FL_W-PL_T)*PL_T; v=volume(d); assert abs(v-area*LEN)/(area*LEN)<0.002, (v,area*LEN)
        # 회전 −θ(x축): 축 (0,0,−1) → (0,−sinθ,−cosθ)
        bs=bodies(d); d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; bs[0].Select2(True,sd)
        mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0,0.0, 0.0,0.0,0.0, 0.0,0.0,-TH, False,1); d.EditRebuild3; assert mv is not None; mv.Name="경사_회전"
        bx=bbox(d); print("   channel rotated box",bx); assert bx[2]<-LEN*COS+50 and bx[1]<-LEN*SIN+50, bx
        # 컷 1: 상단 z>0 제거 (플랫폼 기둥 앞면), 컷 2: 지면 y < GROUND−(PLAT_Y+PL_TOP_OFF) 제거
        YG=GROUND-(PLAT_Y+PL_TOP_OFF)
        for name,rect,check in (("상단_수직컷",[(0,-3500,0.0),(0,600,0.0),(0,600,600),(0,-3500,600)],lambda b: abs(b[5])<0.05),
                                ("하단_지면컷",[(0,-3500,-4000),(0,YG,-4000),(0,YG,600),(0,-3500,600)],lambda b: abs(b[1]-YG)<0.05)):
            ok=False
            for conv in (0,1):
                assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); skobj=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
                sp=[sketch_xy(skobj,mm(q[0]),mm(q[1]),mm(q[2]),conv) for q in rect]
                for i in range(4): sm.CreateLine(sp[i][0],sp[i][1],0,sp[(i+1)%4][0],sp[(i+1)%4][1],0)
                sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
                skc=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(skc,"SKETCH",0,0,0,False,0,NOD,0)
                v0=volume(d); c=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
                bx=bbox(d) if (c is not None and len(bodies(d))==1) else None; print(f"   {name} conv {conv} dv {round(v0-volume(d)) if c else None} box {bx}")
                if bx and check(bx) and len(bodies(d))==1: c.Name=name; ok=True; break
                if c is not None: c.Select2(False,0); d.EditDelete()
                clean_orphans(d)
            assert ok,name
        bx=bbox(d); print("   channel final box",bx); L=math.hypot(PLAT_Z-(PLAT_Z+(GROUND-(PLAT_Y+PL_TOP_OFF))/TAN),PLAT_Y+PL_TOP_OFF-GROUND)
        set_props(d,{"TITLE":f"STAIR STRINGER (절곡 ㄷ채널, {title_side})","SPEC":f"절곡 ㄷ채널 PL 4.5T STS304: 웹 250 × 플랜지 50(안쪽 방향, 판금 R = t/2 = 2.25 권장), 경사 {math.degrees(TH):.1f}°(단높이 {RISE:.2f}×{N}, 단너비 {RUN:.0f}), 웹 상단 모서리 = 앞코선 +20, 경사길이 ≈{L:.0f}, 하단 수평 절단(지면), 상단 수직 절단(플랫폼 기둥 S20002 앞면 z 980). 바깥면 평면에 지주 Ø48.6 용접, 안쪽 웹면에 디딤판 용접. 제26조 500 kg/m² 등분포 σ ≈8.5 MPa(허용 51).",
          "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작(레이저 절단 후 절곡). □75×3.2 파이프 스트링거 대체 — 사용자 지시(판재를 사각형으로 접어서, 환봉/파이프 부착면 확보)."},mat="AISI 304")
        save_new(d,path); app.CloseDoc(d.GetTitle)
    build_channel(P_PL,"-x","우"); build_channel(P_PLL,"+x","좌")
    # (b) 디딤판 S20015: L형(판 300×4.5 + 앞 립 40), 원점 = 앞코 상면, 우측면 스케치 → x ±300
    if not os.path.exists(P_TR):
        d=app.NewDocument(tmpl,0,0,0)
        poly=[(0,0,0),(0,0,TR_D),(0,-TR_T,TR_D),(0,-TR_T,TR_T),(0,-TR_LIP,TR_T),(0,-TR_LIP,0)]
        for conv in (0,1):
            sk=poly_on_plane(d,"우측면",poly,conv); f=extrude(d,sk,X_IN,X_IN,"디딤판_L형"); bx=bbox(d); print("  tread conv",conv,"box",bx)
            if abs(bx[0]+X_IN)<0.05 and abs(bx[3]-X_IN)<0.05 and abs(bx[1]+TR_LIP)<0.05 and abs(bx[5]-TR_D)<0.05 and abs(bx[2])<0.05: break
            f.Select2(False,0); d.EditDelete(); clean_orphans(d)
        bx=bbox(d); assert abs(bx[5]-TR_D)<0.05 and abs(bx[2])<0.05, bx
        set_props(d,{"TITLE":"STAIR TREAD","SPEC":f"절곡판 4.5T STS304 600×{TR_D:.0f}×{TR_LIP:.0f}(앞 립 아래로), 단너비 {RUN:.0f} + 코 {TR_D-RUN:.0f}. 120 kg 중앙 집중 σ ≈81 MPa(3.2T면 114). 미끄럼 방지 무늬판(체커) 권장.","Material":"STS304","QT'Y":"7","DATE":DATE,"REMARK":"자작(절곡·측판에 용접). 220 깊이 3.2T(S20001) 대체 — 사용자 지시(발 270 기준)."},mat="AISI 304")
        save_new(d,P_TR); app.CloseDoc(d.GetTitle)
    # (c) 지주 S20016: Ø48.6×3.7 수직, 원점 = 하단, 길이 = 150 + 900 − 21.35(난간대 하면)
    POST_L=POST_BOT_BELOW+RAIL_H-RAIL_D/2
    if not os.path.exists(P_PO):
        d=app.NewDocument(tmpl,0,0,0)
        assert sel_plane_p(d,"윗면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(POST_D/2)); sm.CreateCircleByRadius(0,0,0,mm(POST_D/2-POST_T)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
        extrude_dir(d,sk,POST_L,"지주_Ø48.6",{1:0.0,4:POST_L})
        set_props(d,{"TITLE":"STAIR HANDRAIL POST","SPEC":f"Ø48.6×3.7T STS304 (KS D 3576 40A Sch40) L{POST_L:.1f}, 수직, 측판 바깥면에 용접(하단 앞코 −150 ~ 상단 난간대 하면). 제13조 7호 100 kg 캔틸레버(레버 880) σ ≈158 MPa(내력 205, SF 1.3).","Material":"STS304","QT'Y":"8","DATE":DATE,"REMARK":"자작. 경사 지주 Ø42.7(S20005) 대체 — 사용자 지시(대각선 → 직선)."},mat="AISI 304")
        save_new(d,P_PO); app.CloseDoc(d.GetTitle)
    # (d) 난간대 S20017: Ø42.7×2.3, 원점 = 시작점, z축 돌출 후 x축 회전으로 경사 → 바디 bbox 검증
    z1,y1=nos(1); Z_S=z1-RAIL_START_EXT; RAIL_L=(PLAT_Z-Z_S)/COS
    if not os.path.exists(P_RA):
        d=app.NewDocument(tmpl,0,0,0)
        assert sel_plane_p(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2)); sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2-RAIL_T)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
        extrude_dir(d,sk,RAIL_L,"난간대_직선",{2:0.0,5:RAIL_L})
        want_y=RAIL_L*SIN; want_z=RAIL_L*COS; ok=False
        for ang in (-TH,TH):
            bs=bodies(d); d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; bs[0].Select2(True,sd)
            mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0,0.0, 0.0,0.0,0.0, 0.0,0.0,ang, False,1); d.EditRebuild3
            if mv is None: print("   rotate None",ang); continue
            bx=bbox(d); print("   rotate",round(math.degrees(ang),2),"box",bx)
            if abs(bx[4]-(want_y+RAIL_D/2*COS))<0.5 and abs(bx[5]-(want_z+RAIL_D/2*SIN))<0.5 and abs(bx[1]+RAIL_D/2*COS)<0.5: mv.Name="경사_회전"; ok=True; break
            mv.Select2(False,0); d.EditDelete(); d.EditRebuild3
        assert ok,"rail rotate"
        set_props(d,{"TITLE":"STAIR HANDRAIL","SPEC":f"Ø42.7×2.3T STS304 (KS D 3576 32A) L{RAIL_L:.0f}, 경사 {math.degrees(TH):.1f}°(계단과 평행), 앞코 위 900(상부)·450(중간) — 산업안전보건기준에 관한 규칙 제13조 2호·5호·6호. 시작 = 첫 단 지주에서 60 앞, 끝 = 플랫폼 기둥 S20002 앞면.","Material":"STS304","QT'Y":"4","DATE":DATE,"REMARK":"자작. 구 난간대 S20004(지면까지 연장·굽힘)·중간 난간대 S20013 대체 — 사용자 지시(잡는 위치부터 시작)."},mat="AISI 304")
        save_new(d,P_RA); app.CloseDoc(d.GetTitle)
    rep["parts"]=[os.path.basename(p) for p in (P_PL,P_TR,P_PO,P_RA)]
# ---------- 1b. 중간 난간대 S20018: 지주 사이 4절 + 앞 스텁(다중바디), 직선 파이프 → 지주 자리 컷(x 관통) → 전체 −θ 회전 ----------
if STAGE in ("all","midrail"):
    close_unsaved_new()
    z1,y1=nos(1); Z_S=z1-RAIL_START_EXT; RAIL_L=(PLAT_Z-Z_S)/COS; GAP=POST_D/COS+2.0
    if not os.path.exists(P_MR):
        d=app.NewDocument(tmpl,0,0,0)
        assert sel_plane_p(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2)); sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2-RAIL_T)); sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; extrude_dir(d,sk,RAIL_L,"중간난간대_직선",{2:0.0,5:RAIL_L})
        # 회전 −θ 먼저 (x축, 원점) → 이후 수직 지주 자리를 수직 슬롯으로 컷
        bs=bodies(d); d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; bs[0].Select2(True,sd)
        mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0,0.0, 0.0,0.0,0.0, 0.0,0.0,-TH, False,1); d.EditRebuild3; assert mv is not None,"rotate"; mv.Name="경사_회전"
        bx=bbox(d); assert abs(bx[4]-(RAIL_L*SIN+RAIL_D/2*COS))<0.5 and abs(bx[5]-(RAIL_L*COS+RAIL_D/2*SIN))<0.5, bx
        # 지주 자리 수직 슬롯: 로컬 z = (z_k − Z_S) ± (POST_D/2+1), y 전체 → x 양방향 관통
        GAPZ=POST_D+2.0; cuts=[]
        for k in (1,3,5,7):
            zk,yk=nos(k); zc=zk-Z_S; cuts.append((zc-GAPZ/2,zc+GAPZ/2))
        for conv in (0,1):
            assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); skobj=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
            for a_,b_ in cuts:
                pts=[(0,-100,a_),(0,2100,a_),(0,2100,b_),(0,-100,b_)]; sp=[sketch_xy(skobj,mm(q[0]),mm(q[1]),mm(q[2]),conv) for q in pts]
                for i in range(4): sm.CreateLine(sp[i][0],sp[i][1],0,sp[(i+1)%4][0],sp[(i+1)%4][1],0)
            sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            skc=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(skc,"SKETCH",0,0,0,False,0,NOD,0)
            v0=volume(d); c=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
            nb=len(bodies(d)); print("   midrail cut conv",conv,"bodies",nb,"dv",round(v0-volume(d)))
            if c is not None and nb==5: c.Name="지주자리_수직컷"; break
            if c is not None: c.Select2(False,0); d.EditDelete()
            clean_orphans(d)
        assert len(bodies(d))==5, len(bodies(d))
        bb=sorted([[round(v*1000,2) for v in pv(b,"GetBodyBox")] for b in bodies(d)],key=lambda b:b[2]); print("   segments z(local):",[(b[2],b[5]) for b in bb])
        for a_,b_ in cuts: assert not any(b[2]<b_-0.01 and b[5]>a_+0.01 for b in bb), ("segment inside slot",a_,b_)
        GAP=GAPZ
        set_props(d,{"TITLE":"STAIR MID RAIL (4절+스텁)","SPEC":f"Ø42.7×2.3T STS304 (KS D 3576 32A), 앞코 위 450(제13조 2호 중간 난간대), 경사 {math.degrees(TH):.1f}°. 지주 Ø48.6 자리 수직 슬롯 {GAP:.1f}(z 방향, 틈 1) 5절 다중바디 1파일 — 지주 사이 절단(끝면 수직) 후 용접. 경사 총장 {RAIL_L:.0f}.","Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"자작. 구 중간 난간대 S20013 대체."},mat="AISI 304")
        save_new(d,P_MR); app.CloseDoc(d.GetTitle)
    # 어셈블리: 중간 난간대(S20017-3/-4) → S20018 ×2
    a=app.GetOpenDocumentByName(ASM20); app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
    def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
    cc=comps(); z1,y1=nos(1); Z_S=z1-RAIL_START_EXT; y_mid=y1+MID_H-RAIL_START_EXT*TAN
    old=[n for n,c in cc.items() if n.startswith("S20017") and abs(xform(c)["t_mm"][1]-y_mid)<0.05]; print("delete mid rails",old)
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3
    if app.GetOpenDocumentByName(P_MR) is None: open_doc(app,P_MR,1)
    app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc
    exec(ASM_HELPERS)
    for sx,side in ((1,"R"),(-1,"L")):
        t=[sx*POST_X,y_mid,Z_S]; nm=insert(P_MR,t); made=mate_to_asm(nm,t,f"중간난간대{side}"); g,x=t_ok(nm,t); print(f"  중간난간대{side} {nm} t={x['t_mm']} ok={g}"); assert g
    a.ForceRebuild3(False); print("ww",ww(a))
# ---------- 2. 어셈블리 S20000 ----------
if STAGE in ("all","asm","verify"):
    a=app.GetOpenDocumentByName(ASM20); assert a, "S20000 not loaded"; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
    exec(ASM_HELPERS)
if STAGE in ("all","asm"):
    cc=comps(); old=[n for n in cc if n.split("/")[-1].startswith(("S20006","S20008","S20001MU0","S20004","S20005","S20013","S20014","S20015","S20016","S20017","S20018","S20019"))]
    print("delete",len(old),old)
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3; cc=comps(); print("remaining",sorted(cc)); print("mates",len(mate_names()),"ww",ww(a))
    for p in (P_PL,P_PLL,P_TR,P_PO,P_RA,P_MR):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc
    plan=[]
    plan+= [(P_PL,[X_IN+PL_T,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판R"),(P_PLL,[-X_IN-PL_T,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판L")]
    for k in range(1,8):
        z,y=nos(k); plan.append((P_TR,[0.0,y,z],f"디딤판{k}"))
    for k in (1,3,5,7):
        z,y=nos(k)
        for sx,side in ((1,"R"),(-1,"L")): plan.append((P_PO,[sx*POST_X,y-POST_BOT_BELOW,z],f"지주{k}{side}"))
    z1,y1=nos(1); Z_S=z1-RAIL_START_EXT
    for h,hn,pp in ((RAIL_H,"상부",P_RA),(MID_H,"중간",P_MR)):
        y_s=y1+h-RAIL_START_EXT*TAN
        for sx,side in ((1,"R"),(-1,"L")): plan.append((pp,[sx*POST_X,y_s,Z_S],f"난간대{hn}{side}"))
    inserted=[]
    for path,t,tag in plan:
        nm=insert(path,t); made=mate_to_asm(nm,t,tag); g,x=t_ok(nm,t); print(f"  {tag:10s} {nm[:22]:22s} t={x['t_mm']} ok={g}"); assert g; inserted.append((tag,nm,t))
    a.ForceRebuild3(False); print("ww",ww(a),"fixed",[n for n,c in comps().items() if c.IsFixed]); rep["inserted"]=inserted
if STAGE in ("all","asm","verify"):
    a.ForceRebuild3(False); a.ClearSelection2(True)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
    print("S20000 interferences",len(res))
    for cs,v in res[:30]: print("   ",v,[c[:20] for c in cs])
    rep["interf"]=res
    cc=comps(); rep["boxes"]={n:box(c) for n,c in cc.items()}
    for n,c in sorted(cc.items()):
        if n.startswith(("S20014","S20015","S20016","S20017","S20018","S20019")): print("  ",n[:16],box(c))
json.dump(rep,open(os.path.join(VER,f"stair_rebuild_0917_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
print("DONE",STAGE)
