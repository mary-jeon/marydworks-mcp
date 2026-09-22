import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); am,_ = resolve(app, DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')))
TYPES = {0:'일치',1:'동심',2:'수직',3:'평행',5:'거리',6:'각도'}
f = api.cast('IFeature', am.FirstFeature())
while f:
    if f.GetTypeName2() == 'MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            m2 = api.cast('IMate2', s.GetSpecificFeature2())
            ents = []
            for i in range(m2.GetMateEntityCount()):
                e = api.cast('IMateEntity2', m2.MateEntity(i)); c = e.ReferenceComponent
                cn = api.cast('IComponent2', c).Name2 if c else '-'
                rt = e.ReferenceType2  # 1=point? 2=face 4=plane...
                nm = '?'
                try:
                    ref = e.Reference
                    if ref is not None:
                        if rt == 4: nm = api.cast('IFeature', ref).Name
                        elif rt == 2:
                            fc = api.cast('IFace2', ref); sur = api.cast('ISurface', fc.GetSurface())
                            if sur.IsPlane():
                                import math
                                n = [round(v,2) for v in fc.Normal]; b = fc.GetBox()
                                nm = f'면 n={n}'
                            else: nm = '곡면'
                except Exception as ex: nm = type(ex).__name__
                ents.append(f'{cn}:{nm}')
            print(f'{s.Name:8s} {TYPES.get(m2.Type, m2.Type):3s} align={m2.Alignment} | ' + ' <-> '.join(ents))
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
