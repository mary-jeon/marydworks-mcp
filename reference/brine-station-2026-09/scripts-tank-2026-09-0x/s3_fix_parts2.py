import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app()
def del_feat(m, names, ftype='BODYFEATURE'):
    ext = api.cast('IModelDocExtension', m.Extension)
    for nm in names:
        m.ClearSelection2(True)
        ok = ext.SelectByID2(nm, ftype, 0,0,0, False, 0, None, 0)
        d = ext.DeleteSelection2(1) if ok else False
        print('  del', nm, ok, d)
def sketch_top(m, draw):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    m.ClearSelection2(True)
    ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); draw(skm); skm.InsertSketch(True)
def extrude_last(m, depth):
    ext = api.cast('IModelDocExtension', m.Extension); fm = api.cast('IFeatureManager', m.FeatureManager)
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    m.ClearSelection2(True); ext.SelectByID2(last, 'SKETCH', 0,0,0, False, 0, None, 0)
    ff = fm.FeatureExtrusion3(True, False, False, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
    return ff is not None
def report(m):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension); m.ForceRebuild3(False)
    bodies = pd.GetBodies2(0, True) or []
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 바디', len(bodies), '| 오류', ext.GetWhatsWrongCount(),
          '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    print('  save', write.save_model(app, m)['errors'])
# 1) S30007: 전부 지우고 발(454.5~489, H4.5) + 날(450~459, H17.5, 겹침) 재생성
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30007MU0.SLDPRT'))); api.activate(app, m)
print('== S30007')
del_feat(m, ['보스-돌출2','보스-돌출1'])
ext = api.cast('IModelDocExtension', m.Extension)
f = api.cast('IFeature', m.FirstFeature()); sks=[]
while f:
    if f.GetTypeName2()=='ProfileFeature': sks.append(f.Name)
    f = api.cast('IFeature', f.GetNextFeature())
del_feat(m, sks, 'SKETCH')
sketch_top(m, lambda s: (s.CreateCornerRectangle(-0.2445,-0.2445,0, 0.2445,0.2445,0), s.CreateCornerRectangle(-0.22725,-0.22725,0, 0.22725,0.22725,0)))
print('  발', extrude_last(m, 0.0045))
sketch_top(m, lambda s: (s.CreateCornerRectangle(-0.2295,-0.2295,0, 0.2295,0.2295,0), s.CreateCornerRectangle(-0.225,-0.225,0, 0.225,0.225,0)))
print('  날', extrude_last(m, 0.0175))
report(m)
# 2) S30008: 판금 피처 제거(평판만 남김)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
print('== S30008')
del_feat(m, ['모서리 플랜지3','베이스-플랜지2'])
del_feat(m, ['스케치10','스케치25'], 'SKETCH')
report(m)
# 3) S30009: 패드 재생성 (y -16.5~-8)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009')
del_feat(m, ['보스-돌출3','보스-돌출2'])
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.0075, -0.0165, 0, 0.0075, -0.008, 0); skm.InsertSketch(True)
print('  패드', extrude_last(m, 0.060))
report(m)
# 4) S30006 뚜껑: 벤트 구멍 Ø35 @ asm(300,300)
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
lidc = next(api.cast('IComponent2', c) for c in root.GetChildren() or [] if api.cast('IComponent2', c).Name2.startswith('S30006'))
T = list(api.cast('IMathTransform', lidc.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]
pa = [0.300, 0.740, 0.300]
pp = [sum(R[r][i]*(pa[r]-t[r]) for r in range(3)) for i in range(3)]  # R^T(p-t): R rows are basis
print('  뚜껑 파트좌표', [round(v*1000,1) for v in pp])
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30006MU0.SLDPRT'))); api.activate(app, m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True)
ok = ext.SelectByID2('', 'FACE', pp[0], pp[1], 0.0, False, 0, None, 0)
print('  윗면 face sel', ok)
skm.InsertSketch(True)
skm.CreateCircleByRadius(pp[0], pp[1], 0, 0.0175)
skm.InsertSketch(True)
fm = api.cast('IFeatureManager', m.FeatureManager)
f = api.cast('IFeature', m.FirstFeature()); last=None
while f:
    if f.GetTypeName2()=='ProfileFeature': last=f.Name
    f = api.cast('IFeature', f.GetNextFeature())
m.ClearSelection2(True); ext.SelectByID2(last, 'SKETCH', 0,0,0, False, 0, None, 0)
fc = fm.FeatureCut4(True, False, False, 0, 0, 0.005, 0.005, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
print('  벤트 구멍 컷', fc is not None)
report(m)
