# 2026-09-14: 50A 텔레스코픽 라인 자작·규격 부품 생성 (파트 좌표: 축 Z, 원점 = 상단, −z로 연장)
#  G13d 배럴 니플 R2 L58 · K1 플런저 관 · K2 슬리브 관 65A · K3 씰 캡 · K4 O링 P60(압축 단면 표현)
import os, sys, json, math
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
mm=lambda v:v/1000.0
Zp=lambda n: os.path.join(Z,n)
stop=watchdog(); app=connect(); tmpl=app.GetUserPreferenceStringValue(8)
for x in list(pv(app,"GetDocuments") or []):
    try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
    except Exception: continue
    if (ty==1 and not pn and tt.startswith("파트")) or tt.startswith("K2_sleeve_pipe_65A_Sch10S_L255"):
        app.CloseDoc(tt); print("closed",tt)
old255=Zp("K2_sleeve_pipe_65A_Sch10S_L255.SLDPRT")
if os.path.exists(old255): os.remove(old255); print("removed K2 L255")
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def sel_plane(d,nm):
    ko={"정면":"Front Plane","윗면":"Top Plane","우측면":"Right Plane"}[nm]
    d.ClearSelection2(True); return d.Extension.SelectByID2(nm,"PLANE",0,0,0,False,0,NOD,0) or d.Extension.SelectByID2(ko,"PLANE",0,0,0,False,0,NOD,0)
def feats(d):
    out=[]; f=pv(d,"FirstFeature")
    while f is not None: out.append((f.Name,pv(f,"GetTypeName2"))); f=pv(f,"GetNextFeature")
    return out
def new_sketch(d,plane,draw):
    assert sel_plane(d,plane); d.SketchManager.InsertSketch(True); sm=d.SketchManager; sm.AddToDB=True; draw(sm); sm.AddToDB=False
    d.SketchManager.InsertSketch(True); d.ClearSelection2(True); last=[n for n,t in feats(d) if t=="ProfileFeature"][-1]
    assert d.Extension.SelectByID2(last,"SKETCH",0,0,0,False,0,NOD,0)
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): bs=bodies(d); assert len(bs)==1,len(bs); return [round(v*1000,2) for v in pv(bs[0],"GetBodyBox")]
def extrude(d,depth,name,start_off=0.0,flip=False):
    # 스케치면(정면=XY)에서 −z 방향. start_off>0 이면 z=−start_off 에서 시작(오프셋 시작조건, 방향은 결과 박스로 검증)
    if start_off:
        f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,3,mm(start_off),flip)
    else:
        f=d.FeatureManager.FeatureExtrusion3(True,False,True,0,0,mm(depth),0.0,False,False,False,False,0.0,0.0,False,False,False,False,True,True,True,0,0.0,False)
    d.EditRebuild3; assert f is not None, "extrude "+name; f.Name=name; return f
def ring(sm,ro,ri):
    sm.CreateCircleByRadius(0,0,0,mm(ro)); 
    if ri: sm.CreateCircleByRadius(0,0,0,mm(ri))
def tube_part(path,ro,ri,L,props,title_feat):
    if os.path.exists(path): print("exists",os.path.basename(path)); return
    d=app.NewDocument(tmpl,0,0,0)
    new_sketch(d,"정면",lambda sm: ring(sm,ro,ri)); extrude(d,L,title_feat)
    bx=bbox(d); print(os.path.basename(path),"box",bx,"ww",ww(d)); assert abs(bx[2]+L)<0.1 and abs(bx[5])<0.1 and abs(bx[3]-ro)<0.1 and not ww(d), bx
    cp=d.Extension.CustomPropertyManager("")
    for k,v in props.items(): cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍",props.get("_mat","STS 304"))
    except Exception as ex: print("  mat exc",ex)
    e=I4(); w=I4(); ok=d.Extension.SaveAs(path,0,1,NOD,e,w); print("  saved",ok,e.value); assert ok
