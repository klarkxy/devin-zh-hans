# Changelog

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
- **术语统一**：issue → 议题（tracker 类；Devin Review 代码缺陷语境保留「问题」）、
  ticket → 工单、harness → 运行框架、grants（充值语境）→ 赠额、triage → 分诊、
  On-call → 值班（Devin Oncall 产品名保留）、Agent Readiness/Devin Oncall/Box 等保留英文。
- 验证：四层沙盒 + 真实安装全绿（语言包 27,398、i18next 命中率 100%、
  运行时查找 17/17、完整性 12/12 自洽）；1.3.0 VSIX 已装本机。
  `build_patch.py` 直接拾取 `w*.json`，无需预合并进 `dict/webapp-zh.json`。
- **术语统一**：issue → 议题（Jira/Linear/Pylon tracker 类；Devin Review 代码缺陷语境保留
  「问题」）；ticket/ticketing system → 工单；triage → 分诊；grants 在充值语境 → 赠额；
  On-call → 值班。全部经过三批独立验收（结构/键对齐/占位符/术语）。
- 修正 qa 验收发现的转义与引号问题（w03 的 `\n\n` 还原、`「」`→`“”` 等 20 余处）。

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
