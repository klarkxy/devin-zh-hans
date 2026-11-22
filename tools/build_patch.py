# -*- coding: utf-8 -*-
"""
build_patch.py — 由词表生成插件产物

输入（tools/data/）：
    todo.json          NLS 缺口清单（由 analyze_nls.py 生成）
    zh/g1..g4.json     历史缺口的 en -> 中文
    zh/g6.json         Devin 3.11.x 新增缺口的 en -> 中文
    zh/g7.json         内置扩展贡献点的 en -> 中文
    webapp.json        webapp-host 的 i18n key（由 analyze_webapp.py 生成）

输出（仓库根）：
    translations/main.i18n.json               官方译文 + 本插件补充的合并版语言包
    translations/extensions/windsurf.i18n.json  windsurf 扩展贡献点（兼容旧的语言包路线）
    assets/ui-dict.json                        DOM 翻译器通用词典
    assets/ui-strings-zh.json                  DOM 翻译器人工词表（含 webapp 专有文案）
    assets/ext-manifest.*.json                 内置扩展贡献点的落地计划（见 build_manifest_plan.py）
    assets/webapp-i18n.json                    webapp-host i18next 覆盖表（en -> zh）
    tools/data/meta.json / build.log

前提：本机已安装官方简体中文语言包（合并版的底子来自它）。
"""
import json, os, re, sys, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import (  # noqa: E402
    DEVIN_APP as _APP, LANGPACK as _LP, DATA as _DATA,
    DICT as _DICT, PLUGIN as _PLUGIN,
)
# 词表输入目录（不受 DEVIN_ZH_DATA 输出重定向影响）
ZH_IN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "zh")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# build_patch 直接写插件产物目录；_paths 已支持 DEVIN_ZH_* 重定向（受限 shell 用）。
from _paths import TRANS as _T, ASSETS as _A  # noqa: E402
TRANS = _T
TRANS_EXT = os.path.join(TRANS, "extensions")
ASSETS = _A
for _d in (TRANS, TRANS_EXT, ASSETS, _DATA):
    os.makedirs(_d, exist_ok=True)

log = []


def L(*a):
    s = " ".join(str(x) for x in a)
    log.append(s)
    print(s)


def rd(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def wr(p, obj, indent=None, sort=False):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, sort_keys=sort)


L("Devin 安装目录 :", _APP)
L("中文语言包     :", _LP)

# ───────────────────────── 读译文 ─────────────────────────
todo = rd(os.path.join(_DATA, "todo.json"))["by_file"]      # {file: [{key,en}]}
en2zh = {}
# n*.json：3.14 大更新（NLS 缺口 7,027 条）的分批译文；与 g 词表同格式、直接并入。
NLS_GLOBS = ("g[0-9]*.json", "n[0-9]*.json")
nls_tables = []
for pat in NLS_GLOBS:
    nls_tables.extend(sorted(glob.glob(os.path.join(ZH_IN, pat))))
for p in nls_tables:
    d = rd(p)
    d.pop("_comment", None)
    en2zh.update(d)
L("NLS 译文条数   :", len(en2zh), "（来自", len(nls_tables), "个词表）")

# ───────────────────────── 1. NLS 补充表 ─────────────────────────
supp = {}
miss_en = []
for f, items in todo.items():
    for it in items:
        z = en2zh.get(it["en"])
        if not z:
            miss_en.append(it["en"])
            continue
        supp.setdefault(f, {})[it["key"]] = z
n_supp = sum(len(v) for v in supp.values())
L("\n[1] NLS 补充表:", n_supp, "条 /", len(supp), "个源文件")
if miss_en:
    L("    ⚠ 未命中译文:", len(miss_en), miss_en[:3])

wr(os.path.join(_DATA, "nls-supplement.json"), supp, indent=1)

# ───────────────────────── 2. 合并版语言包 ─────────────────────────
if not _LP:
    L("[2] ✗ 未找到官方中文语言包，无法生成合并版")
    sys.exit(1)

main = rd(os.path.join(_LP, "translations", "main.i18n.json"))
contents = main.setdefault("contents", {})

