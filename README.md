# Devin 简体中文

为 **Devin Desktop**（Windsurf 改名而来的 VS Code fork）提供完整简体中文界面。

## 下载

**[⬇ 下载最新版 devin-zh-hans.vsix](https://github.com/klarkxy/devin-zh-hans/releases/latest/download/devin-zh-hans.vsix)**
　·　[全部版本](https://github.com/klarkxy/devin-zh-hans/releases)　·　[更新日志](CHANGELOG.md)

### Windows

```powershell
# 关闭 Devin
Get-Process Devin -ErrorAction SilentlyContinue | Stop-Process -Force

# 安装（文件名固定，链接永远指向最新版）
& "$env:LOCALAPPDATA\Programs\Devin\bin\devin-desktop.cmd" --install-extension .\devin-zh-hans.vsix

# 启动（不要带 ELECTRON_RUN_AS_NODE）
Remove-Item Env:\ELECTRON_RUN_AS_NODE -ErrorAction SilentlyContinue
Start-Process "$env:LOCALAPPDATA\Programs\Devin\Devin.exe"
```

### macOS

已在 macOS（Darwin 27.0.0）、Devin Desktop **3.11.228 / VS Code 1.126.0**
上实际安装，并由用户重启后人工确认汉化生效。

**安装前请先备份完整的 `Devin.app`，并确认当前用户可写应用目录。**
第 2/3/4 层需要修改 `.app` 内的资源，**会使原有 macOS 代码签名校验失效**；
`product.json.checksums` 自洽并不意味着 macOS 签名仍然有效。
本插件不重签名，也不关闭或绕过系统安全检查。若系统阻止启动，请恢复原应用备份。

保存工作并完全退出 Devin，下载 VSIX 后安装：

```sh
"/Applications/Devin.app/Contents/Resources/app/bin/devin-desktop" \
  --install-extension ./devin-zh-hans.vsix
open -a Devin
```

自定义安装位置请调整命令路径。扩展运行时优先使用当前 Devin 的
`vscode.env.appRoot`，也会探测 `/Applications/Devin.app` 与
`~/Applications/Devin.app`，不依赖 Windows 的 `Devin.exe`。
如果外壳仍是英文，在命令面板执行 `Configure Display Language`，选择简体中文。

> 首次安装后**重启一次** Devin 才会完全生效 —— 语言包与窗口脚本在启动早期被读取，
> 而扩展激活在启动后期。此后每次启动都是中文。

## 覆盖范围

Devin 的界面由四个互不相通的字符串来源拼成，所以要分四层落地。

| 层 | 覆盖内容 | 机制 |
|---|---|---|
| **1. 语言包** | 菜单栏、命令面板、设置界面、侧边栏、状态栏、右键菜单、对话框 | 合并版 `main.i18n.json`（21,161 条）写进官方 zh-hans 语言包 |
| **2. 内置扩展** | 5 个 Devin 内置扩展的 60+ 个命令标题、设置项标题与说明（254 个字段） | `package.nls.json` + `package.nls.zh-cn.json` + `%key%` 占位符 |
| **3. Agent UI（i18next）** | Agent 侧边栏、会话窗口与设置页的 i18n 文案 | 把中文按英文 key 深合并进 webapp-host 的 `en` 资源（11,747 条 / 309 个命名空间） |
| **4. DOM 翻译器** | 运行时数据拼出来、语言包与 i18next 都碰不到的文案 | 窗口注入脚本 + TreeWalker + MutationObserver（词典 20,604 条 + 60 条正则） |

### 第 3 层的原理

从 Devin 3.11 起，Agent 侧边栏不再是一个独立的 chat-client bundle，而是
`out/vs/workbench/devin-webapp-host/`（约 91 MB、1,800+ 个 chunk），由
`workbench.desktop.main.js` 用 `import("@devin/webapp-host")` 挂进 **workbench 渲染进程**。

它内部自建 i18next，并且**自带多语言**——只是没有中文：

```js
gu = [{code:"en"}, {code:"ja", translation: () => import("./ja-XXXX.js")},
      {code:"pt", …}, {code:"es", …}]
```

Devin 自己的初始化调用（`entry-host-editor-mode-menu-*.js`）是：

```js
Mt.isInitialized || Eu()
```

本插件把它原地扩成：

```js
Mt.isInitialized||Eu(),
Mt.addResourceBundle("en","translation",{ /* 中文，按英文 key */ },!0,!0)
```

也就是**沿用 Devin 自己的 i18next 实例和 `en` 命名空间**，不新增 locale、不改 `lng`、
不动任何组件代码 —— ja / pt / es 用户完全不受影响。

### 第 2 层的原理

Devin 内置的 `windsurf`、`windsurf-dev-containers`、`windsurf-remote-devin`、
`windsurf-remote-openssh`、`windsurf-remote-wsl` 把命令标题与设置项说明**硬编码**在
`package.json` 里，且目录内没有 `package.nls*.json`，所以语言包机制对它们完全无效。

VS Code 解析扩展 manifest 的顺序是「语言包 bundle → `package.nls.<lang>.json` → `package.nls.json`」。
本插件走第二条：把 `package.json` 里 254 个字符串换成 `%key%`，并写两个 nls 文件。
这一步**不需要注册语言包 bundle，也不需要碰 `languagepacks.json`**。

### 完整性校验

`product.json.checksums` 保护 12 个文件，其中两个是注入脚本的窗口 HTML、一个是 webapp 入口。
本插件每次写完都会重算这些条目的哈希，实测 **12 / 12 自洽 → 不会出现「Devin 安装似乎损坏」**。
这仅指 Devin 自身的资源校验；macOS 代码签名是独立的校验机制，见上方安装说明。

## 自动化行为

扩展每次启动都静默自检并修复，全程幂等（第二次运行零写入）：

| 检查项 | 行为 |
|---|---|
| 合并版语言包被 Devin 更新覆盖 | 自动重写 |
| 内置扩展的 `package.json` 被还原成英文 | 自动重新 `%key%` 化并补 nls 文件 |
| webapp i18next 载荷被覆盖 | 自动重新注入（并识别旧载荷、原地替换而不是叠加） |
| 窗口脚本或 `<script>` 标签被覆盖 | 自动重写并重新注入 |
| `product.json.checksums` 与文件不符 | 自动同步为自洽 |

因此 **Devin 自动更新后无需手动处理**，下次启动会自己恢复。

## 命令

| 命令 | 作用 |
|---|---|
| `Devin 中文: 查看汉化状态` | 四层各自是否落地、完整性校验自洽情况 |
| `Devin 中文: 重新应用汉化` | 重新落地所有汉化（幂等，Devin 更新后用它恢复） |
| `Devin 中文: 卸载汉化并回滚` | 从备份还原到安装前状态 |

## 刻意不翻译的区域

代码编辑器（Monaco）、终端（xterm）、**Agent 消息正文**
（`[data-transcript-row-key]` / `[data-slate-node]` / `.prose` / `[data-streamdown]`）、
输入框内容（`[data-devin-input-box]` / `[contenteditable]`；普通输入框仅翻译 placeholder）、`[translate="no"]`、`cn` 之外的行内代码。

保证不碰代码，也不碰你和 Agent 的对话内容。

## 已知边界

- 少数文案仍可能显示英文：多段拼接的句子（React 把文本拆成多个节点）、
  纯由表达式拼出的日期与配额提示、`about:blank` webview 里的内嵌页面。
- Monaco 编辑器内部渲染文本不翻译（canvas 双渲染，也不应翻译）。
- 跨域 iframe（内嵌的 `app.devin.ai`）不在注入范围内。
- macOS 已在上述版本人工验证；其他系统/Devin 版本仍需验证，且修改应用资源会影响代码签名。

## Devin 更新后

自动更新会覆盖 `resources/app`（macOS 为 `Contents/Resources/app`），第 2/3/4 层随之失效（第 1 层在用户目录，通常保留）。
扩展下次激活时会检测并**自动重新落地**；若没恢复，执行命令面板里的
**`Devin 中文: 重新应用汉化`**。

## 回滚

优先使用命令面板里的 **`Devin 中文: 卸载汉化并回滚`**：从
`~/.devin/devin-zh-backups/files-v2/manifest.json` 按完整路径还原全部文件，
删除本插件新建的文件，然后卸载插件，避免下次启动重新应用。
同名的各扩展 `package.json` 分别保存，不再按文件名混用。

**不要在 Devin 升级后把旧备份覆盖到新版本。** 旧版 `vsix-*` 备份缺少完整路径信息，
无法安全自动合并还原；必要时重新安装 Devin。macOS 无法启动时，可恢复安装前的完整
`.app` 备份，并卸载插件，避免再次修改。

仅卸载扩展可以使用以下命令，但**不会还原已修改的应用资源**：

```powershell
& "$env:LOCALAPPDATA\Programs\Devin\bin\devin-desktop.cmd" --uninstall-extension devin-zh.devin-zh-hans
```

```sh
"/Applications/Devin.app/Contents/Resources/app/bin/devin-desktop" \
  --uninstall-extension devin-zh.devin-zh-hans
```

## 开发者

```powershell
python tools/analyze_nls.py           # NLS 缺口分析 -> data/coverage.md / missing.json / todo.json
python tools/analyze_webapp.py        # webapp-host i18n 分析 -> data/webapp.json / webapp.md
python tools/build_manifest_plan.py   # 内置扩展贡献点计划 -> assets/ext-manifest.*
python tools/build_patch.py           # 词表 -> translations/ / assets/
python tools/build_dom.py             # DOM 运行时 -> dist/devin-zh-dom.js
node tools/verify_layers.js --apply   # 沙盒副本上跑一遍真实落地逻辑并断言
node --test tools/test_installation.js # 无需安装 Devin 的路径/幂等/回滚回归测试
python tools/verify_integrity.py      # 完整性/占位符/注入状态报告
```

详见 [`tools/README.md`](tools/README.md) 与 [`docs/architecture.md`](docs/architecture.md)。

## 许可

MIT。语言包内含 Microsoft 官方 zh-hans 译文（MIT 许可）。
