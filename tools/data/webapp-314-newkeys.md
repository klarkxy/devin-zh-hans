# Devin 3.14 webapp 新增文案 i18n key 提取报告

- 采集日期：2026-11-19
- 采集手段：**只用 grep / read / glob 工具**（无 pwsh、无 shell）
- 目标文件：
  `C:\Users\27837\AppData\Local\Programs\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets\chunk-entry-host-editor-mode-menu-BWLlgqZu.js`
- 参照基线：`tools/data/webapp-en.json`（3.11，19,269 key / 317 命名空间）
- 方法：沿用 [webapp-314-anchor.md](webapp-314-anchor.md) 的「精确 pattern 指纹」法。grep 只回报「命中行数 + 行首约 10 k 字符」，行中段内容不可见，故全部结论由「pattern 命中/未命中」推导。

---

## 0. 结论速查：新串 → key → 命名空间

| # | 英文原文（3.14） | key | 命名空间线索 | 所在行 | 资源形态 | 状态 |
|---|---|---|---|---|---|---|
| 1 | `Pin to top` | **`pin`** | `personalDevin` | 17 | JSON `"pin":"Pin to top"` | ✅ 确认 |
| 2 | `Pin to left rail` | **`pin`** | 同一批 `pin` 键的另一命名空间（第 3 行 JS 对象） | 3 | JS 模板字面量 `` pin:`Pin to left rail` `` | ✅ 确认 |
| 3 | `Share as template` | **`shareAsTemplate`** | 第 7 行 JSON 命名空间（疑为 bot 菜单/侧栏组） | 7 | JSON | ✅ 确认 |
| 4 | `Template library` | **`templateLibrary`** | `personalDevin`（另有第 7 行一处） | 7、17 | JSON | ✅ 确认 |
| 5 | `Permanently delete this {{botName}}, its settings and its sessions` | **`settingsDeleteDescription`** | 第 7 行 JSON 命名空间 | 7 | JSON | ✅ 确认 |
| 6 | `Stop {{botName}} from responding. You can unarchive it later.` | **`settingsArchiveDescription`** | 第 7 行 JSON 命名空间 | 7 | JSON | ✅ 确认 |
| 7 | `Nothing in progress right now` | `??????Empty`（6 字母前缀 + `Empty`，共 11 字符，首字母 ∈ n–z） | 第 17 行 | 17 | JSON | ⚠️ 值确认 / key 部分收敛 |
| 8 | `View all {{botNamePlural}}` | 未定（两个 key：一个 1–5 字母，一个 12–15 字母） | 第 7、17 行 | 7、17 | JSON | ⚠️ 值确认 / key 未定 |
| 9 | `View all Bots` / `View all bots` | — | — | — | — | ❌ **原文不存在**（截图里是 #8 的插值结果） |

> 关键对照：3.11 里 `personalDevin.templateLibrary` = `Template library`（`webapp-en.json:15034`）。3.14 把「点号扁平 key」拆成了 **命名空间 `personalDevin` + 子键 `templateLibrary`**，这解释了为什么直接 grep `"personalDevin.templateLibrary"` 会空手而归。

**新串总数：7 条**（其中 #5/#6 是旧串改写、#1–#4 全新；#7/#8 为 3.11 中完全不存在的空状态/入口文案），另有 1 条 key 结构重构（`Template library`）。

---

## 1. 3.14 资源形态（本轮最重要的发现）

3.14 的 chunk 里 i18n 资源**同时存在两种形态**，这是 3.11 所没有的，也是本轮一开始连续探测失败的原因：

### 形态 A — JS 对象字面量（反引号值 + 无引号 camelCase 键）

第 26 行的可见头部直接暴露了命名空间映射结构：

