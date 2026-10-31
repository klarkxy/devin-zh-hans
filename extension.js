/**
 * Devin 简体中文 —— 扩展运行时
 *
 * 四层落地，全程幂等：
 *   1) 语言包层：把合并版 main.i18n.json（官方译文 + 本插件补齐的缺口）写进已安装的
 *      官方 zh-hans 语言包。VS Code 在同一 locale 下按扩展顺序合并 translations，
 *      官方包 ms-ceintl.* 排序在后会把我们的 vscode bundle 盖掉，所以必须硬覆盖。
 *   2) 扩展贡献点层：Devin 内置的 5 个扩展（windsurf / windsurf-dev-containers /
 *      windsurf-remote-*）把命令标题与设置说明硬编码在 package.json 里，且没有
 *      package.nls*.json，语言包机制无效。这里写 package.nls.json + package.nls.zh-cn.json，
 *      并把 package.json 的字符串换成 %key%。
 *   3) webapp i18next 层：Agent UI（out/vs/workbench/devin-webapp-host/）自建 i18next，
 *      只有 en/ja/pt/es 没有 zh。把中文按英文 key 深合并进它的 en 资源。
 *   4) DOM 层：往 workbench.html / sessions.html 注入 devin-zh-dom.js，
 *      覆盖运行时数据拼出来的文案（Agent 侧边栏、会话窗口、菜单）。
 *
 * 第 2/3 层会改到 product.json.checksums 里的文件，所以每次写完都同步哈希，
 * 避免 Devin 启动时报「安装似乎损坏」。
 */
'use strict';
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const childProcess = require('child_process');

const TAG = '[devin-zh]';
const log = (...a) => console.log(TAG, ...a);
const BACKUP_ROOT = path.join(process.env.DEVIN_HOME || path.join(os.homedir(), '.devin'), 'devin-zh-backups');

// 需要注入 DOM 翻译器的窗口
const PAGES = [
  ['out/vs/code/electron-browser/workbench/workbench.html', './workbench.js'],
  ['out/vs/sessions/electron-browser/sessions.html', './sessions.js'],
];

// Devin 内置扩展：package.json 里的贡献点需要 %key% 化
const EXT_FAMILY = [
  'windsurf',
  'windsurf-dev-containers',
  'windsurf-remote-devin',
  'windsurf-remote-openssh',
  'windsurf-remote-wsl',
];

// ───────────────────────── 环境探测 ─────────────────────────
// DEVIN_INSTALL / DEVIN_HOME 供 tools/verify_layers.js 指向沙盒副本；
// 正常使用时留空，走标准探测。
function devinHome() {
  return process.env.DEVIN_HOME || path.join(os.homedir(), '.devin');
}

function findDevinInstall() {
  if (process.platform === 'darwin') {
    const app = vscode.env && vscode.env.appRoot;
    const cands = [
      process.env.DEVIN_INSTALL,
      app && path.resolve(app, '..', '..'),
      '/Applications/Devin.app/Contents',
      path.join(os.homedir(), 'Applications', 'Devin.app', 'Contents'),
    ];
    for (const c of cands) {
      if (!c) continue;
      const inst = c.endsWith('.app') ? path.join(c, 'Contents') : c;
      if (fs.existsSync(path.join(inst, 'Resources', 'app', 'product.json'))) return inst;
    }
  }
  const cands = [
    process.env.DEVIN_INSTALL,
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Devin'),
    'C:\\Program Files\\Devin',
  ];
  for (const c of cands) {
    if (c && fs.existsSync(path.join(c, 'Devin.exe'))) return c;
  }
  return null;
}

function devinApp(inst) {
  const mac = path.join(inst, 'Resources', 'app');
  return fs.existsSync(mac) ? mac : path.join(inst, 'resources', 'app');
}

function findLangpack() {
  const root = path.join(devinHome(), 'extensions');
  if (!fs.existsSync(root)) return null;
  for (const d of fs.readdirSync(root)) {
    if (/language-pack-zh-hans/.test(d)) {
      const p = path.join(root, d);
      if (fs.existsSync(path.join(p, 'translations', 'main.i18n.json'))) return p;
    }
  }
  return null;
}

