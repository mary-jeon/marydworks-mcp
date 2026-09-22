import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
def last_sketch(m):
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def loose_sketches(m):
    out=[]; f = api.cast('IFeature', m.FirstFeature())
    while f:
        if f.GetTypeName2()=='ProfileFeature': out.append(f.Name)
        f = api.cast('IFeature', f.GetNextFeature())
    return out
def rect_lines(skm, x1, z1, x2, z2):
    ok = True
    ok &= skm.CreateLine(x1, z1, 0, x2, z1, 0) is not None
    ok &= skm.CreateLine(x2, z1, 0, x2, z2, 0) is not None
    ok &= skm.CreateLine(x2, z2, 0, x1, z2, 0) is not None
    ok &= skm.CreateLine(x1, z2, 0, x1, z1, 0) is not None
    return ok
def strip_by_lines(m, rect, depth=0.025):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    fm = api.cast('IFeatureManager', m.FeatureManager)
    while skm.ActiveSketch is not None: skm.InsertSketch(True)
    prev = last_sketch(m)
    m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True)
    skm.AddToDB = True; skm.DisplayWhenAdded = False
    ok = rect_lines(skm, rect[0], rect[1], rect[2], rect[3])
    skm.AddToDB = False; skm.DisplayWhenAdded = True
    skm.InsertSketch(True)
    cur = last_sketch(m)
    if not ok or cur == prev: return False, f'선 {ok} 스케치 {cur}'
    m.ClearSelection2(True); ext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    ff = fm.FeatureExtrusion3(True, False, True, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
    return ff is not None, cur
# 1) S30008: 떠돌이 스케치 정리(상판 스케치 제외) + 스커트 4 (선 방식)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
ext = api.cast('IModelDocExtension', m.Extension); pd = api.cast('IPartDoc', m)
skm = api.cast('ISketchManager', m.SketchManager)
while skm.ActiveSketch is not None: skm.InsertSketch(True)
# 흡수 안 된 스케치 중 마지막 것(테스트 잔재) 정리 — 피처로 안 쓰인 것만
f = api.cast('IFeature', m.FirstFeature()); tops=[]
while f:
    if f.GetTypeName2()=='ProfileFeature': tops.append(f.Name)
    f = api.cast('IFeature', f.GetNextFeature())
print('S30008 최상위 스케치:', tops)
for nm in tops:
    if nm != '스케치58':
        m.ClearSelection2(True)
        if ext.SelectByID2(nm, 'SKETCH', 0,0,0, False, 0, None, 0): print('  잔재 삭제', nm, ext.DeleteSelection2(1))
m.ForceRebuild3(False)
B1, B2 = 0.248, 0.250
STRIPS = [(-B2, -B2, -B1, B2), (B1, -B2, B2, B2), (-B1, B1, B1, B2), (-B1, -B2, B1, -B1)]
for i, rect in enumerate(STRIPS):
    ok, msg = strip_by_lines(m, rect)
    print(f'스커트{i+1}:', ok, msg)
pd.SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
bx = [round(v*1000,1) for v in pd.GetPartBox(True)]
mass = api.cast('IMassProperty', ext.CreateMassProperty()).Mass
print('S30008 box', bx, '| mass %.3f' % mass)
print('save', write.save_model(app, m)['errors'])
if mass > 8 or bx[1] > -20: sys.exit('덮개 이상 — 중단')
# 2) S30009 옆날개 40 재생성
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
ext = api.cast('IModelDocExtension', m.Extension); pd = api.cast('IPartDoc', m)
skm = api.cast('ISketchManager', m.SketchManager); fm = api.cast('IFeatureManager', m.FeatureManager)
while skm.ActiveSketch is not None: skm.InsertSketch(True)
for _ in range(4):
    f = api.cast('IFeature', m.FirstFeature()); feats=[]; sks=[]
    while f:
        t = f.GetTypeName2()
        if t in ('Extrusion','Boss','ICE','Cut'): feats.append(f.Name)
        if t == 'ProfileFeature': sks.append(f.Name)
        f = api.cast('IFeature', f.GetNextFeature())
    if not feats and not sks: break
    for nm in reversed(feats):
        m.ClearSelection2(True)
        if ext.SelectByID2(nm, 'BODYFEATURE', 0,0,0, False, 0, None, 0): ext.DeleteSelection2(1)
    for nm in sks:
        m.ClearSelection2(True)
        if ext.SelectByID2(nm, 'SKETCH', 0,0,0, False, 0, None, 0): ext.DeleteSelection2(1)
m.ForceRebuild3(False)
def prof_on_right(draw, depth):
    prev = last_sketch(m)
    m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True)
    skm.AddToDB = True; skm.DisplayWhenAdded = False
    ok = draw(skm)
    skm.AddToDB = False; skm.DisplayWhenAdded = True
    skm.InsertSketch(True)
    cur = last_sketch(m)
    if not ok or cur == prev: return False
    m.ClearSelection2(True); ext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    return fm.FeatureExtrusion3(True, False, False, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False) is not None
ok1 = prof_on_right(lambda s: s.CreateCircleByRadius(0,0,0, 0.007) is not None, 0.060); print('너클', ok1)
ok2 = prof_on_right(lambda s: rect_lines(s, 0.002, -0.010, 0.035, -0.006), 0.060); print('윗날개', ok2)
ok3 = prof_on_right(lambda s: rect_lines(s, -0.0075, -0.040, -0.0045, 0.0), 0.060); print('옆날개', ok3)
pd.SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
print('S30009 box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
print('save', write.save_model(app, m)['errors'])
if not (ok1 and ok2 and ok3): sys.exit('경첩 이상 — 중단')
# 3) 어셈블리: 경첩 삭제/재삽입, 덮개 삽입(이미 삭제된 상태), 잠금
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {2:'미구속',3:'완전정의',4:'과구속'}
f = api.cast('IFeature', am.FirstFeature()); old=[]
while f:
    if f.GetTypeName2()=='MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            m2 = api.cast('IMate2', s.GetSpecificFeature2())
            for i in range(m2.GetMateEntityCount()):
                e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
                if c is not None and api.cast('IComponent2', c).Name2.startswith('S30009'): old.append(s.Name); break
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
for nm in old:
    am.ClearSelection2(True)
    if aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
for n in list(C):
    if n.startswith('S30009MU0-'):
        am.ClearSelection2(True)
        if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
am.ForceRebuild3(False)
INS = [
 ('S30008MU0.SLDPRT', (-0.2375, 0.768, -0.2375)),
 ('S30009MU0.SLDPRT', (-0.340, 0.780, 0.008)),
 ('S30009MU0.SLDPRT', (-0.195, 0.780, 0.008)),
]
for fn, t in INS:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D, fn)]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[next(n for n in C if n.startswith('S30006'))]
for n in sorted(C):
    if n.startswith(('S30008MU0-','S30009MU0-')):
        print(n, 'box', [round(v*1000,1) for v in C[n].GetBox(False, False)])
        am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
        f1 = api.cast('IFace2', (api.cast('IBody2', C[n].GetBody()).GetFaces() or [None])[0])
        f2 = api.cast('IFace2', (api.cast('IBody2', lid.GetBody()).GetFaces() or [None])[0])
        api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
        r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
        m2, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
        print('  잠금 err', err)
am.ForceRebuild3(False)
print('오류', aext.GetWhatsWrongCount())
print('상태:', {n: ST.get(c.GetConstrainedStatus(), c.GetConstrainedStatus()) for n, c in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
import re
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and re.match(r'^S[0-9]', d['title'].upper()):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso'], S)
print('snap ok')
