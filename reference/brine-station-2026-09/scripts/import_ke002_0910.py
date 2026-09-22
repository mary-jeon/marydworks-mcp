# 2026-09-10: 코사플러스 KE002 STEP(제조사 다운로드, 13파트 어셈블리 구조) → 어셈블리로 임포트 → 「어셈블리를 파트로 저장」(전 컴포넌트) → Station 폴더 B4c 파트
#  단계 1: 임포트+파트 저장+형상 조사(이 스크립트). 단계 2(align): 우리 B4b 원점 규약(패드면 y0, 스템축 = Y축)으로 바디 이동 후 어셈블리 교체.
#  임포트 시 「SOLIDWORKS 새 문서」 템플릿 대화상자가 떠서 LoadFile4가 블록됨 → 스레드로 확인 버튼 클릭.
import os, sys, json, time, threading, collections, ctypes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
VER=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"_검증")
STEP=r"<PROJECT_DIR>\_3D다운로드\B4b_KE002-F35C11-DC.step"
OUT=os.path.join(Z,"B4c_actuator_KOSAPLUS_KE002-F35C11-DC.SLDPRT")
assert os.path.exists(STEP)
stop=watchdog(); app=connect()
# ---- 재실행 대비: 곡면만 남은 B4c(이 세션에서 만든 파일)를 닫고 삭제
dd=app.GetOpenDocumentByName(OUT)
if dd is not None: app.CloseDoc(dd.GetTitle); print("closed old B4c")
if os.path.exists(OUT): os.remove(OUT); print("removed old B4c file")
# ---- 임포트 옵션: 니트 옵션(swImportNeutral_KnitOption=577) → 솔리드 형성 시도
import pythoncom
tlb=pythoncom.LoadTypeLib(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\swconst.tlb"); knit_enum={}
for i in range(tlb.GetTypeInfoCount()):
    if "KnitOption" in tlb.GetDocumentation(i)[0]:
        ti=tlb.GetTypeInfo(i); ta=ti.GetTypeAttr(); knit_enum={ti.GetNames(ti.GetVarDesc(j).memid)[0]:ti.GetVarDesc(j).value for j in range(ta.cVars)}
print("knit enum",knit_enum,"current",app.GetUserPreferenceIntegerValue(577))
solid_val=[v for k,v in knit_enum.items() if "solid" in k.lower()]
if solid_val:
    print("set KnitOption ->",solid_val[0],app.SetUserPreferenceIntegerValue(577,solid_val[0]),"now",app.GetUserPreferenceIntegerValue(577))
print("toggles: SolidSurface",app.GetUserPreferenceToggle(686),"SolidBody",app.GetUserPreferenceToggle(694),"SurfaceBody",app.GetUserPreferenceToggle(695))
u=ctypes.windll.user32
def dialog_clicker(stop_evt):
    # 「SOLIDWORKS 새 문서」(#32770) 대화상자의 '확인' 버튼을 누른다 (마우스·포커스 점유 없음)
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(h,l):
        n=u.GetWindowTextLengthW(h); buf=ctypes.create_unicode_buffer(n+1); u.GetWindowTextW(h,buf,n+1)
        if buf.value=="SOLIDWORKS 새 문서" and u.IsWindowVisible(h):
            kids=[]
            @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            def cb2(c,l2):
                m=u.GetWindowTextLengthW(c); b2=ctypes.create_unicode_buffer(m+1); u.GetWindowTextW(c,b2,m+1)
                if b2.value=="확인": kids.append(c)
                return True
            u.EnumChildWindows(h,cb2,0)
            for c in kids: u.SendMessageW(c,0x00F5,0,0); print("  [clicker] 템플릿 대화상자 확인 클릭")
        return True
    while not stop_evt.is_set():
        u.EnumWindows(cb,0); time.sleep(0.5)
evt=threading.Event(); th=threading.Thread(target=dialog_clicker,args=(evt,),daemon=True); th.start()
already=[dd for dd in (pv(app,"GetDocuments") or []) if dd.GetTitle.startswith("B4b_KE002") and dd.GetType==2]
if already:
    d=already[0]; app.ActivateDoc3(d.GetTitle,False,0,I4()); evt.set(); print("reuse open import asm")
else:
    imp=app.GetImportFileData(STEP)
    e=I4(); t0=time.time(); d=app.LoadFile4(STEP,"r",imp,e); evt.set()
    print("LoadFile4",d is not None,"err",e.value,f"{time.time()-t0:.0f}s")
d=app.ActiveDoc; title=d.GetTitle; print("imported:",title,d.GetType)
assert title.startswith("B4b_KE002") and d.GetType==2, "expected imported assembly"
cm=d.ConfigurationManager; kids=[(c.Name2,os.path.basename(c.GetPathName)) for c in pv(cm.ActiveConfiguration.GetRootComponent3(True),"GetChildren")]
print("children",len(kids)); [print("  ",k) for k in kids]
# ---- 어셈블리 → 파트 저장 (전 컴포넌트)
ext=d.Extension
opt=None
for args in ((1,),(0,),()):
    try: opt=ext.GetAdvancedSaveAsOptions(*args); print("GetAdvancedSaveAsOptions",args,"->",opt is not None); break
    except Exception as ex: print("  GetAdvancedSaveAsOptions",args,"exc",ex)
assert opt is not None
opt.GeometryToSave=1   # swSaveAsmAsPart_AllComponents
try: opt.PreserveGeometryReferences=False
except Exception as ex: print("  PreserveGeometryReferences exc",ex)
e=I4(); w=I4(); ok=ext.SaveAs3(OUT,0,1,NOD,opt,e,w); print("SaveAs3 part",ok,"err",e.value,"warn",w.value,"exists",os.path.exists(OUT))
assert ok and os.path.exists(OUT)
# 임포트 어셈블리·자식 닫기(저장 안 함)
app.CloseDoc(title)
for n,p in kids:
    for dd in list(pv(app,"GetDocuments") or []):
        if os.path.basename(dd.GetPathName)==p: app.CloseDoc(dd.GetTitle)
print("closed import asm + children; stray files in Z?",[f for f in os.listdir(Z) if f.startswith(("KE00","____"))])
# ---- 파트 열어 조사
d=open_doc(app,OUT,1); app.ActivateDoc3(OUT,False,0,I4()); d=app.ActiveDoc; print("part",d.GetTitle,d.GetType)
bs=list(pv(d,"GetBodies2",0,True) or []); bx=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]
print("bodies",len(bs),"box",bx,"dims",[round(bx[3]-bx[0],1),round(bx[4]-bx[1],1),round(bx[5]-bx[2],1)])
vol=sum(pv(b,"GetMassProperties",0)[3]*1e9 for b in bs); print("vol",round(vol))
cyl=[]; pl=[]
for b in bs:
    for fc in b.GetFaces():
        s=fc.GetSurface; fb=[round(v*1000,1) for v in fc.GetBox]
        if s.IsCylinder:
            p=s.CylinderParams; cyl.append((round(p[6]*1000,2),[round(p[3],3),round(p[4],3),round(p[5],3)],fb))
        elif s.IsPlane:
            pl.append((round(fc.GetArea*1e6),[round(v,3) for v in pv(fc,"Normal")],fb))
small=[c for c in cyl if c[0]<=3.2]
print("small-cyl axis groups",collections.Counter(tuple(abs(a) for a in c[1]) for c in small).most_common(5))
for c in sorted(small,key=lambda c:(c[1],c[2]))[:24]: print("  r",c[0],"ax",c[1],"box",c[2])
print("big cyl:"); [print("  r",c[0],"ax",c[1],"box",c[2]) for c in sorted([c for c in cyl if c[0]>3.2],key=lambda c:-c[0])[:10]]
pl.sort(key=lambda x:-x[0]); print("largest planes:"); [print("  A",p[0],"n",p[1],"box",p[2]) for p in pl[:8]]
json.dump({"box":bx,"vol":vol,"bodies":len(bs),"kids":kids,"small":small,"big":sorted(cyl,key=lambda c:-c[0])[:20],"planes":pl[:20]},open(os.path.join(VER,"ke002_import_0910.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set(); print("stage1 done (part saved as",os.path.basename(OUT),", left open)")
