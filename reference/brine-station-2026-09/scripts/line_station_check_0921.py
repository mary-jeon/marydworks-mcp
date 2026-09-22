# 2026-09-21 판 210x580 통일·제작 가이드 J24a 반영 후: 염수주입라인.SLDASM 저장 -> 스테이션 S00000MU0(읽기 전용)에서 라인<->외부 간섭(상승/하강). check_stroke150_station_0917.py 축약본. S00000은 저장하지 않음
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from swconn import *
from swpv import pv
Zp = lambda n: os.path.join(Z, n); rep = {}
app = connect()
LINE = ("B9k", "J25a", "J8g", "J9f", "G11f", "J11e", "G3e", "B4e", "G13f", "G13g", "H16d", "J19n", "J5p", "J1d", "J2d", "B10b", "F4")
a = app.GetOpenDocumentByName(ASM); app.ActivateDoc3(ASM, False, 0, I4()); a = app.ActiveDoc; a.ShowConfiguration2("상승"); a.ForceRebuild3(False)
if a.GetSaveFlag:
    e = I4(); w = I4(); ok = a.Save3(1, e, w); print("saved 염수주입라인.SLDASM", ok, e.value, w.value); assert ok
PS = Zp("S00000MU0.SLDASM"); s = app.GetOpenDocumentByName(PS) or open_doc(app, PS, 2, True); app.ActivateDoc3(PS, False, 0, I4()); s = app.ActiveDoc; scm = s.ConfigurationManager
print("station readonly", s.IsOpenedReadOnly, "cfgs", list(pv(s, "GetConfigurationNames")))
cfg0 = scm.ActiveConfiguration.Name
for cfg in ("상승", "하강"):
    if cfg not in list(pv(s, "GetConfigurationNames")): print("no cfg", cfg); continue
    s.ShowConfiguration2(cfg); s.ForceRebuild3(False); out = []
    def walk(c, depth):
        for ch in (pv(c, "GetChildren") or []):
            if ch.GetSuppression2 != 2: continue
            out.append((ch.Name2, ch))
            if depth < 6: walk(ch, depth + 1)
    walk(scm.ActiveConfiguration.GetRootComponent3(True), 0)
    line = [(n, c) for n, c in out if n.split("/")[-1].startswith(LINE)]
    others = [(n, c) for n, c in out if not n.split("/")[-1].startswith(LINE) and pv(c, "GetChildren") in (None, ()) ]
    print(f"[station {cfg}] line parts {len(line)} other leaf parts {len(others)}")
    s.ClearSelection2(True)
    for n, c in line + others: c.Select4(True, NOD, False)
    idm = s.InterferenceDetectionManager; idm.TreatCoincidenceAsInterference = False; idm.TreatSubAssembliesAsComponents = False; idm.IncludeMultibodyPartInterferences = False; idm.MakeInterferingPartsTransparent = False
    rows = [([c_.Name2.split("/")[-1] for c_ in (pv(it, "Components") or [])], round(it.Volume * 1e9, 1)) for it in (pv(idm, "GetInterferences") or [])]; idm.Done(); s.ClearSelection2(True)
    ext = [r for r in rows if any(x.startswith(LINE) for x in r[0]) and not all(x.startswith(LINE) for x in r[0])]
    newp = [r for r in rows if any(x.startswith(("J1d", "J5p", "J25a")) for x in r[0])]
    print(f"[station {cfg}] all {len(rows)} | line<->external {len(ext)}: {ext[:10]} | involving J1d/J5p/J25a: {newp}")
    wb = {n.split('/')[-1]: box(c) for n, c in line if n.split('/')[-1].startswith(("J1d", "J5p", "J25a"))}
    for k, v in wb.items(): print("    ", k, v)
    rep[cfg] = {"ext": ext, "new_parts": newp, "boxes": wb, "all": len(rows)}
s.ShowConfiguration2(cfg0)
json.dump(rep, open(os.path.join(VER, "line_station_check_0921.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str); print("DONE")
