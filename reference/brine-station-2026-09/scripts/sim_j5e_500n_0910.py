# 2026-09-10: SOLIDWORKS Simulation 재실행 — 현 형상(J1c+J8e / J5e t8+J9d PL6 h34), TA2 코드 H 정격 500 N. sim_j5b_600n.py에서 부품명·하중·구멍 반경만 바꿈.
#  1_UP_static : "1.상승했을때(해석)" — J1c 고정판(상면 고정) + J8e 후단 러그(핀홀 Ø8에 +Z 500 N) + 중력
#  2_DN_static : "2.하강했을때(해석)" — J5e 이동판(소켓 구멍 Ø32 고정 = 노즐 걸림, 부시 구멍 Ø28.5 반경 구속) + J9d 러그(핀홀 Ø8에 −Z 500 N) + 중력
#  가정: AISI 304, 용접 = 접촉면 본딩. 어셈블리는 저장하지 않는다(스터디는 메모리).
import os, sys, json, glob, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
FORCE_N=500.0
stop=watchdog(); app=connect()
asm=app.GetOpenDocumentByName(ASM) or open_doc(app,ASM,2); app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return list(root().GetChildren)
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
FIXED_KEEP=["J1c_fixed_plate_185x580_t10-2","J8e_lug_PL6_40x26-1"]
DN_KEEP=["J5e_moving_plate_180x540_t8-2","J9d_lug_PL6_40x31-2"]
cw=None
try: cw=app.GetAddInObject("SldWorks.Simulation")
except Exception: pass
if cw is None:
    app.LoadAddIn(glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\Simulation\cosworks.dll")[0]); cw=app.GetAddInObject("SldWorks.Simulation")
cwa=cw.COSMOSWORKS
MATLIB=glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\*\sldmaterials\solidworks materials.sldmat"); MATLIB=MATLIB[0]
def disp_array(objs): return VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_VARIANT,objs)
def call(o,n):
    a=getattr(o,n); return a() if callable(a) else a
B_=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BOOL,False); D_=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_R8,0.0)
def refv(obj): return NOD if obj is None else VARIANT(pythoncom.VT_DISPATCH,obj)
def faces_of(comp):
    b=comp.GetBody; return list(b.GetFaces()) if b else []
def cyl_faces(comp,r,tol=0.3):
    out=[]
    for f in faces_of(comp):
        s=f.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000-r)<tol: out.append(f)
    return out
def plane_faces(comp,normal,z,tol=0.5):
    out=[]
    for f in faces_of(comp):
        s=f.GetSurface
        if s.IsPlane:
            pp=s.PlaneParams; n=pp[0:3]; p=[v*1000 for v in pp[3:6]]
            if (all(abs(n[i]-normal[i])<1e-3 for i in range(3)) or all(abs(n[i]+normal[i])<1e-3 for i in range(3))) and abs(p[2]-z)<tol and f.GetArea>0.005: out.append(f)
    return out
def ensure_config(cfg,keep_names):
    asm.ShowConfiguration2(cfg); asm.EditRebuild3; assert cm.ActiveConfiguration.Name==cfg
    keep=[c for c in comps() if c.Name2 in keep_names]; rest=[c for c in comps() if c.Name2 not in keep_names]
    assert len(keep)==len(keep_names), [c.Name2 for c in keep]
    sel([c.Name2 for c in keep]); asm.EditUnsuppress2; asm.ClearSelection2(True)
    sel([c.Name2 for c in rest]); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
    st={c.Name2:c.GetSuppression2 for c in comps()}
    ok=all(st.get(n)==2 for n in keep_names) and all(st[n]==0 for n in st if n not in keep_names)
    print(f"  config {cfg}: active {[n for n in st if st[n]==2]} ok={ok}"); assert ok
    return {c.Name2:c for c in comps() if c.Name2 in keep_names}
def new_study(nm):
    doc=cwa.ActiveDoc; sm=doc.StudyManager
    for i in range(sm.StudyCount):
        st=sm.GetStudy(i)
        if st.Name==nm: return st,doc
    e=I4(); s=sm.CreateNewStudy3(nm,0,0,e); print("  study created:",nm,"err",e.value,"config",s.ConfigurationName if s else None); return s,doc
def set_materials(study):
    solm=study.SolidManager
    for i in range(solm.ComponentCount):
        e=I4(); c=solm.GetComponentAt(i,e)
        for k in range(c.SolidBodyCount):
            e2=I4(); b=c.GetSolidBodyAt(k,e2); r=b.SetLibraryMaterial2(MATLIB,"AISI 304"); print("   material",c.ComponentName,b.SolidBodyName,"->",r)
def add_fixed(study,faces,label):
    e=I4(); r=study.LoadsAndRestraintsManager.AddRestraint(0,disp_array(faces),NOD,e); print(f"   fixed [{label}] faces={len(faces)} err={e.value} ok={r is not None}"); return r
def add_slider_xy(study,faces,label):
    e=I4(); r=study.LoadsAndRestraintsManager.AddRestraint(7,disp_array(faces),NOD,e)
    if r is not None:
        call(r,"RestraintBeginEdit"); r.Unit=0; r.SetTranslationComponentsValues(True,False,False,0.0,0.0,0.0); call(r,"RestraintEndEdit")
    print(f"   radial [{label}] faces={len(faces)} err={e.value} ok={r is not None}"); return r
