# 2026-09-21 염수주입라인: (1) 고정판 J1c·이동판 J5n 외형을 210x580(x -75~135, y +-290)으로 통일 -> 새 파일 J1d / J5p 로 SaveAs(구 파일 보존)
#   (2) 구매품 샤프트 홀더 J23d(MISUMI SHFSS20) x4 -> 제작 가이드 블록 J24a x4 (같은 좌표계·같은 취부 피치 48 -> J1 판 M6 탭 재사용, 평면 메이트 재부착)
# usage: line_plates_guide_0921.py plates | guide | replace | all
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
STAGE = sys.argv[1] if len(sys.argv) > 1 else "all"
mm = lambda v: v / 1000.0
Zp = lambda n: os.path.join(Z, n)
DATE = "2026-09-21"; rep = {"stage": STAGE}
XMIN, XMAX, YH = -75.0, 135.0, 290.0
P_J1_OLD = Zp("J1c_fixed_plate_185x580_t10.SLDPRT"); P_J1 = Zp("J1d_fixed_plate_210x580_t10.SLDPRT")
P_J5_OLD = Zp("J5n_moving_plate_180x540_t8.SLDPRT"); P_J5 = Zp("J5p_moving_plate_210x580_t8.SLDPRT")
P_G = Zp("J24a_shaft_guide_fab_60x40x40.SLDPRT"); P_G_OLD = Zp("J23d_shaft_support_MISUMI_SHFSS20_catalog.SLDPRT")
app = connect(); tmpl = app.GetUserPreferenceStringValue(8)
LINE = [d for d in app.GetDocuments if d.GetTitle.startswith("염수주입라인")][0]; P_LINE = LINE.GetPathName

def ww(doc):
    fe = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None); co = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None); wa = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None)
    doc.Extension.GetWhatsWrong(fe, co, wa); return [(f.Name, c) for f, c in zip(fe.value or [], co.value or [])]
def feats(d):
    out = []; f = pv(d, "FirstFeature")
    while f is not None: out.append((f.Name, pv(f, "GetTypeName2"))); f = pv(f, "GetNextFeature")
    return out
def bodies(d): return list(pv(d, "GetBodies2", 0, True) or [])
def bbox(d):
    bs = bodies(d); assert len(bs) == 1, len(bs); return [round(v * 1000, 2) for v in pv(bs[0], "GetBodyBox")]
def volume(d): return d.Extension.CreateMassProperty.Volume * 1e9
def sel_plane(d, ko):
    en = {"정면": "Front Plane", "윗면": "Top Plane", "우측면": "Right Plane"}[ko]; d.ClearSelection2(True)
    return d.Extension.SelectByID2(ko, "PLANE", 0, 0, 0, False, 0, NOD, 0) or d.Extension.SelectByID2(en, "PLANE", 0, 0, 0, False, 0, NOD, 0)
def origin_sel(d, append):
    for nm in ("Point1@원점", "Point1@Origin"):
        if d.Extension.SelectByID2(nm, "EXTSKETCHPOINT", 0, 0, 0, append, 0, NOD, 0): return True
    return False
def rel(d, kind, *ents):
    d.ClearSelection2(True)
    for i, e in enumerate(ents): assert e.Select4(i > 0, NOD), kind
    d.SketchAddConstraints(kind); d.ClearSelection2(True)
def rel_origin(d, kind, e):
    d.ClearSelection2(True); assert e.Select4(False, NOD); assert origin_sel(d, True); d.SketchAddConstraints(kind); d.ClearSelection2(True)
def dim(d, name, e1, e2, at, how="d"):
    """e2 None -> against origin. at = text position in sketch coords (mm)."""
    d.ClearSelection2(True); assert e1.Select4(False, NOD)
    if e2 == "origin": assert origin_sel(d, True)
    elif e2 is not None: assert e2.Select4(True, NOD)
    fn = {"d": d.AddDimension2, "h": d.AddHorizontalDimension2, "v": d.AddVerticalDimension2}[how]
    dd = fn(mm(at[0]), mm(at[1]), 0.0); d.ClearSelection2(True); assert dd is not None, name
    dm = dd.GetDimension2(0); dm.Name = name; return round(dm.SystemValue * 1000, 3)
def set_props(d, props):
    cp = d.Extension.CustomPropertyManager("")
    for k, v in props.items():
        if cp.Get(k): cp.Set2(k, v)
        else: cp.Add3(k, 30, v, 1)
