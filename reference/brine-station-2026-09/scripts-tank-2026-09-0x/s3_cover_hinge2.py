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
def sketch_top(m, draw, plane='윗면'):
    ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
    m.ClearSelection2(True); ext.SelectByID2(plane, 'PLANE', 0,0,0, False, 0, None, 0)
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
def cut_last(m, depth):
    ext = api.cast('IModelDocExtension', m.Extension); fm = api.cast('IFeatureManager', m.FeatureManager)
    m.ClearSelection2(True); ext.SelectByID2(last_sketch(m), 'SKETCH', 0,0,0, False, 0, None, 0)
    fc = fm.FeatureCut4(True, False, False, 0, 0, depth, depth, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
    return fc is not None
def report(m):
    pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension); m.ForceRebuild3(False)
    print('  box', [round(v*1000,1) for v in pd.GetPartBox(True)], '| 바디', len(pd.GetBodies2(0, True) or []),
          '| 오류', ext.GetWhatsWrongCount(), '| mass %.3f' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
    print('  save', write.save_model(app, m)['errors'])
# 0) 커브 확인
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30007MU0.SLDPRT')))
pd = api.cast('IPartDoc', m)
print('S30007 box', [round(v*1000,1) for v in pd.GetPartBox(True)],
      'mass %.3f' % api.cast('IMassProperty', api.cast('IModelDocExtension', m.Extension).CreateMassProperty()).Mass)
# 1) S30008: 블록(500, 0~20) -> 하부 3중 사각 컷(520/476.5/471.5, 깊이 15) => 판 15~20 + 날 0~15
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
print('== S30008'); wipe(m)
sketch_top(m, lambda s: s.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0))
print('  블록', extrude_last(m, 0.020))
sketch_top(m, lambda s: (s.CreateCornerRectangle(-0.260,-0.260,0, 0.260,0.260,0),
                         s.CreateCornerRectangle(-0.23825,-0.23825,0, 0.23825,0.23825,0),
                         s.CreateCornerRectangle(-0.23575,-0.23575,0, 0.23575,0.23575,0)))
print('  하부 컷', cut_last(m, 0.015))
report(m)
# 2) S30009: 일반 경첩 — 윗날개(y -2~0, z -25~2) + 옆날개(z 0~2, y -33.5~0) + 너클 Ø8 (z=-x_sk 매핑)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30009MU0.SLDPRT'))); api.activate(app, m)
print('== S30009 경첩'); wipe(m)
sketch_top(m, lambda s: s.CreateCornerRectangle(-0.002, -0.002, 0, 0.025, 0.0, 0), plane='우측면')
print('  윗날개', extrude_last(m, 0.060))
sketch_top(m, lambda s: s.CreateCornerRectangle(-0.002, -0.0335, 0, 0.0, 0.0, 0), plane='우측면')
print('  옆날개', extrude_last(m, 0.060))
sketch_top(m, lambda s: s.CreateCircleByRadius(-0.0015, 0.0015, 0, 0.004), plane='우측면')
print('  너클', extrude_last(m, 0.060))
report(m)
# 3) 어셈블리
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am); am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
# 힌지 삭제 후 재삽입 (기하 변경으로 잠금 메이트 무효)
for n in list(C):
    if n.startswith('S30009MU0-'):
        am.ClearSelection2(True)
        if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0):
            print('힌지 삭제', n, aext.DeleteSelection2(0))
am.ForceRebuild3(False)
# 덮개 거리 메이트: 무효 시 삭제·재생성
f = api.cast('IFeature', am.FirstFeature()); dang=[]
while f:
    if f.GetTypeName2()=='MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            ec = s.GetErrorCode2(True); ec = ec[0] if isinstance(ec, tuple) else ec
            if ec: dang.append((s.Name, ec))
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
print('오류 메이트:', dang)
for nm, _ in dang:
    am.ClearSelection2(True)
    if aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
am.ForceRebuild3(False); C = comps()
covN = next(n for n in C if n.startswith('S30008MU0-')); lidN = next(n for n in C if n.startswith('S30006MU0-'))
def faces_of(c):
    T = list(api.cast('IMathTransform', c.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]; out=[]
    for fx in api.cast('IBody2', c.GetBody()).GetFaces() or []:
        fx = api.cast('IFace2', fx); s = api.cast('ISurface', fx.GetSurface())
        if not s.IsPlane(): continue
        n = list(fx.Normal); n=[round(sum(n[k]*R[k][i] for k in range(3)),2) for i in range(3)]
        b = list(fx.GetBox()); pts=[[sum(p[k]*R[k][i] for k in range(3))+t[i] for i in range(3)] for p in [(b[i],b[j],b[k]) for i in (0,3) for j in (1,4) for k in (2,5)]]
        cen=[round(sum(p[i] for p in pts)/8*1000,1) for i in range(3)]; out.append({'face':fx,'n':n,'c':cen,'A':round(fx.GetArea()*1e6)})
    return out
def rollback_last():
    f = api.cast('IFeature', am.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s: last=s.Name; s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    am.ClearSelection2(True)
    if aext.SelectByID2(last, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
    print('   롤백', last)
if C[covN].GetConstrainedStatus() != 3:
    for align, flip in [(1,False),(1,True),(0,False),(0,True)]:
        cb_c = [fx for fx in faces_of(C[covN]) if fx['n']==[0,-1,0]]
        lt_c = [fx for fx in faces_of(C[lidN]) if fx['n']==[0,1,0] and abs(fx['c'][1]-740)<1]
        cb = max(cb_c, key=lambda fx: fx['A']); lt = max(lt_c, key=lambda fx: fx['A'])
        am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
        api.cast('IEntity', cb['face']).Select4(False, sd); api.cast('IEntity', lt['face']).Select4(True, sd)
        r = a.AddMate5(5, align, flip, 0.0275, 0.0275, 0.0275, 1,1, 0,0,0, False, False, 0)
        m2, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
        am.ForceRebuild3(False)
        b = [round(v*1000,1) for v in C[covN].GetBox(False, False)]
        ok = (m2 is not None and err==1 and abs(b[4]-772.5)<0.3 and abs(b[1]-752.5)<0.3)
        print('덮개 거리27.5 align', align, 'flip', flip, 'err', err, 'box', b, '채택' if ok else '')
        if ok: break
        if m2 is not None: rollback_last(); am.ForceRebuild3(False)
# 경첩 재삽입: (tx, 774.5, 12.5), 잠금
for tx in (-0.340, -0.195):
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D,'S30009MU0.SLDPRT')]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, tx, 0.7745, 0.0125, 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[lidN]
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
# 재질/속성 갱신
for fn, spec in [('S30008MU0','PL 5T'), ('S30009MU0','HINGE 60x2T')]:
    m,_ = resolve(app, DocSelector(path=os.path.join(D, fn + '.SLDPRT')))
    api.cast('IPartDoc', m).SetMaterialPropertyName2('', MAT, 'STS 316')
    cpm = api.cast('ICustomPropertyManager', api.cast('IModelDocExtension', m.Extension).CustomPropertyManager(''))
    cpm.Add3('SPEC', 30, spec, 1); m.ForceRebuild3(False)
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
