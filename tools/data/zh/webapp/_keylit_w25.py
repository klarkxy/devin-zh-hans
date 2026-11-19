# -*- coding: utf-8 -*-
"""Byte-level check: raw key literal in output must equal raw key literal in source."""
import re

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w25.json"
START, END = 2801, 3200

KEY = re.compile(r'^\s*("(?:[^"\\]|\\.)*")\s*:')


def lit(line):
    m = KEY.match(line)
    return m.group(1) if m else None


src = open(SRC, encoding="utf-8").read().splitlines()
out = open(OUT, encoding="utf-8").read().splitlines()

bad = []
for i, ln in enumerate(range(START, END + 1)):
    a = lit(src[ln - 1])
    b = lit(out[i + 1])
    if a is None or b is None or a != b:
        bad.append((ln, a, b))

print("byte-level key literal mismatches:", len(bad))
for x in bad[:5]:
    print(x)
print("output lines:", len(out), "| first:", out[0].strip(), "| last:", out[-1].strip())
