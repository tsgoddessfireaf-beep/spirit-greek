// Keeps the "reading survives a refresh" wiring from slipping. The full refresh,
// leave-and-return and New reading checks were run in a real browser (see the PR).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const block = html.slice(html.indexOf('Keep the reading through a refresh'));

test('the reading is saved after the deal and after each card or pile is turned', () => {
  assert.match(html, /state = 'done';\n    s\.receiptText = els\.receipt\.textContent;\n    saveReading\(\);/);
  assert.match(html, /else \{ turnOver\(card\); saveReading\(\); \}/);
  assert.match(html, /s\.turned\.add\(p\);\n    saveReading\(\);/);
});

test('New reading, a new shuffle and another spread throw the saved reading away', () => {
  assert.match(html, /\$\('again'\)\.addEventListener\('click', \(\) => \{\n    clearSaved\(\);/);
  assert.match(html, /state = 'starting';\n    releaseQueued = false;\n    clearSaved\(\);/);
  assert.match(html, /clearSaved\(\);\n    selectSpread\(b\.dataset\.spread\);/);
});

test('the saved reading lives only in this browser and is restored on load', () => {
  assert.match(block, /localStorage\.setItem\(SAVE_KEY/);
  assert.match(block, /const saved = loadSaved\(\);\n  if \(saved\) \{/);
  assert.ok(!/fetch\(|sendBeacon|XMLHttpRequest/.test(block), 'saving never sends anything');
});
