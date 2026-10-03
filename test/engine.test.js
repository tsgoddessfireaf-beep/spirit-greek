// Fairness proof for the Intuitive Shuffle engine. Run: node --test
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('../engine.js');
const { CARDS, SPREADS } = require('../deck.js');

const hexToBytes = (hex) => Uint8Array.from(hex.match(/../g), (h) => parseInt(h, 16));

// A master stream with a fixed seed, so every run gives identical results (never flaky).
function masterRng(label) {
  const seed = new Uint8Array(32);
  for (let i = 0; i < label.length; i++) seed[i % 32] ^= label.charCodeAt(i);
  return E.createRng(seed);
}
function seedFrom(rng) {
  const bytes = new Uint8Array(32);
  for (let i = 0; i < 32; i += 4) {
    const w = rng.nextU32();
    bytes[i] = w & 255; bytes[i + 1] = (w >>> 8) & 255;
    bytes[i + 2] = (w >>> 16) & 255; bytes[i + 3] = w >>> 24;
  }
  return bytes;
}

// Chi-square critical value, Wilson-Hilferty approximation. z = 3.72 is a 1-in-10,000 cut-off.
function chiSquareCritical(df, z = 3.72) {
  const a = 2 / (9 * df);
  return df * (1 - a + z * Math.sqrt(a)) ** 3;
}
function chiSquare(counts) {
  const total = counts.reduce((s, c) => s + c, 0);
  const expected = total / counts.length;
  return counts.reduce((s, c) => s + (c - expected) ** 2 / expected, 0);
}

test('deck has 78 unique cards; spreads are sized correctly', () => {
  assert.equal(CARDS.length, 78);
  assert.equal(new Set(CARDS.map((c) => c.name)).size, 78);
  assert.equal(CARDS.filter((c) => c.arcana === 'major').length, 22);
  assert.equal(SPREADS.one.positions.length, 1);
  assert.equal(SPREADS.three.positions.length, 3);
  assert.equal(SPREADS.celtic.positions.length, 10);
});

test('ChaCha20 block matches the RFC 8439 section 2.3.2 test vector', () => {
  const key = E.bytesToWords(hexToBytes(
    '000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f'));
  const nonce = E.bytesToWords(hexToBytes('000000090000004a00000000'));
  const out = Array.from(E.chachaBlock(key, 1, nonce), (w) => w.toString(16).padStart(8, '0'));
  assert.deepEqual(out, [
    'e4e7f110', '15593bd1', '1fdd0f50', 'c47120a3',
    'c7f4d1c7', '0368c033', '9aaa2204', '4e6cd4c3',
    '466482d2', '09aa9f07', '05d7c214', 'a2028bd9',
    'd19c12b5', 'b94e16de', 'e883d0cb', '4e3c50a2',
  ]);
});

test('randomInt stays in range and is even across a small range', () => {
  const rng = masterRng('randomInt');
  const counts = new Array(7).fill(0);
  for (let i = 0; i < 70000; i++) counts[E.randomInt(rng, 7)]++;
  assert.ok(chiSquare(counts) < chiSquareCritical(6));
});

test('200,000 Celtic Cross readings: every card equally likely in every position', () => {
  const master = masterRng('fairness');
  const N = 200000;
  const size = 10;
  // counts[source][position][card]
  const counts = {
    jumper: Array.from({ length: size }, () => new Array(78).fill(0)),
    dealt: Array.from({ length: size }, () => new Array(78).fill(0)),
  };
  let reversedCount = 0;
  for (let r = 0; r < N; r++) {
    const reading = E.createReading({
      spreadSize: size, sessionRng: E.createRng(seedFrom(master)), reversals: true,
    });
    const jumperCount = E.randomInt(master, size + 1); // 0..10 jumpers, all cases covered
    for (let j = 0; j < jumperCount; j++) reading.addJumper(j);
    const spread = reading.deal(E.createRng(seedFrom(master)));

    const ids = spread.map((p) => p.card);
    assert.equal(new Set(ids).size, size, 'no card may appear twice in one spread');
    spread.forEach((p, pos) => {
      counts[p.source][pos][p.card]++;
      if (p.reversed) reversedCount++;
    });
  }
  const critical = chiSquareCritical(77);
  for (const source of ['jumper', 'dealt']) {
    counts[source].forEach((row, pos) => {
      const stat = chiSquare(row);
      assert.ok(stat < critical,
        `${source} position ${pos + 1}: chi-square ${stat.toFixed(1)} >= ${critical.toFixed(1)}`);
    });
  }
  const reversedShare = reversedCount / (N * size);
  assert.ok(Math.abs(reversedShare - 0.5) < 0.005, `reversed share ${reversedShare}`);
});

test('jumper rarity matches the table (chance of at least one jumper in 30 s)', () => {
  const rng = masterRng('rarity');
  const u01 = () => rng.nextU32() / 0x100000000;
  const trials = 20000;
  const ticks = Math.round(30 / E.DIALS.tickSec);
  const cases = [
    { activity: 0, expected: 1 - Math.exp(-30 / 300) },  // ~9.5%  (still)
    { activity: 1, expected: 1 - Math.exp(-30 / 30) },   // ~63.2% (cap)
  ];
  for (const { activity, expected } of cases) {
    let hit = 0;
    for (let t = 0; t < trials; t++) {
      for (let k = 0; k < ticks; k++) {
        if (E.shouldJump(activity, E.DIALS.tickSec, u01())) { hit++; break; }
      }
    }
    const share = hit / trials;
    assert.ok(Math.abs(share - expected) < 0.015,
      `activity ${activity}: got ${share.toFixed(3)}, expected ${expected.toFixed(3)}`);
  }
});

