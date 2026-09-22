# 2026-09-16 밤: 사용자 지시 「파트1 원래 자리·형상, 네 코너 대각선(패드 3구멍 중 대각 2개), 일자 금지」
#  되돌림: 파트1 L 200×200 복원 / 뒤 패드 거리100 메이트 → 뒤보 일치 복원 / 윙 스케치2 8구멍 = 앞 (±725,−1426)+(±625,−1326), 뒤 (±725,−2686)+(±625,−2786)
#  S10000 어셈블리 컷 원 4개 이동(±625 위치는 데크판·뒤보 위) / 리벳너트·볼트 이동 / 캡 F5 파일 삭제
import os, sys, math, pythoncom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop = watchdog(); app = connect()
S0 = os.path.join(Z, "S00000MU0.SLDASM"); S1 = os.path.join(Z, "S10000MU0.SLDASM")
NUT = "F1_rivetnut_POP_SPH-1240-3W_approx"; BOLT = "F3_bolt_M12x35_SEMS_SUNCO_HXNP3-SUS-M12-35_MISUMI"; CAP = "F5_column_cap_PL6_93x93"
def set_T(c, R, t):
    arr = list(R[0])+list(R[1])+list(R[2])+[t[0]/1000, t[1]/1000, t[2]/1000, 1.0, 0, 0, 0]
    xf = c.Transform2; xf.ArrayData = VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, arr); c.Transform2 = xf
def M(c):
    x = list(c.Transform2.ArrayData); return [x[0:3], x[3:6], x[6:9]], x[9:12]
def cyl_yz(comp, r, tol=0.2):
    out = set()
    for f in (comp.GetBody.GetFaces() if comp.GetBody else []):
        s = f.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000 - r) < tol:
            bb = f.GetBox; c = [(bb[i]+bb[i+3])/2 for i in range(3)]; R, t = M(comp); w = [(sum(c[j]*R[j][i] for j in range(3))+t[i])*1000 for i in range(3)]; out.add((round(w[1]), round(w[2])))
    return out
def ww(d):
    fe = VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT, None); co = VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT, None); wa = VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT, None)
    d.Extension.GetWhatsWrong(fe, co, wa); return [(x.Name, c) for x, c in zip(fe.value or [], co.value or [])]
def mates_iter(doc):
    f = pv(doc, "FirstFeature")
    while f is not None:
        if pv(f, "GetTypeName2") == "MateGroup":
            sf = f.GetFirstSubFeature
            while sf is not None: yield sf; sf = sf.GetNextSubFeature
        f = pv(f, "GetNextFeature")
# ---- 1) 파트1 revert outline
P = os.path.join(Z, "파트1.SLDPRT"); d = app.GetOpenDocumentByName(P) or open_doc(app, P, 1); e = I4(); app.ActivateDoc3(P, False, 0, e); d = app.ActiveDoc; assert d.GetTitle.startswith("파트1")
if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치1", "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(d, "EditSketch"); sk = d.SketchManager.ActiveSketch
for s in list(sk.GetSketchSegments):
    if s.GetType != 0 or s.ConstructionGeometry: continue
    a = s.GetStartPoint2; b = s.GetEndPoint2; ax, ay, bx, by = a.X*1000, a.Y*1000, b.X*1000, b.Y*1000
    if abs(ax+70) < 0.5 and abs(bx+70) < 0.5:
        d.ClearSelection2(True); assert d.Extension.SelectByID2(s.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); d.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, -0.030, 0, 0)
    if abs(ay+70) < 0.5 and abs(by+70) < 0.5:
        d.ClearSelection2(True); assert d.Extension.SelectByID2(s.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); d.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, 0, -0.030, 0)
