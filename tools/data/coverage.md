# Devin 桌面版汉化可行性实证报告

- Devin 安装目录: `C:\Users\27837\AppData\Local\Programs\Devin\resources\app`
- 应用版本: Devin 1.141.2 / windsurfVersion 3.14.30833 / codeiumVersion 1.48.2
- 语言包: `C:\Users\27837\.devin\extensions\ms-ceintl.vscode-language-pack-zh-hans-1.131.0-universal`

## 1. NLS 结构

| 文件 | 结构 | 规模 |
|---|---|---:|
| `out/nls.keys.json` | `[[源文件, [key,...]], ...]` | 2,188 个源文件 |
| `out/nls.messages.json` | 展平的默认英文数组 | 27,547 条 |
| `main.i18n.json` → `contents` | `{源文件: {key: 译文}}` | 2,188 个源文件 |

展平后 key 总数 = **27,547**  ·  与 messages 数组长度一致 ✅

## 2. 覆盖率 (按 (源文件, key) 二元组)

- 全部 NLS 字符串 : **27,496**
- 官方语言包已译  : **27,397** (99.6%)
- 缺中文          : **99** (0.4%)
- 语言包译文总条数 : 27,398  (其中 1 条本构建已不存在)

## 3. 缺失字符串按源文件聚合 TOP 45

| 缺失 | 该文件总数 | 源文件 |
|---:|---:|---|
| 8 | 132 | `vs/workbench/contrib/chat/browser/aiCustomization/aiCustomizationDiscoveryPage` |
| 7 | 100 | `vs/sessions/contrib/sessions/browser/views/sessionsList` |
| 3 | 55 | `vs/workbench/contrib/chat/browser/voiceClient/voiceSessionController` |
| 3 | 43 | `vs/sessions/contrib/providers/agentHost/browser/agentHostSessionConfigPicker` |
| 3 | 83 | `vs/workbench/contrib/chat/browser/aiCustomization/pluginListWidget` |
| 3 | 27 | `vs/sessions/contrib/chat/browser/sessionChatInputToolbar` |
| 3 | 23 | `vs/workbench/contrib/chat/browser/aiCustomization/embeddedConnectorDetail` |
| 3 | 10 | `vs/sessions/contrib/changes/browser/sessionSyncChanges` |
| 3 | 26 | `vs/sessions/contrib/sessionInputBanners/browser/sessionInputBanners` |
| 2 | 4 | `vs/workbench/services/agentEditorComments/browser/agentEditorCommentsOverlayWidget` |
| 2 | 52 | `vs/workbench/contrib/chat/browser/chatDebug/agentHostChatDebugProvider` |
| 2 | 91 | `vs/workbench/contrib/chat/browser/aiCustomization/mcpListWidget` |
| 2 | 23 | `vs/workbench/contrib/chat/browser/widget/chatContentParts/chatAgentMergeContentPart` |
| 2 | 14 | `vs/sessions/contrib/changes/browser/changesView` |
| 2 | 36 | `vs/sessions/contrib/accountMenu/browser/account.contribution` |
| 2 | 53 | `vs/workbench/contrib/chat/browser/aiCustomization/customizationMigrationDashboard` |
| 2 | 92 | `vs/sessions/contrib/providers/remoteAgentHost/browser/connectionDiagnosticsService` |
| 2 | 36 | `vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionInputPills` |
| 2 | 30 | `vs/workbench/contrib/chat/common/languageModels` |
| 2 | 5 | `vs/sessions/services/sessions/common/sessionComparison` |
| 2 | 64 | `vs/sessions/contrib/automations/browser/automationDialog` |
| 2 | 5 | `vs/workbench/contrib/chat/browser/widget/input/modelPicker/modelPickerActionItem` |
| 2 | 13 | `vs/sessions/contrib/sessions/browser/sessionsTitleBarWidget` |
| 2 | 3 | `vs/workbench/contrib/chat/browser/aiCustomization/aiCustomizationManagementEditorInput` |
| 2 | 34 | `vs/sessions/contrib/chat/browser/sessionWorkspacePicker` |
| 2 | 11 | `vs/workbench/contrib/chat/browser/sessionBackgroundShellsControl` |
| 1 | 3 | `vs/sessions/contrib/chat/browser/newSessionPromptOptions` |
| 1 | 7 | `vs/workbench/browser/parts/editor/editorTypePicker` |
| 1 | 10 | `vs/workbench/contrib/chat/browser/widget/input/modelPicker/modelPickerConfiguration` |
| 1 | 3 | `vs/workbench/contrib/chat/browser/promptTimeline/promptTimelineStickyHeader` |
| 1 | 14 | `vs/workbench/contrib/chat/browser/chatStatus/codexStatusDashboard` |
| 1 | 4 | `vs/sessions/contrib/sessionInputBanners/browser/sessionInputBannerWidget` |
| 1 | 3 | `vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostDownloadProgress` |
| 1 | 40 | `vs/workbench/contrib/chat/browser/aiCustomization/embeddedAgentPluginDetail` |
| 1 | 162 | `vs/workbench/contrib/chat/browser/aiCustomization/aiCustomizationManagementEditor` |
| 1 | 5 | `vs/workbench/contrib/chat/browser/widget/input/modelPicker/modelPickerModelConfig` |
| 1 | 13 | `vs/workbench/contrib/chat/browser/widget/input/modelPicker/modelPickerCard` |
| 1 | 2 | `vs/sessions/contrib/canvases/electron-browser/sessionCanvasActions` |
| 1 | 2 | `vs/sessions/contrib/changes/browser/sessionChangesEditorInput` |
| 1 | 45 | `vs/sessions/contrib/chat/browser/sessionComparisonResult` |
| 1 | 52 | `vs/workbench/contrib/chat/browser/widget/chatContentParts/chatThinkingContentPart` |
| 1 | 9 | `vs/workbench/contrib/chat/browser/aiCustomization/customizationMarketplaceSourceWarnings` |
| 1 | 53 | `vs/workbench/contrib/chat/browser/widget/chatContentParts/chatQuestionCarouselPart` |
| 1 | 8 | `vs/platform/agentHost/common/openSessionLink` |
| 1 | 23 | `vs/workbench/contrib/chat/browser/widget/input/modelPicker/modelPickerTabbedWidget` |

