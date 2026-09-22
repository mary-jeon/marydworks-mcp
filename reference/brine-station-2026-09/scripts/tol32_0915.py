# 2026-09-15: 공차 적용 — 속성 TOLERANCE 기재(원문값) + 모델 수정(J5l 부시 구멍 Ø28 H7, J9f·J8e 러그 두께 5.8) → 저장·닫기
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
DESK=r"<PROJECT_DIR>"; VER=os.path.join(DESK,"_검증")
mm=lambda v:v/1000.0; Zp=lambda n: os.path.join(Z,n)
stop=watchdog(); app=connect()
def act(p,typ=1):
    d=app.GetOpenDocumentByName(p) or open_doc(app,p,typ); app.ActivateDoc3(p,False,0,I4()); return app.ActiveDoc
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
def setp(d,k,v):
    cp=d.Extension.CustomPropertyManager("")
    if cp.Get(k): cp.Set2(k,v)
    else: cp.Add3(k,30,v,1)
def circ_xy(s):
    cpt=pv(s,"GetCenterPoint2")
    try: cx,cy=cpt[0]*1000,cpt[1]*1000
    except TypeError: cx,cy=pv(cpt,"X")*1000,pv(cpt,"Y")*1000
    r=(s.GetRadius() if callable(s.GetRadius) else s.GetRadius)*1000
    return cx,cy,r
