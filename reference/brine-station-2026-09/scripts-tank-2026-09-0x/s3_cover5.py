import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app()
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30008MU0.SLDPRT'))); api.activate(app, m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
fm = api.cast('IFeatureManager', m.FeatureManager); pd = api.cast('IPartDoc', m)
def wipe():
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
def last_sketch():
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
def cut_from_face(draw, pt, depth):
    m.ClearSelection2(True)
    ok = ext.SelectByID2('', 'FACE', pt[0], pt[1], pt[2], False, 0, None, 0)
    skm.InsertSketch(True); draw(skm); skm.InsertSketch(True)
    m.ClearSelection2(True); ext.SelectByID2(last_sketch(), 'SKETCH', 0,0,0, False, 0, None, 0)
    fc = fm.FeatureCut4(True, False, False, 0, 0, depth, depth, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
    return ok, fc is not None
print('== S30008 (4스트립 컷)'); wipe()
m.ClearSelection2(True); ext.SelectByID2('윗면', 'PLANE', 0,0,0, False, 0, None, 0)
skm.InsertSketch(True); skm.CreateCornerRectangle(-0.250,-0.250,0, 0.250,0.250,0); skm.InsertSketch(True)
m.ClearSelection2(True); ext.SelectByID2(last_sketch(), 'SKETCH', 0,0,0, False, 0, None, 0)
ff = fm.FeatureExtrusion3(True, False, False, 0, 0, 0.020, 0.0, False, False, False, False, 0.0, 0.0, False, False, False, False, True, True, True, 0, 0.0, False)
print('블록', ff is not None)
B = 0.23825  # 날 바깥 471.5/2 + ... 476.5/2
def strips(s):
    s.CreateCornerRectangle(-0.255, -0.255, 0, -B, 0.255, 0)      # W
    s.CreateCornerRectangle(B, -0.255, 0, 0.255, 0.255, 0)        # E
    s.CreateCornerRectangle(-B, B, 0, B, 0.255, 0)                # N
    s.CreateCornerRectangle(-B, -0.255, 0, B, -B, 0)              # S
ok, c1 = cut_from_face(strips, (0.245, 0.0, 0.245), 0.015)
print('컷1(4스트립) face', ok, 'cut', c1)
ok, c2 = cut_from_face(lambda s: s.CreateCornerRectangle(-0.23575,-0.23575,0, 0.23575,0.23575,0), (0.0, 0.0, 0.0), 0.015)
print('컷2(안쪽) face', ok, 'cut', c2)
pd.SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
bx = [round(v*1000,1) for v in pd.GetPartBox(True)]
mass = api.cast('IMassProperty', ext.CreateMassProperty()).Mass
print('box', bx, '| 바디', len(pd.GetBodies2(0, True) or []), '| mass %.3f' % mass)
print('save', write.save_model(app, m)['errors'])
if bx[1] > 0.5 or mass > 12: sys.exit('덮개 형상 실패 — 중단')
# 어셈블리 거리 메이트
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am); am.ForceRebuild3(False)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
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
for align, flip in [(1,False),(1,True),(0,False),(0,True)]:
    if C[covN].GetConstrainedStatus() == 3: break
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
am.ForceRebuild3(False)
print('오류:', aext.GetWhatsWrongCount())
print('상태:', {n: ST.get(c.GetConstrainedStatus()) for n, c in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and d['title'].upper().startswith('S300'):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso','front'], S)
print('snap ok')
