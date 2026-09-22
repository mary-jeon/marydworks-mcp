# 2026-09-22 계단·플랫폼 난간 재작업(사용자 지시 「착수해」):
#  0 측판 S20014/S20019 판금(ㅁ 250×50×4.5T, 이음매 1 mm 슬릿 바닥 중앙, InsertConvertToSheetMetal2) / 0.1 디딤판 S20015 ㄴ→ㄷ 판금 / 0.2 8단 유지
#  1 기둥 SQ PIPE-01 S20002 3000→1769.7(PLATE-02 상면) / 바닥 위 □75 가로대(S20003-2·-3, S20009-2·-3) 삭제
#  2 계단 전체를 PLATE-02 상면(1769.7)에서 내려가게(단높이 222.34, 단너비 205) / 3 원형 난간 Ø42.7×2.3 새로(S20021 좌 일체·S20022 우 지주·S20023 뒤 가로대, 높이 3000 유지)
#  4 계단 손잡이 S20020 재생성(앞코 위 900/450, 앞 지주에 붙임). 사용자 파일 S20017-1은 미참조로 보존.
# usage: stair_round_0922.py asmdel | parts | rail | column | asm | station
import os, sys, json, math, re, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"stair_rebuild_0921b.py"),encoding="utf-8").read().split("# ---------- 0.")[0])
STAGE=sys.argv[1]; rep={"stage":STAGE}; DATE="2026-09-22"
BK=r"<MCP_DIR>\_backup\20260922-stair-round"
# ---- 새 레이아웃 ----
GROUND=-9.0; PLAT_Y=1769.7; PLAT_Z=980.0; N=8; RUN=205.0; RISE=(PLAT_Y-GROUND)/N; TH=math.atan2(RISE,RUN); TAN=math.tan(TH); COS=math.cos(TH); SIN=math.sin(TH)
def nos(k): return (PLAT_Z-RUN*(N-k), PLAT_Y-RISE*(N-k))
POST_D=42.7; POST_T=2.3; RAIL_D=42.7; RAIL_T=2.3
COL_L=1769.7; COL_X=337.5; COL_ZF=1017.5; COL_ZB=2142.5              # □75 기둥 중심
TOP_RAIL_TOP=3000.0; MID_C=2347.3                                       # 현 사각 난간 상부 가로대 상면 3000 · 중간 가로대 중심 2347.3 유지
H_TOP=TOP_RAIL_TOP-RAIL_D/2-PLAT_Y; H_MID=MID_C-PLAT_Y                  # 바닥 위 가로대 중심 높이
POST_FRONT=COL_ZF-POST_D/2                                              # 앞 지주 앞면 z
P_HR=Zp("S20020MU0.SLDPRT"); P_RL=Zp("S20021MU0.SLDPRT"); P_RP=Zp("S20022MU0.SLDPRT"); P_RB=Zp("S20023MU0.SLDPRT"); P_COL=Zp("S20002MU0.SLDPRT")
SM_T=4.5; SM_R=SM_T/2; SM_DELTA=(1-math.pi/4)*(2*SM_R*SM_T+SM_T**2)     # 날카로운 모서리→굽힘 치환 시 단위길이 체적 감소 8.69 mm²
print(f"layout: RISE {RISE:.3f} RUN {RUN} TH {math.degrees(TH):.2f}° | H_TOP {H_TOP:.2f} H_MID {H_MID:.2f} POST_FRONT {POST_FRONT}")
# ---- 판금 변환 도우미(sheetmetal_convert_0908 실측 규칙) ----
def sm_feats(d): return [(n,t) for n,t in feats(d) if t in ("SheetMetal","SolidToSheetMetal","FlatPattern")]
def planar_faces(d):
    b=bodies(d)[0]; out=[]
    for f in (pv(b,"GetFaces") or []):
        s=f.GetSurface
        if s.IsPlane: out.append((f.GetArea*1e6,[round(v,3) for v in pv(f,"Normal")],[round(v*1000,2) for v in pv(f,"GetBox")],f))
    return sorted(out,key=lambda x:-x[0])
def perp_edges(face):
    out=[]; n=[round(v,3) for v in pv(face,"Normal")]
    for e in (pv(face,"GetEdges") or []):
        try: fa=pv(e,"GetTwoAdjacentFaces2")
        except Exception: continue
        other=None
        for f2 in fa:
            if f2 is not None and not f2.IsSame(face): other=f2
        if other is None or not other.GetSurface.IsPlane: continue
        n2=[round(v,3) for v in pv(other,"Normal")]
        if abs(sum(p*q for p,q in zip(n,n2)))<1e-3:
            p0=[v*1000 for v in pv(pv(e,"GetStartVertex"),"GetPoint")]; p1=[v*1000 for v in pv(pv(e,"GetEndVertex"),"GetPoint")]
            out.append((e,math.dist(p0,p1),p0,p1))
    return out
def outer_corner_edges(d,min_len,xs):
    """길이 >min_len, 이웃 두 면이 서로 수직인 평면, 양 끝점 x 가 xs 중 하나(=바깥 모서리: 회전축이 x 라 x 는 불변)"""
    b=bodies(d)[0]; cand=[]
    for e in (pv(b,"GetEdges") or []):
        try:
            fa=[f for f in pv(e,"GetTwoAdjacentFaces2") if f is not None]
            if len(fa)!=2 or not all(f.GetSurface.IsPlane for f in fa): continue
            n1=pv(fa[0],"Normal"); n2=pv(fa[1],"Normal")
            if abs(sum(p*q for p,q in zip(n1,n2)))>1e-3: continue
            p0=[v*1000 for v in pv(pv(e,"GetStartVertex"),"GetPoint")]; p1=[v*1000 for v in pv(pv(e,"GetEndVertex"),"GetPoint")]
        except Exception: continue
        L=math.dist(p0,p1)
        if L<min_len or abs(p0[0]-p1[0])>0.01 or not any(abs(p0[0]-x)<0.01 for x in xs): continue
        cand.append((round(p0[0],2),L,e,[round(v,1) for v in p0],[round(v,1) for v in p1]))
    print("   outer corner edges:",[(c[0],round(c[1]),c[3][1:],c[4][1:]) for c in cand]); return cand
