# 2026-09-16: 탱크(S30000) ↔ 프레임(S10000) 조립 구조 반영 — 저장 안 함(검증 후 sw_save 별도).
#  1) S10006 데크판 개구 1200 → 1240 (각 변 +20)
#  2) S30003 마운트 윙: 앞 구멍 (±625,−1326) → (±725,−1326) 제자리 이동, 앞 모서리 C20
#  3) 파트1 패드: 스케치3에 Ø14 2개 추가 → 4-Ø14(±50,±50), 속성 절연 패드
#  4) S10000MU0 어셈블리 컷: 보 상면 Ø13 ×8 (M12 리벳너트용, 깊이 5) — 인스턴스 플립 때문에 파트 파일 대신 어셈블리 피처
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
stop = watchdog(); app = connect()
S0 = os.path.join(Z, "S00000MU0.SLDASM"); S1 = os.path.join(Z, "S10000MU0.SLDASM")
asm = app.GetOpenDocumentByName(S0)
log = {"date": "2026-09-16", "steps": []}
def L(*a):
    print(*a, flush=True); log["steps"].append(" ".join(str(x) for x in a))
def tops():
    root = asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True); return {c.Name2: c for c in root.GetChildren}
def sub(path):
    top, s = path.split("/"); return [x for x in tops()[top].GetChildren if x.Name2 == path][0]
def M(comp):
    a = list(comp.Transform2.ArrayData); return [a[0:3], a[3:6], a[6:9]], a[9:12]
def w_pt(comp, p):
    R, t = M(comp); return [sum(p[j]*R[j][i] for j in range(3)) + t[i] for i in range(3)]
def w_vec(comp, v):
    R, t = M(comp); return [sum(v[j]*R[j][i] for j in range(3)) for i in range(3)]
def cyl_world(comp, r, tol=0.2):
    out = []
    for f in comp.GetBody.GetFaces():
        s = f.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000 - r) < tol:
            bb = f.GetBox; c = [(bb[i]+bb[i+3])/2 for i in range(3)]; out.append([round(v*1000, 1) for v in w_pt(comp, c)])
    return sorted(out)
def planes_world(comp, axis, minarea=0.001):
    out = set()
    for f in comp.GetBody.GetFaces():
        s = f.GetSurface
        if s.IsPlane and f.GetArea > minarea:
            pp = s.PlaneParams; n = w_vec(comp, pp[0:3]); p = w_pt(comp, pp[3:6])
            if abs(n[axis]) > 0.99: out.add(round(p[axis]*1000, 1))
    return sorted(out)
def activate(path):
    e = I4(); app.ActivateDoc3(path, False, 0, e); d = app.ActiveDoc; assert d.GetPathName.lower() == path.lower(), d.GetPathName; return d
def xf_arr(mt):
    a = list(mt.ArrayData); R = [a[0:3], a[3:6], a[6:9]]; t = a[9:12]; s = a[12]; return R, t, s
def apply(mt, p):
    R, t, s = xf_arr(mt); return [sum(p[j]*R[j][i] for j in range(3))*s + t[i] for i in range(3)]
def model_to_sketch(sk, p_model):
    return apply(sk.ModelToSketchTransform, p_model)
def sketch_to_model(sk, p_sk):
    return apply(sk.ModelToSketchTransform.Inverse, p_sk)

# ---------- 1) S10006 개구 ----------
P10006 = os.path.join(Z, "S10006MU0.SLDPRT")
d = activate(P10006)
for nm in ("D2@스케치38", "D3@스케치38"):
    dim = d.Parameter(nm); L("S10006", nm, "before", round(dim.SystemValue*1000, 1)); dim.SystemValue = 1.240; L("  ->", round(dim.SystemValue*1000, 1))
d.EditRebuild3
# ---------- 2) S30003 윙 ----------
P30003 = os.path.join(Z, "S30003MU0.SLDPRT")
d = activate(P30003)
comp_w = sub("S30000MU0-1/S30003MU0-1")
R, t = M(comp_w)
def part_from_world(comp, w):  # inverse of w_pt (R orthonormal)
    Rm, tm = M(comp); v = [w[i]-tm[i] for i in range(3)]; return [sum(v[i]*Rm[j][i] for i in range(3)) for j in range(3)]
targets = {}
for wy in (625.0, -625.0):
    src = part_from_world(comp_w, [-1.109, wy/1000, -1.326]); dst = part_from_world(comp_w, [-1.109, (725.0 if wy > 0 else -725.0)/1000, -1.326])
    targets[wy] = (src, dst)
