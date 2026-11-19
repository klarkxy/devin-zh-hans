# -*- coding: utf-8 -*-
"""Final key-by-key diff report: source slice vs zh/n10.json."""
import io, json, re

SRC = r"H:\Archive\devin-zh-hans\tools\data\nls-todo-314.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\n10.json"
START, END = 4101, 4500
KEY_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*:')
PH = re.compile(r'\{\d+\}')

src = []
with io.open(SRC, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        m = KEY_RE.match(line)
        if m and START <= i <= END:
            src.append(json.loads('"' + m.group(1) + '"'))

out = json.load(io.open(OUT, "r", encoding="utf-8"))
out_keys = list(out)

print("source entries      : %d" % len(src))
print("output entries      : %d" % len(out_keys))
print("same order+keys     : %s" % (src == out_keys))

same, diffk, phbad, badchars, sameph = 0, 0, 0, 0, 0
for k, v in zip(src, out_keys):
    if k != v:
        diffk += 1
    if out[k] == v:
        same += 1
    if sorted(PH.findall(k)) != sorted(PH.findall(out[k])):
        phbad += 1
    if '"' in out[k] or "\\" in out[k]:
        badchars += 1
    if PH.findall(k):
        sameph += 1
print("key mismatches      : %d" % diffk)
print("untranslated values : %d" % same)
print("placeholder bad     : %d" % phbad)
print("bad chars in values : %d" % badchars)
print("entries w/ {n}      : %d" % sameph)
print("total chars zh      : %d" % sum(len(v) for v in out.values()))
