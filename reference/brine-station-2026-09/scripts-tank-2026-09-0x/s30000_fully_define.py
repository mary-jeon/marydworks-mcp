import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
C = {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
def status(n): return C[n].GetConstrainedStatus()
def box(n):
    b = C[n].GetBox(False, False); return [round(v*1000,1) for v in b]
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
    return max(hits, key=lambda f: f['A']) if hits else None
def last_mate_name():
    f = api.cast('IFeature', am.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s: last=s.Name; s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def delete_mate(nm):
    am.ClearSelection2(True); ok = aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0)
    return aext.DeleteSelection2(0) if ok else False
def add_plane_mate(comp, plane):
    am.ClearSelection2(True)
    ok1 = aext.SelectByID2(f'{plane}@{comp}@S30000MU0', 'PLANE', 0,0,0, False, 1, None, 0)
    ok2 = aext.SelectByID2(plane, 'PLANE', 0,0,0, True, 1, None, 0)
    if not (ok1 and ok2): return False, f'sel {ok1},{ok2}'
    r = a.AddMate5(0, 2, False, 0,0,0,0,0,0,0,0, False, False, 0); m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    return (m is not None and err==1), f'err={err}'
def add_face_mate(fa, fb):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fa['face']).Select4(False, sd); api.cast('IEntity', fb['face']).Select4(True, sd)
    r = a.AddMate5(0, 2, False, 0,0,0,0,0,0,0,0, False, False, 0); m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    return (m is not None and err==1), f'err={err}'
def add_dist_mate(fa, plane, dist, flip):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fa['face']).Select4(False, sd)
    ok2 = aext.SelectByID2(plane, 'PLANE', 0,0,0, True, 1, None, 0)
    r = a.AddMate5(5, 2, flip, dist, dist, dist, 1,1, 0,0,0, False, False, 0); m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    return (m is not None and err==1), f'err={err} sel2={ok2}'

targets = ['S30001MU0-1','S30001MU0-2','S30001MU0-3','S30001MU0-4','S30008MU0-1','S30003MU0-1']
print('시작 상태:', {n: ST.get(status(n)) for n in targets})
# 1) 경사판 4장: 윗면↔윗면
for n in ['S30001MU0-1','S30001MU0-2','S30001MU0-3','S30001MU0-4']:
    if status(n) == 3: print(n, '이미 완전정의'); continue
    b0 = box(n)
    ok, msg = add_plane_mate(n, '윗면'); am.ForceRebuild3(False)
    st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
    print(f'{n} 윗면 메이트 {ok} {msg} → 상태 {ST.get(st)} 이동 {moved}')
    if (not ok) or st in (4,5,6) or moved:
        nm = last_mate_name(); print('  롤백', nm, delete_mate(nm)); am.ForceRebuild3(False)
# 2) 충전구 덮개: 밑면 ↔ 뚜껑 윗면
n = 'S30008MU0-1'
if status(n) != 3:
    b0 = box(n)
    cover_bot = pick(C[n], [0,-1,0], 1, 740, tol=3); lid_top = pick(C['S30006MU0-1'], [0,1,0], 1, 740, tol=3)
    if cover_bot and lid_top:
        ok, msg = add_face_mate(cover_bot, lid_top); am.ForceRebuild3(False)
        st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
        print(f'{n} 면 일치 {ok} {msg} → 상태 {ST.get(st)} 이동 {moved}')
        if (not ok) or st in (4,5,6) or moved:
            nm = last_mate_name(); print('  롤백', nm, delete_mate(nm)); am.ForceRebuild3(False)
    else: print(n, '면 못 찾음', cover_bot is None, lid_top is None)
# 3) 플랜지판: 밑면 ↔ 윗면 거리 163.4
n = 'S30003MU0-1'
if status(n) != 3:
    b0 = box(n); pl_bot = pick(C[n], [0,-1,0], 1, b0[1], tol=2)
    if pl_bot:
        d = b0[1]/1000.0
        for flip in (False, True):
            ok, msg = add_dist_mate(pl_bot, '윗면', d, flip); am.ForceRebuild3(False)
            st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
            print(f'{n} 거리 메이트 flip={flip} {ok} {msg} → 상태 {ST.get(st)} 이동 {moved}')
            if ok and st not in (4,5,6) and not moved: break
            nm = last_mate_name(); print('  롤백', nm, delete_mate(nm)); am.ForceRebuild3(False)
    else: print(n, '밑면 못 찾음')
am.ForceRebuild3(False)
print('오류:', aext.GetWhatsWrongCount())
print('최종:', {nn: ST.get(status(nn)) for nn in C})
