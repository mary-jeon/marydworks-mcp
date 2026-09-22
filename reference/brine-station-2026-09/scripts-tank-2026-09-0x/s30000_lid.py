import sys, os; sys.stdout.reconfigure(encoding='utf-8')
exec(open('journal/s30000_place.py', encoding='utf-8').read().split("lid = C['S30006MU0-1']")[0])   # 헬퍼 재사용 (벽 삽입 부분은 이미 존재하므로 건너뜀)
C = comps(); lid = C['S30006MU0-1']; wall = next(C[n] for n in C if n.startswith('S30002MU0-'))
keep = {'일치31','일치32','일치33'}
names = [api.cast('IFeature', api.cast('IMate2', mt)).Name if False else None for mt in []]
# 뚜껑 메이트 이름 수집: MateGroup 순회하며 엔티티에 S30006이 포함된 것
lid_mates = []
f = api.cast('IFeature', am.FirstFeature())
while f:
    if f.GetTypeName2()=='MateGroup':
        s = api.cast('IFeature', f.GetFirstSubFeature())
        while s:
            m2 = api.cast('IMate2', s.GetSpecificFeature2())
            try:
                ents = [api.cast('IMateEntity2', m2.MateEntity(i)) for i in range(m2.GetMateEntityCount())]
                if any(e.ReferenceComponent and api.cast('IComponent2', e.ReferenceComponent).Name2 == 'S30006MU0-1' for e in ents): lid_mates.append(s.Name)
            except Exception: pass
            s = api.cast('IFeature', s.GetNextSubFeature())
    f = api.cast('IFeature', f.GetNextFeature())
print('lid mates:', lid_mates)
delete_mates([n for n in lid_mates if n not in keep]); am.ForceRebuild3(False)
big = sorted([fd for fd in faces_of(lid) if abs(fd['n'][1]) == 1.0], key=lambda f: -f['A'])[:2]
print('lid big faces:', [(f['n'], f['c'], f['A']) for f in big])
under = min(big, key=lambda f: f['c'][1]) if abs(big[0]['c'][1]-big[1]['c'][1]) > 0.5 else big[0]
wall_top = pick(wall, [0,1,0], 1, 730)
am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
api.cast('IEntity', under['face']).Select4(False, sd); api.cast('IEntity', wall_top['face']).Select4(True, sd)
r = a.AddMate5(0, 1, False, 0,0,0,0,0,0,0,0, False, False, 0); print('뚜껑 판 밑면↔벽 상단 (anti-aligned):', 'OK' if (isinstance(r, tuple) and r[0] is not None and int(r[1])==1) else r)
am.ForceRebuild3(False)
mate_planes(lid.Name2, '정면', '정면 정렬'); mate_planes(lid.Name2, '우측면', '우측면 정렬')
am.ClearSelection2(True); am.ForceRebuild3(False); print('오류', aext.GetWhatsWrongCount())
for n, c in comps().items():
    bb=[round(v*1000) for v in c.GetBox(False,False)]; print(f'  {n:18s} X{bb[0]}..{bb[3]} Y{bb[1]}..{bb[4]} Z{bb[2]}..{bb[5]}')
