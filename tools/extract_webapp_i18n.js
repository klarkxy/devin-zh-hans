/**
 * extract_webapp_i18n.js — 从 webapp-host 的 i18n chunk 里取出**带命名空间**的英文资源
 *
 * 为什么不能用正则扫 key:
 *   `analyze_webapp.py` 第一版把 `key: 值` 全抓下来，得到 4,575 个扁平 key。
 *   但 Devin 的 en 资源是**嵌套命名空间**结构：
 *
 *       yl = { composerTips: ma, nav: $a, common: ga, … }
 *       ma = { newSession: `Tip: Start a new session (<shortcut/>)`, … }
 *
 *   i18next 查的是 "composerTips.newSession"，扁平 key 永远匹配不到。
 *
 * 资源有**两种**写法，都要扫：
 *   ① 模板字面量对象： `ma={newSession:\`Tip: …\`}` / `"key":"value"`
 *   ② JSON.parse 内联：`Ss=JSON.parse(\`{"highContrast":"High contrast mode",…}\`)`
 *      —— 设置页那一大片文案全在 ② 里，早期版本整个漏掉。
 *
 * 输出: tools/data/webapp-en.json
 */
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const APP = (() => {
  const c = [process.env.DEVIN_INSTALL,
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Devin'), 'C:\\Program Files\\Devin'];
  for (const p of c) if (p && fs.existsSync(path.join(p, 'Devin.exe'))) return p;
  return null;
})();
if (!APP) { console.error('✗ 未找到 Devin 安装'); process.exit(1); }

const DIR = path.join(APP, 'resources', 'app', 'out', 'vs', 'workbench', 'devin-webapp-host', 'assets');

let chunk = null;
// 3.11 chunk 名以 entry-host-… 开头；3.14 变为 chunk-entry-host-…。
// 守卫形态：3.11 是 Mt.isInitialized||Eu()；3.14 是 at.isInitialized||Jd()（资源根 mu 未变）。
const GUARDS = ['Mt.isInitialized||Eu()', 'at.isInitialized||Jd()'];
for (const f of fs.readdirSync(DIR)) {
  if (!(f.startsWith('entry-host-editor-mode-menu')
    || f.startsWith('chunk-entry-host-editor-mode-menu')) || !f.endsWith('.js')) continue;
  const p = path.join(DIR, f);
  const src = fs.readFileSync(p, 'utf8');
  if (GUARDS.some((g) => src.includes(g))) { chunk = p; break; }
}
if (!chunk) { console.error('✗ 未找到 i18n 入口 chunk'); process.exit(1); }

const src = fs.readFileSync(chunk, 'utf8');
console.log('i18n chunk:', path.basename(chunk), (src.length / 1048576).toFixed(2), 'MB');

// ───────────────────────── 配平工具 ─────────────────────────
function matchBrace(s, open) {
  let depth = 0, i = open, q = null;
  for (; i < s.length; i++) {
    const ch = s[i];
    if (q) {
      if (ch === '\\') { i++; continue; }
      if (ch === q) q = null;
      continue;
    }
    if (ch === '`' || ch === '"' || ch === "'") { q = ch; continue; }
    if (ch === '/' && s[i + 1] === '/') { const j = s.indexOf('\n', i); i = j < 0 ? s.length : j; continue; }
    if (ch === '/' && s[i + 1] === '*') { const j = s.indexOf('*/', i + 2); i = j < 0 ? s.length : j + 1; continue; }
    if (ch === '{') depth++;
    else if (ch === '}') { depth--; if (depth === 0) return i; }
  }
  return -1;
}

function splitTop(s) {
  const out = [];
  let depth = 0, start = 0, q = null;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (q) {
      if (ch === '\\') { i++; continue; }
      if (ch === q) q = null;
      continue;
    }
    if (ch === '`' || ch === '"' || ch === "'") { q = ch; continue; }
    if (ch === '{' || ch === '[' || ch === '(') depth++;
    else if (ch === '}' || ch === ']' || ch === ')') depth--;
    else if (ch === ',' && depth === 0) { out.push(s.slice(start, i)); start = i + 1; }
  }
  const tail = s.slice(start);
  if (tail.trim()) out.push(tail);
  return out;
}

const STR = /^`([\s\S]*)`$|^"([\s\S]*)"$|^'([\s\S]*)'$/;