# Devin 升级后 NLS key 会变，合并版里会留下永远不会被查询的死条目
# （官方语言包本身就有约 1,000 条本构建已不存在的 key，上一版插件补充的也在内）。
# 用当前构建的 nls.keys.json 精确剔除：contents 只服务 vscode 核心 bundle，
# 不在 keys.json 里的 key 永远查不到，删掉纯属减重，不影响任何界面。
cur_keys = set()
keys_path = os.path.join(_APP or "", "out", "nls.keys.json")
if os.path.exists(keys_path):
    for entry in rd(keys_path):
        for k in entry[1]:
            cur_keys.add((entry[0], k))

pruned = 0
if cur_keys:
    for f in list(contents):
        tgt = contents.get(f)
        if not isinstance(tgt, dict):
            continue
        for k in list(tgt):
            if (f, k) not in cur_keys:
                del tgt[k]
                pruned += 1
        if not tgt:
            del contents[f]

added = 0
for f, kv in supp.items():
    tgt = contents.setdefault(f, {})
    for k, v in kv.items():
        if k not in tgt:
            tgt[k] = v
            added += 1

# 强制回正：官方 zh-hans 面向 VS Code，且部分按键、助记符存在上下文误译。
# 这些精确覆盖会在补充译文之后应用，因此也能修正官方包已经包含的 key。
context_fixed = 0
for fix_name in ("g8-brand.json", "context-overrides.json"):
    fix_path = os.path.join(ZH_IN, fix_name)
    if not os.path.exists(fix_path):
        continue
    for f, kv in rd(fix_path).items():
        tgt = contents.get(f)
        if not isinstance(tgt, dict):
            continue
        for k, v in kv.items():
            if tgt.get(k) != v:
                tgt[k] = v
                context_fixed += 1
L("[2b] 品牌与上下文回正: %d 条" % context_fixed)

out_main = os.path.join(TRANS, "main.i18n.json")
wr(out_main, main)
total = sum(len(v) for v in contents.values())
L("[2] main.i18n.json: 剔除死条目 %d 条, 新增 %d 条, 总 %s 条, %.2f MB"
  % (pruned, added, format(total, ","), os.path.getsize(out_main) / 1048576))

# ───────────────────────── 3. DOM 通用词典 ─────────────────────────
# DOM 层是按**可见文本**匹配的，所以词典的键必须是英文原文，不是 NLS key。
# 英文原文的来源是 out/nls.keys.json（顺序）与 out/nls.messages.json（值）—— 两者
# 逐项对应，可以精确还原「(源文件, key) -> 英文默认值」。再用合并版语言包的
# contents[源文件][key] 找到中文，就得到 (英文原文 -> 中文)。
#
# 早期版本错把 NLS key 当成了英文原文（例如拿 "desktopShell.goBack" 去匹配界面上的
# "Back"），结果词典条数看着不少、实际命中率很低。这里改成按原文建表。
nls_pairs = 0
ui = {}
keys_path = os.path.join(_APP or "", "out", "nls.keys.json")
msgs_path = os.path.join(_APP or "", "out", "nls.messages.json")
if os.path.exists(keys_path) and os.path.exists(msgs_path):
    _keys = rd(keys_path)
    _msgs = rd(msgs_path)
    _flat = [(e[0], k) for e in _keys for k in e[1]]
    if len(_flat) == len(_msgs):
        bad = re.compile(
            r"[\n\r\t<>{}]"                      # 多行 / 标记 / 插值
            r"|\$\(|//|https?:"                  # 命令 id / URL
            r"|\.(js|ts|css|json|md)\b|=>"       # 文件名 / 箭头
            r"|\bnull\b|\bundefined\b"
            r"|^\s|\s$"
        )
        for (f, k), en in zip(_flat, _msgs):
            if not isinstance(en, str):
                continue
            s = en.strip()
            if s != en or not (2 <= len(s) <= 60):
                continue
            if bad.search(s):
                continue
            if s.isupper() and len(s) > 2:
                continue
            if "%" in s or "&" in s:              # 占位符 / 加速键由语言包负责
                continue
            if not re.search(r"[A-Za-z]", s):
                continue
            z = (contents.get(f) or {}).get(k)
            if not isinstance(z, str) or not z.strip() or z.strip() == s:
                continue
            ui.setdefault(s, z)
        nls_pairs = len(_flat)
    else:
        L("    ⚠ nls.keys.json 与 nls.messages.json 长度不一致（%d vs %d），跳过原文词典"
          % (len(_flat), len(_msgs)))
