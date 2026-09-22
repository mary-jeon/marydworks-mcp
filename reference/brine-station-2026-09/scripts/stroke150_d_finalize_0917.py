# 2026-09-17 마무리: 고아 스케치 전수 검사 → 저장(라인 어셈블리·J1c·J5l, Station 폴더만) → 파트 창 닫기(S00000MU0 유지) → 미참조 후보 참조 검사
import os, sys, json
sys.path.insert(0, r"<PROJECT_DIR>\_scripts")
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
Zp=lambda n: os.path.join(Z,n); rep={}
app=connect()
def ww(doc):
    fe=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); co=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None); wa=VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT,None)
    doc.Extension.GetWhatsWrong(fe,co,wa); return [(f.Name,c) for f,c in zip(fe.value or [],co.value or [])]
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
# 1) 고아 스케치: 오늘 만들거나 고친 파트 전부
PARTS=["J1c_fixed_plate_185x580_t10","J5n_moving_plate_180x540_t8","B9j_TiMOTION_TA2-2H-150274-5511-010-1","B10b_linear_bushing_MISUMI_LHFRW20_catalog","J23d_shaft_support_MISUMI_SHFSS20_catalog",
       "J2d_guide_shaft_MISUMI_PSSFAQ20-580-B13_catalog","J19n_hose_YASUNG_HSPF-032_up_loop190","J19n_hose_YASUNG_HSPF-032_dn_loop142"]
orph={}
for n in PARTS:
    p=Zp(n+".SLDPRT"); d=app.GetOpenDocumentByName(p) or open_doc(app,p,1)
    o=orphan_sketches(d); orph[n]=o; print(f"  orphan {n}: {o}  ww {ww(d)}  dirty {d.GetSaveFlag}")
assert not any(orph.values()), orph
rep["orphans"]={k:len(v) for k,v in orph.items()}
# 2) 저장: 라인 어셈블리 + dirty 파트(Station 폴더 안, 오늘 대상만). S00000/S30000는 저장 안 함.
a=app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM,False,0,I4()); a=app.ActiveDoc
a.ShowConfiguration2("상승"); a.ForceRebuild3(False); print("asm ww",ww(a),"cfg",a.ConfigurationManager.ActiveConfiguration.Name)
saved=[]
for n in PARTS:
    d=app.GetOpenDocumentByName(Zp(n+".SLDPRT"))
    if d is not None and d.GetSaveFlag:
        e=I4(); w=I4(); ok=d.Save3(1,e,w); print("  saved part",n,ok,e.value,w.value); assert ok; saved.append(n)
e=I4(); w=I4(); ok=a.Save3(1,e,w); print("  saved asm",ok,e.value,w.value); assert ok; saved.append("염수주입라인.SLDASM")
rep["saved"]=saved
# 3) 창 닫기: 파트 문서 전부(어셈블리가 참조하는 것은 메모리에 남고 창만 닫힘). 미참조(B9i·J2d-660·J19j)는 저장 없이 닫힘 → 변경 폐기
dirty_left=[]
for x in list(pv(app,"GetDocuments") or []):
    try: tt=x.GetTitle; pn=x.GetPathName; ty=x.GetType
    except Exception: continue
    if ty==1:
        if x.GetSaveFlag and os.path.basename(pn).split(".")[0] not in ("B9i_TiMOTION_TA2-2H-150339-5511-010-1",): dirty_left.append(os.path.basename(pn))
        app.CloseDoc(tt)
print("closed all part windows; dirty parts left (not saved):",dirty_left)
open_now=[]
for x in list(pv(app,"GetDocuments") or []):
    try: open_now.append((x.GetTitle,x.GetType,x.GetSaveFlag))
    except Exception: pass
print("open docs now",[o for o in open_now if o[1]==2]); rep["open_asm"]=[o for o in open_now if o[1]==2]
# 4) 미참조 검사(디스크 기준)
asms=[os.path.join(Z,f) for f in os.listdir(Z) if f.lower().endswith(".sldasm") and not f.startswith("~$")]
refs={}
for p in asms:
    try:
        dep=app.GetDocumentDependencies2(p,True,False,False); names=[os.path.basename(x).lower() for x in (dep or [])[1::2]] if dep else []
    except Exception as ex: names=[]; print("dep exc",os.path.basename(p),ex)
    refs[os.path.basename(p)]=set(names)
cands=[l.strip() for l in open(os.path.join(DESK,"_검증","unused_candidates_0917c.txt"),encoding="utf-8") if l.strip()]
res={}
for c in cands:
    fn=(c+".SLDPRT").lower(); who=[k for k,s in refs.items() if fn in s]; res[c]=who; print(("USED  " if who else "free  ")+c,who)
rep["unused_check"]=res
# 라인 어셈블리 결손 확인
dep=app.GetDocumentDependencies2(ASM,True,False,False); miss=[x for x in (dep or [])[1::2] if not os.path.exists(x)]; print("line asm missing refs",miss); rep["missing"]=miss
json.dump(rep,open(os.path.join(DESK,"_검증","stroke150d_finalize_0917.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
app.ActivateDoc3(ASM,False,0,I4()); print("DONE finalize")
