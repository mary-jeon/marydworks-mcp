import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = os.path.normpath('Z:/28. <PROJECT_NAME>/1_Modeling/S_BrineCharge Station')
app = api.get_app()
def inv_map(T, p):
    R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]
    return [sum(R[r][i]*(p[r]-t[r]) for r in range(3)) for i in range(3)]
# 1) S00000에서 패드 4개 중심(전역) → 탱크 로컬 → 윙 로컬
am,_ = resolve(app, DocSelector(path=os.path.join(D,'S00000MU0.SLDASM')))
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
pads = []
tankT = None
for c in root.GetChildren() or []:
    c = api.cast('IComponent2', c)
    if c.Name2.startswith('파트1^'):
        b = c.GetBox(False, False)
        pads.append(((b[0]+b[3])/2, (b[1]+b[4])/2, (b[2]+b[5])/2))
    if c.Name2.startswith('S30000'):
        tankT = list(api.cast('IMathTransform', c.Transform2).ArrayData)
print('패드 중심(전역 mm):', [[round(v*1000,1) for v in p] for p in pads])
locs = [inv_map(tankT, p) for p in pads]
print('탱크 로컬(mm):', [[round(v*1000,1) for v in p] for p in locs])
# 윙(S30003) 로컬: S30000 안 윙 컴포넌트 변환
tm,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
cm2 = api.cast('IConfigurationManager', tm.ConfigurationManager); root2 = api.cast('IComponent2', api.cast('IConfiguration', cm2.ActiveConfiguration).GetRootComponent3(True))
wing = next(api.cast('IComponent2', c) for c in root2.GetChildren() or [] if api.cast('IComponent2', c).Name2.startswith('S30003'))
wT = list(api.cast('IMathTransform', wing.Transform2).ArrayData)
wlocs = [inv_map(wT, p) for p in locs]
print('윙 로컬(mm):', [[round(v*1000,1) for v in p] for p in wlocs])
# 2) 윙에 Ø14 홀 4개 (윗면 y=6 면에서 컷)
m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30003MU0.SLDPRT'))); api.activate(app, m)
ext = api.cast('IModelDocExtension', m.Extension); skm = api.cast('ISketchManager', m.SketchManager)
fm = api.cast('IFeatureManager', m.FeatureManager); pd = api.cast('IPartDoc', m)
bx = [round(v*1000,1) for v in pd.GetPartBox(True)]
print('윙 파트 box:', bx)
ytop = bx[4]/1000.0
def last_sketch():
    f = api.cast('IFeature', m.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
while skm.ActiveSketch is not None: skm.InsertSketch(True)
made = 0
for (hx, hy, hz) in wlocs:
    prev = last_sketch()
    m.ClearSelection2(True)
    ok = ext.SelectByID2('', 'FACE', hx, ytop, hz, False, 0, None, 0)
    skm.InsertSketch(True)
    skm.AddToDB = True; skm.DisplayWhenAdded = False
    c = skm.CreateCircleByRadius(hx, hz, 0, 0.007)
    c2 = None
    if c is None:
        c2 = skm.CreateCircleByRadius(-hx, hz, 0, 0.007)
    skm.AddToDB = False; skm.DisplayWhenAdded = True
    skm.InsertSketch(True)
    cur = last_sketch()
    if cur == prev: print('홀 스케치 실패', round(hx*1000), round(hz*1000)); continue
    m.ClearSelection2(True); ext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    fc = fm.FeatureCut4(True, False, False, 0, 0, 0.006, 0.006, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
    print('윙 홀', round(hx*1000), round(hz*1000), 'face', ok, 'circle', c is not None, 'cut', fc is not None)
    if fc is not None: made += 1
m.ForceRebuild3(False)
mass = api.cast('IMassProperty', api.cast('IModelDocExtension', m.Extension).CreateMassProperty()).Mass
print('윙 홀 수', made, '| mass %.2f' % mass)
cpm = api.cast('ICustomPropertyManager', ext.CustomPropertyManager(''))
cpm.Add3('REMARK', 30, '4-D14 HOLE (M12 BOLT)', 1)
print('save', write.save_model(app, m)['errors'])
# 3) 패드(파트1^) 중심 Ø14 홀
pc = None
for c in root.GetChildren() or []:
    c = api.cast('IComponent2', c)
    if c.Name2.startswith('파트1^') and c.Name2.endswith('-1'):
        pc = c; break
pm = api.cast('IModelDoc2', pc.GetModelDoc2()); api.activate(app, pm)
pext = api.cast('IModelDocExtension', pm.Extension); pskm = api.cast('ISketchManager', pm.SketchManager)
pfm = api.cast('IFeatureManager', pm.FeatureManager)
pbx = [round(v*1000,1) for v in api.cast('IPartDoc', pm).GetPartBox(True)]
print('패드 파트 box:', pbx)
def plast():
    f = api.cast('IFeature', pm.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='ProfileFeature': last=f.Name
        f = api.cast('IFeature', f.GetNextFeature())
    return last
while pskm.ActiveSketch is not None: pskm.InsertSketch(True)
prev = plast()
pm.ClearSelection2(True)
ok = pext.SelectByID2('', 'FACE', 0.0, 0.0, pbx[5]/1000.0, False, 0, None, 0)
pskm.InsertSketch(True)
pskm.AddToDB = True; pskm.DisplayWhenAdded = False
cc = pskm.CreateCircleByRadius(0, 0, 0, 0.007)
pskm.AddToDB = False; pskm.DisplayWhenAdded = True
pskm.InsertSketch(True)
cur = plast()
if cur != prev:
    pm.ClearSelection2(True); pext.SelectByID2(cur, 'SKETCH', 0,0,0, False, 0, None, 0)
    fc = pfm.FeatureCut4(True, False, False, 0, 0, 0.007, 0.007, False, False, False, False, 0,0, False, False, False, False, False, True, True, True, True, False, 0, 0, False, False)
    print('패드 홀 face', ok, 'circle', cc is not None, 'cut', fc is not None)
else:
    print('패드 홀 스케치 실패')
pm.ForceRebuild3(False)
# 저장: 가상부품은 S00000 저장으로
api.activate(app, am); am.ForceRebuild3(False)
print('S00000 오류', api.cast('IModelDocExtension', am.Extension).GetWhatsWrongCount())
print('save S00000', write.save_model(app, am)['errors'])
import re
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and re.match(r'^S[0-9]', d['title'].upper()):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
