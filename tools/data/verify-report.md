> 本报告读的是**本机真实安装目录的当前状态**，回答「现在是否已落地」。
> 想验证插件*能不能*落地（尤其在新版 Devin 上），跑 `node tools/verify_layers.js --apply`：
> 它在 `resources/app` 的沙盒副本上执行真实落地逻辑，并断言四层结果与幂等性。

## 1. product.json 完整性校验（补丁后重新计算）

| 结果 | 受保护文件 |
|---|---|
| ✅ 一致 | `vs/base/parts/sandbox/electron-browser/preload.js` |
| ✅ 一致 | `vs/workbench/workbench.desktop.main.js` |
| ✅ 一致 | `vs/workbench/windsurf-chat-client/index.js` |
| ✅ 一致 | `vs/workbench/devin-webapp-host/index.js` |
| ✅ 一致 | `vs/workbench/workbench.desktop.main.css` |
| ✅ 一致 | `vs/workbench/api/node/extensionHostProcess.js` |
| ✅ 一致 | `vs/code/electron-browser/workbench/workbench.html` |
| ✅ 一致 | `vs/code/electron-browser/workbench/workbench.js` |
| ✅ 一致 | `vs/sessions/sessions.desktop.main.js` |
| ✅ 一致 | `vs/sessions/sessions.desktop.main.css` |
| ✅ 一致 | `vs/sessions/electron-browser/sessions.html` |
| ✅ 一致 | `vs/sessions/electron-browser/sessions.js` |

**结论：12 个受保护文件全部自洽 → 不会触发“Devin 安装似乎损坏”告警**

## 2. 内置扩展的 %key% 占位符可解析性

| 扩展 | 占位符 | 无法解析 | 缺中文 |
|---|---:|---:|---:|
| `windsurf` | 142 | 0 | 0 |
| `windsurf-dev-containers` | 32 | 0 | 0 |
| `windsurf-remote-devin` | 4 | 0 | 0 |
| `windsurf-remote-openssh` | 30 | 0 | 0 |
| `windsurf-remote-wsl` | 22 | 0 | 0 |

合计：**230** 个占位符，无法解析 **0**，缺中文 **0**

### 抽样对照

| key | 英文默认 | 中文 |
|---|---|---|
| `windsurf.contributes.commands.0.title` | Log in | **登录** |
| `windsurf.contributes.commands.0.category` | Devin | **Devin** |
| `windsurf.contributes.commands.1.title` | Log Out | **退出登录** |
| `windsurf.contributes.commands.1.category` | Devin | **Devin** |
| `windsurf.contributes.commands.2.title` | Provide Devin auth token (backup login) | **提供 Devin 身份验证令牌（备用登录）** |
| `windsurf.contributes.commands.2.category` | Devin | **Devin** |
| `windsurf.contributes.commands.3.title` | Import VS Code settings | **导入 VS Code 设置** |
| `windsurf.contributes.commands.3.category` | Devin | **Devin** |


## 3. 语言包 bundle 注册与译文可查性

- 语言包版本 : 1.131.0 (engines.vscode = ^1.131.0)
- 已注册 bundle 数 : **95**
- 含 `windsurf` : ✅
- vscode bundle 译文总量 : **27,398** 条
- 本插件补充的 6928 条可查 : **6928/6928** ✅

## 4. Agent UI（webapp-host）与 DOM 层

- webapp i18next 载荷 : ✅ `chunk-entry-host-editor-mode-menu-BWLlgqZu.js`
  - 使用 Devin 自带的 `addResourceBundle("en","translation",…)` : ❌
  - 原始初始化锚点保留 : ❌
  - 载荷份数（应为 1） : 1
- webapp 覆盖词条 : **31,961** 条
- DOM 词典 : 35,804 条（通用 12,385 + 界面 23,419）
- 注入 `workbench.html` : ✅（运行时 ✅）
- 注入 `sessions.html` : ✅（运行时 ✅）
