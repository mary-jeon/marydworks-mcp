# 2026-09-09: 하강 호스를 단일 원호(양끝 기울기 큼) 대신 상승 호스와 같은 경로 형식(수직 스텁 20 + r47 굽힘 + 큰 R 원호 + r47 굽힘 + 수직 스텁 20)으로 다시 만든다.
# D=332(니플 끝 -148 → 이동 니플 상단 -480), X=100, L=365.9. 파일 J19c_hose_3-4in_dn_s_L366. 원호 파트(J19c_..._dn_arc_L366)는 어셈블리에서 빼고 파일은 백업 폴더로.
import os, sys, json, math, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
tmpl=app.GetUserPreferenceStringValue(8)
mm=lambda v:v/1000.0
OX=100.0; ZP_DN=-510.0; NIP_FIX_END=-148.0; L_HOSE=365.9; R_HOSE=47.0; D_DN=(ZP_DN+30)-NIP_FIX_END   # -332
D=-D_DN
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
        segs.append(("arc",(cx,cy),(x,y),(x1,y1),ang)); x,y,h=x1,y1,h2
    st(s); arc(r,a1); st(t); arc(R,-(a1+a2)); st(t); arc(r,a2); st(s)
    return segs,(x,y)
def path_len(segs):
    return sum((math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1]) if sg[0]=="line" else abs(sg[4])*math.hypot(sg[2][0]-sg[1][0],sg[2][1]-sg[1][1])) for sg in segs)
def solve_hose(r):
    import random
    X,L=OX,L_HOSE
    def sc(p):
        a1,a2,R,t=p
        if R<r or t<0 or a1<0 or a1+a2<=0.02: return 1e6
        segs,(ex,ey)=hose_segments(r,a1,a2,R,t); return math.hypot(ex-X,ey+D)+abs(path_len(segs)-L)
    rnd=random.Random(3); best=(1e9,None)
    for _ in range(400):
        p=[rnd.uniform(0.1,2.0),rnd.uniform(-1.0,2.0),r*rnd.uniform(1.0,8.0),rnd.uniform(0,D)]
        v=sc(p); step=[0.2,0.2,r*0.5,max(10.0,D/8)]
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
v,(a1,a2,R,t)=solve_hose(R_HOSE); segs,end=hose_segments(R_HOSE,a1,a2,R,t)
xs=[]; ys=[]
for sg in segs:
    for p in (sg[1],sg[2]) if sg[0]=="line" else (sg[2],sg[3]): xs.append(p[0]); ys.append(p[1])
    if sg[0]=="arc":
        cx,cy=sg[1]; rr=math.hypot(sg[2][0]-cx,sg[2][1]-cy); xs+= [cx-rr,cx+rr]  # 보수적 extents
print(f"hose dn S-path: resid {v:.3f} a1 {math.degrees(a1):.1f} a2 {math.degrees(a2):.1f} R {R:.1f} t {t:.1f} end {end} L {path_len(segs):.1f} (target {L_HOSE}) D {D}")
print(f"  path x extents (conservative) {min(xs):.1f}~{max(xs):.1f}")
if v>0.5: raise SystemExit("solver residual too large")
json.dump({"r":R_HOSE,"a1":a1,"a2":a2,"R":R,"t":t,"resid":v,"L":L_HOSE,"D":D,"OX":OX,"end":end,"segments":segs},open(os.path.join(VER,"J5c_dn120_hose_path.json"),"w"),indent=1)
name_dn="J19c_hose_3-4in_dn_s_L366.SLDPRT"; PD=os.path.join(Z,name_dn)
if os.path.exists(PD): raise SystemExit("exists: "+PD)
done=False
for direction in (1,-1):
    dh=app.NewDocument(tmpl,0,0,0)
    try:
        dh.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or dh.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
        dh.SketchManager.InsertSketch(True); sm=dh.SketchManager; sm.AddToDB=True
        for sg in segs:
            if sg[0]=="line": sm.CreateLine(mm(sg[1][0]),mm(sg[1][1]),0,mm(sg[2][0]),mm(sg[2][1]),0)
            else:
                cc_,p0,p1,ang=sg[1],sg[2],sg[3],sg[4]
                sm.CreateArc(mm(cc_[0]),mm(cc_[1]),0,mm(p0[0]),mm(p0[1]),0,mm(p1[0]),mm(p1[1]),0,direction*(1 if ang>0 else -1))
        sm.AddToDB=False; dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
        skf=dh.FeatureByName("스케치1") or dh.FeatureByName("Sketch1"); sk=skf.GetSpecificFeature2
        segs_sw=pv(sk,"GetSketchSegments"); Ls=sum((s_.GetLength() if callable(s_.GetLength) else s_.GetLength) for s_ in segs_sw)*1000
        print(f"  direction={direction}: sketch length {Ls:.1f}")
        if abs(Ls-L_HOSE)>2.0: app.CloseDoc(dh.GetTitle); continue
        dh.Extension.SelectByID2("윗면","PLANE",0,0,0,False,0,NOD,0) or dh.Extension.SelectByID2("Top Plane","PLANE",0,0,0,False,0,NOD,0)
        dh.SketchManager.InsertSketch(True); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(14.1)); dh.SketchManager.CreateCircleByRadius(0,0,0,mm(9.5)); dh.SketchManager.InsertSketch(True); dh.ClearSelection2(True)
        dh.Extension.SelectByID2("스케치2","SKETCH",0,0,0,False,1,NOD,0) or dh.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,False,1,NOD,0)
        dh.Extension.SelectByID2("스케치1","SKETCH",0,0,0,True,4,NOD,0) or dh.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,True,4,NOD,0)
        f=None
        for attempt in ("swept3","swept4"):
            try:
                if attempt=="swept3": f=dh.FeatureManager.InsertProtrusionSwept3(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False)
                else: f=dh.FeatureManager.InsertProtrusionSwept4(False,False,0,False,False,0,0,False,0.0,0.0,0,0,True,True,True,0.0,False,False,0.0,0)
                if f: break
            except Exception as ex: print("  ",attempt,"exception",ex)
        if not f: raise RuntimeError("sweep failed")
        dh.EditRebuild3; bx=[round(v_*1000,1) for v_ in dh.GetPartBox(True)]; print("  hose dn box",bx)
        cp=dh.Extension.CustomPropertyManager("")
        for k_,v_ in {"TITLE":"HOSE 3/4in (하강 상태 굽힘)","SPEC":f"do88 F19 Silicone Hose Blue Flexible 3/4\" ID19 OD28.2, 자유길이 {L_HOSE} + 니플 삽입 2x20 = 절단 약 {round(L_HOSE)+40}, 최소 굽힘반경 47. 하강(스트로크 120, 낙차 {D:.0f}·OX {OX:.0f}) 경로: 수직 20 + r47 {math.degrees(a1):.0f}° + R{R:.0f} + r47 {math.degrees(a2):.0f}° + 수직 20","QT'Y":"1","Material":"SILICONE","DATE":"2026-09-09","REMARK":"상승 J19c_up_r47과 같은 호스 1본. 2026-09-09 하강 스트로크 140→120으로 직선 L366 파트 대체(HANDOFF §1-16)"}.items(): cp.Add3(k_,30,v_,1)
        dh.SetMaterialPropertyName2("","SOLIDWORKS Materials","Natural Rubber"); dh.EditRebuild3
        e=I4(); wn=I4(); ok=dh.Extension.SaveAs(PD,0,1,NOD,e,wn); print("  saved",ok,name_dn,e.value,wn.value); done=True; break
    except Exception as ex:
        print("FAIL dn hose",ex); app.CloseDoc(dh.GetTitle); raise