function sha256b64(p) {
  return crypto.createHash('sha256').update(fs.readFileSync(p)).digest('base64').replace(/=+$/, '');
}

function sameFile(a, b) {
  try {
    if (!fs.existsSync(a) || !fs.existsSync(b)) return false;
    if (fs.statSync(a).size !== fs.statSync(b).size) return false;
    return fs.readFileSync(a).equals(fs.readFileSync(b));
  } catch { return false; }
}

function sameJson(a, b) {
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch { return false; }
}

function backup(p) {
  // Full paths distinguish the five built-in package.json files.
  const d = path.join(BACKUP_ROOT, 'files-v2');
  fs.mkdirSync(d, { recursive: true });
  const index = path.join(d, 'manifest.json');
  const entries = fs.existsSync(index) ? JSON.parse(fs.readFileSync(index, 'utf8')) : {};
  if (Object.prototype.hasOwnProperty.call(entries, p)) return;
  const dst = path.join(d, crypto.createHash('sha256').update(p).digest('hex'));
  const exists = fs.existsSync(p);
  if (exists) fs.copyFileSync(p, dst);
  entries[p] = exists ? dst : null;
  writeJson(index, entries);
}

function readJson(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; }
}

function writeJson(p, obj) {
  fs.writeFileSync(p, JSON.stringify(obj, null, '\t'), 'utf8');
}

// ───────────────────────── 第 1 层：语言包落地 ─────────────────────────
function applyLanguagePack(ctx) {
  const lp = findLangpack();
  if (!lp) {
    log('未检测到官方中文语言包 —— VSIX 自带的 localizations 会直接生效。');
    return { langpack: false, changed: false };
  }
  const src = path.join(ctx.extensionPath, 'translations', 'main.i18n.json');
  const dst = path.join(lp, 'translations', 'main.i18n.json');
  let changed = false;

  if (!sameFile(src, dst)) {
    backup(dst);
    fs.copyFileSync(src, dst);
    log('已写入合并版 main.i18n.json');
    changed = true;
  }

  // windsurf 扩展的贡献点 bundle（兼容只认语言包、不认 package.nls 的旧路径）
  const wsSrc = path.join(ctx.extensionPath, 'translations', 'extensions', 'windsurf.i18n.json');
  const wsDst = path.join(lp, 'translations', 'extensions', 'windsurf.i18n.json');
  if (fs.existsSync(wsSrc) && !sameFile(wsSrc, wsDst)) {
    backup(wsDst);
    fs.mkdirSync(path.dirname(wsDst), { recursive: true });
    fs.copyFileSync(wsSrc, wsDst);
    log('已写入 windsurf.i18n.json');
    changed = true;
  }

  // 在语言包清单里注册 windsurf bundle（幂等）
  const pkgPath = path.join(lp, 'package.json');
  try {
    const pkg = readJson(pkgPath);
    const locs = pkg && pkg.contributes && pkg.contributes.localizations;
    if (Array.isArray(locs) && locs[0]) {
      locs[0].translations = locs[0].translations || [];
      if (!locs[0].translations.some((t) => t.id === 'windsurf')) {
        backup(pkgPath);
        locs[0].translations.push({
          id: 'windsurf',
          path: './translations/extensions/windsurf.i18n.json',
        });
        writeJson(pkgPath, pkg);
        log('已在语言包清单注册 windsurf bundle');
        changed = true;
      }
    }
  } catch (e) { log('注册 bundle 失败:', e.message); }

  return { langpack: true, changed };
}

// ───────────────────────── 第 2 层：内置扩展贡献点 ─────────────────────────
function setByPath(obj, parts, value) {
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    if (cur[k] === undefined || cur[k] === null) return false;
    cur = cur[k];
  }
  const last = parts[parts.length - 1];
  if (cur[last] === undefined) return false;
  cur[last] = value;
  return true;
}

