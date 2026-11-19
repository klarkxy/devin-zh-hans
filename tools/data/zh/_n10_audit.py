# -*- coding: utf-8 -*-
"""Audit: sentence-final punctuation of each translation vs its source key."""
import io, json, re

SRC = r"H:\Archive\devin-zh-hans\tools\data\nls-todo-314.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\n10.json"
KEY_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*:')

rows = []
with io.open(SRC, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        m = KEY_RE.match(line)
        if m:
            rows.append((i, json.loads('"' + m.group(1) + '"')))
src = [k for ln, k in rows if 4101 <= ln <= 4500]
d = json.load(io.open(OUT, "r", encoding="utf-8"))

SUF = ["......", "……", "...", "…", "。", "！", "？", "!", "?", "：", ":", "）", ")", "，", ",", ".", "”"]
MAP = {".": "。", "...": "……", "?": "？", "!": "！", ":": "：", ",": "，", ")": "）", "…": "……"}


def tail(s):
    s = s.rstrip()
    for t in SUF:
        if s.endswith(t):
            return t
    return ""


bad = []
for k in src:
    v = d[k]
    a, b = tail(k), tail(v)
    aa = MAP.get(a, a)
    bb = MAP.get(b, b)
    if aa != bb:
        bad.append((k[-45:], v[-45:], a, b))

print("tail mismatches: %d" % len(bad))
for x in bad:
    print("  key=...%r  val=...%r  [%r vs %r]" % x)

# spacing audit: CJK immediately adjacent to latin letters/digits without space
SP = re.compile(r'[\u4e00-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u4e00-\u9fff]')
susp = []
for k in src:
    v = d[k]
    vv = re.sub(r'`[^`]*`', "", v)
    vv = re.sub(r'\{\d+\}', "", vv)
    vv = re.sub(r'<[^>]*>', "", vv)
    for m in SP.finditer(vv):
        susp.append((v[max(0, m.start() - 12):m.end() + 12],))
print("no-space CJK/latin adjacencies: %d" % len(susp))
for s in susp[:40]:
    print("   ", s[0])
