import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
fm = api.cast('IFeatureManager', m.FeatureManager); pd = api.cast('IPartDoc', m)
def wipe():
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
def last_sketch():
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def extrude(depth, down=False):
    m.ClearSelection2(True); ext.SelectByID2(last_sketch(), 'SKETCH', 0,0,0, False, 0, None, 0)
    ff = fm.FeatureExtrusion3(True, False, down, 0, 0, depth, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
    return ff is not None
def sk_top(draw):
    m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); draw(skm); skm.InsertSketch(True)
print('== S30008 절곡 커버 2T'); wipe()
sk_top(lambda s: s.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0))
print('상판', extrude(0.002))
B1, B2 = 0.248, 0.250
STRIPS = [(-B2, -B2, -B1, B2), (B1, -B2, B2, B2), (-B1, B1, B1, B2), (-B1, -B2, B1, -B1)]
downs = []
for (x1, z1, x2, z2) in STRIPS:
    sk_top(lambda s, a=x1, b=z1, c=x2, d=z2: s.CreateCornerRectangle(a, b, 0, c, d, 0))
    downs.append(extrude(0.025, down=True))
print('스커트 하향 4:', downs)
m.ForceRebuild3(False)
bx = [round(v*1000,1) for v in pd.GetPartBox(True)]
mass = api.cast('IMassProperty', ext.CreateMassProperty()).Mass
print('box', bx, '| 바디', len(pd.GetBodies2(0, True) or []), '| mass %.3f' % mass)
pd.SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
cpm = api.cast('ICustomPropertyManager', ext.CustomPropertyManager(''))
cpm.Add3('SPEC', 30, 'PL 2T BENDING', 1)
print('save', write.save_model(app, m)['errors'])
if not all(downs) or bx[1] > -20:
    sys.exit('스커트 실패 — 중단(수동 검토 필요)')
# 어셈블리: 덮개/경첩/손잡이 재배치 (덮개 밑면 768 유지, 상판 768~770, 스커트 743~768)
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {2:'미구속',3:'완전정의',4:'과구속'}
# 관련 메이트/컴포넌트 정리 후 재삽입
f = api.cast('IFeature', am.FirstFeature()); old=[]
while f:
    if f.GetTypeName2()=='MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            m2 = api.cast('IMate2', s.GetSpecificFeature2())
            for i in range(m2.GetMateEntityCount()):
                e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
                if c is not None and api.cast('IComponent2', c).Name2.startswith(('S30008','S30009','S30011')): old.append(s.Name); break
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
for nm in old:
    am.ClearSelection2(True)
    if aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
for n in list(C):
    if n.startswith(('S30008MU0-','S30009MU0-','S30011MU0-')):
        am.ClearSelection2(True)
        if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0): print('삭제', n, aext.DeleteSelection2(0))
am.ForceRebuild3(False)
INS = [
 ('S30008MU0.SLDPRT', (-0.2375, 0.768, -0.2375)),
 ('S30009MU0.SLDPRT', (-0.340, 0.7805, 0.008)),
 ('S30009MU0.SLDPRT', (-0.195, 0.7805, 0.008)),
 ('S30011MU0.SLDPRT', (-0.2975, 0.770, -0.430)),
]
for fn, t in INS:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D, fn)]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[next(n for n in C if n.startswith('S30006'))]
for n in sorted(C):
    if n.startswith(('S30008MU0-','S30009MU0-','S30011MU0-')):
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
