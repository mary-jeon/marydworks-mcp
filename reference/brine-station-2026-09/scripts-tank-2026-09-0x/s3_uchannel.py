import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
def wipe(m):
    ext = api.cast('IModelDocExtension', m.Extension)
    for _ in range(3):
        f = api.cast('IFeature', m.FirstFeature()); feats=[]; sks=[]
        while f:
            t = f.GetTypeName2()
            if t in ('Extrusion','Boss','BossThin','ExtruThin','Cut','CutThin','ICE','DeleteBody'): feats.append(f.Name)
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
def extrude_last(m, depth, down=False):
    ext = api.cast('IModelDocExtension', m.Extension); fm = api.cast('IFeatureManager', m.FeatureManager)
    m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
    return fm.FeatureExtrusion3(True, False, down, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False) is not None
def report(m):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension); m.ForceRebuild3(False)
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 바디', len(pd.GetBodies2(0, True) or []),
          '| 오류', ext.GetWhatsWrongCount(), '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    print('  save', write.save_model(app, m)['errors'])
# 1) S30007 U채널 커브: 통 링(450/498, H25) -> 홈 컷(459/489, 깊이 20.5)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30007MU0.SLDPRT'))); api.activate(app, m)
print('== S30007 U채널'); wipe(m)
sketch_top(m, lambda s: (s.CreateCornerRectangle(-0.249,-0.249,0, 0.249,0.249,0), s.CreateCornerRectangle(-0.225,-0.225,0, 0.225,0.225,0)))
print('  통', extrude_last(m, 0.025))
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True)
ok = ext.SelectByID2('', 'FACE', 0.2405, 0.025, 0.0, False, 0, None, 0); print('  상면 sel', ok)
skm.InsertSketch(True)
skm.CreateCornerRectangle(-0.2445,-0.2445,0, 0.2445,0.2445,0)
skm.CreateCornerRectangle(-0.2295,-0.2295,0, 0.2295,0.2295,0)
skm.InsertSketch(True)
fm = api.cast('IFeatureManager', m.FeatureManager)
m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
fc = fm.FeatureCut4(True, False, False, 0, 0, 0.0205, 0.0205, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
print('  홈 컷', fc is not None)
report(m)
# 2) S30008 덮개: 평판 500x5 + 테두리 날(471.5/476.5) 아래로 15
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
print('== S30008 평판+날'); wipe(m)
sketch_top(m, lambda s: s.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0))
print('  판', extrude_last(m, 0.005))
sketch_top(m, lambda s: (s.CreateCornerRectangle(-0.23825,-0.23825,0, 0.23825,0.23825,0), s.CreateCornerRectangle(-0.23575,-0.23575,0, 0.23575,0.23575,0)))
print('  날(하향)', extrude_last(m, 0.015, down=True))
report(m)
# 3) S30009 힌지: 배럴 +- 패드 y -19~-7 (겹침 1)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009'); wipe(m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCircleByRadius(0,0,0, 0.008); skm.InsertSketch(True)
print('  배럴', extrude_last(m, 0.060))
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.0075, -0.019, 0, 0.0075, -0.007, 0); skm.InsertSketch(True)
print('  패드', extrude_last(m, 0.060))
report(m)
# 4) 어셈블리: 덮개 거리 27.5, 힌지 재삽입(y759, z20), 검사·저장
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps()
# 거리 메이트 치수 27.5로
f = api.cast('IFeature', am.FirstFeature()); dists=[]
while f:
    if f.GetTypeName2()=='MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            if s.Name.startswith('거리') and 'S30008' in str(mates := [api.cast('IComponent2', api.cast('IMateEntity2', api.cast('IMate2', s.GetSpecificFeature2()).MateEntity(i)).ReferenceComponent).Name2 for i in range(api.cast('IMate2', s.GetSpecificFeature2()).GetMateEntityCount()) if api.cast('IMateEntity2', api.cast('IMate2', s.GetSpecificFeature2()).MateEntity(i)).ReferenceComponent]):
                dists.append(s.Name)
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
print('덮개 거리 메이트:', dists)
p = api.cast('IDimension', am.Parameter('D1@' + dists[-1])); print('rc', p.SetSystemValue3(0.0275, 2, None))
am.ForceRebuild3(False)
covN = next(n for n in C if n.startswith('S30008MU0-'))
print('덮개 box', [round(v*1000,1) for v in C[covN].GetBox(False, False)])
# 힌지 재삽입
for n in list(C):
    if n.startswith('S30009MU0-'):
        am.ClearSelection2(True)
        if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0):
            print('힌지 삭제', n, aext.DeleteSelection2(0))
am.ForceRebuild3(False)
for tx in (-0.340, -0.195):
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D,'S30009MU0.SLDPRT')]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, tx, 0.759, 0.020, 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
smgr = api.cast('ISelectionMgr', am.SelectionManager)
lid = C[next(n for n in C if n.startswith('S30006MU0-'))]
for n in sorted(C):
    if n.startswith('S30009MU0-'):
        print(n, 'box', [round(v*1000,1) for v in C[n].GetBox(False, False)])
        am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
        f1 = api.cast('IFace2', (api.cast('IBody2', C[n].GetBody()).GetFaces() or [None])[0])
        f2 = api.cast('IFace2', (api.cast('IBody2', lid.GetBody()).GetFaces() or [None])[0])
        api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
        r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
        m2, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
        print('  잠금 err', err)
am.ForceRebuild3(False)
# 재질(재생성 부품) + SPEC 갱신
for fn, spec in [('S30007MU0','U-CH RING 4.5T'), ('S30008MU0','PL 5T'), ('S30009MU0','D16x60')]:
    m,_ = resolve(app, DocSelector(path=os.path.join(D, fn + '.SLDPRT')))
    api.cast('IPartDoc', m).SetMaterialPropertyName2('', MAT, 'STS 316')
    cpm = api.cast('ICustomPropertyManager', api.cast('IModelDocExtension', m.Extension).CustomPropertyManager(''))
    cpm.Add3('SPEC', 30, spec, 1)
    m.ForceRebuild3(False)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
print('오류:', aext.GetWhatsWrongCount())
print('상태:', {n: ST.get(c.GetConstrainedStatus()) for n, c in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and d['title'].upper().startswith('S300'):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso'], S)
print('snap ok')
