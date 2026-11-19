# -*- coding: utf-8 -*-
"""Verify w24.json against webapp-todo.json lines 2401-2800."""
import io
import json
import re
import sys

SRC = 'webapp-todo.json'
OUT = 'zh/webapp/w24.json'
START, END = 2401, 2800

raw_lines = io.open(SRC, encoding='utf-8').read().split('\n')
src_slice = raw_lines[START - 1:END]
print('source lines:', len(src_slice))

src_keys = []
for ln in src_slice:
    s = ln.strip()
    if s.startswith(','):
        s = s[1:].strip()
    assert s.startswith('"'), ln[:60]
    s = s[:-1] if s.endswith(',') else s
    assert s.endswith(': ""'), ln[:60]
    body = s[1:]
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '\\':
            i += 2
            continue
        if ch == '"':
            break
        i += 1
    ks_literal = body[:i]
    decoded = json.loads('"' + ks_literal + '"')
    src_keys.append((ks_literal, decoded))

out_raw = io.open(OUT, 'rb').read()
problems = []
if out_raw.startswith(b'\xef\xbb\xbf'):
    problems.append('BOM present')
text = out_raw.decode('utf-8')
try:
    out = json.loads(text)
except Exception as e:
    print('FATAL json error:', e)
    sys.exit(1)

out_keys = list(out)
out_lines = text.split('\n')
print('out entries:', len(out))

if len(out_keys) != len(src_keys):
    problems.append('count mismatch: src %d vs out %d' % (len(src_keys), len(out_keys)))

src_dec = [d for _, d in src_keys]
if src_dec != out_keys:
    for idx, (a, b) in enumerate(zip(src_dec, out_keys)):
        if a != b:
            problems.append('key mismatch at #%d: %r != %r' % (idx + 1, a, b))
            break
    extra = set(src_dec) ^ set(out_keys)
    problems.append('key set diff sample: %r' % (list(extra)[:4],))

# raw literal key text must match too (escapes byte-identical), by comparing
# the file's own key lines against source lines
body_lines = out_lines[:-1] if out_lines and out_lines[-1] == '' else out_lines
if len(body_lines) != len(src_slice) + 2:
    problems.append('line count out %d vs src %d' % (len(body_lines), len(src_slice) + 2))
if body_lines[0].strip() != '{' or body_lines[-1].strip() != '}':
    problems.append('brace lines wrong: %r / %r' % (body_lines[0], body_lines[-1]))
entry_lines = body_lines[1:-1]
for idx, (ln, (ks_lit, _)) in enumerate(zip(entry_lines, src_keys), 1):
    if not ln.startswith('  "'):
        problems.append('indent wrong at entry %d: %r' % (idx, ln[:80]))
    if not ln.startswith('  "' + ks_lit + '": '):
        problems.append('raw key line %d not byte-identical: %r' % (idx, ln[:90]))
    if idx < len(entry_lines):
        if not ln.endswith('",'):
            problems.append('entry %d missing trailing comma: %r' % (idx, ln[-40:]))
    else:
        if ln.endswith(',') or not ln.endswith('"'):
            problems.append('last entry shape wrong: %r' % ln[-40:])

PH = re.compile(r'\{\{.*?\}\}')
TAG = re.compile(r'<[^<>]+>')
NL = re.compile(r'\\n')

ph_bad, tag_bad, esc_bad, nl_bad, punct_bad = [], [], [], [], []

for k, v in out.items():
    kp = sorted(PH.findall(k))
    vp = sorted(PH.findall(v))
    if kp != vp:
        ph_bad.append((k, kp, vp))
    kt = sorted(TAG.findall(k))
    vt = sorted(TAG.findall(v))
    if kt != vt:
        tag_bad.append((k, kt, vt))
    if '"' in v or '\\' in v:
        esc_bad.append((k, v))
    if v.count('\n') != k.count('\n'):
        nl_bad.append((k, v))
    # period rules
    ks = k.rstrip()
    vs = v.rstrip()
    if ks and vs:
        if ks.endswith('...') or ks.endswith('\u2026'):
            if not vs.endswith('\u2026\u2026'):
                punct_bad.append((k, v, 'ellipsis'))
        elif ks.endswith('.'):
            if not vs.endswith('\u3002'):
                punct_bad.append((k, v, 'period'))
        elif ks.endswith('?'):
            if not vs.endswith('\uff1f'):
                punct_bad.append((k, v, 'question'))
        elif ks.endswith('!'):
            if not vs.endswith('\uff01'):
                punct_bad.append((k, v, 'bang'))
        else:
            if vs[-1] in '\u3002\uff1f\uff01':
                punct_bad.append((k, v, 'extra-period'))

print('placeholder problems:', len(ph_bad))
for x in ph_bad[:10]:
    print('  ', x)
print('tag problems:', len(tag_bad))
for x in tag_bad[:10]:
    print('  ', x)
print('quote/backslash problems:', len(esc_bad))
for x in esc_bad[:10]:
    print('  ', x)
print('newline-count problems:', len(nl_bad))
for x in nl_bad[:10]:
    print('  ', x)
print('punctuation problems:', len(punct_bad))
for x in punct_bad[:15]:
    print('  ', x)
print('structural problems:', len(problems))
for x in problems[:15]:
    print('  ', x)

identity = [k for k, v in out.items() if k == v]
print('identity mappings (%d): %s' % (len(identity), identity))
empty = [k for k, v in out.items() if not v.strip()]
print('empty values:', len(empty))

ok = not (ph_bad or tag_bad or esc_bad or nl_bad or punct_bad or problems or empty)
print('RESULT:', 'PASS' if ok else 'FAIL')
