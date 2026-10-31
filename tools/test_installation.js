'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const ROOT = path.resolve(__dirname, '..');
const SOURCE = fs.readFileSync(path.join(ROOT, 'extension.js'), 'utf8');

function loadExtension({ platform, env = {}, appRoot, home = os.homedir(), fileSystem = fs,
  pathModule = platform === 'win32' ? path.win32 : path.posix }) {
  const commands = {};
  const messages = [];
  const executions = [];
  const vscode = {
    env: { appRoot },
    window: {
      showInformationMessage: async (message) => { messages.push(message); },
      showWarningMessage: async (message, options, ...choices) => {
        messages.push(message);
        return choices[0];
      },
    },
    commands: {
      registerCommand: (name, callback) => {
        commands[name] = callback;
        return { dispose() {} };
      },
      executeCommand: async (...args) => { executions.push(args); },
    },
  };
  const context = {
    module: { exports: {} },
    console: { log() {} },
    process: { platform, env, execPath: process.execPath, pid: process.pid },
    require(name) {
      if (name === 'vscode') return vscode;
      if (name === 'fs') return fileSystem;
      if (name === 'os') return { homedir: () => home, tmpdir: os.tmpdir };
      if (name === 'path') return pathModule;
      return require(name);
    },
  };
  vm.runInNewContext(SOURCE + '\nmodule.exports.probe = { findDevinInstall, devinApp, backup };', context);
  return { ...context.module.exports, commands, messages, executions };
}

test('macOS detects appRoot, system/user installs, and explicit bundle/Contents paths', () => {
  const cases = [
    [{ appRoot: '/custom/Devin.app/Contents/Resources/app' }, '/custom/Devin.app/Contents'],
    [{}, '/Applications/Devin.app/Contents'],
    [{}, '/home/test/Applications/Devin.app/Contents'],
    [{ env: { DEVIN_INSTALL: '/override/Devin.app/Contents' } }, '/override/Devin.app/Contents'],
    [{ env: { DEVIN_INSTALL: '/override/Devin.app' } }, '/override/Devin.app/Contents'],
  ];
  for (const [options, expected] of cases) {
    // Exact string matching also tests case-sensitive Resources resolution.
    const files = new Set([expected + '/Resources/app/product.json', expected + '/Resources/app']);
    const ext = loadExtension({
      platform: 'darwin', home: '/home/test', ...options,
      fileSystem: { existsSync: (p) => files.has(p) },
    });
    assert.equal(ext.probe.findDevinInstall(), expected);
    assert.equal(ext.probe.devinApp(expected), expected + '/Resources/app');
  }
  const missing = loadExtension({ platform: 'darwin', fileSystem: { existsSync: () => false } });
  assert.equal(missing.probe.findDevinInstall(), null);
});

test('Windows retains explicit, LOCALAPPDATA, and Program Files installation discovery', () => {
  const cases = [
    [{ DEVIN_INSTALL: 'D:\\Apps\\Devin' }, 'D:\\Apps\\Devin'],
    [{ LOCALAPPDATA: 'C:\\Users\\test\\AppData\\Local' }, 'C:\\Users\\test\\AppData\\Local\\Programs\\Devin'],
    [{}, 'C:\\Program Files\\Devin'],
  ];
  for (const [env, expected] of cases) {
    const ext = loadExtension({
      platform: 'win32', env,
      fileSystem: { existsSync: (p) => p === path.win32.join(expected, 'Devin.exe') },
    });
    assert.equal(ext.probe.findDevinInstall(), expected);
    assert.equal(ext.probe.devinApp(expected), path.win32.join(expected, 'resources', 'app'));
  }
});

function write(p, value) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, typeof value === 'string' ? value : JSON.stringify(value));
}

function snapshot(root) {
  const files = {};
  if (!fs.existsSync(root)) return files;
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const p = path.join(root, entry.name);
    if (entry.isDirectory()) Object.assign(files, snapshot(p));
    else files[p] = fs.readFileSync(p).toString('base64');
  }
  return files;
}