function getByPath(obj, parts) {
  let cur = obj;
  for (const k of parts) {
    if (cur === undefined || cur === null) return undefined;
    cur = cur[k];
  }
  return cur;
}

function applyExtensionManifests(ctx) {
  const inst = findDevinInstall();
  if (!inst) return { ext: false, changed: false };

  const planPath = path.join(ctx.extensionPath, 'assets', 'ext-manifest.json');
  const enPath = path.join(ctx.extensionPath, 'assets', 'ext-manifest.en.json');
  const zhPath = path.join(ctx.extensionPath, 'assets', 'ext-manifest.zh.json');
  const plan = readJson(planPath);
  const enMap = readJson(enPath);
  const zhMap = readJson(zhPath);
  if (!plan || !enMap) { log('缺少 ext-manifest 产物，跳过扩展贡献点层'); return { ext: false, changed: false }; }

  const extRoot = path.join(devinApp(inst), 'extensions');
  let changed = false;

  for (const name of EXT_FAMILY) {
    const entries = plan[name];
    if (!Array.isArray(entries) || !entries.length) continue;
    const dir = path.join(extRoot, name);
    const pkgPath = path.join(dir, 'package.json');
    if (!fs.existsSync(pkgPath)) continue;

    const pkg = readJson(pkgPath);
    if (!pkg) continue;

    // 2a) 两个 nls 文件
    const nlsEn = {};
    const nlsZh = {};
    for (const e of entries) {
      const en = enMap[e.key];
      if (typeof en !== 'string') continue;
      nlsEn[e.key] = en;
      const zh = zhMap[e.key];
      if (typeof zh === 'string') nlsZh[e.key] = zh;
    }
    const pEn = path.join(dir, 'package.nls.json');
    const pZh = path.join(dir, 'package.nls.zh-cn.json');
    if (!sameJson(readJson(pEn), nlsEn)) {
      backup(pEn);
      writeJson(pEn, nlsEn);
      changed = true;
    }
    if (!sameJson(readJson(pZh), nlsZh)) {
      backup(pZh);
      writeJson(pZh, nlsZh);
      changed = true;
    }

    // 2b) package.json 里的字符串换成 %key%
    let dirty = false;
    for (const e of entries) {
      const cur = getByPath(pkg, e.path);
      if (typeof cur !== 'string') continue;
      if (cur === '%' + e.key + '%') continue;
      if (setByPath(pkg, e.path, '%' + e.key + '%')) dirty = true;
    }
    if (dirty) {
      backup(pkgPath);
      writeJson(pkgPath, pkg);
      log('已本地化扩展贡献点: ' + name + ' (' + entries.length + ' 个字段)');
      changed = true;
    }
  }
  return { ext: true, changed };
}

// ───────────────────────── 第 3 层：webapp i18next ─────────────────────────
// webapp-host 的 i18n 入口在 entry-host-editor-mode-menu-*.js：
//
//     function Eu({pseudoLocale:e=!1,englishOverrides:t}={}){
//       let n={en:{translation: t ? JSON.parse(JSON.stringify(mu)) : mu, review:hu}};
//       return Mt.use(Mn).init({resources:n, lng:"en", fallbackLng:"en",
//                               ns:["translation","review"], defaultNS:"translation", …}),
//              t && Mt.addResourceBundle("en","translation",t,!0,!0), Mt }
//     …
//     Mt.isInitialized || Eu()
//
// `mu` 就是英文资源对象本身（`mu=yl`）。**必须往 mu 上合并中文**，不能在 init 之后
// 调 addResourceBundle —— i18next 的 initAsync 默认 true，init 完成时用 resources
// 覆盖已有 bundle，后加的会被吃掉。这正是「载荷明明在文件里、界面却仍显示原始 key
// （sidebar.automations）」的原因。
//
// 做法：在 `Mt.isInitialized||Eu()` 前插入深合并语句。
// Devin 用 `var mu,hu,gu;` 先声明、再在 _u() 闭包里 `mu=yl` 赋值，此处 mu 已就绪；
// `mu||(mu={})` 兼容未就绪的时序。
//
// ★ 必须**深合并**。载荷只覆盖一部分 key（localSettings 199 个里 57 个），
//   若用 Object.assign(mu, zh) 做浅合并，`mu.localSettings` 会被整个替换成只含
//   中文子集的新对象，未翻译的 142 个 key 随之消失，界面回退成显示 key 本身
//   （`localSettings.general.openEditorSettings.label`）。全量算下来会丢 7,843 个
//   英文 key。所以注入一个递归合并函数，把中文逐层写进现有英文对象。
const WEBAPP_DIR = 'out/vs/workbench/devin-webapp-host';
const HOST_ANCHOR = 'Mt.isInitialized||Eu()';
const HOST_MARK = '/*devin-zh*/';
const HOST_END = '/*/devin-zh*/';

