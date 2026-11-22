# -*- coding: utf-8 -*-
"""
build_dom.py — 生成 DOM 翻译器 dist/devin-zh-dom.js

为什么需要这一层（Devin 3.11.216 起）：
  Agent 侧边栏不再是独立的 chat-client bundle，而是 `out/vs/workbench/devin-webapp-host/`
  这一套 rolldown 产物，由 `workbench.desktop.main.js` 用 `import("@devin/webapp-host")`
  挂进 **workbench 渲染进程**。也就是说 Agent UI 与编辑器外壳现在同处一个窗口。

  这带来两个后果：
    · 好消息：注入 workbench.html 的脚本现在能覆盖 Agent UI，不需要再改 chat-client。
    · 坏消息：它的文案来自运行时数据 + 2000 多个 chunk 里的字面量，语言包机制依然无效
      （它的 i18next 只有 en/ja/pt/es，没有 zh）。

  所以仍然需要窗口级 DOM 翻译器兜底。本脚本把词典和规则打进一个自包含的 IIFE。

词典来源：
    assets/ui-dict.json        官方语言包英文 -> 中文（约 1.9 万条，覆盖通用 VS Code 文案）
    assets/ui-strings-zh.json  人工/agent 翻译的 webapp 与界面短语（约 6.8 千条）

产物：
    dist/devin-zh-dom.js       随 VSIX 分发，由 extension.js 复制到窗口目录并注入 <script>
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _paths import PLUGIN as _PLUGIN, ASSETS as _ASSETS, DIST as _DIST, DICT as _DICT  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ───────────────────────── 运行时骨架 ─────────────────────────
RUNTIME = r"""/* devin-zh-dom.js — Devin 界面简体中文（DOM 层）
 *
 * 由 tools/build_dom.py 生成，请勿手改。
 * 只修改文本节点与输入框 placeholder，不触碰 React 状态、事件或输入内容。
 */
