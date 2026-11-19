# -*- coding: utf-8 -*-
"""Independent verifier: source range vs w36.json."""
import io, json, re
from collections import Counter

SRC = r'H:\Archive\devin-zh-hans\tools\data\webapp-todo.json'
OUT = r'H:\Archive\devin-zh-hans\tools\data\zh\webapp\w36.json'
FIRST, LAST = 7201, 7600

# --- source keys, one per line, exact order ---
raw = io.open(SRC, encoding='utf-8').read()
lines = raw.split('\n')
src_keys = []
for n in range(FIRST, LAST + 1):
    line = lines[n - 1].strip()
    if line.endswith(','):
        line = line[:-1]
    obj = json.loads('{' + line + '}')
    src_keys.append(list(obj.keys())[0])

# --- output ---
blob = io.open(OUT, 'rb').read()
print('BOM:', blob[:3] == b'\xef\xbb\xbf')
print('ends with newline:', blob.endswith(b'\n'))
txt = blob.decode('utf-8')
pairs = json.loads(txt, object_pairs_hook=lambda kv: kv)
out_keys = [k for k, _ in pairs]
out_vals = [v for _, v in pairs]
out = dict(pairs)

ph = re.compile(r'\{\{.*?\}\}')
tag = re.compile(r'</?[A-Za-z][A-Za-z0-9]*>')
fails = []

if len(out_keys) != len(src_keys):
    fails.append('count: src=%d out=%d' % (len(src_keys), len(out_keys)))
if len(set(out_keys)) != len(out_keys):
    fails.append('duplicate keys in output')
if out_keys != src_keys:
    for i, (a, b) in enumerate(zip(src_keys, out_keys)):
        if a != b:
            fails.append('order/key mismatch at line %d:\n  src=%r\n  out=%r' % (FIRST + i, a, b))
            break
if set(out_keys) != set(src_keys):
    fails.append('key set differs: missing=%r extra=%r' % (
        sorted(set(src_keys) - set(out_keys))[:5], sorted(set(out_keys) - set(src_keys))[:5]))

for i, k in enumerate(src_keys):
    v = out.get(k, '')
    n = FIRST + i
    if not isinstance(v, str) or not v.strip():
        fails.append('empty value line %d' % n)
        continue
    if '"' in v:
        fails.append('halfwidth double quote in value line %d' % n)
    if '\\' in v:
        fails.append('backslash in value line %d' % n)
    a, b = Counter(ph.findall(k)), Counter(ph.findall(v))
    if a != b:
        fails.append('placeholder mismatch line %d: %r vs %r' % (n, sorted(a.elements()), sorted(b.elements())))
    a, b = Counter(tag.findall(k)), Counter(tag.findall(v))
    if a != b:
        fails.append('tag mismatch line %d: %r vs %r' % (n, sorted(a.elements()), sorted(b.elements())))

# indentation / formatting checks
bad_indent = [i + 1 for i, ln in enumerate(txt.split('\n')) if ln.startswith(' ') and not ln.startswith('  "')]
print('total entries:', len(out_keys))
print('formatting: non 2-space indent lines:', len(bad_indent))
print('src keys:', len(src_keys), '| out keys:', len(out_keys), '| identical order:', out_keys == src_keys)
print('placeholder multiset mismatches:', sum(1 for f in fails if f.startswith('placeholder')))
print('FAILS:', len(fails))
for f in fails[:20]:
    print(' -', f)
print('RESULT:', 'PASS' if not fails else 'FAIL')
