import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
DRY = '--apply' not in sys.argv
app = api.get_app(); sel = DocSelector(path=os.path.join(D,'S20000MU0.SLDASM')); am,_ = resolve(app, sel); a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
comps = {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}

def faces_of(name):
    c = comps[name]; T = list(api.cast('IMathTransform', c.Transform2).ArrayData); R = [T[0:3], T[3:6], T[6:9]]; t = T[9:12]
    body = api.cast('IBody2', c.GetBody()); out = []
    for f in body.GetFaces() or []:
        f = api.cast('IFace2', f); s = api.cast('ISurface', f.GetSurface())
        if not s.IsPlane(): continue
        n = list(f.Normal); n_asm = [sum(n[k]*R[k][i] for k in range(3)) for i in range(3)]  # row-vector * R
        b = list(f.GetBox()); corners = [(b[i], b[j], b[k]) for i in (0,3) for j in (1,4) for k in (2,5)]
        pts = [[sum(p[k]*R[k][i] for k in range(3)) + t[i] for i in range(3)] for p in corners]
        cen = [sum(p[i] for p in pts)/8*1000 for i in range(3)]
        out.append({'face': f, 'n': [round(v,2) for v in n_asm], 'c': [round(v,1) for v in cen]})
    return out
def pick(name, n, axis, val, tol=1.0):
    for fd in faces_of(name):
        if fd['n'] == n and abs(fd['c'][axis]-val) < tol: return fd
    raise RuntimeError(f'{name}: face n={n} {"xyz"[axis]}={val} not found; have ' + str([(f['n'], f['c']) for f in faces_of(name)][:12]))
sm_ = api.cast('ISelectionMgr', am.SelectionManager)
def mate(fa, fb, label):
    am.ClearSelection2(True); sd = api.cast('ISelectData', sm_.CreateSelectData()); sd.Mark = 1
    api.cast('IEntity', fa['face']).Select4(False, sd); api.cast('IEntity', fb['face']).Select4(True, sd)
    if DRY: print(f'  [dry] {label}: {fa["n"]}@{fa["c"]} <-> {fb["n"]}@{fb["c"]}'); return True
    r = a.AddMate5(0, 2, False, 0, 0, 0, 0, 0, 0, 0, 0, False, False, 0)
    m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    print(f'  {label}: mate={api.cast("IFeature", m).Name if m else None} err={err}'); return m is not None and err == 1  # swAddMateError_NoError = 1
PLAN = {
 'S20010MU0-3': [('bottom', (0,-1,0), 1, 1953.2, 'S20007MU0-1', (0,1,0), 1, 1953.2), ('outer', (1,0,0), 0, 300, 'S20002MU0-3', (-1,0,0), 0, 300), ('front', (0,0,-1), 2, 980, 'S20007MU0-1', (0,0,-1), 2, 980)],
 'S20010MU0-4': [('bottom', (0,-1,0), 1, 1953.2, 'S20007MU0-1', (0,1,0), 1, 1953.2), ('outer', (-1,0,0), 0, -300, 'S20002MU0-5', (1,0,0), 0, -300), ('front', (0,0,-1), 2, 980, 'S20007MU0-1', (0,0,-1), 2, 980)],
 'S20011MU0-2': [('bottom', (0,-1,0), 1, 1953.2, 'S20007MU0-1', (0,1,0), 1, 1953.2), ('rear', (0,0,1), 2, 2180, 'S20007MU0-1', (0,0,1), 2, 2180), ('end', (1,0,0), 0, 295.5, 'S20010MU0-3', (-1,0,0), 0, 295.5)],
 'S20003MU0-18': [('top', (0,1,0), 1, 1913.2, 'S20007MU0-1', (0,-1,0), 1, 1913.2), ('inner', (-1,0,0), 0, 300, 'S20007MU0-1', (1,0,0), 0, 300), ('end', (0,0,-1), 2, 1055, 'S20002MU0-4', (0,0,1), 2, 1055)],
 'S20003MU0-17': [('top', (0,1,0), 1, 1913.2, 'S20007MU0-1', (0,-1,0), 1, 1913.2), ('inner', (1,0,0), 0, -300, 'S20007MU0-1', (-1,0,0), 0, -300), ('end', (0,0,-1), 2, 1055, 'S20002MU0-6', (0,0,1), 2, 1055)],
}
ok_all = True
for comp, rules in PLAN.items():
    print('==', comp)
    for label, n1, ax1, v1, other, n2, ax2, v2 in rules:
        try:
            fa = pick(comp, list(n1), ax1, v1); fb = pick(other, list(n2), ax2, v2)
        except RuntimeError as e:
            print('  FACE MISSING:', str(e)[:300]); ok_all = False; continue
        ok_all &= mate(fa, fb, f'{label} <-> {other}')
    if not DRY and ok_all:
        am.ClearSelection2(True); comps[comp].Select4(False, None, False); a.UnfixComponent(); print('  unfixed', comp)
if not DRY:
    am.ClearSelection2(True); am.ForceRebuild3(False)
    bad = []; f = api.cast('IFeature', am.FirstFeature())
    while f:
        if f.GetTypeName2() == 'MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s:
                e = s.GetErrorCode2(True); e = e[0] if isinstance(e, tuple) else e
                if int(e) != 0: bad.append((s.Name, int(e)))
                s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    print('rebuild 오류', aext.GetWhatsWrongCount(), '| 메이트 오류:', bad or '없음')
    for name in PLAN:
        bb = [round(v*1000,1) for v in comps[name].GetBox(False, False)]; print(f'  {name}: X{bb[0]}..{bb[3]} Y{bb[1]}..{bb[4]} Z{bb[2]}..{bb[5]}')
print('ALL OK' if ok_all else 'PROBLEMS')
