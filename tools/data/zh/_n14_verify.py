# -*- coding: utf-8 -*-
"""Verify tools/data/zh/n14.json against nls-todo-314.json lines 5701-6002."""
import io
import json
import re
import sys

SRC = r"H:\Archive\devin-zh-hans\tools\data\nls-todo-314.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\n14.json"
FIRST_LINE, LAST_LINE = 5701, 6002  # inclusive, 1-based

LINE_RE = re.compile(r'^\s*("(?:[^"\\]|\\.)*")\s*:\s*""\s*,?\s*$')
PH = re.compile(r"\{\d+\}")

problems = []
notes = []

# --- source side -----------------------------------------------------------
with io.open(SRC, encoding="utf-8-sig") as f:
    src_lines = f.read().splitlines()

src_raw = []
src_keys = []
for i in range(FIRST_LINE - 1, LAST_LINE):
    m = LINE_RE.match(src_lines[i])
    if not m:
        problems.append("source line %d unparsable: %r" % (i + 1, src_lines[i]))
        continue
    src_raw.append(m.group(1))
    src_keys.append(json.loads(m.group(1)))

# --- output side -----------------------------------------------------------
raw = io.open(OUT, "rb").read()
if raw[:3] == b"\xef\xbb\xbf":
    problems.append("output has UTF-8 BOM")
text = raw.decode("utf-8")
try:
    pairs = json.loads(text, object_pairs_hook=lambda p: p)
except Exception as exc:  # noqa: BLE001
    problems.append("output is not valid JSON: %s" % exc)
    pairs = []

out_keys = [k for k, _ in pairs]
out_vals = [v for _, v in pairs]

if len(set(out_keys)) != len(out_keys):
    dupes = sorted({k for k in out_keys if out_keys.count(k) > 1})
    problems.append("duplicate keys: %r" % dupes)

# --- 1. key set / order ----------------------------------------------------
kept_src = [(r, k) for r, k in zip(src_raw, src_keys) if k in set(out_keys)]
skipped = [k for k in src_keys if k not in set(out_keys)]

extra = [k for k in out_keys if k not in set(src_keys)]
if extra:
    problems.append("output has keys not in source range: %r" % extra[:10])

if [k for _, k in kept_src] != out_keys:
    problems.append("key order mismatch (source-order-restricted vs output)")
    for idx, (a, b) in enumerate(zip([k for _, k in kept_src], out_keys)):
        if a != b:
            problems.append("  first divergence at output index %d: src=%r out=%r" % (idx, a, b))
            break

# byte-exact raw key tokens (no re-escaping drift)
out_raw = re.findall(r'^\s*("(?:[^"\\]|\\.)*")\s*:', text, re.M)
if out_raw != [r for r, _ in kept_src]:
    problems.append("raw key tokens differ from source text")

# --- 2. placeholders + value hygiene --------------------------------------
for key, val in zip(out_keys, out_vals):
    if not isinstance(val, str):
        problems.append("non-string value for %r" % key)
        continue
    if val.strip() == "":
        problems.append("empty translation for %r" % key)
    if '"' in val:
        problems.append('half-width double quote in value of %r: %r' % (key, val))
    if "\\" in val:
        problems.append("literal backslash in value of %r: %r" % (key, val))
    if sorted(PH.findall(key)) != sorted(PH.findall(val)):
        problems.append(
            "placeholder mismatch for %r: key=%r value=%r"
            % (key, PH.findall(key), PH.findall(val))
        )
    elif PH.findall(key) != PH.findall(val):
        notes.append("placeholder order changed (deliberate, count equal): %r" % key)
    if ("\n" in key) != ("\n" in val):
        problems.append("newline mismatch for %r" % key)
    # sentence-ending punctuation must follow the source
    k, v = key.rstrip(), val.rstrip()
    if k.endswith("..."):
        if not v.endswith("……"):
            problems.append("ellipsis mismatch for %r: value=%r" % (key, val))
    elif k.endswith(".") != v.endswith("。"):
        problems.append("period mismatch for %r: value=%r" % (key, val))
    elif not k.endswith(".") and k[-1:] in "!?" and v.endswith("。"):
        problems.append("unexpected period at end of %r: value=%r" % (key, val))

# --- 3. formatting ---------------------------------------------------------
if "\r" in text:
    problems.append("output contains CR (expected LF only)")
if text.endswith("\n}\n") is False:
    problems.append("output does not end with closing brace + newline")
if re.search(r'^("|[^ ].*":)', text, re.M):
    problems.append("found a line without 2-space indent")
if ",\n}" in text or ",\n  }" in text:
    problems.append("trailing comma before closing brace")

# --- 4. coverage / skip sanity --------------------------------------------
SYMBOLS = " \t-/,:|()·•—[]{}<>\"'.%@" + "\u2192\u2191\u2193\u00d7\u2022"
for k in skipped:
    if re.search(r"[A-Za-z\u4e00-\u9fff]", k):
        notes.append("skipped key contains letters (review): %r" % k)
    if PH.sub("", k).strip(SYMBOLS):
        notes.append("skipped key has non-placeholder content: %r" % k)

print("source entries : %d" % len(src_keys))
print("written entries: %d" % len(out_keys))
print("skipped        : %d" % len(skipped))
print("first key      : %s" % out_keys[0])
print("last key       : %s" % out_keys[-1])
print("")
if notes:
    print("NOTES (%d):" % len(notes))
    for n in notes:
        print("  " + n)
    print("")
if problems:
    print("PROBLEMS (%d):" % len(problems))
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("ALL CHECKS PASSED")
