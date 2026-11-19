# -*- coding: utf-8 -*-
"""w33 批次校验：源区间 6001-6400 与 zh/webapp/w33.json 逐键比对。

用法： python tools/data/_w33_verify.py
校验项：
  1. 键集合与顺序与源区间完全一致
  2. {{...}} 占位符多重集一致（键 vs 值）
  3. <tag> 标签多重集一致
  4. 值内无半角双引号、无反斜杠、无空值
  5. 首尾标点（句号/问号/省略号/冒号）跟随原文
  6. UTF-8 无 BOM、2 空格缩进、可被 json 解析
"""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "webapp-todo.json")
OUT = os.path.join(ROOT, "data", "zh", "webapp", "w33.json")
START, END = 6001, 6400  # 1 基行号，含两端

PH = re.compile(r"\{\{[^{}]*\}\}")
TAG = re.compile(r"</?([a-zA-Z][\w-]*)>")
ASCII_ONLY_OK = {
    "P3", "PAT", "PR", "PagerDuty", "Perforce",
    "PR #{{number}}", "PR {{number}}",
    "PR #{{number}} {{owner}}/{{repo}} {{title}}",
}


def main():
    raw = open(OUT, "rb").read()
    problems = []
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("BOM present")
    text = raw.decode("utf-8")
    data = json.loads(text)

    lines = open(SRC, encoding="utf-8").read().splitlines()
    src_keys = []
    for i in range(START - 1, END):
        obj = json.loads("{" + lines[i].rstrip().rstrip(",") + "}")
        src_keys.append(list(obj.keys())[0])
    out_keys = list(data.keys())

    if src_keys != out_keys:
        problems.append("key set/order mismatch: src=%d out=%d" % (len(src_keys), len(out_keys)))
        for i, (a, b) in enumerate(zip(src_keys, out_keys)):
            if a != b:
                problems.append("  idx %d\n    src: %r\n    out: %r" % (i, a, b))

    for k, v in data.items():
        if '"' in v or "\\" in v:
            problems.append("quote/backslash in value: %r" % k)
        if not v.strip():
            problems.append("empty value: %r" % k)
        if collections.Counter(PH.findall(k)) != collections.Counter(PH.findall(v)):
            problems.append("placeholder mismatch: %r -> %r" % (k, v))
        if collections.Counter(TAG.findall(k)) != collections.Counter(TAG.findall(v)):
            problems.append("tag mismatch: %r -> %r" % (k, v))
        src_p = k.rstrip().endswith((".", "?", "!", "…", ":"))
        out_p = v.rstrip().endswith(("。", "？", "！", "……", "："))
        if src_p != out_p:
            problems.append("punct parity: %r -> %r" % (k, v))
        if k != v and all(ord(c) < 128 for c in v) and k not in ASCII_ONLY_OK:
            problems.append("ascii-only value not in allowlist: %r" % k)

    if any(l.startswith("    ") for l in text.split("\n")):
        problems.append("4-space indent found")

    print("entries: %d (src %d)" % (len(out_keys), len(src_keys)))
    if problems:
        print("FAIL (%d)" % len(problems))
        for p in problems:
            print(" -", p)
        return 1
    print("OK: keys+order, placeholders, tags, quotes, punctuation, indent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
