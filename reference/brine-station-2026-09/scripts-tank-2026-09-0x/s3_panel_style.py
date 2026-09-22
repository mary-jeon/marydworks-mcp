import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
def wipe(m):
    ext = api.cast('IModelDocExtension', m.Extension)
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
def report(m, spec=None):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
    pd.SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
    if spec:
        cpm = api.cast('ICustomPropertyManager', ext.CustomPropertyManager('')); cpm.Add3('SPEC', 30, spec, 1)
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 바디', len(pd.GetBodies2(0, True) or []),
          '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    print('  save', write.save_model(app, m)['errors'])
# 1) S30007: 일자 커브 링 450/459 x 25H (첫 피처 링 = 성공 패턴)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30007MU0.SLDPRT'))); api.activate(app, m)
print('== S30007 일자 링'); wipe(m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True)
skm.CreateCornerRectangle(-0.2295,-0.2295,0, 0.2295,0.2295,0)
skm.CreateCornerRectangle(-0.225,-0.225,0, 0.225,0.225,0)
skm.InsertSketch(True)
print('  링', extrude_last(m, 0.025))
report(m, 'FB 25x4.5 RING')
# 2) S30008: 평판 500 x 5T만
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
print('== S30008 평판'); wipe(m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0); skm.InsertSketch(True)
print('  판', extrude_last(m, 0.005))
report(m, 'PL 5T')
# 3) S30009: 옆날개 연장 (y -37 까지) — 기존 옆날개 재생성
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009 옆날개 연장'); wipe(m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCircleByRadius(0, 0, 0, 0.004); skm.InsertSketch(True)
print('  너클', extrude_last(m, 0.060))
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(0.002, -0.004, 0, 0.027, -0.002, 0); skm.InsertSketch(True)
print('  윗날개', extrude_last(m, 0.060))
m.ClearSelection2(True); ext.SelectByID2('우측면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.004, -0.037, 0, -0.002, 0.002, 0); skm.InsertSketch(True)
print('  옆날개', extrude_last(m, 0.060))
report(m, 'HINGE 60x2T')
# 4) 어셈블리 재구성
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {2:'미구속',3:'완전정의',4:'과구속'}
# 재생성 부품들의 기존 메이트/컴포넌트 정리 후 재삽입+잠금 (커브/덮개/경첩)
targets = [n for n in C if n.startswith(('S30007','S30008','S30009'))]
f = api.cast('IFeature', am.FirstFeature()); old=[]
while f:
    if f.GetTypeName2()=='MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            m2 = api.cast('IMate2', s.GetSpecificFeature2())
            for i in range(m2.GetMateEntityCount()):
                e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
                if c is not None and api.cast('IComponent2', c).Name2.startswith(('S30007','S30008','S30009')): old.append(s.Name); break
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
print('메이트 삭제:', old)
for nm in old:
    am.ClearSelection2(True)
    if aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
for n in targets:
    am.ClearSelection2(True)
    if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0):
        print('삭제', n, aext.DeleteSelection2(0))
am.ForceRebuild3(False)
INS = [
 ('S30007MU0.SLDPRT', (-0.2375, 0.740, -0.2375)),
 ('S30008MU0.SLDPRT', (-0.2375, 0.768, -0.2375)),
 ('S30009MU0.SLDPRT', (-0.340, 0.777, 0.0105)),
 ('S30009MU0.SLDPRT', (-0.195, 0.777, 0.0105)),
]
for fn, t in INS:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D, fn)]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[next(n for n in C if n.startswith('S30006'))]
for n in sorted(C):
    if n.startswith(('S30007','S30008','S30009')):
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
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and d['title'].upper().startswith('S300'):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso','front'], S)
print('snap ok')
