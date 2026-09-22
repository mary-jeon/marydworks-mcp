# 2026-09-15: Tameson BL2SA3-114 STEP(형상 대용) → G3e 파트: 유로축 Z·스템 +Y 정렬, 면간 110 → 태성 32A 100으로 양단 5 트림, 포트 나사부 표현 컷 Ø42.8×15, 속성
#  + G13g 소켓 리브 z 범위 실측
import os, sys, json, math, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
from swdialog import template_clicker
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
STEP=os.path.join(DESK,r"_원문\32A\valve\bl2sa3-114.step")
OUT=os.path.join(Z,"G3e_valve_3PC_32A_TAESUNG_S3_alt_Tameson_BL2SA3-114.SLDPRT")
mm=lambda v:v/1000.0; DATE="2026-09-15"; L_TS=100.0; ENG=15.0; R_BORE=21.4
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def body(d): return bodies(d)[0]
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def vol(d): return sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bodies(d))
def sel_body(d,b):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
def probe(d):
    import time
    for attempt in range(3):
        try:
            cyl=[]; pl=[]
            for fc in body(d).GetFaces():
                s=fc.GetSurface; fb=[round(v*1000,2) for v in fc.GetBox]; A=fc.GetArea*1e6
                if s.IsCylinder:
                    p=s.CylinderParams; cyl.append(((p[3],p[4],p[5]),p[6]*1000,A,(p[0]*1000,p[1]*1000,p[2]*1000),fb))
                elif s.IsPlane: pl.append((tuple(pv(fc,"Normal")),A,fb))
            return cyl,pl
        except pythoncom.com_error as ex:
            print("  probe com_error, retry",attempt,ex); time.sleep(2); d.ForceRebuild3(False)
    raise SystemExit("probe failed")
def flow_axis(cyl):
    acc=collections.defaultdict(float)
    for ax,r,A,o,fb in cyl: acc[tuple(round(abs(v),2) for v in ax)]+=A
    return max(acc.items(),key=lambda kv:kv[1])[0]
def feat_names(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append(f.Name); f=pv(f,"GetNextFeature")
    return out
def delete(d,n,kind="BODYFEATURE"):
    d.ClearSelection2(True); d.Extension.SelectByID2(n,kind,0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
def sketch_circle(d,r):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    d.SketchManager.InsertSketch(True); d.SketchManager.AddToDB=True; d.SketchManager.CreateCircleByRadius(0,0,0,mm(r)); d.SketchManager.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    last=[n for n in feat_names(d) if n.startswith("스케치")][-1]; assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0); return last
def offset_cut(d,r,start,depth,name,check):
    # 정면 스케치 원 r, 시작 오프셋 start, 깊이 depth; 방향·flip 조합 시도, check(d)로 검증
    for dirflag in (True,False):
        for flip in (False,True):
            sk=sketch_circle(d,r)
            f=d.FeatureManager.FeatureCut4(True,False,dirflag,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,False,True,True,False,False,False,3,mm(start),flip,False); d.EditRebuild3
            if f is None: delete(d,sk,"SKETCH"); continue
            f.Name=name
            if check(d): return True
            delete(d,name)
    return False
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
# ---------- 소켓 리브 실측
Pg=os.path.join(Z,"G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP.SLDPRT"); dg=act(Pg)
ribs=[]
for fc in body(dg).GetFaces():
    fb=[round(v*1000,2) for v in fc.GetBox]
    if max(abs(fb[0]),abs(fb[3]),abs(fb[1]),abs(fb[4]))>24.6: ribs.append((fb[2],fb[5],round(max(abs(fb[0]),abs(fb[3]),abs(fb[1]),abs(fb[4])),2)))
ribs=sorted(set(ribs)); print("G13g faces beyond r24.5 (z0,z1,rmax):",ribs[:20])
# ---------- 밸브
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle)
if os.path.exists(OUT): os.remove(OUT)
evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); d=app.ActiveDoc; print("import",d.GetTitle,d.GetType,"err",e.value)
if d.GetType==2:
    kids=list(pv(d.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren"))
    def ext(c):
        b=box(c); return (b[3]-b[0])*(b[4]-b[1])*(b[5]-b[2]) if b else 0
    big=max(kids,key=ext); pd=big.GetModelDoc2; app.ActivateDoc3(pd.GetTitle,False,0,I4()); pd=app.ActiveDoc; t=d.GetTitle
    e=I4(); w=I4(); ok=pd.Extension.SaveAs(OUT,0,1,NOD,e,w); app.CloseDoc(t)
    for x in list(pv(app,"GetDocuments") or []):
        try:
            if x.GetTitle.lower().startswith("bl2sa3-114"): app.CloseDoc(x.GetTitle)
        except Exception: pass
else:
    e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w)
d=act(OUT); print("box0",partbox(d),"vol",round(vol(d)))
cyl,pl=probe(d); ax=flow_axis(cyl); print("flow axis",ax)
# 스템축: +Y 평면(패드) 면적 큰 것으로 판단 → 먼저 유로축을 Z로
def rot(axis_vec,sgn):
    b=body(d); sel_body(d,b)
    if axis_vec=="y": mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,sgn,0, False,1)
    elif axis_vec=="x": mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,0,sgn, False,1)
    else: mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, sgn,0,0, False,1)
    d.EditRebuild3; assert mv; return mv
