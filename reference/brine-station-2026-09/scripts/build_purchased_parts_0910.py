# 2026-09-10: 구매품 3D 4종을 프로젝트 규약으로 정렬해 Station 폴더에 저장 (CLAUDE.md §4)
#  J2c  = MISUMI PSSFAQ16-590-B10 STEP(파트, 원통 Ø16×600, 나사 미표현)  → 축 −Z, 상단 z 0(J1c M16 탭 쪽)
#  G11f = MISUMI SHCCG8-22.8 STEP(어셈블리: 핀+E링)                   → 핀 축 +Y, 머리/핀 경계 y 0, 머리 −y
#  J11e = MISUMI SHCCG8-18 STEP(어셈블리: 핀+E링)                     → 동일
#  G3c  = Tameson BL2SA3-034 (09-09 백업 SLDPRT, 형상 대용)            → 유로 축 −Z, 상단 끝면 z 0, ISO 패드 −y(패드면 y −43.5)
#  방법: STEP 어셈블리는 자식 SaveAs → 새 파트 InsertPart3 + MoveCopyBody(원 변환), 이후 전체 바디 정렬 회전(축별 피처)+이동. 무게중심으로 검증.
#  이미 만든 출력 파일은 건너뜀(재실행 안전).
import os, sys, json, math, shutil, re, time
RUN=str(int(time.time())%100000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.spatial.transform import Rotation
from swconn import *
from swpv import pv
from swdialog import template_clicker
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
DL=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_3D다운로드")
TMP=os.path.join(DL,"_children_tmp")
mm=lambda v:v/1000.0
stop=watchdog(); app=connect()
SPIOP=r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\spiop"
for _i in range(30):   # 닫으면 목록의 다른 객체가 무효가 되므로 한 번에 하나씩(최대 30)
    victim=None
    for x in (pv(app,"GetDocuments") or []):
        try: pth=x.GetPathName or ""; tt=x.GetTitle
        except Exception: continue
        if pth.startswith(TMP) or pth.startswith(SPIOP) or tt.startswith(("PIVOT PIN","RING_SHCCG","G11e_SHCCG","J11d_SHCCG")): victim=tt; break
    if victim is None: break
    n0=len(pv(app,"GetDocuments") or []); app.CloseDoc(victim); n1=len(pv(app,"GetDocuments") or []); print("closed leftover",victim,n0,"->",n1)
    if n1>=n0: print("  cannot close, giving up"); break
shutil.rmtree(TMP,ignore_errors=True); os.makedirs(TMP,exist_ok=True)
tmpl=app.GetUserPreferenceStringValue(8)
for x in list(pv(app,"GetDocuments") or []):
    tt=x.GetTitle
    if re.fullmatch(r"파트[4-9][0-9]",tt) and not x.GetPathName: app.CloseDoc(tt); print("closed stray",tt)
JOBS=[
 {"code":"J2c","src":os.path.join(DL,"J2_PSSFAQ16-590-B10.step"),"out":"J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT",
  "R":[[0,0,-1],[0,1,0],[1,0,0]],"t":[0,0,0],
  "props":{"TITLE":"GUIDE SHAFT (MISUMI PSSFAQ16-590-B10)","SPEC":"MISUMI PSSFAQ16-590-B10: Ø16 g6(−0.006/−0.017) L590 + 편단 M16×P2.0 수나사 B10(전장 600), SUS440C 상당 고주파 담금질 56HRC↑, 경질 크롬 도금 HV750↑ 5 µm↑, L 공차 ±0.8, 진직도 (L/100)×0.01, 진원도 0.005, 단부 직각도 0.2. 3D = MISUMI 생성 STEP(형번 정확, 나사 미표현 단순 원통). 파트 좌표: 축 −Z, 상단(나사 쪽) z 0","MATERIAL":"SUS440C 상당","QT'Y":"2","DATE":"2026-09-10","REMARK":"J1c M16 탭 관통(t10 = 나사길이 10)에 체결, 풀림 방지제. 하단 자유단. 종전 J2(PSSFAQ16-250-B30 STEP을 L600으로 쓴 것) 대체"}},
 {"code":"G11f","src":os.path.join(DL,"G11e_SHCCG8-22.8.step"),"out":"G11f_MISUMI_SHCCG8-22.8_pin.SLDPRT",
  "R":[[0,1,0],[-1,0,0],[0,0,1]],"t":[0,0,0],
  "props":{"TITLE":"REAR PIN (MISUMI SHCCG8-22.8)","SPEC":"MISUMI SHCCG8-22.8 힌지핀 플랜지붙이 고정링 타입: D8 g6(−0.005/−0.014, L부), L22.8(±0.2), 헤드 Ø12×T2, 고정링 홈 M0.9·d7(+0.09/0)·N3, E형 고정링 JIS No.7 부속, SUS304. 전체길이 L+N+T = 27.8. 3D = MISUMI 생성 STEP(핀+E링 2바디). 파트 좌표: 핀 축 +Y, 머리/핀 경계 y 0, 머리 −y","MATERIAL":"SUS304","QT'Y":"1","DATE":"2026-09-10","REMARK":"TA2 후단 클레비스 U(바깥폭 22.4, TraceParts 3D 실측)에 러그 J8e를 꽂는 핀. L = U 바깥폭 + 0.4. 종전 SHCCG8-18.4(U 18 가정) 대체 — 승인도면으로 최종 확인"}},
 {"code":"J11e","src":os.path.join(DL,"J11d_SHCCG8-18.0.step"),"out":"J11e_MISUMI_SHCCG8-18_pin.SLDPRT",
  "R":[[0,1,0],[-1,0,0],[0,0,1]],"t":[0,0,0],
  "props":{"TITLE":"ROD PIN (MISUMI SHCCG8-18)","SPEC":"MISUMI SHCCG8-18 힌지핀 플랜지붙이 고정링 타입: D8 g6(−0.005/−0.014, L부), L18(±0.2), 헤드 Ø12×T2, 고정링 홈 M0.9·d7(+0.09/0)·N3, E형 고정링 JIS No.7 부속, SUS304. 전체길이 23. 3D = MISUMI 생성 STEP(핀+E링 2바디). 파트 좌표: 핀 축 +Y, 머리/핀 경계 y 0, 머리 −y","MATERIAL":"SUS304","QT'Y":"2","DATE":"2026-09-10","REMARK":"TA2 전단 클레비스 U(바깥폭 17.6, TraceParts 3D 실측)에 러그 J9d를 꽂는 핀(상승/하강 인스턴스 2). L = U 바깥폭 + 0.4. 종전 SHCCG8-20.4(U 20 가정) 대체 — 승인도면으로 최종 확인. MISUMI 형번 표기는 SHCCG8-18"}},
 {"code":"G3c","src":r"<MCP_DIR>\_backup\20260909-unused\G3_valve_body_Tameson_BL2SA3-034.SLDPRT","out":"G3c_valve_3PC_3-4in_ISO_Tameson_BL2SA3-034.SLDPRT",
  "R":[[0,0,-1],[-1,0,0],[0,1,0]],"t":[-118.6,-91.2,57.4],
  "props":{"TITLE":"BALL VALVE 3PC 3/4in ISO5211 (형상 대용: Tameson BL2SA3-034)","SPEC":"구매 사양: 스텐 3PC 볼밸브 3/4\"(20A) 풀보어 · ISO5211 F03/F04(F05) 직접 취부 패드 · 자동장착용(태성 20S3 계열, 형번·치수 원문 미확보). 3D 형상 대용 = Tameson BL2SA3-034(G3/4 암 BSPP, 3PC 풀보어 보어 20, ISO5211 F03/F04/F05, 스템 9각, 316(1.4408), PTFE 시트, PN63, −20~180 ℃, 850 g) 제조사 STEP: 면간 83, 유로축→패드면 43.5(STEP 실측). 파트 좌표: 유로 축 −Z, 상단 끝면 z 0, 패드면 y −43.5","MATERIAL":"SUS316(CF8M)","QT'Y":"1","DATE":"2026-09-10","REMARK":"종전 근사 G3b(L80·패드 48 가정)를 같은 규격군의 제조사 3D로 대체(CLAUDE.md §4 ②). 태성 20S3 실치수 확인 시 스택(H16 −117·B4c y −43.5·호스 L353) 재조정"}},
]
def bodies(d): return list(pv(d,"GetBodies2",0,False) or [])
def bbox(b): return np.array([v*1000 for v in pv(b,"GetBodyBox")])
def centroid(b): return np.array(pv(b,"GetMassProperties",0)[0:3])*1000
def sel_bodies(d,bs):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1
    for b in bs: b.Select2(True,sd)
SLOT={"x":(0,0,1),"y":(0,1,0),"z":(1,0,0)}   # 실측: 8번째 인수=Z, 9번째=Y, 10번째=X
def rotate_bodies(d,pick,R,name):
    """pick(): 피처마다 돌릴 바디를 새로 고른다(이동 피처가 생기면 바디 객체·이름이 바뀜)"""
    ang=Rotation.from_matrix(np.array(R,float).T).as_euler("xyz")
    for axis,val in zip("xyz",ang):
        if abs(val)<1e-9: continue
        s=SLOT[axis]; sel_bodies(d,pick()); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, s[0]*val,s[1]*val,s[2]*val, False,1); d.EditRebuild3
        assert mv is not None, ("rot failed",name,axis); mv.Name=f"{name}_{axis.upper()}"
