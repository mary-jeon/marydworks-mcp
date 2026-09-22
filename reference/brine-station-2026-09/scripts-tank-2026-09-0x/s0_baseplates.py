import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
TPL = r'c:\solidworks data\00. <USER> 솔리드웍스 템플릿\01. 문서 템플릿\이텍 Part.prtdot'
app = api.get_app()
def last_sketch(m):
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def make_plate(fn, half, holes, title, spec):
    try:
        m,_ = resolve(app, DocSelector(path=os.path.join(D, fn))); api.activate(app, m); new=False
        ext = api.cast('IModelDocExtension', m.Extension)
        # wipe
        for _ in range(3):
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
    except Exception:
        m = api.cast('IModelDoc2', api.dyn(app).NewDocument(TPL, 0, 0, 0)); api.activate(app, m); new=True
        ext = api.cast('IModelDocExtension', m.Extension)
    skm = api.cast('ISketchManager', m.SketchManager); fm = api.cast('IFeatureManager', m.FeatureManager)
    m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
    skm.InsertSketch(True); skm.CreateCornerRectangle(-half, -half, 0, half, half, 0); skm.InsertSketch(True)
    m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
    ff = fm.FeatureExtrusion3(True, False, False, 0, 0, 0.009, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
    print(' ', fn, '판', ff is not None)
    for hx, hz in holes:
        m.ClearSelection2(True)
        ok = ext.SelectByID2('', 'FACE', 0.0, 0.009, 0.0, False, 0, None, 0)
        skm.InsertSketch(True); skm.CreateCircleByRadius(hx, hz, 0, 0.007); skm.InsertSketch(True)
        m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
        fc = fm.FeatureCut4(True, False, False, 0, 0, 0.009, 0.009, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
        if fc is None: print('   구멍 실패', hx, hz)
    pd = api.cast('IPartDoc', m); pd.SetMaterialPropertyName2('', MAT, 'SS 275'); m.ForceRebuild3(False)
    cpm = api.cast('ICustomPropertyManager', ext.CustomPropertyManager(''))
    import datetime
    today = datetime.date.today().strftime('%Y-%m-%d')
    rel = 'S10000MU0' if fn.startswith('S10011') else 'S20000MU0'
    for k, v in [('TITLE', title), ('SPEC', spec), ("QT'Y", '4'), ('RELATION NO.', rel), ('PROJECT NO.', 'S00000MU0'),
                 ('APPROVED', '박종창'), ('CHECKED', '정상현'), ('DISIGNED', '전혜리'), ('REMARK', 'M12 세트앵커'),
                 ('Material', '"SW-Material@' + fn + '"'), ('중량', '"SW-Mass@' + fn + '"')]:
        cpm.Add3(k, 30, v, 1)
    api.dyn(m).DeleteCustomInfo2('', 'DATE'); cpm.Add3('DATE', 64, today, 1)
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], 'mass %.2f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    print('  save', write.save_model(app, m, out_path=os.path.join(D, fn) if new else None)['errors'])
print('== S10011 BODY 베이스 플레이트 200x200x9, 4-M12')
make_plate('S10011MU0.SLDPRT', 0.100, [(0.070,0.070),(0.070,-0.070),(-0.070,0.070),(-0.070,-0.070)], 'BASE PLATE-01', 'PL 200x200x9T')
print('== S20012 사다리 베이스 플레이트 150x150x9, 2-M12')
make_plate('S20012MU0.SLDPRT', 0.075, [(0.050,0.0),(-0.050,0.0)], 'BASE PLATE-02', 'PL 150x150x9T')
# ---- S10000에 4장 (기둥 하부, up=-X → 회전 필요)
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S10000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IConfiguration', cm.ActiveConfiguration)
rootc = api.cast('IComponent2', root.GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in rootc.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
POS = [(-0.725, 0.0), (0.725, 0.0), (-0.725, -2.786), (0.725, -2.786)]  # (Y, Z) 기둥 중심
have = sum(1 for n in C if n.startswith('S10011'))
if have == 0:
    for R in ([0,1,0, -1,0,0, 0,0,1], [0,-1,0, 1,0,0, 0,0,1]):
        y0, z0 = POS[0]
        a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D,'S10011MU0.SLDPRT')]),
                         VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, R + [1.100, y0, z0, 1,0,0,0]),
                         VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
        am.ForceRebuild3(False); C = comps()
        n = next(n for n in C if n.startswith('S10011'))
        b = [round(v*1000) for v in C[n].GetBox(False, False)]
        print('회전 시험', R[:6], 'box', b)
        if 1099 <= b[0] <= 1101 or 1099 <= b[3] <= 1101 and (b[3]-b[0]) == 9 or (b[3]-b[0])==9:
            good = (b[3]-b[0])==9 and b[0] >= 1099
            if good:
                print('  방향 OK'); break
        am.ClearSelection2(True)
        if aext.SelectByID2(n + '@S10000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
        am.ForceRebuild3(False); C = comps()
    C = comps()
    Rgood = R
    for y0, z0 in POS[1:]:
        a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D,'S10011MU0.SLDPRT')]),
                         VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, list(Rgood) + [1.100, y0, z0, 1,0,0,0]),
                         VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
    am.ForceRebuild3(False); C = comps()
col = C['S10001MU0-1']
for n in sorted(C):
    if n.startswith('S10011'):
        print(n, 'box', [round(v*1000) for v in C[n].GetBox(False, False)])
        if C[n].GetConstrainedStatus() != 3:
            am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
            f1 = api.cast('IFace2', (api.cast('IBody2', C[n].GetBody()).GetFaces() or [None])[0])
            f2 = api.cast('IFace2', (api.cast('IBody2', col.GetBody()).GetFaces() or [None])[0])
            api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
            r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
            m2, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
            print('  잠금 err', err)
am.ForceRebuild3(False)
print('S10000 오류', aext.GetWhatsWrongCount())
print('save S10000', write.save_model(app, am)['errors'])
# ---- S20000에 4장 (타워 기둥 하부, 로컬 up=+Y → identity, 판을 y -9..0로: ty=-0.009)
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S20000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension); api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager)
rootc = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps2(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in rootc.GetChildren() or []}
C = comps2(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
POS2 = [(0.3375, 1.0175), (-0.3375, 1.0175), (0.3375, 2.1425), (-0.3375, 2.1425)]
if not any(n.startswith('S20012') for n in C):
    for x0, z0 in POS2:
        a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D,'S20012MU0.SLDPRT')]),
                         VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, x0, -0.009, z0, 1,0,0,0]),
                         VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps2()
leg = C.get('S20002MU0-3') or next(C[n] for n in C if n.startswith('S20002'))
for n in sorted(C):
    if n.startswith('S20012'):
        print(n, 'box', [round(v*1000) for v in C[n].GetBox(False, False)])
        if C[n].GetConstrainedStatus() != 3:
            am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
            f1 = api.cast('IFace2', (api.cast('IBody2', C[n].GetBody()).GetFaces() or [None])[0])
            f2 = api.cast('IFace2', (api.cast('IBody2', leg.GetBody()).GetFaces() or [None])[0])
            api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
            r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
            m2, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
            print('  잠금 err', err)
am.ForceRebuild3(False)
print('S20000 오류', aext.GetWhatsWrongCount())
print('save S20000', write.save_model(app, am)['errors'])
# ---- 최상위 재생성·저장
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S00000MU0.SLDASM'))); api.activate(app, am); am.ForceRebuild3(False)
print('S00000 오류', api.cast('IModelDocExtension', am.Extension).GetWhatsWrongCount())
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and d['title'].upper().startswith(('S0','S1','S2')):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