test('activity: still is 0, shaking raises it, and it never exceeds 1', () => {
  assert.equal(E.computeActivity({ speed: 'slow' }), 0);
  const shaky = E.computeActivity({ shake: 8, speed: 'normal', holdSec: 10 });
  assert.ok(shaky > E.computeActivity({ shake: 1, speed: 'normal', holdSec: 10 }));
  const extreme = E.computeActivity({
    shake: 100, tapTimesSec: [0, 0.2, 0.9, 1.0, 1.8, 2.0, 2.5], nowSec: 2.5,
    speed: 'fast', holdSec: 500,
  });
  assert.ok(extreme <= 1);
});

test('reading receipt: same inputs replay the same reading; a different ding changes it', async () => {
  const secure = new Uint8Array(32).fill(7);
  const ding = { dingAt: 1759480000000, holdMs: 21450, trace: { taps: [1200, 3400], motion: [0.4, 1.9] } };

  async function run(dingInputs) {
    const sessionSeed = await E.makeSessionSeed(secure, 'Will the shop open on time?');
    const reading = E.createReading({ spreadSize: 3, sessionRng: E.createRng(sessionSeed), reversals: true });
    reading.addJumper(9000);
    const dealSeed = await E.makeDealSeed(sessionSeed, dingInputs);
    return reading.deal(E.createRng(dealSeed)).map((p) => [p.card, p.reversed, p.source]);
  }

  const first = await run(ding);
  assert.deepEqual(await run(ding), first);
  const later = await run({ ...ding, dingAt: ding.dingAt + 1 });
  assert.equal(later[0][0], first[0][0], 'the jumper comes from the session seed, so it replays');
  assert.notDeepEqual(later.slice(1), first.slice(1), 'one millisecond later deals different cards');
});

test('a full spread accepts no more jumpers', () => {
  const reading = E.createReading({ spreadSize: 1, sessionRng: masterRng('full') });
  assert.ok(reading.addJumper(0));
  assert.ok(reading.isFull());
  assert.equal(reading.addJumper(1), null);
});

// ---- Swipe mode ------------------------------------------------------------
function line(x0, y0, x1, y1, steps = 20, ms = 300) {
  return Array.from({ length: steps + 1 }, (_, i) => ({
    x: x0 + ((x1 - x0) * i) / steps, y: y0 + ((y1 - y0) * i) / steps, t: (ms * i) / steps,
  }));
}
function circle(clockwise, turns = 1.1, r = 60, steps = 60, ms = 600) {
  return Array.from({ length: steps + 1 }, (_, i) => {
    const a = (clockwise ? 1 : -1) * 2 * Math.PI * turns * (i / steps);
    return { x: 100 + r * Math.cos(a), y: 100 + r * Math.sin(a), t: (ms * i) / steps };
  });
}

test('swipe shapes are recognized', () => {
  const k = (pts) => { const s = E.classifyStroke(pts); return `${s.kind}:${s.dir}`; };
  assert.equal(k(line(0, 0, 200, 10)), 'horizontal:right');
  assert.equal(k(line(200, 0, 0, -10)), 'horizontal:left');
  assert.equal(k(line(0, 200, 8, 0)), 'vertical:up');
  assert.equal(k(line(0, 0, -8, 200)), 'vertical:down');
  // Screen y points down, so increasing angle looks clockwise.
  assert.equal(k(circle(true)), 'circular:cw');
  assert.equal(k(circle(false)), 'circular:ccw');
  assert.equal(k(line(0, 0, 5, 3, 3, 80)), 'tap:null');
  assert.equal(E.classifyStroke([{ x: 1, y: 1, t: 0 }]).kind, 'tap');
  // Back-and-forth (left, right, left) is side-to-side, not a circle.
  const zigzag = [...line(0, 0, 150, 5), ...line(150, 5, 0, 10), ...line(0, 10, 150, 15)]
    .map((p, i) => ({ ...p, t: i * 15 }));
  assert.equal(E.classifyStroke(zigzag).kind, 'horizontal');
  // Speed is reported in px per second.
  assert.equal(E.classifyStroke(line(0, 0, 300, 0, 30, 500)).speed, 600);
});

test('swipe activity rises with speed and unevenness, stays within 0..1', () => {
  assert.equal(E.swipeActivity({}), 0);
  const slow = E.swipeActivity({ speeds: [300] });
  const fast = E.swipeActivity({ speeds: [2400] });
  assert.ok(fast > slow);
  const steady = E.swipeActivity({ speeds: [1000, 1000, 1000, 1000] });
  const uneven = E.swipeActivity({ speeds: [300, 2400, 500, 1000] });
  assert.ok(uneven > steady);
  assert.ok(E.swipeActivity({ speeds: [9e9, 1, 9e9], shake: 999 }) <= 1);
});

test('20 swipes match the 30-second rarity table', () => {
  const rng = masterRng('swipes');
  const u01 = () => rng.nextU32() / 0x100000000;
  const trials = 20000;
  for (const [activity, expected] of [[0, 1 - Math.exp(-30 / 300)], [1, 1 - Math.exp(-1)]]) {
    const p = E.swipeJumpChance(activity);
    let hit = 0;
    for (let t = 0; t < trials; t++) {
      for (let k = 0; k < 20; k++) if (u01() < p) { hit++; break; }
    }
    const share = hit / trials;
    assert.ok(Math.abs(share - expected) < 0.015,
      `activity ${activity}: got ${share.toFixed(3)}, expected ${expected.toFixed(3)}`);
  }
});

test('Celtic Cross follows the laying order: 3 below, 4 left, 5 above', () => {
  const p = SPREADS.celtic.positions;
  assert.match(p[2], /^Beneath/);
  assert.match(p[3], /^Behind/);
  assert.match(p[4], /^Crowns/);
  assert.match(p[5], /^Before/);
});