function entries(lit) {
  const s = lit.trim();
  if (s[0] !== '{') return [];
  const close = matchBrace(s, 0);
  if (close < 0) return [];
  const body = s.slice(1, close);
  const out = [];
  for (const part of splitTop(body)) {
    const m = part.match(/^\s*(?:`([^`]*)`|"([^"]*)"|'([^']*)'|([A-Za-z_$][\w$]*))\s*:\s*([\s\S]*)$/);
    if (!m) continue;
    out.push([m[1] ?? m[2] ?? m[3] ?? m[4], m[5].trim()]);
  }
  return out;
}

// ───────────────────────── ① 模板字面量对象 ─────────────────────────
const literals = new Map();
{
  const re = /([A-Za-z_$][\w$]*)\s*=\s*\{/g;
  let m;
  while ((m = re.exec(src))) {
    const name = m[1];
    const open = src.indexOf('{', m.index + m[0].length - 1);
    const close = matchBrace(src, open);
    if (close < 0) break;
    if (!literals.has(name)) literals.set(name, src.slice(open, close + 1));
    re.lastIndex = close + 1;
  }
}
console.log('模板字面量对象:', literals.size);

// ───────────────────────── ② JSON.parse(`…`) 内联资源 ─────────────────────────
// 关键：模板字符串里的 \` \" \\ 需要先反转义回 JS 源码形态，才能当 JSON 解析。
// 早期直接 JSON.parse 原文会因 \" 与 \u 的转义层级不同而失败。
function unescapeTemplate(raw) {
  let out = '';
  for (let i = 0; i < raw.length; i++) {
    const ch = raw[i];
    if (ch !== '\\') { out += ch; continue; }
    const n = raw[i + 1];
    i++;
    switch (n) {
      case 'n': out += '\n'; break;
      case 't': out += '\t'; break;
      case 'r': out += '\r'; break;
      case '`': out += '`'; break;
      case '\\': out += '\\'; break;
      case '"': out += '\\"'; break;   // 模板里 \" 在 JSON 里仍是转义引号
      case "'": out += "'"; break;
      case 'u': out += '\\u' + raw.slice(i + 1, i + 5); i += 4; break;
      default: out += n;
    }
  }
  return out;
}

/** 宽松 JSON 解析：失败时用 eval 兜底（只有纯字面量）。 */
function looseParse(text) {
  try { return JSON.parse(text); } catch { }
  try { return JSON.parse(text.replace(/\n/g, '\\n').replace(/\t/g, '\\t')); } catch { }
  try {
    // 只允许字面量，禁掉任何标识符
    if (/[A-Za-z_$][\w$]*\s*\(/.test(text)) return null;
    // eslint-disable-next-line no-new-func
    return new Function('return (' + text + ')')();
  } catch { }
  return null;
}

const jsonResources = new Map();   // name -> 对象
{
  const re = /([A-Za-z_$][\w$]*)\s*=\s*JSON\.parse\(\s*`([\s\S]*?)`\s*\)/g;
  let m;
  while ((m = re.exec(src))) {
    const name = m[1];
    const raw = unescapeTemplate(m[2]);
    const obj = looseParse(raw);
    if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
      if (!jsonResources.has(name)) jsonResources.set(name, obj);
    }
  }
}
const jsonKeys = [...jsonResources.values()].reduce((a, o) => a + Object.keys(o).length, 0);
console.log('JSON.parse 内联资源:', jsonResources.size, '个 /', jsonKeys, '个顶层 key');

// ───────────────────────── 解析资源根 ─────────────────────────
function aliasOf(name, maxHops = 6) {
  let cur = name;
  for (let h = 0; h < maxHops; h++) {
    if (literals.has(cur)) return cur;
    const re = new RegExp('\\b' + cur.replace(/\$/g, '\\$') + '\\s*=\\s*([A-Za-z_$][\\w$]*)\\s*[,;}]');
    const mm = src.match(re);
    if (!mm) return null;
    cur = mm[1];
  }
  return null;
}

let rootName = null, reviewName = null;
{
  const at = src.search(/resources\s*:\s*([A-Za-z_$][\w$]*)\s*,\s*lng:/);
  let def = null;
  if (at >= 0) {
    const objName = src.slice(src.indexOf(':', at) + 1).match(/^\s*([A-Za-z_$][\w$]*)/)[1];
    const esc = objName.replace(/\$/g, '\\$');
    def = src.match(new RegExp('\\b' + esc +
      '\\s*=\\s*\\{\\s*en\\s*:\\s*\\{\\s*translation\\s*:\\s*t\\s*\\?[^:]+:\\s*([A-Za-z_$][\\w$]*)\\s*,\\s*review\\s*:\\s*([A-Za-z_$][\\w$]*)'));
    if (!def) {
      def = src.match(new RegExp('\\b' + esc +
        '\\s*=\\s*\\{\\s*en\\s*:\\s*\\{\\s*translation\\s*:\\s*([A-Za-z_$][\\w$]*)\\s*(?:,\\s*review\\s*:\\s*([A-Za-z_$][\\w$]*))?'));
    }
  } else {
    def = src.match(/resources\s*:\s*\{\s*en\s*:\s*\{\s*translation\s*:\s*([A-Za-z_$][\w$]*)\s*(?:,\s*review\s*:\s*([A-Za-z_$][\w$]*))?/);
  }
  if (def) { rootName = def[1]; reviewName = def[2] || null; }
}
if (!rootName) { console.error('✗ 未定位 en 资源根变量'); process.exit(1); }
const rootLit = aliasOf(rootName);
console.log('en 资源变量:', rootName, '->', rootLit || '(缺失)', '| review:', reviewName || '(无)');

// ───────────────────────── 展开对象树 ─────────────────────────
function resolveInline(lit, seen, depth) {
  if (depth > 10) return null;
  const obj = {};
  for (const [k, v] of entries(lit)) {
    const sm = v.match(STR);
    if (sm) { obj[k] = sm[1] ?? sm[2] ?? sm[3]; continue; }
    if (v[0] === '{') { const s2 = resolveInline(v, seen, depth + 1); if (s2) obj[k] = s2; continue; }
    const im = v.match(/^([A-Za-z_$][\w$]*)$/);
    if (im) { const s2 = resolveName(im[1], new Set(seen), depth + 1); if (s2) obj[k] = s2; }
  }
  return obj;
}

function resolveName(name, seen, depth) {
  if (depth > 10 || seen.has(name)) return null;
  if (jsonResources.has(name)) return jsonResources.get(name);   // ② 直接可用
  const lit = literals.get(name);
  if (!lit) return null;
  seen.add(name);
  return resolveInline(lit, seen, depth);
}

function flat(obj, pre, out) {
  for (const k of Object.keys(obj)) {
    const v = obj[k];
    const key = pre ? pre + '.' + k : k;
    if (v && typeof v === 'object' && !Array.isArray(v)) flat(v, key, out);
    else if (typeof v === 'string') out[key] = v;
  }
  return out;
}

const nsMap = {};
function addNs(name, obj) {
  if (!obj || typeof obj !== 'object') return;
  const o = flat(obj, '', {});
  if (Object.keys(o).length) {
    // 同名命名空间合并（模板字面量与 JSON.parse 可能各提供一部分）
    nsMap[name] = Object.assign(nsMap[name] || {}, o);
  }
}

{
  const rootObj = rootLit ? resolveName(rootLit, new Set(), 0) : null;
  if (!rootObj) { console.error('✗ 资源根展开失败'); process.exit(1); }
  for (const ns of Object.keys(rootObj)) addNs(ns, rootObj[ns]);
}

const total = Object.values(nsMap).reduce((a, b) => a + Object.keys(b).length, 0);
console.log('命名空间:', Object.keys(nsMap).length, '| 叶子 key:', total);
const top = Object.entries(nsMap).map(([k, v]) => [k, Object.keys(v).length])
  .sort((a, b) => b[1] - a[1]).slice(0, 8);
console.log('最大命名空间:', top.map(([k, n]) => k + '(' + n + ')').join(', '));

// 设置页抽查
for (const probe of ['settingsUi.highContrast', 'common.highContrast', 'settings.highContrast',
  'settingsUi.displayLanguage', 'common.displayLanguage']) {
  const [ns, ...rest] = probe.split('.');
  const k = rest.join('.');
  const v = nsMap[ns] && nsMap[ns][k];
  if (v) console.log('  抽查 %-32s %s', probe, '"' + v + '"');
}

// 落盘位置可用环境变量改写（受限 shell 无法写 tools/data 时指到别处）
const OUT_DIR = process.env.DEVIN_ZH_DATA || path.join(ROOT, 'tools', 'data');
fs.mkdirSync(OUT_DIR, { recursive: true });
fs.writeFileSync(path.join(OUT_DIR, 'webapp-en.json'),
  JSON.stringify({
    namespaces: nsMap,
    stats: {
      total, ns: Object.keys(nsMap).length, chunk: path.basename(chunk),
      jsonResources: jsonResources.size, jsonKeys,
    },
  }, null, 1), 'utf8');
console.log('✓ ' + path.join(OUT_DIR, 'webapp-en.json'));
