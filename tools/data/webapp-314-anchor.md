# Devin 3.14 webapp i18n 注入锚点

- 采集日期：2026-11-19
- 采集手段：只用 grep / read / glob 工具（无 pwsh、无 shell，符合沙箱约束）
- 目标文件：
  `C:\Users\27837\AppData\Local\Programs\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets\chunk-entry-host-editor-mode-menu-BWLlgqZu.js`
- 文件规模：39 MB 级压缩 JS，单行 ~1.5 MB；grep 输出被截断到行首约 10 k 字符，**任何位于行中段的匹配都看不见内容**，只看得见 "Found N matches" 与行号。
- 因此全部结论用「渐进 pattern + 字符类二分」得到：每个 pattern 只回答「文件里是否存在这样的子串」，靠逐步收窄字符类把标识符一个字一个字逼出来。

## 0. 结论速查（3.11 → 3.14 对照）

| 角色 | 3.11（旧，参照） | 3.14（新，实测） | 精确字符串 | 所在行 |
|---|---|---|---|---|
| i18next 实例 | `Mt` | **`at`** | `at` | 26 |
| i18next 模块（`.use()` 的实参） | `Mn` | **`pd`** | `at.use(pd)` | 26 |
| 语言检测/初始化函数 | `Eu` | **`Jd`** | `at.isInitialized\|\|Jd()` | **38** |
| en 资源根变量 | `mu` | **`mu`**（名字没变） | `translation:t?JSON.parse(JSON.stringify(mu)):mu` | 26 |
| review 资源根变量 | `hu` | **`hu`**（名字没变） | `,review:hu}` | 26 |
| resources 变量 | `n` | **`n`** | `n={en:{translation:…,review:hu}}` | 26 |
| 深拷贝开关 | `t` | **`t`** | `translation:t?…:mu` | 26 |

一句话：**混淆名换了一批，但 `mu` / `hu` / `n` / `t` 这几个资源侧的名字与 3.11 完全一致**，只有 i18next 实例（`Mt→at`）、i18next 模块（`Mn→pd`）、初始化函数（`Eu→Jd`）换了。

## 1. 可直接用于 patch 的唯一串（已逐条 grep 验证唯一性）

以下 4 条在整文件内均只命中 1 次，可直接当作查找串使用。

### P1 — 初始化守卫（旧 `Mt.isInitialized||Eu()` 的等价物）

```
at.isInitialized||Jd()
```

验证：`[^A-Za-z0-9_$.]at\.isInitialized\|\|Jd\(\)` → 1 处，第 **38** 行。
左边界 `[^A-Za-z0-9_$.]` 用来证明 `at` 是完整标识符（不是 `xat` 之类的尾巴）；实测 `at.isInitialized` 全文件只出现这一次。
该串前面紧邻的字符是 `{`、`(` 或 `}` 之一（`[,;]` 两侧都不命中），即它处在一个表达式/块内部，不是语句首。

### P2 — i18next init 调用（旧 `Mt.use(Mn).init({resources:n,lng:"en",…})` 的等价物）

```
at.use(pd).init({resources:n,lng:`en`,fallbackLng:`en`,ns:[`translation`,`review`],defaultNS:`translation`,interpolation:{escapeValue:!1,
```

- 第 **26** 行，整串是 1 次命中（分段验证见 §2 的 B 组 / C 组）。
- 字符串改成了反引号模板字面量（3.11 是双引号），这是 3.14 与 3.11 最直观的形态差异。
- `interpolation:{escapeValue:!1,` 之后还有键（`escapeValue` 后面紧跟逗号，另有键名，见 §4 未决项）。
- 该调用前面紧邻 `,` 或 `;`（`[,;]at\.use\(pd\)\.init\(\{resources:n,lng:`en`` → 1 命中），说明它和旧版一样是逗号表达式里的一条语句。

### P3 — en/review 资源对象定义

```
n={en:{translation:t?JSON.parse(JSON.stringify(mu)):mu,review:hu}}
```

整串 1 次命中，第 **26** 行。

### P4 — en 资源根变量

```
mu
```

只在 P3 的三元里出现（`t?JSON.parse(JSON.stringify(mu)):mu`）；`mu={` 在全文件 **0 命中**，且 `as mu[,}]` 有命中（见 §4 未决项），说明 `mu` 是**被 import 进来的绑定**，英文资源本体不在本行内联。

