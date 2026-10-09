// Checks the card-back image the page uses. Run: node --test
// (Its half-turn symmetry is measured when it is built: card-backs/web_back.py.)
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const BACK = 'img/card-back.jpg';

// Width and height from a JPEG's start-of-frame marker.
function jpegSize(buf) {
  assert.equal(buf.readUInt16BE(0), 0xffd8, 'not a JPEG');
  let i = 2;
  while (i < buf.length) {
    const marker = buf.readUInt16BE(i);
    const len = buf.readUInt16BE(i + 2);
    if (marker >= 0xffc0 && marker <= 0xffc3) {
      return { height: buf.readUInt16BE(i + 5), width: buf.readUInt16BE(i + 7) };
    }
    i += 2 + len;
  }
  throw new Error('no frame marker');
}

test('card back: the page uses it', () => {
  const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.ok(html.includes(`url("${BACK}")`));
});

test('card back: a JPEG in the card shape (7 : 12)', () => {
  const { width, height } = jpegSize(fs.readFileSync(path.join(root, BACK)));
  assert.deepEqual({ width, height }, { width: 704, height: 1200 });
  assert.ok(Math.abs(width / height - 7 / 12) < 0.01);
});
