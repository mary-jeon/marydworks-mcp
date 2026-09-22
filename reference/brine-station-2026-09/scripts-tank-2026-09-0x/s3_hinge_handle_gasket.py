import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
TPL = r'c:\solidworks data\00. <USER> 솔리드웍스 템플릿\01. 문서 템플릿\이텍 Part.prtdot'
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
def sk(m, plane, draw):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    m.ClearSelection2(True); ext.SelectByID2(plane, 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); draw(skm); skm.InsertSketch(True)
def report(m, mat, spec, title):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
    pd.SetMaterialPropertyName2('', MAT, mat); m.ForceRebuild3(False)
    cpm = api.cast('ICustomPropertyManager', ext.CustomPropertyManager(''))
    cpm.Add3('SPEC', 30, spec, 1); cpm.Add3('TITLE', 30, title, 1)
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 바디', len(pd.GetBodies2(0, True) or []),
          '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
# 1) S30009 경첩 리모델: 너클 Ø14 + 윗날개 35x4 + 옆날개 43x3, L60
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009 경첩(개선)'); wipe(m)
sk(m, '우측면', lambda s: s.CreateCircleByRadius(0, 0, 0, 0.007))
print('  너클', extrude_last(m, 0.060))
sk(m, '우측면', lambda s: s.CreateCornerRectangle(0.002, -0.010, 0, 0.035, -0.006, 0))
print('  윗날개', extrude_last(m, 0.060))
sk(m, '우측면', lambda s: s.CreateCornerRectangle(-0.0075, -0.043, 0, -0.0045, 0.0, 0))
print('  옆날개', extrude_last(m, 0.060))
report(m, 'STS 316', 'HINGE 60', 'HINGE')
print('  save', write.save_model(app, m)['errors'])
# 2) S30011 손잡이: 환봉 Ø10 ㄷ자 (기둥2 + 그립)
try:
    m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30011MU0.SLDPRT'))); api.activate(app, m); wipe(m); new=False
except Exception:
    m = api.cast('IModelDoc2', api.dyn(app).NewDocument(TPL, 0, 0, 0)); api.activate(app, m); new=True
print('== S30011 손잡이')
sk(m, '윗면', lambda s: s.CreateCircleByRadius(0.010, 0, 0, 0.005))
print('  기둥1', extrude_last(m, 0.035))
sk(m, '윗면', lambda s: s.CreateCircleByRadius(0.110, 0, 0, 0.005))
print('  기둥2', extrude_last(m, 0.035))
sk(m, '우측면', lambda s: s.CreateCircleByRadius(0, 0.035, 0, 0.005))
print('  그립', extrude_last(m, 0.120))
report(m, 'STS 316', 'RB 10', 'HANDLE')
print('  save', write.save_model(app, m, out_path=os.path.join(D,'S30011MU0.SLDPRT') if new else None)['errors'])
# 3) S30012 개스킷: EPDM 링 444/474 x 3T (압축 상태)
try:
    m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30012MU0.SLDPRT'))); api.activate(app, m); wipe(m); new=False
except Exception:
    m = api.cast('IModelDoc2', api.dyn(app).NewDocument(TPL, 0, 0, 0)); api.activate(app, m); new=True
print('== S30012 개스킷')
sk(m, '윗면', lambda s: (s.CreateCornerRectangle(-0.237,-0.237,0, 0.237,0.237,0), s.CreateCornerRectangle(-0.222,-0.222,0, 0.222,0.222,0)))
print('  링', extrude_last(m, 0.003))
report(m, 'EPDM', 'EPDM SPONGE 15x5T', 'GASKET')
print('  save', write.save_model(app, m, out_path=os.path.join(D,'S30012MU0.SLDPRT') if new else None)['errors'])
# 4) 어셈블리
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {2:'미구속',3:'완전정의',4:'과구속'}
# 기존 경첩 삭제
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
        if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0): print('경첩 삭제', n, aext.DeleteSelection2(0))
am.ForceRebuild3(False); C = comps()
INS = [('S30009MU0.SLDPRT', (-0.340, 0.783, 0.008)), ('S30009MU0.SLDPRT', (-0.195, 0.783, 0.008))]
if not any(n.startswith('S30011') for n in C): INS.append(('S30011MU0.SLDPRT', (-0.2975, 0.773, -0.430)))
if not any(n.startswith('S30012') for n in C): INS.append(('S30012MU0.SLDPRT', (-0.2375, 0.765, -0.2375)))
for fn, t in INS:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D, fn)]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[next(n for n in C if n.startswith('S30006'))]
for n in sorted(C):
    if n.startswith(('S30009MU0-','S30011MU0-','S30012MU0-')):
        print(n, 'box', [round(v*1000,1) for v in C[n].GetBox(False, False)])
        if C[n].GetConstrainedStatus() != 3:
            am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
            f1 = api.cast('IFace2', (api.cast('IBody2', C[n].GetBody()).GetFaces() or [None])[0])
            f2 = api.cast('IFace2', (api.cast('IBody2', lid.GetBody()).GetFaces() or [None])[0])
            api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
            r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
            m2, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
            print('  잠금 err', err)
am.ForceRebuild3(False)
# 신규 부품 속성(결재선 등)
import datetime
today = datetime.date.today().strftime('%Y-%m-%d')
BASE = {'RELATION NO.': 'S30000MU0', 'PROJECT NO.': 'S00000MU0', 'APPROVED': '박종창', 'CHECKED': '정상현', 'DISIGNED': '전혜리', 'REMARK': ''}
for fn, qty in [('S30009MU0.SLDPRT','2'), ('S30011MU0.SLDPRT','1'), ('S30012MU0.SLDPRT','1')]:
    m,_ = resolve(app, DocSelector(path=os.path.join(D, fn)))
    cpm = api.cast('ICustomPropertyManager', api.cast('IModelDocExtension', m.Extension).CustomPropertyManager(''))
    props = dict(BASE); props["QT'Y"] = qty
    props['Material'] = '"SW-Material@' + fn + '"'; props['중량'] = '"SW-Mass@' + fn + '"'
    for k, v in props.items(): cpm.Add3(k, 30, v, 1)
    api.dyn(m).DeleteCustomInfo2('', 'DATE'); cpm.Add3('DATE', 64, today, 1)
print('속성 완료')
print('오류', aext.GetWhatsWrongCount())
print('상태:', {n: ST.get(c.GetConstrainedStatus(), c.GetConstrainedStatus()) for n, c in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and d['title'].upper().startswith('S300'):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso'], S)
print('snap ok')
