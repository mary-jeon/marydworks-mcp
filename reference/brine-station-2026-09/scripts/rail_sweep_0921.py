# 2026-09-21 handrail as ONE part: fully-defined layout sketch (named dims) on Right plane -> circular thin sweeps along sketch lines. Part origin = tread-1 nosing. Use x2 (L/R) at x = +-325.
# usage: rail_sweep_0921.py test | save
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"stair_rebuild_0921b.py"),encoding="utf-8").read().split("# ---------- 0.")[0])
MODE=sys.argv[1] if len(sys.argv)>1 else "test"
P_HR=Zp("S20017MU0.SLDPRT"); BK_RAIL=r"<MCP_DIR>\_backup\20260921-rail"
z1,y1=nos(1); ZEND=PLAT_Z-z1; NPOST=(1,3,5,7); BOT=-20.0     # post path bottom = nose -20 (box top is nose +20; mitre cut later)
def nose(u): return u*TAN
close_unsaved_new(); d=app.NewDocument(tmpl,0,0,0); ext=d.Extension
old_pref=app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10,False)
try:
    assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch; sm=d.SketchManager; sm.AddToDB=True
    def S(u,v): return sketch_xy(sk,0.0,mm(v),mm(u),1)
    def line(a,b,constr=False):
        p=S(*a); q=S(*b); L=sm.CreateLine(p[0],p[1],0,q[0],q[1],0); assert L is not None,(a,b)
        if constr: L.ConstructionGeometry=True
        return L
    H=line((0,0),(RUN,0),True); V=line((RUN,0),(RUN,RISE),True); Nl=line((0,0),(ZEND,nose(ZEND)),True)
    u0=-RAIL_START_EXT
    BL=line((u0,nose(u0)+BOT),(ZEND,nose(ZEND)+BOT),True)
    TL=line((u0,nose(u0)+PL_TOP_OFF),(ZEND,nose(ZEND)+PL_TOP_OFF),True)
    MR=line((u0,nose(u0)+MID_H),(ZEND,nose(ZEND)+MID_H)); TRl=line((u0,nose(u0)+RAIL_H),(ZEND,nose(ZEND)+RAIL_H))
    SL=line((u0,nose(u0)+BOT),(u0,nose(u0)+RAIL_H),True); EL=line((ZEND,nose(ZEND)+BOT),(ZEND,nose(ZEND)+RAIL_H),True)
    posts=[line((RUN*(k-1),nose(RUN*(k-1))+BOT),(RUN*(k-1),nose(RUN*(k-1))+RAIL_H)) for k in NPOST]
    sm.AddToDB=False
    sp=lambda L:L.GetStartPoint2; ep=lambda L:L.GetEndPoint2
    def rel(kind,*ents):
        d.ClearSelection2(True)
        for i,e in enumerate(ents): assert e.Select4(i>0,NOD),kind
        d.SketchAddConstraints(kind); d.ClearSelection2(True)
    def origin_sel(append):
        for nm in ("Point1@원점","Point1@Origin"):
            if ext.SelectByID2(nm,"EXTSKETCHPOINT",0,0,0,append,0,NOD,0): return True
        return False
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
    dims={}
    def dim(name,how,e1,e2,at):
        d.ClearSelection2(True); assert e1.Select4(False,NOD)
        if e2 is not None: assert e2.Select4(True,NOD)
        elif how!="len": assert origin_sel(True)
        p=S(*at); x,y,z=p[0],p[1],0.0
        dd={"h":d.AddHorizontalDimension2,"v":d.AddVerticalDimension2,"len":d.AddDimension2,"d":d.AddDimension2}[how](x,y,z)
        d.ClearSelection2(True); assert dd is not None,name
        dm=dd.GetDimension2(0); dm.Name=name; dims[name]=round(dm.SystemValue*1000,3)
    dim("단너비_RUN","len",H,None,(RUN/2,-60)); dim("단높이_RISE","len",V,None,(RUN+60,RISE/2))
    dim("끝_플랫폼앞코","h",ep(Nl),None,(ZEND/2,-150))
    dim("시작_연장","h",sp(SL),None,(u0/2,-220))
    dim("지주하단_앞코아래","v",sp(posts[0]),None,(-120,BOT/2))
    dim("측판윗면_경로하단위","v",sp(TL),sp(BL),(u0-140,nose(u0)))
    dim("상부난간_높이","v",ep(posts[0]),None,(-160,RAIL_H/2))
    dim("중간난간_간격","v",sp(TRl),sp(MR),(u0-80,nose(u0)+(RAIL_H+MID_H)/2))
    for i in range(1,len(posts)): dim(f"지주간격{i}","d",posts[i-1],posts[i],(RUN*(NPOST[i]-1)-RUN,nose(RUN*(NPOST[i]-1))+RAIL_H+120))
    status=sk.GetConstrainedStatus; print("sketch status",status,"(3 = fully defined)","dims",dims)
    assert status==3,("master sketch not fully defined",status)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    skname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(skname).Name="난간_레이아웃"; M="난간_레이아웃"
    msegs=d.FeatureByName(M).GetSpecificFeature2.GetSketchSegments
    def is_vert(s_):
        a=s_.GetStartPoint2; b=s_.GetEndPoint2; return abs(a.X-b.X)<1e-9 or abs(a.Y-b.Y)<1e-9
    solid=[(s_.GetName,is_vert(s_)) for s_ in msegs if not s_.ConstructionGeometry]; assert len(solid)==6,solid
    tl_name=TL.GetName; el_name=EL.GetName
    n_rail=0; n_post=0
    for nm,isp in sorted(solid,key=lambda t:t[1]):          # rails first, then posts
        assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True)
        assert d.Extension.SelectByID2(f"{nm}@{M}","EXTSKETCHSEGMENT",0,0,0,False,0,NOD,0); assert d.SketchManager.SketchUseEdge3(False,False)
        st=d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        pname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; pf=d.FeatureByName(pname)
        if isp: n_post+=1; tag=f"지주{n_post}"
        else: n_rail+=1; tag=f"난간대{n_rail}"
        pf.Name=f"경로_{tag}"; dia,th=(POST_D,POST_T) if isp else (RAIL_D,RAIL_T)
        fd=d.FeatureManager.CreateDefinition(17); fd.CircularProfile=True; fd.CircularProfileDiameter=mm(dia); fd.Merge=True; fd.ThinFeature=True; fd.ThinWallType=1; fd.SetWallThickness(True,mm(th)); fd.SetWallThickness(False,mm(th))
        d.ClearSelection2(True); assert d.Extension.SelectByID2(f"경로_{tag}","SKETCH",0,0,0,False,4,NOD,0)
        f=d.FeatureManager.CreateFeature(fd); d.ClearSelection2(True); assert f is not None,("sweep failed",tag); f.Name=f"스윕_{tag}"
        print(f"  {tag}: path status {st}, D{dia}x{th}, bodies {len(bodies(d))}, vol {volume(d):.0f}")
    # post bottom mitre: cut everything below the stringer top line (TL)
    v0=volume(d); assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); sk2=d.SketchManager.ActiveSketch; sm=d.SketchManager
    assert d.Extension.SelectByID2(f"{tl_name}@{M}","EXTSKETCHSEGMENT",0,0,0,False,0,NOD,0); assert sm.SketchUseEdge3(False,False); d.ClearSelection2(True)
    c=list(sk2.GetSketchSegments)[0]
    def S2(u,v): return sketch_xy(sk2,0.0,mm(v),mm(u),1)
    DEPTH=400.0; sm.AddToDB=True
    pa=S2(u0,nose(u0)+PL_TOP_OFF); pA=S2(u0,-DEPTH); pB=S2(ZEND,-DEPTH); pe=S2(ZEND,nose(ZEND)+PL_TOP_OFF)
    la=sm.CreateLine(pa[0],pa[1],0,pA[0],pA[1],0); lb=sm.CreateLine(pA[0],pA[1],0,pB[0],pB[1],0); le=sm.CreateLine(pB[0],pB[1],0,pe[0],pe[1],0); sm.AddToDB=False
    def near(pt,L):
        a=L.GetStartPoint2; b=L.GetEndPoint2; return a if (a.X-pt[0])**2+(a.Y-pt[1])**2<(b.X-pt[0])**2+(b.Y-pt[1])**2 else b
    rel("sgVERTICAL2D",la); rel("sgVERTICAL2D",le); rel("sgHORIZONTAL2D",lb)
    rel("sgMERGEPOINTS",sp(la),near(pa,c)); rel("sgMERGEPOINTS",ep(la),sp(lb)); rel("sgMERGEPOINTS",ep(lb),sp(le)); rel("sgMERGEPOINTS",ep(le),near(pe,c))
    S=S2; dim("컷깊이","v",sp(lb),None,(u0-200,-DEPTH/2)); st2=sk2.GetConstrainedStatus; print("cut sketch status",st2)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    cname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(cname).Name="지주하단_경사컷_스케치"
    assert d.Extension.SelectByID2("지주하단_경사컷_스케치","SKETCH",0,0,0,False,0,NOD,0)
    cf=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert cf is not None,"mitre cut"; cf.Name="지주하단_경사컷"
    bs=bodies(d); bx=[round(v*1000,2) for v in pv(bs[0],"GetBodyBox")] if len(bs)==1 else None
    print("after mitre: bodies",len(bs),"box",bx,"dv",round(v0-volume(d)),"ww",ww(d))
    want_ymin=PL_TOP_OFF-(POST_D/2)*TAN; assert len(bs)==1 and abs(bx[1]-want_ymin)<0.1,(bx,want_ymin); assert abs(bx[3]-POST_D/2)<0.05 and abs(bx[0]+POST_D/2)<0.05,("wall went outward",bx)
    # rail upper ends: vertical cut at the platform post front face (u = ZEND); rectangle's left edge collinear with master EL
    assert sel_plane_p(d,"우측면"); d.SketchManager.InsertSketch(True); sk3=d.SketchManager.ActiveSketch; sm=d.SketchManager
    def S3(u,v): return sketch_xy(sk3,0.0,mm(v),mm(u),1)
    V0=2000.0; HH=700.0; WW=100.0; assert V0<nose(ZEND)+MID_H-60 and V0+HH>nose(ZEND)+RAIL_H+60
    q=[S3(ZEND,V0),S3(ZEND,V0+HH),S3(ZEND+WW,V0+HH),S3(ZEND+WW,V0)]; sm.AddToDB=True
    r1=sm.CreateLine(q[0][0],q[0][1],0,q[1][0],q[1][1],0); r2=sm.CreateLine(q[1][0],q[1][1],0,q[2][0],q[2][1],0); r3=sm.CreateLine(q[2][0],q[2][1],0,q[3][0],q[3][1],0); r4=sm.CreateLine(q[3][0],q[3][1],0,q[0][0],q[0][1],0); sm.AddToDB=False
    rel("sgVERTICAL2D",r1); rel("sgVERTICAL2D",r3); rel("sgHORIZONTAL2D",r2); rel("sgHORIZONTAL2D",r4)
    rel("sgMERGEPOINTS",ep(r1),sp(r2)); rel("sgMERGEPOINTS",ep(r2),sp(r3)); rel("sgMERGEPOINTS",ep(r3),sp(r4)); rel("sgMERGEPOINTS",ep(r4),sp(r1))
    d.ClearSelection2(True); assert r1.Select4(False,NOD); assert d.Extension.SelectByID2(f"{el_name}@{M}","EXTSKETCHSEGMENT",0,0,0,True,0,NOD,0); d.SketchAddConstraints("sgCOLINEAR"); d.ClearSelection2(True)
    S=S3; dim("끝단컷_하단높이","v",sp(r1),None,(ZEND+250,V0/2)); dim("끝단컷_높이","len",r1,None,(ZEND+180,V0+HH/2)); dim("끝단컷_폭","len",r4,None,(ZEND+WW/2,V0-80))
    st3=sk3.GetConstrainedStatus; print("end cut sketch status",st3)
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    cname=[n for n,t in feats(d) if t=="ProfileFeature"][-1]; d.FeatureByName(cname).Name="끝단_수직컷_스케치"
    assert d.Extension.SelectByID2("끝단_수직컷_스케치","SKETCH",0,0,0,False,0,NOD,0)
    cf2=d.FeatureManager.FeatureCut4(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False,False); d.EditRebuild3; assert cf2 is not None,"end cut"; cf2.Name="끝단_수직컷"
    bs=bodies(d); bx=[round(v*1000,2) for v in pv(bs[0],"GetBodyBox")] if len(bs)==1 else None
    print("after end cut: bodies",len(bs),"box",bx,"ww",ww(d)); assert len(bs)==1 and abs(bx[5]-ZEND)<0.05,(bx,ZEND); assert st3==3 and st2==3
    rep={"dims":dims,"master_status":status,"cut_status":st2,"box":bx,"volume_mm3":round(volume(d)),"want_ymin":want_ymin}
    set_props(d,{"TITLE":"STAIR HANDRAIL (용접 일체: 지주 4 + 상부·중간 난간대)","SPEC":f"난간대 Ø42.7×2.3T(KS D 3576 32A)·지주 Ø48.6×3.7T(40A Sch40) STS304. 레이아웃 스케치 1장(완전 정의, 치수: 단너비 {RUN:.0f}·단높이 {RISE:.2f}·상부 900·중간 450·지주 간격 {2*RUN:.0f}) → 선을 경로로 원형 스윕, 한 바디. 지주 하단은 측판(ㅁ 250×50) 윗면 경사 {math.degrees(TH):.1f}°로 절단해 윗면 위에 올려 용접. 제13조 2·5·6·7호.","Material":"STS304","QT'Y":"2","DATE":DATE,"REMARK":"자작. 좌/우 같은 파트 2개(평면 대칭). 개별 파트 S20016(지주)·구 S20017·S20018 대체 — 사용자 지시(선으로 그려 스윕, 연결되게, 하나로 좌/우)."},mat="AISI 304")
    if MODE=="save":
        a=app.GetOpenDocumentByName(ASM20); assert a,"S20000 not loaded"; app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc; cm=a.ConfigurationManager
        exec(ASM_HELPERS)
        cc=comps(); old=[n for n in cc if n.split("/")[-1].startswith(("S20016","S20017","S20018"))]; print("remove from asm",len(old),old)
        for n in old: a.ClearSelection2(True); cc[n].Select4(False,NOD,False); a.Extension.DeleteSelection2(0)
        a.EditRebuild3; print("asm ww",ww(a))
        bk=os.path.join(BK_RAIL,"S20017MU0.SLDPRT"); assert os.path.exists(bk) and os.path.getsize(bk)==os.path.getsize(P_HR),"backup S20017"
        if app.GetOpenDocumentByName(P_HR) is not None: app.CloseDoc(P_HR)
        assert app.GetOpenDocumentByName(P_HR) is None
        app.ActivateDoc3(d.GetTitle,False,0,I4()); save_new(d,P_HR)
        app.ActivateDoc3(ASM20,False,0,I4()); a=app.ActiveDoc
        for sx,side in ((1,"R"),(-1,"L")):
            t=[sx*POST_X,y1,z1]; nm=insert(P_HR,t); made=mate_to_asm(nm,t,f"난간{side}"); g,x=t_ok(nm,t); print(f"  난간{side} {nm} t={x['t_mm']} ok={g}"); assert g
        a.ForceRebuild3(False); print("asm ww",ww(a)); a.ClearSelection2(True)
        idm=a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference=False; idm.TreatSubAssembliesAsComponents=False; idm.IncludeMultibodyPartInterferences=False; idm.MakeInterferingPartsTransparent=False
        res=sorted([([c_.Name2 for c_ in (pv(it,"Components") or [])],round(it.Volume*1e9,1)) for it in (pv(idm,"GetInterferences") or [])],key=lambda r:-r[1]); idm.Done(); a.ClearSelection2(True)
        print("S20000 interferences",len(res)); [print("   ",v,cs) for cs,v in res[:12]]; rep["interf"]=res
        rep["boxes"]={n:box(c) for n,c in comps().items() if n.startswith("S20017")}; print(rep["boxes"])
    json.dump(rep,open(os.path.join(VER,f"rail_sweep_0921_{MODE}.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
finally:
    app.SetUserPreferenceToggle(10,old_pref)
print("DONE",MODE)