tries=0
while flow_axis(probe(d)[0])!=(0.0,0.0,1.0) and tries<4:
    ax=flow_axis(probe(d)[0]); tries+=1
    # 유로축 ax → Z: ax가 x축 성분 크면 y둘레, y 성분 크면 x둘레 회전(각도 atan2)
    if abs(ax[0])>=abs(ax[1]):
        a=math.atan2(ax[0],ax[2])
        for sgn in (1,-1):
            mv=rot("y",sgn*a); mv.Name=f"정렬_회전{tries}"
            if flow_axis(probe(d)[0])==(0.0,0.0,1.0): break
            delete(d,mv.Name)
    else:
        a=math.atan2(ax[1],ax[2])
        for sgn in (1,-1):
            mv=rot("x",sgn*a); mv.Name=f"정렬_회전{tries}"
            if flow_axis(probe(d)[0])==(0.0,0.0,1.0): break
            delete(d,mv.Name)
cyl,pl=probe(d); assert flow_axis(cyl)==(0.0,0.0,1.0), flow_axis(cyl)
# 스템축 = 유로축에 수직인 큰 평면(패드)의 법선: 면적 최대 평면 중 법선 z 성분 0
pads=sorted([p for p in pl if abs(p[0][2])<0.05],key=lambda p:-p[1])[:3]; print("pad candidates",[(tuple(round(v,2) for v in p[0]),round(p[1]),p[2]) for p in pads])
pn=pads[0][0]
if abs(pn[1])<0.9:   # 패드 법선을 +Y 로 (z 둘레 회전)
    a=math.atan2(pn[0],pn[1])
    for sgn in (1,-1):
        mv=rot("z",sgn*a); mv.Name="정렬_스템"
        cyl,pl=probe(d); pads=sorted([p for p in pl if abs(p[0][2])<0.05],key=lambda p:-p[1])[:1]
        if abs(pads[0][0][1])>0.99: break
        delete(d,"정렬_스템")
cyl,pl=probe(d); pads=sorted([p for p in pl if abs(p[0][2])<0.05],key=lambda p:-p[1])[:1]; pn=pads[0][0]
if pn[1]<0:   # 패드가 −Y면 z둘레 180°
    mv=rot("z",math.pi); mv.Name="정렬_스템2"