else:
    L("    ⚠ 未找到 nls.keys.json / nls.messages.json，跳过原文词典")

wr(os.path.join(ASSETS, "ui-dict.json"), ui, indent=0, sort=True)
L("[3] DOM 通用词典: %s 条（由 %s 条 NLS 原文反查）(%.2f MB)"
  % (format(len(ui), ","), format(nls_pairs, ","),
     os.path.getsize(os.path.join(ASSETS, 'ui-dict.json')) / 1048576))
# ───────────────────────── 4. webapp-host 词表 ─────────────────────────
# 人工/agent 翻译的 webapp 文案（英文原文 -> 中文）。
# 两份产物用途不同，不能混：
#   assets/ui-strings-zh.json  DOM 层用：键是英文原文，必须能整串匹配到文本节点
#                              → 含 {{...}} 插值的条目要剔除（渲染后被替换成实际值）
#   assets/webapp-i18n.json    i18next 覆盖层用：键是 i18n key（点分），值是中文
#                              → 含 {{...}} 的反而要保留（i18next 会做插值）
webapp_zh = {}
# w*.json：分批翻译产物（todo 切片），未合并进 dict/webapp-zh.json 时也直接拾取。
# 与 README 的合并命令语义一致（那边会把同批文件折叠进 webapp-zh.json，重复读取无害）。
for p in (os.path.join(_DICT, "webapp-zh.json"),
          os.path.join(ZH_IN, "webapp-merged.json"),
          *sorted(glob.glob(os.path.join(ZH_IN, "webapp", "w*.json")))):
    if os.path.exists(p):
        webapp_zh.update(rd(p))
L("\n[4] webapp 词表:", len(webapp_zh), "条")

extra = {}
# 顺序即优先级：人工校订 > 旧界面词表 > DOM 增量词表 > webapp 译文
for name in ("ui-common-zh.json", "ui-strings-zh.json", "dom-30825.json"):
    p = os.path.join(_DICT, name)
    if os.path.exists(p):
        d = rd(p)
        d.pop("_comment", None)
        extra.update(d)
L("    人工校订词表:", len(extra), "条")

dom_extra = dict(extra)
for en, zh in webapp_zh.items():
    if not zh or zh.strip() == en.strip():
        continue
    if "{{" in en or "}}" in en:      # 插值模板，DOM 层匹配不到整串
        continue
    if re.fullmatch(r"[A-Za-z]", en):
        # 星期、尺寸等单字母只有 i18next 上下文才能区分；全局替换会误改菜单访问键。
        continue
    if len(en) > 200:
        continue
    dom_extra.setdefault(en, zh)      # 人工校订优先，不覆盖
wr(os.path.join(ASSETS, "ui-strings-zh.json"), dom_extra, indent=0, sort=True)
L("    assets/ui-strings-zh.json: %s 条 (%.2f MB)"
  % (format(len(dom_extra), ","), os.path.getsize(os.path.join(ASSETS, 'ui-strings-zh.json')) / 1048576))

