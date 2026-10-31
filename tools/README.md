# tools

仓库级工具。所有脚本通过 [`_paths.py`](_paths.py) 解析路径，**不写死任何用户目录**。

本仓库只维护一个插件，**仓库根目录就是插件根目录**，所以脚本里没有「插件选择」这类参数。

## 路径解析

| 环境变量 | 用途 | 默认 |
|---|---|---|
| `DEVIN_INSTALL` | Windows 安装根目录（含 `Devin.exe`）；扩展与 `verify_layers.js` 在 macOS 也接受 `.app` 或其 `Contents` 目录 | Windows 标准安装目录；macOS 为 `/Applications/Devin.app`、`~/Applications/Devin.app` |
| `DEVIN_HOME` | Devin 用户目录 | `~/.devin` |
| `DEVIN_PLUGIN_REPO` | 发布目标仓库 | `klarkxy/devin-zh-hans` |

`DEVIN_INSTALL` / `DEVIN_HOME` 同时被 `extension.js` 尊重，这是 `verify_layers.js`
能在沙盒副本上验证落地逻辑的关键。
其他历史 Python 分析工具的 `_paths.py` 仍以 Windows 安装树为基础；macOS 安装与验证
请使用扩展、`verify_layers.js` 和下方不依赖安装的回归测试。

关键目录：

| 位置 | 说明 |
|---|---|
| `./`（仓库根） | 插件本体：`package.json` / `extension.js` / `assets/` / `dist/` / `translations/` |
| `tools/data/` | 中间数据（分析结果、译文、构建日志），会提交 |
| `tools/data/zh/` | 译文词表：`g1–g4`（历史 NLS 缺口）、`g6`（3.11 新增 NLS 缺口）、`g7`（内置扩展贡献点） |
| `tools/data/zh/webapp/` | webapp 文案译文，分批 `b00–b09` / `c00–c01` |
| `tools/dict/` | 人工维护的词表，会提交 |
| `build/` | VSIX 打包输出，**被 git 忽略** |
| `.verify/` | 验证沙盒，**被 git 忽略** |

## 构建流水线

顺序固定，后一步依赖前一步的产物：

```powershell
python tools/analyze_nls.py           # ① NLS 缺口
python tools/analyze_webapp.py        # ② Agent UI i18n 缺口
python tools/build_manifest_plan.py   # ③ 内置扩展贡献点计划
python tools/build_patch.py           # ④ 由词表生成 translations/ 与 assets/
python tools/build_dom.py             # ⑤ 生成 dist/devin-zh-dom.js
python tools/build_vsix.py            # ⑥ 打包
```

### ① `analyze_nls.py` — NLS 缺口分析

扫 `out/nls.keys.json` 与 `out/nls.messages.json`（两者顺序一一对应），
与已装官方语言包的 `contents` 做差集。

输出：

| 文件 | 内容 |
|---|---|
| `data/coverage.md` | 覆盖率报告（按源文件聚合、Devin 专有模块清单、样例） |
| `data/missing.json` | 完整缺口清单 `{file, key, en}` |
| `data/todo.json` | 按源文件分组的待译清单，**`build_patch.py` 的输入** |

用途：判断一次 Devin 更新引入了多少新字符串。3.11.216 → 缺口 162 条。

### ② `analyze_webapp.py` + `extract_webapp_i18n.js` — Agent UI 的 i18n 分析

`extract_webapp_i18n.js` 从 i18n 入口 chunk 里还原**带命名空间**的 en 资源树。

关键点：资源有两种写法，都必须扫。

```js
// ① 对象字面量
ma={sessionNav:`Tip: Move between sessions (<up/> / <down/>)`,…}
// ② 内联 JSON 字符串 —— 设置页 3,938 个 key 全在这里
Ss=JSON.parse(`{"displayLanguage":"Display language",…}`)
```

只扫 ① 会得到 8,189 个 key，设置页整页英文；两种都扫得到 **317 个命名空间 / 19,269 个 key**。
解析 ② 需要把模板字符串的转义还原成 JSON 层级（`\"`、`\uXXXX`），否则会
`Expecting ',' delimiter` / `Invalid \escape`。

脚本用**结构化解析**而不是 `vm` 执行 —— 这些字面量里夹着 IIFE 和跨 chunk 引用，
执行会抛 `n is not a function`。

产物 `data/webapp-en.json` 给 `analyze_webapp.py` 与 `build_patch.py` 共用。

输出：

| 文件 | 内容 |
|---|---|
| `data/webapp.json` | `{keys: [{key, en, chunk}], stats}` |
| `data/webapp.md` | 覆盖率报告 |
| `data/webapp-todo.json` | 待译清单 `{en: ""}` |

