import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am); am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
C = {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
def vec(o):
    try: return [round(v,3) for v in list(o)]
    except Exception: return o
def dofs(n):
    r = C[n].GetRemainingDOFs()
    out = {}
    if r[9]: out['T1'] = vec(r[10])
    if r[11]: out['T2'] = vec(r[12])
    if r[1]: out['R1p'] = vec(r[2]); out['R1d'] = vec(r[4])
    if r[5]: out['R2p'] = vec(r[6]); out['R2d'] = vec(r[8])
    return out
def status(n): return C[n].GetConstrainedStatus()
def box(n): return [round(v*1000,1) for v in C[n].GetBox(False, False)]
def faces_of(c):
    T = list(api.cast('IMathTransform', c.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]; out=[]
    for f in api.cast('IBody2', c.GetBody()).GetFaces() or []:
        f = api.cast('IFace2', f); s = api.cast('ISurface', f.GetSurface())
        if not s.IsPlane(): continue
        n = list(f.Normal); n=[round(sum(n[k]*R[k][i] for k in range(3)),2) for i in range(3)]
        b = list(f.GetBox()); pts=[[sum(p[k]*R[k][i] for k in range(3))+t[i] for i in range(3)] for p in [(b[i],b[j],b[k]) for i in (0,3) for j in (1,4) for k in (2,5)]]
        cen=[round(sum(p[i] for p in pts)/8*1000,1) for i in range(3)]; out.append({'face':f,'n':n,'c':cen,'A':round(f.GetArea()*1e6)})
    return out
def pick(c, n, axis, val, tol=2.0):
    hits=[fd for fd in faces_of(c) if fd['n']==n and abs(fd['c'][axis]-val)<tol]
    return max(hits, key=lambda f: f['A']) if hits else None
def add_face_mate(fa, fb, mtype=0, align=2, flip=False, d=0.0):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fa['face']).Select4(False, sd); api.cast('IEntity', fb['face']).Select4(True, sd)
    r = a.AddMate5(mtype, align, flip, d,d,d, 1,1, 0,0,0, False, False, 0)
    m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    return m, err
def rollback_last():
    f = api.cast('IFeature', am.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s: last=s.Name; s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    am.ClearSelection2(True); ok = aext.SelectByID2(last, 'MATE', 0,0,0, False, 0, None, 0)
    print('  롤백', last, aext.DeleteSelection2(0) if ok else False)

wall = C['S30002MU0-1']
print('== 남은 자유도')
for n in ['S30001MU0-1','S30001MU0-2','S30001MU0-3','S30001MU0-4','S30003MU0-1','S30008MU0-1']:
    print(f'  {n}: {dofs(n)} 상태={ST.get(status(n))}')
# 1) 경사판: 스텁 바깥면 ↔ 벽 바깥면 일치 (외면 플러시)
for n in ['S30001MU0-1','S30001MU0-2','S30001MU0-3','S30001MU0-4']:
    if status(n) == 3: continue
    b0 = box(n); cx = (b0[0]+b0[3])/2; cz = (b0[2]+b0[5])/2
    if abs(cz) > abs(cx): axis, sgn = 2, (1 if cz>0 else -1)
    else: axis, sgn = 0, (1 if cx>0 else -1)
    nrm = [0,0,0]; nrm[axis] = sgn
    pf = pick(C[n], nrm, axis, 600*sgn); wf = pick(wall, nrm, axis, 600*sgn)
    if not pf or not wf: print(n, '면 없음', nrm, pf is None, wf is None); continue
    m, err = add_face_mate(pf, wf); am.ForceRebuild3(False)
    st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
    print(f'{n} 외면 일치 err={err} → {ST.get(st)} 이동={moved}')
    if m is not None and (err!=1 or st in (4,5,6) or moved): rollback_last(); am.ForceRebuild3(False)
# 2) 덮개: 밑면 ↔ 뚜껑 윗면 (재복구)
n = 'S30008MU0-1'
if status(n) != 3:
    b0 = box(n)
    cb = pick(C[n], [0,-1,0], 1, b0[1]); lt = pick(C['S30006MU0-1'], [0,1,0], 1, b0[1])
    if cb and lt:
        m, err = add_face_mate(cb, lt); am.ForceRebuild3(False)
        st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
        print(f'{n} 면 일치 err={err} → {ST.get(st)} 이동={moved}')
        if m is not None and (err!=1 or st in (4,5,6) or moved): rollback_last(); am.ForceRebuild3(False)
    else: print(n, '면 못 찾음')
# 3) 플랜지판: 밑면 ↔ 벽 밑면 거리 메이트 (조합 재시도)
n = 'S30003MU0-1'
if status(n) != 3:
    b0 = box(n)
    pb = pick(C[n], [0,-1,0], 1, b0[1]); wb = pick(wall, [0,-1,0], 1, 35)
    d = abs(b0[1]-35.0)/1000.0
    done = False
    for align in (0,1,2):
        for flip in (False, True):
            m, err = add_face_mate(pb, wb, mtype=5, align=align, flip=flip, d=d); am.ForceRebuild3(False)
            st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
            print(f'{n} 거리 align={align} flip={flip} err={err} → {ST.get(st)} 이동={moved}')
            if m is not None and err==1 and st not in (4,5,6) and not moved: done=True; break
            if m is not None: rollback_last(); am.ForceRebuild3(False)
        if done: break
am.ForceRebuild3(False)
print('오류:', aext.GetWhatsWrongCount())
print('최종 상태:', {n: ST.get(status(n)) for n in C})