function makeFixture(t, mac) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'devin-zh-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const inst = path.join(root, mac ? 'Devin.app/Contents' : 'Devin');
  const app = path.join(inst, mac ? 'Resources' : 'resources', 'app');
  const home = path.join(root, 'home');
  if (!mac) write(path.join(inst, 'Devin.exe'), '');
  const plan = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/ext-manifest.json')));
  const en = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/ext-manifest.en.json')));
  for (const [name, entries] of Object.entries(plan)) {
    const pkg = { name };
    for (const entry of entries) {
      let obj = pkg;
      for (let i = 0; i < entry.path.length - 1; i++) {
        const key = entry.path[i];
        obj = obj[key] || (obj[key] = /^\d+$/.test(String(entry.path[i + 1])) ? [] : {});
      }
      obj[entry.path[entry.path.length - 1]] = en[entry.key];
    }
    write(path.join(app, 'extensions', name, 'package.json'), pkg);
  }
  const pages = [
    ['vs/code/electron-browser/workbench/workbench.html', './workbench.js'],
    ['vs/sessions/electron-browser/sessions.html', './sessions.js'],
  ];
  const checksums = {};
  for (const [rel, anchor] of pages) {
    const file = path.join(app, 'out', rel);
    write(file, '<script src="' + anchor + '" type="module"></script>');
    checksums[rel] = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('base64').replace(/=+$/, '');
  }
  write(path.join(app, 'product.json'), { version: 'test', checksums });
  const chunk = path.join(app, 'out/vs/workbench/devin-webapp-host/assets/entry-host-editor-mode-menu-test.js');
  write(chunk, 'var mu={};var Mt={isInitialized:false};function Eu(){Mt.isInitialized=true}Mt.isInitialized||Eu();');
  const lp = path.join(home, 'extensions/test.language-pack-zh-hans');
  write(path.join(lp, 'package.json'), { contributes: { localizations: [{ translations: [] }] } });
  write(path.join(lp, 'translations/main.i18n.json'), { contents: { original: { key: 'original' } } });
  // A pre-existing runtime must be restored, not deleted.
  write(path.join(path.dirname(path.join(app, 'out', pages[0][0])), 'devin-zh-dom.js'), '// original runtime');
  return { inst, app, home, lp, chunk, pages };
}

