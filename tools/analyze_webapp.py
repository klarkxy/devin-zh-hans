# -*- coding: utf-8 -*-
"""
analyze_webapp.py — 分析新版 Agent UI（devin-webapp-host）的 i18n 资源与缺口

背景（Devin 3.11 起）：
  Agent 侧边栏由 `out/vs/workbench/devin-webapp-host/` 承担（87 MB / 约 1,877 chunk），
  由 `workbench.desktop.main.js` 用 `import("@devin/webapp-host")` 挂进 workbench 渲染进程。

  它自建 i18next，`entry-host-editor-mode-menu-*.js` 里：

      let n = { en: { translation: t ? … : mu, review: hu } }
      … Mt.use(Mn).init({ resources: n, lng: "en", fallbackLng: "en",
                          ns: ["translation","review"], defaultNS: "translation" })
      gu = [{code:"en"}, {code:"ja",…}, {code:"pt",…}, {code:"es",…}]     ← 没有中文

  **关键：资源是嵌套命名空间结构**，不是扁平 key：

      yl = { composerTips: ma, nav: $a, common: ga, apps: …, … }
      ma = { newSession: "Tip: Start a new session (<shortcut/>)", … }
      $a = { newSession: "New session", security: "Security", … }

  i18next 查的是 "composerTips.newSession"。早期版本按 `key: 值` 正则扫出 4,575 个
  扁平 key 并注入成 { "newSession": … }，**永远匹配不到**，等于一条都没生效。
  现在改为调用 `tools/extract_webapp_i18n.js`（结构化解析，不执行代码）拿到真正的树。

输出：
    tools/data/webapp-en.json    {namespaces: {ns: {key: en}}, stats}
    tools/data/webapp.json       + covered / missing / todo
    tools/data/webapp.md         覆盖率报告
"""
import json, os, re, subprocess, sys, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import DEVIN_APP as _APP, DATA as _DATA, DICT as _DICT, PLUGIN as _PLUGIN  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EN_JSON = os.path.join(_DATA, "webapp-en.json")


def load_dict():
    """英文原文 -> 中文。优先级：webapp 专用 > 人工校订 > 通用词表。"""
    d = {}
    for p in (os.path.join(_PLUGIN, "assets", "ui-dict.json"),
              os.path.join(_PLUGIN, "assets", "ui-strings-zh.json")):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                d.update(json.load(f))
    for p in (os.path.join(_DICT, "ui-common-zh.json"),
              os.path.join(_DICT, "webapp-zh.json")):
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                dd = json.load(f)
                dd.pop("_comment", None)
                d.update(dd)
    # w*.json 分批译文：尚未折叠进 dict/webapp-zh.json 时也认成已覆盖。
    for p in sorted(glob.glob(os.path.join(_DATA, "zh", "webapp", "w*.json"))):
        with open(p, "r", encoding="utf-8") as f:
            d.update(json.load(f))
    return d


def main():
    rc = subprocess.call(["node", os.path.join(os.path.dirname(__file__), "extract_webapp_i18n.js")])
    if rc != 0 or not os.path.exists(EN_JSON):
        print("✗ 提取 webapp i18n 资源失败")
        return 1

    en = json.load(open(EN_JSON, encoding="utf-8"))
    ns = en["namespaces"]
    stats = en["stats"]

    dict_ = load_dict()

    # 统计：按 key 计数，同时按英文原文去重
    total_keys = 0
    covered_keys = 0
    uniq_en = set()
    uniq_hit = set()
    missing = []
    todo = []

    for name, kv in ns.items():
        for k, v in kv.items():
            if not isinstance(v, str):
                continue
            total_keys += 1
            uniq_en.add(v)
            z = dict_.get(v)
            if z and z.strip() != v.strip():
                covered_keys += 1
                uniq_hit.add(v)
            else:
                missing.append({"ns": name, "key": k, "en": v})
                if 2 <= len(v) <= 200 and re.search(r"[A-Za-z]", v):
                    todo.append(v)

    todo = sorted(set(todo))
    out = {
        "chunk": stats.get("chunk"),
        "namespaces": len(ns),
        "totalKeys": total_keys,
        "uniqueEnglish": len(uniq_en),
        "coveredKeys": covered_keys,
        "coveredEnglish": len(uniq_hit),
        "missing": len(missing),
        "todo": len(todo),
        "missingList": missing,
    }
    with open(os.path.join(_DATA, "webapp.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    with open(os.path.join(_DATA, "webapp-todo.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({e: "" for e in todo}, f, ensure_ascii=False, indent=0)

    A = ["# webapp-host（新版 Agent UI）i18n 资源与词典覆盖\n",
         "- i18n chunk: `%s`" % stats.get("chunk"),
         "- 命名空间: **%d**" % len(ns),
         "- 叶子 key: **%s**" % format(total_keys, ","),
         "- 去重后英文原文: **%s**" % format(len(uniq_en), ","),
         "- 词典已覆盖: **%s** (%.1f%%)"
         % (format(len(uniq_hit), ","), len(uniq_hit) / max(len(uniq_en), 1) * 100),
         "- 仍缺中文: **%s**（其中可整串替换 %s）"
         % (format(len(uniq_en) - len(uniq_hit), ","), format(len(todo), ",")),
         "\n## 最大的命名空间\n", "| 条数 | 命名空间 |", "|---:|---|"]
    top = sorted(ns.items(), key=lambda kv: -len(kv[1]))[:15]
    for k, v in top:
        A.append("| %d | `%s` |" % (len(v), k))
    A += ["\n## 缺口样例（前 60）\n", "| 命名空间 | key | 英文 |", "|---|---|---|"]
    seen = set()
    n = 0
    for m in missing:
        if m["en"] in seen:
            continue
        seen.add(m["en"])
        A.append("| `%s` | `%s` | %s |"
                 % (m["ns"], m["key"], m["en"].replace("|", "\\|")[:100]))
        n += 1
        if n >= 60:
            break
    with open(os.path.join(_DATA, "webapp.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(A) + "\n")

    print("OK ns=%d keys=%d uniqueEn=%d covered=%d missing=%d todo=%d"
          % (len(ns), total_keys, len(uniq_en), len(uniq_hit),
             len(uniq_en) - len(uniq_hit), len(todo)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
