import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write
app = api.get_app()
LIB = os.path.normpath(r'Z:\_CellModeling').lower()
def lib_children(md):
    cm = api.cast('IConfigurationManager', md.ConfigurationManager)
    try: root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
    except Exception: return None
    out = []
    for c in root.GetChildren() or []:
        c = api.cast('IComponent2', c)
        p = os.path.normpath(c.GetPathName() or '').lower()
        if p.startswith(LIB): out.append((c.Name2, p))
    return out
docs = api.list_docs(app, with_raw=True, light=True)
# 비 S계열 어셈블리 전부에 undo 시도 (S계열은 우리 작업 undo 위험 — 제외)
for d in docs:
    t = d['title'].upper()
    md = api.cast('IModelDoc2', d['_raw'])
    if int(md.GetType()) != 2: continue
    if t.startswith('S0') or t.startswith('S1') or t.startswith('S2') or t.startswith('S3'): continue
    before = lib_children(md)
    if before is None: continue
    api.activate(app, md)
    n_undo = 0
    for i in range(60):
        try:
            ok = md.EditUndo2(1)
        except Exception:
            ok = False
        if not ok: break
        n_undo += 1
    md.ForceRebuild3(False)
    after = lib_children(md)
    if n_undo or (after and len(after) != len(before)):
        print(d['title'], 'undo', n_undo, '회 | 라이브러리 자식', len(before), '->', len(after))
print('--- undo 후 라이브러리 참조 현황')
for d in api.list_docs(app, with_raw=True, light=True):
    md = api.cast('IModelDoc2', d['_raw'])
    if int(md.GetType()) != 2: continue
    ch = lib_children(md)
    if ch: print(d['title'], len(ch), '개:', sorted(set(n.rsplit('-',1)[0] for n,_ in ch)))
