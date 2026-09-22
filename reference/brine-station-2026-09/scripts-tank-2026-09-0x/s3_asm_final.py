import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read, write; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
MAT = r'c:\solidworks data\00. retech 솔리드웍스 템플릿\05. 재질 데이터베이스\이텍.sldmat'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
smgr = api.cast('ISelectionMgr', am.SelectionManager)
ST = {1:'?',2:'미구속',3:'완전정의',4:'과구속',5:'해없음',6:'무효'}
def mates_referencing(prefixes):
    out=[]; f = api.cast('IFeature', am.FirstFeature())
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s:
                m2 = api.cast('IMate2', s.GetSpecificFeature2())
                for i in range(m2.GetMateEntityCount()):
                    e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
                    if c is not None and api.cast('IComponent2', c).Name2.startswith(prefixes): out.append(s.Name); break
                s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    return out
def del_mates(names):
    for nm in names:
        am.ClearSelection2(True)
        if aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0): aext.DeleteSelection2(0)
def rollback_last_mate():
    f = api.cast('IFeature', am.FirstFeature()); last=None
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s: last=s.Name; s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    del_mates([last]); print('   롤백', last)
def faces_of(c):
    T = list(api.cast('IMathTransform', c.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]; out=[]
    for f in api.cast('IBody2', c.GetBody()).GetFaces() or []:
        f = api.cast('IFace2', f); s = api.cast('ISurface', f.GetSurface())
        if not s.IsPlane(): continue
        n = list(f.Normal); n=[round(sum(n[k]*R[k][i] for k in range(3)),2) for i in range(3)]
        b = list(f.GetBox()); pts=[[sum(p[k]*R[k][i] for k in range(3))+t[i] for i in range(3)] for p in [(b[i],b[j],b[k]) for i in (0,3) for j in (1,4) for k in (2,5)]]
        cen=[round(sum(p[i] for p in pts)/8*1000,1) for i in range(3)]; out.append({'face':f,'n':n,'c':cen,'A':round(f.GetArea()*1e6)})
    return out
# 1) 덮개·힌지 옛 메이트/컴포넌트 정리
C = comps()
old = mates_referencing(('S30008MU0','S30009MU0'))
print('삭제할 메이트:', old); del_mates(old)
for n in list(C):
    if n.startswith('S30009MU0-'):
        am.ClearSelection2(True)
        if aext.SelectByID2(n + '@S30000MU0', 'COMPONENT', 0,0,0, False, 0, None, 0):
            print('컴포넌트 삭제', n, aext.DeleteSelection2(0))
am.ForceRebuild3(False); C = comps()
# 2) 덮개: 커브와 중심 정렬 + 밑면-뚜껑윗면 거리 25
curbN = next(n for n in C if n.startswith('S30007MU0-'))
covN = next(n for n in C if n.startswith('S30008MU0-'))
lidN = next(n for n in C if n.startswith('S30006MU0-'))
for pl in ('정면','우측면'):
    am.ClearSelection2(True)
    ok1 = aext.SelectByID2(pl + '@' + covN + '@S30000MU0', 'PLANE', 0,0,0, False, 1, None, 0)
    ok2 = aext.SelectByID2(pl + '@' + curbN + '@S30000MU0', 'PLANE', 0,0,0, True, 1, None, 0)
    r = a.AddMate5(0, 2, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
    m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    print('덮개', pl, '정렬 sel', ok1, ok2, 'err', err)
am.ForceRebuild3(False)
for align, flip in [(0,False),(0,True),(1,False),(1,True)]:
    cb_c = [f for f in faces_of(C[covN]) if f['n']==[0,-1,0]]
    lt_c = [f for f in faces_of(C[lidN]) if f['n']==[0,1,0] and abs(f['c'][1]-740)<1]
    cb = max(cb_c, key=lambda f: f['A']); lt = max(lt_c, key=lambda f: f['A'])
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', cb['face']).Select4(False, sd); api.cast('IEntity', lt['face']).Select4(True, sd)
    r = a.AddMate5(5, align, flip, 0.025, 0.025, 0.025, 1,1, 0,0,0, False, False, 0)
    m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    am.ForceRebuild3(False)
    b = [round(v*1000,1) for v in C[covN].GetBox(False, False)]
    ok = (m is not None and err==1 and abs(b[1]-765.0)<0.3)
    print('덮개 거리25 align', align, 'flip', flip, 'err', err, 'box', b, '채택' if ok else '')
    if ok: break
    if m is not None: rollback_last_mate(); am.ForceRebuild3(False)
# 3) 힌지 재삽입 + 벤트 삽입 + 잠금
ins = [(os.path.join(D,'S30009MU0.SLDPRT'), (-0.340, 0.7565, 0.0155)), (os.path.join(D,'S30009MU0.SLDPRT'), (-0.195, 0.7565, 0.0155))]
if not any(n.startswith('S30010MU0-') for n in C): ins.append((os.path.join(D,'S30010MU0.SLDPRT'), (0.300, 0.735, 0.300)))
for path, t in ins:
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [path]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, t[0],t[1],t[2], 1,0,0,0]),
                     VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
