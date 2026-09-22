# 2026-09-16: T볼트 호스 클램프 TRUSCO TTHC-1942 근사 파트(MISUMI 규격표: 외경 38~42, 밴드 19×0.7, 육각너트 11, SUS304, CAD 없음)
#  + 염수주입라인.SLDASM 배치 2개: 고정측 니플 H16d-1 바브 중앙(z −181, 고정) / 이동측 니플 H16d-2 바브 중앙(기준면 메이트, ZP+45.8)
import os, sys, math, pythoncom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop = watchdog(); app = connect()
NAME = "F4_hoseclamp_TRUSCO_TTHC-1942_approx"; P = os.path.join(Z, NAME + ".SLDPRT"); mm = lambda v: v/1000.0
def sel_plane_doc(d, names):
    for nm in names:
        if d.Extension.SelectByID2(nm, "PLANE", 0, 0, 0, False, 0, NOD, 0): return nm
    raise RuntimeError("no plane")
if not os.path.exists(P):
    tmpl = app.GetUserPreferenceStringValue(8); d = app.NewDocument(tmpl, 0, 0, 0); sm = d.SketchManager
    # ring: annulus on 정면(XY), extrude ±9.5 (band 19) along Z
    sel_plane_doc(d, ("정면", "Front Plane")); sm.InsertSketch(True); sm.AddToDB = True
    sm.CreateCircleByRadius(0, 0, 0, mm(20.5)); sm.CreateCircleByRadius(0, 0, 0, mm(21.2)); sm.AddToDB = False; sm.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2("스케치1", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
    f1 = d.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, mm(9.5), mm(9.5), False, False, False, False, 0, 0, False, False, False, False, True, True, True, 0, 0, False)
    print("ring", f1 is not None)
    # T-bolt housing block (approx): x 21.2~33, y ±6.5, z ±9.5 — sketch on 정면 rectangle, extrude ±9.5, merge
    sel_plane_doc(d, ("정면", "Front Plane")); sm.InsertSketch(True); sm.AddToDB = True
    sm.CreateCornerRectangle(mm(21.0), mm(-6.5), 0, mm(33.0), mm(6.5), 0); sm.AddToDB = False; sm.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2("스케치2", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
    f2 = d.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, mm(9.5), mm(9.5), False, False, False, False, 0, 0, False, False, False, False, True, True, True, 0, 0, False)
    print("block", f2 is not None); d.EditRebuild3
    b = d.GetPartBox(True); print("bbox mm", [round(v*1000, 2) for v in b]); assert abs(b[5]*1000-9.5) < 0.1
    try:
        import glob; lib = glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\*\sldmaterials\solidworks materials.sldmat")[0]; d.SetMaterialPropertyName2("", lib, "AISI 304")
    except Exception as ex: print("mat err", ex)
    cpm = d.Extension.CustomPropertyManager("")
    for k, v in (("TITLE", "HOSE CLAMP T-BOLT (TRUSCO TTHC-1942)"), ("SPEC", "TRUSCO T볼트 호스 클램프 올스테인리스 TTHC-1942: 호스 외경 38~42, 밴드 19×0.7, 육각너트 11, 체결토크 15, SUS304 (MISUMI 221006433416 계열, 발주코드 856-6819)"), ("REMARK", "근사형상(밴드 링 ID41×19×0.7 + T볼트 하우징 블록). CAD 없음(MISUMI 페이지 CAD 항목 없음). 야성 HSPF-032(OD41) ↔ 온다 SFHN-3234 바브 체결 2곳"), ("MATERIAL", "SUS304"), ("DATE", "2026-09-16"), ("QT'Y", "2")): cpm.Add3(k, 30, v, 1)
    e = I4(); wn = I4(); ok = d.Extension.SaveAs(P, 0, 1, NOD, e, wn); print("saved", ok, e.value); app.CloseDoc(d.GetTitle)
else: print("exists", P)
pd = app.GetOpenDocumentByName(P) or open_doc(app, P, 1)
e = I4(); app.ActivateDoc3(ASM, False, 0, e); a = app.ActiveDoc; assert a.GetTitle.startswith("염수주입라인"), a.GetTitle
a.ShowConfiguration2("상승"); a.EditRebuild3
def comps(): return {c.Name2: c for c in a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
def set_T(c, R, t):
    arr = list(R[0])+list(R[1])+list(R[2])+[t[0]/1000, t[1]/1000, t[2]/1000, 1.0, 0, 0, 0]
    xf = c.Transform2; xf.ArrayData = VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, arr); c.Transform2 = xf