# i18next 覆盖表：必须**保留命名空间结构**，否则 i18next 一条都查不到。
# 形状就是 en 资源树的子集：{ ns: { key: 中文 } }
#   i18next 查 "composerTips.newSession"  → root.composerTips.newSession
# 早期版本把它拍平成 { "newSession": … }，看似 4,575 条其实全废。
wa_ns = {}
en_path = os.path.join(_DATA, "webapp-en.json")
if os.path.exists(en_path):
    _en = rd(en_path)["namespaces"]
    # 用完整词典查（含 assets/ui-dict.json 从 NLS 反查来的通用词），
    # 否则 nav.security = "Security" 这类基础词会漏掉。
    # 先放入完整 webapp 词表：插值模板不能进 DOM，但必须保留给 i18next。
    # 再用通用词典和人工校订覆盖，保持既有的译文优先级。
    _lookup = dict(webapp_zh)
    for p in (os.path.join(ASSETS, "ui-dict.json"),
              os.path.join(ASSETS, "ui-strings-zh.json")):
        if os.path.exists(p):
            _lookup.update(rd(p))
    for name, kv in _en.items():
        tgt = {}
        for k, v in kv.items():
            if not isinstance(v, str):
                continue
            z = _lookup.get(v)
            if z and z.strip() != v.strip():
                tgt[k] = z
        if tgt:
            wa_ns[name] = tgt
    # 产品名与普通名词共用英文原文时，只能按 i18n key 区分。
    # 与英文相同的值表示撤销全局译文，保留该产品/套餐名原文。
    key_override_path = os.path.join(ZH_IN, "webapp-key-overrides.json")
    if os.path.exists(key_override_path):
        key_override_count = 0
        for name, overrides in rd(key_override_path).items():
            for k, z in overrides.items():
                if name not in _en or k not in _en[name]:
                    raise KeyError("未知的 webapp key 覆盖: %s.%s" % (name, k))
                if z == _en[name][k]:
                    if name in wa_ns:
                        wa_ns[name].pop(k, None)
                else:
                    wa_ns.setdefault(name, {})[k] = z
                key_override_count += 1
        L("    Webapp 精确键覆盖:", key_override_count, "条")
else:
    L("    ⚠ 缺少 data/webapp-en.json，先跑 tools/analyze_webapp.py")

wr(os.path.join(ASSETS, "webapp-i18n.json"), wa_ns, indent=0, sort=True)
L("    assets/webapp-i18n.json: %s 条 / %d 个命名空间 (%.2f MB)"
  % (format(sum(len(v) for v in wa_ns.values()), ","), len(wa_ns),
     os.path.getsize(os.path.join(ASSETS, 'webapp-i18n.json')) / 1048576))

# ───────────────────────── 5. windsurf 扩展贡献点（兼容旧路线） ─────────────────────────
g7 = rd(os.path.join(ZH_IN, "g7.json")) if os.path.exists(os.path.join(ZH_IN, "g7.json")) else {}
plan = rd(os.path.join(ASSETS, "ext-manifest.json")) if os.path.exists(os.path.join(ASSETS, "ext-manifest.json")) else {}
enmap = rd(os.path.join(ASSETS, "ext-manifest.en.json")) if os.path.exists(os.path.join(ASSETS, "ext-manifest.en.json")) else {}

pkgzh = {}
for ext, entries in plan.items():
    for e in entries:
        en = enmap.get(e["key"])
        z = g7.get(en) if en else None
        if z:
            pkgzh[e["key"]] = z
wr(os.path.join(TRANS_EXT, "windsurf.i18n.json"),
   {"": ["Devin 简体中文补丁 —— 内置扩展贡献点译文", "Do not edit this file."],
    "version": "1.0.0",
    "contents": {"package": pkgzh}})
L("\n[5] 扩展贡献点译文:", len(pkgzh), "条 / 字段", sum(len(v) for v in plan.values()))

# ───────────────────────── 6. 汇总 ─────────────────────────
meta = {
    "devinDir": _APP,
    "langpackDir": _LP,
    "langpackVersion": None,
    "nlsPairs": n_supp,
    "nlsFiles": len(supp),
    "nlsTotal": total,
    "uiDict": len(ui),
    "webappDict": len(webapp_zh),
    "webappI18n": sum(len(v) for v in wa_ns.values()),
    "extFields": sum(len(v) for v in plan.values()),
    "extZh": len(pkgzh),
}
try:
    meta["langpackVersion"] = rd(os.path.join(_LP, "package.json")).get("version")
except Exception:
    pass
wr(os.path.join(_DATA, "meta.json"), meta, indent=1)
L("\n" + json.dumps(meta, ensure_ascii=False, indent=1))

with open(os.path.join(_DATA, "build.log"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(log))


