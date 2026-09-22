import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
app = api.get_app()
def top_face(m, normal_axis, sign):
    pd = api.cast('IPartDoc', m)
    best = None; bestA = 0
    for bo in pd.GetBodies2(0, True) or []:
        for fx in api.cast('IBody2', bo).GetFaces() or []:
            fx = api.cast('IFace2', fx); s = api.cast('ISurface', fx.GetSurface())
            if not s.IsPlane(): continue
            n = list(fx.Normal)
            if abs(n[normal_axis] - sign) < 0.01 and fx.GetArea() > bestA:
                best = fx; bestA = fx.GetArea()
    return best
def cut_hole(m, face, cx, cy, depth):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    fm = api.cast('IFeatureManager', m.FeatureManager)
    smgr = api.cast('ISelectionMgr', m.SelectionManager)
    def last():
        f = api.cast('IFeature', m.FirstFeature()); l=None
        while f:
            if f.GetTypeName2()=='ProfileFeature': l=f.Name
            f = api.cast('IFeature', f.GetNextFeature())
        return l
    while skm.ActiveSketch is not None: skm.InsertSketch(True)
    prev = last()
    m.ClearSelection2(True)
    sd = api.cast('ISelectData', smgr.CreateSelectData())
    api.cast('IEntity', face).Select4(False, sd)
    skm.InsertSketch(True)
    skm.AddToDB = True; skm.DisplayWhenAdded = False
    c = skm.CreateCircleByRadius(cx, cy, 0, 0.007)
    skm.AddToDB = False; skm.DisplayWhenAdded = True
    skm.InsertSketch(True)
    cur = last()
    if cur == prev: return False, 'sketch'
    m.ClearSelection2(True); ext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    fc = fm.FeatureCut4(True, False, False, 0, 0, depth, depth, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
    return fc is not None, cur
# 1) 윙 남은 홀 2개 (로컬 -z측: (-675,-680), (675,-680)) — 윗면(normal +y)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30003MU0.SLDPRT'))); api.activate(app, m)
face = top_face(m, 1, 1)
print('윙 윗면', face is not None)
for (cx, cz) in [(-0.675, -0.680), (0.675, -0.680)]:
    ok, msg = cut_hole(m, face, cx, cz, 0.006)
    print('윙 홀', round(cx*1000), round(cz*1000), ok, msg)
    face = top_face(m, 1, 1)
m.ForceRebuild3(False)
print('윙 mass %.2f' % api.cast('IMassProperty', api.cast('IModelDocExtension', m.Extension).CreateMassProperty()).Mass)
print('save', write.save_model(app, m)['errors'])
# 2) 패드 홀 (정확한 면 방향 탐색: 두께축 자동)
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S00000MU0.SLDASM')))
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
pc = next(api.cast('IComponent2', c) for c in root.GetChildren() or [] if api.cast('IComponent2', c).Name2.startswith('파트1^') and api.cast('IComponent2', c).Name2.endswith('-1'))
pm = api.cast('IModelDoc2', pc.GetModelDoc2()); api.activate(app, pm)
pbx = api.cast('IPartDoc', pm).GetPartBox(True)
dims = [pbx[3]-pbx[0], pbx[4]-pbx[1], pbx[5]-pbx[2]]
axis = dims.index(min(dims))
print('패드 두께축', 'xyz'[axis], [round(v*1000,1) for v in dims])
face = top_face(pm, axis, 1)
print('패드 면', face is not None)
ok, msg = cut_hole(pm, face, 0.0, 0.0, 0.007)
print('패드 홀', ok, msg)
pm.ForceRebuild3(False)
api.activate(app, am); am.ForceRebuild3(False)
print('S00000 오류', api.cast('IModelDocExtension', am.Extension).GetWhatsWrongCount())
print('save S00000', write.save_model(app, am)['errors'])
import re
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and re.match(r'^S[0-9]', d['title'].upper()):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
