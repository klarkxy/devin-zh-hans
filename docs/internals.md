# Devin Desktop 内部机制与实证记录

这份文档记录逆向/实测得到的事实，以及几条**导致错误结论的坑**。所有结论都标注了证据来源。
版本基线：**Devin 1.126.0 / windsurfVersion 3.11.216 / codeiumVersion 1.48.2**。

## 1. Devin Desktop 的身份

**它是 Windsurf（Exafunction / Codeium）改名而来的 VS Code fork。**

证据来自本机 `resources/app/product.json`：

```
nameShort        : "Devin"
applicationName  : "devin-desktop"
oldNameShort     : "Windsurf"          ← 改名痕迹
oldDataFolderName: ".windsurf"
oldUrlProtocol   : "windsurf"
licenseName      : "MIT"
codeiumVersion   : "1.48.2"
windsurfVersion  : "3.11.216"
author           : Exafunction, Inc.
extensionsGallery: marketplace.windsurf.com
```

因此它同时具备两套扩展机制：标准 VS Code 扩展（VSIX）+ 自己的 Agent UI。

## 2. 相关目录

| 路径 | 内容 |
|---|---|
| `%LOCALAPPDATA%\Programs\Devin\` | 安装树（**未打包成 asar**，`resources/app` 是明文目录） |
| `…\resources\app\out\vs\workbench\devin-webapp-host\` | **Agent UI（3.11 起的实现）**，87 MB / 1,877 chunk |
| `…\resources\app\out\vs\workbench\windsurf-chat-client\index.js` | 旧版 Agent 侧边栏（21 MB，3.11 仍在，但已不是主路径） |
| `…\resources\app\out\vs\sessions\sessions.desktop.main.js` | 会话窗口（40 MB） |
| `…\bin\devin-desktop.cmd` | CLI，等价于 VS Code 的 `code` —— `--install-extension` 可用 |
| `%USERPROFILE%\.devin\argv.json` | 启动参数（`locale` 在这里） |
| `%USERPROFILE%\.devin\extensions\` | 用户扩展与语言包 |
| `%APPDATA%\devin\languagepacks.json` | 语言包缓存索引（**不要伪造它的 hash**，见坑 2） |
| `%APPDATA%\devin\logs\<时间戳>\` | 日志（`main.log` / `exthost.log` / `renderer.log`） |

## 3. NLS（界面字符串）机制

`out/nls.keys.json` 的结构是 `[[源文件, [key...]], ...]`（1,786 个源文件），
`out/nls.messages.json` 是与之**顺序一一对应**的展平英文数组（21,210 条）。
两者的长度一致，可用来精确还原每个 key 的默认英文。

**关键**：`workbench.desktop.main.js` 里对 `nls.messages.json` 的引用次数是 **0**
—— 英文默认值是**内联**在 bundle 里的，运行时并不读那个 json。
所以「改 `nls.messages.json` 让界面变中文」这条路**不通**，只能走语言包。

覆盖率见 [coverage.md](../tools/data/coverage.md)：21,161 条中官方语言包覆盖 20,999 条（99.2%），缺 162 条。

## 4. 完整性校验的确切范围

`out/vs/workbench/workbench.desktop.main.js` 里的实现（反混淆后）：

```js
async _isPure(){
  let i = this.productService.checksums || {};        // ← 只取 product.json 的 checksums
  await this.lifecycleService.when(4);
  let e = await Promise.all(Object.keys(i).map(o => this._resolve(o, i[o])));
  //                ^^^^^^^^^^^^^^ 只遍历清单里的键
  ...
}
async _resolve(i, e){ ... this.checksumService.checksum(uri) ... }
_createChecksumPair(i, e, t){ return { uri:i, actual:e, expected:t, isPure: e===t } }
_showNotification(){ ... }        // ← 失败只弹通知，不阻止启动
```

结论：

- 校验范围**就是** `product.json.checksums` 里列出的文件（3.11 是 **12 个**），
  **不含** `extensions/`，也不含用户目录；
- 哈希算法是 `base64(sha256(file))` 去掉 `=` 填充；
- 校验失败**只弹通知**，不阻止启动。

受保护的 12 个文件（3.11.216）：

```
vs/base/parts/sandbox/electron-browser/preload.js
vs/workbench/workbench.desktop.main.js
vs/workbench/windsurf-chat-client/index.js
vs/workbench/devin-webapp-host/index.js                   ← 3.11 新增（442 B 的入口，不是 chunk）
vs/workbench/workbench.desktop.main.css
vs/workbench/api/node/extensionHostProcess.js
vs/code/electron-browser/workbench/workbench.html         ← 我们注入 DOM 脚本
vs/code/electron-browser/workbench/workbench.js
vs/sessions/sessions.desktop.main.js
vs/sessions/sessions.desktop.main.css
vs/sessions/electron-browser/sessions.html                ← 我们注入 DOM 脚本
vs/sessions/electron-browser/sessions.js
```

`node_modules/@exa/chat-client/index.js`、`devin-webapp-host/assets/**` **不在**清单里，改它们无需同步哈希。

## 5. Agent UI 的实现（3.11 变化）

### 5.1 挂载方式

`workbench.desktop.main.js`：

```js
let n = await import("@devin/webapp-host");
this.startup.mark("webappHostImported");
c = n.installDevinHost(CLn(t, a, this.instantiationService, r, l, o, () => …))
```

`@devin/webapp-host` 由 `out/vs/workbench/devin-webapp-host/index.js` 提供（`import.meta.resolve` 解析）。
**所以 Agent UI 现在跑在 workbench 渲染进程里**，不再是一个独立窗口
（`sessions.html` 那条路仍然存在，用于会话窗口）。

### 5.2 i18n 结构

`devin-webapp-host/assets/entry-host-editor-mode-menu-*.js`：

```js
resources: { en: { translation: yl, review: lu } }, lng: "en", fallbackLng: "en"
gu = [{code:"en"},
      {code:"ja", translation: () => import("./ja-Cd26s5QO.js"), review: () => import("./ja-yCsZX4qV.js")},
      {code:"pt", …}, {code:"es", …}]

function Eu({pseudoLocale: e = !1, englishOverrides: t} = {}) { … Mt.use(Mn).init({…}) }
…
Mt.isInitialized || Eu()
```

**3.14.30819 的变化**（实证见 `tools/data/webapp-314-anchor.md`）：

- chunk 改名为 `chunk-entry-host-editor-mode-menu-*.js`（多了 `chunk-` 前缀）；
- 混淆名变化：`Mt`→`at`、`Eu`→`Jd`、`Mn`→`pd`，**资源根 `mu` 与 `hu` 未变**；
- 守卫语句变为 `at.isInitialized||Jd()`；字符串字面量全部改用反引号；
- i18next init 结构不变：`n={en:{translation:t?JSON.parse(JSON.stringify(mu)):mu,review:hu}}`、
  `at.use(pd).init({resources:n,lng:`en`,fallbackLng:`en`,ns:[`translation`,`review`],defaultNS:`translation`,…})`。

插件代码以 `HOST_ANCHORS` 数组同时接受两种守卫、以 `HOST_CHUNK_PREFIXES` 同时匹配两种
chunk 前缀，因此 3.11 与 3.14 安装都能落地。

要点：

- 有**真实的多语言机制**（`ja` 5,030 key、`es` 4,846 key、`pt` 1,229 key），但**没有中文**；
- `useTranslation(` 的调用数是 **2**（不是 0），说明大部分组件**确实**走 i18next —— 
  这与 3.10 时代「chat-client 里 useTranslation 为 0、资源表是死数据」的结论相反；
- 所以 3.11 起不必再靠 DOM 硬翻译，可以按 key 覆盖 —— 这是本插件第 3 层的由来。

### 5.3 为什么不新增一个 zh locale

- 加 locale 需要改 `gu` 数组、改 `changeLanguage` 的调用点、还要维护一份**完整**资源
  （Devin 侧 19,269 个 key 且随版本变化），成本高且容易漏；
- Devin 自己的 `englishOverrides` 入口只服务 `en`，改 locale 反而更脆弱；
- 不新增 locale 就不会影响 ja / pt / es 用户；
- 覆盖已有的 `en` 值语义上也更贴切：我们要的是「同一个 key 换一种语言显示」，
  而不是「多一种可选语言」。

### 5.4 注入点是 mu，不是 addResourceBundle

第 3 层最初写成在 `Eu()` 之后调 `addResourceBundle`：

```js
Mt.isInitialized || Eu(), Mt.addResourceBundle("en","translation",{…},!0,!0)
```

**这条路径不成立。** i18next 的 `initAsync` 默认 `true`，`init()` 是异步完成的；
资源注册在 `loadResources` 的回调里才生效，届时会用 `resources` 对象**覆盖**
已有 bundle。结果就是：载荷完整躺在文件里、校验全绿，界面却显示原始 key
（`sidebar.automations`）。

正确做法是改 `resources` 本身。`Eu()` 里：

```js
function Eu({pseudoLocale:e=!1,englishOverrides:t}={}){
  let n={en:{translation: t ? JSON.parse(JSON.stringify(mu)) : mu, review:hu}};
  return Mt.use(Mn).init({resources:n, …}), t && …, Mt
}
```

`mu` 就是英文资源对象（`var mu,hu,gu;` 之后 `mu=yl`）。在锚点**之前**插一句：

```js
Object.assign(mu||{}, {中文}),
Mt.isInitialized || Eu()
```

中文就成了 `init({resources})` 的一部分，和英文同源同寿命，不依赖任何时序。

两个副作用要小心：

- **必须插在锚点之前。** 插在其后则 `init` 已用旧 `mu` 完成，改 `mu` 不再生效。
- **别留尾逗号。** 锚点后原本跟着 `,`，插在其前再拼 `payload + ','` 会得到
  `…,Mt.isInitialized||Eu(),}`。整个 chunk 语法错误，Devin 直接起不来。
  `verify_layers.js` 为此加了专门断言。

### 5.4.1 必须逐命名空间合并，不能用 Object.assign 整体覆盖

resources 是**两层**结构：`{ ns: { "点号key": 文案 } }`，第二层的 key 是带点号的
扁平字符串（`"general.openEditorSettings.label"`），不是嵌套对象。

所以「深合并」的正确写法是**对每个命名空间各做一次 Object.assign**：

```js
Object.assign(mu.settings||(mu.settings={}), {中文}),
Object.assign(mu.sidebar||(mu.sidebar={}), {中文}),
…
```

若写成 `Object.assign(mu, {中文})`（整体浅合并），`mu.localSettings` 会被替换成
只含中文子集的新对象，未翻译的英文 key 随之消失 —— i18next 查不到就回退成
**显示 key 本身**：

```
localSettings.general.openEditorSettings.label
localSettings.agents.searchPlaceholder
```

这正是 1.2.1 之后设置页成片原始 key 的原因。全量算下来会丢 7,843 个英文 key。

另外不要用递归函数实现「深合并」：`function` 声明不能出现在逗号表达式里
（`Object.assign(…),function __dz(){}` 是语法错误，整个 chunk 起不来）。
两层结构下逐命名空间合并既正确又最简单。

### 5.5 资源有两种写法，第二种漏掉会丢掉设置页整页

en 资源在 chunk 里以两种形式出现：

```js
// ① 对象字面量（模板/普通字符串）
ma={agentLocation:`Tip: Run Devin in the cloud…`, sessionNav:`Tip: Move between sessions (<up/> / <down/>)`,…}

// ② 内联 JSON 字符串
Ss=JSON.parse(`{"wikiEffortLow":"Low","wikiEffortMedium":"Medium",…}`)
```

**设置页那 3,938 个 key 全在 ② 里**（`settings` 命名空间）。只扫 ① 的话，
读出的树只有 8,189 个 key，设置页的「外观 / 语言 / 通知」整页会保持英文。

解析 ② 还要处理转义层级：模板字符串里的 `\"` 在 JSON 里应当是 `\"`（保留反斜杠），
`\u` 要连后面 4 位一起搬。直接 `JSON.parse` 原文会报
`Expecting ',' delimiter` 或 `Invalid \escape`。

### 5.6 DOM 层仍然需要

即便有 i18n，仍有大量文案来自运行时数据（会话标题、仓库名、动态状态、计数值），
以及被拆成多个文本节点的句子。这部分只能 DOM 兜底。

新版 DOM 的跳过标记（实测存在）：`[data-transcript-row-key]`（42 处）、
`[data-slate-node]` / `[data-slate-editor]`、`[data-devin-input-box]`（14 处）、
`[data-streamdown]`（51 处）、`.prose`（65 处）、`.xterm`（189 处）、`translate="no"`（1,247 处）。
注意 `[data-testid*="message-content"]` 在新版**一处都没有**，已不能作为主要判据。

## 6. 内置扩展的贡献点无法走语言包

5 个 Devin 内置扩展的 `contributes` 全是硬编码英文，目录内没有 `package.nls*.json`：

| 扩展 | 命令数 | 硬编码 title | package.nls* |
|---|---:|---:|---|
| `windsurf` | 60 | 60 | 无 |
| `windsurf-dev-containers` | 11 | 11 | 无 |
| `windsurf-remote-devin` | 1 | 1 | 无 |
| `windsurf-remote-openssh` | 13 | 13 | 无 |
| `windsurf-remote-wsl` | 14 | 14 | 无 |

`workbench.desktop.main.js` 的解析顺序（反混淆）：

```js
async getLocalizedMessages(extUri, manifest, nlsConfig) {
  const nlsDefault = joinPath(extUri, "package.nls.json");
  const id = `${manifest.publisher}.${manifest.name}`;
  const c = nlsConfig.translations[id];          // ① 语言包 bundle
  if (c) { … return { values: g.contents?.package, default: nlsDefault }; }
  …const p = await this.findMessageBundles(extUri, nlsConfig);   // ② package.nls.<lang>.json
  …                                                             // ③ package.nls.json
}
```

所以只要写 `package.nls.zh-cn.json` + `%key%`，**不需要注册语言包 bundle**。
（1.0.x 走的是 ① 那条路：改 `package.json` 为 `%key%` 再把中文塞进语言包的
`translations/extensions/windsurf.i18n.json`。两条都能用，②更简单、少一个同步点。）

## 7. 三个坑

### 坑 1：`ELECTRON_RUN_AS_NODE` 会让 Devin 变成 Node，然后静默退出

`bin/devin-desktop.cmd` 用 `set ELECTRON_RUN_AS_NODE=1` + `Devin.exe out/cli.js` 实现 CLI。
用这个变量跑完脚本后如果没清掉，再 `Start-Process Devin.exe` 启动的其实是 **Node 进程**：

- 进程列表里没有 Devin（或一闪而过）
- 日志目录不新建
- **exit code 0**（正常退出，不报错）

表现和「补丁破坏了完整性校验导致软件拒绝启动」一模一样。判定：

```powershell
& "$env:LOCALAPPDATA\Programs\Devin\Devin.exe" --version
# v24.x.x  → 中了这个坑（Node 版本）
# v3x.x.x  → 正常（应用版本）
```

### 坑 2：不要伪造 `languagepacks.json` 的 hash

VS Code 用 `clp/<hash>.<locale>` 作为语言包缓存目录名。
把 hash 改成自定义值（本意是「强制重建」）会让它在启动时 `scandir` 一个不存在的目录：

```
ENOENT: no such file or directory, scandir
  '…\AppData\Roaming\Devin\clp\devin-zh-1792211331252.zh-cn'
```

正确做法：**只补 `translations` 条目，不动 hash**。
因为 hash 只由「语言包扩展 id + 版本」决定、不含 bundle 列表，补条目不会让它失配。

### 坑 3：不要用「启动一次看进程在不在」判断补丁安全性

排查过程中一度据此得出「改 `extensions/windsurf/package.json` 会触发字节级哈希校验」的结论，
并写进了文档 —— **是错的**。后来做基线测试才推翻：**完全未打补丁的原始状态同样启动不起来**，
原因是坑 1 的环境变量残留。

教训：启动本身受单实例锁、更新检查、环境变量等多因素影响，**单点采样会得出错误结论**。
要么读代码（如第 4 节那样），要么固定全部变量做多次采样。

另一个相关的误判：一次「读入 JSON → 原样写回」（值一个都没改，只有格式变化）也被当成了校验证据，
实际上那次运行同样受环境变量干扰。

### 坑 4（3.11 新增）：webapp-host 的 i18n 入口是带 hash 的 chunk 文件名

`entry-host-editor-mode-menu-DUnUGWLA.js` 里的 hash 是构建期生成的，**每次 Devin 更新都会变**。
所以：

- 不能写死文件名去寻找，必须按��缀 `entry-host-editor-mode-menu*` + 内容含锚点来定位；
- 同理，改写时也不能依赖字节偏移，只能靠字符串锚点 `Mt.isInitialized||Eu()`；
- 该 chunk 不在 `product.json.checksums` 里（清单里是那个 442 字节的 `index.js`），
  但**下次 Devin 更新会整个换掉**，所以注入必须是幂等且可重复的。

### 坑 5（3.11 新增）：`devin-webapp-host/assets` 是 91 MB / 1,877 个文件

任何「全量扫描所有 chunk」的脚本都要注意耗时。本仓库的 `tools/analyze_webapp.py` 只扫一遍
（约 3 秒），并把结果缓存到 `tools/data/webapp.json`；验证脚本只复制 i18n 入口那一个 chunk。

## 8. Devin 的自动更新

安装树由 Inno Setup 维护（`unins000.exe`），自动更新会覆盖 `resources/app`。
被覆盖的是第 2/3/4 层（扩展贡献点、webapp i18next、窗口注入），
第 1 层的语言包在用户目录、通常保留。

因此插件的 `extension.js` 每次启动都做幂等自检，四层全部自动修复。