> ⚠️ 修正一个容易踩的假设：`resources:{en:{translation:` **不存在**（0 命中）。3.14 与 3.11 一样，资源对象是在 `n=` 处定义、init 里只写 `resources:n`。

## 2. 证据链（pattern → 命中/未命中 → 推断）

行号均为 grep 工具报的行号。命中数为 0 的行同样是证据（用于排除字符类）。

### A 组：定位 `isInitialized||XXX()` 的形态

| # | grep pattern | 结果 | 推断 |
|---|---|---|---|
| A1 | `isInitialized\|\|` | 2 处（26、38） | 文件里有两处，先不分线 |
| A2 | `isInitialized\|\|[A-Za-z_$]\(\)` | 0 | 不是单字符函数 |
| A3 | `isInitialized\|\|[A-Za-z_$][A-Za-z0-9_$]\(\)` | 1（38） | 是两字符函数，且目前只在 38 行 |
| A4 | `isInitialized\|\|[a-z][A-Za-z0-9_$]\(\)` | 0 | 首字母不是小写 |
| A5 | `isInitialized\|\|[A-Z][A-Za-z0-9_$]\(\)` | 1（38） | 首字母大写 |
| A6 | `isInitialized\|\|[A-M]…` | 1（38） | 首字母 ∈ A–M |
| A7 | `isInitialized\|\|[A-G]…` | 0 | 排除 A–G |
| A8 | `isInitialized\|\|[H-J]…` | 1（38） | 首字母 ∈ H–J |
| A9 | `isInitialized\|\|[H-I]…` | 0 | 首字母 = **J** |
| A10 | `isInitialized\|\|J[a-z]\(\)` | 1（38） | 第二字母小写 |
| A11 | `isInitialized\|\|J[a-m]\(\)` | 1（38） | ∈ a–m |
| A12 | `isInitialized\|\|J[a-f]\(\)` | 1（38） | ∈ a–f |
| A13 | `isInitialized\|\|J[a-c]\(\)` | 0 | ∈ d–f |
| A14 | `isInitialized\|\|J[d-e]\(\)` | 1（38） | ∈ d–e |
| A15 | `isInitialized\|\|Jd\(\)` | 1（38） | 第二字母 = **d** ⇒ 函数名 **`Jd`** |

### B 组：定位 init 调用的「实例名」与「模块名」

（为提速，A3 之后不再逐个字符穷举，而是「先定长度、再二分字符、用左边界类保证不误配」）

| # | grep pattern | 结果 | 推断 |
|---|---|---|---|
| B1 | `\.use\([A-Za-z_$][A-Za-z0-9_$]{0,3}\)\.init\(\{resources:` | 1（26） | `.use(X).init({resources:` 唯一 |
| B2 | `[^A-Za-z0-9_$.][A-Za-z_$][A-Za-z0-9_$]\.use\(…init\(\{resources:` | 1（26） | 实例名**恰好 2 字符**（左边界类排除"长名截尾"的误配） |
| B3 | `[^…][a-z][A-Za-z0-9_$]\.use\(…` | 1（26） | 首字母小写 |
| B4 | `[^…][a-m]…` / `[a-f]` / `[a-c]` / `[a-b]` / `[a]` | 1 / 1 / 1 / 1 / 1 | 首字母 = **a** |
| B5 | `[^…][a][a-z]\.use\(…` | 1（26） | 第二字母小写 |
| B6 | `[^…][a][a-m]…` | 0 | 第二字母 ∈ n–z |
| B7 | `[^…][a][t-z]…` | 1（26） | ∈ t–z |
| B8 | `[^…]at\.use\(…` | 1（26） | 实例名 = **`at`** |
| B9 | `at\.use\([A-Za-z_$][A-Za-z0-9_$]\)\.init\(\{resources:n,` | 1（26） | 模块名**恰好 2 字符** |
| B10 | `at\.use\([a-m]…` / `[A-M]` / `[N-Z]` / `[_$]` | 0 / 0 / 0 / 0 | 首字母不在这些集合 |
| B11 | `at\.use\([n-z]…` | 1（26） | 首字母 ∈ n–z |
| B12 | `at\.use\([n-s]…` | 1（26） | ∈ n–s |
| B13 | `at\.use\([n-p]…` | 1（26） | ∈ n–p |
| B14 | `at\.use\(n…` / `at\.use\(o…` | 0 / 0 | 首字母 = **p** |
| B15 | `at\.use\(p[a-z]\)…` | 1（26） | 第二字母小写 |
| B16 | `at\.use\(p[a-m]\)…` | 1（26） | ∈ a–m |
| B17 | `at\.use\(p[a-f]\)…` | 1（26） | ∈ a–f |
| B18 | `at\.use\(p[a-c]\)…` | 0 | ∈ d–f |
| B19 | `at\.use\(p[d-e]\)…` | 1（26） | ∈ d–e |
| B20 | `at\.use\(pd\)…` | 1（26） | 模块名 = **`pd`** |
| B21 | `[,;]at\.use\(pd\)\.init\(\{resources:n,lng:`en`` | 1（26） | 前面是 `,` 或 `;` |
| B22 | `at\.changeLanguage\(` | 1（26） | 旁证：`at` 确实是 i18next 实例（`changeLanguage` 是 i18next 独有 API） |

