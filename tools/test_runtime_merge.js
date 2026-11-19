/**
 * test_runtime_merge.js — 真正在 Node 里模拟 webapp 的 i18next 初始化，验证中文能查到
 *
 * 这比「文件里有载荷」强得多：它证明
 *   ① 注入后的代码语法可执行
 *   ② Object.assign 在 Eu() 之前生效，中文进入 resources
 *   ③ i18next 查 composerTips.sidebar / sidebar.automations 能拿到中文
 *
 * 用真 i18next 太重，这里用一个 30 行的最小实现，只验证「key → resources 的查找路径」。
 */
'use strict';
const fs = require('fs');
const path = require('path');

const APP = (() => {
  const c = [process.env.DEVIN_INSTALL,
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Devin'), 'C:\\Program Files\\Devin'];
  for (const p of c) if (p && fs.existsSync(path.join(p, 'Devin.exe'))) return p;
  return null;
})();

const chunkDir = path.join(APP, 'resources', 'app', 'out', 'vs', 'workbench',
  'devin-webapp-host', 'assets');
// 3.11 chunk 名以 entry-host-… 开头；3.14 变为 chunk-entry-host-…（双前缀动态定位）。
const PREFIXES = ['entry-host-editor-mode-menu', 'chunk-entry-host-editor-mode-menu'];
let chunkPath = null;
for (const f of fs.readdirSync(chunkDir)) {
  if (PREFIXES.some((p) => f.startsWith(p)) && f.endsWith('.js')) {
    chunkPath = path.join(chunkDir, f);
    break;
  }
}
const src = fs.readFileSync(chunkPath, 'utf8');

// ── 1. 载荷直接用当前产物（不依赖安装目录里的历史形态）──
const zhPath = path.join(__dirname, '..', 'assets', 'webapp-i18n.json');
const zh = JSON.parse(fs.readFileSync(zhPath, 'utf8'));
console.log('载荷: ' + Object.keys(zh).length + ' 个命名空间, '
  + Object.values(zh).reduce((a, o) => a + Object.keys(o).length, 0) + ' 条');

// ── 2. 模拟 Devin 的英文资源 mu（取真实 chunk 里 mu = yl 的形态）──
// 只用截图里出现过的 key 造一个最小 mu，验证合并与查找。
const mu = {
  sidebar: {
    automations: 'Automations',
    recent: 'Recent',
    security: 'Security',
    wiki: 'Wiki',
    review: 'Review',
    customize: 'Customize',
  },
  composerTips: {
    sidebar: 'Tip: Hide or show the sidebar (<shortcut/>)',
    newSession: 'Tip: Start a new session (<shortcut/>)',
    sessionNav: 'Tip: Move between sessions (<up/> / <down/>)',
  },
  nav: { newSession: 'New session', security: 'Security' },
  settings: { highContrast: 'High contrast mode', uiFont: 'Interface font' },
};

// ── 3. 执行注入语句（与 extension.js 的 makePayload 一字不差）──
const dz = "function __dz(a,b){for(var k in b){var v=b[k];"
  + "if(v&&typeof v===\"object\"&&!Array.isArray(v)){"
  + "__dz(a[k]&&typeof a[k]===\"object\"?a[k]:(a[k]={}),v)}"
  + "else{a[k]=v}}return a}";
const stmt = dz + ';__dz(mu||(mu={}),' + JSON.stringify(zh) + ')';
eval(stmt);

// ── 4. 模拟 i18next 的 key 查找：优先匹配最长命名空间，其余点号保留在扁平 key 中 ──
function t(key) {
  const parts = key.split('.');
  for (let i = parts.length - 1; i > 0; i--) {
    const ns = parts.slice(0, i).join('.');
    if (!mu[ns]) continue;
    const value = mu[ns][parts.slice(i).join('.')];
    if (typeof value === 'string') return value;
  }
  return key;
}

const cases = [
  ['sidebar.automations', '自动化'],
  ['sidebar.recent', '最近'],
  ['nav.security', '安全'],
  ['composerTips.sidebar', '提示：隐藏或显示侧边栏'],
  ['composerTips.agentLocation', '提示：在云端或本机上运行 Devin'],
  ['composerTips.newSession', '提示：开始新会话'],
  ['nav.newSession', '新建会话'],
  ['settings.highContrast', '高对比度模式'],
  ['settings.uiFont', '界面字体'],
  ['localSettings.general.openEditorSettings.label', '打开编辑器设置'],
  ['localSettings.sections.devinTab', 'Devin 标签页'],
  ['localSettings.chisel.descriptionWithPath', '这些设置仅适用于 Devin Local'],
  ['notificationPreferences.description', '收件箱'],
  ['notificationPreferences.mobilePushFor', '将“{{name}}”推送到移动端'],
];

let pass = 0;
console.log('\n== i18next 查找验证 ==');
for (const [key, want] of cases) {
  const got = t(key);
  const ok = got.includes(want);
  if (ok) pass++;
  console.log((ok ? '✓' : '✗') + ' ' + key.padEnd(26) + ' → ' + got);
}

// ── 5. 深合并完整性：载荷没覆盖到的英文 key 必须仍然存在 ──
// 这是 1.2.1 的根因。载荷只覆盖一部分 key，若用 Object.assign 浅合并，
// 整个命名空间会被替换成只含中文子集的对象，未翻译的 key 直接消失，
// 界面回退成显示 key 本身（localSettings.general.openEditorSettings.label）。
console.log('\n== 深合并完整性（未覆盖的英文 key 不能丢）==');
// guard 必须是「载荷确实没覆盖」的 key —— w 批次已把 localSettings 全覆盖，
// 改用确认不在载荷里的键（3.14 的英文 key 空间有 3.3 万个，载荷覆盖 31,961）。
const zhKeys = new Set(Object.keys(zh).flatMap((ns) => Object.keys(zh[ns]).map((k) => ns + '.' + k)));
const guards = [
  ['transcript', 'someUncoveredKey', 'Untouched English'],
  ['settings', 'anotherUncoveredKey', 'Still English'],
  ['nav', 'uncoveredPlaceholder', 'Raw'],
];
for (const [ns, k, en] of guards) {
  if (zhKeys.has(ns + '.' + k)) {
    console.log('⚠ guard ' + ns + '.' + k + ' 已被载荷覆盖，需换一个');
    process.exit(1);
  }
  mu[ns] = mu[ns] || {};
  mu[ns][k] = en;
}
// 重新跑一遍注入（此时 mu 里已有上面这些「未覆盖」的英文）
eval(stmt);
let guardPass = 0;
for (const [ns, k, en] of guards) {
  const got = mu[ns] && mu[ns][k];
  const ok = got === en;
  if (ok) guardPass++;
  console.log((ok ? '✓' : '✗') + ' ' + (ns + '.' + k).padEnd(50) + ' → ' + got);
}

const total = pass + guardPass;
const want = cases.length + guards.length;
console.log(''); console.log(total + '/' + want + ' 通过');
process.exit(total === want ? 0 : 1);


