# 2026-09-10: CLAUDE.md §4 — 3D 미제공 확인된 근사 형상 파트(G13·G14·H16·G3b)와 단순화 STEP(J2)의 SPEC/REMARK에 사실 명기(날짜 없음, 중복 append 방지) + 저장
#  + KE002 중간 산출물(_3D다운로드\KE002_children: 자식 파트 13·합성 어셈블리) SW에서 닫고 삭제(B4c는 링크 끊김)
import os, sys, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
TMP=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_3D다운로드","KE002_children")
stop=watchdog(); app=connect()
NOTE={
 "G13_weld_socket_3-4in_L25.SLDPRT":     ("SPEC","근사형상(나사 미표현) — PF3/4 SUS 용접소켓 3D는 MISUMI·GrabCAD 미제공(MISUMI 후보 요도시 S-20A는 Rp 나사·L36)"),
 "G14_close_nipple_3-4in_L32.SLDPRT":    ("SPEC","근사형상(나사 미표현) — PF3/4 SUS 클로즈니플 3D는 MISUMI·GrabCAD 미제공(MISUMI 후보 TRUSCO TNN-20A는 R 나사·CAD 없음)"),
 "H16_hose_nipple_3-4in_short_L30.SLDPRT":("SPEC","근사형상(나사·바브 미표현) — PF3/4 SUS 호스니플 3D는 MISUMI·GrabCAD 미제공(MISUMI 후보 이녹 304HN-20은 R 나사·2D만)"),
 "G3b_valve_3PC_3-4in_ISO_F03F04_SUS.SLDPRT":("SPEC","근사형상(한국바자 3PC 자동장착용 치수표 기준) — ISO5211 패드 부착 3PC 나사식 SUS 볼밸브 3D는 MISUMI·GrabCAD 미제공"),
 "J2_guide_shaft_MISUMI_PSSFAQ16-590-B10.SLDPRT":("REMARK","3D는 MISUMI STEP PSSFAQ16-250-B30(나사 생략 원통)을 L590으로 쓴 것 — 정확 형번 PSSFAQ16-590-B10 STEP은 MISUMI 로그인 후 교체. 카탈로그 공차 D16 g6(−0.006/−0.017)·L ±0.8·진직도 (L/100)×0.01·나사 M16 P2.0 유효길이 B−4"),
}
for fn,(key,note) in NOTE.items():
    p=os.path.join(Z,fn); d=app.GetOpenDocumentByName(p) or open_doc(app,p,1); app.ActivateDoc3(p,False,0,I4()); d=app.ActiveDoc
    cp=d.Extension.CustomPropertyManager(""); cur=cp.Get(key) or ""
    if "근사형상" in cur and key=="SPEC" or ("PSSFAQ16-250-B30" in cur and key=="REMARK"):
        print("skip (already)",fn); continue
    new=(cur+" | "+note) if cur else note
    r=cp.Set2(key,new) if cur else cp.Add3(key,30,new,1)
    e=I4(); w=I4(); ok=d.Save3(1,e,w); print("set",key,fn,"->",r,"save",ok,e.value)
# ---- 중간 산출물 정리
for x in list(pv(app,"GetDocuments") or []):
    pth=x.GetPathName
    if pth and pth.startswith(TMP): app.CloseDoc(x.GetTitle); print("closed",os.path.basename(pth))
if os.path.isdir(TMP):
    n=len(os.listdir(TMP)); shutil.rmtree(TMP,ignore_errors=True); print("removed",TMP,"files",n,"left?",os.path.isdir(TMP))
stop.set(); print("done")
