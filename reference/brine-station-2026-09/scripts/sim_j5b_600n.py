# SOLIDWORKS Simulation 재실행 (2026-09-09, J5b 형상 + LA25 600 N 확정).
#  "1_UP_static": config "1.상승했을때(해석)" — 구조부품만 (J1c 고정판 + J8b 브래킷). 고정판 상면 고정, 브래킷 핀홀에 LA25 최대추력 600 N (+Z, 노즐 걸림 시 반력) + 중력.
#  "2_DN_static": config "2.하강했을때(해석)" — 구조부품만 (J5d 이동판 t8 + J9b 클레비스). 소켓 구멍 고정(노즐이 로봇에 걸린 경우), 부시 구멍 반경방향 구속(가이드봉), 클레비스 핀홀에 600 N (−Z) + 중력.
# 가정: 재질 AISI 304, 용접부 = 접촉면 본딩. sim_j3.py에서 부품명·하중만 바꿈. 어셈블리는 저장하지 않는다.
import os, sys, json, glob, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
FORCE_N = 600.0
app=connect()
asm=app.GetOpenDocumentByName(ASM)
if asm is None: asm=open_doc(app,ASM,2)
app.ActivateDoc3(ASM,False,0,I4()); asm=app.ActiveDoc
name=asm.GetTitle.replace(".SLDASM",""); cm=asm.ConfigurationManager
def root(): return cm.ActiveConfiguration.GetRootComponent3(True)
def comps(): return list(root().GetChildren)
def sel(names):
    asm.ClearSelection2(True)
    for n in names: asm.Extension.SelectByID2(n+"@"+name,"COMPONENT",0,0,0,True,0,NOD,0)
# 09-09 실측 부품명 (dump)
FIXED_KEEP=["J1c_fixed_plate_185x580_t10-1","J8b_bent_U_bracket_t6_136x194x60-1"]
DN_KEEP=["J5d_moving_plate_220x540_t8-2","J9b_rod_clevis_t6_44x40x60-2"]
cw=None
try: cw=app.GetAddInObject("SldWorks.Simulation")
except Exception: pass
if cw is None:
    app.LoadAddIn(glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\Simulation\cosworks.dll")[0]); cw=app.GetAddInObject("SldWorks.Simulation")
cwa=cw.COSMOSWORKS
MATLIB=glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\*\sldmaterials\solidworks materials.sldmat")
MATLIB=MATLIB[0] if MATLIB else r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\korean\sldmaterials\solidworks materials.sldmat"
print("material lib:",MATLIB)
def disp_array(objs): return VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_VARIANT,objs)
def call(o,n):
    a=getattr(o,n); return a() if callable(a) else a
B_=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_BOOL,False); D_=lambda: VARIANT(pythoncom.VT_BYREF|pythoncom.VT_R8,0.0)
def refv(obj): return NOD if obj is None else VARIANT(pythoncom.VT_DISPATCH,obj)
def faces_of(comp):
    b=comp.GetBody
    return list(b.GetFaces()) if b else []
def cyl_faces(comp,r,tol=0.3):
    out=[]
    for f in faces_of(comp):
        s=f.GetSurface
        if s.IsCylinder:
            cp=s.CylinderParams; rad=cp[6]*1000
            if abs(rad-r)<tol: out.append(f)
    return out
def plane_faces(comp,normal,z,tol=0.5):
    out=[]
    for f in faces_of(comp):
        s=f.GetSurface
        if s.IsPlane:
            pp=s.PlaneParams; n=pp[0:3]; p=[v*1000 for v in pp[3:6]]
            if all(abs(n[i]-normal[i])<1e-3 for i in range(3)) or all(abs(n[i]+normal[i])<1e-3 for i in range(3)):
                if abs(p[2]-z)<tol and f.GetArea>0.005: out.append(f)
    return out
def ensure_config(cfg,keep_names):
    if cfg not in list(asm.GetConfigurationNames):
        c=asm.AddConfiguration3(cfg,"Simulation 해석용 — 구조부품만 활성","",0)
        print("config created:",cfg,c is not None)
    asm.ShowConfiguration2(cfg); asm.EditRebuild3
    assert cm.ActiveConfiguration.Name==cfg, cm.ActiveConfiguration.Name
    keep=[c for c in comps() if c.Name2 in keep_names]; rest=[c for c in comps() if c.Name2 not in keep_names]
    sel([c.Name2 for c in keep]); asm.EditUnsuppress2; asm.ClearSelection2(True)
    sel([c.Name2 for c in rest]); asm.EditSuppress2; asm.ClearSelection2(True); asm.EditRebuild3
    st={c.Name2:c.GetSuppression2 for c in comps()}
    ok=all(st.get(n)==2 for n in keep_names) and all(st[n]==0 for n in st if n not in keep_names)
    print(f"  config {cfg}: active {[n for n in st if st[n]==2]} ok={ok}")
    assert ok, "suppression state mismatch"
    return {n:c for n,c in ((c.Name2,c) for c in comps()) if n in keep_names}
