import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
TPL = r'c:\solidworks data\00. <USER> 솔리드웍스 템플릿\01. 문서 템플릿\이텍 Part.prtdot'
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
def wipe_features(m):
    ext = api.cast('IModelDocExtension', m.Extension)
    names = []
    f = api.cast('IFeature', m.FirstFeature())
    while f:
        if f.GetTypeName2() in ('Extrusion','Boss','BossThin','ExtruThin','Cut','CutThin','ICE','Fillet','DeleteBody'): names.append(f.Name)
        f = api.cast('IFeature', f.GetNextFeature())
    for nm in reversed(names):
        m.ClearSelection2(True)
        ok = ext.SelectByID2(nm, 'BODYFEATURE', 0,0,0, False, 0, None, 0)
        d = ext.DeleteSelection2(1) if ok else False
        print('  del', nm, ok, d)
    # 남은 스케치 정리
    f = api.cast('IFeature', m.FirstFeature()); sks=[]
    while f:
        if f.GetTypeName2()=='ProfileFeature': sks.append(f.Name)
        f = api.cast('IFeature', f.GetNextFeature())
    for nm in sks:
        m.ClearSelection2(True)
        ok = ext.SelectByID2(nm, 'SKETCH', 0,0,0, False, 0, None, 0)
        if ok: ext.DeleteSelection2(1)
def sketch_on_top(m, draw):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    m.ClearSelection2(True)
    ok = ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0) or ext.SelectByID2('Top Plane', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); draw(skm); skm.InsertSketch(True)
def extrude_last_sketch(m, depth, flip=False):
    ext = api.cast('IModelDocExtension', m.Extension); fm = api.cast('IFeatureManager', m.FeatureManager)
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    m.ClearSelection2(True); ext.SelectByID2(last, 'SKETCH', 0,0,0, False, 0, None, 0)
    ff = fm.FeatureExtrusion3(True, flip, False, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
    return ff is not None
def finish(m, path=None):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
    pd.SetMaterialPropertyName2('', MAT, 'STS 304'); m.ForceRebuild3(False)
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 오류', ext.GetWhatsWrongCount(),
          '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    r = write.save_model(app, m, out_path=path); print('  saved', r['errors'])
# 1) S30007 커브: ㄴ자 링 — 발(459~489, H4.5) + 날(450~459, H17.5)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30007MU0.SLDPRT'))); api.activate(app, m)
print('== S30007'); wipe_features(m)
sketch_on_top(m, lambda s: (s.CreateCornerRectangle(-0.2445,-0.2445,0, 0.2445,0.2445,0), s.CreateCornerRectangle(-0.2295,-0.2295,0, 0.2295,0.2295,0)))
print('  발 extrude', extrude_last_sketch(m, 0.0045))
sketch_on_top(m, lambda s: (s.CreateCornerRectangle(-0.2295,-0.2295,0, 0.2295,0.2295,0), s.CreateCornerRectangle(-0.225,-0.225,0, 0.225,0.225,0)))
print('  날 extrude', extrude_last_sketch(m, 0.0175))
finish(m)
# 2) S30008 덮개: 평판 500각 5T
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
print('== S30008'); wipe_features(m)
sketch_on_top(m, lambda s: s.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0))
print('  판 extrude', extrude_last_sketch(m, 0.005))
finish(m)
# 3) S30009 힌지: 패드(60x15, H8.5, y -16.5~-8) + 배럴(Ø16, 축X)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009'); wipe_features(m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True)
ok = ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0) or ext.SelectByID2('Right Plane', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCircleByRadius(0,0,0, 0.008); skm.InsertSketch(True)
print('  배럴 extrude', extrude_last_sketch(m, 0.060))
m.ClearSelection2(True)
ok = ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0) or ext.SelectByID2('Right Plane', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.0165, -0.0075, 0, -0.008, 0.0075, 0); skm.InsertSketch(True)
print('  패드 extrude', extrude_last_sketch(m, 0.060))
finish(m)
# 4) S30010 벤트: 25A 파이프 OD34 t3.4 x 100
try:
    m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30010MU0.SLDPRT'))); api.activate(app, m); print('== S30010 (기존)'); wipe_features(m)
except Exception:
    m = api.cast('IModelDoc2', api.dyn(app).NewDocument(TPL, 0, 0, 0)); api.activate(app, m); print('== S30010 (신규)')
sketch_on_top(m, lambda s: (s.CreateCircleByRadius(0,0,0, 0.017), s.CreateCircleByRadius(0,0,0, 0.0136)))
print('  관 extrude', extrude_last_sketch(m, 0.100))
finish(m, os.path.join(D,'S30010MU0.SLDPRT'))
