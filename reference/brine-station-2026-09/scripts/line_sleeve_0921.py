# 2026-09-21 (가)안: 봉은 고정, 잡는 부품을 네모 클램프 블록 J24a -> 플랜지 달린 원통 슬리브 J25a x4 (제작, 리니어 부시와 같은 모양: 플랜지 D54 T8, 몸통 D32, PCD 43 4-D5.5)
#   고정판 J1d: 구 M6 탭 8개(피치 48) 삭제 -> M5 탭 16개(PCD 43, 이동판 J5p 부시 취부와 같은 배치) 새 스케치(완전 정의)+컷
# usage: line_sleeve_0921.py sleeve | plate | replace
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pythoncom
from win32com.client import VARIANT
from swconn import *
from swpv import pv
STAGE = sys.argv[1]; mm = lambda v: v / 1000.0; Zp = lambda n: os.path.join(Z, n); DATE = "2026-09-21"; rep = {"stage": STAGE}
P_J1 = Zp("J1d_fixed_plate_210x580_t10.SLDPRT"); P_S = Zp("J25a_shaft_sleeve_flanged_fab_D54xL50.SLDPRT")
FL_D, FL_T, BODY_D, LEN, BORE, PCD, MNT = 54.0, 8.0, 32.0, 50.0, 20.0, 43.0, 5.5
SET_Z = -(FL_T + (LEN - FL_T) / 2); SET_D = 4.2          # M5 set screws x2 (90 deg apart) at mid body
SHAFTS = [(0.0, 240.0), (0.0, -240.0), (90.0, 240.0), (90.0, -240.0)]; TAP_D = 4.2
app = connect(); tmpl = app.GetUserPreferenceStringValue(8)
def ww(doc):
    fe = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None); co = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None); wa = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_VARIANT, None)
    doc.Extension.GetWhatsWrong(fe, co, wa); return [(f.Name, c) for f, c in zip(fe.value or [], co.value or [])]
def feats(d):
    out = []; f = pv(d, "FirstFeature")
    while f is not None: out.append((f.Name, pv(f, "GetTypeName2"))); f = pv(f, "GetNextFeature")
    return out
def last_sketch(d): return [n for n, t in feats(d) if t == "ProfileFeature"][-1]
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
def rel_o(d, kind, e):
    d.ClearSelection2(True); assert e.Select4(False, NOD); assert origin_sel(d, True); d.SketchAddConstraints(kind); d.ClearSelection2(True)
def dim(d, name, e1, e2, at, how="d"):
    d.ClearSelection2(True); assert e1.Select4(False, NOD)
    if e2 == "origin": assert origin_sel(d, True)
    elif e2 is not None: assert e2.Select4(True, NOD)
    fn = {"d": d.AddDimension2, "h": d.AddHorizontalDimension2, "v": d.AddVerticalDimension2}[how]
    dd = fn(at[0], at[1], 0.0); d.ClearSelection2(True); assert dd is not None, name
    dm = dd.GetDimension2(0); dm.Name = name; return round(dm.SystemValue * 1000, 3)
def set_props(d, props):
    cp = d.Extension.CustomPropertyManager("")
    for k, v in props.items():
        if cp.Get(k): cp.Set2(k, v)
        else: cp.Add3(k, 30, v, 1)
def extrude_negz(d, skname, depth, fname, merge=True):
    for dirn in (False, True):
        d.ClearSelection2(True); assert d.Extension.SelectByID2(skname, "SKETCH", 0, 0, 0, False, 0, NOD, 0); z0 = [round(v * 1000, 2) for b in bodies(d) for v in (pv(b, "GetBodyBox")[2],)]
        f = d.FeatureManager.FeatureExtrusion3(True, False, dirn, 0, 0, mm(depth), 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, merge, True, True, 0, 0.0, False); d.EditRebuild3
        if f is None: continue
        bx = bbox(d)
        if abs(bx[5]) < 0.01 and abs(bx[2] + depth) < 0.01 or (z0 and abs(bx[5]) < 0.01 and bx[2] <= -depth + 0.01): f.Name = fname; return f
        f.Select2(False, 0); d.EditDelete(); d.EditRebuild3
    raise AssertionError(fname)
def sk_map(sk):
    a = list(sk.ModelToSketchTransform.ArrayData); R = [a[0:3], a[3:6], a[6:9]]; t = a[9:12]
    return lambda px, py, pz: [(R[0][i] * px + R[1][i] * py + R[2][i] * pz) + t[i] for i in range(3)][:2]

