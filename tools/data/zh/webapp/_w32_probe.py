# -*- coding: utf-8 -*-
"""Probe: consistency re-use for w32 range (webapp-todo.json lines 5601-6000)."""
import json, glob, io, os

SRC = r'H:/Archive/devin-zh-hans/tools/data/webapp-todo.json'
OUT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/_w32_probe.txt'

lines = io.open(SRC, encoding='utf-8').read().split('\n')
seg = lines[5600:6000]
src_keys = []
for ln in seg:
    obj = json.loads('{' + ln.strip().rstrip(',') + '}')
    src_keys.append(list(obj.keys())[0])

corpus = {}
for f in sorted(glob.glob(r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/*.json')):
    try:
        d = json.load(io.open(f, encoding='utf-8'))
    except Exception:
        continue
    for k, v in d.items():
        corpus.setdefault(k, (os.path.basename(f), v))

out = io.open(OUT, 'w', encoding='utf-8')
out.write('RANGE SIZE: %d  first=%r  last=%r\n' % (len(src_keys), src_keys[0], src_keys[-1]))
dup = [(k, corpus[k]) for k in src_keys if k in corpus]
out.write('KEY OVERLAP WITH EXISTING BATCHES: %d\n' % len(dup))
for k, (f, v) in dup:
    out.write('  [%s] %r => %r\n' % (f, k, v))

terms = ['My Workspace', 'blueprint', 'artifact', 'side chat', 'side pane', 'tracker',
         'plan', 'full seat', 'rail', 'tier', 'Mirror', 'nboard', 'slug', 'Operations',
         'Useful', 'memory', 'team plan', 'pull request', 'incident', 'run-as', 'bypass',
         'Smart', 'wrap', 'fit', 'secret', 'hook', 'Customize', 'finding', 'Atlas',
         'Unleash', 'red-team', 'staging', 'budget', 'responder', 'mention', 'whitelist']
for t in terms:
    hits = [(k, v) for k, (f, v) in corpus.items() if t.lower() in k.lower()]
    out.write('\n== %s == (%d)\n' % (t, len(hits)))
    for k, v in hits[:14]:
        out.write('   %r => %r\n' % (k, v))
out.close()
print('ok')
