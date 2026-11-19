# Devin 桌面版汉化可行性实证报告

- Devin 安装目录: `C:\Users\27837\AppData\Local\Programs\Devin\resources\app`
- 应用版本: Devin 1.141.2 / windsurfVersion 3.14.30819 / codeiumVersion 1.48.2
- 语言包: `C:\Users\27837\.devin\extensions\ms-ceintl.vscode-language-pack-zh-hans-1.131.0-universal`

## 1. NLS 结构

| 文件 | 结构 | 规模 |
|---|---|---:|
| `out/nls.keys.json` | `[[源文件, [key,...]], ...]` | 2,188 个源文件 |
| `out/nls.messages.json` | 展平的默认英文数组 | 27,547 条 |
| `main.i18n.json` → `contents` | `{源文件: {key: 译文}}` | 1,786 个源文件 |

展平后 key 总数 = **27,547**  ·  与 messages 数组长度一致 ✅

## 2. 覆盖率 (按 (源文件, key) 二元组)

- 全部 NLS 字符串 : **27,496**
- 官方语言包已译  : **20,469** (74.4%)
- 缺中文          : **7,027** (25.6%)
- 语言包译文总条数 : 21,161  (其中 692 条本构建已不存在)

## 3. 缺失字符串按源文件聚合 TOP 45

| 缺失 | 该文件总数 | 源文件 |
|---:|---:|---|
| 230 | 230 | `vs/platform/agentHost/common/meta/copilotd/toolPresentation` |
| 132 | 132 | `vs/workbench/contrib/chat/browser/aiCustomization/aiCustomizationDiscoveryPage` |
| 120 | 120 | `vs/sessions/contrib/sessions/browser/views/automationsView` |
| 119 | 358 | `vs/workbench/contrib/chat/browser/chat.shared.contribution` |
| 114 | 128 | `vs/sessions/contrib/chat/browser/sessionsChatAccessibilityHelp` |
| 111 | 162 | `vs/workbench/contrib/chat/browser/aiCustomization/aiCustomizationManagementEditor` |
| 105 | 105 | `vs/workbench/contrib/chat/browser/aiCustomization/customizationMigrationCategories` |
| 93 | 135 | `vs/platform/agentHost/common/agentHostSchema` |
| 92 | 92 | `vs/sessions/contrib/providers/remoteAgentHost/browser/connectionDiagnosticsService` |
| 81 | 100 | `vs/sessions/contrib/sessions/browser/views/sessionsList` |
| 81 | 83 | `vs/sessions/contrib/chat/browser/chat.contribution` |
| 72 | 72 | `vs/workbench/contrib/chat/browser/chatPetAchievements` |
| 66 | 66 | `vs/platform/agentHost/node/copilot/copilotCustomizationCommandDisplay` |
| 66 | 91 | `vs/workbench/contrib/chat/browser/aiCustomization/mcpListWidget` |
| 64 | 64 | `vs/sessions/contrib/automations/browser/automationDialog` |
| 63 | 82 | `vs/sessions/common/contextkeys` |
| 63 | 63 | `vs/sessions/contrib/changes/browser/createPullRequestWidget` |
| 61 | 120 | `vs/workbench/contrib/chat/browser/actions/chatAccessibilityHelp` |
| 60 | 60 | `vs/platform/agentHost/common/agentMerge` |
| 56 | 56 | `vs/workbench/contrib/chat/browser/aiCustomization/toolsListWidget` |
| 55 | 80 | `vs/sessions/contrib/sessions/browser/sessionsActions` |
| 55 | 55 | `vs/workbench/contrib/chat/browser/voiceClient/voiceSessionController` |
| 54 | 54 | `vs/workbench/contrib/chat/browser/aiCustomization/embeddedMarketplaceDetail` |
| 53 | 53 | `vs/workbench/contrib/chat/browser/aiCustomization/customizationMigrationDashboard` |
| 52 | 52 | `vs/platform/agentHost/common/copilotCliConfig` |
| 52 | 83 | `vs/workbench/contrib/chat/browser/aiCustomization/pluginListWidget` |
| 48 | 61 | `vs/platform/agentHost/common/agentHostStarter.config.contribution` |
| 45 | 45 | `vs/sessions/contrib/chat/browser/sessionComparisonResult` |
| 44 | 52 | `vs/workbench/contrib/chat/browser/chatDebug/agentHostChatDebugProvider` |
| 43 | 43 | `vs/platform/agentHost/node/shared/agentMergeServerTools` |
| 43 | 43 | `vs/workbench/contrib/chat/browser/chatDebug/chatDebugWireLogView` |
| 42 | 42 | `vs/sessions/contrib/automations/browser/automationTools` |
| 41 | 41 | `vs/workbench/contrib/agentsVoice/browser/agentsVoice.contribution` |
| 40 | 202 | `vs/workbench/common/theme` |
| 40 | 40 | `vs/sessions/contrib/sessions/browser/views/automationsAccessibility` |
| 40 | 70 | `vs/sessions/contrib/sessions/browser/views/sessionsViewActions` |
| 39 | 39 | `vs/platform/agentHost/node/shared/sessionServerTools` |
| 39 | 40 | `vs/workbench/contrib/chat/browser/aiCustomization/embeddedAgentPluginDetail` |
| 38 | 38 | `vs/workbench/contrib/chat/browser/widget/chatPetWidget` |
| 37 | 66 | `vs/workbench/contrib/chat/browser/widget/chatListRenderer` |
| 36 | 36 | `vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionInputPills` |
| 36 | 36 | `vs/platform/agentHost/node/shared/worktreeIsolation` |
| 36 | 36 | `vs/platform/agentHost/common/streamingToolCallDisplay` |
| 36 | 36 | `vs/workbench/contrib/chat/browser/sessionChatPillOptions` |
| 35 | 35 | `vs/sessions/contrib/providers/remoteAgentHost/browser/connectionDiagnosticsReport` |

