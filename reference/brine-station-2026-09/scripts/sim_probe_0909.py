# 2026-09-09: 1_UP_static / 2_DN_static (600 N, J1c+J8b / J5d t8+J9b) 재실행 후 영역별 von Mises 판독.
import os, json, math, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
app=connect(); asm=app.GetOpenDocumentByName(ASM) or open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
cm=asm.ConfigurationManager
cw=app.GetAddInObject("SldWorks.Simulation"); cwa=cw.COSMOSWORKS; sm=cwa.ActiveDoc.StudyManager
def call(o,n):
    a=getattr(o,n); return a() if callable(a) else a
def va(objs): return VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_VARIANT,objs)
out={}
for name in ("2_DN_static","1_UP_static"):
    s=[sm.GetStudy(i) for i in range(sm.StudyCount) if sm.GetStudy(i).Name==name][0]
    asm.ShowConfiguration2(s.ConfigurationName); asm.EditRebuild3
    mr=s.CreateMesh(1,0.5,0.025); r=call(s,"RunAnalysis"); print("==",name,"mesh",mr,"rerun ->",r)
    res=s.Results
    root=cm.ActiveConfiguration.GetRootComponent3(True); comps={c.Name2:c for c in root.GetChildren if c.GetSuppression2==2}
    def faces(comp): return list(comp.GetBody.GetFaces())
    def cyl(comp,rad,tol=0.3):
        o=[]
        for f in faces(comp):
            su=f.GetSurface
            if su.IsCylinder and abs(su.CylinderParams[6]*1000-rad)<tol: o.append(f)
        return o
    def planes(comp,zc):
        o=[]
        for f in faces(comp):
            su=f.GetSurface
            if su.IsPlane and abs(abs(su.PlaneParams[2])-1)<1e-3 and abs(su.PlaneParams[5]*1000-zc)<0.5: o.append(f)
        return o
    if name=="2_DN_static":
        pl=[c for n,c in comps.items() if n.startswith("J5d_")][0]; cl=[c for n,c in comps.items() if n.startswith("J9b_")][0]
        regions={"이동판 소켓구멍(고정면)":cyl(pl,17.0),"이동판 부시구멍":cyl(pl,14.25),"이동판 M4탭":cyl(pl,1.65),"이동판 상면":planes(pl,0.0),"이동판 하면":planes(pl,-8.0),
                 "클레비스 핀홀":cyl(cl,5.25),"클레비스 전체면":faces(cl)}
    else:
        pl=[c for n,c in comps.items() if n.startswith("J1c_")][0]; br=[c for n,c in comps.items() if n.startswith("J8b_")][0]
        regions={"고정판 상면(고정)":planes(pl,0.0),"고정판 하면":planes(pl,-10.0),"고정판 볼트구멍":cyl(pl,4.5),"고정판 가이드봉탭":cyl(pl,7.0),"브래킷 핀홀":cyl(br,5.25),"브래킷 전체면":faces(br)}
    out[name]={}
    for lab,fs in regions.items():
        if not fs: print("  ",lab,"faces 0"); continue
        e=I4()
        try:
            v=res.GetStressForEntities2(True,9,0,NOD,va(fs),3,e)
            vals=list(v) if v else []
            if v and len(v)>=2 and abs(v[0]-round(v[0]))<1e-9 and v[0]>1: vals=[v[i] for i in range(1,len(v),2)]
            mx=max(vals) if vals else None
            print(f"   {lab:22s} faces={len(fs):3d} nodes={len(vals):6d} max VON={mx:.1f} MPa err={e.value}")
            out[name][lab]={"faces":len(fs),"max_von_MPa":mx}
        except Exception as ex: print("   ",lab,"ERR",ex)
    e=I4(); g=res.GetMinMaxStress(9,0,0,NOD,3,e); print("   global max VON",g[3]); out[name]["global_max_von_MPa"]=g[3]
    e=I4(); d=res.GetMinMaxDisplacement(3,0,NOD,0,e); out[name]["global_max_ures_mm"]=d[3]; print("   global max URES",d[3])
asm.ShowConfiguration2("상승"); asm.EditRebuild3
json.dump(out,open(os.path.join(VER,"J5b_sim_probe_600N.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("saved J5b_sim_probe_600N.json ; assembly NOT saved")
