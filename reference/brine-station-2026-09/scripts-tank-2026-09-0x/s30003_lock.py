import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
smgr = api.cast('ISelectionMgr', am.SelectionManager)
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
def rollback_last():
    f = api.cast('IFeature', am.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s: last=s.Name; s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    am.ClearSelection2(True); ok = aext.SelectByID2(last, 'MATE', 0,0,0, False, 0, None, 0)
    print('   롤백', last, aext.DeleteSelection2(0) if ok else False)
n = 'S30003MU0-1'
combos = [('plane', 0, False), ('plane', 0, True), ('plane', 2, False), ('plane', 2, True), ('walltop', 1, False), ('walltop', 1, True)]
for kind, align, flip in combos:
    if status(n) == 3: break
    b0 = box(n)
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    if kind == 'plane':
        pb_c = [f for f in faces_of(C[n]) if f['n']==[0,-1,0]]
        pb = max(pb_c, key=lambda f: f['A'])
        api.cast('IEntity', pb['face']).Select4(False, sd)
        ok2 = aext.SelectByID2('윗면', 'PLANE', 0,0,0, True, 1, None, 0)
        d = abs(b0[1])/1000.0
    else:
        pt_c = [f for f in faces_of(C[n]) if f['n']==[0,1,0]]
        wt_c = [f for f in faces_of(C['S30002MU0-1']) if f['n']==[0,-1,0] and abs(f['c'][1]-35)<2]
        pt = max(pt_c, key=lambda f: f['A']); wt = max(wt_c, key=lambda f: f['A'])
        api.cast('IEntity', pt['face']).Select4(False, sd); api.cast('IEntity', wt['face']).Select4(True, sd)
        ok2 = True; d = abs(35.0-b0[4])/1000.0
    r = a.AddMate5(5, align, flip, d,d,d, 1,1, 0,0,0, False, False, 0)
    m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    am.ForceRebuild3(False); st = status(n); delta = [round(x-y,1) for x,y in zip(box(n), b0)]; moved = any(abs(v)>0.2 for v in delta)
    print(f'{n} {kind} align={align} flip={flip} d={round(d*1000,1)} err={err} → {ST.get(st)} 이동 {delta}')
    if m is not None and err==1 and st not in (4,5,6) and not moved: print('  채택'); break
    if m is not None: rollback_last(); am.ForceRebuild3(False)
am.ForceRebuild3(False)
print('오류:', aext.GetWhatsWrongCount())
print('상태:', {k: ST.get(C2.GetConstrainedStatus()) for k, C2 in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
print('save', write.save_model(app, am)['errors'])
