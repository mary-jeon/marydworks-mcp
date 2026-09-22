import sys, os; sys.stdout.reconfigure(encoding='utf-8')
exec(open('journal/s30000_place.py', encoding='utf-8').read().split("lid = C['S30006MU0-1']")[0])
C = comps(); lid = C['S30006MU0-1']; wall = next(C[n] for n in C if n.startswith('S30002MU0-'))
def lid_mate_names():
    out=[]; f = api.cast('IFeature', am.FirstFeature())
    while f:
        if f.GetTypeName2()=='MateGroup':
            s = api.cast('IFeature', f.GetFirstSubFeature())
            while s:
                m2 = api.cast('IMate2', s.GetSpecificFeature2())
                try:
                    ents = [api.cast('IMateEntity2', m2.MateEntity(i)) for i in range(m2.GetMateEntityCount())]
                    if any(e.ReferenceComponent and api.cast('IComponent2', e.ReferenceComponent).Name2 == 'S30006MU0-1' for e in ents): out.append(s.Name)
                except Exception: pass
                s = api.cast('IFeature', s.GetNextSubFeature())
        f = api.cast('IFeature', f.GetNextFeature())
    return out
keep = {'일치31','일치32','일치33'}
delete_mates([n for n in lid_mate_names() if n not in keep]); am.ForceRebuild3(False)
big = sorted(faces_of(lid), key=lambda f: -f['A'])[:2]; print('largest faces:', [(f['n'], f['c'], f['A']) for f in big])
wall_top = pick(wall, [0,1,0], 1, 730)
def try_face(fd):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fd['face']).Select4(False, sd); api.cast('IEntity', wall_top['face']).Select4(True, sd)
    r = a.AddMate5(0, 1, False, 0,0,0,0,0,0,0,0, False, False, 0); ok = isinstance(r, tuple) and r[0] is not None and int(r[1])==1
    am.ForceRebuild3(False); bb=[round(v*1000) for v in lid.GetBox(False,False)]; print('  mate', 'OK' if ok else r, '| lid box Y', bb[1], '..', bb[4], 'Z', bb[2], '..', bb[5]); return ok, bb
ok, bb = try_face(big[0])
if not (ok and bb[1] >= 690 and bb[4] <= 740):
    delete_mates([n for n in lid_mate_names() if n not in keep]); am.ForceRebuild3(False)
    ok, bb = try_face(big[1])
mate_planes(lid.Name2, '정면', '정면 정렬'); mate_planes(lid.Name2, '우측면', '우측면 정렬')
am.ClearSelection2(True); am.ForceRebuild3(False); print('오류', aext.GetWhatsWrongCount())
for n, c in comps().items():
    bb=[round(v*1000) for v in c.GetBox(False,False)]; print(f'  {n:18s} X{bb[0]}..{bb[3]} Y{bb[1]}..{bb[4]} Z{bb[2]}..{bb[5]}')
