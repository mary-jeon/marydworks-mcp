import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
def last_sketch(m):
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def try_strip(m, rect):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    fm = api.cast('IFeatureManager', m.FeatureManager)
    prev = last_sketch(m)
    m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); skm.CreateCornerRectangle(rect[0], rect[1], 0, rect[2], rect[3], 0); skm.InsertSketch(True)
    cur = last_sketch(m)
    if cur == prev: return False, '스케치 미생성'
    m.ClearSelection2(True); ext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    ff = fm.FeatureExtrusion3(True, False, True, 0, 0, 0.025, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
    return ff is not None, cur
def feat_dump(m):
    f = api.cast('IFeature', m.FirstFeature()); out=[]
    while f:
        t = f.GetTypeName2()
        if t in ('Extrusion','Boss','ICE','Cut','ProfileFeature'): out.append((f.Name, t))
        f = api.cast('IFeature', f.GetNextFeature())
    return out
B1, B2 = 0.248, 0.250
STRIPS = [(-B2, -B2, -B1, B2), (B1, -B2, B2, B2), (-B1, B1, B1, B2), (-B1, -B2, B1, -B1)]
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
fm = api.cast('IFeatureManager', m.FeatureManager)
print('피처:', feat_dump(m))
# 1단계: 롤백 바 끝으로
for code in (2, 3, 1):
    try:
        rc = fm.EditRollback(code, ''); print('EditRollback', code, rc)
        if rc: break
    except Exception as e: print('EditRollback', code, type(e).__name__)
m.ForceRebuild3(False)
ok, msg = try_strip(m, STRIPS[0])
print('롤백 후 스커트1:', ok, msg)
if not ok:
    # 2단계: S30000에서 덮개 관련 정리 후 파트 닫고 재오픈
    am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
    aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
    cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
    C = {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
    f = api.cast('IFeature', am.FirstFeature()); old=[]
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s:
                m2 = api.cast('IMate2', s.GetSpecificFeature2())
                for i in range(m2.GetMateEntityCount()):
                    e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
                    if c is not None and api.cast('IComponent2', c).Name2.startswith('S30008'): old.append(s.Name); break
                s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    for nm in old:
        am.ClearSelection2(True)
        if aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
    for n in list(C):
        if n.startswith('S30008MU0-'):
            am.ClearSelection2(True)
            if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0): print('컴포넌트 삭제', n, aext.DeleteSelection2(0))
    am.ForceRebuild3(False)
    print('save S30000', write.save_model(app, am)['errors'])
    app.CloseDoc('S30008MU0.SLDPRT')
    import time; time.sleep(1)
    err, warn = api.byref_int(), api.byref_int()
    m = api.cast('IModelDoc2', api.dyn(app).OpenDoc6(os.path.join(D,'S30008MU0.SLDPRT'), 1, 1, '', err, warn))
    print('재오픈 err', err.value)
    api.activate(app, m)
    ok, msg = try_strip(m, STRIPS[0])
    print('재오픈 후 스커트1:', ok, msg)
if ok:
    for i, rect in enumerate(STRIPS[1:], start=2):
        ok2, msg2 = try_strip(m, rect)
        print(f'스커트{i}:', ok2, msg2)
pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
pd.SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
bx = [round(v*1000,1) for v in pd.GetPartBox(True)]
mass = api.cast('IMassProperty', ext.CreateMassProperty()).Mass
print('box', bx, '| mass %.3f' % mass)
print('save', write.save_model(app, m)['errors'])