def convert_sm(d,sel_fn,expect,tol,label,variants):
    """sel_fn(mode) -> (fixed_face, bend_edges) 를 시도마다 새로 얻음(실패 후 삭제하면 객체가 끊어짐). variants: [(mode, find), ...]"""
    for mode,find in variants:
        fixed,bend_edges=sel_fn(mode)
        d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; ok=fixed.Select4(False,sd)
        for e in bend_edges:
            s2=d.SelectionManager.CreateSelectData; s2.Mark=2; ok=ok and e.Select4(True,s2)
        v0=volume(d); f=d.FeatureManager.InsertConvertToSheetMetal2(mm(SM_T),False,find,mm(SM_R),0.0002,0,0.5,0,0.5,False); d.EditRebuild3
        v1=volume(d); made=sm_feats(d); w=ww(d); nb=len(bodies(d))
        print(f"   {label}: mode={mode} find={find} sel={ok} edges={len(bend_edges)} feat={f.Name if f else None} vol {round(v0)}→{round(v1)} (expect {round(expect)}) sm {[t for _,t in made]} ww {w} bodies {nb}")
        if any(t=="SolidToSheetMetal" for _,t in made) and abs(v1-expect)<=tol and not w and nb==1:
            for n,t in made:
                try: d.FeatureByName(n).Name={"SheetMetal":"판금1","SolidToSheetMetal":"솔리드-변환1","FlatPattern":"전개도1"}[t]
                except Exception: pass
            d.EditRebuild3; return True
        for n,t in sm_feats(d):
            d.ClearSelection2(True)
            if d.Extension.SelectByID2(n,"BODYFEATURE",0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0)
        d.EditRebuild3; assert abs(volume(d)-v0)<1.0,("revert failed",volume(d),v0)
    return False
def cut_rect_side(d,name,rect,check):
    """우측면 스케치 사각형(모델 좌표 (x,y,z) 4점) → 양방향 관통 컷, bbox check 로 규약(conv) 판정"""
    for conv in (0,1):
        assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); skobj=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
        sp=[sketch_xy(skobj,mm(q[0]),mm(q[1]),mm(q[2]),conv) for q in rect]
        for i in range(4): sm.CreateLine(sp[i][0],sp[i][1],0,sp[(i+1)%4][0],sp[(i+1)%4][1],0)
        sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        skc=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(skc,"SKETCH",0,0,0,False,0,NOD,0)
        v0=volume(d); c=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
        bx=bbox(d) if (c is not None and len(bodies(d))==1) else None; print(f"   {name} conv {conv} dv {round(v0-volume(d)) if c else None} box {bx}")
        if bx and check(bx) and len(bodies(d))==1: c.Name=name; return True
        if c is not None: c.Select2(False,0); d.EditDelete()
        clean_orphans(d)
    raise AssertionError(name)
# ================= 0. 어셈블리에서 구 계단·바닥 위 가로대 제거, 파트 창 닫기 =================
if STAGE=="asmdel":
    a=app.GetOpenDocumentByName(ASM20); assert a; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; exec(ASM_HELPERS)
    cc=comps(); old=[n for n in cc if n.split("/")[-1].startswith(("S20014","S20015","S20017","S20019")) or n.split("/")[-1] in ("S20003MU0-2","S20003MU0-3","S20009MU0-2","S20009MU0-3")]
    print("remove from asm",len(old),sorted(old)); rep["removed"]=sorted(old)
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3; print("remaining",sorted(comps())); print("ww",ww(a))
    for p in (P_PL,P_PLL,P_TR,Zp("S20017-1MU0.SLDPRT")):
        bk=os.path.join(BK,os.path.basename(p)); assert os.path.exists(bk) and os.path.getsize(bk)==os.path.getsize(p),("backup missing",p)
        dd=app.GetOpenDocumentByName(p)
        if dd is not None: app.CloseDoc(dd.GetTitle)
        print("  closed",os.path.basename(p),app.GetOpenDocumentByName(p) is None)
