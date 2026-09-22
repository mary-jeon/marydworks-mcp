# 2026-09-14: KOSAPLUS KE008 STEP(제조사, SW2015 어셈블리) → 임포트 → 자식 파트 임시 저장 + Transform 기록 → 새 파트에 InsertPart3 합성(B4d)
#  파트 좌표 규약(B4c와 동일): 스템축 = 파트 Z, 취부(패드) 면 z=0, 몸체 +z, 스템축 x=y=0
import os, sys, json, math, re, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np
from scipy.spatial.transform import Rotation
from swconn import *
from swpv import pv
from swdialog import template_clicker
DESK=r"<PROJECT_DIR>"
STEP=os.path.join(DESK,"_원문","32A","kosa","kosaplus_KE005_F357C14.step")
TMP=os.path.join(DESK,"_3D다운로드","KE005_children"); os.makedirs(TMP,exist_ok=True)
OUT=os.path.join(Z,"B4e_actuator_KOSAPLUS_KE005-F357C14-DC.SLDPRT")
REC=os.path.join(DESK,"_검증","ke005_children_0915.json")
mm=lambda v:v/1000.0
stop=watchdog(); app=connect()
stage=sys.argv[1] if len(sys.argv)>1 else "children"
if stage=="children":
    already=[x for x in (pv(app,"GetDocuments") or []) if x.GetTitle.lower().startswith("kosaplus_ke005") and x.GetType==2]
    if already: d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); print("reuse open import asm")
    else:
        evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); print("LoadFile4 err",e.value)
    d=app.ActiveDoc; title=d.GetTitle; print("imported",title,d.GetType)
    cm=d.ConfigurationManager
    def walk(c,depth,acc):
        for k in (pv(c,"GetChildren") or []):
            kids=pv(k,"GetChildren") or []
            if kids and depth<8: walk(k,depth+1,acc)
            else: acc.append(k)
    leaves=[]; walk(cm.ActiveConfiguration.GetRootComponent3(True),0,leaves); print("leaf components",len(leaves))
    rec=[]
    for k,c in enumerate(leaves):
        if c.GetSuppression2!=2: continue
        md=c.GetModelDoc2; base=os.path.basename(c.GetPathName)
        safe=f"c{k:02d}_"+"".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in base)
        p=os.path.join(TMP,safe)
        if not os.path.exists(p):
            app.ActivateDoc3(md.GetTitle,False,0,I4()); e=I4(); w=I4(); ok=md.Extension.SaveAs(p,0,1,NOD,e,w)
        else: ok="exists"
        xf=xform(c); bb=box(c); rec.append({"name":c.Name2,"file":p,"saveas":ok,"R":xf["R"],"t_mm":xf["t_mm"],"box":bb})
        print(f"  {k:2d} {c.Name2[-44:]:44s} save {ok} t {xf['t_mm']} box {bb}")
    app.ActivateDoc3(title,False,0,I4()); d=app.ActiveDoc
    root_box=box(cm.ActiveConfiguration.GetRootComponent3(True)); print("asm box",root_box)
    json.dump({"rec":rec,"title":title},open(REC,"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
    app.CloseDoc(title)
    for x in list(pv(app,"GetDocuments") or []):
        pn=x.GetPathName or ""
        if pn.startswith(TMP) or x.GetTitle.lower().startswith("kosaplus_ke005") or (not pn and x.GetType==1 and x.GetTitle.startswith("파트")): 
            try: app.CloseDoc(x.GetTitle)
            except Exception: pass
    print("children stage done", len(rec))
elif stage=="compose":
    rec=json.load(open(REC,encoding="utf-8"))["rec"]
    TG=np.array([0.0,0.0,0.0])   # KE005: 합성 후 align 스테이지에서 패드·스템축 실측해 이동
    dd=app.GetOpenDocumentByName(OUT)
    if dd is not None: app.CloseDoc(dd.GetTitle)
    if os.path.exists(OUT): os.remove(OUT); print("removed old B4d")
    tmpl=app.GetUserPreferenceStringValue(8); d=app.NewDocument(tmpl,0,0,0); print("new part",d.GetTitle)
    def bodies(): return list(pv(d,"GetBodies2",0,False) or [])
    def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
    def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
    def sel_body(b):
        d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
    def box_close(a,b,tol=0.3): return np.all(np.abs(np.array(a)-np.array(b))<tol)
    final=[]
    def target():
        c=[b for b in bodies() if not any(box_close(bbox(b),fb,0.05) for fb in final)]
        assert len(c)==1, ("target ambiguous",len(c)); return c[0]
    SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}
    for k,r in enumerate(rec):
        Rc=np.array(r["R"]); tc=np.array(r["t_mm"]); exp_box=np.array(r["box"])
        before={pv(b,"Name") for b in bodies()}
        f=d.InsertPart3(r["file"],1|512|262144,""); d.EditRebuild3
        new=[b for b in bodies() if pv(b,"Name") not in before]
        if f is None or len(new)!=1: print("  skip",k,r["name"][-40:],"f",f is not None,"new",len(new)); 
        if not new: continue
        if len(new)>1:
            # 다중바디 파트: 전부 동일 변환 적용
            pass
        for b in new:
            c_loc=centroid(b); c_rot_exp=c_loc@Rc
            if not np.allclose(Rc,np.eye(3),atol=1e-6):
                ang=Rotation.from_matrix(Rc.T).as_euler("xyz")
                for axis,val in zip("xyz",ang):
                    if abs(val)<1e-9: continue
                    s=SLOT[axis]; sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3; assert mv; b=target()
                c_got=centroid(b); assert np.all(np.abs(c_got-c_rot_exp)<0.1), ("rot mismatch",r["name"],c_got,c_rot_exp)
            t=tc+TG; sel_body(b); mv=d.FeatureManager.InsertMoveCopyBody2(mm(t[0]),mm(t[1]),mm(t[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv
            b=target(); got=bbox(b); final.append(got)
        print(f"  [{k}] {r['name'][-40:]:40s} bodies {len(new)} box {got.round(1)} exp {exp_box.round(1)}")
    bs=bodies(); pb=np.array([v*1000 for v in pv(d,"GetPartBox",True)]); vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs)
    print("bodies",len(bs),"part box (asm coords)",pb.round(2),"vol",round(vol))
    e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w); print("saved raw B4d",ok,e.value)
    json.dump({"part_box":pb.tolist(),"vol":vol,"bodies":len(bs)},open(os.path.join(DESK,"_검증","ke005_b4e_raw_0915.json"),"w",encoding="utf-8"),indent=1)
elif stage=="align":
    d=app.GetOpenDocumentByName(OUT) or open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc
    bs=list(pv(d,"GetBodies2",0,False) or []); cyl=[]; pl=[]
    for b in bs:
        for fc in b.GetFaces():
            s_=fc.GetSurface; fb=[round(v*1000,2) for v in fc.GetBox]; A=fc.GetArea*1e6
            if s_.IsCylinder:
                p=s_.CylinderParams; cyl.append(((round(p[3],3),round(p[4],3),round(p[5],3)),round(p[6]*1000,2),round(A),(round(p[0]*1000,2),round(p[1]*1000,2),round(p[2]*1000,2)),fb))
            elif s_.IsPlane: pl.append((tuple(round(v,3) for v in pv(fc,"Normal")),round(A),fb))
    # 탭홀(r 2.1~3.4) 축 방향 집계 → 스템축
    small=[c for c in cyl if 2.0<=c[1]<=3.5]
    axc=collections.Counter(tuple(abs(v) for v in c[0]) for c in small); ax=axc.most_common(1)[0][0]; print("tap-hole axis",ax,axc.most_common(3))
    k=[i for i,v in enumerate(ax) if v>0.9][0]   # 스템축 인덱스
    holes=[c for c in small if abs(abs(c[0][k])-1)<1e-3]
    # 패드면: 스템축에 수직인 평면 중, 탭홀 시작 좌표(축값 극단)에 가까운 큰 평면
    hz=[c[4][k] if True else 0 for c in holes]; hz2=[c[4][k+3] for c in holes]
    lo=min(hz); hi=max(hz2); print("holes axis range",lo,hi)
    pads=[p for p in pl if abs(abs(p[0][k])-1)<1e-3 and p[1]>500]; pads.sort(key=lambda p:-p[1])
    padA=[p for p in pads if abs(p[2][k]-lo)<1.0 or abs(p[2][k]-hi)<1.0]; print("pad candidates",[(p[0],p[1],p[2][k]) for p in padA[:4]])
    assert padA, "pad face"
    pad=padA[0]; pz=pad[2][k]; pn=pad[0][k]
    # 스템축 (다른 두 좌표) = 탭홀 원점 평균
    oth=[i for i in range(3) if i!=k]; c0=np.mean([c[3][oth[0]] for c in holes]); c1=np.mean([c[3][oth[1]] for c in holes]); print("stem axis coords",oth,c0,c1,"pad at",k,pz,"normal",pn)
    # 회전: 스템축 k → z, 패드 법선이 −z(몸체 +z)가 되도록
    def sel_all():
        d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
        for b in list(pv(d,"GetBodies2",0,False) or []): b.Select2(True,sd)
    mvs=[]
    if k==0: sel_all(); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,-math.pi/2,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_회전"; mvs.append(mv)
    elif k==1: sel_all(); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,0,math.pi/2, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_회전"; mvs.append(mv)
    pb=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("after rot box",pb)
    # 재실측: 탭홀 축이 z인지, 패드 z
    bs=list(pv(d,"GetBodies2",0,False) or []); small=[]
    for b in bs:
        for fc in b.GetFaces():
            s_=fc.GetSurface
            if s_.IsCylinder:
                p=s_.CylinderParams
                if 2.0<=p[6]*1000<=3.5 and abs(abs(p[5])-1)<1e-3: fb=[round(v*1000,2) for v in fc.GetBox]; small.append(((round(p[0]*1000,2),round(p[1]*1000,2)),fb[2],fb[5]))
    assert small, "tap holes after rot"
    cx=np.mean([s_[0][0] for s_ in small]); cy=np.mean([s_[0][1] for s_ in small]); zlo=min(s_[1] for s_ in small); zhi=max(s_[2] for s_ in small)
    # 패드면 = 탭홀 시작면 = 파트 박스의 z 끝 중 탭홀 범위에 가까운 쪽
    padz=zlo if abs(zlo-pb[2])<abs(zhi-pb[5]) else zhi
    flip=(padz==zhi)   # 패드가 +z 끝이면 뒤집어 −z 끝(0)으로
    if flip: sel_all(); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,math.pi,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_뒤집기"; pb=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; cx=-cx; padz=pb[2]
    sel_all(); mv=d.FeatureManager.InsertMoveCopyBody2(mm(-cx),mm(-cy),mm(-padz),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_이동"
    pb=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; print("final box",pb)
    bs=list(pv(d,"GetBodies2",0,False) or []); holes=[]
    for b in bs:
        for fc in b.GetFaces():
            s_=fc.GetSurface
            if s_.IsCylinder:
                p=s_.CylinderParams; rr=p[6]*1000; fb=[v*1000 for v in fc.GetBox]
                if 2.0<=rr<=3.5 and abs(abs(p[5])-1)<1e-3 and fb[2]<3: holes.append((round(rr,2),round(p[0]*1000,1),round(p[1]*1000,1),round(math.hypot(p[0]*1000,p[1]*1000),1)))
    print("mount-face holes (r,x,y,PCD/2):",sorted(set(holes)))
    e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value)
stop.set(); print("stage",stage,"done")