function findHostChunk(app) {
  const dir = path.join(app, WEBAPP_DIR, 'assets');
  if (!fs.existsSync(dir)) return null;
  for (const f of fs.readdirSync(dir)) {
    if (!f.startsWith('entry-host-editor-mode-menu') || !f.endsWith('.js')) continue;
    const p = path.join(dir, f);
    try {
      if (fs.readFileSync(p, 'utf8').includes(HOST_ANCHOR)) return p;
    } catch { }
  }
  return null;
}

/**
 * 生成注入片段：把中文逐命名空间合并进 mu。
 *
 * resources 的形状是 `{ ns: { "点号key": 文案 } }` —— 只有**两层**，
 * 第二层的 key 是带点号的扁平字符串（`"general.openEditorSettings.label"`），
 * 不是嵌套对象。所以「深合并」等于「对每个命名空间各做一次 Object.assign」，
 * 不需要递归函数：
 *
 *   Object.assign(mu["settings"]||(mu["settings"]={}), {…}),
 *   Object.assign(mu["sidebar"]||(mu["sidebar"]={}), {…})
 *
 * 这样既覆盖中文，又保留该命名空间里未被翻译的英文 key。
 * 用递归函数会踩两个坑：`function` 声明不能出现在逗号表达式里（语法错误），
 * 以及把点号 key 当路径展开会破坏原有结构。
 */
function makePayload(zh) {
  const parts = [];
  for (const ns of Object.keys(zh)) {
    // 命名空间名本身是安全标识符时用 .x，否则用 ["x"]
    const init = /^[A-Za-z_$][\w$]*$/.test(ns)
      ? 'mu.' + ns + '||(mu.' + ns + '={})'
      : 'mu[' + JSON.stringify(ns) + ']||(mu[' + JSON.stringify(ns) + ']={})';
    parts.push('Object.assign(' + init + ',' + JSON.stringify(zh[ns]) + ')');
  }
  return HOST_MARK + parts.join(',') + HOST_END;
}

// 用当前 Electron/Node 对完整 ES module 做语法检查。先在临时文件验证，失败则不碰原 chunk。
function webappSyntaxError(source) {
  const tmp = path.join(os.tmpdir(), 'devin-zh-webapp-' + process.pid + '-' + Date.now() + '.mjs');
  try {
    fs.writeFileSync(tmp, source, 'utf8');
    const r = childProcess.spawnSync(process.execPath, ['--check', tmp], {
      env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' },
      stdio: 'ignore', windowsHide: true,
    });
    if (r.error) return r.error.message;
    if (r.status !== 0) return 'node --check exited ' + r.status;
    return null;
  } finally {
    try { fs.rmSync(tmp, { force: true }); } catch { }
  }
}

function writeValidWebappChunk(chunk, source) {
  const error = webappSyntaxError(source);
  if (error) {
    log('webapp 语法检查失败，已放弃写入: ' + error);
    return false;
  }
  fs.writeFileSync(chunk, source, 'utf8');
  return true;
}

