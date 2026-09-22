# 2026-09-22 저녁 정정(사용자 「손잡이는 내가 만든 S20017-1로 돌려내라 · 계단은 로봇 타이어 지면까지」):
#  지면 = 로봇 타이어 접지 월드 x 1,100.2 → S20000 로컬 y −50.2 (플랫폼 기둥 하단 1,050 기준). 총 높이 1,819.9 = 8단 × 227.49, 단너비 205 → 47.97°
#  손잡이 = 사용자 파트 S20017-1(형태 유지): 경사를 정하는 치수 D3@스케치1 만 새 경사에 맞게 조정(시컨트 반복), 배치는 종전과 같은 규칙(원점 z = 종전 236.2, 난간 중심선이 앞코선 위 같은 높이)
# usage: stair_round2_0922.py asmdel | parts | handrail | asm | station
import os, sys
_here=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,_here)
_src=open(os.path.join(_here,"stair_round_0922.py"),encoding="utf-8").read()
_hdr=_src.split("# ================= 0.")[0].replace('STAGE=sys.argv[1]; rep={"stage":STAGE}','STAGE=sys.argv[1]; rep={"stage":STAGE+"_r2"}')
exec(_hdr)
# ---- 지면 재정의 ----
TIRE_X=1100.2; COL_BOTTOM_X=1050.0; GROUND=-(TIRE_X-COL_BOTTOM_X)
RISE=(PLAT_Y-GROUND)/N; TH=math.atan2(RISE,RUN); TAN=math.tan(TH); COS=math.cos(TH); SIN=math.sin(TH)
P_UHR=Zp("S20017-1MU0.SLDPRT"); OLD_T=(325.0,1988.8,236.2); OLD_NOSE1=(-455.0,236.25); OLD_TAN=math.tan(math.atan2(245.25,205.0))
OFF_ABOVE_NOSE=OLD_T[1]-(OLD_NOSE1[1]+(OLD_T[2]-OLD_NOSE1[0])*OLD_TAN)     # 종전 배치에서 원점(난간 중심선)이 앞코선 위 얼마였나
print(f"layout2: GROUND {GROUND} RISE {RISE:.4f} TH {math.degrees(TH):.2f}° | user handrail offset above nose line {OFF_ABOVE_NOSE:.1f}")
# 0. 어셈블리에서 현 계단(측판·디딤판·내 손잡이 S20020) 제거
if STAGE=="asmdel":
    a=app.GetOpenDocumentByName(ASM20); assert a; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; exec(ASM_HELPERS)
    cc=comps(); old=[n for n in cc if n.split("/")[-1].startswith(("S20014","S20015","S20019","S20020"))]; print("remove",sorted(old))
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3; print("remaining",sorted(comps()),"ww",ww(a))
    for p in (P_PL,P_PLL,P_TR,P_HR):
        dd=app.GetOpenDocumentByName(p)
        if dd is not None: app.CloseDoc(dd.GetTitle)
    e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved S20000 (parts removed)")
# 1. 측판 재생성(GROUND −50.2) — stair_round_0922 의 build_stringer 를 새 GROUND 로 실행
if STAGE=="parts":
    close_unsaved_new()
    exec(_src[_src.index("    def build_stringer(path,sgn,title_side):")+4:_src.index("    build_stringer(P_PL,+1,\"우\"); build_stringer(P_PLL,-1,\"좌\")")].replace("\n    ","\n"))
    build_stringer(P_PL,+1,"우"); build_stringer(P_PLL,-1,"좌")
    YG=GROUND-(PLAT_Y+PL_TOP_OFF)
    for path in (P_PL,P_PLL):
        d=app.GetOpenDocumentByName(path) or open_doc(app,path,1); app.ActivateDoc3(path,False,0,I4()); d=app.ActiveDoc; bx0=bbox(d)
        if bx0[1]<YG-0.05: cut_rect_side(d,"하단_지면컷_판금후",[(0,-3500,-4000),(0,YG,-4000),(0,YG,600),(0,-3500,600)],lambda b: abs(b[1]-YG)<0.05)
        bx=bbox(d); assert abs(bx[1]-YG)<0.05 and abs(bx[4]+PL_TOP_OFF)<0.05 and not ww(d) and not orphan_sketches(d),(bx,ww(d))
        cp=d.Extension.CustomPropertyManager(""); sp=cp.Get("SPEC"); cp.Set2("SPEC",sp.replace("하단 지면 절단","하단 지면 절단(지면 = 로봇 타이어 접지, 플랫폼 기둥 하단보다 50.2 아래)"))
        e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved",os.path.basename(path),bx); app.CloseDoc(d.GetTitle)
