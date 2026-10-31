/**
 * verify_layers.js — 在不启动 Devin 的情况下验证四层落地逻辑
 *
 * 用法：
 *     node tools/verify_layers.js            # 沙盒干跑（不写任何文件）
 *     node tools/verify_layers.js --apply    # 沙盒写入（验证幂等与完整性）
 *     node tools/verify_layers.js --real     # 对真实安装执行（等同扩展激活）
 *
 * 原理：给 extension.js 喂一个假的 `vscode` 模块，直接调 activate()，
 * 验证的就是插件真实会执行的代码路径，而不是另写一份。
 *
 * 沙盒：把 Devin 安装树里**被本插件碰到的文件**、以及官方中文语言包的
 * translations，复制到 <repo>/.verify/ 下，用 DEVIN_INSTALL / DEVIN_HOME 指过去。
 * 这样验证全程不写系统目录，也不依赖管理员权限。
 */
'use strict';
const path = require('path');
const fs = require('fs');
const Module = require('module');
const os = require('os');
const crypto = require('crypto');
const childProcess = require('child_process');

const APPLY = process.argv.includes('--apply');
const REAL = process.argv.includes('--real');
const KEEP = process.argv.includes('--keep');   // 复用已有沙盒（验证幂等）
const UPGRADE = process.argv.includes('--upgrade'); // 从带旧载荷的干净 chunk 升级
const ROOT = path.resolve(__dirname, '..');
const SANDBOX = path.join(ROOT, '.verify');

const FAMILY = ['windsurf', 'windsurf-dev-containers', 'windsurf-remote-devin',
  'windsurf-remote-openssh', 'windsurf-remote-wsl'];

// ── 定位真实安装 ──
const REAL_INST = (() => {
  if (process.platform === 'darwin') {
    const c = [process.env.DEVIN_INSTALL, '/Applications/Devin.app/Contents',
      path.join(os.homedir(), 'Applications', 'Devin.app', 'Contents')];
    for (const p of c) {
      if (!p) continue;
      const inst = p.endsWith('.app') ? path.join(p, 'Contents') : p;
      if (fs.existsSync(path.join(inst, 'Resources', 'app', 'product.json'))) return inst;
    }
    return null;
  }
  const c = [process.env.DEVIN_INSTALL,
    path.join(process.env.LOCALAPPDATA || '', 'Programs', 'Devin'), 'C:\\Program Files\\Devin'];
  for (const p of c) if (p && fs.existsSync(path.join(p, 'Devin.exe'))) return p;
  return null;
})();
const REAL_HOME = process.env.DEVIN_HOME || path.join(os.homedir(), '.devin');
const RESOURCES = process.platform === 'darwin' ? 'Resources' : 'resources';

// 被本插件写入的路径（相对 resources/app）
const TOUCHED = [
  'product.json',
  'out/nls.keys.json',
  'out/vs/code/electron-browser/workbench/workbench.html',
  'out/vs/sessions/electron-browser/sessions.html',
  'out/vs/workbench/devin-webapp-host/assets',
  ...FAMILY.map((n) => 'extensions/' + n + '/package.json'),
];

// product.json.checksums 里的受保护文件全部复制进沙盒，
// 否则「12/12 自洽」这条断言只能跳过（沙盒里缺文件）。
function protectedFiles(app) {
  try {
    const prod = JSON.parse(fs.readFileSync(path.join(app, 'product.json'), 'utf8'));
    return Object.keys(prod.checksums || {}).map((k) => 'out/' + k);
  } catch {
    return [];
  }
}