function applyWebappI18n(ctx) {
  const inst = findDevinInstall();
  if (!inst) return { webapp: false, changed: false };
  const app = devinApp(inst);

  const zh = readJson(path.join(ctx.extensionPath, 'assets', 'webapp-i18n.json'));
  if (!zh) { log('缺少 webapp-i18n.json，跳过 webapp 层'); return { webapp: false, changed: false }; }

  const chunk = findHostChunk(app);
  if (!chunk) {
    log('未找到 webapp-host 的 i18n 入口（Devin 版本可能已变更），跳过 webapp 层');
    return { webapp: false, changed: false };
  }

  const payload = makePayload(zh);

  let s = fs.readFileSync(chunk, 'utf8');

  // 已有载荷：按位置整体替换（旧式 addResourceBundle 的也走这里，会被换成新形态）
  const a0 = s.indexOf(HOST_MARK);
  const b0 = s.indexOf(HOST_END);
  if (a0 >= 0 && b0 > a0) {
    const old = s.slice(a0, b0 + HOST_END.length);
    if (old === payload && !webappSyntaxError(s)) return { webapp: true, changed: false };
    backup(chunk);
    // 旧式载荷形如 `/*devin-zh*/Mt.isInitialized||Eu(),Mt.addResourceBundle(…)`，
    // 锚点被吞进了载荷里 —— 先整体摘掉，再补回锚点，最后把新载荷插到锚点之前。
    let next = s.slice(0, a0) + s.slice(b0 + HOST_END.length);
    if (!next.includes(HOST_ANCHOR)) {
      // 锚点原本在载荷内部，摘掉后需要补回。定位闭包尾 `cL=s(),` 或直接找载荷原位置。
      const near = next.slice(Math.max(0, a0 - 60), a0);
      if (/cL=s\(\),$/.test(near)) {
        next = next.slice(0, a0) + HOST_ANCHOR + ',' + next.slice(a0);
      } else {
        next = next.replace(/(cL=s\(\),)\s*/, '$1' + HOST_ANCHOR + ',');
      }
    }
    const at2 = next.indexOf(HOST_ANCHOR);
    if (at2 >= 0) {
      next = next.slice(0, at2) + payload + ',' + next.slice(at2);
      // 旧载荷两侧原本各有一个表达式分隔逗号；整体摘掉再插入会留下 `,,/*devin-zh*/`。
      // 只收敛注入点处的重复逗号，不改其它代码。
      next = next.replace(/,(?:\s*,)+\s*\/\*devin-zh\*\//g, ',' + HOST_MARK);
      // 锚点原本紧跟的逗号可能变成尾逗号（`…,Mt.isInitialized||Eu(),}`），必须收敛，
      // 否则整个 chunk 语法错误、Devin 起不来。
      next = next.replace(/(Mt\.isInitialized\|\|Eu\(\)),(\s*\})/g, '$1$2');
    }
    if (!writeValidWebappChunk(chunk, next)) return { webapp: false, changed: false };
    log('已更新 webapp 中文资源（' + Object.keys(zh).length + ' 个命名空间根）');
    return { webapp: true, changed: true };
  }

  const at = s.indexOf(HOST_ANCHOR);
  if (at < 0) return { webapp: false, changed: false };
  backup(chunk);
  // 必须插在锚点**之前**：Object.assign 先改 mu，Eu() 的 init 才会把中文一并注册。
  // 插在之后则 init 已用旧 mu 完成，改 mu 不再影响已注册的 resources。
  s = s.slice(0, at) + payload + ',' + s.slice(at);
  s = s.replace(/(Mt\.isInitialized\|\|Eu\(\)),(\s*\})/g, '$1$2');
  // 语法自检：写坏 chunk 会让 Devin 起不来，宁可跳过也不落盘
  if (!writeValidWebappChunk(chunk, s)) return { webapp: false, changed: false };
  log('已注入 webapp 中文资源（' + Object.keys(zh).length + ' 个命名空间根）');
  return { webapp: true, changed: true };
}