## 4. Devin/Windsurf 专有源文件

| 缺失 | 总数 | 源文件 |
|---:|---:|---|
| 3 | 6 | `vs/workbench/contrib/windsurfOnboarding/browser/windsurfOnboarding.contribution` |
| 1 | 3 | `vs/workbench/contrib/windsurfDesktopShell/browser/createDevinHost` |
| 1 | 12 | `vs/workbench/contrib/windsurfCascadeView/browser/cascadeView.contribution` |
| 1 | 23 | `vs/workbench/contrib/windsurfDesktopShell/browser/devinWebappCommands` |
| 1 | 4 | `vs/workbench/contrib/windsurfCascadeView/browser/cloudSessionWorkspaceEditorInput` |
| 0 | 24 | `vs/workbench/contrib/devinCloudSaveNotices/electron-browser/devinCloudSaveNotices.contribution` |
| 0 | 6 | `vs/platform/windsurfSvg/browser/windsurfCodicons` |
| 0 | 10 | `vs/workbench/contrib/windsurfSettingsPage/browser/windsurfSettingsPage.contribution` |
| 0 | 5 | `vs/workbench/browser/windsurfSaveFile` |
| 0 | 8 | `vs/workbench/contrib/windsurfFeedback/browser/windsurfFeedback.contribution` |
| 0 | 14 | `vs/workbench/contrib/windsurfPullRequest/browser/pullRequest.contribution` |
| 0 | 55 | `vs/workbench/contrib/windsurfDesktopShell/browser/desktopShellMenubar` |
| 0 | 11 | `vs/platform/windsurfChatClient/electron-main/chatClientPreviewDownload` |
| 0 | 2 | `vs/workbench/contrib/windsurfCascade/browser/windsurfCascadeMainThreadCommands` |
| 0 | 16 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapViewer.contribution` |
| 0 | 5 | `vs/platform/windsurfChatClient/common/chatClientPreview` |
| 0 | 4 | `vs/workbench/contrib/devinCloudFiles/browser/devinCloudFilesStatusView` |
| 0 | 5 | `vs/workbench/contrib/windsurfMcpService/browser/windsurfMcp.contribution` |
| 0 | 3 | `vs/workbench/contrib/windsurfDesktopShell/browser/devinWebappEditors` |
| 0 | 12 | `vs/platform/windsurfChatClient/electron-main/chatClientPreviewMainService` |
| 0 | 5 | `vs/workbench/contrib/windsurfAgentWindow/browser/cloudSessionEditorWindow` |
| 0 | 21 | `vs/workbench/contrib/windsurfAcpService/browser/acpRemoteHostActions` |
| 0 | 6 | `vs/workbench/contrib/windsurfAcpService/browser/acpSessionsQuickAccess` |
| 0 | 2 | `vs/workbench/contrib/windsurfAcpService/browser/windsurfAcp.contribution` |
| 0 | 4 | `vs/platform/theme/common/colors/windsurfDiffColors` |
| 0 | 1 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapBookmarkDecorationService` |
| 0 | 5 | `vs/workbench/contrib/windsurfDesktopShell/browser/desktopShellAppControls` |
| 0 | 7 | `vs/workbench/contrib/windsurfAgentWindow/browser/windsurfAgentWindowActions` |
| 0 | 12 | `vs/workbench/contrib/windsurfMigration/electron-browser/windsurfMigration.contribution` |
| 0 | 2 | `vs/workbench/contrib/windsurfDesktopShell/browser/devinWebappKeybindingEditing` |
| 0 | 2 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapExportAction` |
| 0 | 11 | `vs/workbench/contrib/windsurfChatClient/electron-browser/chatClientModuleSelection.contribution` |
| 0 | 13 | `vs/platform/theme/common/colors/windsurfCustomColors` |
| 0 | 2 | `vs/workbench/contrib/windsurfCustomAppIcon/browser/windsurfAppIconCustomization.contribution` |
| 0 | 2 | `vs/workbench/contrib/windsurfAcpService/browser/windsurfAcpService` |
| 0 | 7 | `vs/workbench/services/devinCloudFiles/browser/devinCloudEditorError` |
| 0 | 2 | `vs/workbench/contrib/windsurfAgentWindow/electron-browser/agentWindowReveal` |
| 0 | 1 | `vs/workbench/contrib/windsurfAgentWindow/electron-browser/windsurfAgentWindowActions` |
| 0 | 4 | `vs/workbench/contrib/windsurfAgentWindow/browser/devinSessionSshWindow` |
| 0 | 1 | `vs/workbench/contrib/windsurfCascade/browser/windsurfCascade.contribution` |
| 0 | 4 | `vs/workbench/contrib/windsurfDatadogRum/browser/datadogRum.contribution` |
| 0 | 2 | `vs/platform/windsurfAuth/common/windsurfAuth` |
| 0 | 5 | `vs/workbench/contrib/windsurfStatusBarSettingsService/browser/windsurfStatusBarSettingsPanel` |
| 0 | 1 | `vs/workbench/contrib/windsurfCascadeView/browser/readOnlyDiffContentProvider` |
| 0 | 1 | `vs/workbench/contrib/windsurfCascadeView/browser/snippetEditorPane` |
| 0 | 3 | `vs/workbench/contrib/windsurfDesignTokenEditor/browser/designTokenEditor.contribution` |
| 0 | 1 | `vs/workbench/contrib/windsurfAgentWindow/electron-browser/agentWorkspacePrewarm` |
| 0 | 1 | `vs/workbench/contrib/windsurfDesktopShell/browser/desktopShell.contribution` |
| 0 | 1 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapHomeEditorInput` |
| 0 | 1 | `vs/workbench/contrib/windsurfStatusBarSettingsService/browser/tabs/keybindingTab` |
| 0 | 1 | `vs/workbench/contrib/windsurfPlanEditor/browser/planEditor.contribution` |

