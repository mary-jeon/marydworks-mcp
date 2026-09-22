import sys, os; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write
app = api.get_app()
LIB = os.path.normpath(r'Z:\_CellModeling').lower()
targets = {}  # parent doc path -> [component names]
docs = api.list_docs(app, with_raw=True, light=True)
for d in docs:
    md = api.cast('IModelDoc2', d['_raw'])
    if int(md.GetType()) != 2: continue
    cm = api.cast('IConfigurationManager', md.ConfigurationManager)
    try: root = api.cast('IComponent2', api.cast('IConfiguration', cm.ActiveConfiguration).GetRootComponent3(True))
    except Exception: continue
    names = []
    for c in root.GetChildren() or []:
        c = api.cast('IComponent2', c)
        p = c.GetPathName() or ''
        if os.path.normpath(p).lower().startswith(LIB): names.append(c.Name2)
    if names: targets[d['title']] = names
print('사용처:', targets)
for title, names in targets.items():
    md = next(api.cast('IModelDoc2', d['_raw']) for d in docs if d['title'] == title)
    api.activate(app, md)
    ext = api.cast('IModelDocExtension', md.Extension)
    base = title.rsplit('.', 1)[0]
    for n in names:
        md.ClearSelection2(True)
        ok = ext.SelectByID2(n + '@' + base, 'COMPONENT', 0,0,0, False, 0, None, 0)
        dele = ext.DeleteSelection2(0) if ok else False
        print(title, '에서', n, '삭제:', ok, dele)
    md.ForceRebuild3(False)
    print('  오류', ext.GetWhatsWrongCount())
    try: print('  save', title, write.save_model(app, md)['errors'])
    except Exception as e: print('  save 실패', title, e)
# 라이브러리 문서 닫기
for d in api.list_docs(app, with_raw=False, light=True):
    p = d.get('path') or ''
    if os.path.normpath(p).lower().startswith(LIB):
        app.CloseDoc(d['title']); print('닫음', d['title'])
# 최종 dirty 확인
left = [d['title'] for d in api.list_docs(app, with_raw=False, light=False) if d.get('dirty')]
print('남은 dirty:', left)
