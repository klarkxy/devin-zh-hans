# -*- coding: utf-8 -*-
"""Verify zh/n10.json against nls-todo-314.json lines 4101-4500."""
import io, json, re, sys

SRC = r"H:\Archive\devin-zh-hans\tools\data\nls-todo-314.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\n10.json"
START, END = 4101, 4500

KEY_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*:')
PH_RE = re.compile(r'\{\d+\}')

rows = []
with io.open(SRC, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        m = KEY_RE.match(line)
        if m:
            rows.append((i, json.loads('"' + m.group(1) + '"')))
src_keys = [k for (ln, k) in rows if START <= ln <= END]

raw = io.open(OUT, "rb").read()
problems = []

# --- format checks -----------------------------------------------------
if raw.startswith(b"\xef\xbb\xbf"):
    problems.append("BOM present")
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError as e:
    print("FAIL: not valid UTF-8:", e)
    sys.exit(1)
data = json.loads(text)
out_keys = list(data.keys())

if out_keys != src_keys:
    problems.append("key set/order mismatch")
    for i, (a, b) in enumerate(zip(src_keys, out_keys)):
        if a != b:
            problems.append("  first diff at index %d: src=%r out=%r" % (i, a, b))
            break
    if len(src_keys) != len(out_keys):
        problems.append("  length %d vs %d" % (len(src_keys), len(out_keys)))

for n, line in enumerate(text.split("\n"), 1):
    if line and not line.startswith("  ") and not line.startswith("}") and not line.startswith("{"):
        problems.append("line %d not 2-space indented" % n)
        break
if "\t" in text:
    problems.append("tab found")
if re.search(r',\s*[}\]]', text):
    problems.append("trailing comma found")
if not text.endswith("\n"):
    problems.append("missing trailing newline")

# --- per-entry checks --------------------------------------------------
bad_quote, bad_slash, empty, ph_mismatch, same_as_src, you = [], [], [], [], [], []
for k, v in data.items():
    if v is None or v == "":
        empty.append(k)
        continue
    if '"' in v:
        bad_quote.append(k)
    if "\\" in v:
        bad_slash.append(k)
    kp = PH_RE.findall(k)
    vp = PH_RE.findall(v)
    if sorted(kp) != sorted(vp):
        ph_mismatch.append((k, kp, vp))
    if v == k:
        same_as_src.append(k)
    if "您" in v:
        you.append(k)

for name, lst in (("empty values", empty),
                  ("half-width double quote in value", bad_quote),
                  ("backslash in value", bad_slash),
                  ("identical to source", same_as_src),
                  ("uses 您", you)):
    if lst:
        print("NOTE %s: %d -> %s" % (name, len(lst), lst[:8]))
if ph_mismatch:
    problems.append("placeholder mismatch in %d entries: %s" % (len(ph_mismatch), ph_mismatch[:5]))
if empty:
    problems.append("empty values: %d" % len(empty))

# escape sanity: raw file may only contain \" \\ \n \t \/ \b \f \r \u
for m in re.finditer(r'\\(.)', text):
    if m.group(1) not in 'n"\\/bfrtu':
        problems.append("odd escape \\%s at %d" % (m.group(1), m.start()))

# literal newlines in keys must be mirrored in values
nl_entries = [k for k in src_keys if "\n" in k]
print("entries with literal newlines in key: %d" % len(nl_entries))
for k in nl_entries:
    if data[k].count("\n") != k.count("\n"):
        problems.append("newline count differs for multi-line entry: %r" % k[:60])

# [[...]] link markers must survive verbatim
missing_links = []
for k in src_keys:
    for link in re.findall(r'\[\[[^\]]+\]\]', k):
        if link not in data[k]:
            missing_links.append((k[:40], link))
if missing_links:
    problems.append("lost [[...]] markers: %s" % missing_links)
print("[[...]] markers preserved: %d -> %d" % (
    sum(len(re.findall(r'\[\[[^\]]+\]\]', k)) for k in src_keys),
    sum(len(re.findall(r'\[\[[^\]]+\]\]', data[k])) for k in src_keys)))

print("entries: %d (expected %d)" % (len(data), END - START + 1))
print("source keys in range: %d" % len(src_keys))
print("keys with placeholders: %d" % sum(1 for k in src_keys if PH_RE.search(k)))
print("==== %s ====" % ("ALL CHECKS PASSED" if not problems else "FAILED"))
for p in problems:
    print("  -", p)
sys.exit(1 if problems else 0)
