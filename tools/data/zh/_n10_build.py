# -*- coding: utf-8 -*-
"""Build zh/n10.json for nls-todo-314.json lines 4101-4500 (400 entries).

Keys are taken verbatim from the source file (JSON-decoded), translations are
keyed by 1-based source line number, so no key can be mis-transcribed.
"""
import io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _n10_tr_a import TR as TR_A          # noqa: E402
from _n10_tr_b import TR as TR_B          # noqa: E402

SRC = r"H:\Archive\devin-zh-hans\tools\data\nls-todo-314.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\n10.json"
START, END = 4101, 4500

KEY_RE = re.compile(r'^"((?:[^"\\]|\\.)*)"\s*:')
PH_RE = re.compile(r'\{\d+\}')

TR = {}
TR.update(TR_A)
TR.update(TR_B)

# Brand / product names intentionally left verbatim (Microsoft Teams).
ALLOW_SAME = {4268}


def main():
    rows = []
    with io.open(SRC, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            m = KEY_RE.match(line)
            if m:
                rows.append((i, json.loads('"' + m.group(1) + '"')))

    slice_rows = [(ln, k) for (ln, k) in rows if START <= ln <= END]
    print("source lines %d-%d -> %d keys" % (START, END, len(slice_rows)))
    print("translations supplied: %d" % len(TR))

    lens = [ln for ln, _ in slice_rows]
    missing = [ln for ln in lens if ln not in TR]
    extra = sorted(ln for ln in TR if ln not in set(lens))
    if missing or extra:
        print("MISSING lines: %s" % missing)
        print("EXTRA lines:   %s" % extra)
        sys.exit(2)

    problems = []
    data = {}
    for ln, key in slice_rows:
        val = TR[ln]
        if not val.strip():
            problems.append("line %d: empty translation" % ln)
        if '"' in val:
            problems.append("line %d: half-width double quote in value" % ln)
        if "\\" in val:
            problems.append("line %d: backslash in value" % ln)
        kp = sorted(PH_RE.findall(key))
        vp = sorted(PH_RE.findall(val))
        if kp != vp:
            problems.append("line %d: placeholders %s vs %s" % (ln, kp, vp))
        if key.count("\n") != val.count("\n"):
            problems.append("line %d: newline count %d vs %d"
                            % (ln, key.count("\n"), val.count("\n")))
        if val == key and ln not in ALLOW_SAME:
            problems.append("line %d: identical to source" % ln)
        data[key] = val

    if len(data) != len(slice_rows):
        problems.append("duplicate keys collapsed: %d vs %d" % (len(data), len(slice_rows)))

    if problems:
        print("BLOCKED:")
        for p in problems:
            print("  -", p)
        sys.exit(3)

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote %s (%d entries, %d bytes)" % (OUT, len(data), os.path.getsize(OUT)))


main()