def new_study(ascii_name):
    doc=cwa.ActiveDoc; sm=doc.StudyManager
    for i in range(sm.StudyCount):
        st=sm.GetStudy(i)
        if st.Name==ascii_name: print("  study exists:",ascii_name,"— reuse"); return st,doc
    e=I4(); s=sm.CreateNewStudy3(ascii_name,0,0,e)
    print("  study created:",ascii_name,"err",e.value,"config",s.ConfigurationName if s else None)
    return s,doc
def set_materials(study):
    solm=study.SolidManager
    for i in range(solm.ComponentCount):
        e=I4(); c=solm.GetComponentAt(i,e)
        for k in range(c.SolidBodyCount):
            e2=I4(); b=c.GetSolidBodyAt(k,e2); r=b.SetLibraryMaterial2(MATLIB,"AISI 304")
            print("   material",c.ComponentName,b.SolidBodyName,"AISI 304 ->",r)
def add_fixed(study,faces,label):
    lrm=study.LoadsAndRestraintsManager; e=I4()
    r=lrm.AddRestraint(0,disp_array(faces),NOD,e)
    print(f"   restraint fixed [{label}] faces={len(faces)} err={e.value} ok={r is not None}")
    return r
def add_slider_xy(study,faces,label):
    lrm=study.LoadsAndRestraintsManager; e=I4()
    r=lrm.AddRestraint(7,disp_array(faces),NOD,e)
    if r is not None:
        call(r,"RestraintBeginEdit"); r.Unit=0
        r.SetTranslationComponentsValues(True,False,False,0.0,0.0,0.0)
        call(r,"RestraintEndEdit")
    print(f"   restraint radial-fixed [{label}] faces={len(faces)} err={e.value} ok={r is not None}")
    return r
def add_force_z(study,faces,refplane,value_N,label):
    lrm=study.LoadsAndRestraintsManager; e=I4()
    f=lrm.AddForce2(0,0,disp_array(faces),refv(refplane),e)
    if f is not None:
        call(f,"ForceBeginEdit"); f.Unit=0
        f.SetForceComponentValues(False,False,True,0.0,0.0,float(value_N))
        call(f,"ForceEndEdit")
        b1,b2,b3,d1,d2,d3=B_(),B_(),B_(),D_(),D_(),D_(); f.GetForceComponentValues(b1,b2,b3,d1,d2,d3); print("     readback force:",b3.value,d3.value,"unit",f.Unit)
    print(f"   force {value_N:+.0f} N along Z [{label}] faces={len(faces)} err={e.value} ok={f is not None}")
    return f
def add_gravity(study,refplane):
    lrm=study.LoadsAndRestraintsManager; e=I4()
    g=lrm.AddGravity(refv(refplane),e)
    if g is not None:
        call(g,"GravityBeginEdit"); g.Unit=0; g.SetGravitationalAcclerationValues(0.0,0.0,-9.81); call(g,"GravityEndEdit")
        d1,d2,d3=D_(),D_(),D_(); g.GetGravitationalAcclerationValues(d1,d2,d3); print("     readback gravity:",d1.value,d2.value,d3.value)
    print("   gravity err",e.value,"ok",g is not None)
    return g
def mesh_and_run(study):
    m=study.Mesh; m.Quality=1
    size=0.5
    r=study.CreateMesh(1,size,size/20.0); print("   mesh ->",r,"nodes",m.NodeCount,"elems",m.ElementCount,"failed",m.IsMeshFailed)
    r=study.RunAnalysis; print("   run ->",r,"(0=success)")
    return r==0
