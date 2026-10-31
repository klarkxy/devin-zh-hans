# 架构：为什么汉化要分四层

这个插件不是普通语言包。Devin Desktop 的界面由**四个互不相通的字符串来源**拼成，
任何单一机制都只能覆盖其中一部分。

## 四层与各自的覆盖面

| 层 | 覆盖 | 机制 | 生效时机 |
|---|---|---|---|
| **1. 语言包** | 菜单栏、命令面板、设置界面、活动栏、状态栏、右键菜单、对话框 | 合并版 `main.i18n.json` 写进官方 zh-hans 语言包 | 启动最早期 |
| **2. 扩展贡献点** | 内置 5 个 Devin 扩展的命令标题、设置项标题与说明（254 个字段） | `package.nls.json` + `package.nls.zh-cn.json` + `%key%` | 启动早期 |
| **3. Agent UI i18next** | Agent 侧边栏、会话窗口与设置页的 i18n 文案（11,413 条） | 追加 `addResourceBundle("en","translation",{…})` | 窗口加载 |
| **4. DOM 翻译器** | 运行时数据拼出来的其余文案 | 窗口 HTML 注入脚本 + TreeWalker + MutationObserver | 窗口加载后持续 |

## 第 1 层：语言包，补齐官方缺口

Devin 是 VS Code fork，继承完整 NLS 机制，本机已装官方简体中文语言包。实测覆盖率：

```
全部 NLS 字符串   21,161
官方语言包已译    20,999   ← 99.2%
缺中文               162   ← 本插件补齐
```

关键是**这 162 条无法用 `contributes.localizations` 单独提供**：VS Code 在同一 locale 下
按扩展顺序合并 `translations`，官方包 `ms-ceintl.*` 排序在后会把我们的 `vscode` bundle 盖掉。
所以扩展激活时会把合并版直接写进已安装的官方语言包。

> 注：NLS 默认英文是**内联**在 `workbench.desktop.main.js` 里的，`out/nls.messages.json`
> 运行时并不加载 —— 所以「改 `nls.messages.json`」这条路上不通，只能走语言包。

合并版同时**剔除死条目**：官方语言包自带约 1,000 条本构建已不存在的 key（Devin 每次升级都会变），
它们永远不会被查到，删掉只是减重。判定依据是当前构建的 `out/nls.keys.json`。

## 第 2 层：扩展贡献点，只能改文件

内置的 5 个 Devin 扩展全部把命令标题与设置说明硬编码在 `package.json` 里，
且目录下**没有** `package.nls*.json`，`localize` / `l10n.t` 调用数为 0。
语言包机制对它们完全无效。

VS Code 解析扩展 manifest 的顺序（`workbench.desktop.main.js` 的 `getLocalizedMessages`）：

```
1. 语言包 bundle：translations[`${publisher}.${name}`]
2. 扩展目录：package.nls.<language>.json     ← 例如 package.nls.zh-cn.json
3. 扩展目录：package.nls.json                ← 英文默认值
```

本插件走第 2 条：把 `package.json` 里 254 个字符串换成 `%key%`，写两个 nls 文件。
**不需要注册语言包 bundle，也不需要碰 `languagepacks.json`** —— 这比 1.0.x 的路线少一个
容易出错的环节（旧路线要往 `languagepacks.json` 里补条目，还要小心别伪造 hash）。

**这一层要写安装目录，但是安全的**：`product.json.checksums` 只覆盖 12 个文件，
`extensions/` 整个目录不在其中。

## 第 3 层：Agent UI 的 i18next

这是 1.1.0 相对 1.0.x 最大的变化。

**Devin 3.11 起，Agent 侧边栏换了实现。** 以前是 `windsurf-chat-client/index.js`（25 MB 单文件），
现在是 `out/vs/workbench/devin-webapp-host/`：

```
out/vs/workbench/devin-webapp-host/
    index.js         ← 442 字节的稳定入口，被 workbench 用 import("@devin/webapp-host") 加载
    assets/*.js      ← 1,877 个 chunk，约 91 MB
    splash.html      ← 启动占位
    index.css
```

`workbench.desktop.main.js` 里：

```js
let n = await import("@devin/webapp-host");
c = n.installDevinHost(CLn(t, a, this.instantiationService, …))
```

也就是说 **Agent UI 现在和编辑器外壳同处一个渲染进程**（以前是独立窗口）。
这带来两个后果：

- 好消息：注入 `workbench.html` 的脚本能覆盖 Agent UI，不需要再改 chat-client bundle。
- 但语言包机制依然无效：它的文案来自运行时数据 + 1,800 个 chunk 里的字面量。

它的 i18n 结构（`entry-host-editor-mode-menu-*.js`）：

```js
resources: { en: { translation: yl, review: lu } }, lng: "en", fallbackLng: "en"
gu = [{code:"en"},
      {code:"ja", translation: () => import("./ja-Cd26s5QO.js"), …},
      {code:"pt", …}, {code:"es", …}]
```

**四份资源，没有中文。** 初始化入口：

```js
Mt.isInitialized || Eu()
```

本插件把它原地扩成：

```js
Mt.isInitialized||Eu(),
Mt.addResourceBundle("en","translation",{ /* 中文按英文 key */ },!0,!0)
```

为什么这么写而不是新增一个 zh locale：

- `addResourceBundle(…, !0, !0)` 是**深合并**（第三参数 deep、第四参数 overwrite），
  语义正好等于「用中文覆盖这些英文值」；