am.ForceRebuild3(False); C = comps()
lid = C[lidN]
for n in sorted(C):
    if n.startswith(('S30009MU0-','S30010MU0-')):
        b = [round(v*1000,1) for v in C[n].GetBox(False, False)]; print(n, 'box', b)
        if C[n].GetConstrainedStatus() != 3:
            am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
            f1 = api.cast('IFace2', (api.cast('IBody2', C[n].GetBody()).GetFaces() or [None])[0])
            f2 = api.cast('IFace2', (api.cast('IBody2', lid.GetBody()).GetFaces() or [None])[0])
            api.cast('IEntity', f1).Select4(False, sd); api.cast('IEntity', f2).Select4(True, sd)
            r = a.AddMate5(16, 0, False, 0,0,0, 1,1, 0,0,0, False, False, 0)
            m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
            print('  잠금 err', err)
am.ForceRebuild3(False)
# 4) 재질 STS 316
for fn in ['S30001MU0','S30002MU0','S30003MU0','S30005MU0','S30006MU0','S30007MU0','S30008MU0','S30009MU0','S30010MU0']:
    m,_ = resolve(app, DocSelector(path=os.path.join(D, fn + '.SLDPRT')))
    api.cast('IPartDoc', m).SetMaterialPropertyName2('', MAT, 'STS 316'); m.ForceRebuild3(False)
print('재질 STS 316 적용')
# 5) 속성
import datetime
today = datetime.date.today().strftime('%Y-%m-%d')
BASE = {'RELATION NO.': 'S30000MU0', 'PROJECT NO.': 'S00000MU0', 'APPROVED': '박종창', 'CHECKED': '정상현', 'DISIGNED': '전혜리'}
INFO = {
 'S30000MU0.SLDASM': ('BRINE TANK','STS 316','1'), 'S30001MU0.SLDPRT': ('HOPPER PANEL','PL 5T','4'),
 'S30002MU0.SLDPRT': ('TANK WALL','PL 5T','1'), 'S30003MU0.SLDPRT': ('MOUNT WING','PL 6T','1'),
 'S30005MU0.SLDPRT': ('OUTLET','PT 1-1/2"','1'), 'S30006MU0.SLDPRT': ('TANK LID','PL 5T','1'),
 'S30007MU0.SLDPRT': ('FILL CURB','L-RING 4.5T','1'), 'S30008MU0.SLDPRT': ('FILL COVER','PL 5T','1'),
 'S30009MU0.SLDPRT': ('WELD HINGE','D16x60','2'), 'S30010MU0.SLDPRT': ('VENT PIPE','25A','1'),
}
for fn, (title, spec, qty) in INFO.items():
    m,_ = resolve(app, DocSelector(path=os.path.join(D, fn)))
    cpm = api.cast('ICustomPropertyManager', api.cast('IModelDocExtension', m.Extension).CustomPropertyManager(''))
    props = dict(BASE); props.update({'TITLE': title, 'SPEC': spec, "QT'Y": qty, 'REMARK': ''})
    if fn.endswith('.SLDPRT'):
        props['Material'] = '"SW-Material@' + fn + '"'
        props['중량'] = '"SW-Mass@' + fn + '"'
    for k, v in props.items():
        rc = cpm.Add3(k, 30, v, 1)
        if rc not in (0,1): print(' prop rc', fn, k, rc)
    api.dyn(m).DeleteCustomInfo2('', 'DATE'); cpm.Add3('DATE', 64, today, 1)
print('속성 완료')
# 6) 최종 검사·저장·스냅샷
am.ForceRebuild3(False)
print('오류:', aext.GetWhatsWrongCount())
print('상태:', {n: ST.get(c.GetConstrainedStatus()) for n, c in comps().items()})
r2 = read.audit(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), None, True, 200, 120)
print('간섭:', [(i['components'], round(i['volume_mm3'],1)) for i in r2.get('interferences', [])])
for d in api.list_docs(app, with_raw=True, light=False):
    if d.get('dirty') and d['title'].upper().startswith('S300'):
        mm = api.cast('IModelDoc2', d['_raw']); print('save', d['title'], write.save_model(app, mm)['errors'])
S = r'<HOME>\AppData\Local\Temp\claude\Z--28------------------------------1-Modeling-S-BrineCharge-Station\fce0f6b5-cb07-4e3d-8de8-d54e6221bcfb\scratchpad\s3'
snap = read.snapshot(DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')), ['iso'], S)
print('snap ok')