d.SketchManager.InsertSketch(True); d.EditRebuild3; b = d.GetPartBox(True); print("파트1 bbox", [round(v*1000, 1) for v in b]); assert abs(b[0]*1000+100) < 0.1 and abs(b[1]*1000+100) < 0.1
cp = d.Extension.CustomPropertyManager(""); cp.Add3("SPEC", 30, "PAD L형 200x200x6(한 사분면 제외) 3-D24 절연 EPDM t6", 1)
e = I4(); w = I4(); print("save 파트1", d.Save3(1, e, w), e.value); app.CloseDoc("파트1.SLDPRT")
# ---- 2) S00000: rear pads back (delete 거리100 mates, add coincident to rear beam)
e = I4(); app.ActivateDoc3(S0, False, 0, e); asm = app.ActiveDoc; assert asm.GetTitle.startswith("S00000")
def tops(): return {c.Name2: c for c in asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
for sf in list(mates_iter(asm)):
    if "뒤보_거리100" in sf.Name: asm.ClearSelection2(True); sf.Select2(False, 0); print("delete", sf.Name, asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True)
asm.EditRebuild3
for pn, ys in (("파트1-2", -0.675), ("파트1-4", 0.675)):
    b0 = box(tops()[pn]); zr = b0[2]/1000.0   # pad rear face z (may still be at -2736 or moved)
    ok = False
    for al in (1, 0, 2):
        asm.ClearSelection2(True)
        s1 = asm.Extension.SelectByID2("", "FACE", -1.103, ys, zr, False, 1, NOD, 0)
        s2 = asm.Extension.SelectByID2("", "FACE", -1.050, 0.0, -2.836, True, 1, NOD, 0)
        sel = asm.SelectionManager; names = [(sel.GetSelectedObjectsComponent4(i, -1).Name2 if sel.GetSelectedObjectsComponent4(i, -1) else "?") for i in (1, 2)]
        if not (s1 and s2 and pn in names[0] and "S10003MU0-2" in names[1]): print("  face pick failed", names); continue
        err = I4(); mate = asm.AddMate5(0, al, False, 0, 0, 0, 0, 0, 0, 0, 0, False, False, 0, err); asm.ClearSelection2(True); asm.EditRebuild3
        b1 = box(tops()[pn]); print(pn, "coincident align", al, mate is not None, err.value, "->", b1)
        if b1 and abs(b1[2] + 2836) < 0.05 and abs(b1[5] + 2636) < 0.05: ok = True; last = list(mates_iter(asm))[-1]; last.Name = f"{pn}_뒤보_일치"; break
        if mate is not None:
            last = list(mates_iter(asm))[-1]; asm.ClearSelection2(True); last.Select2(False, 0); asm.Extension.DeleteSelection2(0); asm.ClearSelection2(True); asm.EditRebuild3
    assert ok, pn + " restore failed"
# ---- 3) wing sketch2 -> original diagonal
wp = app.GetOpenDocumentByName(os.path.join(Z, "S30003MU0.SLDPRT")); e = I4(); app.ActivateDoc3(os.path.join(Z, "S30003MU0.SLDPRT"), False, 0, e); d = app.ActiveDoc; assert d.GetTitle.startswith("S30003")
if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치2", "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(d, "EditSketch"); sk2 = d.SketchManager.ActiveSketch
# sketch: x = -world_y, y = -(world_z+2056). targets: front (±725,-1426)->(∓725, 630) keep; (±625,-1326)->(∓625,730); rear (±725,-2686)->(∓725,-630) keep; (±625,-2786)->(∓625,-730)
mv = 0
for seg in list(sk2.GetSketchSegments):
    if seg.GetType != 1: continue
    cpx, cpy = seg.GetCenterPoint2.X*1000, seg.GetCenterPoint2.Y*1000
    dx = dy = 0.0
    if abs(abs(cpx)-725) < 0.5 and abs(cpy-730) < 0.5: dx = (100 if cpx < 0 else -100)          # ∓725,730 -> ∓625,730
    if abs(abs(cpx)-725) < 0.5 and abs(cpy+530) < 0.5: dx = (100 if cpx < 0 else -100); dy = -200  # ∓725,-530 -> ∓625,-730
    if dx or dy:
        d.ClearSelection2(True); assert d.Extension.SelectByID2(seg.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); d.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, dx/1000, dy/1000, 0); mv += 1
