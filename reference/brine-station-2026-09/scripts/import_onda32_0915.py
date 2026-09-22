# 2026-09-15: ONDA 32A STEP(니플·소켓·호스니플) → Station 파트. 규약: 주축 = Z, 상단 z 0, 아래로 −L. 호스니플은 나사쪽이 위(z 0), 바브가 아래.
import os, sys, json, math, collections
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import numpy as np, pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
from swdialog import template_clicker
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증"); SRC=os.path.join(DESK,r"_원문\32A\onda")
mm=lambda v:v/1000.0; DATE="2026-09-15"
ITEMS=[
 ("ONDA_SFN2-32.stp","G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP.SLDPRT",None,{
   "TITLE":"BARREL NIPPLE R1-1/4 (ONDA SFN2-32, MISUMI) — 고정판 용접",
   "SPEC":"온다제작소 SFN2-32(MISUMI 오다제작소 221000590818): 원형 니플 R1-1/4×R1-1/4, SUS304TP, L 50(도면 SFN2型 p.13), 외경 Ø42.7(STEP 실측), 내경 35.5. 한쪽을 고정판 J1c 구멍(Ø43)에 삽입해 밑면 필릿 용접, 다른 쪽 밸브 상단에 물림. 최고압 2.0 MPa.",
   "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"규격품 3D: onda.co.jp 공식 STEP(로그인 불요), MISUMI 표준단가 5,184원(API). 나사 미표현."}),
 ("ONDA_SFS3-32.stp","G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP.SLDPRT",None,{
   "TITLE":"SOCKET Rc1-1/4 (ONDA SFS3-32, MISUMI) — 이동판 플러시 용접",
   "SPEC":"온다제작소 SFS3-32(MISUMI 221000590740): 리브 소켓 Rc1-1/4×Rc1-1/4(테이퍼 암), SCS13A, L 51·øD 48.5(리브 51.5, 도면 SFS3型 p.05). 이동판 구멍 Ø49에 상면 플러시 삽입 후 양면 필릿 용접. 위: 호스니플 R1-1/4 / 아래: 노즐관 R1-1/4.",
   "Material":"SCS13A","QT'Y":"1","DATE":DATE,"REMARK":"규격품 3D: onda.co.jp STEP. MISUMI 표준단가 14,010원. Rc(테이퍼)와 R 니플 조합(JIS B 2308 허용)."}),
 ("ONDA_SFHN-3234.stp","H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP.SLDPRT","hose",{
   "TITLE":"HOSE NIPPLE R1-1/4 x HOSE ID32 (ONDA SFHN-3234, MISUMI)",
   "SPEC":"온다제작소 SFHN-3234(MISUMI 221000586026): 육각 호스니플 R1-1/4, 바브 øD 34, L 87, 육각 B 45, 내경 27(도면 SFHN型 p.07). 호스 HSPF-032(내경 32)에 바브 34 압입(허용 여부 호스 카탈로그 확인 — 치수 우선이면 요도시 HONI-32A D33, 3D 없음). 상부: 밸브 하단 물림 / 하부: 소켓에 물림(뒤집어 설치).",
   "Material":"SCS13A","QT'Y":"2","DATE":DATE,"REMARK":"규격품 3D: onda.co.jp STEP. MISUMI 표준단가 24,810원. 나사·바브 요철은 STEP 그대로."}),
]
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def partbox(d): return [round(v*1000,2) for v in pv(d,"GetPartBox",True)]
def sel_body(d,b):
    d.ClearSelection2(True); sd=d.SelectionManager.CreateSelectData; sd.Mark=1; return b.Select2(False,sd)
def probe(d):
    cyl=[]
    for b in bodies(d):
        for fc in b.GetFaces():
            s=fc.GetSurface
            if s.IsCylinder:
                p=s.CylinderParams; cyl.append((tuple(p[3:6]),p[6]*1000,fc.GetArea*1e6,tuple(v*1000 for v in p[0:3]),[round(v*1000,2) for v in fc.GetBox]))
    return cyl
def main_axis(cyl):
    acc=collections.defaultdict(float)
    for ax,r,A,o,fb in cyl: acc[tuple(round(abs(v),3) for v in ax)]+=A
    return max(acc.items(),key=lambda kv:kv[1])[0]
def set_props(d,props,mat):
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items():
        if cp.Get(k): cp.Set2(k,v)
        else: cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍",mat)
    except Exception as ex: print("  mat exc",ex)
rep={}
for stp,outname,kind,props in ITEMS:
    OUT=os.path.join(Z,outname); STEP=os.path.join(SRC,stp)
    dd=app.GetOpenDocumentByName(OUT)
    if dd is not None: app.CloseDoc(dd.GetTitle)
    if os.path.exists(OUT): os.remove(OUT)
    evt=template_clicker(); imp=app.GetImportFileData(STEP); e=I4(); d=app.LoadFile4(STEP,"r",imp,e); evt.set(); d=app.ActiveDoc; print("import",stp,"→",d.GetTitle,d.GetType,"err",e.value)
    if d.GetType==2:
        kids=list(pv(d.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True),"GetChildren"))
        def ext(c):
            b=box(c); return (b[3]-b[0])*(b[4]-b[1])*(b[5]-b[2]) if b else 0
        big=max(kids,key=ext); pd=big.GetModelDoc2; app.ActivateDoc3(pd.GetTitle,False,0,I4()); pd=app.ActiveDoc; t=d.GetTitle
        e=I4(); w=I4(); ok=pd.Extension.SaveAs(OUT,0,1,NOD,e,w); app.CloseDoc(t)
        for x in list(pv(app,"GetDocuments") or []):
            try:
                if x.GetTitle.lower().startswith(stp.lower().replace(".stp","")): app.CloseDoc(x.GetTitle)
            except Exception: pass
    else:
        e=I4(); w=I4(); ok=d.Extension.SaveAs(OUT,0,1,NOD,e,w)
    d=act(OUT); bx=partbox(d); cyl=probe(d); ax=main_axis(cyl); print("  box",bx,"main axis",ax,"bodies",len(bodies(d)))
    # 회전: 주축 → Z. 축이 x면 y축 둘레 ±90°, y면 x축 둘레 ±90°. 결과 검증: 주축 (0,0,1)
    b=bodies(d)[0]
    if ax!=(0.0,0.0,1.0):
        for sgn in (1,-1):
            sel_body(d,b)
            if abs(ax[0])>0.9: mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,sgn*math.pi/2,0, False,1)
            else: mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,0,sgn*math.pi/2, False,1)
            d.EditRebuild3; assert mv; mv.Name="정렬_회전"
            ax2=main_axis(probe(d)); b=bodies(d)[0]; print("  rot sign",sgn,"→ axis",ax2)
            if ax2==(0.0,0.0,1.0): break
            d.ClearSelection2(True); d.Extension.SelectByID2("정렬_회전","BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3; b=bodies(d)[0]
    bx=partbox(d); cyl=probe(d)
    # 축 위치(x,y): 주축 원통 원점의 중앙값 → 0; z: 상단 → 0. 호스니플은 나사쪽(외경 33.5 원통)이 위가 되도록 필요 시 뒤집기
    zc=[c for c in cyl if tuple(round(abs(v),3) for v in c[0])==(0.0,0.0,1.0)]
    xs=[c[3][0] for c in zc]; ys=[c[3][1] for c in zc]; cx=float(np.median(xs)); cy=float(np.median(ys))
    flip=False
    if kind=="hose":
        # 바브(r≈17) 면의 z 중심 vs 나사(r≈16.75) 면의 z 중심: 바브가 위(z 큰 쪽)면 뒤집는다
        barb=[c for c in zc if abs(c[1]-17.0)<0.15]; thr=[c for c in zc if abs(c[1]-16.75)<0.2]
        zb=np.mean([(c[4][2]+c[4][5])/2 for c in barb]) if barb else None; zt=np.mean([(c[4][2]+c[4][5])/2 for c in thr]) if thr else None
        print("  hose nipple barb z",zb,"thread z",zt)
        if zb is not None and zt is not None and zb>zt: flip=True
    if flip:
        sel_body(d,b); mv=d.FeatureManager.InsertMoveCopyBody2(0,0,0,0, 0,0,0, 0,math.pi,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_뒤집기"; b=bodies(d)[0]; bx=partbox(d)
        cyl=probe(d); zc=[c for c in cyl if tuple(round(abs(v),3) for v in c[0])==(0.0,0.0,1.0)]; cx=float(np.median([c[3][0] for c in zc])); cy=float(np.median([c[3][1] for c in zc]))
    ztop=bx[5]
    sel_body(d,b); mv=d.FeatureManager.InsertMoveCopyBody2(mm(-cx),mm(-cy),mm(-ztop),0, 0,0,0, 0,0,0, False,1); d.EditRebuild3; assert mv; mv.Name="정렬_이동"
    bx=partbox(d); cyl=probe(d); zc=sorted(set((round(c[1],2),round(c[3][0],1),round(c[3][1],1)) for c in cyl if tuple(round(abs(v),3) for v in c[0])==(0.0,0.0,1.0)))
    print("  final box",bx,"Z-cyl (r,x,y)",zc[:8])
    assert abs(bx[5])<0.05 and abs(bx[2]+(bx[5]-bx[2]))<0.05
    set_props(d,props,{"STS304":"STS 304","SCS13A":"STS 304"}.get(props["Material"],"STS 304"))
    e=I4(); w=I4(); print("  save",d.Save3(1,e,w),e.value)
    rep[outname]={"box":bx,"zcyl":zc[:8]}
json.dump(rep,open(os.path.join(VER,"onda32_import_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("done")
