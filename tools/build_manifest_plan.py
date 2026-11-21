# -*- coding: utf-8 -*-
"""
build_manifest_plan.py — 生成「内置扩展贡献点」的本地化计划

为什么需要这一层：
  Devin 内置的 5 个扩展（windsurf / windsurf-dev-containers / windsurf-remote-devin /
  windsurf-remote-openssh / windsurf-remote-wsl）的 package.json 里，命令标题、设置项
  说明全部是**硬编码英文**，且目录下没有 package.nls*.json，所以语言包机制完全无效。

  VS Code 的解析顺序（workbench.desktop.main.js 的 getLocalizedMessages）是：

      1. 语言包 bundle（translations[`${publisher}.${name}`]）
      2. 扩展目录下的 package.nls.<language>.json   ← 例如 package.nls.zh-cn.json
      3. 扩展目录下的 package.nls.json              ← 英文默认值

  走第 2 条最省事：只要把 package.json 里的字符串换成 `%key%`，再放两个
  package.nls.json / package.nls.zh-cn.json，不需要注册语言包 bundle，
  也不需要碰 languagepacks.json。

产物（都在 assets/，随 VSIX 分发，由 extension.js 在启动时落地）：
    assets/ext-manifest.json      {"<扩展名>": [{"path":[...JSON 指针...], "key":"..."}]}
    assets/ext-manifest.en.json   {key: 英文默认值}
    assets/ext-manifest.zh.json   {key: 中文}
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import DEVIN_APP as _APP, DATA as _DATA, DICT as _DICT, ASSETS as _ASSETS  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXT_ROOT = os.path.join(_APP or "", "extensions")
NAMES = [
    "windsurf",
    "windsurf-dev-containers",
    "windsurf-remote-devin",
    "windsurf-remote-openssh",
    "windsurf-remote-wsl",
]


def keyfor(ext, path):
    """把 JSON 指针变成稳定的 nls key（点分，不含 % 和空格）。"""
    parts = []
    for p in path:
        if isinstance(p, int):
            parts.append(str(p))
        else:
            s = str(p).replace(" ", "_")
            parts.append(s)
    return ext + "." + ".".join(parts)


def collect(ext, pkg, nls_en=None):
    """返回 [(path, 英文)]，path 是 package.json 里的 JSON 指针。

    字段可能是两种形态：
      1. 明文英文 —— 全新安装或 Devin 更新后的原始状态；
      2. %key% —— 本插件（或上一版）已落地过，package.nls.json 里存有英文默认值。
         Devin 更新会重写 package.json（恢复明文），但如果扩展没随版本变化，
         已落地的 %key% 会保留；此时从 package.nls.json 反查英文，计划保持完整。
    """
    nls_en = nls_en or {}

    def resolve(v):
        """%key% → package.nls.json 里的英文默认值；解析不到返回 None（跳过）。"""
        if not (isinstance(v, str) and v.startswith("%") and v.endswith("%")):
            return v
        return nls_en.get(v[1:-1])

    out = []
    c = pkg.get("contributes") or {}

    for i, cmd in enumerate(c.get("commands") or []):
        base = ["contributes", "commands", i]
        for f in ("title", "category"):
            v = resolve(cmd.get(f))
            if isinstance(v, str) and not v.startswith("%"):
                out.append((base + [f], v))

    for i, a in enumerate(c.get("authentication") or []):
        v = resolve(a.get("label"))
        if isinstance(v, str) and not v.startswith("%"):
            out.append((["contributes", "authentication", i, "label"], v))

    cfg = c.get("configuration")
    cfg = cfg if isinstance(cfg, list) else ([cfg] if isinstance(cfg, dict) else [])
    for i, b in enumerate(cfg):
        base = ["contributes", "configuration"] + ([i] if isinstance(c.get("configuration"), list) else [])
        v = resolve(b.get("title"))
        if isinstance(v, str) and not v.startswith("%"):
            out.append((base + ["title"], v))
        for pk, pv in (b.get("properties") or {}).items():
            for f in ("markdownDescription", "description"):
                v = resolve(pv.get(f))
                if isinstance(v, str) and not v.startswith("%"):
                    out.append((base + ["properties", pk, f], v))
                    break

    return out


def main():
    if not os.path.isdir(EXT_ROOT):
        print("✗ 未找到内置扩展目录:", EXT_ROOT)
        return 1

    # 词表输入目录固定（不受 DEVIN_ZH_DATA 输出重定向影响）
    zh_in = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "zh")
    with open(os.path.join(zh_in, "g7.json"), "r", encoding="utf-8") as f:
        zh_by_en = json.load(f)

    plan, en_map, zh_map, stats = {}, {}, {}, {}
    for ext in NAMES:
        p = os.path.join(EXT_ROOT, ext, "package.json")
        if not os.path.exists(p):
            print("  · 跳过（不存在）:", ext)
            continue
        with open(p, "r", encoding="utf-8") as f:
            pkg = json.load(f)
        # 已落地过的扩展：package.nls.json 里有英文默认值，%key% 从这里反查
        nls_en = {}
        nls_path = os.path.join(EXT_ROOT, ext, "package.nls.json")
        if os.path.exists(nls_path):
            try:
                with open(nls_path, "r", encoding="utf-8") as f:
                    nls_en = json.load(f)
            except Exception:
                nls_en = {}
        fields = collect(ext, pkg, nls_en)
        entries = []
        miss = []
        for path, en in fields:
            k = keyfor(ext, path)
            entries.append({"path": path, "key": k})
            en_map[k] = en
            z = zh_by_en.get(en)
            if z:
                zh_map[k] = z
            else:
                miss.append(en)
        plan[ext] = entries
        stats[ext] = {"fields": len(entries), "zh": len(entries) - len(miss)}
        if miss:
            print("  ⚠ %s 缺译文 %d 条: %s" % (ext, len(miss), miss[:3]))

    os.makedirs(_ASSETS, exist_ok=True)
    # 受限 shell 无法写 assets/ 时，用 DEVIN_ZH_ASSETS 重定向输出目录
    out_assets = os.environ.get("DEVIN_ZH_ASSETS") or _ASSETS
    os.makedirs(out_assets, exist_ok=True)
    for name, obj in (("ext-manifest.json", plan),
                      ("ext-manifest.en.json", en_map),
                      ("ext-manifest.zh.json", zh_map)):
        with open(os.path.join(out_assets, name), "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, ensure_ascii=False, indent=0, sort_keys=True)

    print("OK 扩展字段 %d 个, 英文 %d 条, 中文 %d 条"
          % (sum(v["fields"] for v in stats.values()), len(en_map), len(zh_map)))
    for k, v in stats.items():
        print("   %-26s %3d 字段 / %3d 有中文" % (k, v["fields"], v["zh"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
