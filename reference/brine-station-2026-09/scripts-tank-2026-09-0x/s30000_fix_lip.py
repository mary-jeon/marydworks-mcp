import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); sel = DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')); am,_ = resolve(app, sel); a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
C = {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
def faces_of(c):
    T = list(api.cast('IMathTransform', c.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]; out=[]
    for f in api.cast('IBody2', c.GetBody()).GetFaces() or []:
        f = api.cast('IFace2', f); s = api.cast('ISurface', f.GetSurface())
        if not s.IsPlane(): continue
        n = list(f.Normal); n=[round(sum(n[k]*R[k][i] for k in range(3)),2) for i in range(3)]
        b = list(f.GetBox()); pts=[[sum(p[k]*R[k][i] for k in range(3))+t[i] for i in range(3)] for p in [(b[i],b[j],b[k]) for i in (0,3) for j in (1,4) for k in (2,5)]]
        cen=[round(sum(p[i] for p in pts)/8*1000,1) for i in range(3)]; out.append({'face':f,'n':n,'c':cen,'A':round(f.GetArea()*1e6)})
    return out
def pick(c, n, axis, val, tol=1.5):
    hits=[fd for fd in faces_of(c) if fd['n']==n and abs(fd['c'][axis]-val)<tol]
    if not hits: raise RuntimeError(f'{c.Name2}: n={n} {"xyz"[axis]}={val} not found; have {[(f["n"],f["c"],f["A"]) for f in faces_of(c) if f["n"]==n][:8]}')
    return max(hits, key=lambda f: f['A'])
smgr = api.cast('ISelectionMgr', am.SelectionManager)
def mate_faces(fa, fb, label, align=2):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fa['face']).Select4(False, sd); api.cast('IEntity', fb['face']).Select4(True, sd)
    r = a.AddMate5(0, align, False, 0,0,0,0,0,0,0,0, False, False, 0); m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    print(f'  {label}: {"OK" if m is not None and err==1 else "FAIL err=%s"%err}'); return m
def delete_mates(names):
    for nm in names:
        am.ClearSelection2(True); ok = aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0); d = aext.DeleteSelection2(0) if ok else False; print(f'  delete {nm}: sel={ok} del={d}')
def errors():
    am.ForceRebuild3(False); return aext.GetWhatsWrongCount()
wall = C['S30002MU0-1']; cone = C['S30001MU0-1']; lid = C['S30006MU0-1']
print('lip faces of cone-1 (n=+Y):', [(f['c'], f['A']) for f in faces_of(cone) if f['n']==[0,1,0]])
delete_mates(['일치52']); print('errors after delete:', errors())
wall_bot = pick(wall, [0,-1,0], 1, 30, tol=6); lip_top = pick(cone, [0,1,0], 1, 35, tol=1.5)
print('  wall_bot', wall_bot['c'], wall_bot['A'], '| lip_top', lip_top['c'], lip_top['A'])
mate_faces(wall_bot, lip_top, '벽 바닥↔립 윗면'); print('errors:', errors())
for n in ['S30002MU0-1','S30006MU0-1','S30008MU0-1','S30001MU0-1']:
    b = C[n].GetBox(False, False); print(f'{n:14s} Y {b[1]*1000:7.1f}..{b[4]*1000:7.1f}')
r = aext.GetWhatsWrong()
if r and r[1]: print('  whats wrong:', [(api.cast('IFeature', f).Name, c) for f, c in zip(r[1], r[2])])