## 4. Devin/Windsurf 专有源文件

| 缺失 | 总数 | 源文件 |
|---:|---:|---|
| 0 | 24 | `vs/workbench/contrib/devinCloudSaveNotices/electron-browser/devinCloudSaveNotices.contribution` |
| 0 | 14 | `vs/workbench/contrib/windsurfPullRequest/browser/pullRequest.contribution` |
| 0 | 12 | `vs/platform/windsurfChatClient/electron-main/chatClientPreviewMainService` |
| 0 | 4 | `vs/platform/theme/common/colors/windsurfDiffColors` |
| 0 | 55 | `vs/workbench/contrib/windsurfDesktopShell/browser/desktopShellMenubar` |
| 0 | 7 | `vs/workbench/contrib/windsurfAgentWindow/browser/windsurfAgentWindowActions` |
| 0 | 8 | `vs/workbench/contrib/windsurfFeedback/browser/windsurfFeedback.contribution` |
| 0 | 5 | `vs/workbench/contrib/windsurfMcpService/browser/windsurfMcp.contribution` |
| 0 | 5 | `vs/platform/windsurfChatClient/common/chatClientPreview` |
| 0 | 16 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapViewer.contribution` |
| 0 | 12 | `vs/workbench/contrib/windsurfCascadeView/browser/cascadeView.contribution` |
| 0 | 4 | `vs/workbench/contrib/devinCloudFiles/browser/devinCloudFilesStatusView` |
| 0 | 5 | `vs/workbench/contrib/windsurfDesktopShell/browser/desktopShellAppControls` |
| 0 | 3 | `vs/workbench/contrib/windsurfDesignTokenEditor/browser/designTokenEditor.contribution` |
| 0 | 23 | `vs/workbench/contrib/windsurfDesktopShell/browser/devinWebappCommands` |
| 0 | 13 | `vs/platform/theme/common/colors/windsurfCustomColors` |
| 0 | 12 | `vs/workbench/contrib/windsurfMigration/electron-browser/windsurfMigration.contribution` |
| 0 | 2 | `vs/workbench/contrib/windsurfAcpService/browser/windsurfAcpService` |
| 0 | 4 | `vs/workbench/contrib/windsurfCascadeView/browser/cloudSessionWorkspaceEditorInput` |
| 0 | 21 | `vs/workbench/contrib/windsurfAcpService/browser/acpRemoteHostActions` |
| 0 | 10 | `vs/workbench/contrib/windsurfSettingsPage/browser/windsurfSettingsPage.contribution` |
| 0 | 5 | `vs/workbench/browser/windsurfSaveFile` |
| 0 | 11 | `vs/workbench/contrib/windsurfChatClient/electron-browser/chatClientModuleSelection.contribution` |
| 0 | 11 | `vs/platform/windsurfChatClient/electron-main/chatClientPreviewDownload` |
| 0 | 6 | `vs/workbench/contrib/windsurfOnboarding/browser/windsurfOnboarding.contribution` |
| 0 | 3 | `vs/workbench/contrib/windsurfDesktopShell/browser/devinWebappEditors` |
| 0 | 6 | `vs/workbench/contrib/windsurfAcpService/browser/acpSessionsQuickAccess` |
| 0 | 2 | `vs/workbench/contrib/windsurfCascade/browser/windsurfCascadeMainThreadCommands` |
| 0 | 7 | `vs/workbench/services/devinCloudFiles/browser/devinCloudEditorError` |
| 0 | 6 | `vs/platform/windsurfSvg/browser/windsurfCodicons` |
| 0 | 1 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapHomeEditorInput` |
| 0 | 2 | `vs/workbench/contrib/windsurfAgentWindow/electron-browser/agentWindowReveal` |
| 0 | 5 | `vs/workbench/contrib/windsurfAgentWindow/browser/cloudSessionEditorWindow` |
| 0 | 4 | `vs/workbench/contrib/windsurfDatadogRum/browser/datadogRum.contribution` |
| 0 | 1 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapBookmarkDecorationService` |
| 0 | 1 | `vs/workbench/contrib/windsurfPlanEditor/browser/planEditor.contribution` |
| 0 | 2 | `vs/workbench/contrib/windsurfAcpService/browser/windsurfAcp.contribution` |
| 0 | 5 | `vs/workbench/contrib/windsurfStatusBarSettingsService/browser/windsurfStatusBarSettingsPanel` |
| 0 | 1 | `vs/workbench/contrib/windsurfAgentWindow/electron-browser/agentWorkspacePrewarm` |
| 0 | 2 | `vs/workbench/contrib/windsurfCodeMapViewer/browser/codeMapExportAction` |
| 0 | 1 | `vs/workbench/contrib/windsurfDesktopShell/browser/desktopShell.contribution` |
| 0 | 1 | `vs/workbench/contrib/windsurfCascade/browser/windsurfCascade.contribution` |
| 0 | 1 | `vs/workbench/contrib/windsurfCascadeView/browser/snippetEditorPane` |
| 0 | 2 | `vs/workbench/contrib/windsurfCustomAppIcon/browser/windsurfAppIconCustomization.contribution` |
| 0 | 4 | `vs/workbench/contrib/windsurfAgentWindow/browser/devinSessionSshWindow` |
| 0 | 3 | `vs/workbench/contrib/windsurfDesktopShell/browser/createDevinHost` |
| 0 | 2 | `vs/platform/windsurfAuth/common/windsurfAuth` |
| 0 | 1 | `vs/workbench/contrib/windsurfStatusBarSettingsService/browser/tabs/keybindingTab` |
| 0 | 1 | `vs/workbench/contrib/windsurfCascadeView/browser/readOnlyDiffContentProvider` |
| 0 | 2 | `vs/workbench/contrib/windsurfDesktopShell/browser/devinWebappKeybindingEditing` |
| 0 | 1 | `vs/workbench/contrib/windsurfAgentWindow/electron-browser/windsurfAgentWindowActions` |

专有文件合计: 51 个文件, 全部 key 359, 其中缺中文 0

## 5. 缺中文的 Devin/Windsurf 字符串样例 (前 60)

| 源文件 | 英文原文 |
|---|---|

## 6. 完全缺中文的源文件 (语言包零覆盖)

共 0 个文件。前 30：


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
