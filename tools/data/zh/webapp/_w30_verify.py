# -*- coding: utf-8 -*-
"""Verify w30.json against webapp-todo.json lines 4801-5200."""
import json, re, collections, sys

SRC = r'H:/Archive/devin-zh-hans/tools/data/webapp-todo.json'
OUT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/w30.json'

raw = open(OUT, 'rb').read()
print('BOM present      :', raw[:3] == b'\xef\xbb\xbf')
text = raw.decode('utf-8')

src_lines = open(SRC, encoding='utf-8').read().split('\n')
seg = src_lines[4800:5200]
src_keys = []
for line in seg:
    obj = json.loads('{' + line.strip().rstrip(',') + '}')
    src_keys.append(list(obj.keys())[0])

out = json.loads(text)
out_keys = list(out.keys())

fails = []

# 1 key set / order / exact characters
print('source entries   :', len(src_keys))
print('output entries   :', len(out_keys))
if len(src_keys) != 400:
    fails.append('source range size %d != 400' % len(src_keys))
if out_keys != src_keys:
    fails.append('KEY ORDER/TEXT MISMATCH')
    for i, (a, b) in enumerate(zip(src_keys, out_keys)):
        if a != b:
            fails.append('  first diff idx %d line %d\n    src=%r\n    out=%r' % (i, 4801 + i, a, b))
            break
    if len(out_keys) != len(src_keys):
        fails.append('  length %d vs %d' % (len(out_keys), len(src_keys)))
print('keys identical & in order :', out_keys == src_keys)

# 2 {{...}} placeholder multiset
ph = re.compile(r'\{\{[^{}]*\}\}')
for i, k in enumerate(src_keys):
    v = out.get(k, '')
    a, b = collections.Counter(ph.findall(k)), collections.Counter(ph.findall(v))
    if a != b:
        fails.append('PLACEHOLDER line %d key=%r\n  key=%s\n  val=%s' % (4801 + i, k[:50], dict(a), dict(b)))

# 3 <tag> multiset (incl. [[...]] markers)
tag = re.compile(r'</?[A-Za-z][A-Za-z0-9_]*(?:\s*/)?>|\[\[[^\]]*\]\]')
for i, k in enumerate(src_keys):
    v = out.get(k, '')
    a, b = collections.Counter(tag.findall(k)), collections.Counter(tag.findall(v))
    if a != b:
        fails.append('TAG line %d key=%r\n  key=%s\n  val=%s' % (4801 + i, k[:50], dict(a), dict(b)))
print('placeholders/tags checked :', len(src_keys))

# 4 forbidden characters / empties in values
for k, v in out.items():
    if '"' in v:
        fails.append('ASCII double quote in value: %r' % k[:60])
    if '\\' in v:
        fails.append('backslash in value: %r' % k[:60])
    if not v.strip():
        fails.append('empty value: %r' % k[:60])
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', v):
        fails.append('control char in value: %r' % k[:60])

# 5 identity translations whitelist (brands / person / model names)
brand_exact_ok = {
    'Mastodon', 'Maya Chen', 'Microsoft Entra ID', 'Microsoft Teams', 'NVIDIA T4',
    'Netlify', 'My Workspace',
    'Mythos 5.1 High', 'Mythos 5.1 Low', 'Mythos 5.1 Max', 'Mythos 5.1 Medium',
    'Mythos 5.1 XHigh', 'Mythos 5.2 High', 'Mythos 5.2 Low', 'Mythos 5.2 Max',
    'Mythos 5.2 Medium',
}
same = [k for k, v in out.items() if k == v]
unexpected = [k for k in same if k not in brand_exact_ok]
print('identity values  :', len(same), sorted(same)[:20])
if unexpected:
    fails.append('unexpected untranslated: %r' % unexpected)

# 6 formatting
lines = text.split('\n')
bad_indent = [l[:40] for l in lines[1:-2] if l and not l.startswith('  "')]
if bad_indent:
    fails.append('bad indent lines: %r' % bad_indent[:5])
if not re.search(r'\}\n$', text):
    fails.append('file does not end with closing brace + newline')
if ',\n}' in text:
    fails.append('trailing comma before closing brace')

# 7 CJK spacing spot check (warn only): ascii-word touching CJK without space
warn = []
for k, v in out.items():
    stripped = re.sub(r'\{\{[^{}]*\}\}', 'VAR', v)
    stripped = tag.sub('', stripped)
    if re.search(r'[\u4e00-\u9fa5][A-Za-z0-9]', stripped) or re.search(r'[A-Za-z0-9][\u4e00-\u9fa5]', stripped):
        warn.append((k[:46], v[:56]))
print('spacing warnings :', len(warn))
for w in warn:
    print('   warn:', w)

print('---- RESULT ----')
if fails:
    print('FAILURES (%d):' % len(fails))
    for f in fails:
        print(' -', f)
    sys.exit(1)
print('ALL CHECKS PASSED')
