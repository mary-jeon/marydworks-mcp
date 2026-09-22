import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps(); ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
smgr = api.cast('ISelectionMgr', am.SelectionManager)
# 1) 삽입 (없으면)
need = []
if not any(n.startswith('S30007MU0-') for n in C): need.append((os.path.join(D,'S30007MU0.SLDPRT'), (-0.2375, 0.740, -0.2375)))
if not any(n.startswith('S30009MU0-') for n in C):
    need.append((os.path.join(D,'S30009MU0.SLDPRT'), (-0.340, 0.748, 0.008)))
    need.append((os.path.join(D,'S30009MU0.SLDPRT'), (-0.195, 0.748, 0.008)))
for path, t in need:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [path]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
for n in sorted(C):
    if n.startswith(('S30007','S30009')):
        b = C[n].GetBox(False, False); print(n, 'box', [round(v*1000,1) for v in b])
# 2) 잠금 메이트: 새 부품 ↔ 뚜껑(S30006)
lid = C['S30006MU0-1']
def lock(n):
    c = C[n]
    if c.GetConstrainedStatus() == 3: print(n, '이미 완전정의'); return
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark = 1
    f1 = api.cast('IFace2', (api.cast('IBody2', c.GetBody()).GetFaces() or [None])[0])
    f2 = api.cast('IFace2', (api.cast('IBody2', lid.GetBody()).GetFaces() or [None])[0])
    api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
    r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
    m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    am.ForceRebuild3(False)
    print(n, '잠금 err=', err, '→', ST.get(C[n].GetConstrainedStatus()))
for n in sorted(C):
    if n.startswith(('S30007','S30009')): lock(n)
# 3) 속성
import datetime
today = datetime.date.today().strftime('%Y-%m-%d')
PROPS = {
 'S30000MU0.SLDASM': ('BRINE TANK', 'STS 304', '1'),
 'S30001MU0.SLDPRT': ('HOPPER PANEL', 'PL 5T', '4'),
 'S30002MU0.SLDPRT': ('TANK WALL', 'PL 5T', '1'),
 'S30003MU0.SLDPRT': ('MOUNT WING', 'PL 6T', '1'),
 'S30005MU0.SLDPRT': ('OUTLET', 'PT 1-1/2\"', '1'),
 'S30006MU0.SLDPRT': ('TANK LID', 'PL 5T', '1'),
 'S30007MU0.SLDPRT': ('FILL CURB', 'FB 25x4.5', '1'),
 'S30008MU0.SLDPRT': ('FILL COVER', 'PL 5T', '1'),
 'S30009MU0.SLDPRT': ('WELD HINGE', 'D16x60', '2'),
}
for fn, (title, spec, qty) in PROPS.items():
    m,_ = resolve(app, DocSelector(path=os.path.join(D, fn)))
    cpm = api.cast('ICustomPropertyManager', api.cast('IModelDocExtension', m.Extension).CustomPropertyManager(''))
    for k, v in [('TITLE', title), ('SPEC', spec), ("QT'Y", qty)]:
        rc = cpm.Add3(k, 30, v, 1)  # swCustomPropertyReplaceValue
        if rc not in (0,1): print(' prop rc', fn, k, rc)
    api.dyn(m).DeleteCustomInfo2('', 'DATE')
    rc = cpm.Add3('DATE', 64, today, 1)
    if rc not in (0,1): print(' DATE rc', fn, rc)
print('속성 기입 완료', today)
# 4) 간섭·저장
am.ForceRebuild3(False)
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
print('상태:', {n: ST.get(c.GetConstrainedStatus()) for n, c in comps().items()})
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and (d['title'].upper().startswith('S300') or d['title'].upper().startswith('S30000')):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
snap = read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso'], S)
print('snap', len(snap['files']))
