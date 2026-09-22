import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM'))); a = api.cast('IAssemblyDoc', am)
f = api.cast('IFeature', am.FirstFeature())
def walk(f, depth=0):
    while f:
        t = f.GetTypeName2()
        if t == 'MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s:
                yield s
                s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
for s in walk(f):
    m2 = api.cast('IMate2', s.GetSpecificFeature2())
    ents = []
    for i in range(m2.GetMateEntityCount()):
        e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
        ents.append((api.cast('IComponent2', c).Name2 if c else '-', e.ReferenceType2))
    ec = s.GetErrorCode2(True); ec = ec[0] if isinstance(ec, tuple) else ec
    print(f'{s.Name:8s} type={m2.Type} err={ec} sup={s.IsSuppressed()} {ents}')