d.SketchManager.InsertSketch(True); d.EditRebuild3; print("wing circles moved", mv)
e = I4(); w = I4(); print("save wing", d.Save3(1, e, w), e.value); app.CloseDoc("S30003MU0.SLDPRT")
# ---- 4) S10000: cut circles + nuts
e = I4(); app.ActivateDoc3(S1, False, 0, e); a = app.ActiveDoc; assert a.GetTitle.startswith("S10000")
def comps(): return {c.Name2: c for c in a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
feat = a.FeatureByName("리벳너트홀_D16.1x8"); skn = None; sf = pv(feat, "GetFirstSubFeature")
while sf is not None:
    if pv(sf, "GetTypeName2") == "ProfileFeature": skn = sf.Name
    sf = pv(sf, "GetNextSubFeature")
if a.SketchManager.ActiveSketch is not None: a.SketchManager.InsertSketch(True)
a.ClearSelection2(True); assert a.Extension.SelectByID2(skn, "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(a, "EditSketch"); sko = a.SketchManager.ActiveSketch
arr = list(sko.ModelToSketchTransform.ArrayData); Rs = [arr[0:3], arr[3:6], arr[6:9]]; ts = arr[9:12]
def m2s(p): return [sum(p[j]*Rs[j][i] for j in range(3)) + ts[i] for i in range(3)]
MOVES = [((-725, -1326), (-625, -1326)), ((725, -1326), (625, -1326)), ((-725, -2586), (-625, -2786)), ((725, -2586), (625, -2786))]
mv = 0
for seg in list(sko.GetSketchSegments):
    if seg.GetType != 1: continue
    cpt = seg.GetCenterPoint2
    for (y0, z0), (y1, z1) in MOVES:
        src = m2s([-1.100, y0/1000, z0/1000]); dst = m2s([-1.100, y1/1000, z1/1000])
        if math.hypot(cpt.X-src[0], cpt.Y-src[1]) < 0.0005:
            a.ClearSelection2(True); assert a.Extension.SelectByID2(seg.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); a.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, dst[0]-src[0], dst[1]-src[1], 0); mv += 1
a.SketchManager.InsertSketch(True); a.EditRebuild3; print("cut circles moved", mv)
for n, c in comps().items():
    if n.startswith(NUT):
        R, t = M(c); y, z = round(t[1]*1000), round(t[2]*1000)
        for (y0, z0), (y1, z1) in MOVES:
            if (y, z) == (y0, z0): set_T(c, R, (t[0]*1000, float(y1), float(z1))); print("  nut", n, "->", (y1, z1))
a.EditRebuild3
fh = set()
for n, c in comps().items():
    if n in ("S10002MU0-1", "S10002MU0-2", "S10003MU0-2", "S10006MU0-2"): fh |= cyl_yz(c, 8.05)
print("frame holes (beams+deck)", sorted(fh))
e = I4(); w = I4(); print("save S10000", a.Save3(1, e, w), e.value); app.CloseDoc("S10000MU0.SLDASM")
# ---- 5) S00000 bolts
e = I4(); app.ActivateDoc3(S0, False, 0, e); asm = app.ActiveDoc
for n, c in tops().items():
    if n.startswith(BOLT):
        R, t = M(c); y, z = t[1]*1000, t[2]*1000
        for (y0, z0), (y1, z1) in MOVES:
            if abs(y-y0) < 5 and abs(z-z0) < 5: set_T(c, R, (t[0]*1000, y + (y1-y0), z + (z1-z0))); print("  bolt", n, "->", (y1, z1))
asm.ForceRebuild3(False); tp = tops()
wing = [k for k in tp["S30000MU0-1"].GetChildren if "S30003" in k.Name2][0]; wh = cyl_yz(wing, 7.0)
fh = set(); nuts = set()
for k in tp["S10000MU0-1"].GetChildren:
    nm = k.Name2.split('/')[-1]
    if nm in ("S10002MU0-1", "S10002MU0-2", "S10003MU0-2", "S10006MU0-2"): fh |= cyl_yz(k, 8.05)
    if NUT in nm: nuts.add((round(M(k)[1][1]*1000), round(M(k)[1][2]*1000)))
ph = set()
for n in ("파트1-1", "파트1-2", "파트1-3", "파트1-4"): ph |= cyl_yz(tp[n], 12.0)
print("wing", sorted(wh)); print("frame", sorted(fh)); print("nuts", sorted(nuts)); print("mismatch wing/frame", wh ^ fh, "| wing/nuts", wh ^ nuts, "| not covered by pads", wh - ph)
for n in ("파트1-1", "파트1-2", "파트1-3", "파트1-4"): print(n, box(tp[n]))
idm = asm.InterferenceDetectionManager; asm.ClearSelection2(True)
for n in list(tp):
    if n.startswith(BOLT) or n in ("S30000MU0-1", "S10000MU0-1", "파트1-1", "파트1-2", "파트1-3", "파트1-4"): asm.Extension.SelectByID2(n + "@S00000MU0", "COMPONENT", 0, 0, 0, True, 0, NOD, 0)
idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False
res = idm.GetInterferences; inter = [(round(it.Volume*1e9, 1), [x.Name2.split('/')[-1] for x in it.Components]) for it in (res or []) if not all("염수주입라인" in x.Name2 for x in it.Components) and not all(x.Name2.startswith("S10000") for x in it.Components)]
idm.Done; asm.ClearSelection2(True)
from collections import Counter; print("interference:", Counter(tuple(sorted(set(x.split('-')[0] for x in cn))) for v, cn in inter))
print("S00000 err", ww(asm))
e = I4(); w = I4(); print("save S00000", asm.Save3(1, e, w), e.value)
capp = os.path.join(Z, CAP + ".SLDPRT")
if app.GetOpenDocumentByName(capp) is not None: app.CloseDoc(CAP + ".SLDPRT")
if os.path.exists(capp): os.remove(capp); print("deleted cap file", capp)
e = I4(); app.ActivateDoc3(S0, False, 0, e); print("active", app.ActiveDoc.GetTitle); stop.set()