def results(study,label):
    res=study.Results; out={}
    e=I4()
    try: v=res.GetMinMaxStress(9,0,0,NOD,3,e)
    except Exception as ex: v=None; print("   stress err",ex)
    print(f"   [{label}] vonMises minmax (N/mm^2):",v,"err",e.value); out["von_raw_u3"]=list(v) if v else None
    e=I4()
    try: d=res.GetMinMaxDisplacement(3,0,NOD,0,e)
    except Exception as ex: d=None; print("   disp err",ex)
    print(f"   [{label}] URES minmax (mm):",d,"err",e.value); out["ures_raw_u0"]=list(d) if d else None
    try:
        m=study.Mesh; emax=int(out["von_raw_u3"][2]); nmax=int(out["ures_raw_u0"][2])
        x,y,z=D_(),D_(),D_(); m.GetElementLocation(emax,x,y,z); out["von_max_at_mm"]=[round(x.value*1000,1),round(y.value*1000,1),round(z.value*1000,1)]
        x,y,z=D_(),D_(),D_(); m.GetNodeLocation(nmax,x,y,z); out["ures_max_at_mm"]=[round(x.value*1000,1),round(y.value*1000,1),round(z.value*1000,1)]
        out["mesh"]={"nodes":m.NodeCount,"elems":m.ElementCount}
        print(f"   [{label}] max VON at {out['von_max_at_mm']} ; max URES at {out['ures_max_at_mm']} ; mesh {out['mesh']}")
    except Exception as ex: print("   hotspot err",ex)
    e=I4()
    try: fos=res.GetMinMaxFactorOfSafety(True,NOD,0,0,e)
    except Exception as ex: fos=None; print("   fos err",ex)
    print(f"   [{label}] FOS minmax:",fos,"err",e.value); out["fos_raw"]=list(fos) if fos else None
    return out
def plane_ref():
    asm.ClearSelection2(True)
    ok=asm.Extension.SelectByID2("정면","PLANE",0,0,0,False,0,NOD,0) or asm.Extension.SelectByID2("Front Plane","PLANE",0,0,0,False,0,NOD,0)
    p=asm.SelectionManager.GetSelectedObject6(1,-1); asm.ClearSelection2(True); print("  ref plane 정면:",ok,p is not None); return p
report={"force_N":FORCE_N,"date":"2026-09-09","parts":{"up":FIXED_KEEP,"dn":DN_KEEP}}
_sm=cwa.ActiveDoc.StudyManager
for _i in range(_sm.StudyCount-1,-1,-1):
    _n=_sm.GetStudy(_i).Name
    if _n in ("1_UP_static","2_DN_static","tmp_up","tmp_dn"): print("  delete old study",_n,_sm.DeleteStudy(_n))
# ---- Study 1: 상승, 고정판 J1c + 브래킷 J8b
c1=ensure_config("1.상승했을때(해석)",set(FIXED_KEEP))
plate=c1[FIXED_KEEP[0]]; brk=c1[FIXED_KEEP[1]]
top_faces=plane_faces(plate,(0,0,1),0.0); pin_faces=cyl_faces(brk,5.25)
print("  study1 faces: plate top",len(top_faces),"bracket pin holes",len(pin_faces))
assert top_faces and pin_faces
s1,doc=new_study("1_UP_static"); ref=plane_ref()
set_materials(s1)
add_fixed(s1,top_faces,"고정판 상면(호퍼 플랜지 볼트면)")
add_force_z(s1,pin_faces,ref,+FORCE_N,"브래킷 핀홀 LA25 600 N 상향(노즐 걸림 반력)")
add_gravity(s1,ref)
if mesh_and_run(s1): report["1_UP_static"]=results(s1,"1.상승")
# ---- Study 2: 하강, 이동판 J5d + 클레비스 J9b
c2=ensure_config("2.하강했을때(해석)",set(DN_KEEP))
mplate=c2[DN_KEEP[0]]; clv=c2[DN_KEEP[1]]
sock=cyl_faces(mplate,17.0); bush=cyl_faces(mplate,14.25); clv_pin=cyl_faces(clv,5.25)
print("  study2 faces: socket hole",len(sock),"bushing holes",len(bush),"clevis pin holes",len(clv_pin))
assert sock and bush and clv_pin
s2,doc=new_study("2_DN_static"); ref=plane_ref()
set_materials(s2)
add_fixed(s2,sock,"소켓 구멍(노즐이 로봇에 걸림)")
add_slider_xy(s2,bush,"부시 구멍 반경방향 구속(가이드봉)")
add_force_z(s2,clv_pin,ref,-FORCE_N,"클레비스 핀홀 LA25 600 N 하향")
add_gravity(s2,ref)
if mesh_and_run(s2): report["2_DN_static"]=results(s2,"2.하강")
asm.ShowConfiguration2("상승"); asm.EditRebuild3
out=os.path.join(VER,"J5b_sim_results_600N.json")
json.dump(report,open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("saved",out,"; assembly NOT saved")
