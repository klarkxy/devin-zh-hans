# -*- coding: utf-8 -*-
"""Verify w32.json against webapp-todo.json lines 5601-6000."""
import json, io, re, collections

SRC = r'H:/Archive/devin-zh-hans/tools/data/webapp-todo.json'
OUT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/w32.json'
DUMP = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/_w32_pairs.txt'
START, COUNT = 5600, 400

raw = open(OUT, 'rb').read()
print('BOM:', raw[:3] == b'\xef\xbb\xbf')
text = raw.decode('utf-8')

lines = io.open(SRC, encoding='utf-8').read().split('\n')
seg = lines[START:START + COUNT]
src_keys = []
for ln in seg:
    obj = json.loads('{' + ln.strip().rstrip(',') + '}')
    src_keys.append(list(obj.keys())[0])

out = json.loads(text)
out_keys = list(out.keys())
fails, warns = [], []

# 1 count / order / exact key text
if len(src_keys) != COUNT:
    fails.append('source range size %d != %d' % (len(src_keys), COUNT))
if out_keys != src_keys:
    fails.append('KEY ORDER/TEXT MISMATCH')
    for i, (a, b) in enumerate(zip(src_keys, out_keys)):
        if a != b:
            fails.append('  first diff idx %d line %d\n    src=%r\n    out=%r' % (i, 5601 + i, a, b))
            break
    if len(out_keys) != len(src_keys):
        fails.append('  length %d vs %d' % (len(out_keys), len(src_keys)))

# 2 placeholders multiset
ph = re.compile(r'\{\{[^{}]*\}\}')
for i, k in enumerate(src_keys):
    a = collections.Counter(ph.findall(k))
    b = collections.Counter(ph.findall(out.get(k, '')))
    if a != b:
        fails.append('PLACEHOLDER mismatch line %d: %r\n  key=%s\n  val=%s' % (5601 + i, k[:60], dict(a), dict(b)))

# 3 tags preserved (including <icon />, <button>, <lnk>)
tag = re.compile(r'</?[A-Za-z][A-Za-z0-9_]*(?:\s+[^<>]*)?/?>')
for i, k in enumerate(src_keys):
    a = collections.Counter(tag.findall(k))
    b = collections.Counter(tag.findall(out.get(k, '')))
    if a != b:
        fails.append('TAG mismatch line %d: %r\n  key=%s\n  val=%s' % (5601 + i, k[:70], dict(a), dict(b)))

# 4 forbidden / empty / control chars
for k, v in out.items():
    if '"' in v:
        fails.append('ASCII double quote in value: %r' % k[:50])
    if '\\' in v:
        fails.append('backslash in value: %r' % k[:50])
    if not v.strip():
        fails.append('empty value: %r' % k[:50])
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', v):
        fails.append('control char in value: %r' % k[:50])

# 5 identity translations must be brand/technical only
brand_ok = {'OAuth', 'Okta', 'OpenAI', 'OpenID Connect', 'Op...'}
ELLIPSIS_VERBATIM = {'Op...'}
same = [k for k, v in out.items() if k == v]
unexpected = [k for k in same if k not in brand_ok]
print('identity translations:', sorted(same))
if unexpected:
    fails.append('unexpected untranslated: %r' % unexpected)

# 6 sentence-final punctuation follows the source
def endkind(s):
    s = s.rstrip()
    if s.endswith('。'):
        return 'full'
    if s.endswith('？'):
        return 'q'
    if s.endswith('……'):
        return 'ell'
    return 'none'

for i, k in enumerate(src_keys):
    v = out.get(k, '')
    ks = k.rstrip()
    if k in ELLIPSIS_VERBATIM:
        # intentionally kept verbatim: truncated fragment, no translatable content
        # (matches the existing w07.json entry for the same key)
        continue
    if ks.endswith('...') or ks.endswith('…'):
        if not v.rstrip().endswith('……'):
            fails.append('source ends with ellipsis but value does not: line %d %r -> %r' % (5601 + i, k[:50], v[:50]))
    elif ks.endswith('.'):
        if not v.rstrip().endswith('。'):
            fails.append('source ends with "." but value does not: line %d %r -> %r' % (5601 + i, k[:50], v[:50]))
    elif ks.endswith('?'):
        if not v.rstrip().endswith('？'):
            fails.append('source ends with "?" but value does not: line %d %r -> %r' % (5601 + i, k[:50], v[:50]))
    else:
        if v.rstrip().endswith('。') or v.rstrip().endswith('？'):
            fails.append('source has no final period but value does: line %d %r -> %r' % (5601 + i, k[:60], v[:60]))

# 7 formatting
if not re.search(r'\}\n$', text):
    fails.append('file does not end with closing brace + newline')
if ',\n}' in text:
    fails.append('trailing comma before closing brace')
bad_indent = [l[:40] for l in text.split('\n')[1:-2] if l and not l.startswith('  "')]
if bad_indent:
    fails.append('bad indent lines: %r' % bad_indent[:5])

# 8 spacing/style warns
for k, v in out.items():
    if re.search(r'[\u4e00-\u9fa5],', v) or re.search(r'[\u4e00-\u9fa5]\.(?![a-zA-Z0-9])', v):
        warns.append(('halfwidth punct', k[:40], v[:50]))
    if re.search(r'[\u4e00-\u9fa5][A-Za-z0-9]', v) and not re.search(r'[A-Za-z0-9][\u4e00-\u9fa5]', ''):
        pass  # noqa: spacing is checked by eye below
    if '\u60a8' in v:
        fails.append('polite-ni violation (您): %r' % v[:40])

# dump pairs for alignment review
with io.open(DUMP, 'w', encoding='utf-8', newline='\n') as fh:
    for i, k in enumerate(src_keys):
        fh.write('%d\t%s\n\t=> %s\n' % (5601 + i, k, out[k]))

print('---- RESULT ----')
print('source entries :', len(src_keys))
print('output entries :', len(out_keys))
print('keys identical & in order :', out_keys == src_keys)
print('empty/dup check :', len(set(out_keys)) == len(out_keys))
print('warnings :', len(warns))
for w in warns[:10]:
    print('   warn:', w)
if fails:
    print('FAILURES (%d):' % len(fails))
    for f in fails:
        print(' -', f)
else:
    print('ALL CHECKS PASSED')
