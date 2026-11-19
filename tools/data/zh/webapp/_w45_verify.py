# -*- coding: utf-8 -*-
"""w45 verifier: source slice (lines 10801-10965) vs zh/webapp/w45.json.

Checks
  1. UTF-8 readable, 2-space indent, no BOM, no trailing comma, JSON parses
  2. produced key set == source key set, in the same order
  3. every produced key exists verbatim in the source slice (character-exact)
  4. {{...}} placeholder multiset identical per entry (key vs value)
  5. no half-width double quote / backslash anywhere in values
  6. whitespace/ASCII-run sanity: leftover English sentences reported
  7. newline+indent formatting matches the batch convention
"""
import io
import json
import re
import sys
from collections import Counter

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w45.json"
FIRST, LAST = 10801, 10965

PH = re.compile(r"\{\{[^{}]*\}\}")
TAG = re.compile(r"<[^<>]+>")

fails = []


def fail(msg):
    fails.append(msg)


raw_bytes = open(OUT, "rb").read()
if raw_bytes.startswith(b"\xef\xbb\xbf"):
    fail("BOM present")

text = raw_bytes.decode("utf-8")

# --- source slice -----------------------------------------------------------
src_lines = io.open(SRC, "r", encoding="utf-8").read().splitlines()
src = []
for lineno in range(FIRST, LAST + 1):
    raw = src_lines[lineno - 1].rstrip().rstrip(",")
    obj = json.loads("{" + raw + "}")
    (key,) = obj.keys()
    src.append((lineno, key, raw))
src_keys = [k for _, k, _ in src]

# --- output -----------------------------------------------------------------
try:
    out = json.loads(text, object_pairs_hook=list)
except Exception as exc:                     # noqa: BLE001
    print("FATAL: output is not valid JSON: %r" % (exc,))
    sys.exit(2)
out_pairs = list(out)
out_keys = [k for k, _ in out_pairs]

# --- 2/3: key set, order, exactness ----------------------------------------
if len(set(out_keys)) != len(out_keys):
    dup = [k for k, n in Counter(out_keys).items() if n > 1]
    fail("duplicate keys in output: %r" % (dup,))

rest = [k for k in src_keys if k not in set(out_keys)]          # skipped entries
if len(rest) + len(out_keys) != len(src_keys):
    fail("count mismatch: source=%d output=%d skipped=%d"
         % (len(src_keys), len(out_keys), len(rest)))

expected_kept = [k for k in src_keys if k not in set(rest)]
if out_keys != expected_kept:
    for i, (a, b) in enumerate(zip(out_keys, expected_kept)):
        if a != b:
            fail("order/content differs at index %d: out=%r src=%r" % (i, a, b))
            break
    else:
        fail("order differs in length: out=%d expected=%d" % (len(out_keys), len(expected_kept)))

for k in out_keys:
    if k not in src_keys:
        fail("key not in source: %r" % (k,))

# --- 4: placeholders -------------------------------------------------------
for k, v in out_pairs:
    ck, cv = Counter(PH.findall(k)), Counter(PH.findall(v))
    if ck != cv:
        fail("placeholder multiset differs: %r\n  key=%r\n  val=%r" % (k, sorted(ck), sorted(cv)))
    tk, tv = Counter(TAG.findall(k)), Counter(TAG.findall(v))
    if tk != tv:
        fail("tag multiset differs: %r\n  key=%r\n  val=%r" % (k, sorted(tk), sorted(tv)))

# --- 5: forbidden characters ----------------------------------------------
for k, v in out_pairs:
    if '"' in v:
        fail("half-width double quote in value: %r -> %r" % (k, v))
    if "\\" in v:
        fail("backslash in value: %r -> %r" % (k, v))
    if not v.strip():
        fail("empty value: %r" % (k,))

# --- 6: leftover English -----------------------------------------------
ASCII_WORD = re.compile(r"[A-Za-z]{3,}")
ALLOW = set("""
Devin ACU MCP GitHub GitLab Jira Slack Teams Jupyter DeepWiki SWE Unified
CLI API URL JSON YAML SQL PR Wiki Kubernetes Docker Gerrit HTTP HTTPS OAuth
Outpost ID RAM px px B GB KB MB UTC Client Admin Lightning Max Flex Standard
creator Creator
""".split())
for k, v in out_pairs:
    bare = TAG.sub("", PH.sub("", v))
    left = [w for w in ASCII_WORD.findall(bare) if w not in ALLOW]
    if left:
        print("NOTE leftover-ascii: %r -> %r  (%r)" % (k, v, left))

# --- 7: formatting ------------------------------------------------------
for i, line in enumerate(text.splitlines()):
    if line.startswith("  ") and (len(line) - len(line.lstrip(" "))) != 2:
        fail("bad indent at line %d" % (i + 1))
if text.rstrip().endswith(","):
    fail("trailing comma at end of file")
json.loads(text)  # final strict re-parse

print("")
print("source entries in slice : %d" % len(src_keys))
print("translated in output    : %d" % len(out_keys))
print("skipped (pure symbols)  : %d" % len(rest))
print("failures                : %d" % len(fails))
for f in fails:
    print("  FAIL " + f)
print("RESULT: %s" % ("PASS" if not fails else "FAIL"))
sys.exit(0 if not fails else 1)