def activate(path):
    app.ActivateDoc3(path, False, 0, I4()); return app.ActiveDoc

old_pref = app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10, False)
try:
    # ---------- 1. plates ----------
    if STAGE in ("all", "plates"):
        for p_old, p_new, skname, tag, spec_old, spec_new, extra in (
            (P_J1_OLD, P_J1, "스케치3", "J1", "185(X −75~110)×580(Y ±290)", "210(X −75~135)×580(Y ±290)", "고정판"),
            (P_J5_OLD, P_J5, "스케치1", "J5", "180×540(x −45~135, y ±270)", "210×580(x −75~135, y ±290)", "이동판")):
            if os.path.exists(p_new): print("exists, skip", os.path.basename(p_new)); continue
            d = app.GetOpenDocumentByName(p_old); assert d is not None, p_old
            d = activate(p_old); v0 = volume(d); b0 = bbox(d) if d.SketchManager.ActiveSketch is None else None
            if d.SketchManager.ActiveSketch is None:
                d.ClearSelection2(True); assert d.Extension.SelectByID2(skname, "SKETCH", 0, 0, 0, False, 0, NOD, 0); d.EditSketch()
            sk = d.SketchManager.ActiveSketch; lines = [s for s in sk.GetSketchSegments if s.GetType == 0]; assert len(lines) == 4, len(lines)
            H0 = sorted([L for L in lines if abs(L.GetStartPoint2.Y - L.GetEndPoint2.Y) < 1e-9], key=lambda L: L.GetStartPoint2.Y); V0 = sorted([L for L in lines if abs(L.GetStartPoint2.X - L.GetEndPoint2.X) < 1e-9], key=lambda L: L.GetStartPoint2.X); assert len(H0) == 2 and len(V0) == 2
            for _ in range(3):      # return value of SetCoords is unreliable when H/V relations drag neighbours -> verify by coordinates below
                for L, y in ((H0[0], -YH), (H0[1], YH)):
                    q = sorted([L.GetStartPoint2, L.GetEndPoint2], key=lambda p_: p_.X); q[0].SetCoords(mm(XMIN), mm(y), 0.0); q[1].SetCoords(mm(XMAX), mm(y), 0.0)
                for L, x in ((V0[0], XMIN), (V0[1], XMAX)):
                    q = sorted([L.GetStartPoint2, L.GetEndPoint2], key=lambda p_: p_.Y); q[0].SetCoords(mm(x), mm(-YH), 0.0); q[1].SetCoords(mm(x), mm(YH), 0.0)
            H = [L for L in lines if abs(L.GetStartPoint2.Y - L.GetEndPoint2.Y) < 1e-9]; V = [L for L in lines if abs(L.GetStartPoint2.X - L.GetEndPoint2.X) < 1e-9]; assert len(H) == 2 and len(V) == 2
            for L in H: rel(d, "sgHORIZONTAL2D", L)
            for L in V: rel(d, "sgVERTICAL2D", L)
            pts = [p for L in lines for p in (L.GetStartPoint2, L.GetEndPoint2)]
            for i in range(len(pts)):
                for j in range(i + 1, len(pts)):
                    if abs(pts[i].X - pts[j].X) < 1e-9 and abs(pts[i].Y - pts[j].Y) < 1e-9: rel(d, "sgMERGEPOINTS", pts[i], pts[j])
            left = min(V, key=lambda L: L.GetStartPoint2.X); right = max(V, key=lambda L: L.GetStartPoint2.X); bot = min(H, key=lambda L: L.GetStartPoint2.Y); top = max(H, key=lambda L: L.GetStartPoint2.Y)
            dims = {"외형_X마이너스": dim(d, "외형_X마이너스", left, "origin", (XMIN / 2, -YH - 40)), "외형_X플러스": dim(d, "외형_X플러스", right, "origin", (XMAX / 2, -YH - 40)),
                    "외형_Y플러스": dim(d, "외형_Y플러스", top, "origin", (XMAX + 40, YH / 2)), "외형_Y마이너스": dim(d, "외형_Y마이너스", bot, "origin", (XMAX + 40, -YH / 2))}
            d.SketchManager.InsertSketch(True); d.EditRebuild3; b1 = bbox(d); v1 = volume(d)
            print(f"  {tag} box {b0} -> {b1}  dims {dims}  dv {round(v1 - v0)}  ww {ww(d)}")
            assert abs(b1[0] - XMIN) < 0.01 and abs(b1[3] - XMAX) < 0.01 and abs(b1[1] + YH) < 0.01 and abs(b1[4] - YH) < 0.01, b1
            assert all(abs(abs(v) - w) < 0.01 for v, w in zip(dims.values(), (75.0, 135.0, 290.0, 290.0))), dims
            cp = d.Extension.CustomPropertyManager(""); sp = cp.Get("SPEC"); assert spec_old in sp, (tag, sp[:80]); sp = sp.replace(spec_old, spec_new)
            if tag == "J1": sp = sp.replace("클램프형 샤프트 서포트 MISUMI SHFSS20 ×4로 고정", "제작 가이드 블록 J24a ×4(클램프식, 보어 Ø20 H7 × 40)로 고정")
            set_props(d, {"SPEC": sp, "DATE": DATE, "REMARK": (cp.Get("REMARK") or "") + f" / 09-21 외형 210×580 통일({extra}·상대 판과 동일 외형·동일 위치 — 사용자 지시), 구 파일 {os.path.basename(p_old)} 보존."})
            e = I4(); w = I4(); ok = d.Extension.SaveAs(p_new, 0, 1, NOD, e, w); print("  saved", os.path.basename(p_new), ok, e.value, w.value); assert ok
            rep[tag] = {"box": b1, "dims": dims, "dv": round(v1 - v0)}
    # ---------- 2. fabricated guide block J24a ----------
    if STAGE in ("all", "guide") and not os.path.exists(P_G):
        L_, YN, YP, HT = 60.0, -17.0, 23.0, 40.0            # X +-30, Y -17..+23 (slit side +Y = asm -x), Z 0..-40
        BORE, MNT, PITCH = 20.0, 7.0, 48.0; SLIT = 1.5; CB_Y = 16.5; CB_Z = -HT / 2
        for x in list(pv(app, "GetDocuments") or []):
            try:
                if x.GetType == 1 and not x.GetPathName and x.GetTitle.startswith(("파트", "Part")): app.CloseDoc(x.GetTitle); print("closed unsaved", x.GetTitle)
            except Exception: pass
        d = app.NewDocument(tmpl, 0, 0, 0); assert sel_plane(d, "정면"); d.SketchManager.InsertSketch(True); sm = d.SketchManager; sm.AddToDB = True
        r = [sm.CreateLine(mm(-L_ / 2), mm(YN), 0, mm(L_ / 2), mm(YN), 0), sm.CreateLine(mm(L_ / 2), mm(YN), 0, mm(L_ / 2), mm(YP), 0), sm.CreateLine(mm(L_ / 2), mm(YP), 0, mm(-L_ / 2), mm(YP), 0), sm.CreateLine(mm(-L_ / 2), mm(YP), 0, mm(-L_ / 2), mm(YN), 0)]
        cb = sm.CreateCircleByRadius(0, 0, 0, mm(BORE / 2)); c1 = sm.CreateCircleByRadius(mm(PITCH / 2), 0, 0, mm(MNT / 2)); c2 = sm.CreateCircleByRadius(mm(-PITCH / 2), 0, 0, mm(MNT / 2)); sm.AddToDB = False
        sp_ = lambda L: L.GetStartPoint2; ep_ = lambda L: L.GetEndPoint2
        rel(d, "sgHORIZONTAL2D", r[0]); rel(d, "sgVERTICAL2D", r[1]); rel(d, "sgHORIZONTAL2D", r[2]); rel(d, "sgVERTICAL2D", r[3])
        for i in range(4): rel(d, "sgMERGEPOINTS", ep_(r[i]), sp_(r[(i + 1) % 4]))
        rel_origin(d, "sgCONCENTRIC", cb) if False else rel_origin(d, "sgCOINCIDENT", cb.GetCenterPoint2)
        hl = sm.CreateLine(mm(-PITCH / 2), 0, 0, mm(PITCH / 2), 0, 0); hl.ConstructionGeometry = True; rel(d, "sgHORIZONTAL2D", hl)
        rel(d, "sgMERGEPOINTS", sp_(hl), c2.GetCenterPoint2); rel(d, "sgMERGEPOINTS", ep_(hl), c1.GetCenterPoint2); rel_origin(d, "sgCOINCIDENT", hl)
        g = {"길이_L": dim(d, "길이_L", r[0], None, (0, YN - 25)), "보어중심_취부쪽": dim(d, "보어중심_취부쪽", r[0], "origin", (-L_ / 2 - 25, YN / 2)),
             "보어중심_슬릿쪽": dim(d, "보어중심_슬릿쪽", r[2], "origin", (-L_ / 2 - 25, YP / 2)), "좌우대칭": dim(d, "좌우대칭", r[1], "origin", (L_ / 4, YP + 25)),
             "보어_H7": dim(d, "보어_H7", cb, None, (18, 18)), "취부구멍_M6용": dim(d, "취부구멍_M6용", c1, None, (PITCH / 2 + 12, -12)), "취부피치": dim(d, "취부피치", hl, None, (0, -8)), "취부구멍2_M6용": dim(d, "취부구멍2_M6용", c2, None, (-PITCH / 2 - 12, -12)), "취부_중심에서": dim(d, "취부_중심에서", c1.GetCenterPoint2, "origin", (PITCH / 4, 8), "h")}
        sk = d.SketchManager.ActiveSketch; st = sk.GetConstrainedStatus; print("  guide base sketch status", st, g)
        d.SketchManager.InsertSketch(True); d.ClearSelection2(True); skn = [n for n, t in feats(d) if t == "ProfileFeature"][-1]; d.FeatureByName(skn).Name = "블록_외형·보어·취부"
        okx = False
        for dirn in (False, True):
            d.ClearSelection2(True); assert d.Extension.SelectByID2("블록_외형·보어·취부", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
            f = d.FeatureManager.FeatureExtrusion3(True, False, dirn, 0, 0, mm(HT), 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False); d.EditRebuild3
            if f is None: continue
            bx = bbox(d); print("   extrude dirn", dirn, bx)
            if abs(bx[2] + HT) < 0.01 and abs(bx[5]) < 0.01: f.Name = "블록_H40"; okx = True; break
            f.Select2(False, 0); d.EditDelete(); d.EditRebuild3
        assert okx, "extrude dir"
        # slit (through all in Z), fully defined
        assert sel_plane(d, "정면"); d.SketchManager.InsertSketch(True); sm = d.SketchManager; sm.AddToDB = True; Y0 = 6.0; Y1 = YP + 3.0
        s = [sm.CreateLine(mm(-SLIT / 2), mm(Y0), 0, mm(SLIT / 2), mm(Y0), 0), sm.CreateLine(mm(SLIT / 2), mm(Y0), 0, mm(SLIT / 2), mm(Y1), 0), sm.CreateLine(mm(SLIT / 2), mm(Y1), 0, mm(-SLIT / 2), mm(Y1), 0), sm.CreateLine(mm(-SLIT / 2), mm(Y1), 0, mm(-SLIT / 2), mm(Y0), 0)]; sm.AddToDB = False
        rel(d, "sgHORIZONTAL2D", s[0]); rel(d, "sgVERTICAL2D", s[1]); rel(d, "sgHORIZONTAL2D", s[2]); rel(d, "sgVERTICAL2D", s[3])
        for i in range(4): rel(d, "sgMERGEPOINTS", ep_(s[i]), sp_(s[(i + 1) % 4]))
        g["슬릿폭"] = dim(d, "슬릿폭", s[0], None, (12, Y0 - 6)); g["슬릿_반폭"] = dim(d, "슬릿_반폭", s[1], "origin", (12, Y0 + 4)); g["슬릿_시작"] = dim(d, "슬릿_시작", s[0], "origin", (-14, Y0 / 2)); g["슬릿_끝"] = dim(d, "슬릿_끝", s[2], "origin", (-14, Y1 - 4))
        st2 = d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True)
        skn = [n for n, t in feats(d) if t == "ProfileFeature"][-1]; d.FeatureByName(skn).Name = "슬릿_스케치"; assert d.Extension.SelectByID2("슬릿_스케치", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
        v0 = volume(d); c = d.FeatureManager.FeatureCut4(False, False, False, 1, 1, 0.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False); d.EditRebuild3; assert c is not None; c.Name = "슬릿_1.5"
        print("  slit status", st2, "dv", round(v0 - volume(d)), "bodies", len(bodies(d)))
        # clamp bolt M5 along X at (Y 16.5, Z -20): clearance D5.5 on +X half, tap drill D4.2 on -X half (sketch on Right plane = YZ at X 0, inside the slit)
        def yz_circle(name, dia, flip, dname):
            assert sel_plane(d, "우측면"); d.SketchManager.InsertSketch(True); sk = d.SketchManager.ActiveSketch; sm = d.SketchManager
            a = list(sk.ModelToSketchTransform.ArrayData); R = [a[0:3], a[3:6], a[6:9]]; t = a[9:12]
            def S(px, py, pz): return [(R[0][i] * px + R[1][i] * py + R[2][i] * pz) + t[i] for i in range(3)][:2]
            q = S(0.0, mm(CB_Y), mm(CB_Z)); sm.AddToDB = True; ci = sm.CreateCircleByRadius(q[0], q[1], 0, mm(dia / 2)); sm.AddToDB = False
            o = S(0.0, 0.0, 0.0); ax = "h" if abs(S(0.0, 1.0, 0.0)[0] - o[0]) > 0.5 else "v"      # which sketch axis carries model Y
            d.ClearSelection2(True); ci.GetCenterPoint2.Select4(False, NOD); origin_sel(d, True); fn = d.AddHorizontalDimension2 if ax == "h" else d.AddVerticalDimension2
            dd = fn(q[0] + 0.02, q[1] + 0.02, 0.0); dd.GetDimension2(0).Name = dname + "_Y"; g[dname + "_Y"] = round(dd.GetDimension2(0).SystemValue * 1000, 3)
            d.ClearSelection2(True); ci.GetCenterPoint2.Select4(False, NOD); origin_sel(d, True); fn = d.AddVerticalDimension2 if ax == "h" else d.AddHorizontalDimension2
            dd = fn(q[0] - 0.02, q[1] - 0.02, 0.0); dd.GetDimension2(0).Name = dname + "_Z"; g[dname + "_Z"] = round(dd.GetDimension2(0).SystemValue * 1000, 3)
            g[dname + "_지름"] = dim(d, dname + "_지름", ci, None, (0, 0)); stx = sk.GetConstrainedStatus
            d.SketchManager.InsertSketch(True); d.ClearSelection2(True); skn = [n for n, t_ in feats(d) if t_ == "ProfileFeature"][-1]; d.FeatureByName(skn).Name = name + "_스케치"
            for fl in (flip, not flip):
                d.ClearSelection2(True); assert d.Extension.SelectByID2(name + "_스케치", "SKETCH", 0, 0, 0, False, 0, NOD, 0); v_ = volume(d)
                cf = d.FeatureManager.FeatureCut4(True, False, fl, 1, 0, 0.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False); d.EditRebuild3
                if cf is None: continue
                # verify side: probe material at X = +-15 on the hole axis by volume change sign only is ambiguous -> use face count on a section? simpler: check the body's bbox of the cut feature faces
                faces = [f_ for f_ in (pv(cf, "GetFaces") or [])]; xs_ = []
                for f_ in faces:
                    bb = pv(f_, "GetBox"); xs_ += [bb[0] * 1000, bb[3] * 1000]
                side = "+X" if max(xs_) > 1.0 else "-X"; print(f"   {name} flip={fl} faces x range {min(xs_):.1f}..{max(xs_):.1f} -> {side}, status {stx}, dv {round(v_ - volume(d))}")
                return cf, side, stx
            raise AssertionError(name)
        cf1, side1, s3 = yz_circle("클램프_관통_Ø5.5", 5.5, False, "관통")
        if side1 != "+X":
            cf1.Select2(False, 0); d.EditDelete(); d.EditRebuild3
            d.ClearSelection2(True); assert d.Extension.SelectByID2("클램프_관통_Ø5.5_스케치", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
            cf1 = d.FeatureManager.FeatureCut4(True, False, True, 1, 0, 0.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False); d.EditRebuild3; assert cf1 is not None
            xs_ = [v * 1000 for f_ in pv(cf1, "GetFaces") for v in (pv(f_, "GetBox")[0], pv(f_, "GetBox")[3])]; assert max(xs_) > 1.0, xs_
        cf1.Name = "클램프_관통_Ø5.5"
        cf2, side2, s4 = yz_circle("클램프_탭드릴_Ø4.2", 4.2, True, "탭")
        if side2 != "-X":
            cf2.Select2(False, 0); d.EditDelete(); d.EditRebuild3
            d.ClearSelection2(True); assert d.Extension.SelectByID2("클램프_탭드릴_Ø4.2_스케치", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
            cf2 = d.FeatureManager.FeatureCut4(True, False, False, 1, 0, 0.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False); d.EditRebuild3; assert cf2 is not None
            xs_ = [v * 1000 for f_ in pv(cf2, "GetFaces") for v in (pv(f_, "GetBox")[0], pv(f_, "GetBox")[3])]; assert min(xs_) < -1.0, xs_
        cf2.Name = "클램프_탭드릴_Ø4.2(M5)"
        bx = bbox(d); vol = volume(d); print("  guide final box", bx, "vol", round(vol), "statuses", st, st2, s3, s4, "ww", ww(d)); assert st == 3 and st2 == 3
        assert abs(bx[0] + 30) < 0.01 and abs(bx[3] - 30) < 0.01 and abs(bx[1] + 17) < 0.01 and abs(bx[4] - 23) < 0.01 and abs(bx[2] + 40) < 0.01 and abs(bx[5]) < 0.01, bx
        try: d.SetMaterialPropertyName2("", "이텍", "STS 304")
        except Exception as ex: print("  mat exc", ex)
        set_props(d, {"TITLE": "SHAFT GUIDE BLOCK (제작, 클램프식)", "SPEC": "STS304 블록 60×40×H40 절삭. 보어 Ø20 H7 관통(가이드 봉 J2d Ø20 g6 끼움, 물림 길이 40 — 구매품 SHFSS20의 20 대비 2배), 슬릿 1.5 + 클램프 볼트 M5×35(관통 Ø5.5 / 반대쪽 M5 탭, 드릴 Ø4.2) @보어 중심에서 슬릿 쪽 16.5·높이 중앙. 취부 2-Ø7 피치 48(M6×50, J1 고정판 밑면 기존 M6 탭 재사용). 자리파기는 모델 미표현(M5 머리 Ø9.5×5.4 가공 권장).", "Material": "STS304", "QT'Y": "4", "DATE": DATE,
                      "REMARK": "자작. 구매품 샤프트 홀더 J23d(MISUMI SHFSS20) ×4 대체 — 사용자 지시(가이드를 따로 제작, 4개). 좌표계·취부 피치는 J23d와 동일(평면 메이트 그대로 재부착)."})
        e = I4(); w = I4(); ok = d.Extension.SaveAs(P_G, 0, 1, NOD, e, w); print("  saved", os.path.basename(P_G), ok, e.value, w.value); assert ok
        rep["guide"] = {"box": bx, "vol": round(vol), "dims": g, "status": [st, st2, s3, s4]}; app.CloseDoc(d.GetTitle)
    # ---------- 3. replace J23d -> J24a in the line assembly ----------
    if STAGE in ("all", "replace"):
        a = activate(P_LINE); cm = a.ConfigurationManager
        root = cm.ActiveConfiguration.GetRootComponent3(True); old = [c for c in pv(root, "GetChildren") if c.Name2.startswith("J23d")]; print("replace", [c.Name2 for c in old])
        if old:
            a.ClearSelection2(True)
            for i, c in enumerate(old): c.Select4(i > 0, NOD, False)
            ok = a.ReplaceComponents2(P_G, "", True, 0, True); print("  ReplaceComponents2", ok); a.ClearSelection2(True)
        a.ForceRebuild3(False)
        f = pv(a, "FirstFeature")
        while f is not None:
            if pv(f, "GetTypeName2") == "MateGroup":
                sf = f.GetFirstSubFeature
                while sf is not None:
                    if "J23d" in sf.Name: sf.Name = sf.Name.replace("J23d", "J24a")
                    sf = sf.GetNextSubFeature
            f = pv(f, "GetNextFeature")
        res = {}
        for cfg in list(a.GetConfigurationNames):
            a.ShowConfiguration2(cfg); a.ForceRebuild3(False); root = a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
            kids = {c.Name2: box(c) for c in pv(root, "GetChildren") if c.Name2.startswith(("J24a", "J1d", "J5p", "J1c", "J5n", "J23d"))}
            a.ClearSelection2(True); idm = a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = True; idm.IncludeMultibodyPartInterferences = False; idm.MakeInterferingPartsTransparent = False
            itf = sorted([([c_.Name2[:24] for c_ in (pv(it, "Components") or [])], round(it.Volume * 1e9, 1)) for it in (pv(idm, "GetInterferences") or [])], key=lambda r_: -r_[1]); idm.Done(); a.ClearSelection2(True)
            res[cfg] = {"ww": ww(a), "interf": itf, "boxes": kids}; print(" cfg", cfg, "ww", ww(a), "interf", len(itf)); [print("     ", v, cs) for cs, v in itf[:10]]
        a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
        for n, b in res["상승"]["boxes"].items(): print("   ", n, b)
        rep["asm"] = res
finally:
    app.SetUserPreferenceToggle(10, old_pref)
json.dump(rep, open(os.path.join(VER, f"line_plates_guide_0921_{STAGE}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print("DONE", STAGE)
