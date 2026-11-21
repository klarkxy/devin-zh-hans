# Changelog

## 1.3.1

适配 **windsurf 3.14.30825 / 30833**，并修复 issue #3 报告的「更新后汉化失效」。

- **修复「更新后失效」的根因：注入永远晚于 webapp 挂载。** Devin 自动更新会在
  重启时用干净文件覆盖注入产物，而扩展激活（`onStartupFinished`）比 webapp
  挂载晚约 6–14 秒 —— 注入只改磁盘，本轮会话的内存里仍是英文，观感即「汉化
  失效」。现在启动注入后自动重载窗口一次（`healWindowReload`），让页面重新
  读盘；幂等性保证重载后的第二次激活零写入、不再触发重载。
- **修复 1.2.x 旧式载荷升级时的语法 bug。** 旧版把载荷插在锚点前用逗号分隔，
  升级替换时摘掉旧载荷会在块首留下孤立逗号（`function wR(){,…}`），
  `node --check` 拦下导致更新被放弃。现在插入前先摘掉块首孤立逗号
  （`verify_layers.js --upgrade` 场景实测复现并修复）。
- **修复 `devin-zh.status` 的扩展贡献点检查 bug。** 旧逻辑 `!s.includes('%"')`
  在 JSON 转义下永假/永真不定，五个内置扩展实际全部落地却显示 1/5；
  现在逐 `%key%` 引用校验 zh-cn 表。
- **webapp 层新增 537 条**（`tools/data/zh/webapp/w46.json`，3.14.30825 相对
  30819 的 806 个缺失 key，剔除纯占位符/符号 87 条与保持原文的品牌类）：
  i18next 覆盖表 31,961 → **32,233 条 / 426 命名空间**（3.14.30825 全部
  32,764 key 的 98.4%；唯一未覆盖 ns 是 `gateway`，仅 1 个示例占位符）。
- **DOM 词典新增 272 条**（`tools/dict/dom-30825.json`，30825 新增界面文案）：
  DOM 词典 35,265 → **35,565 条**。
- **NLS 层零缺口。** 3.14.30833 的 99 条新 NLS 缺口全部为 `{0} {1}` 类纯
  占位符模板（35 unique），按既有规则跳过；扩展贡献点计划 230 字段与 30819
  完全一致，无需更新。
- **构建工具支持目录重定向**（`DEVIN_ZH_DATA/ASSETS/TRANS/DIST`，经
  `_paths.py` 统一生效；词表输入目录与产物输出目录分离），受限 shell 下
  流水线可完整跑通。
- 术语与既有词表对齐的裁决：`spend limit` 统一「支出上限」、`pull request`
  统一「拉取请求」、`Wiki —` 前缀与 `Devin Webapp` 产品名保持原文；
  `automations.booleanTrue/False` → 是/否、头像部件 `Disc/Azure/Visor` →
  圆盘/天蓝/面罩、`Op...` → 运算符…、`Signal JSON` → 信号 JSON。
- 验证：`test_installation.js` 7/7（含 globalState 桩）、`test_runtime_merge.js`
  17/17、`test_dom_runtime.js` 4/4、`verify_layers.js` 三场景（fresh/幂等/
  upgrade）全绿；30825 chunk 注入后 `node --check` 通过、载荷锚点前就位、
  语法安全。

## 1.3.0

适配 **Devin 1.141.2 / windsurf 3.14.30819**（大版本更新：NLS 总量 21,161 → 27,496，
webapp 命名空间 317 → 427 / key 19,269 → 32,770），全层补齐至接近全覆盖。

- **适配 3.14 的 webapp chunk 重构。** i18n 入口改名 `chunk-entry-host-editor-mode-menu-*.js`，
  i18next 守卫变为 `at.isInitialized||Jd()`（混淆名 Mt/Eu/Mn → at/Jd/pd，资源根 `mu` 未变）。
  插件以锚点数组同时兼容 3.11 与 3.14；`verify_layers.js`、`extract_webapp_i18n.js`、
  `test_runtime_merge.js`、`verify_integrity.py` 同步双前缀/双守卫。
  `build_manifest_plan.py` 支持从已落地的 `%key%` 反查 package.nls.json 重建完整计划。
- **NLS 层新增 6,928 条**（`tools/data/zh/n00–n14.json`，3.14 缺口 7,027 条的全量翻译，
  99 条纯占位符模板除外）：合并版语言包 20,611 → **27,398 条**，覆盖率 ~100%。
- **webapp 层新增 10,872 条**（`tools/data/zh/webapp/w18–w45.json` + 3.14 新串 w17）：
  i18next 覆盖表 20,865 → **31,961 条 / 426 命名空间**（3.14 全部 32,770 key 的 97.5%），
  DOM 词典 20,985 → **35,265 条**。92 条纯符号/占位符串按规则跳过。