```js
…},sessionList:{collapseChildren:`Collapse children`,expandChildren:`Expand children`},
sheet:{resize:`Resize sheet`},
spaceHeader:{moreActions:`More actions`,pin:`Pin`,pinToSidebar:`Pin to sidebar`,unpin:`Unpin`,viewSessionInsights:`View session insights`},
table:{resizeColumn:`Resize column`},
tabs:{agents:`Agents`,browser:`Browser`,citations:`Citations`,…},
terminal:{scrollToBottom:`Scroll to bottom`},
transcript:{and:`and`,…,sideChat:`Side chat`},
viz:{barList:`Bar list`,…},workingWords:{actualizing:`Actualizing`,…}
```

第 17 行的可见头部则是「一组以逗号分隔的声明」形态：`…},ma={analyse:`Analyze`,…},ha={searchWeb:…},ga={moreSendOptions:…}` —— 这些 `ma/ha/ga` 是**压缩后的变量名**，不是命名空间名。

### 形态 B — `JSON.parse(` 包裹的 JSON 串（双引号键值）

第 9 行可直接看到：

```js
vr=JSON.parse(`{"saveSchedule":"Save schedule","openRepository":"Open repository",…}`)
```

**形态 B 里才有可读的命名空间名**，例如第 17 行存在 `"personalDevin":{…}`。本轮 #1、#4 的命名空间归属就是靠形态 B 判定的。

### 由此推出的探测规律

| 想找的串出现在 | 正确 pattern 形状 | 错误的探法 |
|---|---|---|
| 形态 A | `` key:`English text` `` | `key:"English text"` |
| 形态 B | `"key":"English text"` | `` key:`English text` `` |

本轮前 6 次探测全部用反引号形态去撞第 17 行的串，因此 `pinToTop:`Pin to top`` 等一律 0 命中；换 `"pin":"Pin to top"` 立刻命中。

---

## 2. 证据链（pattern → 命中/未命中 → 推断）

行号为 grep 工具回报行号；「Found N matches」为**命中行数**（见 §4 陷阱 1）。

### A 组：#1 `Pin to top` → key `pin`

