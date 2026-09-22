import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); m,_ = resolve(app, DocSelector(path=os.path.join(D,'S30002MU0.SLDPRT')))
pd = api.cast('IPartDoc', m); ext = api.cast('IModelDocExtension', m.Extension)
api.activate(app, m)
skm = api.cast('ISketchManager', m.SketchManager)
# 스케치1 편집 진입
f = api.cast('IFeature', m.FirstFeature()); prof = None
while f:
    if f.Name == '스케치1': prof = f
    f = api.cast('IFeature', f.GetNextFeature())
m.ClearSelection2(True)
ok = ext.SelectByID2('스케치1', 'SKETCH', 0,0,0, False, 0, None, 0); print('select sketch', ok)
m.EditSketch()
sk = api.cast('ISketch', prof.GetSpecificFeature2())
lines = []
for s in sk.GetSketchSegments() or []:
    s = api.cast('ISketchSegment', s)
    if s.GetType()==0:
        ln = api.cast('ISketchLine', s); a_ = api.cast('ISketchPoint', ln.GetStartPoint2()); b_ = api.cast('ISketchPoint', ln.GetEndPoint2())
        lines.append((s, (round(a_.X*1000,1), round(a_.Y*1000,1)), (round(b_.X*1000,1), round(b_.Y*1000,1))))
print('lines:', [(a,b) for _,a,b in lines])
def seg_at(p):  # p에 끝점이 있는 라인들
    return [s for s,a,b in lines if a==p or b==p]
smgr = api.cast('ISelectionMgr', m.SelectionManager)
for corner in [(595.0,-595.0), (-595.0,-595.0), (-595.0,595.0)]:
    pair = seg_at(corner)
    if len(pair) != 2: print('corner', corner, 'lines', len(pair), 'SKIP'); continue
    m.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData())
    api.cast('IEntity', pair[0]).Select4(False, sd); api.cast('IEntity', pair[1]).Select4(True, sd)
    arc = skm.CreateFillet(0.0025, 1)
    print('fillet at', corner, 'OK' if arc is not None else 'FAIL')
skm.InsertSketch(True)  # 스케치 종료
rc = m.ForceRebuild3(False); print('rebuild', rc, '| 오류', ext.GetWhatsWrongCount())
print('box', [round(v*1000,1) for v in pd.GetPartBox(True)])
print('mass %.2f kg' % api.cast('IMassProperty', ext.CreateMassProperty()).Mass)
r = ext.GetWhatsWrong()
if r and r[1]: print('whats wrong:', [(api.cast('IFeature', x).Name, c) for x, c in zip(r[1], r[2])])