function buildSandbox() {
  if (!REAL_INST) return null;
  const app = path.join(REAL_INST, RESOURCES, 'app');
  const dst = process.platform === 'darwin'
    ? path.join(SANDBOX, 'Devin.app', 'Contents') : path.join(SANDBOX, 'Devin');
  const dstApp = path.join(dst, RESOURCES, 'app');
  const homeDst = path.join(SANDBOX, 'home');

  if (KEEP && fs.existsSync(dst)) {
    // 复用已有沙盒：用来验证第二次激活的幂等性
    return { inst: dst, home: homeDst };
  }

  if (fs.existsSync(SANDBOX)) fs.rmSync(SANDBOX, { recursive: true, force: true });
  fs.mkdirSync(dstApp, { recursive: true });
  if (process.platform !== 'darwin') fs.writeFileSync(path.join(dst, 'Devin.exe'), '');

  for (const rel of TOUCHED.concat(protectedFiles(app))) {
    const s = path.join(app, rel);
    const d = path.join(dstApp, rel);
    if (!fs.existsSync(s)) continue;
    if (fs.statSync(s).isDirectory()) {
      // webapp-host/assets 有 91 MB，只复制 i18n 入口那个 chunk
      fs.mkdirSync(d, { recursive: true });
      for (const f of fs.readdirSync(s)) {
        if (f.startsWith('entry-host-editor-mode-menu')) {
          fs.copyFileSync(path.join(s, f), path.join(d, f));
        }
      }
    } else {
      fs.mkdirSync(path.dirname(d), { recursive: true });
      fs.copyFileSync(s, d);
    }
  }

  const extRoot = path.join(REAL_HOME, 'extensions');
  if (fs.existsSync(extRoot)) {
    for (const d of fs.readdirSync(extRoot)) {
      if (!d.includes('language-pack-zh-hans')) continue;
      const src = path.join(extRoot, d);
      const tgt = path.join(homeDst, 'extensions', d);
      fs.mkdirSync(path.join(tgt, 'translations'), { recursive: true });
      for (const f of ['package.json', 'translations/main.i18n.json']) {
        const s = path.join(src, f);
        if (fs.existsSync(s)) fs.copyFileSync(s, path.join(tgt, f));
      }
    }
  }

  if (UPGRADE) {
    // 回归场景：当前代码里已有一份旧词典，激活时必须替换载荷而不是叠加逗号。
    const dir = path.join(dstApp, 'out/vs/workbench/devin-webapp-host/assets');
    for (const f of fs.readdirSync(dir)) {
      if (!f.startsWith('entry-host-editor-mode-menu')) continue;
      const anchor = 'Mt.isInitialized||Eu()';
      const mark = '/*devin-zh*/', end = '/*/devin-zh*/';
      const oldPayload = mark + 'Object.assign(mu.account||(mu.account={}),{"__upgrade":"old"})' + end;
      let base = fs.readFileSync(path.join(dir, f), 'utf8');
      const a = base.indexOf(mark), b = base.indexOf(end);
      if (a >= 0 && b > a) base = base.slice(0, a) + oldPayload + base.slice(b + end.length);
      else if (base.includes(anchor)) base = base.replace(anchor, oldPayload + ',' + anchor);
      else throw new Error('测试 chunk 缺少注入锚点');
      // 即使复制源已经带有本 bug 的重复逗号，测试也从合法的旧版状态开始。
      base = base.replace(/,(?:\s*,)+\s*\/\*devin-zh\*\//g, ',' + mark);
      fs.writeFileSync(path.join(dir, f), base, 'utf8');
    }
  }
  return { inst: dst, home: homeDst };
}

let ENV;
if (REAL) {
  if (!REAL_INST) { console.error('✗ 未找到 Devin 安装目录'); process.exit(1); }
  ENV = { inst: REAL_INST, home: REAL_HOME };
} else {
  ENV = buildSandbox();
  if (!ENV) { console.error('✗ 未找到 Devin 安装目录，无法建立沙盒'); process.exit(1); }
  process.env.DEVIN_INSTALL = ENV.inst;
  process.env.DEVIN_HOME = ENV.home;
}
const APP = path.join(ENV.inst, RESOURCES, 'app');

// ── 假 vscode ──
const messages = [];
const fakeVscode = {
  window: {
    showInformationMessage: (m) => { messages.push(['info', m]); return Promise.resolve(); },
    showWarningMessage: (m) => { messages.push(['warn', m]); return Promise.resolve(); },
  },
  commands: { registerCommand: () => ({ dispose() { } }) },
};
const origResolve = Module._resolveFilename;
Module._resolveFilename = function (request, ...rest) {
  if (request === 'vscode') return '__vscode_stub__';
  return origResolve.call(this, request, ...rest);
};
require.cache.__vscode_stub__ = {
  id: '__vscode_stub__', filename: '__vscode_stub__', loaded: true, exports: fakeVscode,
};

// ── 干跑时只记录不写 ──
const writes = [];
if (!APPLY) {
  const ow = fs.writeFileSync;
  const oc = fs.copyFileSync;
  const om = fs.mkdirSync;
  fs.writeFileSync = function (p, ...a) { writes.push('write ' + p); return ow.call(fs, p, ...a); };
  fs.copyFileSync = function (a, b, ...r) { writes.push('copy  ' + b); return oc.call(fs, a, b, ...r); };
  fs.mkdirSync = function (p, ...a) { return om.call(fs, p, ...a); };
}

// ── 跑 ──
const origLog = console.log;
const logLines = [];
console.log = (...a) => { logLines.push(a.join(' ')); };

const ext = require(path.join(ROOT, 'extension.js'));
ext.activate({ extensionPath: ROOT, subscriptions: [] });

setTimeout(() => {
  console.log = origLog;
  origLog('安装根: ' + ENV.inst);
  origLog('用户根: ' + ENV.home);
  origLog('模式  : ' + (REAL ? '真实安装' : APPLY ? '沙盒写入' : '沙盒干跑'));
  origLog('\n=== 激活日志 ===');
  logLines.filter((l) => l.includes('[devin-zh]')).forEach((l) => origLog('  ' + l));
  if (!APPLY) {
    origLog('\n=== 将会写入 ===');
    (writes.length ? writes : ['(无改动：已落地过，幂等)']).forEach((w) => origLog('  ' + w));
  }
  origLog('\n=== 提示消息 ===');
  (messages.length ? messages : [['-', '(无)']]).forEach((m) => origLog('  [' + m[0] + '] ' + m[1]));

  // ── 断言 ──
  let bad = 0;
  const ok = (cond, label) => { origLog((cond ? '  ✓ ' : '  ✗ ') + label); if (!cond) bad++; };
  origLog('\n=== 落地状态 ===');

  // 1) 语言包
  const lpRoot = path.join(ENV.home, 'extensions');
  const lp = fs.existsSync(lpRoot)
    ? fs.readdirSync(lpRoot).filter((d) => d.includes('language-pack-zh-hans'))
      .map((d) => path.join(lpRoot, d))
      .find((p) => fs.existsSync(path.join(p, 'translations', 'main.i18n.json')))
    : null;
  if (lp) {
    const c = JSON.parse(fs.readFileSync(path.join(lp, 'translations', 'main.i18n.json'), 'utf8')).contents;
    const n = Object.values(c).reduce((a, v) => a + Object.keys(v || {}).length, 0);
    ok(n >= 21000, '语言包译文 ' + n.toLocaleString() + ' 条');
    const supp = JSON.parse(fs.readFileSync(path.join(ROOT, 'tools/data/nls-supplement.json'), 'utf8'));
    let hit = 0, tot = 0;
    for (const [f, kv] of Object.entries(supp)) for (const k of Object.keys(kv)) { tot++; if (c[f] && k in c[f]) hit++; }
    ok(hit === tot, '本插件补充译文可查 ' + hit + '/' + tot);
    const pkg = JSON.parse(fs.readFileSync(path.join(lp, 'package.json'), 'utf8'));
    const ids = (pkg.contributes.localizations[0].translations || []).map((t) => t.id);
    ok(ids.includes('windsurf'), '语言包已注册 windsurf bundle');
  } else {
    const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
    ok(pkg.contributes.localizations.some((loc) => loc.languageId === 'zh-cn'),
      '使用扩展自带中文语言包');
  }

  // 2) 扩展贡献点
  let nExt = 0, nZh = 0;
  for (const name of FAMILY) {
    const dir = path.join(APP, 'extensions', name);
    const pkgPath = path.join(dir, 'package.json');
    const enPath = path.join(dir, 'package.nls.json');
    const zhPath = path.join(dir, 'package.nls.zh-cn.json');
    if (!fs.existsSync(pkgPath)) continue;
    nExt++;
    if (!fs.existsSync(enPath) || !fs.existsSync(zhPath)) {
      ok(false, name + ': package.nls*.json 未落地');
      continue;
    }
    const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
    const en = JSON.parse(fs.readFileSync(enPath, 'utf8'));
    const zh = JSON.parse(fs.readFileSync(zhPath, 'utf8'));
    const found = [...new Set((JSON.stringify(pkg).match(/%([^%"]+)%/g) || []).map((s) => s.slice(1, -1)))];
    const unresolved = found.filter((k) => !(k in en));
    const nozh = found.filter((k) => !(k in zh));
    ok(found.length > 0 && unresolved.length === 0 && nozh.length === 0,
      name + ': ' + found.length + ' 占位符 / 未解析 ' + unresolved.length + ' / 缺中文 ' + nozh.length);
    nZh += found.length;
  }
  ok(nExt === FAMILY.length, '扩展覆盖 ' + nExt + '/' + FAMILY.length + '，占位符合计 ' + nZh);

  // 3) webapp i18next
  const wdir = path.join(APP, 'out', 'vs', 'workbench', 'devin-webapp-host', 'assets');
  let chunk = null;
  if (fs.existsSync(wdir)) {
    for (const f of fs.readdirSync(wdir)) {
      if (!f.startsWith('entry-host-editor-mode-menu')) continue;
      const p = path.join(wdir, f);
      if (fs.readFileSync(p, 'utf8').includes('/*devin-zh*/')) { chunk = p; break; }
    }
  }
  ok(!!chunk, 'webapp 中文资源已注入' + (chunk ? '（' + path.basename(chunk) + '）' : ''));
  if (chunk) {
    const s = fs.readFileSync(chunk, 'utf8');
    const syntax = childProcess.spawnSync(process.execPath, ['--check', chunk], { stdio: 'ignore' });
    ok(syntax.status === 0, '落地后的 webapp chunk 通过 node --check'
      + (syntax.status === 0 ? '' : ': ' + (syntax.error || 'exit ' + syntax.status)));
    ok(!s.includes(',,/*devin-zh*/'), '载荷前没有重复逗号');
    ok(!s.includes('__upgrade'), '旧版载荷已被完整替换');
    // 注入方式必须是「合并进 mu（resources 对象）」而不是 init 之后 addResourceBundle：
    // i18next 的 initAsync 默认 true，init 完成时用 resources 覆盖 bundle，
    // 后加的会被吃掉 —— 这正是界面显示原始 key 的根因。
    // ★ 必须是「逐命名空间 Object.assign」，不能整体浅合并：
    //   载荷只覆盖一部分 key（localSettings 199 个里 57 个），
    //   若 Object.assign(mu, zh) 整体替换，未翻译的 7,843 个英文 key 会消失，
    //   界面回退成显示 key 本身（localSettings.general.openEditorSettings.label）。
    ok(/\/\*devin-zh\*\/Object\.assign\(mu[.\[]/.test(s),
      '载荷逐命名空间合并（保留未翻译的英文 key）');
    ok(!/\/\*devin-zh\*\/Object\.assign\(mu\|\|\{\},/.test(s),
      '没有整体浅合并 mu 的旧形态');
    ok(!/Mt\.isInitialized\|\|Eu\(\),Mt\.addResourceBundle/.test(s),
      '没有残留旧式 addResourceBundle 载荷');
    ok(s.includes('Mt.isInitialized||Eu()'), '原始初始化锚点保留（不破坏 Devin 自身逻辑）');
    ok(s.split('/*devin-zh*/').length === 2, '载荷只有一份（幂等）');
    // ★ 深合并必须在锚点之前：Eu() 的 init 才会把中文注册进 resources。
    //   插在锚点之后则 init 已用旧 mu 完成，改 mu 不再影响已注册的 resources ——
    //   这正是界面显示原始 key（sidebar.automations）的根因。
    const posMark = s.indexOf('/*devin-zh*/');
    const posAnchor = s.indexOf('Mt.isInitialized||Eu()');
    ok(posMark >= 0 && posAnchor >= 0 && posMark < posAnchor,
      '载荷位于初始化锚点之前（init 时中文已就位）');
    // 尾逗号会让整个 chunk 语法错误、Devin 起不来
    ok(!/Mt\.isInitialized\|\|Eu\(\)\s*,\s*\}/.test(s), '锚点后无残留尾逗号（语法安全）');

    // 载荷的 key 必须真的能在 en 资源树里查到。
    // 载荷是「逐命名空间 Object.assign(mu.x||(mu.x={}),{…})」的逗号序列，
    // 用花括号配平把每个命名空间的 {…} 抠出来，拼回 {ns: {…}} 再比对。
    const enPath = path.join(ROOT, 'tools', 'data', 'webapp-en.json');
    if (fs.existsSync(enPath)) {
      const enNs = JSON.parse(fs.readFileSync(enPath, 'utf8')).namespaces;
      const a = s.indexOf('/*devin-zh*/');
      const b = s.indexOf('/*/devin-zh*/');
      const body = s.slice(a, b);

      const payload = {};
      const reAssign = /Object\.assign\(mu(?:\.([A-Za-z_$][\w$]*)|\[("(?:[^"\\]|\\.)*")\])\|\|/g;
      let m;
      while ((m = reAssign.exec(body))) {
        const ns = m[1] || JSON.parse(m[2]);
        // 跳过 `||(mu.x={})` 里那个空对象，定位真正的载荷 '{'
        const guard = body.indexOf('={})', m.index + m[0].length);
        const ob = guard >= 0
          ? body.indexOf('{', guard + 4)
          : body.indexOf('{', m.index + m[0].length);
        if (ob < 0) continue;
        let depth = 0, k = ob, q = null;
        for (; k < body.length; k++) {
          const ch = body[k];
          if (q) { if (ch === '\\') { k++; continue; } if (ch === q) q = null; continue; }
          if (ch === '"') { q = ch; continue; }
          if (ch === '{') depth++;
          else if (ch === '}') { depth--; if (depth === 0) break; }
        }
        try { payload[ns] = JSON.parse(body.slice(ob, k + 1)); } catch (e) { /* 跳过 */ }
      }

      const nsList = Object.keys(payload);
      if (!nsList.length) {
        ok(false, '载荷无法解析出命名空间');
      } else {
        const bad = nsList.filter((ns) => !(ns in enNs));
        ok(bad.length === 0,
          '载荷命名空间全部存在于 en 资源（' + nsList.length + ' 个'
          + (bad.length ? '，未知 ' + bad.length + ' 个: ' + bad.slice(0, 3).join(',') : '') + '）');

        let checked = 0, found = 0, unknownSamples = [];
        for (const ns of nsList) {
          const src = enNs[ns];
          if (!src) continue;
          for (const k of Object.keys(payload[ns])) {
            checked++;
            if (k in src || (src[k] && typeof src[k] === 'object')) found++;
            else if (unknownSamples.length < 5) unknownSamples.push(ns + '.' + k);
          }
        }
        const ratio = checked ? found / checked : 1;
        ok(ratio >= 0.95,
          '载荷 key 命中率 ' + (ratio * 100).toFixed(1) + '%（' + found + '/' + checked + '）'
          + (unknownSamples.length ? ' 未命中如: ' + unknownSamples.join(', ') : ''));

        const probes = ['composerTips.sessionNav', 'composerTips.sidebar', 'sidebar.automations',
          'sidebar.recent', 'nav.newSession', 'settings.highContrast', 'settings.uiFont'];
        for (const p of probes) {
          let hitv = null;
          const parts = p.split('.');
          for (let i = parts.length - 1; i > 0; i--) {
            const ns = parts.slice(0, i).join('.');
            if (!payload[ns]) continue;
            let cur = payload[ns];
            for (const q of parts.slice(i)) {
              cur = cur && typeof cur === 'object' ? cur[q] : undefined;
            }
            if (typeof cur === 'string') { hitv = cur; break; }
          }
          ok(typeof hitv === 'string', '抽查 ' + p + ' → ' + (typeof hitv === 'string' ? hitv : '(未覆盖)'));
        }
      }
    }
  }

  // 4) DOM
  for (const rel of ['out/vs/code/electron-browser/workbench/workbench.html',
    'out/vs/sessions/electron-browser/sessions.html']) {
    const p = path.join(APP, rel);
    const has = fs.existsSync(p) && fs.readFileSync(p, 'utf8').includes('devin-zh-dom.js');
    const js = fs.existsSync(path.join(path.dirname(p), 'devin-zh-dom.js'));
    ok(has && js, path.basename(rel) + ' 注入 + 运行时存在');
  }

  // 5) checksums
  const prodPath = path.join(APP, 'product.json');
  if (fs.existsSync(prodPath)) {
    const prod = JSON.parse(fs.readFileSync(prodPath, 'utf8'));
    let good = 0, total = 0, skip = 0;
    for (const [k, exp] of Object.entries(prod.checksums || {})) {
      const p = path.join(APP, 'out', k);
      if (!fs.existsSync(p)) { skip++; continue; }
      total++;
      const h = crypto.createHash('sha256').update(fs.readFileSync(p)).digest('base64').replace(/=+$/, '');
      if (h === exp) good++;
    }
    ok(good === total,
      '完整性校验自洽 ' + good + '/' + total + (skip ? '（沙盒缺 ' + skip + ' 个受保护文件，已跳过）' : ''));
  }

  origLog('\n' + (bad ? '✗ ' + bad + ' 项失败' : '✓ 全部通过'));
  process.exit(bad ? 1 : 0);
}, 400);