### ③ `build_manifest_plan.py` — 内置扩展贡献点计划

从 5 个扩展的 `package.json` 里提取所有可本地化字段的 JSON 指针，
配合 `data/zh/g7.json`（英文 → 中文）生成落地计划。

输出：

| 文件 | 内容 |
|---|---|
| `assets/ext-manifest.json` | `{扩展名: [{path: [...], key: "..."}]}` —— 要改成 `%key%` 的位置 |
| `assets/ext-manifest.en.json` | `{key: 英文默认值}` → 写成 `package.nls.json` |
| `assets/ext-manifest.zh.json` | `{key: 中文}` → 写成 `package.nls.zh-cn.json` |

key 是「扩展名 + JSON 指针」，例如
`windsurf.contributes.commands.0.title`，稳定且可读。

### ④ `build_patch.py` — 由词表生成插件产物

输入 `data/todo.json` + `data/zh/g*.json` + `tools/dict/webapp-zh.json`，产物直接写进仓库根：

```
translations/main.i18n.json              合并版语言包（官方 + 补充）→ 21,161 条
translations/extensions/windsurf.i18n.json
assets/ui-dict.json                      DOM 通用词典（官方英文 → 中文）
assets/ui-strings-zh.json                DOM 界面词典（含 webapp 专有文案）
assets/webapp-i18n.json                  webapp i18next 覆盖表（嵌套，按 i18n key）
```

两个要点：

- **剔除死条目**：官方语言包自带约 1,000 条本构建已不存在的 key，用当前
  `out/nls.keys.json` 精确剔除，合并版从 22,003 降到 21,161，全部可查。
- **DOM 词典与 i18next 表不能用同一份**：DOM 层按键（英文原文）整串匹配，
  所以 `{{...}}` 插值模板必须排除（渲染后已被替换成实际值）；
  i18next 表反之要保留它们。脚本里分两份产出。

**前提**：本机已安装官方简体中文语言包（合并版的底子来自它）。

### ⑤ `build_dom.py` — DOM 运行时

把 `assets/ui-dict.json` + `assets/ui-strings-zh.json` 与正则规则打成一个自包含 IIFE，
输出 `dist/devin-zh-dom.js`（约 1.7 MB，随 VSIX 分发）。

设计要点写在 `docs/architecture.md` 第 4 层。改词典后**必须重跑这一步**，
否则 `dist/` 里还是旧词典（`extension.js` 只负责把它复制到窗口目录，不做生成）。

### ⑥ `build_vsix.py` — 打包

```powershell
python tools/build_vsix.py              # 输出到 build/
python tools/build_vsix.py --dry-run    # 只列出会打包哪些文件
```

把仓库根下**属于插件的那部分**塞进 VSIX 的 `extension/`，仓库级目录
（`tools/`、`docs/`、`.github/`、`build/`、`.verify/`）一律排除。
`dist/` 是插件自带的运行时文件，**必须提交**，不要和打包产物 `build/` 混淆。

## 验证

### `test_installation.js` — 跨平台回归测试（无需安装 Devin）

```sh
node --test tools/test_installation.js
node tools/test_dom_runtime.js
```

使用临时 fixture 和假的 `vscode` 模块运行真实扩展代码：
覆盖 macOS 大小写敏感路径、当前 `appRoot`、系统/用户安装目录与环境变量覆盖，
并保留 Windows 三种安装路径探测。两种目录布局均验证四层落地、重复应用、
同名文件分别备份、新建文件清理及卸载回滚；也验证备份失败与备份文件丢失场景。
CI 在 Ubuntu、Windows、macOS 上运行，不访问实际应用或用户配置。

### `verify_layers.js` — 四层落地验证（不启动 Devin）

```powershell
node tools/verify_layers.js              # 沙盒干跑：列出会写哪些文件
node tools/verify_layers.js --apply      # 沙盒写入 + 断言
node tools/verify_layers.js --apply --keep   # 复用沙盒，验证幂等（第二次应零写入）
node tools/verify_layers.js --real       # 对真实安装执行
```

原理：把 `resources/app`（macOS 为 `Contents/Resources/app`）里被本插件碰过的文件
+ 官方语言包（如有）复制到 `.verify/`，沙盒保留各平台实际目录结构，
用 `DEVIN_INSTALL` / `DEVIN_HOME` 指过去，再给 `extension.js` 喂一个假的 `vscode` 模块
直接调 `activate()` —— 验证的是**插件真实会执行的代码路径**，不是另写一份。

断言项：