// ───────────────────────── 第 4 层：DOM 翻译器 ─────────────────────────
function applyDomLayer(ctx) {
  const inst = findDevinInstall();
  if (!inst) { log('未找到 Devin 安装目录，跳过 DOM 层'); return { dom: false, changed: false }; }
  const app = devinApp(inst);
  const runtimeSrc = path.join(ctx.extensionPath, 'dist', 'devin-zh-dom.js');
  const productPath = path.join(app, 'product.json');
  const product = readJson(productPath);

  let changed = false;
  for (const [rel, anchor] of PAGES) {
    const html = path.join(app, rel);
    if (!fs.existsSync(html)) continue;
    const jsName = 'devin-zh-dom.js';
    const jsDst = path.join(path.dirname(html), jsName);

    if (!sameFile(runtimeSrc, jsDst)) {
      try {
        backup(jsDst);
        fs.writeFileSync(jsDst, fs.readFileSync(runtimeSrc));
        log('已写入 ' + rel.replace(/\/[^/]+$/, '/') + jsName);
        changed = true;
      } catch (e) { log('写入运行时失败:', e.message); continue; }
    }

    let s = '';
    try { s = fs.readFileSync(html, 'utf8'); } catch { continue; }
    const tag = '<script src="./' + jsName + '"></script>';
    if (!s.includes(tag)) {
      const a = '<script src="' + anchor + '" type="module"></script>';
      if (!s.includes(a)) { log('HTML 锚点缺失: ' + rel); continue; }
      backup(html);
      fs.writeFileSync(html, s.replace(a, tag + '\n\t' + a), 'utf8');
      log('已注入 script 标签: ' + rel);
      changed = true;
    }
  }

  // 同步 checksums：受保护文件被改过就必须更新哈希，否则启动时告警
  if (product && product.checksums) {
    let dirty = false;
    for (const key of Object.keys(product.checksums)) {
      const p = path.join(app, 'out', key);
      if (!fs.existsSync(p)) continue;
      const h = sha256b64(p);
      if (product.checksums[key] !== h) { product.checksums[key] = h; dirty = true; }
    }
    if (dirty) {
      try {
        backup(productPath);
        writeJson(productPath, product);
        log('已同步 product.json.checksums');
        changed = true;
      } catch (e) { log('同步 checksums 失败:', e.message); }
    }
  }
  return { dom: true, changed };
}

// ───────────────────────── 状态 ─────────────────────────
function collectStatus(ctx) {
  const inst = findDevinInstall();
  const lp = findLangpack();
  const out = [];
  out.push('Devin 安装目录 : ' + (inst || '未找到'));
  out.push('官方中文语言包 : ' + (lp || '未找到（将使用 VSIX 自带 localizations）'));

  if (lp) {
    try {
      const c = readJson(path.join(lp, 'translations', 'main.i18n.json')).contents;
      let n = 0;
      for (const f of Object.keys(c)) n += Object.keys(c[f] || {}).length;
      out.push('语言包译文总量 : ' + n.toLocaleString());
    } catch { }
  }

  if (inst) {
    const app = devinApp(inst);

    // 扩展贡献点
    let extOk = 0, extTotal = 0;
    for (const name of EXT_FAMILY) {
      const dir = path.join(app, 'extensions', name);
      const pkgPath = path.join(dir, 'package.json');
      if (!fs.existsSync(pkgPath)) continue;
      extTotal++;
      const zh = readJson(path.join(dir, 'package.nls.zh-cn.json'));
      const pkg = readJson(pkgPath);
      const s = JSON.stringify(pkg || {});
      if (zh && s.includes('%"') === false && /%[\w.]{6,}%/.test(s)) extOk++;
    }
    if (extTotal) out.push('扩展贡献点汉化 : ' + extOk + ' / ' + extTotal);

    // webapp i18next
    const chunk = findHostChunk(app);
    let wa = false;
    try { wa = !!(chunk && fs.readFileSync(chunk, 'utf8').includes(HOST_MARK)); } catch { }
    out.push('Agent UI i18next : ' + (chunk ? (wa ? '✓ 已注入' : '✗ 未注入') : '未找到入口'));

    // DOM
    for (const [rel] of PAGES) {
      let ok = false;
      try { ok = fs.readFileSync(path.join(app, rel), 'utf8').includes('devin-zh-dom.js'); } catch { }
      out.push('DOM 注入 ' + (rel.includes('sessions') ? 'Sessions 窗口' : '主窗口') + ' : ' + (ok ? '✓' : '✗'));
    }

    // checksums
    try {
      const prod = readJson(path.join(app, 'product.json'));
      let ok = 0, bad = 0;
      for (const [k, exp] of Object.entries(prod.checksums || {})) {
        const p = path.join(app, 'out', k);
        if (!fs.existsSync(p)) { bad++; continue; }
        (sha256b64(p) === exp ? ok++ : bad++);
      }
      out.push('完整性校验自洽 : ' + ok + ' / ' + (ok + bad) + (bad === 0 ? '  ✓ 不会告警' : '  ✗ 有 ' + bad + ' 项不一致'));
    } catch { }
  }
  return out;
}

