# MISUMI 경첩 C-HHSN65A · Takigen 걸쇠 C-1170-2S STEP → Z:\ 파트 저장 + 면 정보(리프 평면·핀 원통) 출력
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from swconn import *
from swpv import pv
stop=watchdog(); app=connect()
T=r"<HOME>\AppData\Local\Temp\claude\C--Users-<USER>-Documents-solidworks\c1c4571f-d1a7-451b-bd77-eecec8eea995\scratchpad\misumi_step"
JOBS=[(os.path.join(T,"C-HHSN65A.stp"),"C-HHSN65A_hinge.SLDPRT",{"TITLE":"HINGE (MISUMI C-HHSN65A)","SPEC":"MISUMI C-HHSN65A 평경첩 SUS304 74.5x50x8.8(구매사양 TK-20)","Material":"STS304","QT'Y":"2","DATE":"2026-09-08","REMARK":"주입구 뚜껑 S30008 경첩. 원 STEP: P282-제작정보/C-HHSN65A_STEP.zip (MISUMI 2026-08-24)"}),
      (os.path.join(T,"C-1170-2S_STEP_AP203AP214","C-1170-2S_214.STEP"),"C-1170-2S_latch.SLDPRT",{"TITLE":"LATCH (Takigen C-1170-2S)","SPEC":"Takigen C-1170-2S 각버클 분리잠금걸쇠 SUS304 70x39x22(구매사양 TK-21)","Material":"STS304","QT'Y":"1","DATE":"2026-09-08","REMARK":"주입구 뚜껑 압착·잠금 겸 손잡이. 원 STEP: P282-제작정보/C-1170-2S_STEP_AP203AP214.zip"})]
rep={}
for step,name,props in JOBS:
    out=os.path.join(Z,name)
    if not os.path.exists(out):
        imp=app.GetImportFileData(step)
        try: imp.ImportSurfaceBodies=False
        except Exception: pass
        e=I4(); d=app.LoadFile4(step,"r",imp,e); print("import",os.path.basename(step),"->",d.GetTitle if d else None,"err",e.value)
        if d is None: raise SystemExit("import failed "+step)
        title=d.GetTitle
        e=I4(); wn=I4(); ok=d.Extension.SaveAs(out,0,1,NOD,e,wn); print("  saved",ok,name,e.value,wn.value,"(from",title,")")
        if title.upper().endswith(".SLDASM"): app.CloseDoc(title)   # 내가 만든 임포트 어셈블리 창만 닫음
    d=app.GetOpenDocumentByName(out)
    if d is None: d=open_doc(app,out,1)
    if d.GetTitle.upper().endswith(".SLDASM"): raise SystemExit("still assembly: "+name)
    cpm=d.Extension.CustomPropertyManager("")
    for k,v in props.items(): cpm.Add3(k,30,v,1)
    try: d.SetMaterialPropertyName2("","이텍","STS 304")
    except Exception: pass
    d.EditRebuild3
    b=[round(v*1000,2) for v in pv(d,"GetPartBox",True)]; bodies=pv(d,"GetBodies2",0,True) or []
    faces=[]
    for bd in bodies:
        for f in bd.GetFaces():
            s=f.GetSurface; fb=[round(v*1000,1) for v in f.GetBox]; A=f.GetArea*1e6
            if s.IsPlane and A>150:
                pp=s.PlaneParams; faces.append(("pln",[round(v,2) for v in pp[0:3]],round(A),fb))
            elif s.IsCylinder and A>60:
                cp=s.CylinderParams; faces.append(("cyl r%.2f ax(%.1f,%.1f,%.1f)"%(cp[6]*1000,cp[3],cp[4],cp[5]),None,round(A),fb))
    faces.sort(key=lambda x:-x[2])
    print(name,"bbox",b,"size",[round(b[i+3]-b[i],2) for i in range(3)],"bodies",len(bodies))
    for f in faces[:14]: print("   ",f)
    rep[name]={"bbox":b,"faces":faces[:30]}
e=I4(); w_=I4()
for step,name,props in JOBS:
    dd=app.GetOpenDocumentByName(os.path.join(Z,name)); print("save props",name,dd.Save3(1,e,w_) if dd else None)
json.dump(rep,open(os.path.join(VER,"tank_recheck_2026-09-08","misumi_hw_import.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1,default=str)
stop.set()