L("wing targets part-local (src->dst):", {k: ([round(x*1000, 1) for x in v[0]], [round(x*1000, 1) for x in v[1]]) for k, v in targets.items()})
if d.SketchManager.ActiveSketch is not None and d.SketchManager.ActiveSketch.Name != "스케치2": d.SketchManager.InsertSketch(True)
d.ClearSelection2(True)
assert d.Extension.SelectByID2("스케치2", "SKETCH", 0, 0, 0, False, 0, NOD, 0), "sketch2 select"
sk = d.SketchManager.ActiveSketch
if sk is None or sk.Name != "스케치2": pv(d, "EditSketch"); sk = d.SketchManager.ActiveSketch
assert sk is not None and sk.Name == "스케치2"
segs = list(sk.GetSketchSegments); circles = [s for s in segs if s.GetType == 1]
L("wing sketch2 segments", len(segs), "arcs", len(circles))
moved = 0
for wy, (src, dst) in targets.items():
    src_s = model_to_sketch(sk, src); dst_s = model_to_sketch(sk, dst)
    def near(p): 
        b = None
        for c in circles:
            cp = c.GetCenterPoint2; dd = math.hypot(cp.X - p[0], cp.Y - p[1])
            if b is None or dd < b[0]: b = (dd, c, cp)
        return b
    dd, c, cp = near(src_s)
    if dd > 0.002:
        dd2, c2, cp2 = near(dst_s); L(f"  src circle absent (nearest {dd*1000:.1f} mm); at dst? {dd2*1000:.2f} mm"); assert dd2 < 0.0005, "circle neither at src nor dst"; continue
    nm = c.GetName; d.ClearSelection2(True); ok = d.Extension.SelectByID2(nm, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0)
    assert ok and d.SelectionManager.GetSelectedObjectCount2(-1) == 1, "select circle"
    d.Extension.MoveOrCopy(False, 1, False, 0.0, 0.0, 0.0, dst_s[0]-src_s[0], dst_s[1]-src_s[1], 0.0)
    cp2 = c.GetCenterPoint2; L(f"  {nm}: ({cp.X*1000:.1f},{cp.Y*1000:.1f}) -> ({cp2.X*1000:.1f},{cp2.Y*1000:.1f}) target ({dst_s[0]*1000:.1f},{dst_s[1]*1000:.1f})")
    assert math.hypot(cp2.X-dst_s[0], cp2.Y-dst_s[1]) < 0.0005, "move failed"; moved += 1
L("wing circles moved this run:", moved)
d.SketchManager.InsertSketch(True); d.EditRebuild3
# chamfer C20 at front corners via sketch chamfer in 스케치1 (in-place edit; feature chamfer API returned None)
def has45(comp):
    for f in comp.GetBody.GetFaces():
        sf = f.GetSurface
        if sf.IsPlane:
            n = w_vec(comp, sf.PlaneParams[0:3])
            if abs(abs(n[1]) - 0.7071) < 0.01 and abs(abs(n[2]) - 0.7071) < 0.01: return True
    return False
if not has45(comp_w):
    d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
    sk1 = d.SketchManager.ActiveSketch
    if sk1 is None or sk1.Name != "스케치1": pv(d, "EditSketch"); sk1 = d.SketchManager.ActiveSketch
    assert sk1 is not None and sk1.Name == "스케치1"
    lines = [x for x in sk1.GetSketchSegments if x.GetType == 0 and not x.ConstructionGeometry]
    made = 0
    for wy in (780.0, -780.0):
        corner = model_to_sketch(sk1, part_from_world(comp_w, [-1.109, wy/1000, -1.276]))
        adj = []
        for ln in lines:
            for pt in (ln.GetStartPoint2, ln.GetEndPoint2):
                if math.hypot(pt.X - corner[0], pt.Y - corner[1]) < 0.0005: adj.append(ln); break
        L("  corner", [round(v*1000, 1) for v in corner[:2]], "adjacent lines", len(adj))
        if len(adj) != 2: continue
        d.ClearSelection2(True)
        for ln in adj: assert d.Extension.SelectByID2(ln.GetName, "SKETCHSEGMENT", 0, 0, 0, True, 0, NOD, 0)
        r = d.SketchManager.CreateChamfer(1, 0.020, 0.020); L("  CreateChamfer ->", r is not None); made += int(r is not None)
    d.SketchManager.InsertSketch(True); d.EditRebuild3
    L("  wing 45deg faces after:", has45(comp_w)); assert has45(comp_w), "sketch chamfer failed"