I3 = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
def mates_iter():
    f = pv(a, "FirstFeature")
    while f is not None:
        if pv(f, "GetTypeName2") == "MateGroup":
            sf = f.GetFirstSubFeature
            while sf is not None: yield sf; sf = sf.GetNextSubFeature
        f = pv(f, "GetNextFeature")
KO = ("우측면", "윗면", "정면"); EN = ("Right Plane", "Top Plane", "Front Plane")
def sel_plane(comp, axis, append):
    for nm in (KO[axis], EN[axis]):
        if a.Extension.SelectByID2(f"{nm}@{comp}@염수주입라인", "PLANE", 0, 0, 0, append, 1, NOD, 0): return True
    return False
def add_mate(mtype, align, flip=False, dist=0.0, name=None):
    err = I4(); m = a.AddMate5(mtype, align, flip, dist, 0.0, 0.0, 0, 0, 0, 0, 0, False, False, 0, err); a.ClearSelection2(True)
    f = None
    if m is not None:
        f = list(mates_iter())[-1]
        if name:
            try: f.Name = name
            except Exception as ex: print("  rename exc", ex)
    return m is not None, err.value, f
def del_feat(f):
    a.ClearSelection2(True); f.Select2(False, 0); a.Extension.DeleteSelection2(0); a.ClearSelection2(True)
cc = comps(); existing = [n for n in cc if n.startswith(NAME)]; print("existing clamps", existing)
NIP2 = [n for n in cc if n.startswith("H16d") and n.endswith("-2")][0]
if len(existing) < 1:
    c1 = a.AddComponent5(P, 0, "", False, "", 0, 0, 0); assert c1
    set_T(c1, I3, (0.0, 0.0, -181.0)); a.ClearSelection2(True); c1.Select4(False, NOD, False); a.FixComponent(); a.ClearSelection2(True)
    print("clamp-1 fixed at z -181")
cc = comps(); existing = sorted(n for n in cc if n.startswith(NAME))
if len(existing) < 2:
    c2 = a.AddComponent5(P, 0, "", False, "", 0, 0, 0); assert c2
    set_T(c2, I3, (0.0, 0.0, -379.2)); a.EditRebuild3
    n2 = c2.Name2; print("clamp-2 added", n2)
    # mates: 우측면(x) coincident, 윗면(y) coincident (closest), 정면(z) distance 60.8 with flip trial
    for axis in (0, 1):
        a.ClearSelection2(True); assert sel_plane(n2, axis, False) and sel_plane(NIP2, axis, True)
        ok, err, f = add_mate(0, 2, False, 0.0, f"클램프2_{KO[axis]}_일치"); print("  mate", KO[axis], ok, err)
    done = False
    for flip in (False, True):
        a.ClearSelection2(True); assert sel_plane(n2, 2, False) and sel_plane(NIP2, 2, True)
        ok, err, f = add_mate(5, 2, flip, 0.0608, "클램프2_정면_거리60.8"); a.EditRebuild3
        t = xform(comps()[n2])["t_mm"]; print("  dist mate flip", flip, ok, err, "-> t", t)
        if abs(t[2] + 379.2) < 0.05: done = True; break
        if f is not None: del_feat(f)
    assert done, "clamp-2 position not achieved"
a.EditRebuild3
for cfg, zexp in (("상승", -379.2), ("하강", -464.2)):
    a.ShowConfiguration2(cfg); a.EditRebuild3; cc = comps()
    for n in sorted(x for x in cc if x.startswith(NAME)): print(f"[{cfg}]", n, "t", xform(cc[n])["t_mm"], "box", box(cc[n]))
a.ShowConfiguration2("상승"); a.EditRebuild3
idm = a.InterferenceDetectionManager; a.ClearSelection2(True)
for n in comps(): comps()[n].Select4(True, NOD, False)
idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False
res = idm.GetInterferences; inter = [(round(it.Volume*1e9, 1), [x.Name2 for x in it.Components]) for it in (res or []) if any(NAME in x.Name2 for x in it.Components)]
idm.Done; a.ClearSelection2(True); print("clamp interferences:", inter)
import pythoncom as pc
fe = VARIANT(pc.VT_BYREF|pc.VT_VARIANT, None); co = VARIANT(pc.VT_BYREF|pc.VT_VARIANT, None); wa = VARIANT(pc.VT_BYREF|pc.VT_VARIANT, None)
a.Extension.GetWhatsWrong(fe, co, wa); print("whatswrong:", [(f.Name, c) for f, c in zip(fe.value or [], co.value or [])])
app.CloseDoc(NAME + ".SLDPRT"); print("line dirty", a.GetSaveFlag); stop.set()
