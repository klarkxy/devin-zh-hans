# -*- coding: utf-8 -*-
# Validates tools/data/zh/n13.json against source lines 5301..5700.
import io
import json
import re
import sys
from collections import Counter

SRC = r"H:\Archive\devin-zh-hans\tools\data\nls-todo-314.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\n13.json"
START, END = 5301, 5700
SKIP = ["{0}\n\n{1}"]  # pure-placeholder entry (real newlines), intentionally skipped

PH = re.compile(r"\{(\d+)\}")

def src_entries():
    raw = io.open(SRC, encoding="utf-8").read().splitlines()
    out = []
    for n in range(START, END + 1):
        s = raw[n - 1].strip()
        if s.endswith(","):
            s = s[:-1]
        obj = json.loads("{" + s + "}")
        (k,) = obj.keys()
        out.append((n, k))
    return out

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg)

# --- raw file checks -------------------------------------------------------
blob = io.open(OUT, "rb").read()
check(not blob.startswith(b"\xef\xbb\xbf"), "BOM present")
text = blob.decode("utf-8")
check(text.endswith("\n"), "missing trailing newline")
check(text.count("{") == text.count("}"), "brace imbalance in raw file")
check(",}" not in text and ",]" not in text, "trailing comma")
check('{ "英' not in text, "unexpected inline formatting")

data = json.loads(text)
check(isinstance(data, dict), "root is not an object")

# --- key set / order -------------------------------------------------------
src = src_entries()
expected = [(n, k) for (n, k) in src if k not in SKIP]
check(len(expected) == 399, "expected 399 translatable entries, source gave %d" % len(expected))

out_items = list(data.items())
check(len(out_items) == len(expected), "count mismatch: out=%d expected=%d" % (len(out_items), len(expected)))
for i, ((n, k), (ok, ov)) in enumerate(zip(expected, out_items)):
    check(k == ok, "order/key mismatch at index %d (source line %d): expected %r got %r" % (i, n, k, ok))

# --- per-entry checks ------------------------------------------------------
whitelist_quotes = set()
for i, ((n, k), (ok, v)) in enumerate(zip(expected, out_items)):
    tag = "line %d" % n
    check(isinstance(v, str) and v.strip() != "", "%s: empty value" % tag)

    # placeholders: same multiset of {n}
    sk, sv = Counter(PH.findall(k)), Counter(PH.findall(v))
    check(sk == sv, "%s: placeholder mismatch key=%s value=%s" % (tag, dict(sk), dict(sv)))
    # braces must only appear as placeholders / known markup
    for s, where in ((k, "key"), (v, "value")):
        residue = PH.sub("", s)
        residue = residue.replace("{{", "").replace("}}", "")
        check("{" not in residue and "}" not in residue,
              "%s: stray brace in %s" % (tag, where))

    # newline parity for multi-line entries
    check(k.count("\n") == v.count("\n"),
          "%s: newline count key=%d value=%d" % (tag, k.count("\n"), v.count("\n")))

    # forbidden characters inside values
    if "\\" in v:
        fails.append("%s: backslash in value" % tag)
    if '"' in v:
        # only allowed inside a VS Code command-link title, as the literal " "
        if v.count('"') == 2 and '](command:' in v and '" "' in v:
            whitelist_quotes.add(n)
        else:
            fails.append("%s: half-width double quote in value" % tag)

    # links / markup preserved
    check(k.count("[[") == v.count("[[") and k.count("]]") == v.count("]]"),
          "%s: [[...]] marker count changed" % tag)
    check(k.count("`") == v.count("`"), "%s: backtick count changed" % tag)
    check(len(re.findall(r"\]\(", k)) == len(re.findall(r"\]\(", v)),
          "%s: markdown link count changed" % tag)

# --- summary ---------------------------------------------------------------
print("entries checked:", len(out_items))
print("placeholder check: OK (all {0}/{1}/... multisets identical)")
print("key set + order: OK (source lines %d-%d, %d entries)" % (START, END, len(expected)))
print("skipped pure-symbol entry:", SKIP)
print("quote whitelist (command-link titles, required by VS Code syntax):",
      sorted(whitelist_quotes))
if fails:
    print("FAILURES (%d):" % len(fails))
    for f in fails[:40]:
        print("  -", f)
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
