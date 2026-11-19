# -*- coding: utf-8 -*-
"""Quality sweep on w24.json."""
import io
import json
import re

out = json.loads(io.open('zh/webapp/w24.json', encoding='utf-8').read())

cjk = re.compile(r'[\u4e00-\u9fff]')
half_after_cjk = re.compile(r'[\u4e00-\u9fff][,;:!?()]|[,;:!?()][\u4e00-\u9fff]')

print('--- half-width punctuation touching CJK ---')
for k, v in out.items():
    for m in half_after_cjk.finditer(v):
        print(' ', repr(m.group(0)), '|', v)
        break

print('--- 您 ---')
print([k for k, v in out.items() if '\u60a8' in v])

print('--- values that are still pure English (>=3 latin words) ---')
for k, v in out.items():
    if k == v and len(re.findall(r'[A-Za-z]{2,}', v)) >= 3:
        print(' ', k)

print('--- length ratio outliers (zh chars / en chars) ---')
rows = []
for k, v in out.items():
    kl = len(k)
    vl = len(v)
    if kl > 40 and vl > 0:
        rows.append((vl / kl, k, v))
rows.sort()
for r, k, v in rows[:4] + rows[-4:]:
    print('  %.2f | %s | %s' % (r, k[:70], v[:60]))

print('--- double spaces / trailing spaces ---')
for k, v in out.items():
    if '  ' in v or v != v.strip():
        print(' ', repr(v))

print('--- latin-CJK spacing sample check (missing space before CJK after latin letter) ---')
bad = []
for k, v in out.items():
    for m in re.finditer(r'[A-Za-z0-9][\u4e00-\u9fff]|[\u4e00-\u9fff][A-Za-z0-9]', v):
        bad.append((k, v))
        break
print('count:', len(bad))
for k, v in bad[:25]:
    print('  ', v)
