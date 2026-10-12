// Checks print/mpc_print.py makes MakePlayingCards-sized files. Run: node --test
// Needs Python 3 with Pillow and NumPy; without them the test is skipped, not failed.
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.join(__dirname, '..');
const hasPython = spawnSync('python3', ['-c', 'import PIL, numpy'], { stdio: 'ignore' }).status === 0;

// Width and height from a JPEG's start-of-frame marker, or a PNG's header.
function imageSize(buf) {
  if (buf.readUInt32BE(0) === 0x89504e47) return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
  let i = 2;
  while (i < buf.length) {
    const marker = buf.readUInt16BE(i);
    if (marker >= 0xffc0 && marker <= 0xffc3) return { height: buf.readUInt16BE(i + 5), width: buf.readUInt16BE(i + 7) };
    i += 2 + buf.readUInt16BE(i + 2);
  }
  throw new Error('no frame marker');
}

test('print files: MPC size (897 x 1497), symmetric back, both fits', { skip: !hasPython && 'python3 with Pillow and NumPy not found' }, () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'mpc-'));
  const back = path.join(tmp, 'back-source.png');
  // A stand-in card back: cream, with a teal frame. (The real back is kept out of the repository.)
  const make = spawnSync('python3', ['-I', '-c',
    'import sys; from PIL import Image, ImageDraw; im = Image.new("RGB", (620, 1110), (232, 220, 200)); ' +
    'ImageDraw.Draw(im).rectangle((60, 60, 559, 1049), outline=(12, 69, 76), width=8); im.save(sys.argv[1])', back]);
  assert.equal(make.status, 0, String(make.stderr));
  for (const fit of ['safe', 'original']) {
    const out = path.join(tmp, fit);
    const run = spawnSync('python3', ['-I', path.join(root, 'print/mpc_print.py'), out, '--fit', fit, '--back', back, '--only', '00,77'], { encoding: 'utf8' });
    assert.equal(run.status, 0, run.stdout + run.stderr);
    assert.match(run.stdout, /largest difference from its half turn: 0\n/);
    for (const f of ['00.jpg', '77.jpg', 'back.png']) {
      assert.deepEqual(imageSize(fs.readFileSync(path.join(out, f))), { width: 897, height: 1497 }, `${fit}/${f}`);
    }
    assert.ok(fs.existsSync(path.join(out, 'check-sheet.jpg')));
  }
  fs.rmSync(tmp, { recursive: true, force: true });
});
