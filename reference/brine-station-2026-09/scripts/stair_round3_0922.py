# 2026-09-22 저녁: 사용자 손잡이 S20017-1 복원 — (1) 경사 D3 조정(stair_round2 handrail 단계에서 메모리 반영됨) 후 끊긴 컷-돌출4(지주·다리 하단을 난간 중심선 아래 852.5(수직)에서 경사 절단)를 같은 규칙의 닫힌 다각형 컷으로 재작성
#  (2) 어셈블리에 y축 180° 회전 배치(종전 배치 실측: 다리가 계단 시작 쪽, 원점 z 280.9, 난간 중심선 = 앞코선 위 872.5)
# usage: stair_round3_0922.py handrail2 | asm | station
import os, sys
_here=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,_here)
_src2=open(os.path.join(_here,"stair_round2_0922.py"),encoding="utf-8").read()
exec(_src2.split("# 0. 어셈블리에서")[0].replace('rep={"stage":STAGE+"_r2"}','rep={"stage":STAGE+"_r3"}'))
RAIL_ABOVE_NOSE=872.5; TRIM_BELOW_RAIL=RAIL_ABOVE_NOSE-PL_TOP_OFF     # 852.5 (수직)
T_Z=280.9; R180=[-1.0,0,0, 0,1.0,0, 0,0,-1.0]
print(f"handrail: rail above nose {RAIL_ABOVE_NOSE}, trim below rail {TRIM_BELOW_RAIL}")
if STAGE=="handrail2":
    d=app.GetOpenDocumentByName(P_UHR) or open_doc(app,P_UHR,1); app.ActivateDoc3(P_UHR,False,0,I4()); d=app.ActiveDoc
    D3=round(d.Parameter("D3@스케치1").SystemValue*1000,3); assert abs(D3-2408.143)<0.01,("D3 not adjusted yet",D3)
    for nm,typ in (("컷-돌출4","BODYFEATURE"),("스케치42","SKETCH")):
        d.ClearSelection2(True)
        if d.Extension.SelectByID2(nm,typ,0,0,0,False,0,NOD,0): d.Extension.DeleteSelection2(0); print("  deleted",nm)
    d.EditRebuild3; print("  after delete ww",ww(d),"orphans",orphan_sketches(d)); assert not ww(d)
    v0=volume(d); bx0=bbox(d)
    # 난간 중심선(원점 통과): 모델 y = −TAN·z (사용자 스케치 규약: 모델 z = −스케치 x). 절단선 = 중심선 − 852.5(수직). 아래쪽 영역 닫힌 다각형 → 양방향 관통 컷
    def trim_y(z): return -TAN*z-TRIM_BELOW_RAIL
    poly=[(0,trim_y(-1000),-1000),(0,trim_y(1000),1000),(0,-2600,1000),(0,-2600,-1000)]
    done=False
    for conv in (0,1):
        assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); skobj=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
        sp=[sketch_xy(skobj,mm(q[0]),mm(q[1]),mm(q[2]),conv) for q in poly]
        for i in range(4): sm.CreateLine(sp[i][0],sp[i][1],0,sp[(i+1)%4][0],sp[(i+1)%4][1],0)
        sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        skc=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.Extension.SelectByID2(skc,"SKETCH",0,0,0,False,0,NOD,0)
        c=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3
        if c is None: clean_orphans(d); continue
        v1=volume(d); bs=bodies(d)
        # 새 경사면: 법선이 난간 방향에 수직(경사면 ⟂ 검사), 개수 4(지주 3 + 다리)
        b=bs[0] if bs else None; incl=[]
        if b is not None:
            for fc in (pv(b,"GetFaces") or []):
                s_=fc.GetSurface
                if s_.IsPlane:
                    n=[round(v,3) for v in pv(fc,"Normal")]
                    if abs(n[0])<0.01 and 0.5<abs(n[1])<0.9: incl.append((n,[round(v*1000,1) for v in pv(fc,"GetBox")],round(fc.GetArea*1e6)))
        print(f"  trim cut conv {conv}: removed {round(v0-v1)} bodies {len(bs)} inclined faces {len(incl)} {[(x[0],x[2]) for x in incl][:5]}")
        if len(bs)==1 and 30000<(v0-v1)<200000 and len(incl)==4: c.Name="지주하단_경사컷_0922"; d.FeatureByName(skc).Name="지주하단_경사컷_스케치_0922"; done=True; break
        c.Select2(False,0); d.EditDelete(); d.EditRebuild3; clean_orphans(d)
    assert done,"trim cut"
    bx=bbox(d); print("  handrail box",bx,"vol",round(volume(d)),"ww",ww(d),"orphans",orphan_sketches(d)); assert not ww(d) and not orphan_sketches(d)
    cp=d.Extension.CustomPropertyManager(""); rk=cp.Get("REMARK") or ""
    cp.Set2("REMARK",rk+f" 컷-돌출4(지주·다리 하단 경사 절단, 스케치 평면 참조가 D3 변경으로 끊김·절단량 0)를 같은 규칙(난간 중심선 아래 수직 {TRIM_BELOW_RAIL:.1f} = 측판 윗면선)의 닫힌 다각형 컷 「지주하단_경사컷_0922」로 대체.")
    e=I4(); w=I4(); assert d.Save3(1,e,w); print("  saved S20017-1"); rep["S20017-1"]={"D3":D3,"box":bx,"vol":round(volume(d))}; app.CloseDoc(d.GetTitle)