def translate_bodies(d,pick,t,name):
    if np.allclose(t,0): return
    sel_bodies(d,pick()); mv=d.FeatureManager.InsertMoveCopyBody2(mm(t[0]),mm(t[1]),mm(t[2]),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3
    assert mv is not None, ("trans failed",name); mv.Name=name
def close_by_path(paths):
    for pth in paths:
        for x in list(pv(app,"GetDocuments") or []):
            if x.GetPathName==pth: app.CloseDoc(x.GetTitle)
rep={}
for job in JOBS:
    out=os.path.join(Z,job["out"])
    if os.path.exists(out): print("skip existing",job["out"]); continue
    src=job["src"]; assert os.path.exists(src), src
    is_step=src.lower().endswith(".step")
    if is_step:
        evt=template_clicker(); imp=app.GetImportFileData(src); e=I4(); d=app.LoadFile4(src,"r",imp,e); evt.set(); d=app.ActiveDoc; title=d.GetTitle
        if d.GetType==2:   # 자식 파트 SaveAs → 새 파트에 합성
            cm=d.ConfigurationManager; kids=list(pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")); rec=[]
            for k,c in enumerate(kids):
                md=c.GetModelDoc2; pth=os.path.join(TMP,f"{job['code']}_{RUN}_c{k}.SLDPRT")
                app.ActivateDoc3(md.GetTitle,False,0,I4()); e=I4(); w=I4(); ok=md.Extension.SaveAs(pth,0,1,NOD,e,w); print("  child saveas",os.path.basename(pth),ok,e.value,w.value); assert ok
                xf=xform(c); rec.append({"file":pth,"R":xf["R"],"t":xf["t_mm"]})
            kid_paths=[c.GetPathName for c in kids]; app.CloseDoc(title); close_by_path(kid_paths); close_by_path([r["file"] for r in rec])
            d=app.NewDocument(tmpl,0,0,0); final=[]
            def target():
                c_=[b for b in bodies(d) if not any(np.all(np.abs(bbox(b)-fb)<0.05) for fb in final)]; assert len(c_)==1,len(c_); return c_[0]
            for r in rec:
                f=d.InsertPart3(r["file"],1|512|262144,""); d.EditRebuild3; assert f is not None
                b=target(); c_loc=centroid(b); Rc=np.array(r["R"]); tc=np.array(r["t"]); c_exp=c_loc@Rc+tc
                if not np.allclose(Rc,np.eye(3),atol=1e-6): rotate_bodies(d,lambda:[target()],Rc,"자식회전")
                translate_bodies(d,lambda:[target()],tc,"자식이동"); b=target(); c_got=centroid(b)
                assert np.all(np.abs(c_got-c_exp)<0.05), ("child transform",job["code"],c_got,c_exp)
                final.append(bbox(b))
    else:   # 백업 SLDPRT → 사본
        shutil.copy2(src,out); d=open_doc(app,out,1); app.ActivateDoc3(out,False,0,I4()); d=app.ActiveDoc
    # ---- 전체 정렬(회전은 축별 피처, 무게중심으로 검증)
    R=np.array(job["R"],float); t=np.array(job["t"],float)
    exp=sorted([centroid(b)@R+t for b in bodies(d)],key=lambda c:(round(c[2],1),round(c[1],1),round(c[0],1)))
    rotate_bodies(d,lambda:bodies(d),R,"정렬회전"); translate_bodies(d,lambda:bodies(d),t,"정렬이동")
    bs=bodies(d); got=sorted([centroid(b) for b in bs],key=lambda c:(round(c[2],1),round(c[1],1),round(c[0],1)))
    assert all(np.all(np.abs(g-e)<0.05) for g,e in zip(got,exp)), ("align",job["code"],got,exp)
    pb=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]
    cp=d.Extension.CustomPropertyManager("")
    for k_,v_ in job["props"].items():
        if cp.Get(k_): cp.Set2(k_,v_)
        else: cp.Add3(k_,30,v_,1)
    if is_step:
        e=I4(); w=I4(); ok=d.Extension.SaveAs(out,0,1,NOD,e,w)
    else:
        e=I4(); w=I4(); ok=d.Save3(1,e,w)
    print(f"[{job['code']}] bodies {len(bs)} box {pb} saved {ok} err {e.value} -> {job['out']}")
    rep[job["code"]]={"out":job["out"],"box":pb,"bodies":[(pv(b,'Name'),bbox(b).round(2).tolist()) for b in bs]}
json.dump(rep,open(os.path.join(VER,"purchased_parts_build_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
close_by_path([os.path.join(TMP,f) for f in os.listdir(TMP)]); shutil.rmtree(TMP,ignore_errors=True)
stop.set(); print("build done")