def add_force_z(study,faces,refplane,value_N,label):
    e=I4(); f=study.LoadsAndRestraintsManager.AddForce2(0,0,disp_array(faces),refv(refplane),e)
    if f is not None:
        call(f,"ForceBeginEdit"); f.Unit=0; f.SetForceComponentValues(False,False,True,0.0,0.0,float(value_N)); call(f,"ForceEndEdit")
        b1,b2,b3,d1,d2,d3=B_(),B_(),B_(),D_(),D_(),D_(); f.GetForceComponentValues(b1,b2,b3,d1,d2,d3); print("     readback force:",b3.value,d3.value)
    print(f"   force {value_N:+.0f} N Z [{label}] faces={len(faces)} err={e.value} ok={f is not None}"); return f
def add_gravity(study,refplane):
    e=I4(); g=study.LoadsAndRestraintsManager.AddGravity(refv(refplane),e)
    if g is not None: call(g,"GravityBeginEdit"); g.Unit=0; g.SetGravitationalAcclerationValues(0.0,0.0,-9.81); call(g,"GravityEndEdit")
    print("   gravity err",e.value,"ok",g is not None); return g
def mesh_and_run(study):
    m=study.Mesh; m.Quality=1; size=0.5
    r=study.CreateMesh(1,size,size/20.0); print("   mesh ->",r,"nodes",m.NodeCount,"elems",m.ElementCount,"failed",m.IsMeshFailed)
    r=study.RunAnalysis; print("   run ->",r,"(0=success)"); return r==0
def results(study,label):
    res=study.Results; out={}
    e=I4(); v=res.GetMinMaxStress(9,0,0,NOD,3,e); out["von_MPa_minmax"]=list(v) if v else None; print(f"   [{label}] von Mises minmax:",v)
    e=I4(); d=res.GetMinMaxDisplacement(3,0,NOD,0,e); out["ures_mm_minmax"]=list(d) if d else None; print(f"   [{label}] URES minmax:",d)
    try:
        m=study.Mesh; emax=int(v[2]); nmax=int(d[2]); x,y,z=D_(),D_(),D_(); m.GetElementLocation(emax,x,y,z); out["von_max_at_mm"]=[round(x.value*1000,1),round(y.value*1000,1),round(z.value*1000,1)]
        x,y,z=D_(),D_(),D_(); m.GetNodeLocation(nmax,x,y,z); out["ures_max_at_mm"]=[round(x.value*1000,1),round(y.value*1000,1),round(z.value*1000,1)]; out["mesh"]={"nodes":m.NodeCount,"elems":m.ElementCount}
        print(f"   [{label}] max VON at {out['von_max_at_mm']} ; max URES at {out['ures_max_at_mm']} ; mesh {out['mesh']}")
    except Exception as ex: print("   hotspot err",ex)
    e=I4()
    try: fos=res.GetMinMaxFactorOfSafety(True,NOD,0,0,e); out["fos_minmax"]=list(fos) if fos else None; print(f"   [{label}] FOS:",fos)
    except Exception as ex: print("   fos err",ex)
    return out
def plane_ref():
    asm.ClearSelection2(True); ok=asm.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or asm.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    p=asm.SelectionManager.GetSelectedObject6(1,-1); asm.ClearSelection2(True); return p
report={"force_N":FORCE_N,"date":"2026-09-10","parts":{"up":FIXED_KEEP,"dn":DN_KEEP},"material":"AISI 304 (SW lib)","assumption":"용접=본딩, 고정판 상면 고정, 소켓 구멍 고정(노즐 걸림), 부시 구멍 반경 구속"}
_sm=cwa.ActiveDoc.StudyManager
for _i in range(_sm.StudyCount-1,-1,-1):
    _n=_sm.GetStudy(_i).Name
    if _n in ("1_UP_static","2_DN_static"): print("  delete old study",_n,_sm.DeleteStudy(_n))
c1=ensure_config("1.상승했을때(해석)",set(FIXED_KEEP)); plate=c1[FIXED_KEEP[0]]; lug=c1[FIXED_KEEP[1]]
top=plane_faces(plate,(0,0,1),0.0); pin=cyl_faces(lug,4.0); print("  study1 faces: plate top",len(top),"lug pin",len(pin)); assert top and pin
s1,doc=new_study("1_UP_static"); ref=plane_ref(); set_materials(s1)
add_fixed(s1,top,"고정판 상면(호퍼 립 용접면)"); add_force_z(s1,pin,ref,+FORCE_N,"J8e 핀홀 TA2 500 N 상향"); add_gravity(s1,ref)
if mesh_and_run(s1): report["1_UP_static"]=results(s1,"1.상승")
c2=ensure_config("2.하강했을때(해석)",set(DN_KEEP)); mplate=c2[DN_KEEP[0]]; lug2=c2[DN_KEEP[1]]
sock=cyl_faces(mplate,16.0); bush=cyl_faces(mplate,14.25); pin2=cyl_faces(lug2,4.0); print("  study2 faces: socket",len(sock),"bush",len(bush),"lug pin",len(pin2)); assert sock and bush and pin2
s2,doc=new_study("2_DN_static"); ref=plane_ref(); set_materials(s2)
add_fixed(s2,sock,"소켓 구멍 Ø32(노즐 걸림)"); add_slider_xy(s2,bush,"부시 구멍 반경 구속"); add_force_z(s2,pin2,ref,-FORCE_N,"J9d 핀홀 TA2 500 N 하향"); add_gravity(s2,ref)
if mesh_and_run(s2): report["2_DN_static"]=results(s2,"2.하강")
asm.ShowConfiguration2("상승"); asm.EditRebuild3
out=os.path.join(VER,"J5e_sim_results_500N.json"); json.dump(report,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1); print("saved",out,"; assembly NOT saved")
stop.set()
