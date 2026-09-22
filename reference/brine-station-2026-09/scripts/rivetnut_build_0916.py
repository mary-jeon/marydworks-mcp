# 2026-09-16: 리벳너트 POP RIVETS SPH-1240-3W 근사 파트 생성(미스미 치수표) + S10000MU0 보 구멍 8곳 배치(고정).
#  근거: kr.misumi-ec.com 221000765924 치수표 M12 — 홀 16.1~16.3, L 20.2, D 15.9, H 21.3, P 1.7. CAD 없음(MISUMI)·GrabCAD M12 없음 → 근사.
#  형상: 머리 Ø21.3×1.7 + 몸통 Ø15.9, 전장 20.2(머리 포함 가정), 관통 보어 Ø10.1(M12 골지름 근사). 체결 후 변형(벌지) 미표현.
import os, sys, math, pythoncom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop = watchdog(); app = connect()
NAME = "F1_rivetnut_POP_SPH-1240-3W_approx"; P = os.path.join(Z, NAME + ".SLDPRT")
S1 = os.path.join(Z, "S10000MU0.SLDASM"); mm = lambda v: v/1000.0
HOLES = [(-725, -1426), (-725, -1326), (-725, -2686), (725, -1426), (725, -1326), (725, -2686), (-625, -2786), (625, -2786)]
def sel_plane(d, names):
    for nm in names:
        if d.Extension.SelectByID2(nm, "PLANE", 0, 0, 0, False, 0, NOD, 0): return nm
    raise RuntimeError("no plane")
if not os.path.exists(P):
    tmpl = app.GetUserPreferenceStringValue(8); d = app.NewDocument(tmpl, 0, 0, 0); print("new part", d.GetTitle)
    sel_plane(d, ("정면", "Front Plane")); d.SketchManager.InsertSketch(True); sm = d.SketchManager; sm.AddToDB = True
    rb, rh, rbore, hh, L = 15.9/2, 21.3/2, 10.1/2, 1.7, 20.2
    pts = [(rbore, 0), (rh, 0), (rh, -hh), (rb, -hh), (rb, -L), (rbore, -L), (rbore, 0)]
    for i in range(len(pts)-1): sm.CreateLine(mm(pts[i][0]), mm(pts[i][1]), 0, mm(pts[i+1][0]), mm(pts[i+1][1]), 0)
    ax = sm.CreateLine(0, mm(3), 0, 0, mm(-L-3), 0); ax.ConstructionGeometry = True
    sm.AddToDB = False; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
    ok1 = d.Extension.SelectByID2("스케치1", "SKETCH", 0, 0, 0, False, 0, NOD, 0) or d.Extension.SelectByID2("Sketch1", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
    ok2 = False
    for nm in ("직선7@스케치1", "Line7@Sketch1", "직선7@Sketch1"):
        if d.Extension.SelectByID2(nm, "EXTSKETCHSEGMENT", 0, 0, 0, True, 16, NOD, 0): ok2 = True; break
    print("select sketch", ok1, "axis", ok2)
    f = d.FeatureManager.FeatureRevolve2(True, True, False, False, False, False, 0, 0, math.radians(360), 0.0, False, False, 0.0, 0.0, 0, 0.0, 0.0, True, True, True)
    b = d.GetPartBox(True); print("revolve", f is not None, "box mm", [round(v*1000, 2) for v in b]); assert f is not None
    try:
        import glob
        lib = glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\*\sldmaterials\solidworks materials.sldmat")[0]
        print("material", d.SetMaterialPropertyName2("", lib, "Plain Carbon Steel"))
    except Exception as ex: print("material err", ex)
    cpm = d.Extension.CustomPropertyManager("")
    for k, v in (("TITLE", "RIVET NUT M12 (POP RIVETS SPH-1240-3W)"), ("SPEC", "POP RIVETS SPH-1240-3W M12x1.75 스틸 3가 크로메이트, 판두께 1.6~4.0, 홀 D16.1~16.3, L20.2 D15.9 H21.3 P1.7 (MISUMI 221000765924)"), ("REMARK", "근사형상: MISUMI 치수표로 회전체 작성(나사·체결 후 벌지 미표현). 3D 없음 — MISUMI CAD 없음, GrabCAD M12 리벳너트 없음(M4~M6만). 데크 링 보 □100×3.2 상면 홀 D16.1에 코킹 체결, 윙 M12 볼트 8본"), ("MATERIAL", "스틸(3가 크로메이트)"), ("DATE", "2026-09-16"), ("QT'Y", "8")):
        cpm.Add3(k, 30, v, 1)
    d.EditRebuild3; e = I4(); wn = I4(); ok = d.Extension.SaveAs(P, 0, 1, NOD, e, wn); print("saved", ok, e.value, wn.value, P)
    app.CloseDoc(d.GetTitle)
else: print("part exists", P)
# place in S10000MU0
a = app.GetOpenDocumentByName(S1); assert a is not None
def set_T(c, R, t):
    arr = list(R[0])+list(R[1])+list(R[2])+[t[0]/1000, t[1]/1000, t[2]/1000, 1.0, 0, 0, 0]
    xf = c.Transform2; xf.ArrayData = VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, arr); c.Transform2 = xf
R = [[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]   # part Y(축, 머리 위) → world −x(위)
root = a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
existing = [c for c in root.GetChildren if c.Name2.startswith(NAME)]
print("existing instances", len(existing))
if len(existing) < 8:
    for (y, z) in HOLES[len(existing):]:
        c = a.AddComponent5(P, 0, "", False, "", 0.0, 0.0, 0.0); assert c, "add"
        set_T(c, R, (-1100.0, float(y), float(z))); a.ClearSelection2(True); c.Select4(False, NOD, False); a.FixComponent(); a.ClearSelection2(True)
a.EditRebuild3
root = a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
for c in root.GetChildren:
    if c.Name2.startswith(NAME): print(c.Name2, "box", box(c))
S0 = os.path.join(Z, "S00000MU0.SLDASM"); asm = app.GetOpenDocumentByName(S0); asm.EditRebuild3
idm = asm.InterferenceDetectionManager; asm.ClearSelection2(True)
for nm in ("S10000MU0-1", "S30000MU0-1", "파트1-1", "파트1-2", "파트1-3", "파트1-4"): asm.Extension.SelectByID2(nm + "@S00000MU0", "COMPONENT", 0, 0, 0, True, 0, NOD, 0)
idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False
res = idm.GetInterferences; inter = [(round(it.Volume*1e9, 1), [x.Name2.split('/')[-1] for x in it.Components]) for it in (res or []) if any(NAME in x.Name2 for x in it.Components)]
idm.Done; asm.ClearSelection2(True); print("rivetnut interferences:", inter)
print("S10000 dirty", a.GetSaveFlag, "visible", a.Visible); stop.set()
