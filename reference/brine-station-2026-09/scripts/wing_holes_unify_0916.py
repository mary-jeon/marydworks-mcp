# 2026-09-16 저녁: 윙 볼트 8구멍을 네 코너 모두 일렬(y ±725, 100 피치)로 통일.
#  뒤 기둥(S10001-3/-4) 상단이 열린 관이라 캡 플레이트 F5(PL6 93×93, 관 안쪽 플러시)를 넣고 그 위에 리벳너트 구멍.
#  변경: F5 신설·S10000 배치 2 / S10000 어셈블리 컷 원 2개 (±625,−2786)→(±725,−2786), 깊이 5→7 / F1 리벳너트 -7·-8 이동 / S30003 스케치2 원 2개 이동 / S00000 F3 볼트 -7·-8 이동
import os, sys, math, pythoncom, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from win32com.client import VARIANT
from swconn import *
from swpv import pv
stop = watchdog(); app = connect()
S0 = os.path.join(Z, "S00000MU0.SLDASM"); S1 = os.path.join(Z, "S10000MU0.SLDASM"); mm = lambda v: v/1000.0
CAP = "F5_column_cap_PL6_93x93"; PCAP = os.path.join(Z, CAP + ".SLDPRT")
NUT = "F1_rivetnut_POP_SPH-1240-3W_approx"; BOLT = "F3_bolt_M12x35_SEMS_SUNCO_HXNP3-SUS-M12-35_MISUMI"
def set_T(c, R, t):
    arr = list(R[0])+list(R[1])+list(R[2])+[t[0]/1000, t[1]/1000, t[2]/1000, 1.0, 0, 0, 0]
    xf = c.Transform2; xf.ArrayData = VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, arr); c.Transform2 = xf
def M(c):
    x = list(c.Transform2.ArrayData); return [x[0:3], x[3:6], x[6:9]], x[9:12]
def wpt(c, p):
    R, t = M(c); return [round((sum(p[j]*R[j][i] for j in range(3))+t[i])*1000, 1) for i in range(3)]
def cyl_yz(comp, r, tol=0.2):
    out = set()
    for f in (comp.GetBody.GetFaces() if comp.GetBody else []):
        s = f.GetSurface
        if s.IsCylinder and abs(s.CylinderParams[6]*1000 - r) < tol:
            bb = f.GetBox; c = [(bb[i]+bb[i+3])/2 for i in range(3)]; w = wpt(comp, c); out.add((round(w[1]), round(w[2])))
    return out
