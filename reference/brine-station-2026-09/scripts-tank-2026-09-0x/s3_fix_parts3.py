import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
def wipe(m):
    ext = api.cast('IModelDocExtension', m.Extension)
    for _round in range(3):
        f = api.cast('IFeature', m.FirstFeature()); feats=[]; sks=[]
        while f:
            t = f.GetTypeName2()
            if t in ('Extrusion','Boss','BossThin','ExtruThin','Cut','CutThin','ICE','MirrorPattern','DeleteBody'): feats.append(f.Name)
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
def sketch_top(m, draw):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); draw(skm); skm.InsertSketch(True)
def last_sketch(m):
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def extrude_last(m, depth):
    ext = api.cast('IModelDocExtension', m.Extension); fm = api.cast('IFeatureManager', m.FeatureManager)
    m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
    return fm.FeatureExtrusion3(True, False, False, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False) is not None
def report(m, save=True):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension); m.ForceRebuild3(False)
    bodies = pd.GetBodies2(0, True) or []
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 바디', len(bodies), '| 오류', ext.GetWhatsWrongCount(),
          '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    if save: print('  save', write.save_model(app, m)['errors'])
# 1) S30007: 통 링(450~489 × 17.5) → 상부 바깥(459~) 13 컷 → ㄴ자
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30007MU0.SLDPRT'))); api.activate(app, m)
print('== S30007'); wipe(m)
sketch_top(m, lambda s: (s.CreateCornerRectangle(-0.2445,-0.2445,0, 0.2445,0.2445,0), s.CreateCornerRectangle(-0.225,-0.225,0, 0.225,0.225,0)))
print('  통', extrude_last(m, 0.0175))
ext = api.cast('IModelDocExtension', m.Extension)
m.ClearSelection2(True)
ok = ext.SelectByID2('', 'FACE', 0.235, 0.0175, 0.0, False, 0, None, 0); print('  상면 sel', ok)
skm = api.cast('ISketchManager', m.SketchManager)
skm.InsertSketch(True)
skm.CreateCornerRectangle(-0.260,-0.260,0, 0.260,0.260,0)
skm.CreateCornerRectangle(-0.2295,-0.2295,0, 0.2295,0.2295,0)
skm.InsertSketch(True)
fm = api.cast('IFeatureManager', m.FeatureManager)
m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
fc = fm.FeatureCut4(True, False, False, 0, 0, 0.013, 0.013, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
print('  ㄴ컷', fc is not None)
report(m)
# 2) S30008: 평판 500각 5T 재생성
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
print('== S30008'); wipe(m)
sketch_top(m, lambda s: s.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0))
print('  판', extrude_last(m, 0.005))
report(m)
# 3) S30009: 배럴 + 패드(겹침 y -16.5~-7)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009'); wipe(m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCircleByRadius(0,0,0, 0.008); skm.InsertSketch(True)
print('  배럴', extrude_last(m, 0.060))
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.0075, -0.0165, 0, 0.0075, -0.007, 0); skm.InsertSketch(True)
print('  패드', extrude_last(m, 0.060))
report(m)
