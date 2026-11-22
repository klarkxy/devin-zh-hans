/* 验证 DOM 层保留输入内容、菜单访问键、快捷键与多义产品名，同时正常翻译普通文本。 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function element(tagName, attrs = {}) {
  return {
    nodeType: 1,
    tagName,
    attrs: { ...attrs },
    parentElement: null,
    isContentEditable: false,
    getAttribute(name) { return this.attrs[name] ?? null; },
    setAttribute(name, value) { this.attrs[name] = value; },
    matches() { return false; },
    querySelectorAll() { return []; },
  };
}

const input = element('INPUT', { placeholder: 'Search all models', value: 'User text stays unchanged' });
const editable = element('INPUT', { placeholder: 'Search all models' });
editable.isContentEditable = true;
const body = element('BODY');
body.querySelectorAll = (selector) => selector.includes('input[placeholder]') ? [input, editable] : [];
input.parentElement = body;
editable.parentElement = body;
const documentElement = element('HTML');
body.parentElement = documentElement;

const accessKeys = 'CEFLMOSTWs'.split('').map((letter) => ({
  nodeType: 3,
  nodeValue: letter,
  parentElement: body,
}));
const regularText = { nodeType: 3, nodeValue: 'Search all models', parentElement: body };
const mnemonic = element('MNEMONIC');
mnemonic.parentElement = body;
const mnemonicText = { nodeType: 3, nodeValue: 'Search all models', parentElement: mnemonic };
const keybinding = element('SPAN');
keybinding.parentElement = body;
keybinding.matches = (selector) => selector.includes('.monaco-keybinding');
const keybindingText = { nodeType: 3, nodeValue: 'Enter', parentElement: keybinding };
const productNames = ['Team', 'Teams', 'Max', 'Pro'].map((name) => ({
  nodeType: 3,
  nodeValue: name,
  parentElement: body,
}));
const textNodes = [...accessKeys, regularText, mnemonicText, keybindingText, ...productNames];

let observerOptions = null;
const document = {
  body,
  documentElement,
  createTreeWalker() {
    let index = 0;
    return { nextNode() { return textNodes[index++] || null; } };
  },
  addEventListener() {},
};
const window = {
  setTimeout() { return 1; },
  setInterval() { return 1; },
  clearInterval() {},
  requestAnimationFrame(fn) { fn(); return 1; },
};
const context = {
  window,
  document,
  console: { log() {} },
  NodeFilter: { SHOW_TEXT: 4, FILTER_ACCEPT: 1, FILTER_REJECT: 2 },
  MutationObserver: class {
    constructor(callback) { this.callback = callback; }
    observe(_target, options) { observerOptions = options; }
  },
  WeakSet,
};
window.MutationObserver = context.MutationObserver;
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../dist/devin-zh-dom.js'), 'utf8'), context);

const results = [
  [input.attrs.placeholder === '搜索所有模型', '普通输入框 placeholder 已翻译'],
  [input.attrs.value === 'User text stays unchanged', '输入内容未被修改'],
  [editable.attrs.placeholder === 'Search all models', 'contenteditable 区域保持跳过'],
  [accessKeys.every((node, index) => node.nodeValue === 'CEFLMOSTWs'[index]),
    '单字母菜单访问键保持原文'],
  [regularText.nodeValue === '搜索所有模型', '普通文本仍正常翻译'],
  [mnemonicText.nodeValue === 'Search all models', 'mnemonic 节点整体跳过'],
  [keybindingText.nodeValue === 'Enter', 'Monaco 快捷键标签保持按键原文'],
  [productNames.every((node, index) => node.nodeValue === ['Team', 'Teams', 'Max', 'Pro'][index]),
    '多义产品名不被 DOM 全局词典覆盖'],
  [observerOptions && observerOptions.attributes === true
    && observerOptions.attributeFilter.includes('placeholder'), 'placeholder 属性变化已纳入观察'],
];
let failed = 0;
for (const [ok, label] of results) {
  console.log((ok ? '✓ ' : '✗ ') + label);
  if (!ok) failed++;
}
console.log((results.length - failed) + '/' + results.length + ' 通过');
process.exit(failed ? 1 : 0);