# 2. 사용자 손잡이 S20017-1: D3 로 경사 맞춤
if STAGE=="handrail":
    d=app.GetOpenDocumentByName(P_UHR) or open_doc(app,P_UHR,1); app.ActivateDoc3(P_UHR,False,0,I4()); d=app.ActiveDoc
    bk=os.path.join(BK,"S20017-1MU0.SLDPRT"); assert os.path.exists(bk)
    def rail():
        sk=d.FeatureByName("스케치1").GetSpecificFeature2
        for s_ in pv(sk,"GetSketchSegments"):
            if pv(s_,"GetType")==0:
                a_=pv(s_,"GetStartPoint2"); b_=pv(s_,"GetEndPoint2")
                if abs(a_.X-b_.X)>1e-6: return (a_.X*1000,a_.Y*1000),(b_.X*1000,b_.Y*1000)
    def slope():
        (x0,y0),(x1,y1)=rail(); return (y1-y0)/(x1-x0)
    dm=d.Parameter("D3@스케치1"); d3_0=dm.SystemValue*1000; s0=slope(); target=TAN; print("  D3",d3_0,"slope",round(s0,5),"target",round(target,5))
    x_a,f_a=d3_0,s0-target; dm.SystemValue=mm(d3_0-30); d.EditRebuild3; x_b,f_b=d3_0-30,slope()-target
    for _ in range(12):
        if abs(f_b)<1e-7: break
        x_n=x_b-f_b*(x_b-x_a)/(f_b-f_a); dm.SystemValue=mm(x_n); d.EditRebuild3; x_a,f_a,x_b,f_b=x_b,f_b,x_n,slope()-target; print(f"   D3 {x_n:.4f} slope err {f_b:.2e}")
    assert abs(f_b)<1e-6,f_b; D3=round(dm.SystemValue*1000,3)
    posts=[]
    sk2=d.FeatureByName("스케치19").GetSpecificFeature2
    for s_ in pv(sk2,"GetSketchSegments"):
        if pv(s_,"GetType")==0 and not s_.ConstructionGeometry:
            a_=pv(s_,"GetStartPoint2"); b_=pv(s_,"GetEndPoint2"); posts.append((round(a_.X*1000,1),round(min(a_.Y,b_.Y)*1000,1),round(max(a_.Y,b_.Y)*1000,1)))
    (x0,y0),(x1,y1)=rail(); bs=bodies(d); bx=[round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
    print("  rail",(round(x0,1),round(y0,1)),(round(x1,1),round(y1,1)),"angle",round(math.degrees(math.atan(slope())),3),"posts",sorted(posts),"box",bx,"ww",ww(d),"bodies",len(bs))
    assert not ww(d) and len(bs)==1
    cp=d.Extension.CustomPropertyManager(""); rk=cp.Get("REMARK") or ""
    cp.Set2("REMARK",(rk+" " if rk else "")+f"09-22: 계단 경사 50.0°→{math.degrees(TH):.2f}°(지면 = 로봇 타이어 접지, 8단×{RISE:.2f}, 단너비 205)에 맞춰 D3@스케치1 2443.461→{D3}만 조정(형태·치수 그 외 불변). 사용자 모델링 파트.")
    e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved S20017-1 D3",D3); rep["S20017-1"]={"D3":D3,"angle":math.degrees(math.atan(slope())),"posts":posts,"box":bx}; app.CloseDoc(d.GetTitle)
# 3. 어셈블리
if STAGE in ("asm","verify"):
    a=app.GetOpenDocumentByName(ASM20); assert a; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; exec(ASM_HELPERS)
if STAGE=="asm":
    for p in (P_PL,P_PLL,P_TR,P_UHR):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc
    plan=[(P_PL,[X_IN,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판R"),(P_PLL,[-X_IN,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판L")]
    for k in range(1,8):
        z,y=nos(k); plan.append((P_TR,[0.0,y,z],f"디딤판{k}"))
    z1,y1=nos(1); ty=y1+(OLD_T[2]-z1)*TAN+OFF_ABOVE_NOSE
    for sx,side in ((1,"R"),(-1,"L")): plan.append((P_UHR,[sx*OLD_T[0],ty,OLD_T[2]],f"손잡이{side}"))
    inserted=[]
    for path,t,tag in plan:
        nm=insert(path,t); made=mate_to_asm(nm,t,tag); g,x=t_ok(nm,t); print(f"  {tag:8s} {nm[:20]:20s} t={x['t_mm']} ok={g}"); assert g; inserted.append((tag,nm,t))
    a.ForceRebuild3(False); print("ww",ww(a)); rep["inserted"]=inserted; rep["handrail_t"]=[OLD_T[0],ty,OLD_T[2]]
if STAGE in ("asm","verify"):
    a.ForceRebuild3(False); a.ClearSelection2(True)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
    print("S20000 interferences",len(res)); [print("   ",v,[c[:18] for c in cs]) for cs,v in res[:30]]; rep["interf"]=res; rep["ww"]=ww(a)
    cc=comps(); rep["boxes"]={n:box(c) for n,c in cc.items()}
    for n,c in sorted(cc.items()):
        if n.startswith(("S20014","S20015","S20019","S20017","S20021","S20022")): print("  ",n[:16],box(c))
    # 손잡이 위쪽 끝 ↔ 앞 원형 지주 앞면 z 996.15 간격, 손잡이 지주 하단 ↔ 측판 윗면
    hb=[box(c) for n,c in cc.items() if n.startswith("S20017")][0]; print("  손잡이 z max",hb[5],"→ 앞 지주 앞면",POST_FRONT,"간격",round(POST_FRONT-hb[5],1)," | 손잡이 y min",hb[1],"지면",GROUND)
    if STAGE=="asm":
        assert not ww(a),ww(a); e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved S20000",e.value,w.value)
        for p in (P_PL,P_PLL,P_TR,P_UHR):
            dd=app.GetOpenDocumentByName(p)
            if dd is not None: app.CloseDoc(dd.GetTitle)
        app.ActivateDoc3(Zp("S00000MU0.SLDASM"),False,0,I4()); print("active",app.ActiveDoc.GetTitle)
if STAGE=="station":
    exec(_src[_src.index('if STAGE=="station":')+len('if STAGE=="station":'):_src.index("json.dump(rep,open(os.path.join(VER,f\"stair_round_0922_{STAGE}.json\")")].replace("\n    ","\n").replace('ST=("S20002","S20014","S20015","S20019","S20020","S20021","S20022","S20023")','ST=("S20002","S20014","S20015","S20019","S20017","S20021","S20022","S20023")'))
json.dump(rep,open(os.path.join(VER,f"stair_round2_0922_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE",STAGE)
