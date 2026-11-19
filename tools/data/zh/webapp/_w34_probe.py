# -*- coding: utf-8 -*-
"""Independent cross-check of w34.json (raw key literals, char level) against source lines 6401-6800."""
import json
import re

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w34.json"

src = open(SRC, encoding="utf-8").read().splitlines()
out = open(OUT, encoding="utf-8").read().splitlines()

# raw key literal of source lines 6401..6800 (1-based -> slice 6400..6799);
# regex, not split(), because keys themselves contain ':' (e.g. "Project rule: {{rule}} ...")
src_raw = [re.match(r'^("(?:[^"\\]|\\.)*")\s*:', s).group(1) for s in src[6400:6800]]
body = [l for l in out if l.startswith('  "')]
out_raw = [re.match(r'^\s*("(?:[^"\\]|\\.)*")\s*:', l).group(1) for l in body]

print("source lines scanned           :", len(src_raw), "(6401-6800)")
print("output entries                 :", len(out_raw))
print("raw key literals identical     :", src_raw == out_raw)
for i, (a, b) in enumerate(zip(src_raw, out_raw)):
    if a != b:
        print("    MISMATCH at source line %d:\n      src=%r\n      out=%r" % (6401 + i, a, b))

pairs = [json.loads("{" + l.strip().rstrip(",") + "}") for l in body]
vals = [list(p.items())[0] for p in pairs]
print("ascii double quote in value    :", any('"' in v for _, v in vals))
print("backslash in value             :", any("\\" in v for _, v in vals))
print("empty value                    :", sum(1 for _, v in vals if not v.strip()))
print("values with CJK                :", sum(1 for _, v in vals if re.search(r"[\u4e00-\u9fff]", v)))
print("kept-as-is (no CJK) entries    :")
for k, v in vals:
    if not re.search(r"[\u4e00-\u9fff]", v):
        print("    %r -> %r" % (k, v))
print("\nsamples:")
for ln in (0, 10, 53, 78, 128, 190, 245, 300, 355, 399):
    k, v = vals[ln]
    print("  %4d  %r -> %r" % (6401 + ln, k, v))