DATE="2026-09-14"
# ---- G13d 배럴 니플 R2 L58 (KS B 1533 50A): OD 60.5(Sch40 관 치수), 보어 52.7
tube_part(Zp("G13d_barrel_nipple_R2_KS_L58.SLDPRT"),30.25,26.35,58.0,{
 "TITLE":"BARREL NIPPLE R2 (KS B 1533 50A) — 고정판 용접",
 "SPEC":"KS B 1533 배럴 니플 50A(2): 수나사 R2 양쪽(KS B 0222), SUS304, L 58(규격 최소 58), OD 60.5·보어 52.7(Sch40 관 치수, KS B 1533 부표1 비고: KS D 3576 Sch20S 이상). 한쪽 끝을 고정판 J1c 구멍(Ø61)에 10 삽입해 밑면 필릿 용접, 다른 쪽 밸브 G2에 20 물림(가정: ISO 7-1 R2 손조임 15.9 + 여유 ≤5 — 미확인). 나사 미표현.",
 "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"규격품(KS B 1533). 나사 R2×G2(밸브 평행 암나사) 조합은 PTFE 테이프 실링 전제 — 종전 3/4 라인과 동일 방식."},"니플_OD60.5_L58")
# ---- K1 플런저 관: 50A Sch40 STS304 (OD 60.5 t3.9) L227, 상단 25 R2 나사(미표현), 미끄럼부 외경 연마
tube_part(Zp("K1_plunger_pipe_50A_Sch40_L227.SLDPRT"),30.25,26.35,227.0,{
 "TITLE":"PLUNGER PIPE 50A (고정측, 텔레스코픽 내관)",
 "SPEC":"STS304 50A Sch40 관(KS D 3576, OD 60.5 t3.9 — JIS G 3459 표8 원문값), L 227. 상단 25: 수나사 R2(KS B 0222, 밸브 G2 하단에 20 물림, 나사 미표현). 미끄럼부(상단 40 이하 전장): 외경 연마 Ø60.5 −0/−0.1 Ra 0.8 이하(O링 미끄럼면), 하단 모서리 C1.5. 내경 52.7.",
 "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 하강 시 씰 캡 하단 아래 10 노출 여유, 상승 시 이동판 상면 위 5."},"플런저_OD60.5_L227")
# ---- K2 슬리브 관: 65A Sch10S (OD 76.3 t3.0) L255 — 이동판 관통 용접, 하단 = 노즐
tube_part(Zp("K2_sleeve_pipe_65A_Sch10S_L263.SLDPRT"),38.15,35.15,263.0,{
 "TITLE":"SLEEVE / NOZZLE PIPE 65A (이동측, 텔레스코픽 외관)",
 "SPEC":"STS304 65A Sch10S 관(KS D 3576, OD 76.3 t3.0 — JIS G 3459 표8 원문값), L 263. 상단 8을 씰 캡 K3 카운터보어에 끼워 둘레 용접, 이동판 J5f 구멍 Ø76.5 관통(관 상단이 판 상면 위 163) 양면 필릿 용접, 하단 100 = 노즐(로봇 개구 210×210 안, 여유 y ±67·x 앞 44/뒤 90).",
 "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 내경 70.3, 플런저 OD 60.5와 반경 틈 4.9(안내는 가이드봉·부시가 담당)."},"슬리브_OD76.3_L263")
# ---- K4 O링 P60 (JIS B 2401 / KS B 2805): 압축 상태 단면 표현 — ID 60.5(플런저) ~ OD 69.2(홈 바닥), 폭 5.7
tube_part(Zp("K4_oring_P60.SLDPRT"),34.6,30.25,5.7,{
 "TITLE":"O-RING P60 (씰 캡 내부, 왕복 운동용)",
 "SPEC":"KS B 2805(JIS B 2401) P60: 선경 5.7, 내경 59.6. 재질 NBR 또는 EPDM(염수·−30 ℃ → EPDM 권장, 재질 확정 미정). 3D는 압축 상태 단면(ID 60.5·OD 69.2·폭 5.7) 표현.",
 "Material":"EPDM","QT'Y":"2","DATE":DATE,"REMARK":"구매품(NOK·MISUMI 등). 3D 원본 미확보 → 단면 표현.","_mat":"고무"},"O링_P60_압축표현")
# ---- K3 씰 캡: Ø90 × L45, 보어 Ø61, O링 홈 2(Ø69.2 폭 7.5 @ z −10~−17.5, −25~−32.5), 하단 카운터보어 Ø76.5 깊이 8(관 삽입 용접)
P3=Zp("K3_seal_cap_D90_L45.SLDPRT")
if not os.path.exists(P3):
    d=app.NewDocument(tmpl,0,0,0)
    segs=[(0,10,30.5),(10,17.5,34.6),(17.5,25,30.5),(25,32.5,34.6),(32.5,37,30.5),(37,45,38.25)]
    first=True
    for (z0,z1,ri) in segs:
        for flip in (False,True):
            new_sketch(d,"정면",lambda sm,ri=ri: ring(sm,45.0,ri)); f=extrude(d,z1-z0,f"캡링_{z0:g}_{z1:g}",start_off=(0.0 if first else z0),flip=flip)
            bs=bodies(d); zr=[[round(v*1000,1) for v in pv(b,"GetBodyBox")] for b in bs]
            ok=len(bs)==1 and abs(min(b[2] for b in zr)+z1)<0.05
            print("  segs",z0,z1,"flip",flip,"bodies",len(bs),zr[-1],"ok",ok)
            if ok: break
            d.ClearSelection2(True); d.Extension.SelectByID2(f.Name,"BODYFEATURE",0,0,0,False,0,NOD,0); d.Extension.DeleteSelection2(1); d.EditRebuild3
            if first: break
        assert ok, ("cap seg failed",z0,z1)
        first=False
    bs=bodies(d); assert len(bs)==1, ("cap not merged",len(bs))
    bx=bbox(d); print("K3 box",bx,"ww",ww(d)); assert abs(bx[2]+45)<0.1 and abs(bx[5])<0.1 and not ww(d), bx
    vol=pv(bs[0],"GetMassProperties",0)[3]*1e9
    exp=sum((z1-z0)*math.pi*(45**2-ri**2) for z0,z1,ri in segs); print("K3 vol",round(vol),"expected",round(exp)); assert abs(vol-exp)<50
    cp=d.Extension.CustomPropertyManager("")
    for k,v in {"TITLE":"SEAL CAP (텔레스코픽 슬리브 상단 씰 하우징)",
     "SPEC":"STS304 환봉 Ø90 기계가공, L 45. 보어 Ø61 H9(플런저 Ø60.5 미끄럼, 틈 0.25~0.3), O링 홈 2개 Ø69.2 폭 7.5(P60 왕복용, 홈 상단 10·25), 하단 카운터보어 Ø76.5 깊이 8(슬리브 관 65A 삽입 후 둘레 용접). 상단 모서리 C1 + 더스트 와이퍼 권장(염 결정 제거 — 형번 미정).",
     "Material":"STS304","QT'Y":"1","DATE":DATE,"REMARK":"자작. 홈 치수는 KS B 2799(O링 홈) 대조 미완 — 미확인."}.items(): cp.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍","STS 304")
    except Exception as ex: print("  mat exc",ex)
    e=I4(); w=I4(); ok=d.Extension.SaveAs(P3,0,1,NOD,e,w); print("  saved K3",ok,e.value); assert ok
else: print("exists K3")
stop.set(); print("parts done")