old_pref = app.GetUserPreferenceToggle(10); app.SetUserPreferenceToggle(10, False)
try:
    # ---------- 1. flanged sleeve J25a ----------
    if STAGE == "sleeve" and not os.path.exists(P_S):
        for x in list(pv(app, "GetDocuments") or []):
            try:
                if x.GetType == 1 and not x.GetPathName: app.CloseDoc(x.GetTitle); print("closed unsaved", x.GetTitle)
            except Exception: pass
        d = app.NewDocument(tmpl, 0, 0, 0); g = {}
        assert sel_plane(d, "정면"); d.SketchManager.InsertSketch(True); sm = d.SketchManager; sm.AddToDB = True
        co = sm.CreateCircleByRadius(0, 0, 0, mm(FL_D / 2)); cb = sm.CreateCircleByRadius(0, 0, 0, mm(BORE / 2)); r = PCD / 2
        hl = sm.CreateLine(mm(-r), 0, 0, mm(r), 0, 0); vl = sm.CreateLine(0, mm(-r), 0, 0, mm(r), 0); hl.ConstructionGeometry = True; vl.ConstructionGeometry = True
        hs = [sm.CreateCircleByRadius(mm(x), mm(y), 0, mm(MNT / 2)) for x, y in ((r, 0), (-r, 0), (0, r), (0, -r))]; sm.AddToDB = False
        rel_o(d, "sgCOINCIDENT", co.GetCenterPoint2); rel_o(d, "sgCOINCIDENT", cb.GetCenterPoint2)
        rel(d, "sgHORIZONTAL2D", hl); rel(d, "sgVERTICAL2D", vl); rel_o(d, "sgATMIDDLE", hl); rel_o(d, "sgATMIDDLE", vl); rel(d, "sgSAMELENGTH", hl, vl)
        rel(d, "sgMERGEPOINTS", hl.GetEndPoint2, hs[0].GetCenterPoint2); rel(d, "sgMERGEPOINTS", hl.GetStartPoint2, hs[1].GetCenterPoint2); rel(d, "sgMERGEPOINTS", vl.GetEndPoint2, hs[2].GetCenterPoint2); rel(d, "sgMERGEPOINTS", vl.GetStartPoint2, hs[3].GetCenterPoint2)
        for h in hs[1:]: rel(d, "sgSAMELENGTH", hs[0], h)
        g["플랜지_외경"] = dim(d, "플랜지_외경", co, None, (mm(30), mm(30))); g["보어_H7"] = dim(d, "보어_H7", cb, None, (mm(-14), mm(14))); g["취부_PCD"] = dim(d, "취부_PCD", hl, None, (0, mm(-6))); g["취부구멍_M5용"] = dim(d, "취부구멍_M5용", hs[0], None, (mm(r + 8), mm(8)))
        st1 = d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.FeatureByName(last_sketch(d)).Name = "플랜지_스케치"
        extrude_negz(d, "플랜지_스케치", FL_T, "플랜지_Ø54_T8")
        assert sel_plane(d, "정면"); d.SketchManager.InsertSketch(True); sm = d.SketchManager; sm.AddToDB = True
        bo = sm.CreateCircleByRadius(0, 0, 0, mm(BODY_D / 2)); bi = sm.CreateCircleByRadius(0, 0, 0, mm(BORE / 2)); sm.AddToDB = False
        rel_o(d, "sgCOINCIDENT", bo.GetCenterPoint2); rel_o(d, "sgCOINCIDENT", bi.GetCenterPoint2)
        g["몸통_외경"] = dim(d, "몸통_외경", bo, None, (mm(20), mm(20))); g["몸통_보어"] = dim(d, "몸통_보어", bi, None, (mm(-12), mm(12)))
        st2 = d.SketchManager.ActiveSketch.GetConstrainedStatus; d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.FeatureByName(last_sketch(d)).Name = "몸통_스케치"
        extrude_negz(d, "몸통_스케치", LEN, "몸통_Ø32_L50")
        bx = bbox(d); assert abs(bx[2] + LEN) < 0.01 and abs(bx[5]) < 0.01 and abs(bx[3] - FL_D / 2) < 0.01, bx
        # set screw tap drills: +X (sketch on Right plane) and +Y (sketch on Top plane), from mid-plane outward through one wall
        sts = []
        for plane, axis, tag in (("우측면", 0, "X"), ("윗면", 1, "Y")):
            assert sel_plane(d, plane); d.SketchManager.InsertSketch(True); sk = d.SketchManager.ActiveSketch; S = sk_map(sk); sm = d.SketchManager
            q = S(0.0, 0.0, mm(SET_Z)); sm.AddToDB = True; ci = sm.CreateCircleByRadius(q[0], q[1], 0, mm(SET_D / 2)); sm.AddToDB = False
            o = S(0.0, 0.0, 0.0); zdir_h = abs(S(0.0, 0.0, 1.0)[0] - o[0]) > 0.5      # model Z along sketch horizontal?
            # centre sits on the bore axis: horizontal/vertical alignment with origin + distance along Z
            d.ClearSelection2(True); ci.GetCenterPoint2.Select4(False, NOD); origin_sel(d, True); d.SketchAddConstraints("sgHORIZONTALPOINTS2D" if zdir_h else "sgVERTICALPOINTS2D"); d.ClearSelection2(True)
            g[f"세트스크류{tag}_높이"] = dim(d, f"세트스크류{tag}_높이", ci.GetCenterPoint2, "origin", (q[0] + 0.015, q[1] + 0.015), "d")
            g[f"세트스크류{tag}_드릴"] = dim(d, f"세트스크류{tag}_드릴", ci, None, (q[0] - 0.01, q[1] - 0.01)); stx = sk.GetConstrainedStatus
            if stx != 3:      # alignment relation name not accepted -> pin with a second dimension is impossible (0 distance); report
                print("   set screw sketch status", stx, tag)
            d.SketchManager.InsertSketch(True); d.ClearSelection2(True); skn = f"세트스크류{tag}_스케치"; d.FeatureByName(last_sketch(d)).Name = skn; okc = False
            for fl in (False, True):
                d.ClearSelection2(True); assert d.Extension.SelectByID2(skn, "SKETCH", 0, 0, 0, False, 0, NOD, 0); v_ = volume(d)
                cf = d.FeatureManager.FeatureCut4(True, False, fl, 1, 0, 0.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False); d.EditRebuild3
                if cf is None: continue
                vals = [pv(f_, "GetBox")[axis + 3] * 1000 for f_ in (pv(cf, "GetFaces") or [])] + [pv(f_, "GetBox")[axis] * 1000 for f_ in (pv(cf, "GetFaces") or [])]
                if vals and min(vals) > -1.0 and max(vals) > 5.0: cf.Name = f"세트스크류{tag}_M5탭드릴"; okc = True; print(f"   set screw {tag}: flip {fl} range {min(vals):.1f}..{max(vals):.1f} dv {round(v_ - volume(d))} status {stx}"); break
                cf.Select2(False, 0); d.EditDelete(); d.EditRebuild3
            assert okc, tag; sts.append(stx)
        vol = volume(d); calc = math.pi / 4 * ((FL_D ** 2 - BORE ** 2) * FL_T + (BODY_D ** 2 - BORE ** 2) * (LEN - FL_T) - 4 * MNT ** 2 * FL_T) - 2 * math.pi / 4 * SET_D ** 2 * (BODY_D - BORE) / 2
        print("  sleeve box", bbox(d), "vol", round(vol), "hand calc ~", round(calc), "statuses", st1, st2, sts, "ww", ww(d)); assert st1 == 3 and st2 == 3
        try: d.SetMaterialPropertyName2("", "이텍", "STS 304")
        except Exception as ex: print("  mat exc", ex)
        set_props(d, {"TITLE": "SHAFT SLEEVE, FLANGED (제작)", "SPEC": "STS304 선삭: 플랜지 Ø54×T8 + 몸통 Ø32, 전장 50. 보어 Ø20 H7 관통(가이드 봉 J2d Ø20 g6 끼움, 물림 길이 50 — 구매품 SHFSS20의 20 대비 2.5배). 취부 4-Ø5.5 PCD 43(0°/90°) = 리니어 부시 LHFRW20과 같은 배치, M5×16 볼트로 고정판 J1d 밑면 M5 탭에 고정. 봉 고정 = M5 세트스크류 2개(90° 간격, 몸통 중앙, 드릴 Ø4.2) — 봉에 자국이 남으니 놋쇠 팁 또는 봉 D컷 권장.", "Material": "STS304", "QT'Y": "4", "DATE": DATE,
                      "REMARK": "자작. 네모 클램프 블록 J24a(같은 날 오전안)·구매 홀더 J23d 대체 — 사용자 지시(위에도 부시처럼 봉을 감싸는 샤프트 커버, 봉은 고정). 좌표계: 취부면 Z 0, 몸통 −Z."})
        e = I4(); w = I4(); ok = d.Extension.SaveAs(P_S, 0, 1, NOD, e, w); print("  saved", os.path.basename(P_S), ok, e.value, w.value); assert ok
        rep["sleeve"] = {"dims": g, "vol": round(vol), "calc": round(calc), "status": [st1, st2] + sts}; app.CloseDoc(d.GetTitle)
    # ---------- 2. fixed plate: drop 8 M6 taps, add 16 M5 taps (PCD 43) ----------
    if STAGE == "plate":
        app.ActivateDoc3(P_J1, False, 0, I4()); d = app.ActiveDoc; assert d.GetTitle.startswith("J1d"); v0 = volume(d)
        if d.FeatureByName("탭_M5_PCD43") is None:
            d.ClearSelection2(True); assert d.Extension.SelectByID2("스케치3", "SKETCH", 0, 0, 0, False, 0, NOD, 0); d.EditSketch(); sk = d.SketchManager.ActiveSketch
            oldc = [s for s in sk.GetSketchSegments if s.GetType == 1 and abs(s.GetRadius * 1000 - 2.5) < 0.01]; print("  old M6 tap circles", len(oldc)); assert len(oldc) == 8
            d.ClearSelection2(True)
            for i, s in enumerate(oldc): s.Select4(i > 0, NOD)
            d.EditDelete(); d.SketchManager.InsertSketch(True); d.EditRebuild3; v1 = volume(d); print("  removed old taps, dv", round(v1 - v0), "(expect +", round(8 * math.pi * 2.5 ** 2 * 10), ")")
            assert sel_plane(d, "정면"); d.SketchManager.InsertSketch(True); sm = d.SketchManager; r = PCD / 2; first = None; g = {}
            for k, (cx, cy) in enumerate(SHAFTS, 1):
                sm.AddToDB = True
                hl = sm.CreateLine(mm(cx - r), mm(cy), 0, mm(cx + r), mm(cy), 0); vl = sm.CreateLine(mm(cx), mm(cy - r), 0, mm(cx), mm(cy + r), 0); hl.ConstructionGeometry = True; vl.ConstructionGeometry = True
                cs = [sm.CreateCircleByRadius(mm(x), mm(y), 0, mm(TAP_D / 2)) for x, y in ((cx + r, cy), (cx - r, cy), (cx, cy + r), (cx, cy - r))]; sm.AddToDB = False
                rel(d, "sgHORIZONTAL2D", hl); rel(d, "sgVERTICAL2D", vl); rel(d, "sgSAMELENGTH", hl, vl)
                # the two lines cross at their midpoints = shaft centre
                rel(d, "sgATMIDDLE", hl, vl) if False else None
                mp = sm.CreatePoint(mm(cx), mm(cy), 0); rel(d, "sgATMIDDLE", mp, hl); rel(d, "sgATMIDDLE", mp, vl)
                rel(d, "sgMERGEPOINTS", hl.GetEndPoint2, cs[0].GetCenterPoint2); rel(d, "sgMERGEPOINTS", hl.GetStartPoint2, cs[1].GetCenterPoint2); rel(d, "sgMERGEPOINTS", vl.GetEndPoint2, cs[2].GetCenterPoint2); rel(d, "sgMERGEPOINTS", vl.GetStartPoint2, cs[3].GetCenterPoint2)
                if first is None: first = (hl, cs[0]); g["PCD"] = dim(d, "탭_PCD", hl, None, (mm(cx), mm(cy - 8))); g["드릴"] = dim(d, "탭드릴_M5", cs[0], None, (mm(cx + r + 10), mm(cy + 10)))
                else: rel(d, "sgSAMELENGTH", first[0], hl)
                for c in cs:
                    if c is not first[1]: rel(d, "sgSAMELENGTH", first[1], c)
                g[f"봉{k}_Y"] = dim(d, f"봉{k}_Y", mp, "origin", (mm(cx - 45), mm(cy / 2)), "v")
                if abs(cx) > 1e-9: g[f"봉{k}_X"] = dim(d, f"봉{k}_X", mp, "origin", (mm(cx / 2), mm(cy + (35 if cy > 0 else -35))), "h")
                else:
                    d.ClearSelection2(True); mp.Select4(False, NOD); origin_sel(d, True); d.SketchAddConstraints("sgVERTICALPOINTS2D"); d.ClearSelection2(True)
            st = d.SketchManager.ActiveSketch.GetConstrainedStatus; print("  tap sketch status", st, g)
            d.SketchManager.InsertSketch(True); d.ClearSelection2(True); d.FeatureByName(last_sketch(d)).Name = "탭_M5_PCD43_스케치"
            assert d.Extension.SelectByID2("탭_M5_PCD43_스케치", "SKETCH", 0, 0, 0, False, 0, NOD, 0)
            cf = d.FeatureManager.FeatureCut4(False, False, False, 1, 1, 0.0, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, False, True, True, False, False, False, 0, 0.0, False, False); d.EditRebuild3; assert cf is not None; cf.Name = "탭_M5_PCD43"
            v2 = volume(d); print("  new taps dv", round(v1 - v2), "(expect", round(16 * math.pi * (TAP_D / 2) ** 2 * 10), ") ww", ww(d)); assert st == 3, st
            assert abs((v1 - v2) - 16 * math.pi * (TAP_D / 2) ** 2 * 10) < 5
            cp = d.Extension.CustomPropertyManager(""); sp = cp.Get("SPEC")
            sp = sp.replace("제작 가이드 블록 J24a ×4(클램프식, 보어 Ø20 H7 × 40)로 고정", "제작 플랜지 슬리브 J25a ×4(보어 Ø20 H7 × 50, M5 세트스크류 2)로 고정")
            set_props(d, {"SPEC": sp + " [09-21 저녁] 슬리브 취부 M5 탭 16개(PCD 43, 0°/90°, 드릴 Ø4.2) @(0|90, ±240) — 구 M6 탭 8개(피치 48)는 삭제.", "DATE": DATE})
            e = I4(); w = I4(); assert d.Save3(1, e, w); print("  saved J1d", e.value, w.value); rep["plate"] = {"dims": g, "status": st}
    # ---------- 3. replace J24a -> J25a ----------
    if STAGE == "replace":
        app.ActivateDoc3(ASM, False, 0, I4()); a = app.ActiveDoc; root = a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
        old = [c for c in pv(root, "GetChildren") if c.Name2.startswith("J24a")]; print("replace", [c.Name2 for c in old])
        if old:
            a.ClearSelection2(True)
            for i, c in enumerate(old): c.Select4(i > 0, NOD, False)
            print("  ReplaceComponents2", a.ReplaceComponents2(P_S, "", True, 0, True)); a.ClearSelection2(True)
        a.ForceRebuild3(False); f = pv(a, "FirstFeature")
        while f is not None:
            if pv(f, "GetTypeName2") == "MateGroup":
                sf = f.GetFirstSubFeature
                while sf is not None:
                    if "J24a" in sf.Name: sf.Name = sf.Name.replace("J24a", "J25a")
                    sf = sf.GetNextSubFeature
            f = pv(f, "GetNextFeature")
        res = {}
        for cfg in list(a.GetConfigurationNames):
            a.ShowConfiguration2(cfg); a.ForceRebuild3(False); root = a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True); kids = list(pv(root, "GetChildren"))
            fixed = [c.Name2 for c in kids if c.IsFixed]
            a.ClearSelection2(True); idm = a.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = True; idm.IncludeMultibodyPartInterferences = False; idm.MakeInterferingPartsTransparent = False
            itf = sorted([([c_.Name2[:22] for c_ in (pv(it, "Components") or [])], round(it.Volume * 1e9, 1)) for it in (pv(idm, "GetInterferences") or [])], key=lambda r_: -r_[1]); idm.Done(); a.ClearSelection2(True)
            new = [x for x in itf if any(n.startswith(("J25a", "J1d", "J5p", "J2d")) for n in x[0])]
            res[cfg] = {"ww": ww(a), "interf": itf, "new": new, "fixed": fixed}; print(" cfg", cfg, "ww", ww(a), "interf", len(itf), "| involving J25a/J1d/J5p/J2d:", new, "| fixed comps:", fixed)
        a.ShowConfiguration2("상승"); a.ForceRebuild3(False); root = a.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
        for c in pv(root, "GetChildren"):
            if c.Name2.startswith("J25a"): print("   ", c.Name2, box(c))
        e = I4(); w = I4(); assert a.Save3(1, e, w); print("saved line asm", e.value, w.value); rep["asm"] = res
finally:
    app.SetUserPreferenceToggle(10, old_pref)
json.dump(rep, open(os.path.join(VER, f"line_sleeve_0921_{STAGE}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str); print("DONE", STAGE)
