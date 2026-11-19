# -*- coding: utf-8 -*-
"""Validate webapp batch w26 against source lines 3201-3600 of webapp-todo.json."""
import json, re, sys, collections, io

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w26.json"
START, END = 3201, 3600  # 1-based inclusive

# ---- load source lines ----
with io.open(SRC, "r", encoding="utf-8") as f:
    src_lines = f.read().splitlines()

region = src_lines[START - 1:END]
src_pairs = []          # (lineno, key, rest)
bad = []
for i, line in enumerate(region):
    lineno = START + i
    m = re.match(r'^(\s*"(?:[^"\\]|\\.)*"):\s*(.*)$', line)
    if not m:
        bad.append((lineno, line))
        continue
    # decode the key exactly as JSON would
    raw_key_literal = m.group(1)
    key = json.loads(raw_key_literal)
    src_pairs.append((lineno, key, m.group(2).strip()))

print("source lines in region :", len(region))
print("source keys parsed     :", len(src_pairs))
if bad:
    print("UNPARSED SOURCE LINES  :", bad[:5])

src_keys = [k for _, k, _ in src_pairs]
dups = [k for k, c in collections.Counter(src_keys).items() if c > 1]
print("duplicate source keys  :", dups)

# ---- load output ----
raw = open(OUT, "rb").read()
print("output has BOM         :", raw.startswith(b"\xef\xbb\xbf"))
text = raw.decode("utf-8")
data = json.loads(text, object_pairs_hook=collections.OrderedDict)
out_keys = list(data.keys())
print("output entries         :", len(out_keys))

fail = []

# 1) JSON formatting: 2-space indent, no trailing comma, no trailing whitespace
canon = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
if text != canon:
    fail.append("format: file is not exactly indent=2 JSON serialization")

# 2) key set + order
if out_keys == src_keys:
    print("key set + order        : OK (exact match, %d keys)" % len(out_keys))
else:
    fail.append("key set/order mismatch")
    missing = [k for k in src_keys if k not in data]
    extra = [k for k in out_keys if k not in src_keys]
    print("  missing:", missing[:10])
    print("  extra  :", extra[:10])
    if [k for k in out_keys if k in src_keys] != [k for k in src_keys if k in out_keys]:
        firstdiff = next((i for i, (a, b) in enumerate(zip(src_keys, out_keys)) if a != b), None)
        print("  first order diff at index:", firstdiff)

# 3) placeholder multiset per entry
PH = re.compile(r"\{\{[^{}]*\}\}")
ph_bad = []
for lineno, key, rest in src_pairs:
    if key not in data:
        continue
    want = sorted(PH.findall(key))
    got = sorted(PH.findall(data[key]))
    if want != got:
        ph_bad.append((lineno, key, data[key], want, got))
if ph_bad:
    fail.append("placeholder mismatch: %d entries" % len(ph_bad))
    for row in ph_bad[:10]:
        print("  PH", row)
else:
    print("placeholder multiset   : OK (all %d entries)" % len(src_pairs))

# 4) no half-width double quote / backslash in values
qb = [(lineno, k, v) for lineno, k, _ in src_pairs if k in data
      for v in [data[k]] if ('"' in v or "\\" in v)]
if qb:
    fail.append("forbidden chars in values: %d" % len(qb))
    for row in qb[:10]:
        print("  BAD", row)
else:
    print("halfquote/backslash    : OK (none in values)")

# 5) tag / [[...]] markers preserved verbatim
MARK = re.compile(r"</?[a-zA-Z][^<>]*>|\[\[[^\]]*\]\]")
mk_bad = []
for lineno, key, rest in src_pairs:
    if key not in data:
        continue
    if MARK.findall(key) != MARK.findall(data[key]):
        mk_bad.append((lineno, key, data[key], MARK.findall(key), MARK.findall(data[key])))
if mk_bad:
    fail.append("markup/link mismatch: %d" % len(mk_bad))
    for row in mk_bad[:10]:
        print("  MK", row)
else:
    print("tags/[[...]] markers   : OK")

# 6) trailing period parity (. / 。 , ... / ……)
def ends(period, s):
    return s.rstrip().endswith(period)
per_bad = []
for lineno, key, rest in src_pairs:
    if key not in data:
        continue
    v = data[key].rstrip()
    if key.rstrip().endswith("...") or key.rstrip().endswith("…"):
        if not (v.endswith("……")):
            per_bad.append((lineno, key, data[key], "ellipsis"))
    elif key.rstrip().endswith("."):
        if not v.endswith("。"):
            per_bad.append((lineno, key, data[key], "period"))
    else:
        if v.endswith("。"):
            per_bad.append((lineno, key, data[key], "extra period"))
if per_bad:
    fail.append("period parity: %d" % len(per_bad))
    for row in per_bad[:12]:
        print("  PER", row)
else:
    print("period parity          : OK")

# 7) untranslated (value identical to key) list, for review
same = [k for k in src_keys if k in data and data[k] == k]
print("value == key (verbatim): %d -> %s" % (len(same), same))

print()
if fail:
    print("FAILED:")
    for f_ in fail:
        print(" -", f_)
    sys.exit(1)
print("ALL CHECKS PASSED")
