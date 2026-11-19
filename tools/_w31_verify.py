# -*- coding: utf-8 -*-
"""Validate w31.json against webapp-todo.json lines 5201-5600."""
import collections
import json
import re
import sys

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w31.json"
START, END = 5201, 5600

errors = []
warnings = []


def src_keys():
    raw = open(SRC, encoding="utf-8").read().splitlines()
    seg = raw[START - 1:END]
    assert len(seg) == 400, len(seg)
    keys = []
    for ln in seg:
        s = ln.strip()
        if s.endswith(","):
            s = s[:-1]
        obj = json.loads("{" + s + "}")
        (k, v), = obj.items()
        keys.append(k)
    return keys


raw_bytes = open(OUT, "rb").read()
if raw_bytes.startswith(b"\xef\xbb\xbf"):
    errors.append("output has BOM")
text = raw_bytes.decode("utf-8")

# structural checks on the raw text
if "\t" in text.replace("\t", "", 0) and "\\t" not in text:
    pass
if re.search(r"^\s*\S", text, re.M):
    bad = [l for l in text.splitlines() if l and not re.match(r"^(  |\{|\})", l)]
    if bad:
        errors.append("non-2-space indentation: %r" % bad[:3])
if text.rstrip().endswith(","):
    errors.append("trailing comma at EOF")

data = json.loads(text, object_pairs_hook=collections.OrderedDict)
keys_src = src_keys()
keys_out = list(data.keys())

if len(data) != len(keys_out):
    errors.append("duplicate keys in output")

if keys_out != keys_src:
    errors.append("KEY SET/ORDER MISMATCH")
    missing = [k for k in keys_src if k not in data]
    extra = [k for k in keys_out if k not in keys_src]
    if missing:
        errors.append("missing %d: %r" % (len(missing), missing[:5]))
    if extra:
        errors.append("extra %d: %r" % (len(extra), extra[:5]))
    for i, (a, b) in enumerate(zip(keys_src, keys_out)):
        if a != b:
            errors.append("first order diff at line %d: src=%r out=%r" % (START + i, a, b))
            break

PH = re.compile(r"\{\{.*?\}\}")
TAG = re.compile(r"</?[A-Za-z][^<>]*>")
ASCII_BAD = re.compile(r'["\\]')

for i, k in enumerate(keys_src):
    if k not in data:
        continue
    v = data[k]

    if not isinstance(v, str):
        errors.append("line %d: value not a string" % (START + i))
        continue

    # placeholders: exact multiset
    pk = collections.Counter(PH.findall(k))
    pv = collections.Counter(PH.findall(v))
    if pk != pv:
        errors.append("line %d: placeholder mismatch src=%r out=%r key=%r"
                      % (START + i, dict(pk), dict(pv), k))

    # tags
    tk = collections.Counter(TAG.findall(k))
    tv = collections.Counter(TAG.findall(v))
    if tk != tv:
        errors.append("line %d: tag mismatch src=%r out=%r key=%r"
                      % (START + i, dict(tk), dict(tv), k))

    # forbidden characters
    if ASCII_BAD.search(v):
        errors.append("line %d: value contains half-width quote/backslash: %r" % (START + i, v))

    if v.strip() == "":
        errors.append("line %d: empty translation" % (START + i))

    if v == k:
        warnings.append("line %d: unchanged from source: %r" % (START + i, k))

    if not re.search(r"[\u4e00-\u9fff]", v):
        warnings.append("line %d: no CJK in value (check skipped?): %r -> %r" % (START + i, k, v))

    # full-width punctuation: no ASCII comma/period/colon in CJK context
    # trailing punctuation rule
    if k.endswith("."):
        if not v.endswith("。"):
            errors.append("line %d: source ends with '.' but value ends %r" % (START + i, v[-2:]))
    else:
        if v.endswith("。"):
            errors.append("line %d: source has no '.' but value ends with '。' : %r" % (START + i, k))
    if k.endswith("...") or k.endswith("…"):
        if not v.endswith("……"):
            errors.append("line %d: ellipsis rule" % (START + i))

    # 您 must not appear
    if "您" in v:
        errors.append("line %d: uses 您" % (START + i))

print("source entries : %d" % len(keys_src))
print("output entries : %d" % len(keys_out))
print("errors         : %d" % len(errors))
for e in errors:
    print("  ERR", e)
print("warnings       : %d" % len(warnings))
for w in warnings:
    print("  WARN", w)

# duplicate-value report (informational)
dups = collections.Counter(data.values())
dup = {v: c for v, c in dups.items() if c > 1}
print("repeated values: %d distinct" % len(dup))
for v, c in sorted(dup.items(), key=lambda x: -x[1])[:10]:
    print("   %2d x %s" % (c, v))

sys.exit(0 if not errors else 1)
