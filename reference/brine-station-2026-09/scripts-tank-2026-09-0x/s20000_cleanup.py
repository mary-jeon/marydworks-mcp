"""S20000MU0 정리: 이름 8건 순서대로 → 속성 기재 → 파트 저장. 한 프로세스에서 실행(캐시 유지)."""
import sys, os, time, json; sys.stdout.reconfigure(encoding='utf-8')
from sw import api, write, read; from sw.models import DocSelector
D = r'<CAD_DIR>'
PAR = DocSelector(path=os.path.join(D, 'S20000MU0.SLDASM'))
TODAY = time.strftime('%Y.%m.%d')
PLAN = [  # (현재 파일명(확장자 없음), 새 이름, TITLE, SPEC)
    ('S20001MU0',                                          'S20001MU0', 'PLATE-01',   '3.2T'),
    ('S20004MU0',                                          'S20002MU0', 'SQ PIPE-01', '75x75x2.3T'),
    ('S20004MU0 - 복사본 (3) - 복사본',                     'S20003MU0', 'SQ PIPE-02', '75x75x2.3T'),
    ('S20004MU0 - 복사본 (2) - 복사본 - 복사본',             'S20004MU0', 'RD PIPE-01', 'Ø34x2.3T'),
    ('S20004MU0 - 복사본 (2) - 복사본 - 복사본 - 복사본',    'S20005MU0', 'RD PIPE-02', 'Ø34x2.3T'),
    ('S20004MU0 - 복사본 (2) - 복사본',                     'S20006MU0', 'SQ PIPE-03', '75x75x2.3T'),
    ('S20001MU0 - 복사본',                                 'S20007MU0', 'PLATE-02',   '4.5T'),
    ('S20004MU0 - 복사본 (2)',                             'S20008MU0', 'SQ PIPE-04', '75x75x2.3T'),
    ('S20004MU0 - 복사본 (3) - 복사본 - 복사본',             'S20009MU0', 'SQ PIPE-05', '75x75x2.3T'),
]
stage = sys.argv[1] if len(sys.argv) > 1 else 'all'
t_all = time.time()
if stage in ('rename', 'all'):
    for old, new, _, _ in PLAN:
        if old == new:
            continue
        if not os.path.exists(os.path.join(D, old + '.SLDPRT')) and os.path.exists(os.path.join(D, new + '.SLDPRT')):
            print(f'skip {old!r} -> {new} (이미 완료)', flush=True); continue
        t0 = time.time()
        tgt = DocSelector(path=os.path.join(D, old + '.SLDPRT'))
        r = write.rename_document(tgt, PAR, new, False, [], None, False, True, None)
        refs = [x for x in r['open_referencing_docs'] if x != 'S20000MU0.SLDASM']
        if refs:
            print('STOP: 예상 밖 참조 문서', old, refs); sys.exit(2)
        a = write.rename_document(tgt, PAR, new, False, [], None, False, False, r['plan_id'])
        s = write.save(a['change_set_id'], None, None, False)
        ok = os.path.exists(os.path.join(D, new + '.SLDPRT')) and not os.path.exists(os.path.join(D, old + '.SLDPRT'))
        print(f'rename {old!r} -> {new}: disk={"OK" if ok else "FAIL"} err={s["saved"][0]["errors"]} {time.time()-t0:.0f}s', flush=True)
        if not ok:
            sys.exit(3)
if stage in ('props', 'all'):
    b = read.bom(PAR, 'top_level', include_mass=False)
    inst = {r['part_number']: r['instances'] for r in b['rows']}
    print('BOM parts:', sorted(inst))
    docs, props_by = [], {}
    for _, new, title, spec in PLAN:
        docs.append(DocSelector(path=os.path.join(D, new + '.SLDPRT')))
        props_by[new] = {'TITLE': title, 'SPEC': spec, "QT'Y": str(inst.get(new, '')), 'DATE': TODAY}
    changed = []
    for sel in docs:
        name = os.path.splitext(os.path.basename(sel.path))[0]
        r = write.set_properties([sel], 'file', props_by[name], None, True, None)
        ch = r['documents'][0]['changes']
        if ch:
            write.set_properties([sel], 'file', props_by[name], None, False, r['plan_id'])
            changed.append(name)
        print(f'props {name}: ' + ', '.join(f"{c['name']} {c['before']!r}->{c['after']!r}" for c in ch) + (' | ' + '; '.join(r['warnings']) if r['warnings'] else ''), flush=True)
    for name in changed:
        s = write.save(None, DocSelector(path=os.path.join(D, name + '.SLDPRT')), None, False)
        print('saved', name, 'err', s['saved'][0]['errors'], flush=True)
print(f'total {time.time()-t_all:.0f}s')
