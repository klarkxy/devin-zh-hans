# -*- coding: utf-8 -*-
"""w35 校验器：源文件 6801-7200 行 vs 产出 w35.json 逐键比对。"""
import json, re, collections, sys

SRC = r"H:\Archive\devin-zh-hans\tools\data\webapp-todo.json"
OUT = r"H:\Archive\devin-zh-hans\tools\data\zh\webapp\w35.json"

raw = open(SRC, "rb").read()
assert not raw.startswith(b"\xef\xbb\xbf"), "src has BOM"
lines = raw.decode("utf-8").split("\n")
seg_lines = lines[6800:7200]           # 0 基索引 -> 1 基 6801..7200
assert len(seg_lines) == 400, len(seg_lines)

# 从原始行文本里取键（行首第一个 " 到行尾 ": "" 之前），逐字符
raw_keys = []
line_re = re.compile(r'^"((?:[^"\\]|\\.)*)":\s*""\s*,?\s*$')
for ln in seg_lines:
    m = line_re.match(ln)
    if not m:
        print("UNPARSED LINE:", repr(ln[:120]))
        sys.exit(1)
    raw_keys.append(m.group(1))

out_raw = open(OUT, "rb").read()
assert not out_raw.startswith(b"\xef\xbb\xbf"), "out has BOM"
out_txt = out_raw.decode("utf-8")
assert out_txt.endswith("\n")
assert "\r" not in out_txt, "CRLF found"
out = json.loads(out_txt, object_pairs_hook=collections.OrderedDict)
out_keys = list(out.keys())

print("源区间键数:", len(raw_keys))
print("产出键数  :", len(out_keys))

# 1. 键集合 + 顺序（用 JSON 解码后的字符串比较，等价于逐字符）
ok = True
if len(raw_keys) != len(out_keys):
    ok = False
    print("FAIL: 数量不一致")
decoded_src = [json.loads('"' + k + '"') for k in raw_keys]
if decoded_src != out_keys:
    ok = False
    print("FAIL: 键顺序/内容不一致")
    for i, (a, b) in enumerate(zip(decoded_src, out_keys)):
        if a != b:
            print("  首个差异 idx", i, "src=", repr(a), "out=", repr(b))
            break
if set(decoded_src) != set(out_keys):
    ok = False
    print("FAIL: 键集合不一致")
    print("  only-src:", list(set(decoded_src) - set(out_keys))[:5])
    print("  only-out:", list(set(out_keys) - set(decoded_src))[:5])

# 2. 键的原始文本形态（含 \" 转义）与产出文件里重新序列化后的形态一致
PH = re.compile(r"\{\{[^{}]*\}\}")
TAG = re.compile(r"</?[A-Za-z][^>]*>")
problems = []
for i, k in enumerate(decoded_src):
    t = out[k]
    if not isinstance(t, str):
        problems.append((i, "value not str"))
    if '"' in t:
        problems.append((i, "半角双引号", k))
    if "\\" in t:
        problems.append((i, "反斜杠", k))
    if collections.Counter(PH.findall(k)) != collections.Counter(PH.findall(t)):
        problems.append((i, "占位符多重集", k))
    if collections.Counter(TAG.findall(k)) != collections.Counter(TAG.findall(t)):
        problems.append((i, "标签", k))
    if t.strip() == "":
        problems.append((i, "空译文", k))

# 3. 格式：2 空格缩进、可被标准 json 重排一致
canon = json.dumps(json.loads(out_txt, object_pairs_hook=collections.OrderedDict),
                   ensure_ascii=False, indent=2) + "\n"
if canon != out_txt:
    ok = False
    print("FAIL: 缩进/格式非 2 空格标准形态")

# 4. 与源区间逐行对照打印（抽样）
print("\n抽样对照：")
for idx in (0, 1, 82, 99, 199, 299, 340, 374, 399):
    print(" ", idx, "|", decoded_src[idx][:64])
    print("     ->", out[decoded_src[idx]][:64])

print("\n问题项:", len(problems))
for p in problems[:20]:
    print("  ", p)

if problems or not ok:
    print("\nRESULT: FAIL")
    sys.exit(1)

# 5. 覆盖源区间之外无多余键（已由数量+顺序保证）
print("\nRESULT: PASS  (400/400 键逐字符一致，顺序一致，占位符/标签多重集一致，译文无半角引号与反斜杠)")
