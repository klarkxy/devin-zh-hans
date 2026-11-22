'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const ROOT = path.resolve(__dirname, '..');

function rd(rel) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
}

test('file-sharing settings keep Devin Cloud in the built-in extension pack', () => {
  const zh = rd('assets/ext-manifest.zh.json');
  const key = 'windsurf.contributes.configuration.properties.devin.acp.shareUserEdits.description';
  assert.match(zh[key], /Devin Cloud/);
  assert.doesNotMatch(zh[key], /Devin 云会话/);
});

test('account and billing keep Pro untranslated like Max and Teams', () => {
  const wa = rd('assets/webapp-i18n.json');
  const en = rd('tools/data/webapp-en.json').namespaces;
  assert.equal(en.auth['accountPicker.tierPro'], 'Pro');
  assert.equal(en.billing['planNames.pro'], 'Pro');
  assert.equal(wa.auth['accountPicker.tierPro'], undefined);
  assert.equal(wa.billing['planNames.pro'], undefined);
  assert.equal(wa.auth['accountPicker.tierMax'], undefined);
  assert.equal(wa.billing['planNames.max'], undefined);
});

test('automation and cron date pickers use distinct weekday initials', () => {
  const wa = rd('assets/webapp-i18n.json');
  assert.equal(wa.automations.dayInitialSunday, '日');
  assert.equal(wa.automations.dayInitialSaturday, '六');
  assert.equal(wa.automations.dayInitialTuesday, '二');
  assert.equal(wa.automations.dayInitialThursday, '四');
  assert.equal(wa.ui['crontabEditor.daySun'], '日');
  assert.equal(wa.ui['crontabEditor.daySat'], '六');
  assert.equal(wa.ui['crontabEditor.dayTue'], '二');
  assert.equal(wa.ui['crontabEditor.dayThu'], '四');
});