- 不碰 `lng`、不碰 `gu` 语言列表、不碰任何组件代码，ja / pt / es 用户零影响；
- 载荷用 `/*devin-zh*/ … /*/devin-zh*/` 标记包住，重复激活时**原地替换而不是叠加**
  （否则每次启动都会把上一版词表再套一层）。

这个 chunk 在 `product.json.checksums` 里吗？**不在** —— 清单里是
`vs/workbench/devin-webapp-host/index.js`（那个 442 字节的入口），不是 `assets/` 下的 chunk。
不过第 4 层改的 html 在清单里，所以哈希同步逻辑照旧要跑。

## 第 4 层：DOM 翻译器，兜住最后一段

即使有了第 3 层，仍有一批文案不走 i18next：运行时数据（会话标题、仓库名、动态状态）、
只在少数 chunk 里硬编码的 props、以及模板被拆成多个文本节点的句子。
这一层是唯一能覆盖它们的办法。

```
往 workbench.html / sessions.html 各插一行
    <script src="./devin-zh-dom.js"></script>
+ 生成 devin-zh-dom.js（TreeWalker + MutationObserver + 25,999 条词典 + 22 条正则）
+ 同步更新这两个 html 的 checksums
```

CSP 是 `script-src 'self'`，同目录外链脚本合法；Trusted Types 只约束 `innerHTML`，
翻译器只改 `nodeValue`，不触发。

设计要点：

- **CJK 短路**：节点里已有中文就不处理，避免二次翻译和把中英混排搞乱。
- **保留前后空白**：`"  New session  "` → `"  新建会话  "`，不破坏 inline 布局。
- **按帧切片**：MutationObserver 一次可能来几百个节点，队列 + `requestAnimationFrame` 批处理。
- **挂载后补扫**：webapp-host 挂载会整体重排，启动后 400 ms 与 1500 ms 各补一轮。

**刻意不翻译**：代码编辑器、终端、**Agent 消息正文**、输入框、`[contenteditable]`、`[translate="no"]`
—— 不碰代码，也不碰用户与 Agent 的对话内容。

## 落地顺序与时序约束

```
用户装 VSIX
   ↓
第一次启动   VS Code 读语言包（还未落地）→ 界面基本中文但缺 162 条
             ↓ 启动后期扩展激活 → 落地语言包 / 内置扩展 / webapp i18next / 注入 DOM
第二次启动   全部生效
```

语言包与窗口脚本都在启动**早期**被读取，而扩展激活在**后期**（`onStartupFinished`）。
因此首次安装需要重启一次 —— 这也是 VS Code 装语言包的固有节奏。

之后每次启动扩展都会静默自检并修复（幂等），所以 Devin 自动更新覆盖文件后不需要手动处理。

## 完整性校验的处理

`product.json.checksums` 保护 12 个文件（3.11 比 3.10 多了
`vs/workbench/devin-webapp-host/index.js`），其中两个是我们注入脚本的窗口 HTML。
每次写完**遍历全部条目**重算哈希（不写死条目列表，Devin 增减受保护文件都不会漏）。
`product.json` 自身不在 checksums 内，因此自洽。

唯一会看到「Devin 安装似乎损坏」的情况：**在 Devin 运行期间手动改过受保护文件** ——
此时当次启动的检查早于扩展激活，会弹一次，下次启动即恢复。

## 备份与回滚

所有写文件操作前会记录到 `~/.devin/devin-zh-backups/files-v2/manifest.json`：
键为目标完整路径，值为原文件备份路径（以目标完整路径的 SHA-256 命名），
或 `null`（原来不存在，由插件新建）。备份失败会中止对应修改，不再忽略失败继续写入。

这样不同扩展的 `package.json`、`package.nls.json` 不会覆盖彼此的备份，
新增 DOM 运行时也可在回滚时移除。回滚前检查所有原文件备份都存在，再逐个还原；
成功后卸载扩展，避免下一次激活重新应用。

旧版 `vsix-*` 备份没有完整路径，不能安全自动合并。不要把旧版本应用备份还原到升级后的
Devin；必要时重新安装。macOS 的完整 `.app` 备份应在安装插件前由用户保存。

## macOS 安装路径与代码签名

扩展优先从 `vscode.env.appRoot` 推导当前 `.app/Contents`，再探测系统与用户
`Applications` 目录；`DEVIN_INSTALL` 也可指定 `.app` 或 `Contents`。
macOS 使用大小写敏感的 `Contents/Resources/app`，Windows 保留 `resources/app`。

资源修改会使原有 macOS 代码签名失效；同步 `product.json.checksums` 不能修复该签名。
插件不执行重签名或系统安全检查绕过。已在 Darwin 27.0.0、Devin 3.11.228 /
VS Code 1.126.0 上由用户重启后人工验证生效，其他版本仍需验证。

## 验证方式

`tools/verify_layers.js` 不启动 Devin 就能验证四层：

```
1. 把 resources/app 里被本插件碰过的文件、以及官方语言包，复制到 <repo>/.verify/
2. DEVIN_INSTALL / DEVIN_HOME 指向沙盒
3. 给 extension.js 喂一个假的 `vscode` 模块，直接调 activate()
4. 断言：语言包条目数、162 条可查、254 个 %key% 全部可解析且有中文、
   webapp 载荷只有一份、两个 html 已注入、checksums 自洽
```

跑 `--apply --keep` 两次，第二次日志为空（零写入）→ 幂等成立。
