# -*- coding: utf-8 -*-
"""
analyze_nls.py — Devin 桌面版（Windsurf/Codeium 换皮 VS Code fork）NLS 缺口分析

输出（tools/data/）：
    coverage.md    覆盖率报告
    missing.json   完整缺口清单 {file, key, en}
    todo.json      按源文件分组的待译清单 {unique, by_file}（build_patch.py 的输入）
"""
import json, os, re, collections, io

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import (  # noqa: E402
    DEVIN_APP as _APP, LANGPACK as _LP, DATA as _DATA,
    DICT as _SHARED, PLUGIN as _PLUGIN, OUT as _OUT,
)
APP = _APP
LP = _LP
WS = os.path.join(APP, "extensions", "windsurf")
# 受限 shell 无法写 tools/data 时，用 DEVIN_ZH_DATA 重定向输出目录
OUTDIR = os.environ.get("DEVIN_ZH_DATA") or _DATA

if not APP:
    raise SystemExit("✗ 未找到 Devin 安装目录（用 DEVIN_INSTALL 指定）")
if not LP:
    raise SystemExit("✗ 未找到官方简体中文语言包（合并版需要它作底子）")

buf = io.StringIO()
def P(*a): print(*a, file=buf)

def load(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

keys_raw = load(os.path.join(APP, "out", "nls.keys.json"))
msgs_raw = load(os.path.join(APP, "out", "nls.messages.json"))
lp_raw   = load(os.path.join(LP, "translations", "main.i18n.json"))
lp_contents = lp_raw["contents"]

# 展平 keys: [(file, key), ...] 与 msgs_raw 顺序一一对应
flat = []
for entry in keys_raw:
    f, ks = entry[0], entry[1]
    for k in ks:
        flat.append((f, k))

P("# Devin 桌面版汉化可行性实证报告\n")
P(f"- Devin 安装目录: `{APP}`")
try:
    _prod = load(os.path.join(APP, "product.json"))
    _author = _prod.get("author")
    if isinstance(_author, dict):
        _author = _author.get("name", "")
    P("- 应用版本: %s %s / windsurfVersion %s / codeiumVersion %s%s"
      % (_prod.get("nameShort"), _prod.get("version"),
         _prod.get("windsurfVersion"), _prod.get("codeiumVersion"),
         (" (%s)" % _author) if _author else ""))
except Exception:
    P("- 应用版本: (读取 product.json 失败)")
P(f"- 语言包: `{LP}`\n")

P("## 1. NLS 结构\n")
P("| 文件 | 结构 | 规模 |")
P("|---|---|---:|")
P(f"| `out/nls.keys.json` | `[[源文件, [key,...]], ...]` | {len(keys_raw):,} 个源文件 |")
P(f"| `out/nls.messages.json` | 展平的默认英文数组 | {len(msgs_raw):,} 条 |")
P(f"| `main.i18n.json` → `contents` | `{{源文件: {{key: 译文}}}}` | {len(lp_contents):,} 个源文件 |")
P(f"\n展平后 key 总数 = **{len(flat):,}**  ·  与 messages 数组长度{'一致 ✅' if len(flat)==len(msgs_raw) else '不一致 ❌'}")

# 顺序映射
default = {}
if len(flat) == len(msgs_raw):
    for (f, k), m in zip(flat, msgs_raw):
        default.setdefault(f, {})[k] = m
else:
    for f, k in flat:
        default.setdefault(f, {})[k] = ""

# 覆盖计算
all_pairs = set(flat)
lp_pairs = set()
for f, kv in lp_contents.items():
    if isinstance(kv, dict):
        for k in kv:
            lp_pairs.add((f, k))

covered = all_pairs & lp_pairs
missing = all_pairs - lp_pairs
P("\n## 2. 覆盖率 (按 (源文件, key) 二元组)\n")
P(f"- 全部 NLS 字符串 : **{len(all_pairs):,}**")
P(f"- 官方语言包已译  : **{len(covered):,}** ({len(covered)/max(len(all_pairs),1)*100:.1f}%)")
P(f"- 缺中文          : **{len(missing):,}** ({len(missing)/max(len(all_pairs),1)*100:.1f}%)")

# 语言包 key 总数对比
lp_total = sum(len(v) for v in lp_contents.values() if isinstance(v, dict))
P(f"- 语言包译文总条数 : {lp_total:,}  (其中 {len(lp_pairs - all_pairs):,} 条本构建已不存在)")

# 专业化: Devin/Windsurf 新增文件
pat = re.compile(r"windsurf|devin|cascade|codeium|exa/|chat_client|acp", re.I)
own_miss = collections.Counter(f for f, k in missing)
own_tot  = collections.Counter(f for f, k in all_pairs)
P("\n## 3. 缺失字符串按源文件聚合 TOP 45\n")
P("| 缺失 | 该文件总数 | 源文件 |")
P("|---:|---:|---|")
for f, n in own_miss.most_common(45):
    P(f"| {n} | {own_tot[f]} | `{f}` |")

P("\n## 4. Devin/Windsurf 专有源文件\n")
P("| 缺失 | 总数 | 源文件 |")
P("|---:|---:|---|")
ws_files = [f for f in own_tot if pat.search(f)]
for f in sorted(ws_files, key=lambda x: -own_miss[x]):
    P(f"| {own_miss[f]} | {own_tot[f]} | `{f}` |")
P(f"\n专有文件合计: {len(ws_files)} 个文件, 全部 key {sum(own_tot[f] for f in ws_files):,}, 其中缺中文 {sum(own_miss[f] for f in ws_files):,}")

P("\n## 5. 缺中文的 Devin/Windsurf 字符串样例 (前 60)\n")
P("| 源文件 | 英文原文 |")
P("|---|---|")
shown = 0
for f in sorted(ws_files, key=lambda x: -own_miss[x]):
    for k in default.get(f, {}):
        if (f, k) in missing:
            txt = default[f][k].replace("|", "\\|").replace("\n", " ")[:130]
            P(f"| `{f.split('/')[-1]}` | {txt} |")
            shown += 1
            if shown >= 60: break
    if shown >= 60: break

P("\n## 6. 完全缺中文的源文件 (语言包零覆盖)\n")
zero = [f for f in own_tot if own_miss[f] == own_tot[f] and own_tot[f] >= 3]
P(f"共 {len(zero)} 个文件。前 30：\n")
for f in sorted(zero, key=lambda x: -own_tot[x])[:30]:
    P(f"- `{f}` ({own_tot[f]} 条)")

# windsurf 扩展 package.json 硬编码情况
WS = os.path.join(APP, "extensions", "windsurf")
pkg = load(os.path.join(WS, "package.json"))
cmds = pkg.get("contributes", {}).get("commands", [])
hard = [c for c in cmds if isinstance(c.get("title"), str) and not str(c["title"]).startswith("%")]
nls_files = [x for x in os.listdir(WS) if x.startswith("package.nls")]
P("\n## 7. 内置扩展的贡献点（Devin 家族）\n")
P("| 扩展 | 命令数 | 硬编码英文 title | 目录内 package.nls* |")
P("|---|---:|---:|---|")
FAMILY = ["windsurf", "windsurf-dev-containers", "windsurf-remote-devin",
          "windsurf-remote-openssh", "windsurf-remote-wsl"]
for name in FAMILY:
    p = os.path.join(APP, "extensions", name, "package.json")
    if not os.path.exists(p):
        continue
    _p = load(p)
    _c = _p.get("contributes", {}).get("commands", []) or []
    _hard = [c for c in _c if isinstance(c.get("title"), str) and not str(c["title"]).startswith("%")]
    _nls = [x for x in os.listdir(os.path.join(APP, "extensions", name)) if x.startswith("package.nls")]
    P("| `%s` | %d | %d | %s |" % (name, len(_c), len(_hard), "、".join(_nls) if _nls else "**无**"))
P("\n结论: 这些扩展的命令标题、菜单、配置项说明全部硬编码英文，**官方语言包机制无法覆盖**；")
P("本插件的做法是写 `package.nls.json` / `package.nls.zh-cn.json` 并把 package.json 里的字符串换成 `%key%`")
P("（见 `tools/build_manifest_plan.py` 与 `extension.js` 的第 2 层）。")

# 导出完整清单
exp = {
    "total": len(all_pairs), "covered": len(covered), "missing": len(missing),
    "missing_list": [
        {"file": f, "key": k, "en": default.get(f, {}).get(k, "")}
        for f, k in sorted(missing)
    ],
}
with open(os.path.join(OUTDIR, "missing.json"), "w", encoding="utf-8") as fh:
    json.dump(exp, fh, ensure_ascii=False, indent=1)

# todo.json：build_patch.py 的输入，按源文件分组
by_file = collections.defaultdict(list)
for f, k in sorted(missing):
    by_file[f].append({"key": k, "en": default.get(f, {}).get(k, "")})
uniq = collections.Counter(default.get(f, {}).get(k, "") for f, k in missing)
with open(os.path.join(OUTDIR, "todo.json"), "w", encoding="utf-8") as fh:
    json.dump({"unique": [[e, n] for e, n in uniq.most_common() if e],
               "by_file": dict(by_file)}, fh, ensure_ascii=False, indent=1)

with open(os.path.join(OUTDIR, "coverage.md"), "w", encoding="utf-8") as fh:
    fh.write(buf.getvalue())
print("OK missing =", len(missing), "total =", len(all_pairs), "files =", len(by_file))
