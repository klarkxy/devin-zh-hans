# -*- coding: utf-8 -*-
"""Verify w34.json against webapp-todo.json lines 6401-6800."""
import json
import re
from collections import Counter

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w34.json"
START, END = 6401, 6800

KEY_RE = re.compile(r'^\s*("(?:[^"\\]|\\.)*")\s*:')
PH_RE = re.compile(r"\{\{.*?\}\}")
TAG_RE = re.compile(r"</?[A-Za-z][^<>]*>")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{3,}")

WHITELIST_WORDS = {
    "Devin", "Review", "Autoapprover", "Pylon", "Slack", "Linear", "GitLab", "GitHub",
    "Bitbucket", "Perforce", "Unleash", "Notion", "Figma", "Jira", "MCP", "OAuth",
    "Azure", "DevOps", "Enterprise", "Center", "Data", "ChatGPT", "Reddit", "Pixel",
    "React", "RRULE", "RTT", "RDS_PSQL_DB_URL", "RE2", "PUT", "API", "URL", "DNS",
    "SSO", "GDPR", "CCPA", "HIPAA", "PAT", "SQL", "HTTP", "YYYY", "UTC",
}

fails = []
notes = []


def ph_counter(s):
    return Counter(PH_RE.findall(s))


# --- source side -------------------------------------------------------------
with open(SRC, encoding="utf-8") as f:
    raw = f.read().splitlines()

src_pairs = []
for ln in range(START, END + 1):
    m = KEY_RE.match(raw[ln - 1])
    if not m:
        fails.append("unparsable source line %d" % ln)
        continue
    src_pairs.append((ln, json.loads(m.group(1))))

src_keys = [k for _, k in src_pairs]

# --- output side -------------------------------------------------------------
with open(OUT, encoding="utf-8") as f:
    text = f.read()

if text.startswith("\ufeff"):
    fails.append("output has BOM")

out = json.loads(text)
out_keys = list(out.keys())

# 1. count / key set / key order
if len(src_keys) != len(out_keys):
    fails.append("count mismatch: source=%d output=%d" % (len(src_keys), len(out_keys)))
if set(src_keys) != set(out_keys):
    only_src = [k for k in src_keys if k not in out]
    only_out = [k for k in out_keys if k not in set(src_keys)]
    fails.append("key set mismatch: missing=%r extra=%r" % (only_src[:5], only_out[:5]))
if src_keys != out_keys:
    for i, (a, b) in enumerate(zip(src_keys, out_keys)):
        if a != b:
            fails.append("order mismatch at index %d (source line %d): %r != %r"
                         % (i, src_pairs[i][0], a, b))
            break

# 2. placeholders / tags
for ln, k in src_pairs:
    if k not in out:
        continue
    v = out[k]
    if ph_counter(k) != ph_counter(v):
        fails.append("placeholder mismatch [line %d] %r: %r -> %r"
                     % (ln, k, sorted(ph_counter(k).elements()), sorted(ph_counter(v).elements())))
    if Counter(TAG_RE.findall(k)) != Counter(TAG_RE.findall(v)):
        fails.append("tag mismatch [line %d] %r: %r -> %r"
                     % (ln, k, TAG_RE.findall(k), TAG_RE.findall(v)))
    # literal $ immediately before a placeholder must survive
    for m in re.finditer(r"\$(?=\{\{)", k):
        if k.count("${{") > v.count("${{"):
            fails.append("dropped literal $ before placeholder [line %d] %r -> %r" % (ln, k, v))
            break

# 3. forbidden characters in values
for ln, k in src_pairs:
    v = out.get(k, "")
    if '"' in v:
        fails.append('half-width double quote in value [line %d] %r' % (ln, k))
    if "\\" in v:
        fails.append("backslash in value [line %d] %r" % (ln, k))

# 4. emptiness / untranslated leftovers
for ln, k in src_pairs:
    v = out.get(k, "")
    if not v.strip():
        fails.append("empty value [line %d] %r" % (ln, k))
    if v == k:
        notes.append("value identical to key [line %d]: %r" % (ln, k))
    if k.endswith("?"):
        if not v.endswith("？"):
            fails.append("question-mark parity [line %d]: %r -> %r" % (ln, k, v))
    elif v.endswith("？"):
        fails.append("question-mark added [line %d]: %r -> %r" % (ln, k, v))

# 5. trailing punctuation parity (., :, …, ...)
# Documented exceptions, each reviewed by hand: none in this range.
EXC_ELLIPSIS = set()
EXC_PERIOD = set()

for ln, k in src_pairs:
    v = out.get(k, "")
    ks, vs = k.rstrip(), v.rstrip()
    if ks.endswith("…") or ks.endswith("..."):
        if ln in EXC_ELLIPSIS:
            continue
        if not vs.endswith("……"):
            fails.append("ellipsis parity [line %d]: %r" % (ln, v))
        continue
    if ks.endswith(".") and ln not in EXC_PERIOD:
        if not vs.endswith("。"):
            fails.append("period parity [line %d]: source ends '.' -> %r" % (ln, v))
    if (not ks.endswith(".")) and vs.endswith("。"):
        fails.append("period parity [line %d]: source no '.' -> %r" % (ln, v))
    if ks.endswith(":") and not vs.endswith("："):
        fails.append("colon parity [line %d]: %r" % (ln, v))

# 6. leftover latin words (report only)
for ln, k in src_pairs:
    v = out.get(k, "")
    if v == k:
        continue
    left = {w for w in WORD_RE.findall(v) if w not in WHITELIST_WORDS}
    if left:
        notes.append("latin leftover [line %d]: %r -> %r | %r" % (ln, k, v, sorted(left)))

# 7. indentation / formatting
for i, line in enumerate(text.splitlines(), 1):
    if line.strip().startswith('"') and not (line.startswith('  "') or line.startswith('{')):
        fails.append("indentation not 2 spaces at output line %d" % i)
        break

print("source entries (lines %d-%d): %d" % (START, END, len(src_pairs)))
print("output entries:                %d" % len(out))
print("distinct keys output:          %d" % len(set(out_keys)))
print("placeholder occurrences:       %d" % sum(sum(ph_counter(k).values()) for _, k in src_pairs))
print("formatting: indent=2, utf-8 no BOM, trailing newline=%s" % text.endswith("\n"))
print("-" * 60)
for n in notes:
    print("NOTE:", n)
if fails:
    print("FAILED: %d problem(s)" % len(fails))
    for f in fails:
        print("  -", f)
    raise SystemExit(1)
print("ALL CHECKS PASSED")
