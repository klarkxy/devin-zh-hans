# -*- coding: utf-8 -*-
"""Verify w44.json against source lines 10401-10800 of webapp-todo.json."""
import json, re, sys, collections

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w44.json"
START, END = 10401, 10800

SKIP = [
    "{{count}}/{{max}}",
    "{{current}} / {{total}}",
    "{{current}} / {{total}}+",
    "{{dollars}} = {{count}} ACU",
    "{{dollars}} = {{count}} ACUs",
    "{{done}}/{{total}}",
    "{{emoji}} {{names, list}}",
    "{{endpoints}} \u00b7 {{cells}}",
    "{{environment}} \u00b7 {{runAs}}",
    "{{eventType}} \u00b7 {{when}}",
    "{{findings}} {{outcome}}",
    "{{formattedCount}} ACU",
    "{{formattedCount}} ACUs",
    "{{formattedSettled}}/{{formattedTotal}}",
    "{{from}} \u2013 {{to}}",
    "{{hours}}h",
    "{{included}} \u00b7 {{excluded}}",
    "{{index}}/{{count}}",
    "{{kinds, list}}",
    "{{labels, list(type: unit)}}",
    "{{label}} \u00d7{{count}}",
    "{{levels, list(style: short)}}",
    "{{levels, list}}",
    "{{minutes}}m",
    "{{minutes}}m {{seconds}}s",
    "{{multiplier}}x",
    "{{names, list(type: unit)}}",
    "{{names, list}}",
    "{{name}} +{{count}}",
]

raw = open(SRC, encoding="utf-8").read().splitlines()
seg = raw[START - 1:END]
print("source segment:", len(seg), "lines |", START, "->", END)

src_keys = []
for i, ln in enumerate(seg, start=START):
    m = re.match(r'^("(?:[^"\\]|\\.)*")\s*:\s*""\s*,?\s*$', ln)
    src_keys.append(json.loads(m.group(1)))
print("source keys parsed:", len(src_keys))

blob = open(OUT, "rb").read()
text = blob.decode("utf-8")
pairs = json.loads(text, object_pairs_hook=lambda p: p)
out_keys = [k for k, _ in pairs]
out_map = dict(pairs)
lines = text.splitlines()

checks = {}
checks["utf8_no_bom"] = (not blob.startswith(b"\xef\xbb\xbf"), "no BOM, decodes as UTF-8")
checks["json_object_root"] = (text.lstrip().startswith("{") and text.rstrip().endswith("}"), "root is one object")
checks["2space_indent"] = (all(l.startswith('  "') for l in lines[1:-1]) and lines[-1] == "}",
                           f"{len(lines)} physical lines, body entries all 2-space indented, closes with single }}")
checks["no_trailing_comma"] = (not re.search(r",\s*[}\]]", text), "no trailing comma")
checks["no_duplicate_keys"] = (len(out_keys) == len(set(out_keys)), f"{len(out_keys)} pairs / {len(set(out_keys))} unique")

missing = [k for k in src_keys if k not in out_map]
extra = [k for k in out_keys if k not in set(src_keys)]
checks["missing_equals_skiplist"] = (missing == SKIP, f"missing={len(missing)} skipped_listed={len(SKIP)} exact_match={missing == SKIP}")
checks["no_extra_keys"] = (not extra, f"extra={extra}")

expected_out = [k for k in src_keys if k in out_map]
checks["order_matches_source"] = (out_keys == expected_out, "output order == source order (skip rows removed)")

PH = re.compile(r"\{\{[^{}]*\}\}")
ph_bad = [(k, collections.Counter(PH.findall(k)), collections.Counter(PH.findall(out_map[k])))
          for k in out_keys
          if collections.Counter(PH.findall(k)) != collections.Counter(PH.findall(out_map[k]))]
checks["placeholder_multiset_match"] = (not ph_bad, f"{len(ph_bad)} mismatches")
for k, a, b in ph_bad:
    print("   PH MISMATCH:", k[:70], dict(a), "!=", dict(b))

q_bad = [k for k in out_keys if '"' in out_map[k] or "\\" in out_map[k]]
checks["no_ascii_quote_or_backslash"] = (not q_bad, f"{len(q_bad)} offending values")
for k in q_bad:
    print("   BAD VALUE:", k[:60], "->", out_map[k][:90])

checks["no_empty_values"] = (all(out_map[k].strip() for k in out_keys), "all values non-empty")
identical = [k for k in out_keys if out_map[k] == k]
checks["no_value_identical_to_source"] = (not identical, f"{len(identical)} identical")

# codepoint-by-codepoint key equality against the source range
cp_bad = [k for k in out_keys if k not in set(src_keys)]
checks["keys_byte_identical"] = (not cp_bad, "every output key matches a source key character-for-character")

body = text.split("\n", 1)[1].rstrip("\n}")
tag_bad = [(k, v) for k, v in out_map.items()
           if re.findall(r"</?[A-Za-z][^>]*>", k) and [t.lower() for t in re.findall(r"</?[A-Za-z][^>]*>", k)]
           != [t.lower() for t in re.findall(r"</?[A-Za-z][^>]*>", v)]]
checks["html_tags_preserved"] = (not tag_bad, f"{len(tag_bad)} tag mismatches")

print("\n--- CHECK RESULTS ---")
ok = True
for name, (passed, detail) in checks.items():
    print(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")
    ok = ok and passed

print(f"\ntranslated {len(out_keys)} / source {len(src_keys)} / skipped {len(missing)}")
print("\nvalues that still contain latin runs (expected: brands, MCP/PR/CLI/API/OAuth, ids):")
for k in out_keys:
    rest = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff\s]", " ", PH.sub("", out_map[k]))
    w = [x for x in rest.split() if re.fullmatch(r"[A-Za-z]{4,}", x) and x.lower() not in ("devin", "mcp", "oauth", "cli", "api")]
    if w:
        print("  ", k[:55], "->", sorted(set(w)))
print("\nRESULT:", "ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