cyl,pl=probe(d)
zc=[c for c in cyl if abs(abs(c[0][2])-1)<1e-3]; big=sorted(zc,key=lambda c:-c[2])[:6]
fx=float(np.median([c[3][0] for c in big])); fy=float(np.median([c[3][1] for c in big]))
bx=partbox(d); zmid=(bx[2]+bx[5])/2
sel_body(d,body(d)); mv=d.FeatureManager.InsertMoveCopyBody2(mm(-fx),mm(-fy),mm(-zmid),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_이동"
bx=partbox(d); print("aligned box",bx)
cyl,pl=probe(d); pad=sorted([p for p in pl if abs(p[0][1]-1)<1e-3],key=lambda p:-p[1])[:2]; print("+Y planes",[(round(p[1]),[round(v,1) for v in p[2]]) for p in pad])
L0=bx[5]-bx[2]; print("face-to-face",round(L0,2))
# 트림: 양단 (L0−100)/2 → 양단 5. 정면(z0)에서 오프셋 시작 50, 깊이 (L0/2−50) 컷 (큰 원 r 60로 몸통 전부 제거)
trim=L0/2-L_TS/2
def chk_top(d): b=partbox(d); return abs(b[5]-L_TS/2)<0.1 and abs(b[2]+L0/2)<0.3
def chk_bot(d): b=partbox(d); return abs(b[2]+L_TS/2)<0.1
if trim>0.2:
    assert offset_cut(d,60.0,L_TS/2,trim+1.0,"트림_상",chk_top), "trim top"
    assert offset_cut(d,60.0,L_TS/2,trim+1.0,"트림_하",chk_bot), "trim bot"
print("trimmed box",partbox(d))
# 포트 나사부 표현 컷 Ø42.8×15 (z 35~50, −50~−35)
def r_faces():
    return [ (c[4][2],c[4][5]) for c in probe(d)[0] if abs(c[1]-R_BORE)<0.05 ]
def chk_pt(d): return any(abs(a-(L_TS/2-ENG))<0.3 and abs(b-L_TS/2)<0.3 for a,b in r_faces())
def chk_pb(d): return any(abs(a+L_TS/2)<0.3 and abs(b+(L_TS/2-ENG))<0.3 for a,b in r_faces())
assert offset_cut(d,R_BORE,L_TS/2-ENG,ENG,"포트컷_상",chk_pt), "port top"
assert offset_cut(d,R_BORE,L_TS/2-ENG,ENG,"포트컷_하",chk_pb), "port bot"
orph=orphan_sketches(d)
for n in orph:
    d.ClearSelection2(True); d.Extension.SelectByID2(n,"SKETCH",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(0)
d.EditRebuild3; print("orphans removed",orph,"remaining",orphan_sketches(d),"ww",ww(d),"final box",partbox(d),"vol",round(vol(d)))
cp=d.Extension.CustomPropertyManager("")
for k,v in {"TITLE":"BALL VALVE 3PC 32A (태성자동밸브 S3, 형상 대용: Tameson BL2SA3-114 STEP 면간 100 트림)",
 "SPEC":"태성자동밸브 3PC 나사식 볼밸브 32A(1-1/4) 자동장착형(S3): 면간 L 100·보어 Ø32·Body/Ball SUS304(SUS316)·Seat PTFE·10 kgf/cm²·−10~90 ℃(카탈로그 2013-36 p.12·도면 A110117-01-04·2012판 p.17 일치). 단품 형번·ISO 패드·스템 각형·나사(PT/PF)·토크 원문 미기재 → 태성 문의. 형상 대용 Tameson BL2SA3-114(G1-1/4, DN32, L110, F04/F05/F07-VK11, 패드 63, 2.1 kg)를 양단 5 트림해 면간 100으로 맞춤. 포트컷 = 나사부 표현(Ø42.8×15).",
 "Material":"STS316","QT'Y":"1","DATE":DATE,
 "REMARK":"로봇과 동일 제조사(태성) 지정(사용자 09-14). 대용 STEP: tameson.com bl2sa3-114.zip. 액추에이터 코사 KE005(□14 표준/□11 옵션) — 태성 스템 확정 전 옵션 미정."}.items():
    if cp.Get(k): cp.Set2(k,v)
    else: cp.Add3(k,30,v,1)
try: d.SetMaterialPropertyName2("","이텍","STS 316")
except Exception as ex: print("mat exc",ex)
e=I4(); w=I4(); print("save",d.Save3(1,e,w),e.value)
json.dump({"ribs":ribs,"box":partbox(d),"L":L_TS},open(os.path.join(VER,"valve114_0915.json"),"w"),indent=1,default=str)
stop.set(); print("done")
