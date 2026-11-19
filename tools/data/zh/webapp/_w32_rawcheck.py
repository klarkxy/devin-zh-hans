# -*- coding: utf-8 -*-
"""Raw-text cross-check (fixed): literal key token + raw value char scan.

Compares the literal source key token (as written on the line, escapes intact)
against the literal key token in w32.json, and scans the raw value substring.
Writes a UTF-8 report so console encoding cannot garble it.
"""
import io, re, json

SRC = r'H:/Archive/devin-zh-hans/tools/data/webapp-todo.json'
OUT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/w32.json'
REPORT = r'H:/Archive/devin-zh-hans/tools/data/zh/webapp/_w32_rawreport.txt'
pat = re.compile(r'^\s*("(?:[^"\\]|\\.)*")\s*:')

src_lines = io.open(SRC, encoding='utf-8').read().split('\n')[5600:6000]
out_text = io.open(OUT, encoding='utf-8').read()
out_lines = out_text.split('\n')
body = out_lines[1:-2]  # drops '{', '}', trailing ''

rep = []
src_tok = [pat.match(l).group(1) for l in src_lines]
out_tok, out_val = [], []
for l in body:
    m = pat.match(l)
    out_tok.append(m.group(1))
    out_val.append(l[m.end():].strip().rstrip(','))

rep.append('src lines            : %d' % len(src_lines))
rep.append('out body lines        : %d' % len(body))
rep.append('raw key tokens identical : %s' % (src_tok == out_tok))

# values are written as ` "..."` so each must start and end with one ASCII quote
bad_q = [v for v in out_val if not (v.startswith('"') and v.endswith('"'))]
rep.append('values not wrapped in exactly one quote pair : %d' % len(bad_q))

# inside the quotes: no backslash, no ASCII double quote
inner = [v[1:-1] for v in out_val if v.startswith('"') and v.endswith('"')]
bad_inner = [x for x in inner if '\\' in x or '"' in x]
rep.append('values containing backslash or ASCII quote : %d' % len(bad_inner))
for x in bad_inner:
    rep.append('   BAD: %r' % x)

ph = re.compile(r'\{\{[^{}]*\}\}')
mism = []
for sl, ot, ov in zip(src_lines, out_tok, out_val):
    if sorted(ph.findall(pat.match(sl).group(1))) != sorted(ph.findall(ov)):
        mism.append((pat.match(sl).group(1), ov))
rep.append('raw placeholder multiset mismatches : %d' % len(mism))
for s, o in mism:
    rep.append('   %s  vs  %s' % (s, o))

rep.append('file ends with newline : %s' % out_text.endswith('\n'))
rep.append('trailing comma before } : %s' % (',\n}' in out_text))
d = json.loads(out_text)
rep.append('json entries          : %d' % len(d))
io.open(REPORT, 'w', encoding='utf-8', newline='\n').write('\n'.join(rep) + '\n')
print('report written')
