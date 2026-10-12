// Checks the privacy-sensitive parts of the "Get my reading" button on the page.
// The full click-through was checked in a real browser; these keep the rules from slipping.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const readme = fs.readFileSync(path.join(__dirname, '..', 'README.md'), 'utf8');
const start = html.indexOf('Written reading (optional)');
const end = html.indexOf("renderEmptySpread();\n  setStatus(secureOk");
const block = html.slice(start, end);

test('the reading code block is found', () => {
  assert.ok(start > 0 && end > start);
});

test('the page only talks to the Aeonic Arts reading server', () => {
  assert.match(block, /https:\/\/us-central1-cogent-spirit-498920-j3\.cloudfunctions\.net/);
  assert.equal((block.match(/fetch\(/g) || []).length, 2, 'only reading and deleteReading');
});

test('server text is shown as plain text, never as markup', () => {
  assert.ok(!/innerHTML|insertAdjacentHTML|outerHTML/.test(block), 'no HTML injection in the reading code');
});

test('saving the question starts unticked and needs a question', () => {
  assert.match(html, /<input type="checkbox" id="saveQ">/);
  assert.ok(!/id="saveQ"[^>]*checked/.test(html));
  assert.match(block, /consent: \$\('saveQ'\)\.checked && Boolean\(s\.question\)/);
});

test('the page makes no other network calls: both fetches are inside the button code', () => {
  assert.equal((html.match(/fetch\(/g) || []).length, 2);
  assert.ok(!/XMLHttpRequest|sendBeacon|WebSocket|navigator\.share/.test(html));
});

test('the wording no longer claims nothing is ever sent', () => {
  assert.ok(!/Nothing is stored or sent anywhere/.test(html));
  assert.ok(!/never leaves this phone/.test(html));
  assert.ok(!/Nothing is stored or sent anywhere/.test(readme));
  assert.match(html, /Get my reading/);
});
