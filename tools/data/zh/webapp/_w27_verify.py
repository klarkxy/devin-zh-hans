# -*- coding: utf-8 -*-
"""Verify w27.json against webapp-todo.json lines 3601-4000."""
import json, io, re, collections

SRC = r'H:/Archive/devin-zh-hans/tools/data/webapp-todo.json'
OUT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/w27.json'

raw_bytes = open(OUT, 'rb').read()
print('BOM:', raw_bytes[:3] == b'\xef\xbb\xbf')
text = raw_bytes.decode('utf-8')

src_lines = open(SRC, encoding='utf-8').read().split('\n')
seg = src_lines[3600:4000]

src_keys = []
for line in seg:
    obj = json.loads('{' + line.strip().rstrip(',') + '}')
    src_keys.append(list(obj.keys())[0])

out = json.loads(text)
out_keys = list(out.keys())

fails = []

# 1 key count / order / exact text
if len(src_keys) != 400:
    fails.append('source range size %d != 400' % len(src_keys))
if out_keys != src_keys:
    fails.append('KEY ORDER/TEXT MISMATCH')
    for i, (a, b) in enumerate(zip(src_keys, out_keys)):
        if a != b:
            fails.append('  first diff at idx %d line %d\n    src=%r\n    out=%r' % (i, 3601 + i, a, b))
            break
    if len(out_keys) != len(src_keys):
        fails.append('  length %d vs %d' % (len(out_keys), len(src_keys)))

# 2 placeholders multiset
ph = re.compile(r'\{\{[^{}]*\}\}')
for i, k in enumerate(src_keys):
    if k not in out:
        continue
    v = out[k]
    a = collections.Counter(ph.findall(k))
    b = collections.Counter(ph.findall(v))
    if a != b:
        fails.append('PLACEHOLDER mismatch line %d: %r\n  key=%s\n  val=%s' % (3601 + i, k[:60], dict(a), dict(b)))

# 3 tags preserved
tag = re.compile(r'</?[A-Za-z][A-Za-z0-9_]*(?:\s*/)?>')
for i, k in enumerate(src_keys):
    if k not in out:
        continue
    a = collections.Counter(tag.findall(k))
    b = collections.Counter(tag.findall(out[k]))
    if a != b:
        fails.append('TAG mismatch line %d: %r\n  key=%s\n  val=%s' % (3601 + i, k[:70], dict(a), dict(b)))

# 4 forbidden chars in values
for k, v in out.items():
    if '"' in v:
        fails.append('ASCII double quote in value: %r' % (k[:50]))
    if '\\' in v:
        fails.append('backslash in value: %r' % (k[:50]))
    if not v.strip():
        fails.append('empty value: %r' % (k[:50]))
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', v):
        fails.append('control char in value: %r' % (k[:50]))

# 5 untranslated leftovers: value identical to key AND key looks like english prose
brand_exact_ok = {
    'Firefox', 'Flask', 'Gerrit', 'Gerrit URL', 'Git', 'GitHub', 'GitHub API URL',
    'GitHub Enterprise', 'GitHub Enterprise app', 'GitHub Enterprise apps',
    'GitHub Enterprise installation', 'GitLab', 'GitLab (gitlab.com)', 'Gmail',
    'Google', 'Google Analytics', 'Google Chat', 'Google Chrome', 'GPT', 'GPT-5.6 Sol',
    'Gemini', 'GraphQL endpoint', 'HTTP', 'HTTP {{status}}', 'Fusion Fast', 'HackMIT 2026',
}
same = [k for k, v in out.items() if k == v]
unexpected = [k for k in same if k not in brand_exact_ok]
print('identity translations (brands/technical):', len(same))
if unexpected:
    fails.append('unexpected untranslated: %r' % unexpected)

# 6 formatting: 2-space indent, no trailing comma, ends with '}\n'
lines = text.split('\n')
bad_indent = [l[:40] for l in lines[1:-2] if l and not l.startswith('  "')]
if bad_indent:
    fails.append('bad indent lines: %r' % bad_indent[:5])
if not re.search(r'\}\n$', text):
    fails.append('file does not end with closing brace + newline')
if ',\n}' in text:
    fails.append('trailing comma before closing brace')

# 7 no half-width comma/period directly between chinese chars (light sanity, warn only)
warn = []
for k, v in out.items():
    if re.search(r'[\u4e00-\u9fa5],', v) or re.search(r'[\u4e00-\u9fa5]\.(?![a-zA-Z0-9])', v):
        warn.append((k[:50], v[:60]))

print('---- RESULT ----')
print('source entries :', len(src_keys))
print('output entries :', len(out_keys))
print('keys identical & in order :', out_keys == src_keys)
print('half-width punct warnings :', len(warn))
for w in warn[:5]:
    print('   warn:', w)
if fails:
    print('FAILURES (%d):' % len(fails))
    for f in fails:
        print(' -', f)
else:
    print('ALL CHECKS PASSED')
