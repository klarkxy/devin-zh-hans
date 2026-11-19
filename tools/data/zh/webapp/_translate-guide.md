# 翻译规则与术语表（子代理必读，适用于 webapp 批次 w* 与 NLS 批次 n*）

两类批次的键风格不同：
- **webapp 批次（w*）**：`tools/data/webapp-todo.json` 的键是英文界面文案，插值形如 `{{var}}`、`{{count, list}}`，标签形如 `<tag>...</tag>`。
- **NLS 批次（n*）**：`tools/data/nls-todo-314.json` 的键是 VS Code NLS 英文原文，**位置参数形如 `{0}`、`{1}`**（单花括号），换行是字面 `\n`。`{0}` 一律原样保留，`\n` 保留在键里；译文对应位置同样保留 `{0}`，需要换行时用 `\n`。NLS 里也可能出现 `&&X` 加速键（如 `文件(&&F)`），若原文无 `&&` 则不加。

## 输出格式（硬性）

- 文件为 JSON 对象：`{ "英文原文": "中文译文", ... }`，UTF-8，无 BOM，无尾逗号，2 空格缩进。
- **键必须逐字符复制原文件中该行从行首 `"` 到冒号前 `"` 的全部内容**（包括 `\"`、`\n`、`{{...}}`、空格、标点），一个字符都不能改。
- 顺序与你在 todo 文件中读到的区间顺序一致（该文件已按字母排序），不要重排、不要漏条。
- 译文中**不得出现半角双引号 `"` 和反斜杠 `\`**：需要引用概念时用中文引号 “ ”。这保证 JSON 永不因转义出错。

## 翻译规则（硬性）

1. `{{var}}` 插值原样保留（`{{count}}`、`{{name, list}}` 等），一个字符不能改、不能删。
2. `<tag>...</tag>`、`<unit>`、`<settingsLink>`、`<agent>`、`<app>` 等标签保留标签本身，只译标签**内部**的英文文本。`[[...]]` 双方括号链接标记**整体保留原文不译**（内部文本按命令名寻址，译了会断链）。
3. 专有名词/品牌不译：Devin、ACU、MCP、GitHub、GitLab、Jira、Slack、Microsoft Teams、Jupyter、DeepWiki、SWE-2、Unified、Devin Local、Devin Cloud、VS Code、SSH、CLI、API、URL、JSON、YAML、SQL、PR、Wiki（设置页词保留 Wiki）。
4. 引号：英文直引号 `"..."` 指代界面文字/值时，译文用中文引号 “...”；指代代码字面量（如 `"models"`、`"New model"`）时保留英文原样。
5. 标点全角：，。；：？！（）——；省略号用 ……；em dash 用 —。
6. **句号跟随原文**：原文以 `.` 结尾 → 译文以 `。` 结尾；原文无句号 → 译文不加句号；原文以 `…`/`...` 结尾 → 译文以 `……` 结尾。
7. **英文/数字与中文之间加一个空格**（本仓库既有风格）：「SWE 模型」「Devin 的会话」「Outpost ID 已复制」「约 30 天」。
8. 称谓统一用「你」，不用「您」。
9. UI 短语（按钮/标签/菜单项）简洁，通常 ≤ 6 字；完整句子要求通顺自然、无翻译腔（避免「被」字堆叠、「的的不休」、欧化长定语）。
10. 复数后缀 `_one`/`_other` 出现在**值**里时照常翻译，用自然表达（如 `{{count}} 条记录`）。
11. 若条目只有纯符号/纯占位符、没有任何可译自然语言（如 `+{{amount}}`），跳过并在总结中列出，不要硬译。
12. 不确定的领域词保持直译或保留英文，不要发明新译名。

## 术语表（与既有词表对齐）

| 英文 | 中文 |
|---|---|
| credits | 额度 |
| Purchase credits | 购买额度 |
| credits left | 剩余额度 |
| Free credits | 免费额度 |
| add-on credits | 附加额度 |
| on-demand credits | 按需额度 |
| ACU | ACU（不译） |
| agent | 智能体 |
| subagent | 子智能体 |
| Agent mode | 智能体模式 |
| session | 会话 |
| playbook | 手册 |
| knowledge | 知识 |
| skill | 技能 |
| insights | 洞察 |
| On-call | 值班 |
| wiki | 知识库（导航语境）；Wiki 设置页语境保留 Wiki |
| Outpost / outpost | 前哨 |
| environment | 环境 |
| organization | 组织 |
| account | 账号 |
| enterprise | 企业 |
| billing tag | 账单标签 |
| snapshot | 快照 |
| trigger | 触发器 |
| automation | 自动化 |
| repository / repo | 仓库 |
| license | 许可证 |
| single sign-on | 单点登录 |
| air-gapped | 隔离网络 |
| machine | 机器 |
| worker | 工作进程 |
| worker credential | 工作进程凭据 |
| outpost pool | 前哨池 |
| grant | 授权（权限语境）；赠额（充值/点数语境） |
| break-glass | 应急暂停 |
| queue | 队列 |
| cron | 定时任务 |
| backfill | 回填 |
| readiness | 就绪度 |
| Agent Readiness | Agent Readiness（不译） |
| MCP server | MCP 服务器 |
| marketplace | 市场 |
| command center | 命令中心 |
| sidebar | 侧边栏 |
| tab | 标签页 |
| preflight check | 预检 |
| incident | 事件 |
| responder | 响应者 |
| breakdown | 明细 |
| spend | 支出 |
| quota | 配额 |
| fallback | 备用（模型）；兜底 |
| premium model | 高级模型 |
| model | 模型 |
| prompt | 提示词 |
| context | 上下文 |
| attachment | 附件 |
| secrets | 密钥 |
| sensitive | 敏感 |
| redact / redacted | 脱敏 |
| share | 共享 |
| member | 成员 |
| owner | 所有者 |
| admin | 管理员 |
| service user | 服务用户 |
| role | 角色 |
| policy | 策略 |
| permission | 权限 |
| default | 默认 |
| pinned | 固定 |
| draft | 草稿 |
| worklog | 工作日志 |
| transcript | 对话记录 |
| analytics | 分析 |
| usage | 用量 |
| consumption | 消耗 |
| rollout | 批量执行（按上下文可作「推广」） |
| scan / code scan | 扫描 / 代码扫描 |
| harness | 运行框架（Copilot/agent harness 语境） |
| issue | 议题（Jira/Linear/Pylon 等 tracker 类） |
| finding | 发现 |
| connection | 连接 |
| channel | 频道 |
| mapping | 映射 |

## 风格范例（摘自已合并词表，模仿它们）

- "Save your changes, then connect from this page." → "保存更改后，再从此页面建立连接。"
- "This draft looks like several independent tasks" → "这份草稿看起来像是几个相互独立的任务"
- "Anything you leave undecided counts as approved." → "你未作出决定的内容均视为已批准。"
- "High server load. Devin is waiting for capacity..." → "服务器负载过高。Devin 正在等待可用容量……"
- "Enter the base URL of your Jira Data Center instance. Devin checks that it reaches a supported version." → "输入你的 Jira Data Center 实例的基础 URL。Devin 会检查能否访问到受支持的版本。"
- "Allow Devin to use this MCP server during sessions" → "允许 Devin 在会话中使用此 MCP 服务器"
- "Install a license file" → "安装许可证文件"
- "Subagents (Preview)" → "子智能体（预览）"
- "Powered by SWE-2 Max (Lightning) — SWE-2 in Lightning mode, max reasoning effort" → "由 SWE-2 Max (Lightning) 驱动 — 以 Lightning 模式运行、推理强度最大的 SWE-2"
- "Temporarily using a backup model" → "暂时使用备用模型"
