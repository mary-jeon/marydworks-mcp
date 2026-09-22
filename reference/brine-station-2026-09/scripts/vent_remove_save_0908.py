"""09-08 저녁: (1) 탱크 조립 S30000MU0 재빌드 + 간섭검사(판금 변환 후 뚜껑 S30008 ↔ 경첩/걸쇠/패드 확인, 통기구 제거 확인)
(2) S30006(통기구 컷 제거)·S30000MU0(S30018 삭제) 저장 (3) S30018MU0 문서 닫고 파일을 sw-mcp\_backup\20260908-unused 로 이동
사용자 지시: "통기구 없애줘. 나중에 내가 생각해볼게"
"""
import sys, os, json, shutil
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
stop=watchdog(); app=connect()
OUT=r"<PROJECT_DIR>\_검증\tank_recheck_2026-09-08\vent_remove_save.json"
BK=r"<MCP_DIR>\_backup\20260908-unused"
log={}
def interf(doc):
    idm=pv(doc,"InterferenceDetectionManager")   # IAssemblyDoc 속성(Extension 아님)
    idm.TreatCoincidenceAsInterference=False; idm.IncludeMultibodyPartInterferences=False; idm.UseTransform=True
    res=[]
    for it in (pv(idm,"GetInterferences") or []):
        res.append({"vol_mm3":round(it.Volume*1e9,1),"comps":[c.Name2 for c in (pv(it,"Components") or [])]})
    idm.Done(); return sorted(res,key=lambda r:-r["vol_mm3"])
def save(d,name):
    e=I4(); w_=I4(); ok=d.Save3(1,e,w_); print("SAVE",name,ok,e.value,w_.value); log.setdefault("saved",{})[name]=[ok,e.value,w_.value]; return ok
A=os.path.join(Z,"S30000MU0.SLDASM"); asm=app.GetOpenDocumentByName(A); app.ActivateDoc3(A,False,0,I4()); print("asm type",asm.GetType, asm.GetTitle)
cm=asm.ConfigurationManager
def comps(): return {c.Name2.split("/")[-1]:c for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")}
asm.ForceRebuild3(False)
cc=comps(); log["components"]=sorted(cc)
print("S30018 in asm:",[n for n in cc if n.startswith("S30018")])
# S30006 통기구 구멍 확인(Ø35 원통면 없음)
S6=os.path.join(Z,"S30006MU0.SLDPRT"); d6=app.GetOpenDocumentByName(S6)
cyl=[]
for f in (pv((pv(d6,"GetBodies2",0,True) or [])[0],"GetFaces") or []):
    s=f.GetSurface
    if s.IsCylinder: cyl.append(round(s.CylinderParams[6]*2000,1))
log["S30006_cyl_dia"]=sorted(cyl); print("S30006 cylinder dia list:",sorted(cyl))
sk=[]; f=pv(d6,"FirstFeature")
while f is not None:
    t=pv(f,"GetTypeName2")
    if t in ("ProfileFeature","Extrusion","ICE","Cut"): sk.append((f.Name,t))
    f=pv(f,"GetNextFeature")
log["S30006_feats"]=sk; print("S30006 feats:",sk)
# 간섭검사 (판금 변환 뚜껑 포함)
log["interf"]=interf(asm); print("interferences:",log["interf"][:12])
# 뚜껑 S30008 ↔ 경첩 위치 확인: 뚜껑 뒤쪽 굽힘(r4)과 리프1(수직면 Y 814~839) 겹침 여부는 간섭 결과로 판정
for n,c in cc.items():
    if n.startswith(("S30008","C-HHSN65A","C-1170","S30017")): print("  ",n,box(c))
# 저장
save(d6,"S30006MU0"); save(asm,"S30000MU0")
# S30018 문서 닫기(내 스크립트가 만든 파트) + 파일 이동
VP=os.path.join(Z,"S30018MU0.SLDPRT")
dv=app.GetOpenDocumentByName(VP)
if dv is not None: app.CloseDoc(dv.GetTitle); print("closed S30018 doc")
os.makedirs(BK,exist_ok=True)
try:
    shutil.move(VP,os.path.join(BK,"S30018MU0.SLDPRT")); log["S30018_moved"]=True; print("moved S30018MU0.SLDPRT ->",BK)
except Exception as ex:
    log["S30018_moved"]=str(ex); print("move failed:",ex)
json.dump(log,open(OUT,"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set()