# ---------- 3) 파트1 패드 ----------
PPAD = os.path.join(Z, "파트1.SLDPRT")
d = activate(PPAD); comp_p = tops()["파트1-1"]
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치3", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
pv(d, "EditSketch"); sk = d.SketchManager.ActiveSketch; assert sk is not None
segs = list(sk.GetSketchSegments); circles = [s for s in segs if s.GetType == 1]
cents = [sketch_to_model(sk, [c.GetCenterPoint2.X, c.GetCenterPoint2.Y, 0]) for c in circles]
L("pad existing circle centers (part mm):", [[round(v*1000, 1) for v in c] for c in cents])
zpl = cents[0][2]
want = [(0.05, 0.05), (-0.05, -0.05)]
d.SketchManager.AddToDB = True
for (px, py) in want:
    if any(abs(c[0]-px) < 0.001 and abs(c[1]-py) < 0.001 for c in cents): L("  exists", px, py); continue
    s = model_to_sketch(sk, [px, py, zpl]); c = d.SketchManager.CreateCircleByRadius(s[0], s[1], 0.0, 0.007); L("  add circle", (px*1000, py*1000), "->", c is not None)
d.SketchManager.AddToDB = False
d.SketchManager.InsertSketch(True); d.EditRebuild3
cp = d.Extension.CustomPropertyManager("")
for k, v in (("TITLE", "INSULATING PAD"), ("SPEC", "PAD 200x200x6 4-D14 절연(비금속) — 재질 미확인"), ("MATERIAL", "미확인(비금속 절연재)"), ("REMARK", "윙 S30003 ↔ 프레임 보 사이 이종금속 절연. M12 리벳너트 체결. 구멍 4개 중 2개 사용(인스턴스 회전 대응)")):
    cp.Add3(k, 30, v, 1); L("  prop", k, "->", cp.Get(k))
# ---------- 4) S10000MU0 어셈블리 컷 ----------
d = activate(S1)
holes = [(-725, -1426), (-725, -1326), (-725, -2686), (725, -1426), (725, -1326), (725, -2686), (-625, -2786), (625, -2786)]
if d.FeatureByName("리벳너트홀_D13x8") is None:
    d.ClearSelection2(True)
    ok = d.Extension.SelectByID2("", "FACE", -1.100, -0.725, -0.800, False, 0, NOD, 0); L("S10000 select S10002-1 top face", ok); assert ok
    d.SketchManager.InsertSketch(True); sk = d.SketchManager.ActiveSketch
    d.SketchManager.AddToDB = True
    for (y, z) in holes:
        s = model_to_sketch(sk, [-1.100, y/1000, z/1000]); c = d.SketchManager.CreateCircleByRadius(s[0], s[1], 0.0, 0.0065); assert c is not None
    d.SketchManager.AddToDB = False
    L("S10000 sketch circles", len(holes))
if d.FeatureByName("리벳너트홀_D13x8") is not None:
    L("S10000 cut already exists; skipping"); feat = d.FeatureByName("리벳너트홀_D13x8")
else:
  feat = d.FeatureManager.FeatureCut4(True, False, False, 0, 0, 0.005, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, True, True, False, 0, 0.0, False, False)
L("S10000 assembly cut:", feat.Name if feat else None); assert feat is not None
if feat.Name != "리벳너트홀_D13x8": feat.Name = "리벳너트홀_D13x8"
d.EditRebuild3
# ---------- verify ----------
activate(S0); asm.ForceRebuild3(False)
V = {}
cw = sub("S30000MU0-1/S30003MU0-1"); V["wing_holes"] = cyl_world(cw, 7.0); V["wing_chamfer_planes45"] = None
V["pad_holes"] = {nm: cyl_world(tops()[nm], 7.0) for nm in ("파트1-1", "파트1-2", "파트1-3", "파트1-4")}
c6 = sub("S10000MU0-1/S10006MU0-2"); V["deck_cut_y"] = planes_world(c6, 1); V["deck_cut_z"] = planes_world(c6, 2)
for nm in ("S10000MU0-1/S10002MU0-1", "S10000MU0-1/S10002MU0-2", "S10000MU0-1/S10003MU0-2", "S10000MU0-1/S10006MU0-2"):
    V["beam_holes_" + nm.split("/")[1]] = cyl_world(sub(nm), 6.5)
for k, v in V.items(): L(k, v)
# interference tank vs frame+pads
idm = asm.InterferenceDetectionManager; asm.ClearSelection2(True)
for nm in ("S30000MU0-1", "S10000MU0-1", "파트1-1", "파트1-2", "파트1-3", "파트1-4"): asm.Extension.SelectByID2(nm + "@S00000MU0", "COMPONENT", 0, 0, 0, True, 0, NOD, 0)
idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False; idm.IncludeMultibodyPartInterferences = False
res = idm.GetInterferences; inter = []
for it in (res or []):
    cn = [c.Name2 for c in it.Components]
    if not all("염수주입라인" in x for x in cn): inter.append((round(it.Volume*1e9, 1), cn))
idm.Done; asm.ClearSelection2(True); L("interference (non-line):", inter)
log["verify"] = V; log["interference"] = inter
json.dump(log, open(os.path.join(VER, "tank_mount_0916.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("NOT SAVED; dirty:", [x.GetTitle for x in app.GetDocuments if x.GetSaveFlag][:20]); stop.set()
