"""09-08 저녁: 산안규칙 제13조(안전난간) 저스트 보완 — 사용자 「법규는 맞춰야지 쩌스트하게, 통과할 정도로만」
 stage edit    : S20005 지주 400→450 (D1@보스-돌출1), S20004 상부 난간대 스케치3 '400'→450·D4 150→193.3 (제자리 치수 편집) → 앞코 기준 높이 검증
 stage midrail : 신규 S20013MU0 중간 난간대 Ø27.2×2.0T (지주 사이 4절 다중바디, 상단 마이터) → S20000MU0에 2개 삽입
 stage toe     : 신규 S10012MU0(+y 변, L1076)·S10013MU0(z 끝, L1400) 발끝막이판 100×3.2T STS304 → S10000MU0 삽입
 stage save    : S20004·S20005·S20000MU0·S10000MU0 저장 (S00000MU0는 저장 안 함)
 좌표: 월드(S00000MU0) −x 상방. S20000MU0 로컬 = (wy+1150, 1100−wx, wz+2230). S10000MU0 로컬 = 월드.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
stop=watchdog(); app=connect()
OUT=r"<PROJECT_DIR>\_검증\stair_law_0908"
stages=sys.argv[1:] or ["edit"]
mm=lambda v:v/1000.0
tmpl=app.GetUserPreferenceStringValue(8)
log={}
def J(name,obj): json.dump(obj,open(os.path.join(OUT,name),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
def ww(doc):
    a,b,c=[VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None) for _ in range(3)]; doc.Extension.GetWhatsWrong(a,b,c); return [(x.Name,y) for x,y in zip(a.value or [],b.value or [])]
def interf(doc):
    app.ActivateDoc3(doc.GetPathName,False,0,I4()); idm=pv(doc,"InterferenceDetectionManager")   # 활성 문서여야 반환됨
    idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=False; idm.UseTransform=True
    res=[{"vol_mm3":round(it.Volume*1e9,1),"comps":[c.Name2 for c in (pv(it,"Components") or [])]} for it in (pv(idm,"GetInterferences") or [])]
    idm.Done(); return sorted(res,key=lambda r:-r["vol_mm3"])
def find(c,pref,out):
    for ch in (pv(c,"GetChildren") or []):
        if ch.Name2.split("/")[-1].startswith(pref): out.append(ch)
        find(ch,pref,out)
    return out
def RT(c):
    a=list(c.Transform2.ArrayData); return [a[0:3],a[3:6],a[6:9]],a[9:12]
def world(R,t,p): return [sum(p[i]*R[i][j] for i in range(3))*1000+t[j]*1000 for j in range(3)]
def worldv(R,v): return [sum(v[i]*R[i][j] for i in range(3)) for j in range(3)]
def segs_of(c,rmin=15):
    md=c.GetModelDoc2; R,t=RT(c); out=[]
    for b in (pv(md,"GetBodies2",0,True) or []):
        for f in (pv(b,"GetFaces") or []):
            s=f.GetSurface
            if s.IsCylinder:
                cp=s.CylinderParams; r=cp[6]*1000
                if r<rmin: continue
                o=world(R,t,cp[0:3]); d=worldv(R,cp[3:6]); fb=list(f.GetBox)
                ws=[world(R,t,[fb[i],fb[j],fb[k]]) for i in (0,3) for j in (1,4) for k in (2,5)]
                ts=[sum((q[m]-o[m])*d[m] for m in range(3)) for q in ws]
                out.append({"r":round(r,2),"P0":[round(o[m]+d[m]*min(ts),1) for m in range(3)],"P1":[round(o[m]+d[m]*max(ts),1) for m in range(3)],"L":round(max(ts)-min(ts),1)})
    return out
TOP=os.path.join(Z,"S00000MU0.SLDASM"); S2P=os.path.join(Z,"S20000MU0.SLDASM"); S1P=os.path.join(Z,"S10000MU0.SLDASM")
top=app.GetOpenDocumentByName(TOP); a2=app.GetOpenDocumentByName(S2P); a1=app.GetOpenDocumentByName(S1P)
NOSE=[(850.0,-2340.0),(600.0,-2195.0),(350.0,-2050.0),(100.0,-1905.0),(-150.0,-1760.0),(-403.2,-1615.0),(-653.2,-1470.0)]   # (x_top, z_nose) 월드, 디딤판 −z 모서리
def rail_heights(label):
    """상부 난간대 직선부(r21.35, 최장) 축선 → 각 디딤판 앞코 위 수직 높이(축·파이프 상단)"""
    root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    res={}
    for c in find(root,"S20004",[]):
        s=max([x for x in segs_of(c) if abs(x["r"]-21.35)<0.1],key=lambda x:x["L"])
        P0,P1=s["P0"],s["P1"]; hs=[]
        for xn,zn in NOSE:
            xa=P0[0]+(P1[0]-P0[0])*(zn-P0[2])/(P1[2]-P0[2]); hs.append(round(xn-xa,1))
        res[c.Name2.split("/")[-1]]={"axis_P0":P0,"axis_P1":P1,"L":s["L"],"h_axis_over_nose":hs,"h_pipe_top":[round(h+21.35,1) for h in hs],"segs":[x for x in segs_of(c) if abs(x["r"]-21.35)<0.1]}
    log[label]=res; print(label,{k:(v["h_axis_over_nose"][0],v["h_axis_over_nose"][-1],v["h_pipe_top"][0]) for k,v in res.items()})
    return res
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
def add_comp(asm,path,R,t):
    """모든 구성에 같은 변환 적용(09-08 Transform2 구성별 실측 대응)"""
    c=asm.AddComponent5(path,0,"",False,"",t[0]/1000,t[1]/1000,t[2]/1000)
    if c is None: raise SystemExit("AddComponent5 failed "+path)
    nm=c.Name2; base=asm.GetTitle.replace(".SLDASM","")
    asm.ClearSelection2(True); asm.Extension.SelectByID2(nm+"@"+base,"COMPONENT",0,0,0,False,0,NOD,0); asm.UnfixComponent(); asm.ClearSelection2(True)
    cfgs=list(asm.GetConfigurationNames); cur=asm.ConfigurationManager.ActiveConfiguration.Name
    for cf in cfgs:
        asm.ShowConfiguration2(cf); cc={x.Name2:x for x in pv(asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
        set_T(cc[nm],R,t); asm.EditRebuild3
    asm.ShowConfiguration2(cur); asm.EditRebuild3
    return nm
def sel_plane(d,names):
    for nm in names:
        if d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0): return nm
    raise RuntimeError("no plane")
def last_sketch(d):
    f=pv(d,"FirstFeature"); last=None
    while f is not None:
        if pv(f,"GetTypeName2")=="ProfileFeature": last=f.Name
        f=pv(f,"GetNextFeature")
    return last
def props(d,p):
    cpm=d.Extension.CustomPropertyManager("")
    for k,v in p.items(): cpm.Add3(k,30,v,1)
def pbox(d): return [round(v*1000,1) for v in pv(d,"GetPartBox",True)]
def save_new(d,name):
    p=os.path.join(Z,name)
    if os.path.exists(p): raise SystemExit("EXISTS "+name)
    e=I4(); wn=I4(); ok=d.Extension.SaveAs(p,0,1,NOD,e,wn); print("saved",ok,name,e.value,wn.value); return p
def save(d,name):
    e=I4(); w_=I4(); ok=d.Save3(1,e,w_); print("SAVE",name,ok,e.value,w_.value); log.setdefault("saved",{})[name]=[ok,e.value,w_.value]

# ================= stage edit =================
if "edit" in stages:
    log["interf_S20000_before"]=interf(a2); print("S20000 interf before:",len(log["interf_S20000_before"]),log["interf_S20000_before"][:6])
    rail_heights("heights_before")
    root2=a2.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    cc={c.Name2.split("/")[-1]:c for c in (pv(root2,"GetChildren") or [])}
    d5=cc["S20005MU0-1"].GetModelDoc2; d4=cc["S20004MU0-7"].GetModelDoc2
    p=d5.Parameter("D1@보스-돌출1"); print("S20005 D1 before",p.SystemValue*1000); p.SystemValue=0.45; d5.EditRebuild3
    print("S20005 box after",pbox(d5),"ww",ww(d5))
    # 새들컷(r21.3 원통면) 위치: 끝단(±225)에 붙어 있는지
    for b in (pv(d5,"GetBodies2",0,True) or []):
        for f in (pv(b,"GetFaces") or []):
            s=f.GetSurface
            if s.IsCylinder and abs(s.CylinderParams[6]*1000-21.3)<0.2:
                print("  saddle cut face box",[round(v*1000,1) for v in f.GetBox])
    for nm,val in (("400@스케치3",0.45),("D4@스케치3",0.1933)):
        p=d4.Parameter(nm); print("S20004",nm,"before",round(p.SystemValue*1000,3)); p.SystemValue=val
    d4.EditRebuild3; print("S20004 box after",pbox(d4),"ww",ww(d4))
    a2.ForceRebuild3(False); print("S20000 ww",ww(a2)); top.ForceRebuild3(False)
    hb=rail_heights("heights_after")
    log["interf_S20000_after_edit"]=interf(a2); print("S20000 interf after edit:",len(log["interf_S20000_after_edit"]),log["interf_S20000_after_edit"][:8])
    # 지주 축 위치(월드) 재확인
    root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    log["posts_after"]={c.Name2.split("/")[-1]:[x for x in segs_of(c) if x["L"]>100] for c in find(root,"S20005",[])}
    for k,v in log["posts_after"].items(): print("  ",k,v)
    J("build_edit.json",log)

# ================= stage midrail_reset =================
if "midrail_reset" in stages:
    P13=os.path.join(Z,"S20013MU0.SLDPRT")
    base=a2.GetTitle.replace(".SLDASM","")
    for cf in list(a2.GetConfigurationNames):
        a2.ShowConfiguration2(cf)
        for c in [x for x in pv(a2.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren") if x.Name2.startswith("S20013")]:
            a2.ClearSelection2(True); a2.Extension.SelectByID2(c.Name2+"@"+base,"COMPONENT",0,0,0,False,0,NOD,0); print("delete comp",c.Name2,a2.Extension.DeleteSelection2(0))
    a2.ClearSelection2(True); a2.ForceRebuild3(False)
    print("S20013 left:",[x.Name2 for x in pv(a2.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren") if x.Name2.startswith("S20013")])
    dv=app.GetOpenDocumentByName(P13)
    if dv is not None: app.CloseDoc(dv.GetTitle)
    try: os.remove(P13); print("removed file",P13)
    except Exception as ex: print("remove failed",ex)

# ================= stage check =================
if "check" in stages:
    top.ForceRebuild3(False); root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    chk={}
    for c in find(root,"S1001",[])+find(root,"S20013",[]):
        n=c.Name2.split("/")[-1]
        if n.startswith(("S10012","S10013","S20013")): chk[n]={"world_box":box(c)}; print(n,"world box",box(c))
    rail_heights("heights_check")
    for c in find(root,"S20013",[]):
        segs=[x for x in segs_of(c,rmin=13) if abs(x["r"]-13.6)<0.1 and x["L"]>100]; s=max(segs,key=lambda x:x["L"]); P0,P1=s["P0"],s["P1"]
        hs=[round(xn-(P0[0]+(P1[0]-P0[0])*(zn-P0[2])/(P1[2]-P0[2])),1) for xn,zn in NOSE]
        chk[c.Name2.split("/")[-1]]["h_axis_over_nose"]=hs; chk[c.Name2.split("/")[-1]]["segs"]=segs; print(c.Name2.split("/")[-1],"mid h",hs[0],hs[-1],"segs",[(x["P0"],x["P1"],x["L"]) for x in segs])
    chk["interf_S20000"]=interf(a2); chk["interf_S10000"]=interf(a1)
    print("S20000 interf",len(chk["interf_S20000"]),[x for x in chk["interf_S20000"] if x["vol_mm3"]>0.5][:8]); print("S10000 interf",len(chk["interf_S10000"]),[x for x in chk["interf_S10000"] if x["vol_mm3"]>0.5][:8])
    print("ww S20000",ww(a2),"S10000",ww(a1)); log["check"]=chk; J("build_check.json",log)

# ================= stage midrail =================
if "midrail" in stages:
    # 월드 기하(변경 후): 기준선(지주 밑점 연결선) 위 ⊥225. 지주 밑점 B0=(833.8,-2328.6) [상부 난간대 자체 하단 지주], u=(-0.866,0.5), n=(-0.5,-0.866)
    u=(-math.sqrt(3)/2,0.5); n=(-0.5,-math.sqrt(3)/2); B0=(833.8,-2328.6); OFF=225.0
    M0=(B0[0]+OFF*n[0],B0[1]+OFF*n[1])                       # s=0 (하단 지주 축과 교차)
    s_top=(-1250.0-M0[1])/u[1]                                # 플랫폼 기둥 면 z=-1250 도달 s
    PITCH=650.0; RP=21.35; RO=13.6; RI=11.6
    GAP=0.5   # 지주 양쪽 용접 맞춤 틈
    slots=[(-30.0,RP+GAP)]+[(k*PITCH-RP-GAP,k*PITCH+RP+GAP) for k in (1,2,3)]
    L_EXT=s_top+RO*math.tan(math.radians(60))+10             # 마이터 이전 여유 길이
    print("midrail: M0",[round(v,1) for v in M0],"s_top",round(s_top,1),"L_ext",round(L_EXT,1),"slots",slots)
    d=app.NewDocument(tmpl,0,0,0)
    sel_plane(d,("우측면","Right Plane")); d.SketchManager.InsertSketch(True)
    d.SketchManager.CreateCircleByRadius(0,0,0,mm(RO)); d.SketchManager.CreateCircleByRadius(0,0,0,mm(RI))
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
    d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(L_EXT),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
    bx=pbox(d); sigma=1.0 if bx[3]>1 else -1.0; print("pipe box",bx,"sigma",sigma)
    # 컷 스케치(윗면 XZ): 슬롯 4개 + 마이터 사다리꼴. 스케치→모델 변환으로 좌표 결정
    sel_plane(d,("윗면","Top Plane")); d.SketchManager.InsertSketch(True); sk=d.SketchManager.ActiveSketch
    xf=list(pv(sk,"ModelToSketchTransform").ArrayData); Rm=[xf[0:3],xf[3:6],xf[6:9]]   # model->sketch 회전
    def s2(X,Zm):   # 모델 (X,0,Z) → 스케치 (sx,sy)
        v=[X,0.0,Zm]; r=[sum(v[i]*Rm[i][j] for i in range(3)) for j in range(3)]; return r[0],r[1]
    def quad(pts):
        pts=[s2(sigma*X,Zm) for X,Zm in pts]
        for i in range(len(pts)):
            a=pts[i]; b=pts[(i+1)%len(pts)]; d.SketchManager.CreateLine(mm(a[0]),mm(a[1]),0,mm(b[0]),mm(b[1]),0)
    d.SketchManager.AddToDB=True
    for x0,x1 in slots: quad([(x0,-30),(x1,-30),(x1,30),(x0,30)])
    # 마이터: 평면 0.5·s − 0.866·Z = s_top  (Z = 부품 Z, 로컬 −y 방향… 부호는 삽입 후 검증)
    # 월드 z = M0z + 0.5·s − σ·0.866·Z_p (부품 Z→월드 z성분 = −σ·0.866, 실측 σ=−1에서 +0.866). 기둥면 z=−1250 ↔ 0.5·s − σ·0.866·Z = 0.5·s_top
    zA,zB=30.0,-30.0; xA=(0.5*s_top+sigma*math.sqrt(3)/2*zA)/0.5; xB=(0.5*s_top+sigma*math.sqrt(3)/2*zB)/0.5
    quad([(xB,zB),(xA,zA),(L_EXT+50,zA),(L_EXT+50,zB)])
    d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
    d.FeatureManager.FeatureCut3(False,False,False,1,1,0.0,0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,0,0.0,False); d.EditRebuild3
    bodies=pv(d,"GetBodies2",0,True) or []; print("bodies",len(bodies),[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bodies],"ww",ww(d))
    # 마이터 면 법선(부품 좌표)
    for b in bodies:
        for f in (pv(b,"GetFaces") or []):
            s=f.GetSurface
            if s.IsPlane:
                nn=[round(v,3) for v in f.Normal]
                if abs(nn[1])<0.01 and abs(abs(nn[0])-0.5)<0.02: print("  miter face normal",nn,"box",[round(v*1000,1) for v in f.GetBox])
    vol=round(pv(d.Extension,"CreateMassProperty").Volume*1e9); print("volume",vol)
    props(d,{"RELATION NO.":"S20013MU0","PROJECT NO.":"S00000MU0","TITLE":"MID RAIL","SPEC":"Ø27.2x2.0T STS304 (KS D 3576 20A Sch10S) 4절 — 지주 사이 절단 후 용접, 상단 플랫폼 기둥면 마이터 60°","Material":"STS 304","QT'Y":"2","DATE":"2026-09-08","REMARK":"산업안전보건기준에 관한 규칙 제13조 2호 중간 난간대(상부 난간대 앞코 위 ~897의 중간 ~448). 상부 난간대 축 기준 ⊥225. 2026-09-08 신설"})
    P13=save_new(d,"S20013MU0.SLDPRT")
    # 삽입 (S20000MU0 로컬). 부품 X(σ) → 로컬 u_l=(0,0.866,0.5), 부품 Y → 로컬 (1,0,0), Z = X×Y
    X_=[0.0,sigma*math.sqrt(3)/2,sigma*0.5]; Y_=[1.0,0.0,0.0]
    Z_=[X_[1]*Y_[2]-X_[2]*Y_[1], X_[2]*Y_[0]-X_[0]*Y_[2], X_[0]*Y_[1]-X_[1]*Y_[0]]
    R13=[X_,Y_,Z_]; yl=1100.0-M0[0]; zl=M0[1]+2230.0
    names=[]
    for xl in (337.5,-337.5):
        names.append(add_comp(a2,P13,R13,(xl,yl,zl)))
    a2.ForceRebuild3(False); top.ForceRebuild3(False)
    root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    mid={}
    for c in find(root,"S20013",[]):
        segs=[x for x in segs_of(c,rmin=13) if abs(x["r"]-13.6)<0.1 and x["L"]>100]; mid[c.Name2.split("/")[-1]]={"box":box(c),"segs":segs}
        # 앞코 위 높이(축)
        s=max(segs,key=lambda x:x["L"]); P0,P1=s["P0"],s["P1"]
        mid[c.Name2.split("/")[-1]]["h_axis_over_nose"]=[round(xn-(P0[0]+(P1[0]-P0[0])*(zn-P0[2])/(P1[2]-P0[2])),1) for xn,zn in NOSE]
        print(c.Name2.split("/")[-1],"box",box(c),"h",mid[c.Name2.split("/")[-1]]["h_axis_over_nose"][:2],"segs",[(x["P0"],x["P1"],x["L"]) for x in segs])
    log["midrail"]={"M0":M0,"s_top":s_top,"slots":slots,"L_ext":L_EXT,"sigma":sigma,"R":R13,"t":[337.5,yl,zl],"volume":vol,"inst":mid}
    log["interf_S20000_after_midrail"]=interf(a2); print("S20000 interf after midrail:",len(log["interf_S20000_after_midrail"]),log["interf_S20000_after_midrail"][:10])
    print("S20000 ww",ww(a2)); J("build_midrail.json",log)

# ================= stage toe =================
if "toe" in stages:
    log["interf_S10000_before"]=interf(a1); print("S10000 interf before:",len(log["interf_S10000_before"]),log["interf_S10000_before"][:6])
    def plate(name,L,H,T,p):
        d=app.NewDocument(tmpl,0,0,0)
        sel_plane(d,("정면","Front Plane")); d.SketchManager.InsertSketch(True)
        d.SketchManager.CreateCornerRectangle(0,0,0,mm(L),mm(H),0)
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.Extension.SelectByID2(last_sketch(d),"SKETCH",0,0,0,False,0,NOD,0)
        d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(T),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False); d.EditRebuild3
        bx=pbox(d); print(name,"box",bx); props(d,p); return save_new(d,name+".SLDPRT"),bx
    P12,bx12=plate("S10012MU0",1076.0,100.0,3.2,{"RELATION NO.":"S10012MU0","PROJECT NO.":"S00000MU0","TITLE":"TOE BOARD-01","SPEC":"PL 100x3.2T L1076 STS304 — 데크 +y 변, 기둥 S10007 사이, 빔 S10002 상면 위·외측면 플러시","Material":"STS 304","QT'Y":"1","DATE":"2026-09-08","REMARK":"산안규칙 제13조 3호 발끝막이판 10 cm. 2026-09-08 신설"})
    P13b,bx13=plate("S10013MU0",1400.0,100.0,3.2,{"RELATION NO.":"S10013MU0","PROJECT NO.":"S00000MU0","TITLE":"TOE BOARD-02","SPEC":"PL 100x3.2T L1400 STS304 — 데크 z 끝(−50) 변, 기둥 S10007 사이, 바닥 립 앞면 플러시","Material":"STS 304","QT'Y":"1","DATE":"2026-09-08","REMARK":"산안규칙 제13조 3호 발끝막이판 10 cm. 2026-09-08 신설"})
    # 두께 방향(σz): 정면 스케치 돌출이 +Z인지 −Z인지 박스로 판단 → t 보정
    def place(path,bx,R,t_origin):
        # 부품 Z 범위 bx[2]..bx[5]; 원점 기준으로 두께가 −Z로 갔으면 R의 Z행 방향으로 평행이동 보정
        tz=bx[2] if bx[2]<-0.01 else 0.0
        t=[t_origin[i]-tz*R[2][i] for i in range(3)]
        return add_comp(a1,path,R,t)
    n12=place(P12,bx12,[[0,0,-1],[-1,0,0],[0,1,0]],(-1100.0,771.8,-125.0))
    n13=place(P13b,bx13,[[0,1,0],[-1,0,0],[0,0,1]],(-1100.0,-700.0,-53.2))
    a1.ForceRebuild3(False); top.ForceRebuild3(False)
    root=top.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    for c in find(root,"S1001",[]):
        if c.Name2.split("/")[-1].startswith(("S10012","S10013")): print(c.Name2.split("/")[-1],"world box",box(c))
    log["toe"]={"S10012":{"box_part":bx12,"expect_world":[-1200,771.8,-1201,-1100,775,-125]},"S10013":{"box_part":bx13,"expect_world":[-1200,-700,-53.2,-1100,700,-50]}}
    log["interf_S10000_after"]=interf(a1); print("S10000 interf after:",len(log["interf_S10000_after"]),log["interf_S10000_after"][:8]); print("S10000 ww",ww(a1))
    J("build_toe.json",log)

# ================= stage save =================
if "save" in stages:
    root2=a2.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    cc={c.Name2.split("/")[-1]:c for c in (pv(root2,"GetChildren") or [])}
    save(cc["S20005MU0-1"].GetModelDoc2,"S20005MU0"); save(cc["S20004MU0-7"].GetModelDoc2,"S20004MU0")
    save(a2,"S20000MU0"); save(a1,"S10000MU0")
    J("build_save.json",log)
stop.set()