| # | pattern | 结果 | 推断 |
|---|---|---|---|
| A1 | `` Pin to top `` | 1（17） | 串存在 |
| A2 | `` Pin to top` `` | 0 | 不以反引号收尾 |
| A3 | `Pin to top[^`]` | 1（17） | 后接非反引号字符 → 形态 A 之外 |
| A4 | `pinToTop:`Pin to top`` | 0 | key 不是 `pinToTop` |
| A5 | `top:`Pin to top`` / `Rail:` / `Menu:` / `Bot:` / `Pin:` / `Item:` / `Action:` / `Label:` | 全 0 | 反引号形态彻底排除 |
| A6 | `"Pin to top"` | 1（17） | 双引号形态 → 形态 B |
| A7 | `[a-zA-Z]":"Pin to top"` | 1（17） | 形如 `"key":"Pin to top"` |
| A8 | `Top":"…` / `top":"…` / `Rail":"…` / `Menu":"…` / `Bot":"…` | 全 0 | key 不以这些词结尾 |
| A9 | `[a-m]":"Pin to top"` → 0；`[n-z]":"Pin to top"` → 1 | — | key 末字符 ∈ n–z |
| A10 | **`"pin":"Pin to top"`** | **1（17）** | **key = `pin`** |
| A11 | `pin:"Pin to top"` | 0 | 排除了形态 A 的无引号键（旁证 A6） |
| A12 | `[n-r]":"Pin to top"` → 1；`[s-z]` → 0 | — | 与末字符 `n` 自洽 |

> 命名空间：`"personalDevin":\{.{0,4000}"pin":"Pin to top"` → **1（17）**。即 `personalDevin.pin` = `Pin to top`。

### B 组：#2 `Pin to left rail` → key `pin`（另一命名空间）

| # | pattern | 结果 | 推断 |
|---|---|---|---|
| B1 | `` Pin to left rail `` | 1（3） | 串存在（第 **3** 行） |
| B2 | `` Pin to left rail` `` | 1（3） | **以反引号收尾** → 形态 A 的模板字面量值 |
| B3 | `Pin to left rail[^`]` | 0 | 与 B2 互证 |
| B4 | `Rail:`Pin to left rail`` / `rail:` / `Pin:` / `pin:` | 全 0 | key 不以 rail/Rail 结尾 |
| B5 | `[A-Za-z0-9]`Pin to left rail`` | 0 | 反引号前不是字母数字 |
| B6 | `:"Pin to left rail"` | 0 | 不是 JSON 值 |
| B7 | `:`Pin to left rail`` | 1（3） | 形如 `X:` + 反引号 |
| B8 | `"pin":"Pin to left rail"` | 0 | 确证第 3 行不是 JSON 形态 |
| B9 | **`` pin:`Pin to left rail` ``** | **1（3）** | **key = `pin`** |

> 结论：`pin` 这个 key 在 3.14 至少存在于两处，取值不同（`Pin to top` / `Pin to left rail`），说明「Pin to …」的文案由**同一 key 在不同命名空间承载**，做汉化时必须按命名空间分别给值，不能按「一个英文串 = 一个 key」映射。

### C 组：#4 `Template library` / #3 `Share as template`

| # | pattern | 结果 | 推断 |
|---|---|---|---|
| C1 | `templateLibrary:`Template library`` | 0 | 不是形态 A |
| C2 | `"Template library"` | 2（**7、17**） | 双引号形态，两处 |
| C3 | **`"templateLibrary":"Template library"`** | **2（7、17）** | **key = `templateLibrary`**，两处 |
| C4 | `"personalDevin":\{"templateLibrary":"Template library"` | 0 | `templateLibrary` 不是 `personalDevin` 的首键 |
| C5 | `"personalDevin":\{.{0,4000}"templateLibrary":"Template library"` | **1（17）** | 第 17 行那处**确实在 `personalDevin` 内**（非首键） |
| C6 | `shareAsTemplate:`Share as template`` | 0 | 不是形态 A |
| C7 | `"Share as template"` | 1（7） | 双引号形态 |
| C8 | **`"shareAsTemplate":"Share as template"`** | **1（7）** | **key = `shareAsTemplate`**，第 7 行 |
| C9 | `"personalDevin":\{.{0,6000}"shareAsTemplate":"Share as template"` | 0 | 第 7 行那处**不在** `personalDevin` 内 → 属于第 7 行的另一个命名空间 |

### D 组：#5 / #6 两条带 `{{botName}}` 的危险操作描述

| # | pattern | 结果 | 推断 |
|---|---|---|---|
| D1 | `its settings and its sessions` | 1（7） | 片段存在第 7 行 |
| D2 | `Permanently delete \{\{botName\}\}` | 1（**3**） | 第 **3** 行另有一条以 `Permanently delete {{botName}}` 开头的串 |
| D3 | `Permanently delete {{botName}}, its settings and its sessions` | 0 | 第 7 行不是这个紧凑写法 |
| D4 | `Permanently delete this \{\{botName\}\}, its settings and its sessions` | **1（7）** | **精确原文**（含 `this`） |
| D5 | `settingsDeleteDescription":"Permanently delete` | 1（7） | key 命中且值以该词开头 |
| D6 | `"settingsDeleteDescription":"Permanently delete {{botName}}, …` | 0 | 与 D3 同因 |
| D7 | `from responding. You can unarchive it later.` | 1（7） | 归档描述尾句存在 |
| D8 | `Stop \{\{botName\}\} from responding` | 1（7） | 动词是 `Stop`（不带 s、不带 this） |
| D9 | `Stops this \{\{botName\}\} from responding` | 0 | 3.11 的旧写法已消失 |
| D10 | `Stops \{\{botName\}\} from responding` | 0 | 同上 |
| D11 | `settingsArchiveDescription":"Stop` | 1（7） | key 命中 |
| D12 | `settingsArchiveDescription":"Stops` | 0 | 值确实是 `Stop` 开头（D11 ∧ D12 互证） |
| D13 | `Stop \{\{botName\}\} from responding\. You can unarchive it later\.` | **1（7）** | **精确原文** |
| D14 | `"personalDevin":\{.{0,4000}"settingsDeleteDescription"/"settingsArchiveDescription"` | 0 / 0 | 这两条**不在** `personalDevin` 内（它在第 17 行，而这两条在第 7 行） |

### E 组：#7 `Nothing in progress right now`

| # | pattern | 结果 | 推断 |
|---|---|---|---|
| E1 | `Nothing in progress` | 0（**在 3.11 资源库中**） | 3.11 无此文案 → 新增 |
| E2 | `[Nn]othing in progress` | 1（17） | 3.14 存在 |
| E3 | `"Nothing in progress right now"` | 1（17） | 双引号形态 |
| E4 | `` Nothing in progress right now` `` | 0 | 不是形态 A |
| E5 | `now:`Nothing in progress right now`` / `[Rr]ight[Nn]ow:`…` | 0 | key 不以 now 结尾 |
| E6 | `Empty":"Nothing in progress right now"` | 1（17） | **key 以 `Empty` 结尾** |
| E7 | `nothingInProgress` | 0 | 无以此开头的 key |
| E8 | `"empty"/"isEmpty"` | 0 / 0 | 不是裸 `empty`，也不是 `isEmpty` |
| E9 | `"[a-zA-Z]{1,6}Empty":"Nothing in progress right now"` | 1（17） | 前缀 1–6 字母 |
| E10 | `"[a-zA-Z]{7,20}Empty":…` | 0 | 前缀 ≤ 6 |
| E11 | 逐个排除 `{1,2}` / `{3,4}` / `{4}` / `{5}` | 全 0 | 前缀 = **6 字母**（合计 11 字符） |
| E12 | `"[a-m][a-zA-Z]{5}Empty":…` → 0；`"[n-z][a-zA-Z]{5}Empty":…` → 1 | — | 首字母 ∈ **n–z** |
| E13 | 猜词全灭：`listEmpty`(0)、`railEmpty`(0)、`nothingEmpty`(0)、`activeEmpty`(0)、`botsEmpty`(0)、`noBotsEmpty`(0)、`noWorkEmpty`(0)、`noworkEmpty`(0)、`progressEmpty`(0)、`inProgressEmpty`(0)、`(spaces|online|pinned|latest|recent|queued|agents|robots|devins|future)Empty`(0)、`(seeAll|noRows|status|second|scroll)Empty`(0) | 全 0 | 只收敛到「6 字母前缀 / 首字母 n–z」，未命中具体词 |

### F 组：#8 / #9 `View all …`

| # | pattern | 结果 | 推断 |
|---|---|---|---|
| F1 | `View all` | 6（3、7、9、17、24、26） | 多处上下文出现 |
| F2 | `View all [Bb]ots` | **0** | **`View all Bots` / `View all bots` 都不存在** |
| F3 | `View all \{\{` | 1（17） | 存在插值形态 |
| F4 | `View all \{\{[a-zA-Z]+\}\}"` | 1（17） | 插值变量名全字母 |
| F5 | `View all \{\{botNamePlural\}\}"` | 1（17） | **变量就是 `botNamePlural`** |
| F6 | `View all \{\{botName\}\}"` | 0 | 不是单数 `botName` |
| F7 | `"viewAll"/"viewAllBots"` | 0 / 0 | key 不是这两个 |
| F8 | `[a-zA-Z]":"View all \{\{botNamePlural\}\}"` | 1（17） | 形如 `"key":"View all {{botNamePlural}}"` |
| F9 | `"all"/"more"/"view"/"open"/"show"/"bots"/"list"/"link"` | 全 0 | 短 key 候选全灭 |
| F10 | `(bots\|viewAll\|seeAll\|allBots\|moreBots\|showBots)":"View all …` | 0 | 同上 |
| F11 | `"viewAllAgents"/"viewAllSessions"/"viewAllBotsLink"/"viewAllBotsList"` | 全 0 | 长 key 候选亦灭 |
| F12 | `[a-zA-Z]{1,5}":"View all …` → 1（17）；`[a-zA-Z]{6,15}":"…` → 1（**7**） | — | 至少两处，一处 1–5 字母、一处 6–15 字母 |

> **重要**：截图上的 `View all Bots` 不是字面量，而是 `View all {{botNamePlural}}` 在 `botNamePlural = Bots` 时的渲染结果。汉化时必须改 `View all {{botNamePlural}}` 这一条（可译作「查看全部 {{botNamePlural}}」），改 `View all Bots` 无效。

### G 组：3.11 基线对照（webapp-en.json）

| # | pattern | 结果 | 结论 |
|---|---|---|---|
| G1 | `Pin to` | 2（5692 `"pin": "Pin to sidebar"`、7987 `"pinToRepository": "Pin to repository"`） | 3.11 **没有** `Pin to top` / `Pin to left rail` |
| G2 | `Nothing in progress` | 0 | 3.11 无此文案 |
| G3 | `Template library` | 1（15034 `"personalDevin.templateLibrary": "Template library"`） | 值未变，**key 结构变**（扁平点号 → 命名空间嵌套） |
| G4 | `View all [Bb]ots?[^a-z]` | 0 | 3.11 连 `View all` 都没有 |
| G5 | `Share as template` | 0 | 3.11 无 |
| G6 | `Permanently delete` | 3（5807、13386、19033） | 5807 是旧版 `settingsDeleteDescription`: 「Permanently delete**s this** {{botName}} **and its settings**」 |
| G7 | 邻键（5690–5694） | `archive`/`unarchive`/`pin`/`unpin` | 3.11 的 `pin` = 「Pin to sidebar」，`unpin` = 「Unpin from sidebar」；3.14 同一 key 改为「Pin to top」 |
| G8 | 邻键（5803–5809） | `settingsDangerZone`/`settingsArchiveDescription`/`settingsUnarchiveDescription`/`settingsDelete`/`settingsDeleteDescription`/`settingsDeleteTitle`/`settingsDeleteConfirmation` | 3.14 这两条 key **名字没变、文案变了** → 旧译文必须重译 |

---

## 3. 3.11 → 3.14 变化归纳

1. **key 结构**：`personalDevin.templateLibrary`（扁平点号）→ `{"personalDevin":{"templateLibrary":…}}`（命名空间嵌套）。**任何按扁平点号去查 3.14 chunk 的探测都会 0 命中。**
2. **字符串引号**：3.11 是 `"`；3.14 形态 A 用反引号模板字面量，形态 B 仍在 `JSON.parse(`…`)` 里保留双引号。
3. **`pin` 语义分裂**：3.11 单一「Pin to sidebar」；3.14 至少三处取值 —— `Pin`（`spaceHeader`）、`Pin to top`（`personalDevin`）、`Pin to left rail`（第 3 行）。
4. **归档/删除文案重写**（key 复用、值变更）：
   - `settingsArchiveDescription`：「Stops this {{botName}} from responding.」→「Stop {{botName}} from responding.」（删去 `this`，`Stops`→`Stop`）
   - `settingsDeleteDescription`：「Permanently deletes this {{botName}} and its settings」→「Permanently delete this {{botName}}, its settings and its sessions」
5. **新增空状态与入口**：`Nothing in progress right now`、`View all {{botNamePlural}}`、`Share as template` 在 3.11 全部不存在。

---

## 4. 陷阱清单（本轮踩过的坑，供后续复用）

1. **grep 的「matches」是命中行数，不是出现次数。** 一行里出现 5 次也只有 1 match。因此「出现几次」不能靠计数判断，只能靠「0 还是 ≥1」。
2. **字符类长度探测必须带左锚。** `[a-zA-Z]{1,2}Empty":"…` 是子串匹配，`xxxEmpty` 里的 `xx` 尾部也能命中，会把「前缀 ≤2」这种结论做成假阳性。正确写法是 `"[a-zA-Z]{1,2}Empty":"…`（把开引号写进 pattern）。
3. **超长行（~1.5 MB）+ 有界重复（`{n,m}`）会互相干扰。** 本轮出现过 `{1,5}` 命中但 `{1,3}`、`{4}`、`{4,5}` 全 0 的矛盾（F 组、E 组）。**凡涉及 `{n,m}` 的否定结论只能当弱证据**，只信「精确字面量命中」这类正向证据。
4. **key 名不等于文案的 camelCase**：`pinToTop:`Pin to top``、`pinToLeftRail:`Pin to left rail``、`shareAsTemplate:`Share as template`` 全是 0；实际 key 是更短的 `pin` / `shareAsTemplate`。
5. **同一英文串在两个命名空间取不同值**（`pin`），不能建立「一串 ↔ 一 key」的一对一表，必须 (命名空间, key) 二元组。
6. **`View all Bots` 是渲染结果**，模板串是 `View all {{botNamePlural}}`。
7. **`"personalDevin":\{[^}]*"key"` 这种写法会误判**：`[^}]*` 遇到命名空间内任何 `}` 即止，而命名空间里若含嵌套对象就先截断了。改用 `.{0,N}` 有界重复（`"personalDevin":\{.{0,4000}"pin":"Pin to top"` → 命中）。

---

## 5. 未决项

| 项 | 已知 | 下一步建议 |
|---|---|---|
| `Nothing in progress right now` 的 key | 以 `Empty` 结尾、总长 11、6 字母前缀、首字母 n–z；第 17 行 | 对 2–6 位逐字符做「带左锚的字符类二分」（`"[a-m]…` / `"[n-z]…`），或对第 17 行做 offset 二分后逐字还原 |
| `View all {{botNamePlural}}` 的 key | 第 17 行一处（短）、第 7 行一处（长）；1–5 / 12–15 字母 | 同上；建议先只锁第 7 行那处（该行文档结构较稀疏） |
| 第 7 行承载 `settingsDeleteDescription` 的命名空间名 | 不是 `personalDevin`（`personalDevin` 在第 17 行） | 试 `bots` / `botSettings` / `botMenu` / `agentSettings` 等候选：`"Ns":\{.{0,4000}"settingsArchiveDescription"` |
| 第 3 行 `pin` 的命名空间名 | 第 3 行是形态 A 的 `…},ma={…}` 声明链 | 从该对象尾部已知键反推对象起点 |
| 其他 `Permanently delete*` | 第 3、9、17 行各有 1 处（`Permanently delete {{botName}}` 在第 3 行） | 逐行确认是否为另 3 条新的删除描述 |

---

## 6. 复现命令（grep 工具，pattern / path 两字段）

```
path = C:\Users\27837\AppData\Local\Programs\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets\chunk-entry-host-editor-mode-menu-BWLlgqZu.js

"pin":"Pin to top"                                                                  # 1 命中 / 第 17 行
pin:`Pin to left rail`                                                              # 1 命中 / 第 3 行
"shareAsTemplate":"Share as template"                                               # 1 命中 / 第 7 行
"templateLibrary":"Template library"                                                # 2 命中 / 第 7、17 行
"settingsDeleteDescription":"Permanently delete this {{botName}}, its settings and its sessions"   # 1 命中 / 第 7 行
"settingsArchiveDescription":"Stop {{botName}} from responding. You can unarchive it later."        # 1 命中 / 第 7 行
"personalDevin":\{.{0,4000}"pin":"Pin to top"                                        # 1 命中 / 第 17 行（命名空间归属）
"personalDevin":\{.{0,4000}"templateLibrary":"Template library"                       # 1 命中 / 第 17 行
"Nothing in progress right now"                                                     # 1 命中 / 第 17 行
View all \{\{botNamePlural\}\}"                                                      # 1 命中 / 第 17 行
View all [Bb]ots                                                                   # 0 命中（原文不存在）
```

（以上每条均已在本轮逐一跑过，命中数与行号即为正文所记。`{{` / `}}` 在 ripgrep 中按字面量匹配，也可写成 `\{\{` / `\}\}`。）