if not done: raise SystemExit("dn hose sketch length mismatch")
# ---- 어셈블리 교체
asm=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager; CFGS=list(pv(asm,"GetConfigurationNames")); title=asm.GetTitle.replace(".SLDASM","")
def comps(): return {c.Name2:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
def set_T(c,R,t):
    arr=list(R[0])+list(R[1])+list(R[2])+[t[0]/1000,t[1]/1000,t[2]/1000,1.0,0,0,0]
    xf=c.Transform2; xf.ArrayData=VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8,arr); c.Transform2=xf
asm.ShowConfiguration2("하강"); asm.EditRebuild3; cc=comps()
R_up=xform(cc["J19c_hose_3-4in_up_r47-1"])["R"]
old=[n for n in cc if n.startswith("J19c_hose_3-4in_dn_arc")]
for n in old:
    asm.ClearSelection2(True); asm.Extension.SelectByID2(n+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0); print("delete",n,asm.Extension.DeleteSelection2(1))
asm.EditRebuild3
newc=asm.AddComponent5(PD,0,"",False,"",0.0,0.0,0.0); newname=newc.Name2; print("added",newname)
for cfg in CFGS:
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; cc=comps(); c=cc[newname]; set_T(c,R_up,(0,0,NIP_FIX_END))
    asm.ClearSelection2(True); asm.Extension.SelectByID2(newname+"@"+title,"COMPONENT",0,0,0,False,0,NOD,0)
    if cfg=="하강": asm.EditUnsuppress2
    else: asm.EditSuppress2
    asm.ClearSelection2(True); asm.ForceRebuild3(False); cc=comps()
    print(f"[{cfg}] {newname} supp={cc[newname].GetSuppression2} t={xform(cc[newname])['t_mm']}")
asm.ShowConfiguration2("하강"); asm.ForceRebuild3(False); cc=comps()
rep={n:box(cc[n]) for n in cc if cc[n].GetSuppression2==2 and n.startswith(("J5d","G13","H16","J17","B10","J9b","J11","J19c","B9c"))}
for n,b in rep.items(): print("  하강",n,b)
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump({"stroke_dn":120,"zp_dn":ZP_DN,"boxes_dn":rep},open(os.path.join(VER,"J5c_dn120_build.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
# 원호 파트 파일 닫고 백업으로 이동
arc_path=os.path.join(Z,"J19c_hose_3-4in_dn_arc_L366.SLDPRT")
da=app.GetOpenDocumentByName(arc_path)
if da is not None: app.CloseDoc(da.GetTitle)
bk=r"<MCP_DIR>\_backup\20260909-unused"; os.makedirs(bk,exist_ok=True)
if os.path.exists(arc_path):
    try: shutil.move(arc_path,os.path.join(bk,os.path.basename(arc_path))); print("moved arc part to",bk)
    except Exception as ex: print("move failed (leave on Z:)",ex)
print("done; NOT saved: B9c, asm")
stop.set()
