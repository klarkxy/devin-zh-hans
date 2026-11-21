# webapp-host（新版 Agent UI）i18n 资源与词典覆盖

- i18n chunk: `chunk-entry-host-editor-mode-menu-2k2EH-7U.js`
- 命名空间: **427**
- 叶子 key: **32,764**
- 去重后英文原文: **25,277**
- 词典已覆盖: **24,928** (98.6%)
- 仍缺中文: **349**（其中可整串替换 330）

## 最大的命名空间

| 条数 | 命名空间 |
|---:|---|
| 6329 | `settings` |
| 1505 | `automations` |
| 1350 | `settingsPages` |
| 1168 | `bots` |
| 949 | `transcript` |
| 940 | `worklog` |
| 935 | `boards` |
| 865 | `billing` |
| 777 | `analyticsRevamp` |
| 504 | `workspace` |
| 465 | `oncall` |
| 440 | `securityRedTeaming` |
| 395 | `sidebar` |
| 360 | `enterprise` |
| 351 | `jira` |

## 缺口样例（前 60）

| 命名空间 | key | 英文 |
|---|---|---|
| `artifactShares` | `version` | v{{version}} |
| `adminHydration` | `reasonCount` | {{reason}} ({{count, number}}) |
| `mcpConfiguration` | `oauth` | OAuth |
| `mcpConfiguration` | `sse` | SSE |
| `mcpConfiguration` | `stdio` | STDIO |
| `mcpConfiguration` | `http` | HTTP |
| `manageAccess` | `bot` | {{botName}} |
| `manageAccess` | `bots` | {{botNamePlural}} |
| `budgets` | `map.usageWithAllocation` | {{used}} / {{limit}} |
| `nativeEditor` | `openInIde` | IDE |
| `gitPermissions` | `authTypePat` | PAT |
| `pluginAudience` | `selectedNames` | {{names, list}} |
| `pluginContents` | `namePlaceholder` | Acme Tools |
| `customizeMcp` | `summaryUrl` | URL |
| `customizeIntro` | `illustration.cli` | CLI |
| `enterpriseNetworking` | `perforceTitle` | Perforce |
| `boards` | `settingsForm.linkPlaceholder` | https://example.com |
| `boards` | `moreTags` | +{{count}} |
| `boards` | `tagEditor.shortLabelCount` | {{count}}/{{max}} |
| `boards` | `dialogs.quotedBoardName` | “{{name}}” |
| `boards` | `ticket.acuValue` | {{acus}} ACU |
| `boards` | `tagIconLabels.slack` | Slack |
| `boards` | `tagIconLabels.gitHub` | GitHub |
| `boards` | `tagIconLabels.linear` | Linear |
| `boards` | `tagIconLabels.flask` | Flask |
| `campaigns` | `panel.budget.acu` | {{value}} ACU |
| `admin` | `orgMembers.enterpriseRoleNames` | {{roles, list}} |
| `admin` | `lifeguardEvals.performance.metrics.f1` | F1 |
| `admin` | `sponsoredEvents.create.namePlaceholder` | HackMIT 2026 |
| `admin` | `sponsoredEvents.create.budgetPlaceholder` | 200 |
| `admin` | `sponsoredEvents.create.acuLimitPlaceholder` | 20 |
| `agentPicker` | `janeWongDevin` | Jane Wong Devin |
| `modelPickerMock` | `anthropicModels` | Anthropic |
| `modelPickerMock` | `googleModels` | Google |
| `modelPickerMock` | `openAIModels` | OpenAI |
| `modelSelect` | `costTagApiLabel` | API |
| `modelSelect` | `costTagByokLabel` | BYOK |
| `modelSelect` | `costTagMultiplierLabel` | {{multiplier}}x |
| `analyticsRevamp` | `cloud.keys.xs` | XS |
| `analyticsRevamp` | `cloud.keys.xl` | XL |
| `analyticsRevamp` | `cloud.keys.jira` | Jira |
| `analyticsRevamp` | `cloud.keys.jiraDataCenter` | Jira Data Center |
| `analyticsRevamp` | `reviewDashboard.versionNumber` | v{{number}} |
| `analyticsRevamp` | `reviewDashboard.examplesOutcomeCount` | {{findings}} {{outcome}} |
| `analyticsRevamp` | `units.acus_one` | ACU |
| `analyticsRevamp` | `units.aiFtes_one` | AI FTE |
| `auth` | `upgrade.freeFeatureDeepWiki` | DeepWiki |
| `apps` | `deploymentVersion` | V{{version}} |
| `automations` | `filterSelection` | {{labels, list(type: unit)}} |
| `automations` | `eventTypeName.webhook` | Webhook |
| `automations` | `introDevin` | Devin |
| `automations` | `preflightStep.webhookUrlLabel` | Webhook URL |
| `automations` | `preflightStep.webhookUrlPlaceholder` | https://example.com/devin/preflight |
| `automations` | `codeStep.stateSummary` | {{size}} / {{max}}KB |
| `automations` | `codeStep.testRunRecentEventOption` | {{eventType}} · {{when}} |
| `automations` | `opEq` | = |
| `automations` | `opGt` | > |
| `automations` | `opGte` | ≥ |
| `automations` | `opLt` | < |
| `automations` | `opLte` | ≤ |