# ---- 1) cap part
if not os.path.exists(PCAP):
    tmpl = app.GetUserPreferenceStringValue(8); d = app.NewDocument(tmpl, 0, 0, 0); sm = d.SketchManager
    for nm in ("정면", "Front Plane"):
        if d.Extension.SelectByID2(nm, "PLANE", 0, 0, 0, False, 0, NOD, 0): break
    sm.InsertSketch(True); sm.AddToDB = True; sm.CreateCornerRectangle(mm(-46.5), mm(-46.5), 0, mm(46.5), mm(46.5), 0); sm.AddToDB = False; sm.InsertSketch(True)
    d.ClearSelection2(True); d.Extension.SelectByID2("스케치1", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
    f = d.FeatureManager.FeatureExtrusion3(True, False, False, 0, 0, mm(6), 0, False, False, False, False, 0, 0, False, False, False, False, True, True, True, 0, 0, False)
    d.EditRebuild3; b = d.GetPartBox(True); print("cap bbox", [round(v*1000, 1) for v in b]); assert f is not None
    try:
        lib = glob.glob(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\lang\*\sldmaterials\solidworks materials.sldmat")[0]; d.SetMaterialPropertyName2("", lib, "Plain Carbon Steel")
    except Exception as ex: print("mat err", ex)
    cp = d.Extension.CustomPropertyManager("")
    for k, v in (("TITLE", "COLUMN CAP PLATE"), ("SPEC", "PL 6T SS275 93x93, 뒤 기둥 □100x3.2 상단 관 안쪽 플러시 삽입 용접(HDG 전), 리벳너트 SPH-1240-3W 구멍 D16.1"), ("REMARK", "탱크 윙 뒤 볼트열 y ±725를 기둥 상단에 두기 위한 캡. 빗물 유입 차단 겸용. 관 내폭 93.6 → 편측 틈 0.3"), ("MATERIAL", "SS275(HDG)"), ("DATE", "2026-09-16"), ("QT'Y", "2")): cp.Add3(k, 30, v, 1)
    e = I4(); wn = I4(); print("cap saved", d.Extension.SaveAs(PCAP, 0, 1, NOD, e, wn), e.value); app.CloseDoc(d.GetTitle)
pcap = app.GetOpenDocumentByName(PCAP) or open_doc(app, PCAP, 1)
# ---- 2) S10000: place caps, move cut circles, depth 7, move rivet nuts
e = I4(); app.ActivateDoc3(S1, False, 0, e); a = app.ActiveDoc; assert a.GetTitle.startswith("S10000"), a.GetTitle
def comps(): return {c.Name2: c for c in a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
Rcap = [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]   # part z -> world +x (아래로 6)
if not [n for n in comps() if n.startswith(CAP)]:
    for y in (-725.0, 725.0):
        c = a.AddComponent5(PCAP, 0, "", False, "", 0, 0, 0); assert c
        set_T(c, Rcap, (-1100.0, y, -2786.0)); a.ClearSelection2(True); c.Select4(False, NOD, False); a.FixComponent(); a.ClearSelection2(True)
a.EditRebuild3
for n, c in comps().items():
    if n.startswith(CAP): print("cap", n, box(c))
feat = a.FeatureByName("리벳너트홀_D16.1x8"); sk = None; sf = pv(feat, "GetFirstSubFeature")
while sf is not None:
    if pv(sf, "GetTypeName2") == "ProfileFeature": sk = sf.Name
    sf = pv(sf, "GetNextSubFeature")
print("cut sketch", sk)
if a.SketchManager.ActiveSketch is not None: a.SketchManager.InsertSketch(True)
a.ClearSelection2(True); assert a.Extension.SelectByID2(sk, "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(a, "EditSketch"); sko = a.SketchManager.ActiveSketch; assert sko is not None
mt = sko.ModelToSketchTransform; arr = list(mt.ArrayData); Rs = [arr[0:3], arr[3:6], arr[6:9]]; ts = arr[9:12]
def m2s(p): return [sum(p[j]*Rs[j][i] for j in range(3)) + ts[i] for i in range(3)]
moved = 0
for seg in list(sko.GetSketchSegments):
    if seg.GetType != 1: continue
    cp = seg.GetCenterPoint2
    for (y0, y1) in ((-625.0, -725.0), (625.0, 725.0)):
        src = m2s([-1.100, y0/1000, -2.786]); dst = m2s([-1.100, y1/1000, -2.786])
        if math.hypot(cp.X-src[0], cp.Y-src[1]) < 0.0005:
            a.ClearSelection2(True); assert a.Extension.SelectByID2(seg.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0)
            a.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, dst[0]-src[0], dst[1]-src[1], 0); moved += 1
            cp2 = seg.GetCenterPoint2; print("  moved circle", seg.GetName, "->", [round(v*1000, 1) for v in (cp2.X, cp2.Y)])
a.SketchManager.InsertSketch(True); print("circles moved", moved)
fd = feat.GetDefinition; fd.AccessSelections(a, NOD); fd.SetDepth(True, 0.007); print("depth 7:", feat.ModifyDefinition(fd, a, NOD)); a.EditRebuild3
for n, c in comps().items():
    if n.startswith(NUT):
        R, t = M(c); y, z = round(t[1]*1000), round(t[2]*1000)
        if (y, z) in ((-625, -2786), (625, -2786)):
            set_T(c, R, (t[0]*1000, 725.0 if y > 0 else -725.0, -2786.0)); print("  nut", n, "moved to", (725 if y > 0 else -725, -2786))
a.EditRebuild3; cc = comps()
holes = {}
for n in ("S10002MU0-1", "S10002MU0-2", "S10003MU0-2"): holes[n] = sorted(cyl_yz(cc[n], 8.05))
for n in cc:
    if n.startswith(CAP): holes[n] = sorted(cyl_yz(cc[n], 8.05))
print("frame holes:", holes)
for n, c in cc.items():
    if n.startswith(NUT): print("  nut", n, [round(v) for v in M(c)[1][1:3]] if False else [round(M(c)[1][1]*1000), round(M(c)[1][2]*1000)])
# ---- 3) S00000: wing sketch2 circles, bolts
wp = app.GetOpenDocumentByName(os.path.join(Z, "S30003MU0.SLDPRT")); e = I4(); app.ActivateDoc3(os.path.join(Z, "S30003MU0.SLDPRT"), False, 0, e); d = app.ActiveDoc; assert d.GetTitle.startswith("S30003")
if d.SketchManager.ActiveSketch is not None: d.SketchManager.InsertSketch(True)
d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치2", "SKETCH", 0, 0, 0, False, 0, NOD, 0); pv(d, "EditSketch"); sk2 = d.SketchManager.ActiveSketch
mv = 0
for seg in list(sk2.GetSketchSegments):
    if seg.GetType != 1: continue
    cp = seg.GetCenterPoint2; x, y = cp.X*1000, cp.Y*1000
    if abs(abs(x)-625) < 0.5 and abs(y+730) < 0.5:
        dx = (-100 if x < 0 else 100)/1000.0
        d.ClearSelection2(True); assert d.Extension.SelectByID2(seg.GetName, "SKETCHSEGMENT", 0, 0, 0, False, 0, NOD, 0); d.Extension.MoveOrCopy(False, 1, False, 0, 0, 0, dx, 0, 0); mv += 1
        print("  wing circle", seg.GetName, "->", round(seg.GetCenterPoint2.X*1000, 1), round(seg.GetCenterPoint2.Y*1000, 1))
d.SketchManager.InsertSketch(True); d.EditRebuild3; print("wing circles moved", mv)
e = I4(); app.ActivateDoc3(S0, False, 0, e); asm = app.ActiveDoc; assert asm.GetTitle.startswith("S00000")
def tops(): return {c.Name2: c for c in asm.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True).GetChildren}
for n, c in tops().items():
    if n.startswith(BOLT):
        R, t = M(c); y, z = round(t[1]*1000), round(t[2]*1000)
        # bolt transform t is offset from hole center (axis offset -2.85/0.32 & washer z); shift by ±100 in y only
        if (y in (-625-3, -625+3, -628, -622) or abs(abs(y)-625) < 5) and abs(z+2786) < 5:
            set_T(c, R, (t[0]*1000, t[1]*1000 + (100 if y > 0 else -100), t[2]*1000)); print("  bolt", n, "shifted y by", (100 if y > 0 else -100))
asm.ForceRebuild3(False); tp = tops()
wing = [k for k in tp["S30000MU0-1"].GetChildren if "S30003" in k.Name2][0]
wh = sorted(cyl_yz(wing, 7.0)); print("wing holes", wh)
fh = set()
for k in tp["S10000MU0-1"].GetChildren:
    if k.Name2.split('/')[-1] in ("S10002MU0-1", "S10002MU0-2", "S10003MU0-2") or CAP in k.Name2: fh |= cyl_yz(k, 8.05)
print("frame holes", sorted(fh)); print("mismatch wing vs frame:", set(wh) ^ fh)
ph = set()
for n in ("파트1-1", "파트1-2", "파트1-3", "파트1-4"): ph |= cyl_yz(tp[n], 12.0)
print("wing holes not covered by pads:", set(wh) - ph)
for n, c in tp.items():
    if n.startswith(BOLT): print("  bolt", n, "box", box(c))
idm = asm.InterferenceDetectionManager; asm.ClearSelection2(True)
for n in list(tp):
    if n.startswith(BOLT) or n in ("S30000MU0-1", "S10000MU0-1", "파트1-1", "파트1-2", "파트1-3", "파트1-4"): asm.Extension.SelectByID2(n + "@S00000MU0", "COMPONENT", 0, 0, 0, True, 0, NOD, 0)
idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False
res = idm.GetInterferences; inter = [(round(it.Volume*1e9, 1), [x.Name2.split('/')[-1] for x in it.Components]) for it in (res or []) if not all("염수주입라인" in x.Name2 for x in it.Components) and not all(x.Name2.startswith("S10000") for x in it.Components)]
idm.Done; asm.ClearSelection2(True)
from collections import Counter
print("interference summary:", Counter(tuple(sorted(set(x.split('-')[0] for x in cn))) for v, cn in inter), "n", len(inter))
fe = VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT, None); co = VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT, None); wa = VARIANT(pythoncom.VT_BYREF|pythoncom.VT_VARIANT, None)
asm.Extension.GetWhatsWrong(fe, co, wa); print("S00000 whatswrong:", [(x.Name, c) for x, c in zip(fe.value or [], co.value or [])])
a1 = app.GetOpenDocumentByName(S1); a1.Extension.GetWhatsWrong(fe, co, wa); print("S10000 whatswrong:", [(x.Name, c) for x, c in zip(fe.value or [], co.value or [])])
for n in (CAP + ".SLDPRT", "S30003MU0.SLDPRT", "S10000MU0.SLDASM", "S00000MU0.SLDASM"):
    dd = app.GetOpenDocumentByName(os.path.join(Z, n)); e = I4(); w = I4(); print("save", n, dd.Save3(1, e, w), e.value)
for n in (CAP + ".SLDPRT", "S30003MU0.SLDPRT", "S10000MU0.SLDASM"):
    dd = app.GetOpenDocumentByName(os.path.join(Z, n))
    if dd is not None and dd.Visible: app.CloseDoc(n)
e = I4(); app.ActivateDoc3(S0, False, 0, e); print("active", app.ActiveDoc.GetTitle); stop.set()
