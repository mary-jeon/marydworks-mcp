import sys, os, pythoncom; sys.stdout.reconfigure(encoding='utf-8')
from win32com.client import VARIANT
from sw import api, read; from sw.models import DocSelector; from sw.selectors import resolve
D = r'<CAD_DIR>'
app = api.get_app(); sel = DocSelector(path=os.path.join(D,'S30000MU0.SLDASM')); am,_ = resolve(app, sel); a = api.cast('IAssemblyDoc', am); aext = api.cast('IModelDocExtension', am.Extension)
api.activate(app, am)
cm = api.cast('IConfigurationManager', am.ConfigurationManager); root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
def comps(): return {api.cast('IComponent2', c).Name2: api.cast('IComponent2', c) for c in root.GetChildren() or []}
C = comps()
# 1) 벽 삽입 (없으면)
if not any(n.startswith('S30002MU0-') for n in C):
    a.AddComponents3(VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, [os.path.join(D,'S30002MU0.SLDPRT')]), VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_R8, [1,0,0, 0,1,0, 0,0,1, 0.0,0.030,0.0, 1,0,0,0]), VARIANT(pythoncom.VT_ARRAY|pythoncom.VT_BSTR, ['']))
    am.ForceRebuild3(False); C = comps()
wall = next(C[n] for n in C if n.startswith('S30002MU0-')); bb=[round(v*1000) for v in wall.GetBox(False,False)]; print('wall', wall.Name2, bb)
# 2) 메이트 헬퍼
def faces_of(c):
    T = list(api.cast('IMathTransform', c.Transform2).ArrayData); R=[T[0:3],T[3:6],T[6:9]]; t=T[9:12]; out=[]
    for f in api.cast('IBody2', c.GetBody()).GetFaces() or []:
        f = api.cast('IFace2', f); s = api.cast('ISurface', f.GetSurface())
        if not s.IsPlane(): continue
        n = list(f.Normal); n=[round(sum(n[k]*R[k][i] for k in range(3)),2) for i in range(3)]
        b = list(f.GetBox()); pts=[[sum(p[k]*R[k][i] for k in range(3))+t[i] for i in range(3)] for p in [(b[i],b[j],b[k]) for i in (0,3) for j in (1,4) for k in (2,5)]]
        cen=[round(sum(p[i] for p in pts)/8*1000,1) for i in range(3)]; out.append({'face':f,'n':n,'c':cen,'A':round(f.GetArea()*1e6)})
    return out
def pick(c, n, axis, val, tol=1.5, biggest=True):
    hits=[fd for fd in faces_of(c) if fd['n']==n and abs(fd['c'][axis]-val)<tol]
    if not hits: raise RuntimeError(f'{c.Name2}: face n={n} {"xyz"[axis]}={val} not found; have {[(f["n"],f["c"],f["A"]) for f in faces_of(c) if f["n"]==n][:6]}')
    return max(hits, key=lambda f: f['A']) if biggest else hits[0]
smgr = api.cast('ISelectionMgr', am.SelectionManager)
def mate_faces(fa, fb, label):
    am.ClearSelection2(True); sd = api.cast('ISelectData', smgr.CreateSelectData()); sd.Mark=1
    api.cast('IEntity', fa['face']).Select4(False, sd); api.cast('IEntity', fb['face']).Select4(True, sd)
    r = a.AddMate5(0, 2, False, 0,0,0,0,0,0,0,0, False, False, 0); m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    print(f'  {label}: {"OK" if m is not None and err==1 else "FAIL err=%s"%err}'); return m is not None and err==1
def mate_planes(comp_name, plane, label):
    am.ClearSelection2(True)
    ok1 = aext.SelectByID2(f'{plane}@{comp_name}@S30000MU0', 'PLANE', 0,0,0, False, 1, None, 0); ok2 = aext.SelectByID2(plane, 'PLANE', 0,0,0, True, 1, None, 0)
    r = a.AddMate5(0, 2, False, 0,0,0,0,0,0,0,0, False, False, 0); m, err = (r[0], int(r[1])) if isinstance(r, tuple) else (r, -1)
    print(f'  {label} ({plane}, sel {ok1},{ok2}): {"OK" if m is not None and err==1 else "FAIL err=%s"%err}')
def delete_mates(names):
    for nm in names:
        am.ClearSelection2(True); ok = aext.SelectByID2(nm, 'MATE', 0,0,0, False, 0, None, 0); d = aext.DeleteSelection2(0) if ok else False; print(f'  delete {nm}: sel={ok} del={d}')
lid = C['S30006MU0-1']; out = C['S30005MU0-1']; fl = C['S30003MU0-1']; cone = C['S30001MU0-1']
# 벽: 중심 정렬 + 바닥면↔경사판 스텁 상단면
if len(wall.GetMates() or []) < 3:
    print('== 벽 S30002'); mate_planes(wall.Name2, '정면', '정면 정렬'); mate_planes(wall.Name2, '우측면', '우측면 정렬')
    wall_bot = pick(wall, [0,-1,0], 1, 30); stub_top = pick(cone, [0,1,0], 1, 30); mate_faces(wall_bot, stub_top, '벽 바닥↔스텁 상단')
else: print('벽 메이트 이미 있음')
# 뚜껑: 기존 메이트 삭제 → 정렬 2 + 밑면↔벽 상단
print('== 뚜껑 S30006'); delete_mates(['일치28','일치45','일치46']); am.ForceRebuild3(False)
mate_planes(lid.Name2, '정면', '정면 정렬'); mate_planes(lid.Name2, '우측면', '우측면 정렬')
lidY = [f for f in faces_of(lid) if f['n']==[0,-1,0]]; under = max(lidY, key=lambda f: f['A']); print('  lid underside candidate', under['c'], under['A'])
wall_top = pick(wall, [0,1,0], 1, 730); mate_faces(under, wall_top, '뚜껑 밑면↔벽 상단')
# 배출구: 기존 메이트 삭제 → 정렬 2 + 상면↔경사판 립 밑면
print('== 배출구 S30005'); delete_mates(['일치34']); am.ForceRebuild3(False)
mate_planes(out.Name2, '정면', '정면 정렬'); mate_planes(out.Name2, '우측면', '우측면 정렬')
top = pick(out, [0,1,0], 1, -305, tol=5); lip_bot = pick(cone, [0,-1,0], 1, -305, tol=1.5); mate_faces(top, lip_bot, '배출구 상면↔립 밑면')
# 플랜지판: 정렬 2 추가
print('== 플랜지판 S30003'); mate_planes(fl.Name2, '정면', '정면 정렬'); mate_planes(fl.Name2, '우측면', '우측면 정렬')
am.ClearSelection2(True); am.ForceRebuild3(False)
print('오류', aext.GetWhatsWrongCount())
for n, c in comps().items():
    bb=[round(v*1000) for v in c.GetBox(False,False)]; print(f'  {n:18s} X{bb[0]}..{bb[3]} Y{bb[1]}..{bb[4]} Z{bb[2]}..{bb[5]}')