> 说明：B10 里刻意按 `[a-z]`/`[A-Z]`/`[_$]` 四类穷举，`[n-z]` 一度被漏测导致「四类全 0 却仍能命中」的假矛盾；补测 `[n-z]` 后自洽。这类"字符类漏一格"是渐进探测的主要坑，记在此处备查。

### C 组：还原 init 选项尾部

| # | grep pattern | 结果 | 推断 |
|---|---|---|---|
| C1 | `\.init\(\{resources:` | 1（26） | 唯一 |
| C2 | `\.init\(\{resources:[A-Za-z_$][A-Za-z0-9_$]{0,2},` | 1（26） | 资源实参是变量名 |
| C3 | `\.init\(\{resources:[A-Za-z_$],` | 1（26） | 该变量**恰好 1 字符** |
| C4 | `\.init\(\{resources:[a-m],` | 0 | 不是 a–m |
| C5 | `\.init\(\{resources:[n-z],` / `[n-s]` / `n` | 1 / 1 / 1 | 变量 = **`n`** |
| C6 | `at\.use\(pd\)\.init\(\{resources:n,lng:`en`` | 1（26） | `lng:`en``（反引号）紧跟其后 |
| C7 | `at\.use\(pd\)\.init\(\{…lng:`en`,fallbackLng:`en`,ns:[`translation`,`review`]` | 1（26） | 选项顺序与 3.11 完全一致 |
| C8 | `ns:\[`translation`,`review`\]`（全文件） | 1（26） | 命名空间仍是 `translation` + `review` |
| C9 | `defaultNS:`translation`,interpolation:` | 1（26） | `defaultNS` 之后是 `interpolation`（**没有** `returnNull`，该 pattern 0 命中） |
| C10 | `interpolation:\{escapeValue:!1,` | 1（26） | `escapeValue:!1` 后面还有键 |

### D 组：还原资源对象（`translation:` 三元）

| # | grep pattern | 结果 | 推断 |
|---|---|---|---|
| D1 | `translation:[A-Za-z_$][A-Za-z0-9_$]{0,3}\?JSON\.parse\(JSON\.stringify\(` | 1（26） | 三元结构仍在 |
| D2 | `translation:[A-Za-z_$]\?JSON\.parse` | 1（26） | 三元条件变量**恰好 1 字符** |
| D3 | `translation:[a-z]\?JSON\.parse` | 1（26） | 小写 |
| D4 | `[a-m]` → 0 / `[n-s]` → 0 / `[t-v]` → 1 / `[t-u]` → 1 / `t` → 1 | — | 条件变量 = **`t`** |
| D5 | `translation:t\?JSON\.parse\(JSON\.stringify\([A-Za-z_$]\)\):` | 0 | `stringify(` 的实参不是 1 字符 |
| D6 | `…\([A-Za-z_$][A-Za-z0-9_$]{0,3}\)\):` | 1（26） | 实参 1–4 字符 |
| D7 | `…\([a-z][A-Za-z0-9_$]\)\):` | 1（26） | 2 字符、小写开头 |
| D8 | `…\([a-m][…]\)\):` → 1；`[a-f]` → 0；`[g-j]` → 0；`[k-l]` → 0 | — | 首字母 = **m** |
| D9 | `…\(m[n-z]\)\):` → 1；`…\(mu\)\):` → 1 | — | 资源根 = **`mu`** |
| D10 | `\{en:\{translation:t\?JSON\.parse\(JSON\.stringify\(mu\)\):mu` | 1（26） | `{en:{translation:…:mu` 成立 |
| D11 | `:mu,review:[A-Za-z_$][A-Za-z0-9_$]{0,3}` → 1；`…[A-Za-z0-9_$]\}` → 1 | — | review 资源是 2 字符变量 |
| D12 | `:mu,review:hu\}` | 1（26） | review 资源根 = **`hu`** |
| D13 | `n=\{en:\{translation:t\?JSON\.parse\(JSON\.stringify\(mu\)\):mu,review:hu\}\}` | 1（26） | 整串成立（P3 全文） |