for (const mac of [true, false]) {
  test(`${mac ? 'macOS' : 'Windows layout'}: four layers, idempotency, and complete rollback`, async (t) => {
    const fixture = makeFixture(t, mac);
    const { inst, app, home, lp, chunk, pages } = fixture;
    const before = { ...snapshot(app), ...snapshot(lp) };
    const ext = loadExtension({
      // On non-Windows hosts use native paths for real filesystem fixtures.
      platform: mac ? 'darwin' : process.platform === 'win32' ? 'win32' : 'linux',
      env: { DEVIN_INSTALL: inst, DEVIN_HOME: home },
      pathModule: path,
    });
    const activate = () => ext.activate({ extensionPath: ROOT, subscriptions: [] });
    activate();
    const patched = { ...snapshot(app), ...snapshot(lp) };
    assert.notDeepEqual(patched, before);
    assert.equal(fs.readFileSync(chunk, 'utf8').split('/*devin-zh*/').length, 2);
    for (const [rel] of pages) {
      const file = path.join(app, 'out', rel);
      assert.match(fs.readFileSync(file, 'utf8'), /devin-zh-dom\.js/);
      const expected = JSON.parse(fs.readFileSync(path.join(app, 'product.json'))).checksums[rel];
      const hash = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('base64').replace(/=+$/, '');
      assert.equal(hash, expected);
    }
    assert.ok(fs.readFileSync(path.join(lp, 'translations/main.i18n.json')).equals(
      fs.readFileSync(path.join(ROOT, 'translations/main.i18n.json'))));
    const plan = JSON.parse(fs.readFileSync(path.join(ROOT, 'assets/ext-manifest.json')));
    for (const [name, fields] of Object.entries(plan)) {
      const dir = path.join(app, 'extensions', name);
      const pkg = fs.readFileSync(path.join(dir, 'package.json'), 'utf8');
      const en = JSON.parse(fs.readFileSync(path.join(dir, 'package.nls.json')));
      const zh = JSON.parse(fs.readFileSync(path.join(dir, 'package.nls.zh-cn.json')));
      for (const field of fields) {
        assert.ok(pkg.includes('%' + field.key + '%'));
        assert.equal(typeof en[field.key], 'string');
        assert.equal(typeof zh[field.key], 'string');
      }
    }
    const index = path.join(home, 'devin-zh-backups/files-v2/manifest.json');
    const entries = JSON.parse(fs.readFileSync(index));
    const packages = Object.keys(entries).filter((p) => p.endsWith(path.sep + 'package.json'));
    assert.equal(packages.length, 6);
    assert.equal(new Set(packages.map((p) => entries[p])).size, 6);
    assert.ok(Object.values(entries).includes(null));
    const backups = snapshot(path.dirname(index));
    activate();
    assert.deepEqual({ ...snapshot(app), ...snapshot(lp) }, patched);
    assert.deepEqual(snapshot(path.dirname(index)), backups);
    await ext.commands['devin-zh.uninstall']();
    assert.deepEqual({ ...snapshot(app), ...snapshot(lp) }, before);
    assert.equal(JSON.stringify(ext.executions), JSON.stringify([
      ['workbench.extensions.uninstallExtension', 'devin-zh.devin-zh-hans'],
    ]));
  });
}

test('backup failure throws before modifying the original target', (t) => {
  const { inst, app, home } = makeFixture(t, true);
  const original = snapshot(app);
  const ext = loadExtension({
    platform: 'darwin', env: { DEVIN_INSTALL: inst, DEVIN_HOME: home },
    pathModule: path,
    fileSystem: {
      ...fs,
      copyFileSync(source, destination) {
        if (destination.includes('files-v2')) throw new Error('simulated backup failure');
        fs.copyFileSync(source, destination);
      },
    },
  });
  const file = path.join(app, 'product.json');
  assert.throws(() => ext.probe.backup(file), /simulated backup failure/);
  assert.deepEqual(snapshot(app), original);
});

test('missing backup aborts rollback before any target is restored', async (t) => {
  const { inst, app, home } = makeFixture(t, true);
  const ext = loadExtension({
    platform: 'darwin', env: { DEVIN_INSTALL: inst, DEVIN_HOME: home },
    pathModule: path,
  });
  ext.activate({ extensionPath: ROOT, subscriptions: [] });
  const patched = snapshot(app);
  const index = path.join(home, 'devin-zh-backups/files-v2/manifest.json');
  const entries = JSON.parse(fs.readFileSync(index));
  const backup = Object.values(entries).filter(Boolean).pop();
  fs.unlinkSync(backup);
  await ext.commands['devin-zh.uninstall']();
  assert.deepEqual(snapshot(app), patched);
  assert.equal(ext.executions.length, 0);
  assert.ok(ext.messages.some((message) => message.includes(backup)));
});

test('legacy basename-only backups are not used for automatic rollback', async (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'devin-zh-legacy-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  write(path.join(root, 'devin-zh-backups/vsix-ext/package.json'), '{}');
  const ext = loadExtension({
    platform: 'darwin', env: { DEVIN_HOME: root },
    pathModule: path, fileSystem: { ...fs, existsSync: (p) => p.startsWith(root) && fs.existsSync(p) },
  });
  ext.activate({ extensionPath: ROOT, subscriptions: [] });
  await ext.commands['devin-zh.uninstall']();
  assert.equal(ext.executions.length, 0);
  assert.ok(ext.messages.some((message) => message.includes('vsix-*')));
});
