# -*- coding: utf-8 -*-
"""w39 verification: source segment vs output, key-by-key."""
import json, re, io

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w39.json"
REP = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\_w39_verify.txt"

rep = io.StringIO()
fails = []

raw = open(OUT, "rb").read()
if raw.startswith(b"\xef\xbb\xbf"):
    fails.append("BOM present in output")
text = raw.decode("utf-8")

lines = open(SRC, encoding="utf-8").read().splitlines()
seg = lines[8400:8800]
src_keys = []
for s in seg:
    idx = s.rindex('":')
    src_keys.append(s[:idx + 1])

out = json.loads(text)
out_keys = list(out.keys())

# byte-exact key check: lift the raw key text back out of each output line
out_raw = []
for l in text.splitlines():
    if l.startswith('  "') or l.startswith('  ?"'):
        pass
for l in text.splitlines()[1:]:
    if l == "}":
        continue
    out_raw.append(l[2:l.rindex('":') + 1])

if len(out_raw) != 400:
    fails.append("raw key lines %d != 400" % len(out_raw))
if out_raw != src_keys:
    fails.append("raw key text mismatch (byte level)")
    for i, (a, b) in enumerate(zip(src_keys, out_raw)):
        if a != b:
            rep.write("RAW MISMATCH at %d\n  src: %r\n  out: %r\n" % (i, a, b))
            break
rep.write("raw key lines compared: %d, byte-exact: %s\n" % (len(out_raw), out_raw == src_keys))
if out_keys != [json.loads("{" + k + ":0}").popitem()[0] for k in src_keys]:
    fails.append("parsed key set/order mismatch")

if len(out_keys) != 400:
    fails.append("key count %d != 400" % len(out_keys))

# JSON string values -> the raw file text must have no \" or \\ inside a value
for i, (k, v) in enumerate(zip(src_keys, out_keys)):
    val = out[v]
    if '"' in val:
        fails.append("entry %d has straight quote in value: %r" % (i, val))
    if "\\" in val:
        fails.append("entry %d has backslash in value: %r" % (i, val))
    if not val.strip():
        fails.append("entry %d empty value" % i)

ph = re.compile(r"\{\{[^{}]*\}\}")
for i, (k, v) in enumerate(zip(src_keys, out_keys)):
    val = out[v]
    ks, vs = sorted(ph.findall(k)), sorted(ph.findall(val))
    if ks != vs:
        fails.append("placeholder mismatch %d: %r vs %r" % (i, ks, vs))

tag = re.compile(r"</?[A-Za-z][A-Za-z0-9]*>")
for i, (k, v) in enumerate(zip(src_keys, out_keys)):
    val = out[v]
    kt, vt = sorted(tag.findall(k)), sorted(tag.findall(val))
    if kt != vt:
        fails.append("tag mismatch %d: %r vs %r" % (i, kt, vt))

def endp(s):
    if s.endswith("。"):
        return "z"
    if s.endswith("……") or s.endswith("…"):
        return "e"
    return "n"

endmis = []
for i, (k, v) in enumerate(zip(src_keys, out_keys)):
    val = out[v]
    ks = "z" if v.endswith(".") else ("e" if (v.endswith("…") or v.endswith("...")) else "n")
    vs = endp(val)
    if ks != vs:
        endmis.append((i, k, val, ks, vs))

# untranslated check
cjk = re.compile(r"[\u4e00-\u9fff]")
for i, (k, v) in enumerate(zip(src_keys, out_keys)):
    val = out[v]
    if not cjk.search(val):
        fails.append("no CJK in value %d: %r" % (i, val))
    if val == k:
        fails.append("value equals key %d" % i)

# formatting checks
bad_indent = [n for n, l in enumerate(text.split("\n")[1:-2], start=2) if l and not l.startswith("  ")]
if bad_indent:
    fails.append("indent anomalies at file lines %r" % bad_indent[:5])
if text.count("\t"):
    fails.append("tab characters present")
if not text.rstrip("\n").endswith("}"):
    fails.append("output does not end with closing brace")
for n, l in enumerate(text.split("\n"), start=1):
    if not l or l in ("{", "}"):
        continue
    if not l.endswith(",") and n != len(text.split("\n")) - 2:
        fails.append("line %d lacks trailing comma: %r" % (n, l[:40]))

dupval = {}
for k in out_keys:
    dupval.setdefault(out[k], []).append(k)
dups = {v: ks for v, ks in dupval.items() if len(ks) > 1}

rep.write("entries: %d\n" % len(out_keys))
rep.write("duplicate-value groups: %d\n" % len(dups))
for v, ks in dups.items():
    rep.write("  VALUE %s  == %d keys\n" % (v, len(ks)))
rep.write("\nfinal-punctuation mismatches (%d):\n" % len(endmis))
for i, k, val, ks, vs in endmis:
    rep.write("  #%d src_end=%s val_end=%s\n    KEY %s\n    VAL %s\n" % (i, ks, vs, k, val))
rep.write("\nFAILURES: %d\n" % len(fails))
for f in fails:
    rep.write("  ! " + f + "\n")
open(REP, "w", encoding="utf-8").write(rep.getvalue())
print("entries", len(out_keys), "failures", len(fails), "endmismatch", len(endmis), "dupvals", len(dups))
