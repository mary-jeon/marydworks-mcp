# 2026-09-16 저녁: 캡 폐기(사용자 「캡 없애」). 뒤 볼트열을 100 앞으로 → 8구멍 전부 □100 세로보 위 일렬 (±725: −1426/−1326 · −2686/−2586).
import os, sys, math, pythoncom
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop = watchdog(); app = connect()
S0 = os.path.join(Z, "S00000MU0.SLDASM"); S1 = os.path.join(Z, "S10000MU0.SLDASM")
CAP = "F5_column_cap_PL6_93x93"; NUT = "F1_rivetnut_POP_SPH-1240-3W_approx"; BOLT = "F3_bolt_M12x35_SEMS_SUNCO_HXNP3-SUS-M12-35_MISUMI"
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
# ---- S10000
e = I4(); app.ActivateDoc3(S1, False, 0, e); a = app.ActiveDoc; assert a.GetTitle.startswith("S10000")
def comps(): return {c.Name2: c for c in a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
for n, c in list(comps().items()):
    if n.startswith(CAP):
        a.ClearSelection2(True); c.Select4(False, NOD, False); print("delete cap comp", n, a.Extension.DeleteSelection2(0)); a.ClearSelection2(True)
feat = a.FeatureByName("리벳너트홀_D16.1x8"); sk = None; sf = pv(feat, "GetFirstSubFeature")
while sf is not None:
    if pv(sf, "GetTypeName2") == "ProfileFeature": sk = sf.Name
    sf = pv(sf, "GetNextSubFeature")
if a.SketchManager.ActiveSketch is not None: a.SketchManager.InsertSketch(True)
a.ClearSelection2(True); assert a.Extension.SelectByID2(sk, "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(a, "EditSketch"); sko = a.SketchManager.ActiveSketch
arr = list(sko.ModelToSketchTransform.ArrayData); Rs = [arr[0:3], arr[3:6], arr[6:9]]; ts = arr[9:12]
def m2s(p): return [sum(p[j]*Rs[j][i] for j in range(3)) + ts[i] for i in range(3)]
mv = 0
for seg in list(sko.GetSketchSegments):
    if seg.GetType != 1: continue
    cp = seg.GetCenterPoint2
    for y in (-725.0, 725.0):
        src = m2s([-1.100, y/1000, -2.786]); dst = m2s([-1.100, y/1000, -2.586])
        if math.hypot(cp.X-src[0], cp.Y-src[1]) < 0.0005:
            a.ClearSelection2(True); assert a.Extension.SelectByID2(seg.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); a.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, dst[0]-src[0], dst[1]-src[1], 0); mv += 1
a.SketchManager.InsertSketch(True); print("cut circles moved", mv)
fd = feat.GetDefinition; fd.AccessSelections(a, NOD); fd.SetDepth(True, 0.005); print("depth 5:", feat.ModifyDefinition(fd, a, NOD)); a.EditRebuild3
for n, c in comps().items():
    if n.startswith(NUT):
        R, t = M(c); y, z = round(t[1]*1000), round(t[2]*1000)
        if z == -2786: set_T(c, R, (t[0]*1000, float(y), -2586.0)); print("  nut", n, "->", (y, -2586))
a.EditRebuild3
# rear pads: move +100 z. find pads' mates to S10003-2 (rear beam) in S00000 → handled below (pads live in S00000)
e = I4(); app.ActivateDoc3(S0, False, 0, e); asm = app.ActiveDoc; assert asm.GetTitle.startswith("S00000")
def tops(): return {c.Name2: c for c in asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
def mates_iter(doc):
    f = pv(doc, "FirstFeature")
    while f is not None:
        if pv(f, "GetTypeName2") == "MateGroup":
            sf = f.GetFirstSubFeature
            while sf is not None: yield sf; sf = sf.GetNextSubFeature
        f = pv(f, "GetNextFeature")
tp = tops()
for pn in ("파트1-2", "파트1-4"):
    pad = tp[pn]; print(pn, "box before", box(pad))
    for m in (pad.GetMates or []):
        ents = []
        for i in range(m.GetMateEntityCount):
            me = m.MateEntity(i); rc = me.ReferenceComponent; ents.append(((rc.Name2 if rc else "?"), [round(v, 4) for v in list(me.EntityParams)[:6]]))
        if any("S10003MU0-2" in e0[0] for e0 in ents):
            print("  mate to rear beam: type", m.Type, ents)
            # find feature name to delete
            for sf in mates_iter(asm):
                try:
                    mm_ = sf.GetSpecificFeature2
                    if mm_ is not None and mm_.GetMateEntityCount == m.GetMateEntityCount and all((mm_.MateEntity(i).ReferenceComponent.Name2 if mm_.MateEntity(i).ReferenceComponent else "?") == (m.MateEntity(i).ReferenceComponent.Name2 if m.MateEntity(i).ReferenceComponent else "?") for i in range(m.GetMateEntityCount)) and mm_.Type == m.Type:
                        # verify same entity params
                        p1 = [round(v, 4) for v in list(mm_.MateEntity(0).EntityParams)[:3]]; p2 = [round(v, 4) for v in list(m.MateEntity(0).EntityParams)[:3]]
                        if p1 == p2:
                            asm.ClearSelection2(True); sf.Select2(False, 0); print("  delete mate", sf.Name, asm.Extension.DeleteSelection2(0)); asm.ClearSelection2(True); break
                except Exception: pass
            # new distance mate 100: pad rear face (z -2836) ↔ beam outer face (z -2836) → pad moves to -2736~-2536
            ys = 675.0 if pn == "파트1-4" else -675.0
            ok = False
            for flip in (False, True):
                asm.ClearSelection2(True)
                s1 = asm.Extension.SelectByID2("", "FACE", -1.103, ys/1000, -2.836, False, 1, NOD, 0)   # pad rear face
                s2 = asm.Extension.SelectByID2("", "FACE", -1.050, 0.0, -2.836, True, 1, NOD, 0)         # beam S10003-2 outer face
                sel = asm.SelectionManager; names = [(sel.GetSelectedObjectsComponent4(i, -1).Name2 if sel.GetSelectedObjectsComponent4(i, -1) else "?") for i in (1, 2)]
                print("  faces:", s1, s2, names)
                err = I4(); mate = asm.AddMate5(5, 2, flip, 0.100, 0, 0, 0, 0, 0, 0, 0, False, False, 0, err); asm.ClearSelection2(True); asm.EditRebuild3
                b = box(tops()[pn]); print("   dist100 flip", flip, mate is not None, err.value, "->", b)
                if b and abs(b[2] + 2736) < 0.05: ok = True; last = list(mates_iter(asm))[-1]; last.Name = f"{pn}_뒤보_거리100"; break
                if mate is not None:
                    last = list(mates_iter(asm))[-1]; asm.ClearSelection2(True); last.Select2(False, 0); asm.Extension.DeleteSelection2(0); asm.ClearSelection2(True)
            assert ok, "pad move failed"
            break
# wing sketch2: (∓725, -730) -> (∓725, -530)
wp = app.GetOpenDocumentByName(os.path.join(Z, "S30003MU0.SLDPRT")); e = I4(); app.ActivateDoc3(os.path.join(Z, "S30003MU0.SLDPRT"), False, 0, e); d = app.ActiveDoc; assert d.GetTitle.startswith("S30003")
if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치2", "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(d, "EditSketch"); sk2 = d.SketchManager.ActiveSketch
mv = 0
for seg in list(sk2.GetSketchSegments):
    if seg.GetType != 1: continue
    cp = seg.GetCenterPoint2; x, y = cp.X*1000, cp.Y*1000
    if abs(abs(x)-725) < 0.5 and abs(y+730) < 0.5:
        d.ClearSelection2(True); assert d.Extension.SelectByID2(seg.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); d.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, 0, 0.200, 0); mv += 1
d.SketchManager.InsertSketch(True); d.EditRebuild3; print("wing circles moved", mv)
e = I4(); app.ActivateDoc3(S0, False, 0, e); asm = app.ActiveDoc
for n, c in tops().items():
    if n.startswith(BOLT):
        R, t = M(c)
        if abs(t[2]*1000 + 2786) < 5: set_T(c, R, (t[0]*1000, t[1]*1000, t[2]*1000 + 200)); print("  bolt", n, "z +200")
asm.ForceRebuild3(False); tp = tops()
wing = [k for k in tp["S30000MU0-1"].GetChildren if "S30003" in k.Name2][0]; wh = cyl_yz(wing, 7.0)
fh = set()
for k in tp["S10000MU0-1"].GetChildren:
    if k.Name2.split('/')[-1] in ("S10002MU0-1", "S10002MU0-2", "S10003MU0-2"): fh |= cyl_yz(k, 8.05)
ph = set()
for n in ("파트1-1", "파트1-2", "파트1-3", "파트1-4"): ph |= cyl_yz(tp[n], 12.0)
print("wing", sorted(wh)); print("frame", sorted(fh)); print("mismatch", wh ^ fh, "| not covered by pads", wh - ph)
for n in ("파트1-2", "파트1-4"): print(n, "box", box(tp[n]))
nuts = sorted((round(M(c)[1][1]*1000), round(M(c)[1][2]*1000)) for n, c in {k.Name2: k for k in tp["S10000MU0-1"].GetChildren}.items() if NUT in n); print("nuts", nuts)
idm = asm.InterferenceDetectionManager; asm.ClearSelection2(True)
for n in list(tp):
    if n.startswith(BOLT) or n in ("S30000MU0-1", "S10000MU0-1", "파트1-1", "파트1-2", "파트1-3", "파트1-4"): asm.Extension.SelectByID2(n + "@S00000MU0", "COMPONENT", 0, 0, 0, True, 0, NOD, 0)
idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False
res = idm.GetInterferences; inter = [(round(it.Volume*1e9, 1), [x.Name2.split('/')[-1] for x in it.Components]) for it in (res or []) if not all("염수주입라인" in x.Name2 for x in it.Components) and not all(x.Name2.startswith("S10000") for x in it.Components)]
idm.Done; asm.ClearSelection2(True)
from collections import Counter; print("interference:", Counter(tuple(sorted(set(x.split('-')[0] for x in cn))) for v, cn in inter))
print("S00000 err", ww(asm), "| S10000 err", ww(app.GetOpenDocumentByName(S1)))
for n in ("S30003MU0.SLDPRT", "S10000MU0.SLDASM", "S00000MU0.SLDASM"):
    dd = app.GetOpenDocumentByName(os.path.join(Z, n)); e = I4(); w = I4(); print("save", n, dd.Save3(1, e, w), e.value)
for n in ("S30003MU0.SLDPRT", "S10000MU0.SLDASM"):
    dd = app.GetOpenDocumentByName(os.path.join(Z, n))
    if dd is not None and dd.Visible: app.CloseDoc(n)
capdoc = app.GetOpenDocumentByName(os.path.join(Z, CAP + ".SLDPRT"))
if capdoc is not None: app.CloseDoc(CAP + ".SLDPRT")
e = I4(); app.ActivateDoc3(S0, False, 0, e); print("active", app.ActiveDoc.GetTitle); stop.set()