# ================= 1. 판금 파트: 측판 ㅁ(슬릿) · 디딤판 ㄷ =================
if STAGE=="parts":
    close_unsaved_new()
    def build_stringer(path,sgn,title_side):
        d=app.NewDocument(tmpl,0,0,0); T=PL_T; W=FL_W; H=PL_H; g=0.5   # 슬릿 1.0 (바닥 플랜지 중앙)
        s=lambda x: sgn*x
        pts=[(s(W/2-g),-H),(0,-H),(0,0),(s(W),0),(s(W),-H),(s(W/2+g),-H),(s(W/2+g),-(H-T)),(s(W-T),-(H-T)),(s(W-T),-T),(s(T),-T),(s(T),-(H-T)),(s(W/2-g),-(H-T))]
        assert sel_plane_p(d,"정면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True
        for i in range(len(pts)):
            a_=pts[i]; b_=pts[(i+1)%len(pts)]; sm.CreateLine(mm(a_[0]),mm(a_[1]),0,mm(b_[0]),mm(b_[1]),0)
        sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(sk).Name="ㅁ_프로파일_슬릿1"; LEN=3000.0
        extrude_dir(d,"ㅁ_프로파일_슬릿1",LEN,"채널_직선",{2:-LEN,5:0.0})
        area=H*W-(H-2*T)*(W-2*T)-2*g*T; v=volume(d); assert abs(v-area*LEN)/(area*LEN)<0.002,(v,area*LEN)
        bs=bodies(d); d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; bs[0].Select2(True,sd)
        mv=d.FeatureManager.InsertMoveCopyBody2(0.0,0.0,0.0,0.0, 0.0,0.0,0.0, 0.0,0.0,-TH, False,1); d.EditRebuild3; assert mv is not None; mv.Name="경사_회전"
        bx=bbox(d); assert bx[2]<-LEN*COS+50 and bx[1]<-LEN*SIN+50, bx
        YG=GROUND-(PLAT_Y+PL_TOP_OFF)
        cut_rect_side(d,"상단_수직컷",[(0,-3500,0.0),(0,600,0.0),(0,600,600),(0,-3500,600)],lambda b: abs(b[5])<0.05)
        cut_rect_side(d,"상단_수평컷_바닥판면",[(0,-PL_TOP_OFF,-600),(0,600,-600),(0,600,600),(0,-PL_TOP_OFF,600)],lambda b: abs(b[4]+PL_TOP_OFF)<0.05)
        cut_rect_side(d,"하단_지면컷",[(0,-3500,-4000),(0,YG,-4000),(0,YG,600),(0,-3500,600)],lambda b: abs(b[1]-YG)<0.05)
        v_solid=volume(d); bx=bbox(d); print("   stringer solid box",bx,"vol",round(v_solid))
        # 판금 변환: 고정면 = 웹 바깥면(x=0 평면, 가장 큰 면), 굽힘 = 그 면의 긴 변 2개(길이 >1000), FindBends 로 나머지 2곳
        def sel_fn(mode):
            pf=planar_faces(d); web=[f for f in pf if abs(f[2][0])<0.01 and abs(f[2][3])<0.01][0]
            if mode=="outer4": return web[3],[c[2] for c in outer_corner_edges(d,1000.0,(0.0,sgn*FL_W))]
            E=perp_edges(web[3]); longE=[e for e in E if e[1]>1000]; assert len(longE)==2,len(longE); return web[3],[e[0] for e in longE]
        corners=outer_corner_edges(d,1000.0,(0.0,sgn*FL_W)); assert len(corners)==4,len(corners); Lsum=sum(c[1] for c in corners); expect=v_solid-SM_DELTA*Lsum
        ok=convert_sm(d,sel_fn,expect,0.02*SM_DELTA*Lsum+300,"stringer",[("outer4",False),("outer4",True),("web2",True)])
        rep.setdefault("sheetmetal",{})[os.path.basename(path)]={"ok":ok,"vol_solid":round(v_solid),"vol":round(volume(d)),"expect":round(expect),"feats":feats(d)}
        assert ok,"stringer sheet metal convert failed"
        L=math.hypot(PLAT_Z-(PLAT_Z+(GROUND-(PLAT_Y+PL_TOP_OFF))/TAN),PLAT_Y+PL_TOP_OFF-GROUND)
        set_props(d,{"TITLE":f"STAIR STRINGER (판금 ㅁ 박스, {title_side})","SPEC":f"판금 ㅁ 박스 PL 4.5T STS304 250×50, 굽힘 R 2.25(t/2) 4곳, 이음매 슬릿 1.0(바닥 플랜지 중앙, 용접), 안쪽 면 x 300·바깥 면 x 350. 경사 {math.degrees(TH):.1f}°(단높이 {RISE:.2f}×{N}, 단너비 {RUN:.0f}), 윗면 = 앞코선 +20(플랫폼 바닥판 상면 1,769.7 위로는 수평 절단), 경사길이 ≈{L:.0f}, 하단 수평 절단(지면), 상단 수직 절단(기둥 S20002 앞면 z 980). 전개도 있음.","Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작(레이저 절단 → 절곡 → 이음매 용접). 09-21 솔리드 모델을 판금 피처로 재작성, 계단을 PLATE-02(바닥판) 상면 기준으로 낮춤 — 사용자 지시."},mat="AISI 304")
        save_new(d,path); app.CloseDoc(d.GetTitle)
    build_stringer(P_PL,+1,"우"); build_stringer(P_PLL,-1,"좌")
    # 디딤판 ㄷ: 우측면 스케치 (y,z), x ±300 중간평면 돌출
    if True:
        d=app.NewDocument(tmpl,0,0,0)
        poly=[(0,0,0),(0,0,TR_D),(0,-TR_LIP,TR_D),(0,-TR_LIP,TR_D-TR_T),(0,-TR_T,TR_D-TR_T),(0,-TR_T,TR_T),(0,-TR_LIP,TR_T),(0,-TR_LIP,0)]
        for conv in (0,1):
            sk=poly_on_plane(d,"우측면",poly,conv); f=extrude(d,sk,X_IN,X_IN,"디딤판_ㄷ형"); bx=bbox(d); print("  tread conv",conv,"box",bx)
            if abs(bx[0]+X_IN)<0.05 and abs(bx[3]-X_IN)<0.05 and abs(bx[1]+TR_LIP)<0.05 and abs(bx[5]-TR_D)<0.05 and abs(bx[2])<0.05: break
            f.Select2(False,0); d.EditDelete(); clean_orphans(d)
        v_solid=volume(d); area=TR_D*TR_T+2*(TR_LIP-TR_T)*TR_T; assert abs(v_solid-area*2*X_IN)<1.0,(v_solid,area*2*X_IN)
        def sel_fn_t(mode):
            pf=planar_faces(d); top=[f for f in pf if f[1]==[0.0,1.0,0.0] and abs(f[2][1])<0.01][0]
            E=perp_edges(top[3]); longE=[e for e in E if e[1]>500]; assert len(longE)==2,[round(e[1]) for e in E]; return top[3],[e[0] for e in longE]
        expect=v_solid-2*SM_DELTA*2*X_IN; ok=convert_sm(d,sel_fn_t,expect,0.02*2*SM_DELTA*2*X_IN+100,"tread",[("top2",True),("top2",False)])
        rep.setdefault("sheetmetal",{})["S20015"]={"ok":ok,"vol_solid":round(v_solid),"vol":round(volume(d)),"expect":round(expect),"feats":feats(d)}; assert ok,"tread sheet metal convert failed"
        set_props(d,{"TITLE":"STAIR TREAD (판금 ㄷ)","SPEC":f"판금 ㄷ 4.5T STS304 600×{TR_D:.0f}×{TR_LIP:.0f}(앞·뒤 립 아래로), 굽힘 R 2.25(t/2) 2곳, 단너비 {RUN:.0f} + 코 {TR_D-RUN:.0f}. 120 kg 중앙 집중 σ ≈81 MPa(ㄴ 기준, ㄷ은 뒤 립이 더 받쳐 보수측). 미끄럼 방지 무늬판(체커) 권장. 전개도 있음.","Material":"STS304","QT'Y":"7","DATE":DATE,"REMARK":"자작(절곡·측판 안쪽 면에 용접). ㄴ(앞 립만, 09-21) → ㄷ(앞·뒤 립) 판금 — 사용자 지시(09-21 논의, 09-22 「현재도 ㄴ」 지적)."},mat="AISI 304")
        save_new(d,P_TR); app.CloseDoc(d.GetTitle)
# ================= 1b. 원형 난간·손잡이(스윕) =================
def sweep_lines_part(d,plane,lines_fn,dia,th,tag_prefix):
    """plane 위 레이아웃 스케치(완전 정의) → 선마다 요소 변환 경로 → 원형 얇은 벽 스윕 병합. lines_fn(sm,S,rel,dim) 이 (solid_segment_names, dims) 반환"""
    old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
    try:
        assert sel_plane_p(d,plane); d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; sm=d.SketchManager; ext=d.Extension
        def rel(kind,*ents):
            d.ClearSelection2(True)
            for i,e in enumerate(ents): assert e.Select4(i>0,NOD),kind
            d.SketchAddConstraints(kind); d.ClearSelection2(True)
        def origin_sel(append):
            for nm in ("Point1@원점","Point1@Origin"):
                if ext.SelectByID2(nm,"EXTSKETCHPOINT",0,0,0,append,0,NOD,0): return True
            return False
        dims={}
        def dim(name,how,e1,e2,at):
            d.ClearSelection2(True); assert e1.Select4(False,NOD)
            if e2 is not None: assert e2.Select4(True,NOD)
            elif how!="len": assert origin_sel(True)
            dd={"h":d.AddHorizontalDimension2,"v":d.AddVerticalDimension2,"len":d.AddDimension2,"d":d.AddDimension2}[how](at[0],at[1],0.0)
            d.ClearSelection2(True); assert dd is not None,name; dm=dd.GetDimension2(0); dm.Name=name; dims[name]=round(dm.SystemValue*1000,3)
        solid,extra=lines_fn(sk,sm,rel,origin_sel,dim)
        status=sk.GetConstrainedStatus; print("  layout status",status,dims); d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        assert status==3,("layout not fully defined",status)
        M=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(M).Name=f"{tag_prefix}_레이아웃"; M=f"{tag_prefix}_레이아웃"
        for i,(nm,tag) in enumerate(solid):
            assert sel_plane_p(d,plane); d.SketchManager.InsertSketch(True)
            assert d.Extension.SelectByID2(f"{nm}@{M}","EXTSKETCHSEGMENT",0,0,0,False,0,NOD,0); assert d.SketchManager.SketchUseEdge3(False,False)
            st=d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
            pname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(pname).Name=f"경로_{tag}"
            fd=d.FeatureManager.CreateDefinition(17); fd.CircularProfile=True; fd.CircularProfileDiameter=mm(dia); fd.Merge=True; fd.ThinFeature=True; fd.ThinWallType=1; fd.SetWallThickness(True,mm(th)); fd.SetWallThickness(False,mm(th))
            d.ClearSelection2(True); assert d.Extension.SelectByID2(f"경로_{tag}","SKETCH",0,0,0,False,4,NOD,0)
            f=d.FeatureManager.CreateFeature(fd); d.ClearSelection2(True); assert f is not None,("sweep failed",tag); f.Name=f"스윕_{tag}"
            print(f"   {tag}: path status {st}, bodies {len(bodies(d))}, vol {volume(d):.0f}")
        return dims,extra,M
    finally: app.SetUserPreferenceToggle(10,old_pref)
if STAGE=="rail":
    close_unsaved_new()
    # (a) S20021 좌측 난간 일체: 원점 = 앞 지주 하단(기둥 상면 중심). 우측면 스케치 (u=z, v=y). 지주 2(0·1125) + 상부 가로대(H_TOP) + 중간 가로대(H_MID)
    DZ=COL_ZB-COL_ZF
    def left_layout(sk,sm,rel,origin_sel,dim):
        def S(u,v): return sketch_xy(sk,0.0,mm(v),mm(u),1)
        def line(a,b):
            p=S(*a); q=S(*b); L=sm.CreateLine(p[0],p[1],0,q[0],q[1],0); assert L is not None; return L
        sm.AddToDB=True; P1=line((0,0),(0,H_TOP)); P2=line((DZ,0),(DZ,H_TOP)); TR=line((0,H_TOP),(DZ,H_TOP)); MR=line((0,H_MID),(DZ,H_MID)); sm.AddToDB=False
        sp=lambda L:L.GetStartPoint2; ep=lambda L:L.GetEndPoint2
        rel("sgVERTICAL2D",P1); rel("sgVERTICAL2D",P2); rel("sgHORIZONTAL2D",TR); rel("sgHORIZONTAL2D",MR)
        d.ClearSelection2(True); assert sp(P1).Select4(False,NOD); assert origin_sel(True); d.SketchAddConstraints("sgCOINCIDENT"); d.ClearSelection2(True)
        rel("sgMERGEPOINTS",ep(P1),sp(TR)); rel("sgMERGEPOINTS",ep(P2),ep(TR)); rel("sgCOINCIDENT",sp(MR),P1); rel("sgCOINCIDENT",ep(MR),P2)
        d.ClearSelection2(True); assert sp(P2).Select4(False,NOD); assert sp(P1).Select4(True,NOD); d.SketchAddConstraints("sgHORIZONTALPOINTS2D"); d.ClearSelection2(True)
        p=S(DZ/2,-80); dim("지주간격","len",TR,None,(p[0],p[1])); p=S(-120,H_TOP/2); dim("상부가로대_높이","len",P1,None,(p[0],p[1])); p=S(-120,H_MID/2); dim("중간가로대_높이","v",sp(MR),None,(p[0],p[1]))
        return [(P1.GetName,"지주_앞"),(P2.GetName,"지주_뒤"),(TR.GetName,"상부가로대"),(MR.GetName,"중간가로대")],{}
    if not os.path.exists(P_RL):
        d=app.NewDocument(tmpl,0,0,0); dims,_,M=sweep_lines_part(d,"우측면",left_layout,RAIL_D,RAIL_T,"난간")
        bx=bbox(d); print("  S20021 box",bx,"vol",round(volume(d)),"ww",ww(d)); assert len(bodies(d))==1 and abs(bx[4]-(H_TOP+RAIL_D/2))<0.1 and abs(bx[5]-(DZ+RAIL_D/2))<0.1 and abs(bx[1])<0.1,bx
        set_props(d,{"TITLE":"PLATFORM RAILING, LEFT (용접 일체: 지주 2 + 상부·중간 가로대)","SPEC":f"Ø42.7×2.3T STS304(KS D 3576 32A) 원형 파이프. 지주 2(앞·뒤 기둥 □75 상면 중심 위, 간격 {DZ:.0f}) + 상부 가로대(바닥 위 {H_TOP:.1f}, 상면 3,000 = 종전 □75 난간 높이 유지) + 중간 가로대(중심 바닥 위 {H_MID:.1f} = 종전 위치). 레이아웃 스케치 완전 정의 → 원형 얇은 벽 스윕 한 바디. 제13조 2·5·6호.","Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 종전 □75×75×2.3 가로대(S20003-2·-3)와 기둥 S20002 윗부분(1,230) 대체 — 사용자 지시(난간을 원형으로, 계단 손잡이처럼, 배치는 종전과 같게). 기둥 상면 마감(캡)은 미표현."},mat="AISI 304")
        save_new(d,P_RL); app.CloseDoc(d.GetTitle); rep["S20021"]={"dims":dims,"box":bx}
    # (b) S20022 우측 지주 단품: Ø42.7×2.3 수직 L = H_TOP + D/2 (상단 3,000)
    if not os.path.exists(P_RP):
        d=app.NewDocument(tmpl,0,0,0); L=H_TOP+RAIL_D/2
        assert sel_plane_p(d,"윗면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; c1=sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2)); c2=sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2-RAIL_T)); sm.AddToDB=False
        for c in (c1,c2):
            d.ClearSelection2(True); pv(c,"GetCenterPoint2").Select4(False,NOD); d.Extension.SelectByID2("Point1@원점","EXTSKETCHPOINT",0,0,0,True,0,NOD,0) or d.Extension.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,True,0,NOD,0); d.SketchAddConstraints("sgCOINCIDENT"); d.ClearSelection2(True)
        old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
        try:
            for c,nm,at in ((c1,"외경",(mm(30),mm(30))),(c2,"내경",(mm(-20),mm(20)))):
                d.ClearSelection2(True); c.Select4(False,NOD); dd=d.AddDimension2(at[0],at[1],0); d.ClearSelection2(True); assert dd; dd.GetDimension2(0).Name=nm
        finally: app.SetUserPreferenceToggle(10,old_pref)
        st=d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); assert st==3,st
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; extrude_dir(d,sk,L,"지주_Ø42.7",{1:0.0,4:L})
        set_props(d,{"TITLE":"PLATFORM RAILING POST, RIGHT","SPEC":f"Ø42.7×2.3T STS304(KS D 3576 32A) 수직 L {L:.1f}(기둥 □75 상면 1,769.7 → 상단 3,000). 오른쪽은 종전과 같이 가로대 없음(지주만).","Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"자작. 기둥 S20002 윗부분 대체 — 사용자 지시(원형, 배치는 종전과 같게: 오른쪽 가로대 없음 확인)."},mat="AISI 304")
        save_new(d,P_RP); app.CloseDoc(d.GetTitle); rep["S20022"]={"L":L,"status":st}
    # (c) S20023 뒤 가로대: Ø42.7×2.3 x 방향 L = 2·COL_X − D (지주 면 사이), 원점 = 중앙
    if not os.path.exists(P_RB):
        d=app.NewDocument(tmpl,0,0,0); L=2*COL_X-RAIL_D
        assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; c1=sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2)); c2=sm.CreateCircleByRadius(0,0,0,mm(RAIL_D/2-RAIL_T)); sm.AddToDB=False
        for c in (c1,c2):
            d.ClearSelection2(True); pv(c,"GetCenterPoint2").Select4(False,NOD); d.Extension.SelectByID2("Point1@원점","EXTSKETCHPOINT",0,0,0,True,0,NOD,0) or d.Extension.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,True,0,NOD,0); d.SketchAddConstraints("sgCOINCIDENT"); d.ClearSelection2(True)
        old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
        try:
            for c,nm,at in ((c1,"외경",(mm(30),mm(30))),(c2,"내경",(mm(-20),mm(20)))):
                d.ClearSelection2(True); c.Select4(False,NOD); dd=d.AddDimension2(at[0],at[1],0); d.ClearSelection2(True); assert dd; dd.GetDimension2(0).Name=nm
        finally: app.SetUserPreferenceToggle(10,old_pref)
        st=d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); assert st==3,st
        sk=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; extrude(d,sk,L/2,L/2,"가로대_Ø42.7"); bx=bbox(d); assert abs(bx[0]+L/2)<0.05 and abs(bx[3]-L/2)<0.05,bx
        set_props(d,{"TITLE":"PLATFORM RAILING, REAR RAIL","SPEC":f"Ø42.7×2.3T STS304(KS D 3576 32A) 수평 L {L:.1f}(뒤 지주 면 사이), 상부(상면 3,000)·중간(중심 2,347.3) 2개 — 종전 □75 가로대 S20009-2·-3 위치.","Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"자작. 사용자 지시(원형, 배치는 종전과 같게)."},mat="AISI 304")
        save_new(d,P_RB); app.CloseDoc(d.GetTitle); rep["S20023"]={"L":L,"status":st}
    # (d) S20020 계단 손잡이: rail_sweep_0921 방식(지주 4 + 상부·중간, 지주 Ø42.7), 끝 = 앞 지주 앞면(POST_FRONT)
    z1,y1=nos(1); ZEND=POST_FRONT-z1; NPOST=(1,3,5,7); BOT=-20.0
    def nose(u): return u*TAN
    if not os.path.exists(P_HR):
        d=app.NewDocument(tmpl,0,0,0); ext=d.Extension
        def hr_layout(sk,sm,rel,origin_sel,dim):
            def S(u,v): return sketch_xy(sk,0.0,mm(v),mm(u),1)
            def line(a,b,constr=False):
                p=S(*a); q=S(*b); L=sm.CreateLine(p[0],p[1],0,q[0],q[1],0); assert L is not None,(a,b)
                if constr: L.ConstructionGeometry=True
                return L
            sm.AddToDB=True
            H=line((0,0),(RUN,0),True); V=line((RUN,0),(RUN,RISE),True); Nl=line((0,0),(ZEND,nose(ZEND)),True); u0=-RAIL_START_EXT
            BL=line((u0,nose(u0)+BOT),(ZEND,nose(ZEND)+BOT),True); TL=line((u0,nose(u0)+PL_TOP_OFF),(ZEND,nose(ZEND)+PL_TOP_OFF),True)
            MR=line((u0,nose(u0)+MID_H),(ZEND,nose(ZEND)+MID_H)); TRl=line((u0,nose(u0)+RAIL_H),(ZEND,nose(ZEND)+RAIL_H))
            SL=line((u0,nose(u0)+BOT),(u0,nose(u0)+RAIL_H),True); EL=line((ZEND,nose(ZEND)+BOT),(ZEND,nose(ZEND)+RAIL_H),True)
            posts=[line((RUN*(k-1),nose(RUN*(k-1))+BOT),(RUN*(k-1),nose(RUN*(k-1))+RAIL_H)) for k in NPOST]
            sm.AddToDB=False; sp=lambda L:L.GetStartPoint2; ep=lambda L:L.GetEndPoint2
            def rel_origin(kind,e):
                d.ClearSelection2(True); assert e.Select4(False,NOD); assert origin_sel(True),"origin"; d.SketchAddConstraints(kind); d.ClearSelection2(True)
            rel("sgHORIZONTAL2D",H); rel("sgVERTICAL2D",V); rel("sgVERTICAL2D",SL); rel("sgVERTICAL2D",EL)
            for p in posts: rel("sgVERTICAL2D",p)
            rel_origin("sgCOINCIDENT",sp(H)); rel("sgMERGEPOINTS",sp(Nl),sp(H)); rel("sgMERGEPOINTS",ep(H),sp(V)); rel("sgCOINCIDENT",ep(V),Nl)
            for L in (BL,MR,TRl,TL): rel("sgPARALLEL",L,Nl)
            rel("sgCOINCIDENT",sp(TL),SL); rel("sgCOINCIDENT",ep(TL),EL)
            rel("sgMERGEPOINTS",sp(SL),sp(BL)); rel("sgMERGEPOINTS",ep(SL),sp(TRl)); rel("sgCOINCIDENT",sp(MR),SL)
            rel("sgMERGEPOINTS",sp(EL),ep(BL)); rel("sgMERGEPOINTS",ep(EL),ep(TRl)); rel("sgCOINCIDENT",ep(MR),EL); rel("sgCOINCIDENT",ep(Nl),EL)
            for p in posts: rel("sgCOINCIDENT",sp(p),BL); rel("sgCOINCIDENT",ep(p),TRl)
            rel_origin("sgCOINCIDENT",posts[0])
            def D(name,how,e1,e2,at): p=S(*at); dim(name,how,e1,e2,(p[0],p[1]))
            D("단너비_RUN","len",H,None,(RUN/2,-60)); D("단높이_RISE","len",V,None,(RUN+60,RISE/2)); D("끝_앞지주앞면","h",ep(Nl),None,(ZEND/2,-150)); D("시작_연장","h",sp(SL),None,(u0/2,-220))
            D("지주하단_앞코아래","v",sp(posts[0]),None,(-120,BOT/2)); D("측판윗면_경로하단위","v",sp(TL),sp(BL),(u0-140,nose(u0))); D("상부난간_높이","v",ep(posts[0]),None,(-160,RAIL_H/2)); D("중간난간_간격","v",sp(TRl),sp(MR),(u0-80,nose(u0)+(RAIL_H+MID_H)/2))
            for i in range(1,len(posts)): D(f"지주간격{i}","d",posts[i-1],posts[i],(RUN*(NPOST[i]-1)-RUN,nose(RUN*(NPOST[i]-1))+RAIL_H+120))
            solid=[(TRl.GetName,"난간대1"),(MR.GetName,"난간대2")]+[(p.GetName,f"지주{i+1}") for i,p in enumerate(posts)]
            return solid,{"TL":TL.GetName,"EL":EL.GetName}
        dims,extra,M=sweep_lines_part(d,"우측면",hr_layout,RAIL_D,RAIL_T,"손잡이")
        # 지주 하단 경사컷(측판 윗면선 TL 아래 제거)
        u0=-RAIL_START_EXT; v0=volume(d); assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); sk2=d.SketchManager.ActiveSketch; sm=d.SketchManager
        assert d.Extension.SelectByID2(f"{extra['TL']}@{M}","EXTSKETCHSEGMENT",0,0,0,False,0,NOD,0); assert sm.SketchUseEdge3(False,False); d.ClearSelection2(True)
        c=list(sk2.GetSketchSegments)[0]
        def S2(u,v): return sketch_xy(sk2,0.0,mm(v),mm(u),1)
        DEPTH=400.0; sm.AddToDB=True; pa=S2(u0,nose(u0)+PL_TOP_OFF); pA=S2(u0,-DEPTH); pB=S2(ZEND,-DEPTH); pe=S2(ZEND,nose(ZEND)+PL_TOP_OFF)
        la=sm.CreateLine(pa[0],pa[1],0,pA[0],pA[1],0); lb=sm.CreateLine(pA[0],pA[1],0,pB[0],pB[1],0); le=sm.CreateLine(pB[0],pB[1],0,pe[0],pe[1],0); sm.AddToDB=False
        def rel(kind,*ents):
            d.ClearSelection2(True)
            for i,e in enumerate(ents): assert e.Select4(i>0,NOD),kind
            d.SketchAddConstraints(kind); d.ClearSelection2(True)
        def near(pt,L):
            a_=L.GetStartPoint2; b_=L.GetEndPoint2; return a_ if (a_.X-pt[0])**2+(a_.Y-pt[1])**2<(b_.X-pt[0])**2+(b_.Y-pt[1])**2 else b_
        sp=lambda L:L.GetStartPoint2; ep=lambda L:L.GetEndPoint2
        rel("sgVERTICAL2D",la); rel("sgVERTICAL2D",le); rel("sgHORIZONTAL2D",lb); rel("sgMERGEPOINTS",sp(la),near(pa,c)); rel("sgMERGEPOINTS",ep(la),sp(lb)); rel("sgMERGEPOINTS",ep(lb),sp(le)); rel("sgMERGEPOINTS",ep(le),near(pe,c))
        old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
        try:
            d.ClearSelection2(True); sp(lb).Select4(False,NOD); (ext.SelectByID2("Point1@원점","EXTSKETCHPOINT",0,0,0,True,0,NOD,0) or ext.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,True,0,NOD,0)); q=S2(u0-200,-DEPTH/2); dd=d.AddVerticalDimension2(q[0],q[1],0); d.ClearSelection2(True); assert dd; dd.GetDimension2(0).Name="컷깊이"
        finally: app.SetUserPreferenceToggle(10,old_pref)
        st2=sk2.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        cname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(cname).Name="지주하단_경사컷_스케치"; assert d.Extension.SelectByID2("지주하단_경사컷_스케치","SKETCH",0,0,0,False,0,NOD,0)
        cf=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert cf is not None,"mitre cut"; cf.Name="지주하단_경사컷"
        bs=bodies(d); bx=[round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]; want_ymin=PL_TOP_OFF-(POST_D/2)*TAN; print("  after mitre: bodies",len(bs),"box",bx,"status",st2); assert len(bs)==1 and abs(bx[1]-want_ymin)<0.1,(bx,want_ymin)
        # 끝단 수직컷(앞 지주 앞면)
        assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); sk3=d.SketchManager.ActiveSketch; sm=d.SketchManager
        def S3(u,v): return sketch_xy(sk3,0.0,mm(v),mm(u),1)
        V0=nose(ZEND)+MID_H-150; HH=RAIL_H-MID_H+300; WW=100.0
        q=[S3(ZEND,V0),S3(ZEND,V0+HH),S3(ZEND+WW,V0+HH),S3(ZEND+WW,V0)]; sm.AddToDB=True
        r1=sm.CreateLine(q[0][0],q[0][1],0,q[1][0],q[1][1],0); r2=sm.CreateLine(q[1][0],q[1][1],0,q[2][0],q[2][1],0); r3=sm.CreateLine(q[2][0],q[2][1],0,q[3][0],q[3][1],0); r4=sm.CreateLine(q[3][0],q[3][1],0,q[0][0],q[0][1],0); sm.AddToDB=False
        rel("sgVERTICAL2D",r1); rel("sgVERTICAL2D",r3); rel("sgHORIZONTAL2D",r2); rel("sgHORIZONTAL2D",r4); rel("sgMERGEPOINTS",ep(r1),sp(r2)); rel("sgMERGEPOINTS",ep(r2),sp(r3)); rel("sgMERGEPOINTS",ep(r3),sp(r4)); rel("sgMERGEPOINTS",ep(r4),sp(r1))
        d.ClearSelection2(True); assert r1.Select4(False,NOD); assert d.Extension.SelectByID2(f"{extra['EL']}@{M}","EXTSKETCHSEGMENT",0,0,0,True,0,NOD,0); d.SketchAddConstraints("sgCOLINEAR"); d.ClearSelection2(True)
        old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
        try:
            for nm,how,e1,e2,at in (("끝단컷_하단높이","v",sp(r1),None,(ZEND+250,V0/2)),("끝단컷_높이","len",r1,None,(ZEND+180,V0+HH/2)),("끝단컷_폭","len",r4,None,(ZEND+WW/2,V0-80))):
                d.ClearSelection2(True); assert e1.Select4(False,NOD)
                if how=="v": (ext.SelectByID2("Point1@원점","EXTSKETCHPOINT",0,0,0,True,0,NOD,0) or ext.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,True,0,NOD,0))
                q_=S3(*at); dd=(d.AddVerticalDimension2 if how=="v" else d.AddDimension2)(q_[0],q_[1],0); d.ClearSelection2(True); assert dd,nm; dd.GetDimension2(0).Name=nm
        finally: app.SetUserPreferenceToggle(10,old_pref)
        st3=sk3.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        cname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(cname).Name="끝단_수직컷_스케치"; assert d.Extension.SelectByID2("끝단_수직컷_스케치","SKETCH",0,0,0,False,0,NOD,0)
        cf2=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert cf2 is not None,"end cut"; cf2.Name="끝단_수직컷"
        bs=bodies(d); bx=[round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]; print("  after end cut: bodies",len(bs),"box",bx,"status",st3,"ww",ww(d)); assert len(bs)==1 and abs(bx[5]-ZEND)<0.05 and st2==3 and st3==3
        set_props(d,{"TITLE":"STAIR HANDRAIL (용접 일체: 지주 4 + 상부·중간 난간대)","SPEC":f"난간대·지주 모두 Ø42.7×2.3T STS304(KS D 3576 32A). 레이아웃 스케치 완전 정의(단너비 {RUN:.0f}·단높이 {RISE:.2f}·상부 900·중간 450·지주 간격 {2*RUN:.0f}) → 원형 스윕 한 바디. 지주 하단은 측판(ㅁ 250×50) 윗면 경사 {math.degrees(TH):.1f}°로 절단해 올려 용접, 위쪽 끝은 플랫폼 앞 원형 지주(Ø42.7, z {POST_FRONT:.1f}) 앞면에서 수직 절단해 맞대기 용접. 제13조 2·5·6·7호.","Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"자작. 좌/우 같은 파트 2개. 계단을 바닥판 기준으로 낮추면서(단높이 222.34) 재생성 — 사용자 지시(원형 난간에 새 손잡이). 사용자 작성 S20017-1은 미참조로 보존."},mat="AISI 304")
        save_new(d,P_HR); app.CloseDoc(d.GetTitle); rep["S20020"]={"dims":dims,"box":bx}
# ================= 1c. 판금 변환 후 끝단 재절단(변환이 플랜지 끝을 3.05 넘겨 재생성함) =================
if STAGE=="fixend":
    YG=GROUND-(PLAT_Y+PL_TOP_OFF)
    for path in (P_PL,P_PLL):
        d=app.GetOpenDocumentByName(path) or open_doc(app,path,1); app.ActivateDoc3(path,False,0,I4()); d=app.ActiveDoc; v0=volume(d); bx0=bbox(d); print(os.path.basename(path),"before",bx0,round(v0))
        if bx0[1]<YG-0.05: cut_rect_side(d,"하단_지면컷_판금후",[(0,-3500,-4000),(0,YG,-4000),(0,YG,600),(0,-3500,600)],lambda b: abs(b[1]-YG)<0.05)
        if bx0[4]>-PL_TOP_OFF+0.05: cut_rect_side(d,"상단_수평컷_판금후",[(0,-PL_TOP_OFF,-600),(0,600,-600),(0,600,600),(0,-PL_TOP_OFF,600)],lambda b: abs(b[4]+PL_TOP_OFF)<0.05)
        bx=bbox(d); print("  after",bx,round(volume(d)),"ww",ww(d),"orphans",orphan_sketches(d)); assert abs(bx[1]-YG)<0.05 and abs(bx[4]+PL_TOP_OFF)<0.05 and not ww(d) and not orphan_sketches(d)
        e=I4(); w=I4(); assert d.Save3(1,e,w); app.CloseDoc(d.GetTitle); rep[os.path.basename(path)]={"box":bx,"vol":round(volume(d)) if False else None}
# ================= 2. 기둥 S20002 3000 → 1769.7 =================
if STAGE=="column":
    d=app.GetOpenDocumentByName(P_COL) or open_doc(app,P_COL,1); app.ActivateDoc3(P_COL,False,0,I4()); d=app.ActiveDoc
    bk=os.path.join(BK,"S20002MU0.SLDPRT"); assert os.path.exists(bk)
    dm=d.Parameter("D1@보스-돌출1"); old=round(dm.SystemValue*1000,3); r=dm.SetSystemValue3(mm(COL_L),2,None); d.ForceRebuild3(False); bx=bbox(d); print("S20002 D1",old,"->",round(dm.SystemValue*1000,3),"r",r,"box",bx)
    assert abs((bx[4]-bx[1])-COL_L)<0.05 or abs((bx[5]-bx[2])-COL_L)<0.05 or abs((bx[3]-bx[0])-COL_L)<0.05,bx
    cp=d.Extension.CustomPropertyManager(""); rk=cp.Get("REMARK") or ""
    set_props(d,{"SPEC":"75x75x2.3T L1769.7","DATE":DATE,"REMARK":(rk+" " if rk else "")+"길이 3000 → 1769.7(플랫폼 바닥판 PLATE-02 상면까지). 바닥 위 난간 부분은 원형 파이프 S20021~S20023으로 대체 — 사용자 지시 09-22. 상단 열린 관(캡 미표현)."})
    e=I4(); w=I4(); assert d.Save3(1,e,w); print("saved S20002",e.value,w.value,"ww",ww(d)); rep["S20002"]={"old":old,"new":COL_L,"box":bx}; app.CloseDoc(d.GetTitle)
# ================= 3. 어셈블리 S20000 =================
if STAGE in ("asm","verify"):
    a=app.GetOpenDocumentByName(ASM20); assert a; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; exec(ASM_HELPERS)
if STAGE=="asm":
    a.ForceRebuild3(False); print("before: ww",ww(a))
    for p in (P_PL,P_PLL,P_TR,P_HR,P_RL,P_RP,P_RB):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc
    plan=[(P_PL,[X_IN,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판R"),(P_PLL,[-X_IN,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판L")]
    for k in range(1,8):
        z,y=nos(k); plan.append((P_TR,[0.0,y,z],f"디딤판{k}"))
    z1,y1=nos(1)
    for sx,side in ((1,"R"),(-1,"L")): plan.append((P_HR,[sx*POST_X,y1,z1],f"손잡이{side}"))
    plan+= [(P_RL,[-COL_X,PLAT_Y,COL_ZF],"난간좌"),(P_RP,[COL_X,PLAT_Y,COL_ZF],"지주우앞"),(P_RP,[COL_X,PLAT_Y,COL_ZB],"지주우뒤"),(P_RB,[0.0,PLAT_Y+H_TOP,COL_ZB],"뒤가로대상"),(P_RB,[0.0,PLAT_Y+H_MID,COL_ZB],"뒤가로대중")]
    inserted=[]
    for path,t,tag in plan:
        nm=insert(path,t); made=mate_to_asm(nm,t,tag); g,x=t_ok(nm,t); print(f"  {tag:8s} {nm[:20]:20s} t={x['t_mm']} ok={g}"); assert g; inserted.append((tag,nm,t))
    a.ForceRebuild3(False); print("ww",ww(a),"fixed",[n for n,c in comps().items() if c.IsFixed]); rep["inserted"]=inserted
    for p in (P_PL,P_PLL,P_TR,P_HR,P_RL,P_RP,P_RB):
        dd=app.GetOpenDocumentByName(p)
        if dd is not None and dd.GetSaveFlag: e=I4(); w=I4(); dd.Save3(1,e,w)
if STAGE in ("asm","verify"):
    a.ForceRebuild3(False); a.ClearSelection2(True)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
    print("S20000 interferences",len(res)); [print("   ",v,[c[:18] for c in cs]) for cs,v in res[:30]]; rep["interf"]=res; rep["ww"]=ww(a)
    cc=comps(); rep["boxes"]={n:box(c) for n,c in cc.items()}
    for n,c in sorted(cc.items()):
        if n.startswith(("S20002","S20014","S20015","S20019","S20020","S20021","S20022","S20023","S20007")): print("  ",n[:16],box(c))
    if STAGE=="asm":
        assert not ww(a),ww(a); e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved S20000",e.value,w.value)
        for p in (P_PL,P_PLL,P_TR,P_HR,P_RL,P_RP,P_RB):
            dd=app.GetOpenDocumentByName(p)
            if dd is not None: app.CloseDoc(dd.GetTitle)
        app.ActivateDoc3(Zp("S00000MU0.SLDASM"),False,0,I4()); print("active",app.ActiveDoc.GetTitle)
# ================= 4. 스테이션 검사(S00000, 저장 안 함): 계단 부품 ↔ 외부 간섭, 지면 =================
if STAGE=="station":
    PS=Zp("S00000MU0.SLDASM"); s=app.GetOpenDocumentByName(PS); assert s; app.ActivateDoc3(PS,False,0,I4()); s=app.ActiveDoc; scm=s.ConfigurationManager; cfg0=scm.ActiveConfiguration.Name; s.ForceRebuild3(False)
    out=[]
    def walk(c,depth):
        for ch in (pv(c,"GetChildren") or []):
            if ch.GetSuppression2!=2: continue
            kids=pv(ch,"GetChildren")
            if kids in (None,()): out.append((ch.Name2,ch))
            elif depth<8: walk(ch,depth+1)
    walk(scm.ActiveConfiguration.GetRootComponent3(True),0); short=lambda n:n.split("/")[-1]
    ST=("S20002","S20014","S20015","S20019","S20020","S20021","S20022","S20023")
    stair=[(n,c) for n,c in out if short(n).startswith(ST)]; others=[(n,c) for n,c in out if not short(n).startswith("S200")]
    zmin=min(box(c)[2] for n,c in stair if box(c)); xmax=max(box(c)[3] for n,c in stair if box(c)); print(f"stair parts {len(stair)} others {len(others)} | 계단 월드 z min {zmin:.1f} · x max(지면 쪽) {xmax:.1f} (지면 1109)")
    s.ClearSelection2(True)
    for n,c in stair+others: c.Select4(True,NOD,False)
    idm=s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    rows=[([short(c_.Name2) for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
    ext=[r for r in rows if any(x.startswith(ST) for x in r[0]) and not all(x.startswith("S200") for x in r[0])]
    print(f"[station] all {len(rows)} | stair<->external {len(ext)}: {ext[:10]}"); rep["station"]={"ext":ext,"all":len(rows),"zmin":zmin,"xmax":xmax}
    s.ShowConfiguration2(cfg0); print("station dirty",s.GetSaveFlag,"(저장 안 함)")
json.dump(rep,open(os.path.join(VER,f"stair_round_0922_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE",STAGE)