def bodies(d): return list(pv(d,"GetBodies2",0,True) or [])
def bbox(d): return [round(v*1000,2) for v in pv(bodies(d)[0],"GetBodyBox")]
GEN="일반공차 KS B ISO 2768-1 m급(JIS B 0405 m 원문: 0.5~3 ±0.1 / 3~6 ±0.1 / 6~30 ±0.2 / 30~120 ±0.3 / 120~400 ±0.5 / 400~1000 ±0.8; KS 본문 미확인). 형상공차 KS B ISO 22081(구 2768-2 K, 2025-12 폐지 확인 필요)."
TOL={
 "J1c_fixed_plate_185x580_t10.SLDPRT": GEN+" | 판 t10 소재 허용차 ±0.70(JIS G 4305 냉연, KS D 3698 미확인). 유로 구멍 Ø43 H11(+0.16/0) — 니플 OD 42.7 용접 여유 0.3~0.46. 봉 구멍 Ø16.5 H11(+0.11/0) — 봉 g6(Ø16 −0.006/−0.017) 관통 여유 0.5~0.63, 위치는 홀더 SHFSS16 보어 H7이 잡음. 홀더 M5 탭 4개소 위치 ±0.1(f급).",
 "J5l_moving_plate_180x540_t8.SLDPRT": GEN+" | 판 t8 소재 허용차 ±0.60(JIS G 4305). 부시 구멍 **Ø28 H7(+0.021/0)** — LHFRW16 외경 D28 0/−0.016 → 틈 0~0.037(안내 정밀도, 09-15 모델 Ø28.5→Ø28 수정). 부시 볼트 M4 탭 PCD38 위치 ±0.1(f급). 소켓 구멍 Ø49 H11(+0.16/0) — 소켓 OD 48.5 용접 여유 0.5~0.66. 두 부시 구멍 중심거리 480 ±0.1(봉 평행도).",
 "J9f_lug_PL6_40x69_pin60.SLDPRT": "두께 **5.8 ±0.05(f급, 기계가공)** — TA2 로드 클레비스 슬롯 6.0(TiMOTION 데이터시트 코드5, 공차 미기재)에 삽입 틈 0.15~0.25. 소재 PL6 ±0.50 그대로 쓰면 삽입 불가 가능. 핀 구멍 **Ø8 H7(+0.015/0)** — 핀 SHCCG8 g6(−0.005/−0.014) 틈 0.005~0.029. 핀 높이 60 ±0.2. "+GEN,
 "J8e_lug_PL6_40x26.SLDPRT": "두께 **5.8 ±0.05(f급, 기계가공)** — TA2 후단 CNC 슬롯 6.0 삽입 틈 0.15~0.25(PL6 ±0.5 원소재 불가). 핀 구멍 Ø8 H7(+0.015/0) — 핀 SHCCG8-22.8 g6 틈 0.005~0.029. "+GEN,
 "J2c_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT": "MISUMI 원문: D16 g6(−0.006/−0.017), L590 ±0.8, 진원도 0.005, 진직도 L/100×0.01(=0.059), 단면 직각도 0.2, M16 p2.0 유효 6. 부시 LHFRW16 내경(0/−0.010)과 최악 −0.004~+0.017(MISUMI 표준 조합).",
 "B10_linear_bushing_MISUMI_LHFRW16.SLDPRT": "MISUMI 원문: 내경 0/−0.010, 외경 D28 0/−0.016, L70 ±0.3, 플랜지 H48·T6, PCD38·d4.5(4홀), 편심·직각도 0.015, C 1230/Co 2350 N. 하우징(판 구멍) 권장 공차 미기재 → 설계 Ø28 H7 채택.",
 "J23b_shaft_support_MISUMI_SHFSS16_STEP.SLDPRT": "MISUMI 원문: 보어 Ø16 H7(슬릿 가공 후 H8로 열릴 수 있음), 취부 d5.5 ×4 PCD(A28/L1 40), 클램프 M4, h12.5 ±0.3. 봉 g6와 틈 +0.006~+0.035(H8 시 0.044).",
 "G11f_MISUMI_SHCCG8-22.8_pin.SLDPRT": "MISUMI 원문: D8 g6(−0.005/−0.014), L ±0.2(JIS B 0405 m), E링 홈 M0.9(+0.1/0)·d7(+0.09/0). 러그 Ø8 H7 틈 0.005~0.029. TA2 클레비스 구멍 8.0 공차 미기재(승인도면 항목).",
 "J11e_MISUMI_SHCCG8-18_pin.SLDPRT": "MISUMI 원문: D8 g6(−0.005/−0.014), L18 ±0.2, E링 홈 M0.9(+0.1/0). 러그 J9f Ø8 H7 틈 0.005~0.029. E링 여유 0.2~0.6(U 바깥폭 17.6 기준).",
 "G13f_barrel_nipple_R1-1-4_ONDA_SFN2-32_STEP.SLDPRT": "나사 R1-1/4 KS B 0222(JIS B 0203 원문): 기준경 41.910, 11산(p 2.3091), 기준길이 12.70(±2.31), 수나사 유효부 최소 19.1. 외경·길이 공차 온다 도면 미기재. 판 구멍 Ø43 H11 용접 여유 0.3~0.46.",
 "G13g_socket_Rc1-1-4_ONDA_SFS3-32_STEP.SLDPRT": "나사 Rc1-1/4 KS B 0222(JIS B 0203): 암나사 l 18.5 / l′ 21.4 / t 13.4. 외경·길이 공차 온다 도면 미기재. 판 구멍 Ø49 H11 용접 여유 0.5~0.66.",
 "H16d_hose_nipple_R1-1-4x34_ONDA_SFHN-3234_STEP.SLDPRT": "나사 R1-1/4 KS B 0222. 바브 Ø34 공차 온다 미기재; 호스 HSPF-032 내경 32.0±1.0 → 직경 간섭 1.0~3.0(압입, 호스밴드 필수).",
 "G3e_valve_3PC_32A_TAESUNG_S3_alt_Tameson_BL2SA3-114.SLDPRT": "태성 면간 L 100 ±1.6(도면 A110117-01-04). 나사 종류·패드·스템 공차 미기재(태성 문의).",
 "J19i_hose_YASUNG_HSPF-032_dn_straight_L336.SLDPRT": "야성 원문: 내경 32.0±1.0, 외경 41.0±1.0. 자유길이 절단 ±5(설계 지정). 굽힘반경 미기재.",
 "J19i_hose_YASUNG_HSPF-032_up_bow_R37.SLDPRT": "야성 원문: 내경 32.0±1.0, 외경 41.0±1.0. 상승 활 R36.5는 기하 요구값(공차 아님) — 실물 접힘 미확인.",
 "B9g_TiMOTION_TA2-2H-140339-5511-010-1.SLDPRT": "TiMOTION 데이터시트: 전단 클레비스 U 슬롯 6.0·깊이 10.5·구멍 8.0, 후단 CNC 슬롯 6.0·깊이 16.0·구멍 8.0 — 공차 미기재(승인도면 요청). STEP 실측 U 22.4/17.6·깊이 21.4/26은 데이터시트와 상이.",
}
rep={}
for fn,t in TOL.items():
    p=Zp(fn)
    if not os.path.exists(p): print("missing",fn); continue
    d=act(p); setp(d,"TOLERANCE",t)
    # 모델 수정
    if fn.startswith("J5l_"):
        if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
        d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1","SKETCH",0,0,0,False,0,NOD,0); d.EditSketch(); sk=d.SketchManager.ActiveSketch; d.ClearSelection2(True); n=0; pts=[]
        for s in list(pv(sk,"GetSketchSegments") or []):
            ty=s.GetType() if callable(s.GetType) else s.GetType
            if ty==1:
                cx,cy,r=circ_xy(s)
                if abs(r-14.25)<0.05: s.Select4(True,NOD); n+=1; pts.append((cx,cy))
        if n: d.Extension.DeleteSelection2(0)
        sm=d.SketchManager; sm.AddToDB=True
        for cx,cy in pts: sm.CreateCircleByRadius(mm(cx),mm(cy),0,mm(14.0))
        sm.AddToDB=False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.ForceRebuild3(False); print("J5l bushing holes ->Ø28",n,"ww",ww(d))
        cp=d.Extension.CustomPropertyManager(""); s_=cp.Get("SPEC") or ""; cp.Set2("SPEC",s_.replace("부시 LHFRW16 Ø28.5","부시 LHFRW16 Ø28 H7"))
    if fn.startswith(("J9f_","J8e_")):
        done=False; f=pv(d,"FirstFeature")
        while f is not None and not done:
            if pv(f,"GetTypeName2") in ("Extrusion","Boss"):
                dd=pv(f,"GetFirstDisplayDimension")
                while dd:
                    dim=dd.GetDimension2(0); val=dim.SystemValue*1000
                    if abs(val-6.0)<0.05:
                        try: dim.SetSystemValue3(mm(5.8),2,None)
                        except Exception: dim.SystemValue=mm(5.8)
                        d.ForceRebuild3(False); print(fn[:8],"thickness 6→",round(dim.SystemValue*1000,2),"ww",ww(d)); done=True; break
                    dd=pv(f,"GetNextDisplayDimension",dd)
            f=pv(f,"GetNextFeature")
        if not done: print(fn[:8],"thickness dim not found — 속성만 기재")
        bx=bbox(d); print("  box",bx)
    e=I4(); w=I4(); ok=d.Save3(1,e,w); rep[fn]=ok; print("saved",fn[:40],ok)
    if not fn.startswith(("J5l_","J9f_","J8e_")): app.CloseDoc(d.GetTitle)
# 러그 두께 5.8 → 어셈블리 y 오프셋(±3 → ±2.9)은 0.1 차이라 유지. 남은 파트 닫기
for fn in ("J5l_moving_plate_180x540_t8.SLDPRT","J9f_lug_PL6_40x69_pin60.SLDPRT","J8e_lug_PL6_40x26.SLDPRT"):
    x=app.GetOpenDocumentByName(Zp(fn))
    if x is not None: app.CloseDoc(x.GetTitle)
json.dump(rep,open(os.path.join(VER,"tol32_0915.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
stop.set(); print("done")
