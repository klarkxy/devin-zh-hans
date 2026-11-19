# -*- coding: utf-8 -*-
"""w37 批次校验：键集合 + 顺序 + {{...}} 占位符多重集 + 标签多重集 + 值内禁用字符。"""
import json, re, sys, collections

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
DST = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w37.json"

with open(SRC, encoding="utf-8") as f:
    lines = f.read().split("\n")

# 1 基行号 7601..8000 -> 0 基索引 7600..7999
chunk = lines[7600:8000]
assert len(chunk) == 400, "源区间行数不是 400：%d" % len(chunk)
body = "\n".join(chunk).rstrip()
if body.endswith(","):
    body = body[:-1]
src = json.loads("{\n" + body + "\n}")
src_keys = list(src.keys())

with open(DST, encoding="utf-8") as f:
    raw = f.read()
dst = json.loads(raw)
dst_keys = list(dst.keys())

ok = True
def bad(msg):
    global ok
    ok = False
    print("FAIL " + msg)

# 键集合
if set(src_keys) != set(dst_keys):
    bad("键集合不一致")
    for k in src_keys:
        if k not in dst:
            print("   缺少键: " + repr(k))
    for k in dst_keys:
        if k not in src:
            print("   多余键: " + repr(k))
# 顺序
if src_keys != dst_keys:
    bad("键顺序不一致")
    for i, (a, b) in enumerate(zip(src_keys, dst_keys)):
        if a != b:
            print("   首个差异 #%d: %r != %r" % (i + 1, a, b))
            break
if len(src_keys) != 400:
    bad("源区间条目数 %d != 400" % len(src_keys))
if len(dst_keys) != len(set(dst_keys)):
    dup = [k for k, c in collections.Counter(dst_keys).items() if c > 1]
    bad("产出有重复键: %r" % dup)

PH = re.compile(r"\{\{.*?\}\}")
TAG = re.compile(r"</?[A-Za-z][^<>]*>")

ph_bad, tag_bad, ch_bad, empty = [], [], [], []
for k in src_keys:
    if k not in dst:
        continue
    v = dst[k]
    ks, vs = collections.Counter(PH.findall(k)), collections.Counter(PH.findall(v))
    if ks != vs:
        ph_bad.append((k, dict(ks), dict(vs)))
    kt, vt = collections.Counter(TAG.findall(k)), collections.Counter(TAG.findall(v))
    if kt != vt:
        tag_bad.append((k, sorted(kt), sorted(vt)))
    # 半角双引号
    if '"' in v:
        ch_bad.append((k, 'half-width "'))
    # 反斜杠：仓库既有约定允许 JSON 必需的 \n（w12/w20/w27 同例），其余一律不允许
    for m in re.finditer(r"\\(.)", v):
        if m.group(1) != "n":
            ch_bad.append((k, "backslash \\" + m.group(1)))
            break
    if not v.strip():
        empty.append(k)

for k, a, b in ph_bad:
    bad("占位符不一致: %r\n   源=%s 译=%s" % (k, a, b))
for k, a, b in tag_bad:
    bad("标签不一致: %r\n   源=%s 译=%s" % (k, a, b))
for k, why in ch_bad:
    bad("禁用字符(%s): %r" % (why, k))
for k in empty:
    bad("空译文: %r" % k)

print("-" * 60)
print("源区间条目: %d" % len(src_keys))
print("产出条目  : %d" % len(dst_keys))
print("占位符/标签/禁用字符: %s" % ("全部通过" if not (ph_bad or tag_bad) else "有问题"))
print("\\n 值（多行键）: %d" % sum(1 for k in src_keys if "\\n" in json.dumps(k, ensure_ascii=False) and "\\n" in json.dumps(dst.get(k, ""), ensure_ascii=False)))
same = [k for k in src_keys if dst.get(k) == k]
print("译文与原文完全相同（品牌/纯专名）: %d" % len(same))
for k in same:
    print("   · " + k)
print("-" * 60)
print("RESULT: " + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
