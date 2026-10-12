// GitHub Pages must publish this repository as plain files. Without .nojekyll, GitHub runs
// Jekyll, which crashes on "{{" in knowledge/sources/waite-pkt-part3.wikisource.md and
// stops every page update (found 2026-10-12: the live page was stuck on an old version).
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

test('.nojekyll exists so GitHub Pages skips Jekyll', () => {
  assert.ok(fs.existsSync(path.join(__dirname, '..', '.nojekyll')));
});

test('the saved source text really does contain Liquid markers (why .nojekyll matters)', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'knowledge', 'sources', 'waite-pkt-part3.wikisource.md'), 'utf8');
  assert.match(src, /\{\{/);
});
