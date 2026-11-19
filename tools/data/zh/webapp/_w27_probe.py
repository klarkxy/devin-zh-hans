import json, glob, os

SRC = r'H:/Archive/devin-zh-hans/tools/data/webapp-todo.json'
OUT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp'

lines = open(SRC, encoding='utf-8').read().split('\n')
hits = [(i, l) for i, l in enumerate(lines, 1) if '\\n' in l]
print('total source lines containing backslash-n:', len(hits))
for i, l in hits[:15]:
    print(i, l[:150])

# which existing batch already contains such keys?
allkeys = {}
for f in sorted(glob.glob(os.path.join(OUT, '*.json'))):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        print('skip', f, e)
        continue
    for k, v in d.items():
        allkeys.setdefault(f, []).append(k)

for f, ks in allkeys.items():
    nl = [k for k in ks if '\\n' in k or '\n' in k]
    if nl:
        print('BATCH', os.path.basename(f), 'multiline keys:', len(nl))
        for k in nl[:5]:
            print('   KEY:', k.replace('\n', '\\n')[:120])
            print('   VAL:', repr(json.dumps({k: json.load(open(f, encoding='utf-8'))[k]}, ensure_ascii=False))[:220])

# also check range 3601-4000 for multiline
seg = lines[3600:4000]
print('range size:', len(seg))
print('range multiline count:', sum(1 for l in seg if '\\n' in l))
for l in seg:
    if '\\n' in l:
        print('  ', l[:160])