### E 组：假锚点排除

| # | grep pattern | 结果 | 说明 |
|---|---|---|---|
| E1 | `at\.isInitialized` | 1（**38**） | 只此一处 |
| E2 | `at\.isInitialized\|\|` | 1（38） | 同上 |
| E3 | `[A-Za-z_$]\.isInitialized\|\|[a-z]\.` | 1（**26**） | 26 行还有**另一个** `X.isInitialized\|\|y.`：左右都是**单字符**标识符，右边不是函数调用 |
| E4 | `isInitialized\|\|[a-z]\.init\(` | 0 | 26 行那处也不是 `.init(` 调用 |
| E5 | `isInitialized\|\|[a-z][A-Za-z0-9_$]{0,2}\(\)` | 0 | 26 行那处不是 `foo()` |
| E6 | `function Jd\(` | **2**（26、38） | `Jd` 在 26 行另有一个同名函数定义 → **同名不同作用域**，必须连上下文一起匹配 |

结论：真正对应 3.11 `Mt.isInitialized||Eu()` 的只有 **38 行的 `at.isInitialized||Jd()`**；26 行那处 `x.isInitialized||y.z` 是噪声（形态不同、右边不是 `Jd`）。

## 3. 结构重建（把压缩代码还原成可读形态）

```js
// —— 第 26 行（i18n 模块）——
const n = {
  en: {
    translation: t ? JSON.parse(JSON.stringify(mu)) : mu,   // t = 深拷贝/环境开关
    review: hu
  }
};

at.use(pd).init({                     // at = i18next 实例；pd = i18next 模块
  resources: n,
  lng: `en`,
  fallbackLng: `en`,
  ns: [`translation`, `review`],
  defaultNS: `translation`,
  interpolation: { escapeValue: !1, /* …还有 1+ 个键，未逐字还原… */ }
});

// 同文件第 26 行还出现 at.changeLanguage( … ) —— 旁证 at 就是那个 i18next 实例

// —— 第 38 行（另一模块）——
function Jd() { /* 语言检测/初始化（3.11 的 Eu） */ }
// …
({ at.isInitialized || Jd(), … })     // 旧版 Mt.isInitialized || Eu()
```