(function () {
  'use strict';
  if (window.__devinZhDom) { window.__devinZhDom.rescan(); return; }

  var DICT = __DICT__;
  var RULES = [];
  (function () {
    var raw = __RULES__;
    for (var i = 0; i < raw.length; i++) RULES.push([new RegExp(raw[i][0]), raw[i][1]]);
  })();

  /* 整棵子树都不碰的标签 */
  var SKIP_TAGS = {
    SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1, OPTION: 1,
    CODE: 1, PRE: 1, KBD: 1, SAMP: 1, VAR: 1, SVG: 1, CANVAS: 1, IFRAME: 1, OBJECT: 1,
    MATH: 1, VIDEO: 1, AUDIO: 1, MNEMONIC: 1
  };

  /* 跳过选择器：代码编辑器、终端、Agent 消息正文、输入框、显式声明不翻译的区域 */
  var SKIP_SEL = [
    '.monaco-editor', '.monaco-diff-editor', '.monaco-list-row .label-name',
    '.monaco-keybinding',
    '.xterm', '.xterm-helper-textarea', '.cm-editor', '.cm-content', '.ace_editor',
    '.view-lines', '.view-line', '.minimap',
    '[data-streamdown]', '.prose', '.markdown-body',
    '[data-transcript-row-key]', '[data-testid*="message-content"]',
    '[data-testid*="transcript"]', '[data-slate-editor]', '[data-slate-node]',
    '[data-devin-input-box]', '[data-testid*="terminal-output"]',
    '[contenteditable="true"]', '[translate="no"]', '.notranslate',
    '[data-devin-zh-skip]'
  ].join(',');

  var CJK = /[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\uFF00-\uFFEF\u3000-\u303F]/;

  var hits = 0;
  var seen = null;
  if (typeof WeakSet === 'function') seen = new WeakSet();
  var visited = [];

  function isVisited(node) {
    if (seen) return seen.has(node);
    return visited.indexOf(node) >= 0;
  }
  function mark(node) {
    if (seen) seen.add(node);
    else if (visited.length < 400000) visited.push(node);
  }

  function shouldSkip(node) {
    for (var el = node.parentElement; el; el = el.parentElement) {
      if (SKIP_TAGS[el.tagName]) return true;
      if (el.isContentEditable) return true;
      if (el.getAttribute && el.getAttribute('translate') === 'no') return true;
      if (el.matches && el.matches(SKIP_SEL)) return true;
    }
    return false;
  }

  function lookup(key) {
    var out = DICT[key];
    if (out !== undefined) return out;
    for (var i = 0; i < RULES.length; i++) {
      var re = RULES[i][0];
      re.lastIndex = 0;
      if (re.test(key)) return key.replace(re, RULES[i][1]);
    }
    return undefined;
  }

  function translateNode(node) {
    if (!node || isVisited(node)) return;
    var text = node.nodeValue;
    if (!text) return;
    var key = text.trim();
    if (!key || key.length > 200) return;
    if (CJK.test(key)) return;            /* 已经是中文（或含中文）就不动，防止二次翻译 */
    if (!/[A-Za-z]/.test(key)) return;

    var out = lookup(key);
    if (out === undefined || out === key) return;
    if (shouldSkip(node)) return;

    mark(node);
    /* 保留原有的前后空白，避免破坏 inline 布局 */
    var lead = text.slice(0, text.indexOf(key));
    var tail = text.slice(text.indexOf(key) + key.length);
    node.nodeValue = lead + out + tail;
    hits++;
  }

  /* 只翻译输入框的 placeholder，不读取或修改输入内容。 */
  function translatePlaceholder(el) {
    if (!el || !el.getAttribute) return;
    if (el.isContentEditable || el.getAttribute('translate') === 'no') return;
    if (el.matches && el.matches(SKIP_SEL)) return;
    if (shouldSkip(el)) return;
    var text = el.getAttribute('placeholder');
    if (!text) return;
    var key = text.trim();
    if (!key || key.length > 200 || CJK.test(key) || !/[A-Za-z]/.test(key)) return;
    var out = lookup(key);
    if (out === undefined || out === key) return;
    var lead = text.slice(0, text.indexOf(key));
    var tail = text.slice(text.indexOf(key) + key.length);
    el.setAttribute('placeholder', lead + out + tail);
    hits++;
  }

  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) { translateNode(root); return; }
    if (root.nodeType !== 1) return;
    translatePlaceholder(root);
    if (root.querySelectorAll) {
      var fields = root.querySelectorAll('input[placeholder],textarea[placeholder]');
      for (var i = 0; i < fields.length; i++) translatePlaceholder(fields[i]);
    }
    if (SKIP_TAGS[root.tagName]) return;
    if (root.matches && root.matches(SKIP_SEL)) return;
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        return n.nodeValue && n.nodeValue.trim()
          ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    var n;
    while ((n = walker.nextNode())) translateNode(n);
  }

  /* 批量调度：MutationObserver 回调里可能一次来几百个节点，按帧切片处理 */
  var queue = [];
  var scheduled = false;

  function flush() {
    scheduled = false;
    var batch = queue.slice(0, 200);
    queue = queue.slice(200);
    for (var i = 0; i < batch.length; i++) walk(batch[i]);
    if (queue.length) schedule([]);
  }

  function schedule(nodes) {
    for (var i = 0; i < nodes.length; i++) queue.push(nodes[i]);
    if (scheduled) return;
    scheduled = true;
    (window.requestAnimationFrame || window.setTimeout)(flush, 16);
  }

  function rescan() {
    if (seen) seen = new WeakSet();
    else visited = [];
    walk(document.body);
  }

  function observe() {
    if (!window.MutationObserver) return;
    new MutationObserver(function (records) {
      var add = [];
      for (var i = 0; i < records.length; i++) {
        var m = records[i];
        if (m.type === 'characterData') {
          if (m.target && m.target.parentElement) add.push(m.target);
        } else if (m.type === 'attributes') {
          add.push(m.target);
        } else {
          for (var j = 0; j < m.addedNodes.length; j++) add.push(m.addedNodes[j]);
        }
      }
      if (add.length) schedule(add);
    }).observe(document.documentElement, {
      childList: true, subtree: true, characterData: true,
      attributes: true, attributeFilter: ['placeholder']
    });
  }

  window.__devinZhDom = {
    rescan: rescan,
    hits: function () { return hits; },
    size: function () { return Object.keys(DICT).length; }
  };

  function boot() {
    walk(document.body);
    observe();
    /* webapp-host 挂载后布局会整体重排，补两轮扫描 */
    window.setTimeout(rescan, 400);
    window.setTimeout(rescan, 1500);
    window.setTimeout(rescan, 4000);
    /* 兜底巡检：会话列表 / 相对时间这类由 Intl.RelativeTimeFormat 生成、
       且会被 React 重新水合的文本，MutationObserver 偶尔收不到（节点被复用后
       只改 textContent 且不在我们观察的祖先链上）。低频补扫很便宜：只走 TreeWalker，
       已是中文的节点被 CJK 短路，实际开销接近零。 */
    var ticks = 0;
    var timer = window.setInterval(function () {
      ticks++;
      rescan();
      if (ticks >= 30) window.clearInterval(timer);   /* 约 60 秒后停 */
    }, 2000);
    console.log('[devin-zh] DOM 翻译器已加载：词典 ' + Object.keys(DICT).length
      + ' 条 / 规则 ' + RULES.length + ' 条');
  }

  if (document.body) boot();
  else document.addEventListener('DOMContentLoaded', boot);
})();
"""

# ───────────────────────── 正则规则 ─────────────────────────
# 只处理「整串匹配才安全」的模板：带数字/占位符的短语，整串替换比逐词替换稳。
#
# 相对时间是重点：webapp 用 `Intl.RelativeTimeFormat(locale)` 生成
# "yesterday" / "3 days ago" / "in 2 hours" 这类文案，locale 由 Devin 传入（en），
# 在 i18next 里查不到对应 key，只能在这一层按形状替换。
RULES = [
    # 相对时间（Intl.RelativeTimeFormat narrow/long 的英文输出）
    [r"^(\d+)\s+seconds?\s+ago$", "$1 秒前"],
    [r"^(\d+)\s+minutes?\s+ago$", "$1 分钟前"],
    [r"^(\d+)\s+hours?\s+ago$", "$1 小时前"],
    [r"^(\d+)\s+days?\s+ago$", "$1 天前"],
    [r"^(\d+)\s+weeks?\s+ago$", "$1 周前"],
    [r"^(\d+)\s+months?\s+ago$", "$1 个月前"],
    [r"^(\d+)\s+years?\s+ago$", "$1 年前"],
    [r"^in\s+(\d+)\s+seconds?$", "$1 秒后"],
    [r"^in\s+(\d+)\s+minutes?$", "$1 分钟后"],
    [r"^in\s+(\d+)\s+hours?$", "$1 小时后"],
    [r"^in\s+(\d+)\s+days?$", "$1 天后"],
    [r"^in\s+(\d+)\s+weeks?$", "$1 周后"],
    [r"^in\s+(\d+)\s+months?$", "$1 个月后"],
    [r"^in\s+(\d+)\s+years?$", "$1 年后"],
    [r"^yesterday$", "昨天"],
    [r"^today$", "今天"],
    [r"^tomorrow$", "明天"],
    [r"^just now$", "刚刚"],
    [r"^last week$", "上周"],
    [r"^next week$", "下周"],
    [r"^last month$", "上个月"],
    [r"^next month$", "下个月"],

    # 计数短语
    [r"^(\d+)\s+MCP\s+servers?$", "$1 个 MCP 服务器"],
    [r"^(\d+)\s+files?\s+changed$", "$1 个文件已更改"],
    [r"^(\d+)\s+files?$", "$1 个文件"],
    [r"^(\d+)\s+insertions?\(\+\)$", "$1 行插入(+)"],
    [r"^(\d+)\s+deletions?\(-\)$", "$1 行删除(-)"],
    [r"^(\d+)\s+issues?\s+found$", "发现 $1 个问题"],
    [r"^(\d+)\s+bugs?\s+found$", "发现 $1 个缺陷"],
    [r"^(\d+)\s+sessions?$", "$1 个会话"],
    [r"^(\d+)\s+comments?$", "$1 条评论"],
    [r"^(\d+)\s+results?$", "$1 个结果"],
    [r"^(\d+)\s+members?$", "$1 名成员"],
    [r"^(\d+)\s+repositories$", "$1 个仓库"],
    [r"^(\d+)\s+selected$", "已选 $1 项"],

    # ── 插值模板渲染后的形态 ──
    # webapp 里大量文案是 `{{count}} jobs queued` 这类 i18next 模板，
    # 渲染后变成 "3 jobs queued"，i18next 的 key 已经查不到，
    # 只能在这一层按渲染后的形状替换。
    [r"^(\d+)\s+jobs?\s+queued$", "已排队 $1 个任务"],
    [r"^(\d+)\s+jobs?\s+queued\s+·\s+oldest:\s*(.+)$", "已排队 $1 个任务 · 最早：$2"],
    [r"^(\d+)\s+days?$", "$1 天"],
    [r"^(\d+)\s+day\s+left$", "剩余 $1 天"],
    [r"^(\d+)\s+days\s+left$", "剩余 $1 天"],
    [r"^(\d+)\s+certificates?$", "$1 个证书"],
    [r"^Detected\s+·\s*(\d+)\s+certificates?\s+·\s*(.+)$", "已检测 · $1 个证书 · $2"],
    [r"^CA bundle saved\s*\((\d+)\s+certificates?\)$", "CA 证书包已保存（$1 个证书）"],
    [r"^Bundle updated\s+(.+)$", "证书包已更新 $1"],
    [r"^(\d+)\s+controls?$", "$1 项控制"],
    [r"^(\d+)\s+connections?$", "$1 个连接"],
    [r"^(\d+)\s+users?$", "$1 名用户"],
    [r"^(\d+)\s+seats?$", "$1 个席位"],
    [r"^(\d+)\s+images?$", "$1 个镜像"],
    [r"^(\d+)\s+credits?$", "$1 点额度"],
    [r"^(\d+)\s+plugins?$", "$1 个插件"],
    [r"^(\d+)\s+skills?$", "$1 个技能"],
    [r"^(\d+)\s+resources?$", "$1 个资源"],
    [r"^(\d+)\s+rules?$", "$1 条规则"],
    [r"^(\d+)\s+models?$", "$1 个模型"],
    [r"^Show\s+(\d+)\s+more\s+results?$", "再显示 $1 个结果"],
    [r"^Show\s+(\d+)\s+more\s+result$", "再显示 $1 个结果"],
    [r"^(\d+)\s+of\s+(\d+)\s+rows$", "$1 / $2 行"],
    [r"^Showing\s+(\d+)\s+of\s+(\d+)$", "显示 $1 / $2"],

    # 提示行前缀
    [r"^Tip:\s*(.+)$", "提示：$1"],
]

# 这些原文同时表示普通名词和产品/套餐名，DOM 无法区分上下文。
# 普通界面仍由 webapp 全局词表翻译，产品键由 webapp-key-overrides.json 精确保留。
DOM_CONTEXT_KEYS = {"Team", "Teams", "Max", "Pro"}


def load():
    d = {}
    p = os.path.join(_ASSETS, "ui-dict.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            d.update(json.load(f))
    p = os.path.join(_ASSETS, "ui-strings-zh.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            d.update(json.load(f))
    return d


def build():
    d = load()
    # 去掉空值与「译文等于原文」的条目
    d = {k: v for k, v in d.items()
         if k and v and k.strip() != v.strip() and k not in DOM_CONTEXT_KEYS}
    js = RUNTIME.replace("__DICT__", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    js = js.replace("__RULES__", json.dumps(
        [[r, s] for r, s in RULES], ensure_ascii=False, separators=(",", ":")))
    return js, len(d)


def main():
    os.makedirs(_DIST, exist_ok=True)
    js, n = build()
    out = os.path.join(_DIST, "devin-zh-dom.js")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(js)
    print("✓ %s" % out)
    print("    词典 %s 条, 规则 %d 条, %.2f MB"
          % (format(n, ","), len(RULES), os.path.getsize(out) / 1048576))
    return 0


if __name__ == "__main__":
    sys.exit(main())