```
· 语言包译文条数 ≥ 21,000，本插件补充的 162 条全部可查，windsurf bundle 已注册
· 5 个扩展共 254 个 %key%：未解析 0、缺中文 0
· webapp i18next 载荷存在、用 addResourceBundle("en","translation")、锚点保留、只有一份
· 两个窗口 HTML 已注入且运行时脚本存在
· product.json.checksums 自洽（沙盒里缺的受保护文件会跳过并注明）
```

未安装官方中文语言包时，验证扩展自带 `zh-cn` localizations 可用，而不是将其视为失败。
该脚本不检查 macOS 代码签名；修改 `.app` 资源后签名校验失效属于独立的风险。

### `verify_integrity.py` — 完整性/占位符/注入状态报告

检查四件事并输出 `data/verify-report.md`：

1. `product.json.checksums` 的 12 个文件实际哈希是否自洽
2. `%key%` 占位符能否在 `package.nls.json` 解析、且都有中文
3. 语言包 bundle 注册状态与本插件补充译文的可查性
4. webapp i18next 载荷与 DOM 注入的落地状态

这个脚本读的是**真实安装目录**，所以它反映的是「这台机器当前是否已落地」。
想验证插件能不能落地，用 `verify_layers.js`。

## 数据目录 `data/`

| 文件 | 说明 |
|---|---|
| `todo.json` / `missing.json` | NLS 分析结果（可重新生成） |
| `zh/g1..g4.json` | 历史 NLS 缺口的译文，格式 `{"English": "中文"}` |
| `zh/g6.json` | 3.11.216 新增缺口的译文（162 条） |
| `zh/g7.json` | 内置扩展贡献点的译文（254 条字段 / 129 条去重英文） |
| `zh/webapp/b*.json` `c*.json` | webapp 文案译文，合并进 `tools/dict/webapp-zh.json` |
| `webapp.json` / `webapp.md` | webapp i18n 分析结果 |
| `coverage.md` / `verify-report.md` | 报告产物 |
| `meta.json` / `build.log` | 构建元信息与日志 |

合并 webapp 译文：

```powershell
python -c "import json,glob,os;d={};[d.update(json.load(open(p,encoding='utf-8'))) for p in sorted(glob.glob('tools/data/zh/webapp/*.json'))];json.dump(d,open('tools/dict/webapp-zh.json','w',encoding='utf-8',newline='\n'),ensure_ascii=False,indent=0,sort_keys=True);print(len(d))"
```

## 发版流程

```powershell
# 1. 改版本号（同时更新 CHANGELOG.md）
#    package.json 的 version

# 2. 本地验证
python tools/build_vsix.py
node tools/verify_layers.js --apply
python tools/release.py --dry-run

# 3. 提交并打 tag
git add -A; git commit -m "release: v1.1.0"
git tag v1.1.0; git push; git push --tags

# 4. CI 会自动构建并发布（.github/workflows/build.yml）
#    也可以本地手动发：
python tools/release.py
```

发布时上传**两个** asset：

| asset | 用途 |
|---|---|
| `devin-zh-hans-<version>.vsix` | 带版本号，用于归档与「我要指定版本」 |
| `devin-zh-hans.vsix` | **固定名**，每次发版覆盖 |

固定名是为了这条 URL 永久有效：

```
https://github.com/klarkxy/devin-zh-hans/releases/latest/download/devin-zh-hans.vsix
```

CI 会校验 **tag 与 `package.json` 的版本一致**，不一致直接失败。

## Devin 更新后的重做流程

```powershell
# ① 看新版缺了什么
python tools/analyze_nls.py            # 看 coverage.md 的「缺中文」数量
python tools/analyze_webapp.py         # 看 webapp.md 的「仍缺中文」数量

# ② 新缺口写进词表
#    NLS 缺口      -> tools/data/zh/g8.json（新建，格式同 g6）
#    webapp 文案   -> tools/data/zh/webapp/d*.json（新建，格式同 b00）
#    扩展贡献点    -> tools/data/zh/g7.json（覆盖式更新）
#    然后合并 webapp 译文（见上一节命令）

# ③ 重建并验证
python tools/analyze_nls.py && python tools/analyze_webapp.py
python tools/build_manifest_plan.py && python tools/build_patch.py && python tools/build_dom.py
node tools/verify_layers.js --apply
python tools/verify_integrity.py

# ④ 打包发版
python tools/build_vsix.py
```

若新版的锚点变了（`verify_layers.js` 报「webapp i18next 载荷已注入」失败），
按 `docs/internals.md` 第 5 节重新定位新的 i18n 初始化语句，更新 `extension.js` 里的
`HOST_ANCHOR`，并把 `@devin/webapp-host` 的加载路径（`WEBAPP_DIR`）核对一遍。
