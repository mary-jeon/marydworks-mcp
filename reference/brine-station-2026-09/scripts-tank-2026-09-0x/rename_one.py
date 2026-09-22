import sys, os, json, time; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write; from sw.models import DocSelector
D = r'<CAD_DIR>'
old, new = sys.argv[1], sys.argv[2]
tgt = DocSelector(path=os.path.join(D, old + '.SLDPRT')); par = DocSelector(path=os.path.join(D, 'S10000MU0.SLDASM'))
t0 = time.time()
r = write.rename_document(tgt, par, new, False, [], None, True, True, None)
refs = [x for x in r['open_referencing_docs'] if x != 'S10000MU0.SLDASM']
if refs: print('STOP: 예상 밖 참조 문서', refs); sys.exit(2)
a = write.rename_document(tgt, par, new, False, [], None, True, False, r['plan_id'])
print('applied component', a['renamed_component'], '-> backup', a['backup'], flush=True)
s = write.save(a['change_set_id'], None, None, False)
for x in s['saved']: print('saved', x['title'], 'err', x['errors'], 'warn', x['warnings'], x.get('references') or '', x.get('warning') or '')
newp, oldp = os.path.join(D, new + '.SLDPRT'), os.path.join(D, old + '.SLDPRT')
print('disk: new exists', os.path.exists(newp), '| old exists', os.path.exists(oldp), '| %.0fs' % (time.time() - t0))
