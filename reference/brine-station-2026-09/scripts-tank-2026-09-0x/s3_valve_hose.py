import sys, os, pythoncom, datetime; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
TPL = r'c:\solidworks data\00. <USER> 솔리드웍스 템플릿\01. 문서 템플릿\이텍 Part.prtdot'
app = api.get_app()
today = datetime.date.today().strftime('%Y-%m-%d')
def last_sketch(m):
    f = api.cast('IFeature', m.FirstFeature()); l=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': l=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return l
def rect_lines(skm, x1, z1, x2, z2):
    ok = True
    ok &= skm.CreateLine(x1, z1, 0, x2, z1, 0) is not None
    ok &= skm.CreateLine(x2, z1, 0, x2, z2, 0) is not None
    ok &= skm.CreateLine(x2, z2, 0, x1, z2, 0) is not None
    ok &= skm.CreateLine(x1, z2, 0, x1, z1, 0) is not None
    return ok
def feat(m, plane, draw, depth):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    fm = api.cast('IFeatureManager', m.FeatureManager)
    while skm.ActiveSketch is not None: skm.InsertSketch(True)
    prev = last_sketch(m)
    m.ClearSelection2(True); ext.SelectByID2(plane, 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True)
    skm.AddToDB = True; skm.DisplayWhenAdded = False
    ok = draw(skm)
    skm.AddToDB = False; skm.DisplayWhenAdded = True
    skm.InsertSketch(True)
    cur = last_sketch(m)
    if not ok or cur == prev: return False
    m.ClearSelection2(True); ext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    return fm.FeatureExtrusion3(True, False, False, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False) is not None
def newpart(fn):
    try:
        m,_ = resolve(app, DocSelector(path=os.path.join(D, fn))); api.activate(app, m); return m, False
    except Exception:
        m = api.cast('IModelDoc2', api.dyn(app).NewDocument(TPL, 0, 0, 0)); api.activate(app, m); return m, True
def props(m, fn, title, spec, qty, remark, mat):
    pd = api.cast('IPartDoc', m); pd.SetMaterialPropertyName2('', MAT, mat); m.ForceRebuild3(False)
    ext = api.cast('IModelDocExtension', m.Extension)
    cpm = api.cast('ICustomPropertyManager', ext.CustomPropertyManager(''))
    for k, v in [('TITLE', title), ('SPEC', spec), ("QT'Y", qty), ('RELATION NO.', 'S30000MU0'), ('PROJECT NO.', 'S00000MU0'),
                 ('APPROVED', '박종창'), ('CHECKED', '정상현'), ('DISIGNED', '전혜리'), ('REMARK', remark),
                 ('Material', '"SW-Material@' + fn + '"'), ('중량', '"SW-Mass@' + fn + '"')]:
        cpm.Add3(k, 30, v, 1)
    api.dyn(m).DeleteCustomInfo2('', 'DATE'); cpm.Add3('DATE', 64, today, 1)
# 1) S30013 전동볼밸브 (근사: 밸브몸통 Ø70xH110 수직 + 액추에이터 박스 100x100x140 상부 측면)
m, new = newpart('S30013MU0.SLDPRT')
print('== S30013 전동볼밸브', '신규' if new else '재생성')
ok1 = feat(m, '윗면', lambda s: s.CreateCircleByRadius(0, 0, 0, 0.035) is not None, 0.110)
ok2 = feat(m, '정면', lambda s: rect_lines(s, -0.050, 0.110, 0.050, 0.250), 0.100)
print('몸통', ok1, '액추에이터', ok2)
pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
props(m, 'S30013MU0.SLDPRT', 'MOTOR BALL VALVE', 'KITZ EA100-UTE-40A', '1', '전동볼밸브 40A 구매품(근사형상)', 'STS 316')
print('box', [round(v*1000,1) for v in pd.GetPartBox(True)])
print('save', write.save_model(app, m, out_path=os.path.join(D,'S30013MU0.SLDPRT') if new else None)['errors'])
# 2) S30014 주름관 (근사: Ø48 x 350)
m, new = newpart('S30014MU0.SLDPRT')
print('== S30014 주름관', '신규' if new else '재생성')
ok1 = feat(m, '윗면', lambda s: (s.CreateCircleByRadius(0,0,0, 0.024) is not None) and (s.CreateCircleByRadius(0,0,0, 0.020) is not None), 0.350)
if not ok1:
    ok1 = feat(m, '윗면', lambda s: s.CreateCircleByRadius(0,0,0, 0.024) is not None, 0.350)
print('관', ok1)
pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
props(m, 'S30014MU0.SLDPRT', 'FLEX HOSE', '40A CORRUGATED L350', '1', '스테인리스 주름관+PT나사 40A 구매품(근사형상)', 'STS 316')
print('box', [round(v*1000,1) for v in pd.GetPartBox(True)])
print('save', write.save_model(app, m, out_path=os.path.join(D,'S30014MU0.SLDPRT') if new else None)['errors'])
# 3) S30000에 삽입: 배출구 아래 (밸브 -718~-608 몸통, 호스 -1068~-718)
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
INS = []
if not any(n.startswith('S30013') for n in C): INS.append(('S30013MU0.SLDPRT', (0.0, -0.718, 0.0)))
if not any(n.startswith('S30014') for n in C): INS.append(('S30014MU0.SLDPRT', (0.0, -1.068, 0.0)))
for fn, t in INS:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D, fn)]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[next(n for n in C if n.startswith('S30006'))]
ST = {2:'미구속',3:'완전정의',4:'과구속'}
for n in sorted(C):
    if n.startswith(('S30013','S30014')):
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
print('오류', aext.GetWhatsWrongCount())
print('상태:', {n: ST.get(c.GetConstrainedStatus(), c.GetConstrainedStatus()) for n, c in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
import re
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and re.match(r'^S[0-9]', d['title'].upper()):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
read.snapshot(DocSelector(path=os.path.join(D,'S00000MU0.SLDASM')), ['front'], S)
print('snap ok')
