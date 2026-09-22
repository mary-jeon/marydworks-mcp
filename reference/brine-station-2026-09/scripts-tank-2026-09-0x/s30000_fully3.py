import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am); am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps()
smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
def vecv(o):
    for f in (lambda: [round(v,3) for v in o.value], lambda: [round(v,3) for v in list(o)], lambda: [round(o[i],3) for i in range(3)]):
        try: return f()
        except Exception: pass
    return str(o)
def dofs(n):
    r = C[n].GetRemainingDOFs(); out = {}
    if r[9]: out['T1'] = vecv(r[10])
    if r[11]: out['T2'] = vecv(r[12])
    if r[1]: out['R1p'] = vecv(r[2]); out['R1d'] = vecv(r[4])
    if r[5]: out['R2p'] = vecv(r[6]); out['R2d'] = vecv(r[8])
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
def add_mate(fa, fb, mtype=0, align=2, flip=False, d=0.0):
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
    print('   롤백', last, aext.DeleteSelection2(0) if ok else False)
wallN = 'S30002MU0-1'
# 1) 경사판: 스텁 바깥면(최대 바깥법선 면) ↔ 벽 바깥면 → 외면 플러시로 당김 허용(바깥축만)
for n in ['S30001MU0-1','S30001MU0-2','S30001MU0-3','S30001MU0-4']:
    if status(n) == 3: print(n, '이미 완전정의'); continue
    b0 = box(n); cx=(b0[0]+b0[3])/2; cz=(b0[2]+b0[5])/2
    axis, sgn = (2, 1 if cz>0 else -1) if abs(cz)>abs(cx) else (0, 1 if cx>0 else -1)
    nrm=[0,0,0]; nrm[axis]=sgn
    cand = [f for f in faces_of(C[n]) if f['n']==nrm]
    pf = max(cand, key=lambda f: f['A']) if cand else None
    wf_c = [f for f in faces_of(C[wallN]) if f['n']==nrm and abs(f['c'][axis]-600*sgn)<2]
    wf = max(wf_c, key=lambda f: f['A']) if wf_c else None
    if not pf or not wf: print(n, '면 없음'); continue
    print(f'{n} 스텁면 {pf["c"]} A={pf["A"]} → 벽면 {wf["c"]}')
    m, err = add_mate(pf, wf); am.ForceRebuild3(False)
    b1 = box(n); st = status(n)
    off_axis_moved = any(abs(b0[i]-b1[i])>0.2 for i in range(6) if i%3 != axis)
    print(f'  err={err} → {ST.get(st)} 이동 {[round(b1[i]-b0[i],1) for i in range(6)]} 축외이동={off_axis_moved}')
    if m is not None and (err!=1 or st in (4,5,6) or off_axis_moved): rollback_last(); am.ForceRebuild3(False)
# 2) 덮개: 남은 회전축 확인 후 평행 메이트로 잠금
n = 'S30008MU0-1'
if status(n) != 3:
    print(n, 'DOF:', dofs(n))
    b0 = box(n)
    side = [f for f in faces_of(C[n]) if f['n']==[1,0,0]]
    pf = max(side, key=lambda f: f['A']) if side else None
    if pf:
        am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
        api.cast('IEntity', pf['face']).Select4(False, sd)
        ok2 = aext.SelectByID2('우측면', 'PLANE', 0,0,0, True, 1, None, 0)
        r = a.AddMate5(3, 2, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
        m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
        am.ForceRebuild3(False); st = status(n); moved = any(abs(x-y)>0.2 for x,y in zip(b0, box(n)))
        print(f'{n} 옆면∥우측면 err={err} sel2={ok2} → {ST.get(st)} 이동={moved}')
        if m is not None and (err!=1 or st in (4,5,6) or moved): rollback_last(); am.ForceRebuild3(False)
# 3) 플랜지판: 거리 메이트, 매 시도 면 재탐색
n = 'S30003MU0-1'
for attempt, (align, flip) in enumerate([(0,True),(0,False),(1,False),(1,True)]):
    if status(n) == 3: break
    b0 = box(n)
    pb_c = [f for f in faces_of(C[n]) if f['n']==[0,-1,0]]
    wb_c = [f for f in faces_of(C[wallN]) if f['n']==[0,-1,0] and abs(f['c'][1]-35)<2]
    if not pb_c or not wb_c: print(n, '면 없음'); break
    pb = max(pb_c, key=lambda f: f['A']); wb = max(wb_c, key=lambda f: f['A'])
    d = abs(b0[1]-35.0)/1000.0
    m, err = add_mate(pb, wb, mtype=5, align=align, flip=flip, d=d); am.ForceRebuild3(False)
    st = status(n); delta = [round(x-y,1) for x,y in zip(box(n), b0)]; moved = any(abs(v)>0.2 for v in delta)
    print(f'{n} 거리 align={align} flip={flip} err={err} → {ST.get(st)} 이동 {delta}')
    if m is not None and err==1 and st not in (4,5,6) and not moved: break
    if m is not None: rollback_last(); am.ForceRebuild3(False)
am.ForceRebuild3(False)
print('오류:', aext.GetWhatsWrongCount())
print('최종:', {n: ST.get(status(n)) for n in comps()})