// ───────────────────────── 激活 ─────────────────────────
function activate(context) {
  const ctx = { extensionPath: context.extensionPath };
  log('扩展已激活, 路径 =', context.extensionPath);

  const run = (silent) => {
    let changed = false;
    const steps = [
      ['语言包', applyLanguagePack],
      ['扩展贡献点', applyExtensionManifests],
      ['webapp i18next', applyWebappI18n],
      ['DOM', applyDomLayer],
    ];
    for (const [name, fn] of steps) {
      try {
        const r = fn(ctx);
        if (r && r.changed) changed = true;
      } catch (e) {
        log(name + ' 层失败:', e.message);
      }
    }
    if (changed) {
      log('汉化已落地 —— 需重启一次 Devin 才能完全生效。');
      vscode.window.showInformationMessage(
        'Devin 简体中文已应用。语言包与界面注入需要重启 Devin 一次才能完全生效。', '知道了'
      ).then(() => { }, () => { });
    } else if (!silent) {
      log('汉化已是最新状态，无需改动。');
    }
    return changed;
  };

  run(true);

  context.subscriptions.push(
    vscode.commands.registerCommand('devin-zh.status', async () => {
      const lines = collectStatus(ctx);
      log('状态:\n' + lines.join('\n'));
      await vscode.window.showInformationMessage('Devin 中文状态：' + lines.join(' | '), { modal: true }, '确定');
    }),
    vscode.commands.registerCommand('devin-zh.apply', async () => {
      const changed = run(false);
      await vscode.window.showInformationMessage(
        changed ? '已重新应用汉化，请重启 Devin。' : '汉化已是最新，无需改动。');
    }),
    vscode.commands.registerCommand('devin-zh.uninstall', async () => {
      const index = path.join(BACKUP_ROOT, 'files-v2', 'manifest.json');
      if (!fs.existsSync(index)) {
        vscode.window.showWarningMessage('没有找到包含完整路径的备份，无法安全自动回滚。旧版 vsix-* 备份请勿混用，必要时重新安装 Devin。');
        return;
      }
      const pick = await vscode.window.showWarningMessage(
        '将从备份还原文件并卸载本插件。请勿在 Devin 已升级后还原旧版本备份。继续？', { modal: true }, '回滚', '取消');
      if (pick !== '回滚') return;

      const entries = JSON.parse(fs.readFileSync(index, 'utf8'));
      for (const b of Object.values(entries)) {
        if (b && !fs.existsSync(b)) {
          await vscode.window.showWarningMessage('备份文件缺失，未执行回滚: ' + b);
          return;
        }
      }
      for (const [t, b] of Object.entries(entries)) {
        try {
          if (b) fs.copyFileSync(b, t);
          else if (fs.existsSync(t)) fs.unlinkSync(t);
          log('已还原 ' + t);
        } catch (e) {
          await vscode.window.showWarningMessage('还原失败 ' + t + ': ' + e.message);
          return;
        }
      }
      await vscode.commands.executeCommand('workbench.extensions.uninstallExtension', 'devin-zh.devin-zh-hans');
      await vscode.window.showInformationMessage('已回滚并卸载扩展，请重启 Devin。');
    })
  );
}

function deactivate() { }

module.exports = { activate, deactivate };