与 3.11 的结构差异仅有三处：①字符串字面量从 `"` 变 `` ` ``；②`Mt/Mn/Eu` → `at/pd/Jd`；③`isInitialized||` 守卫与 init 调用**不在同一行**（26 行 vs 38 行），旧版是相邻两条语句。

## 4. 注入建议

产物侧结论：只要改 **P2 与 P3** 两处即可完成「加中文 + 切语言」，不需要碰运行时。

### 方案 A（推荐）——改 init 文本

1) 资源注入，查找 P3：

```
n={en:{translation:t?JSON.parse(JSON.stringify(mu)):mu,review:hu}}
```

替换为（把中文资源以 `ZH` 常量注入，保持 `en` 原样作为回退）：

```
n={en:{translation:t?JSON.parse(JSON.stringify(mu)):mu,review:hu},zh:{translation:ZH_TRANSLATION,review:hu}}
```

2) 语言切换，查找 ``lng:`en`,fallbackLng:`en` ``（唯一）替换为：

```
lng:`zh-Hans`,fallbackLng:`en`
```

要点：
- `fallbackLng` **必须保留 `en`**，否则漏译 key 会直接回显 `namespace.key`。
- `zh` 的命名空间集合要与 `ns:[`translation`,`review`]` 对齐；`translation` 是主体（317 个命名空间 / 19,269 个叶子 key，见 [webapp.md](webapp.md)），`review` 是审阅界面那一小包。
- `mu` 是 import 绑定（`as mu[,}]` 有命中），若中文包要复用其 key 树，应以 `tools/data/webapp-en.json` 的解析结果为准，而不是在 JS 里内联巨型对象。

### 方案 B（不推荐）——运行时挂包

在守卫串 `at.isInitialized||Jd()` 之前插 `at.addResourceBundle(...)` / `at.changeLanguage(...)`：`at` 在第 38 行的作用域归属未证实（见下），且会在 minify 名变化时立刻失效；只在方案 A 的文本被上游改动时作为兜底。

## 5. 陷阱清单

1. **同名不同作用域**：`function Jd(` 在 26、38 行各出现一次；`at=` 在第 2 行（React 包内）也有局部同名变量。任何字符串替换都必须使用 §1 的完整锚点串，不能只替换 `Jd` / `at`。
2. **26 行有第二处 `isInitialized||`**（形态 `x.isInitialized||y.`，两侧均单字符），不要把它当成 i18n 守卫。
3. **`resources:{en:{translation:` 不存在**（0 命中）。资源对象在 `n=` 处定义，init 里是 `resources:n`。按旧版印象直接搜 `resources:{en:` 会空手而归。
4. **字符串是反引号**：`lng:`en``、`ns:[`translation`,`review`]`、`defaultNS:`translation``。用双引号版本（`lng:"en"`）搜不到。
5. **行号对不上**：任务简报说"26 行超长行"，但命中的 `isInitialized` 守卫落在**第 38 行**，说明该文件至少有 38 个逻辑行；按"行号 = 26"去找会错位。

## 6. 未决项（不影响注入，但值得记录）

- **init 选项尾部未逐字还原**：`interpolation:{escapeValue:!1,` 之后仍有键名（`[a-zA-Z_$]+:` 命中），但 `prefix/suffix/escape/skipOnVariables/unescapePrefix/formatSeparator` 逐个试均未命中，未继续穷举；这段不参与注入，保持原样即可。
- **`Jd` 的函数体未定位**：`function Jd\(\)\{.{0,120}at\.` 0 命中，说明它要么带参、要么是箭头/表达式定义，体内不含 120 字符内的 `at.`。它的语义（3.11 的 `Eu`）按位置推定，未做行为验证。
- **`at` / `mu` 是被 import 的绑定**：`as at[,}]`、`as mu[,}]` 均在 38 行命中；`at=pd`、`at=pd.`、`(var|let|const)[ ,]at=`、`[^A-Za-z0-9_$.]mu=\{` 全 0 命中 —— 说明实例与英文资源本体都不在本行内联。若要做"运行时改语言"的方案 B，必须先确定 `at` 在 38 行的绑定来源。
- **文件逻辑行/模块边界未映射**：26 行与 38 行都出现 `import … as …`，与"每行一个模块"的直觉不符，本轮未继续追（对字符串级 patch 无影响）。

## 7. 复现命令（grep 工具，pattern / path 两字段）

```
path = C:\Users\27837\AppData\Local\Programs\Devin\resources\app\out\vs\workbench\devin-webapp-host\assets\chunk-entry-host-editor-mode-menu-BWLlgqZu.js

pattern = [^A-Za-z0-9_$.]at\.isInitialized\|\|Jd\(\)            # 期望 1 命中 / 第 38 行
pattern = at\.use\(pd\)\.init\(\{resources:n,lng:`en`            # 期望 1 命中 / 第 26 行
pattern = n=\{en:\{translation:t\?JSON\.parse\(JSON\.stringify\(mu\)\):mu,review:hu\}\}   # 期望 1 命中 / 第 26 行
pattern = ns:\[`translation`,`review`\]                          # 期望 1 命中 / 第 26 行
pattern = at\.changeLanguage\(                                   # 旁证：1 命中 / 第 26 行
```

（以上 5 条已在本轮逐一跑过，命中数与行号即为上表所记。）