专有文件合计: 51 个文件, 全部 key 359, 其中缺中文 7

## 5. 缺中文的 Devin/Windsurf 字符串样例 (前 60)

| 源文件 | 英文原文 |
|---|---|
| `windsurfOnboarding.contribution` | Controls the application that onboarding selects for the import of settings and extensions. The user can change the selection. |
| `windsurfOnboarding.contribution` | Onboarding selects no application. |
| `windsurfOnboarding.contribution` | Onboarding selects VS Code when VS Code data exists on the machine. |
| `createDevinHost` | {0} is on this computer. The agent runs on the remote ({1}) and can't read it there. |
| `cascadeView.contribution` | Session name cannot be longer than {0} characters |
| `devinWebappCommands` | Set up Computer Use (macOS permissions) |
| `cloudSessionWorkspaceEditorInput` | Devin Settings |

## 6. 完全缺中文的源文件 (语言包零覆盖)

共 311 个文件。前 30：

- `vs/platform/agentHost/common/meta/copilotd/toolPresentation` (230 条)
- `vs/workbench/contrib/chat/browser/aiCustomization/aiCustomizationDiscoveryPage` (132 条)
- `vs/sessions/contrib/sessions/browser/views/automationsView` (120 条)
- `vs/workbench/contrib/chat/browser/aiCustomization/customizationMigrationCategories` (105 条)
- `vs/sessions/contrib/providers/remoteAgentHost/browser/connectionDiagnosticsService` (92 条)
- `vs/workbench/contrib/chat/browser/chatPetAchievements` (72 条)
- `vs/platform/agentHost/node/copilot/copilotCustomizationCommandDisplay` (66 条)
- `vs/sessions/contrib/automations/browser/automationDialog` (64 条)
- `vs/sessions/contrib/changes/browser/createPullRequestWidget` (63 条)
- `vs/platform/agentHost/common/agentMerge` (60 条)
- `vs/workbench/contrib/chat/browser/aiCustomization/toolsListWidget` (56 条)
- `vs/workbench/contrib/chat/browser/voiceClient/voiceSessionController` (55 条)
- `vs/workbench/contrib/chat/browser/aiCustomization/embeddedMarketplaceDetail` (54 条)
- `vs/workbench/contrib/chat/browser/aiCustomization/customizationMigrationDashboard` (53 条)
- `vs/platform/agentHost/common/copilotCliConfig` (52 条)
- `vs/sessions/contrib/chat/browser/sessionComparisonResult` (45 条)
- `vs/workbench/contrib/chat/browser/chatDebug/chatDebugWireLogView` (43 条)
- `vs/platform/agentHost/node/shared/agentMergeServerTools` (43 条)
- `vs/sessions/contrib/automations/browser/automationTools` (42 条)
- `vs/workbench/contrib/agentsVoice/browser/agentsVoice.contribution` (41 条)
- `vs/sessions/contrib/sessions/browser/views/automationsAccessibility` (40 条)
- `vs/platform/agentHost/node/shared/sessionServerTools` (39 条)
- `vs/workbench/contrib/chat/browser/widget/chatPetWidget` (38 条)
- `vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionInputPills` (36 条)
- `vs/platform/agentHost/common/streamingToolCallDisplay` (36 条)
- `vs/platform/agentHost/node/shared/worktreeIsolation` (36 条)
- `vs/workbench/contrib/chat/browser/sessionChatPillOptions` (36 条)
- `vs/sessions/contrib/providers/remoteAgentHost/browser/connectionDiagnosticsReport` (35 条)
- `vs/sessions/contrib/chat/browser/externalSessionBanner` (33 条)
- `vs/sessions/contrib/sessionInputBanners/browser/sessionWorktreeCleanupEditor` (33 条)

## 7. 内置扩展的贡献点（Devin 家族）

| 扩展 | 命令数 | 硬编码英文 title | 目录内 package.nls* |
|---|---:|---:|---|
| `windsurf` | 52 | 0 | package.nls.json、package.nls.zh-cn.json |
| `windsurf-dev-containers` | 11 | 0 | package.nls.json、package.nls.zh-cn.json |
| `windsurf-remote-devin` | 1 | 0 | package.nls.json、package.nls.zh-cn.json |
| `windsurf-remote-openssh` | 13 | 0 | package.nls.json、package.nls.zh-cn.json |
| `windsurf-remote-wsl` | 14 | 0 | package.nls.json、package.nls.zh-cn.json |

结论: 这些扩展的命令标题、菜单、配置项说明全部硬编码英文，**官方语言包机制无法覆盖**；
本插件的做法是写 `package.nls.json` / `package.nls.zh-cn.json` 并把 package.json 里的字符串换成 `%key%`
（见 `tools/build_manifest_plan.py` 与 `extension.js` 的第 2 层）。