- **扩展贡献点 230/230 全中文**（3.14 删减后从 254 → 230 字段，补 3 条新设置项译文）。
- **术语统一**：issue → 议题（Jira/Linear/Pylon tracker 类；Devin Review 代码缺陷语境保留
  「问题」）；ticket/ticketing system → 工单；triage → 分诊；grants 在充值语境 → 赠额；
  On-call → 值班（Devin Oncall 产品名保留）。全部经过三批独立验收（结构/键对齐/占位符/术语）。
- **合并 1.2.0 的 macOS 支持与按完整路径备份/回滚**：3.14 适配同时覆盖 Windows 与 macOS，
  备份清单改按完整路径登记（`files-v2`），五个内置扩展的 `package.json` 不再互相覆盖。
- 验证：四层沙盒 + 真实安装全绿（语言包 27,398、i18next 命中率 100%、
  运行时查找 17/17、完整性 12/12 自洽）；1.3.0 VSIX 已装本机。
  `build_patch.py` 直接拾取 `w*.json`，无需预合并进 `dict/webapp-zh.json`。
- 修正 qa 验收发现的转义与引号问题（w03 的 `\n\n` 还原、`「」`→`“”` 等 20 余处）。

## 1.2.0

新增 macOS 支持，并重写备份与回滚机制，让汉化可以安全撤销。（感谢 @Menghuan1918，#2）

- **支持 macOS 安装。** 自动探测 macOS 上的 Devin 安装目录，macOS 用户也能完整汉化。
- **重写备份与回滚。** 按文件的完整路径记录备份清单，修复以前 5 个内置扩展的 `package.json`
  只按文件名备份、互相覆盖，导致回滚不完整的问题。
- **旧备份兼容说明。** 用 1.1.0 及更早版本留下的 `vsix-*` 备份没法自动回滚，会弹提示，
  需要手动处理或重装 Devin。
- **CI 覆盖三个平台。** 安装路径与回滚回归测试（7 项）和 DOM 输入框测试在
  Ubuntu、Windows、macOS 上都会运行。
- **已知限制。** 如果 Devin 升级后直接「重新应用汉化」，备份不会刷新，这时回滚可能把旧版文件还原上去。
  建议升级 Devin 后先卸载汉化再重新安装。Windows 图形界面还没人手动测过。

## 1.1.0

适配 **Devin 3.11.216**，重构 Agent UI 汉化落地方式，并补齐桌面设置、通知、模式菜单与模型选择等界面。

- **新增 Agent UI 的 i18next 覆盖层。** 结构化提取 317 个命名空间、19,269 个英文 key，
  同时支持对象字面量与 `JSON.parse` 内联资源。中文在初始化前按命名空间合并进 `en` 资源，
  不新增 locale，也不影响未翻译的英文 key。当前载荷为 **309 个命名空间 / 11,747 条译文**。
- **强化注入安全与升级恢复。** 修复浅合并丢 key、初始化时序覆盖中文、旧载荷替换产生连续逗号等问题。
  webapp chunk 写盘前执行完整 ES module 语法检查；覆盖旧版升级、损坏恢复和重复激活回归路径。
- **扩展 DOM 翻译层。** 当前包含 **20,604 条词典 / 60 条规则**，覆盖相对时间、计数和插值渲染形态。
  新增仅限输入框 placeholder 的翻译，不读取或修改输入内容，并继续跳过代码、终端、Agent 正文和可编辑区域。
- **补齐应用设置。** 覆盖扩展市场、Devin Local 配置、编辑器、Devin Tab、高级设置及下拉选项说明；
  通知页 27 个 key 全部覆盖，包括全部分组和移动端/桌面端提示。
- **补齐对话与模型界面。** 覆盖模式菜单、模式切换提示、Fusion 与模型详情、权限说明、模型搜索及欢迎命令。
- **扩展内置扩展与语言包覆盖。** 合并版语言包 **21,161 条**，补充新版缺口并回正品牌名；
  5 个内置扩展共 **254 个字段**全部提供中文。
- **加强验证。** 四层落地、webapp 语法、运行时查找、placeholder 行为、升级与幂等均纳入测试；
  真实安装完整性校验 **12/12** 自洽。

## 1.0.2

- 修复：不再删除 `languagepacks.json`（那会让 VS Code 到下一次启动才重建，用户得多重启一次），
  改为直接把 `windsurf` bundle 条目补进清单。
- 修复：不再伪造 `languagepacks.json` 的 hash —— VS Code 用它作 `clp/<hash>.<locale>`
  缓存目录名，伪造值会导致启动时 `scandir` 一个不存在的目录并抛 ENOENT。
- 安装提示更明确：告知需要重启一次才能完全生效。

## 1.0.1

- 修复 `languagepacks.json` hash 被伪造导致的 clp 目录 ENOENT。

## 1.0.0

- 首个版本：语言包（22,003 条）+ `windsurf` 扩展贡献点（176 条）+ 窗口级 DOM 翻译器（19,565 条词典）。
- 覆盖编辑器外壳、命令面板、设置项，以及 Agent 侧边栏与会话窗口。
