# -*- coding: utf-8 -*-
"""Independent verification: source range vs produced w41.json."""
import io, json, re, collections, sys

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w41.json"

raw = io.open(SRC, encoding="utf-8").read().split("\n")
src_keys = []
for ln in raw[9200:9600]:
    s = ln.strip()
    if s.endswith(","):
        s = s[:-1]
    src_keys.append(list(json.loads("{" + s + "}").keys())[0])

raw_out = io.open(OUT, "rb").read()
assert not raw_out.startswith(b"\xef\xbb\xbf"), "BOM present"
text = raw_out.decode("utf-8")
data = json.loads(text)
out_keys = list(data.keys())

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg)

# 1. JSON round-trip + key order/set
check(out_keys == src_keys, "key order/set mismatch (src %d, out %d)" % (len(src_keys), len(out_keys)))
check(data == json.loads(text), "roundtrip")
check(text.startswith('{\n  "') and text.endswith("\n"), "2-space indent / trailing newline")
check("\r" not in text, "CRLF line endings")
check(len([l for l in text.split("\n") if re.match(r'^   +"', l)]) == 0, "indent wider than 2 spaces")
check(len([l for l in text.split("\n") if re.match(r'^  "', l)]) == 400, "key line count != 400")
check(",}" not in text and ",]" not in text, "trailing comma")

# 2. exact key byte equality
for i, (a, b) in enumerate(zip(src_keys, out_keys)):
    if a != b:
        fails.append("key[%d] differs: %r != %r" % (i, a, b))

ph = re.compile(r"\{\{[^{}]*\}\}")
sb = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")
tg = re.compile(r"</?[A-Za-z][A-Za-z0-9]*>")

identical_allowed = {
    "VNC", "Vanta", "Veracode", "Vercel", "Visor", "WDW", "WhatsApp",
    "Webhook", "Webhook URL", "V{{version}}",
}
identical = []
for k, v in data.items():
    check(bool(v.strip()), "empty value: %r" % k)
    check(v == v.strip(), "leading/trailing space: %r" % k)
    check('"' not in v, "half-width quote in value: %r" % k)
    check("\\" not in v, "backslash in value: %r" % k)
    check(collections.Counter(ph.findall(k)) == collections.Counter(ph.findall(v)),
          "{{}} placeholder mismatch: %r -> %r (%s vs %s)" % (k, v, ph.findall(k), ph.findall(v)))
    check(collections.Counter(sb.findall(k)) == collections.Counter(sb.findall(v)),
          "{} placeholder mismatch: %r -> %r (%s vs %s)" % (k, v, sb.findall(k), sb.findall(v)))
    check(collections.Counter(tg.findall(k)) == collections.Counter(tg.findall(v)),
          "tag mismatch: %r -> %r" % (k, v))
    if v == k:
        identical.append(k)
        check(k in identical_allowed, "untranslated entry: %r" % k)

# 3. punctuation mirroring
for k, v in data.items():
    ks = k.rstrip()
    if ks.endswith("..."):
        check(v.endswith("\u2026\u2026"), "ellipsis: %r -> %r" % (k, v))
    elif ks.endswith("\u2026"):
        check(v.endswith("\u2026\u2026"), "ellipsis: %r -> %r" % (k, v))
    elif ks.endswith("."):
        check(v.endswith("\u3002"), "period: %r -> %r" % (k, v))
    if ks.endswith("?"):
        check(v.endswith("\uff1f"), "qmark: %r -> %r" % (k, v))
    if ks.endswith(":"):
        check(v.endswith("\uff1a"), "colon: %r -> %r" % (k, v))

# 4. spacing rule report (informational)
adj = re.compile(r"(?:[\u4e00-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u4e00-\u9fff])")
spacing = []
for k, v in data.items():
    stripped = re.sub(r"</?[A-Za-z][A-Za-z0-9]*>", "", v)
    stripped = ph.sub(" ", stripped)
    stripped = sb.sub(" ", stripped)
    m = adj.findall(stripped)
    if m:
        spacing.append((k, v, m))

print("source keys:", len(src_keys), "| output keys:", len(out_keys))
print("identical-to-source (allowed brand/no-op):", len(identical))
for k in identical:
    print("   ", repr(k))
print("HARD FAILS:", len(fails))
for f in fails:
    print("  FAIL", f)
print("spacing flags:", len(spacing))
for k, v, m in spacing:
    print("   ", m, "|", v)
sys.exit(1 if fails else 0)