if STAGE in ("asm","verify"):
    a=app.GetOpenDocumentByName(ASM20); assert a; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager; exec(ASM_HELPERS)
    def t_okR(comp,R_exp,t_exp):
        a.EditRebuild3; x=xform(comps()[comp]); dR=max(abs(x["R"][i][j]-R_exp[i][j]) for i in range(3) for j in range(3)); dt=max(abs(p-q) for p,q in zip(x["t_mm"],t_exp)); return dR<1e-3 and dt<0.02,x
    def insert_R(path,t,R9):
        c=a.AddComponent5(path,0,"",False,"",mm(t[0]),mm(t[1]),mm(t[2])); assert c is not None,path
        arr=list(R9)+[mm(t[0]),mm(t[1]),mm(t[2]),1.0,0.0,0.0,0.0]; xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf; a.EditRebuild3
        if c.IsFixed: a.ClearSelection2(True); c.Select4(False,NOD,False); a.UnfixComponent(); a.ClearSelection2(True)
        return c.Name2
    def mate_R(comp,t,R_exp,tag):
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
                g,x=t_okR(comp,R_exp,t)
                if g and not ww(a): made.append(name); done=True; break
                del_mate(name)
            assert done,("mate failed",comp,name)
        return made
if STAGE=="asm":
    cc=comps(); old=[n for n in cc if n.split("/")[-1].startswith(("S20014","S20015","S20019","S20017","S20020"))]
    for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
    a.EditRebuild3; print("removed",sorted(old),"ww",ww(a))
    for p in (P_PL,P_PLL,P_TR,P_UHR):
        if app.GetOpenDocumentByName(p) is None: open_doc(app,p,1)
    app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc
    plan=[(P_PL,[X_IN,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판R"),(P_PLL,[-X_IN,PLAT_Y+PL_TOP_OFF,PLAT_Z],"측판L")]
    for k in range(1,8):
        z,y=nos(k); plan.append((P_TR,[0.0,y,z],f"디딤판{k}"))
    inserted=[]
    for path,t,tag in plan:
        nm=insert(path,t); made=mate_to_asm(nm,t,tag); g,x=t_ok(nm,t); print(f"  {tag:8s} {nm[:20]:20s} t={x['t_mm']} ok={g}"); assert g; inserted.append((tag,nm,t))
    z1,y1=nos(1); ty=y1+(T_Z-z1)*TAN+RAIL_ABOVE_NOSE; R_exp=[[-1,0,0],[0,1,0],[0,0,-1]]
    for sx,side in ((1,"R"),(-1,"L")):
        t=[sx*325.0,ty,T_Z]; nm=insert_R(P_UHR,t,R180); made=mate_R(nm,t,R_exp,f"손잡이{side}"); g,x=t_okR(nm,R_exp,t); print(f"  손잡이{side} {nm} t={x['t_mm']} R={x['R']} ok={g}"); assert g; inserted.append((f"손잡이{side}",nm,t))
    a.ForceRebuild3(False); print("ww",ww(a)); rep["inserted"]=inserted; rep["handrail_t"]=[325.0,ty,T_Z]
if STAGE in ("asm","verify"):
    a.ForceRebuild3(False); a.ClearSelection2(True)
    idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
    res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
    print("S20000 interferences",len(res)); [print("   ",v,[c[:18] for c in cs]) for cs,v in res[:30]]; rep["interf"]=res; rep["ww"]=ww(a)
    cc=comps(); rep["boxes"]={n:box(c) for n,c in cc.items()}
    for n,c in sorted(cc.items()):
        if n.startswith(("S20014","S20015","S20019","S20017","S20021","S20022")): print("  ",n[:16],box(c))
    hb=[box(c) for n,c in cc.items() if n.startswith("S20017")][0]; z1,y1=nos(1)
    print(f"  손잡이 z {hb[2]}~{hb[5]} (앞 지주 앞면 {POST_FRONT}, 간격 {round(POST_FRONT-hb[5],1)}) | y min {hb[1]} vs 측판 윗면선@z{hb[2]}: {round(y1+(hb[2]-z1)*TAN+PL_TOP_OFF,1)} | y max {hb[4]} = 앞코선@z{hb[5]} {round(y1+(hb[5]-z1)*TAN,1)} + {round(hb[4]-(y1+(hb[5]-z1)*TAN),1)}")
    if STAGE=="asm":
        assert not ww(a),ww(a); e=I4(); w=I4(); assert a.Save3(1,e,w); print("saved S20000",e.value,w.value)
        for p in (P_PL,P_PLL,P_TR,P_UHR):
            dd=app.GetOpenDocumentByName(p)
            if dd is not None: app.CloseDoc(dd.GetTitle)
        app.ActivateDoc3(Zp("S00000MU0.SLDASM"),False,0,I4()); print("active",app.ActiveDoc.GetTitle)
if STAGE=="station":
    exec(_src[_src.index('if STAGE=="station":')+len('if STAGE=="station":'):_src.index("json.dump(rep,open(os.path.join(VER,f\"stair_round_0922_{STAGE}.json\")")].replace("\n    ","\n").replace('ST=("S20002","S20014","S20015","S20019","S20020","S20021","S20022","S20023")','ST=("S20002","S20014","S20015","S20019","S20017","S20021","S20022","S20023")'))
json.dump(rep,open(os.path.join(VER,f"stair_round3_0922_{STAGE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str); print("DONE",STAGE)
