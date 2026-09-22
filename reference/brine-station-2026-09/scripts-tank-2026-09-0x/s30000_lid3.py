import sys, os; sys.stdout.reconfigure(encoding='utf-8')
exec(open('journal/s30000_place.py', encoding='utf-8').read().split("lid = C['S30006MU0-1']")[0])
exec(open('journal/s30000_lid2.py', encoding='utf-8').read().split("keep = {")[0].split("C = comps(); lid")[0])  # (no-op guard)
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
# 1) 판 밑면 ↔ 벽 상단 (anti-aligned)
big = sorted(faces_of(lid), key=lambda f: -f['A'])[:2]
wall_top = pick(wall, [0,1,0], 1, 730)
def try_face(fd):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fd['face']).Select4(False, sd); api.cast('IEntity', wall_top['face']).Select4(True, sd)
    r = a.AddMate5(0, 1, False, 0,0,0,0,0,0,0,0, False, False, 0); ok = isinstance(r, tuple) and r[0] is not None and int(r[1])==1
    am.ForceRebuild3(False); bb=[round(v*1000) for v in lid.GetBox(False,False)]; return ok, bb
ok, bb = try_face(big[0])
if not (ok and 690 <= bb[1] and bb[4] <= 740):
    delete_mates([n for n in lid_mate_names() if n not in keep]); am.ForceRebuild3(False); ok, bb = try_face(big[1])
print('face mate', ok, 'lid box Y', bb[1], bb[4])
# 2) 뚜껑 기준면 법선(어셈블리 좌표) 계산
T = list(api.cast('IMathTransform', lid.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]
def plane_normal(name):
    f = api.cast('IFeature', lid.FeatureByName(name)); rp = api.cast('IRefPlane', f.GetSpecificFeature2()); pt = list(api.cast('IMathTransform', rp.Transform).ArrayData)
    n = pt[6:9]; return [round(sum(n[k]*R[k][i] for k in range(3)),2) for i in range(3)]
normals = {p: plane_normal(p) for p in ('정면','윗면','우측면')}; print('lid plane normals (asm):', normals)
for p, n in normals.items():
    if abs(n[0]) > 0.9: mate_planes(lid.Name2, p, f'{p}→X 정렬(우측면)'.replace('(우측면)','')) if False else None
def mate_plane_to(comp_name, plane, asm_plane, label):
    am.ClearSelection2(True); ok1 = aext.SelectByID2(f'{plane}@{comp_name}@S30000MU0','PLANE',0,0,0,False,1,None,0); ok2 = aext.SelectByID2(asm_plane,'PLANE',0,0,0,True,1,None,0)
    r = a.AddMate5(0, 2, False, 0,0,0,0,0,0,0,0, False, False, 0); print(f'  {label}: sel {ok1},{ok2} ->', 'OK' if (isinstance(r, tuple) and r[0] is not None and int(r[1])==1) else r[1] if isinstance(r, tuple) else r)
for p, n in normals.items():
    if abs(n[0]) > 0.9: mate_plane_to(lid.Name2, p, '우측면', f'뚜껑 {p}(법선 X)↔우측면')
    if abs(n[2]) > 0.9: mate_plane_to(lid.Name2, p, '정면', f'뚜껑 {p}(법선 Z)↔정면')
am.ClearSelection2(True); am.ForceRebuild3(False); print('오류', aext.GetWhatsWrongCount())
for n, c in comps().items():
    bb=[round(v*1000) for v in c.GetBox(False,False)]; print(f'  {n:18s} X{bb[0]}..{bb[3]} Y{bb[1]}..{bb[4]} Z{bb[2]}..{bb[5]}')
