// Intuitive Shuffle engine: no screen code, so every rule can be tested.
//
// How a reading works:
//   1. Hold starts  -> session seed = SHA-256(32 secure random bytes + question).
//                      The session seed drives which card each jumper is.
//   2. While holding -> rare jumpers fly out at random moments. Movement, taps,
//                      speed and time raise the chance; nothing guarantees one.
//                      Each jumper fills the next empty spread position.
//   3. Release (ding) -> deal seed = SHA-256(session seed + ding moment + hold time
//                      + motion/tap trace). It shuffles the remaining deck and
//                      fills any empty positions from the top.
// Every card keeps the same chance in every position: the personal inputs decide
// *which* reading you get, never the odds.
(function (root) {
  'use strict';

  // ---- Tuning dials (one place) -------------------------------------------
  const DIALS = {
    rateStillPerSec: 1 / 300, // still phone: about 1 jumper per 5 minutes
    rateCapPerSec: 1 / 30,    // very shaky / fast: about 1 per 30 seconds (cap)
    tickSec: 0.1,             // how often the jumper chance is checked
    motionFull: 12,           // shake (m/s^2) that counts as "full" motion
    tapWindowSec: 3,          // taps counted over this many recent seconds
    tapsFull: 6,              // this many recent taps counts as "full" tapping
    longWaitSec: 90,          // holding this long adds the full waiting bonus
    weights: { motion: 0.55, taps: 0.3, wait: 0.15 },
    speedBonus: { slow: 0, normal: 0.1, fast: 0.25 },
    // Swipe mode
    secondsPerSwipe: 1.5,     // one swipe counts like this much hand shuffling
    swipeMinPx: 24,           // shorter than this is a tap, not a swipe
    circleTurnDeg: 270,       // total turning that makes a swipe a circle
    swipeFastPxPerSec: 2500,  // swipe speed that counts as "full"
  };

  // ---- ChaCha20 block function (RFC 8439) ----------------------------------
  function rotl(v, c) {
    return (v << c) | (v >>> (32 - c));
  }

  function quarterRound(x, a, b, c, d) {
    x[a] = (x[a] + x[b]) | 0; x[d] = rotl(x[d] ^ x[a], 16);
    x[c] = (x[c] + x[d]) | 0; x[b] = rotl(x[b] ^ x[c], 12);
    x[a] = (x[a] + x[b]) | 0; x[d] = rotl(x[d] ^ x[a], 8);
    x[c] = (x[c] + x[d]) | 0; x[b] = rotl(x[b] ^ x[c], 7);
  }

  // key: 8 words, nonce: 3 words, counter: integer. Returns 16 output words.
  function chachaBlock(key, counter, nonce) {
    const s = new Uint32Array([
      0x61707865, 0x3320646e, 0x79622d32, 0x6b206574,
      key[0], key[1], key[2], key[3], key[4], key[5], key[6], key[7],
      counter >>> 0, nonce[0], nonce[1], nonce[2],
    ]);
    const x = new Int32Array(s);
    for (let i = 0; i < 10; i++) {
      quarterRound(x, 0, 4, 8, 12); quarterRound(x, 1, 5, 9, 13);
      quarterRound(x, 2, 6, 10, 14); quarterRound(x, 3, 7, 11, 15);
      quarterRound(x, 0, 5, 10, 15); quarterRound(x, 1, 6, 11, 12);
      quarterRound(x, 2, 7, 8, 13); quarterRound(x, 3, 4, 9, 14);
    }
    const out = new Uint32Array(16);
    for (let i = 0; i < 16; i++) out[i] = (x[i] + s[i]) >>> 0;
    return out;
  }

  function bytesToWords(bytes) {
    const words = new Uint32Array(bytes.length / 4);
    for (let i = 0; i < words.length; i++) {
      words[i] = (bytes[4 * i] | (bytes[4 * i + 1] << 8) |
        (bytes[4 * i + 2] << 16) | (bytes[4 * i + 3] << 24)) >>> 0;
    }
    return words;
  }

  // Deterministic random stream keyed by a 32-byte seed. Same seed, same stream.
  function createRng(seedBytes) {
    if (!(seedBytes instanceof Uint8Array) || seedBytes.length !== 32) {
      throw new Error('seed must be 32 bytes');
    }
    const key = bytesToWords(seedBytes);
    const nonce = new Uint32Array(3);
    let counter = 0;
    let block = null;
    let index = 16;
    return {
      nextU32() {
        if (index >= 16) {
          block = chachaBlock(key, counter++, nonce);
          index = 0;
        }
        return block[index++];
      },
    };
  }

  // Unbiased whole number from 0 to n-1 (rejection sampling: no modulo bias).
  function randomInt(rng, n) {
    const limit = Math.floor(0x100000000 / n) * n;
    let x;
    do { x = rng.nextU32(); } while (x >= limit);
    return x % n;
  }

  function randomBit(rng) {
    return (rng.nextU32() & 1) === 1;
  }

  // ---- Seeds ---------------------------------------------------------------
  function concatBytes(a, b) {
    const out = new Uint8Array(a.length + b.length);
    out.set(a, 0);
    out.set(b, a.length);
    return out;
  }

  async function sha256(bytes) {
    const subtle = root.crypto && root.crypto.subtle;
    if (!subtle) throw new Error('Secure hashing unavailable: open this page over https.');
    return new Uint8Array(await subtle.digest('SHA-256', bytes));
  }

  function utf8(value) {
    return new TextEncoder().encode(JSON.stringify(value));
  }

  function secureRandomBytes(n) {
    return root.crypto.getRandomValues(new Uint8Array(n));
  }

  function makeSessionSeed(secureBytes, question) {
    return sha256(concatBytes(secureBytes, utf8({ v: 1, question: question || '' })));
  }

  // ding: { dingAt, holdMs, trace }
  function makeDealSeed(sessionSeed, ding) {
    return sha256(concatBytes(sessionSeed, utf8({
      v: 1, dingAt: ding.dingAt, holdMs: ding.holdMs, trace: ding.trace || null,
    })));
  }

  function toHex(bytes) {
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  }

  // ---- A reading -----------------------------------------------------------
  // sessionRng picks jumpers; deal(dealRng) fills whatever is left.
  function createReading({ spreadSize, deckSize = 78, sessionRng, reversals = false }) {
    const remaining = Array.from({ length: deckSize }, (_, i) => i);
    const positions = new Array(spreadSize).fill(null);
    const jumpers = [];

    function nextEmpty() {
      return positions.indexOf(null);
    }

    return {
      positions,
      jumpers,
      remaining,
      isFull() {
        return nextEmpty() === -1;
      },
      // A jumper is a random card from those still in the deck. It fills the next
      // empty position. Face up or face down is animation only.
      addJumper(atMs) {
        const slot = nextEmpty();
        if (slot === -1) return null;
        const card = remaining.splice(randomInt(sessionRng, remaining.length), 1)[0];
        const reversed = reversals ? randomBit(sessionRng) : false;
        const landedFaceUp = randomBit(sessionRng);
        const placed = { card, reversed, position: slot, source: 'jumper', atMs, landedFaceUp };
        positions[slot] = placed;
        jumpers.push(placed);
        return placed;
      },
      // Fisher-Yates shuffle of the remaining deck, then deal empty positions from the top.
      deal(dealRng) {
        for (let i = remaining.length - 1; i > 0; i--) {
          const j = randomInt(dealRng, i + 1);
          [remaining[i], remaining[j]] = [remaining[j], remaining[i]];
        }
        positions.forEach((p, slot) => {
          if (p) return;
          const card = remaining.shift();
          const reversed = reversals ? randomBit(dealRng) : false;
          positions[slot] = { card, reversed, position: slot, source: 'dealt' };
        });
        return positions;
      },
    };
  }

  // ---- Jumper chance -------------------------------------------------------
  function clamp01(v) {
    return Math.max(0, Math.min(1, v));
  }

  // inputs: { shake (m/s^2, smoothed), tapTimesSec (recent, seconds), nowSec, speed, holdSec }
  function computeActivity({ shake = 0, tapTimesSec = [], nowSec = 0, speed = 'normal', holdSec = 0 }) {
    const motion = clamp01(shake / DIALS.motionFull);
    const recent = tapTimesSec.filter((t) => nowSec - t <= DIALS.tapWindowSec);
    let taps = clamp01(recent.length / DIALS.tapsFull);
    if (recent.length >= 3) {
      // Uneven rhythm counts more than a steady metronome.
      const gaps = recent.slice(1).map((t, i) => t - recent[i]);
      const mean = gaps.reduce((a, b) => a + b, 0) / gaps.length;
      const sd = Math.sqrt(gaps.reduce((a, g) => a + (g - mean) ** 2, 0) / gaps.length);
      taps *= 0.5 + 0.5 * clamp01(mean > 0 ? sd / mean : 0);
    }
    const wait = clamp01(holdSec / DIALS.longWaitSec);
    const w = DIALS.weights;
    return clamp01(w.motion * motion + w.taps * taps + w.wait * wait + (DIALS.speedBonus[speed] || 0));
  }

  function jumperRatePerSec(activity) {
    return DIALS.rateStillPerSec + clamp01(activity) * (DIALS.rateCapPerSec - DIALS.rateStillPerSec);
  }

  // u01: a fresh random number in [0, 1). Returns true if a card jumps this tick.
  function shouldJump(activity, dtSec, u01) {
    return u01 < 1 - Math.exp(-jumperRatePerSec(activity) * dtSec);
  }

  // ---- Swipe mode ----------------------------------------------------------
  // points: [{ x, y, t }] in screen pixels (y grows downward) and milliseconds.
  // Returns { kind: 'tap' | 'horizontal' | 'vertical' | 'circular', dir, lengthPx, durationMs, speed }.
  function classifyStroke(points) {
    const first = points[0];
    const last = points[points.length - 1];
    let length = 0, sumAbsDx = 0, sumAbsDy = 0, turn = 0, prevAngle = null;
    let lastDx = 0, lastDy = 0;
    for (let i = 1; i < points.length; i++) {
      const dx = points[i].x - points[i - 1].x;
      const dy = points[i].y - points[i - 1].y;
      const d = Math.hypot(dx, dy);
      if (d < 2) continue; // ignore jitter
      length += d; sumAbsDx += Math.abs(dx); sumAbsDy += Math.abs(dy);
      lastDx = dx; lastDy = dy;
      const angle = Math.atan2(dy, dx);
      if (prevAngle !== null) {
        let delta = angle - prevAngle;
        while (delta > Math.PI) delta -= 2 * Math.PI;
        while (delta <= -Math.PI) delta += 2 * Math.PI;
        // A sharp reversal (back-and-forth) is not part of a smooth circle.
        if (Math.abs(delta) < (150 * Math.PI) / 180) turn += delta;
      }
      prevAngle = angle;
    }
    const durationMs = Math.max(1, (last ? last.t : 0) - (first ? first.t : 0));
    const base = { lengthPx: Math.round(length), durationMs: Math.round(durationMs), speed: Math.round((length / durationMs) * 1000) };
    if (!first || length < DIALS.swipeMinPx) return { kind: 'tap', dir: null, ...base };
    const turnDeg = (turn * 180) / Math.PI;
    // Screen y grows downward, so a positive turn looks clockwise.
    if (Math.abs(turnDeg) >= DIALS.circleTurnDeg) return { kind: 'circular', dir: turnDeg > 0 ? 'cw' : 'ccw', ...base };
    const netDx = last.x - first.x;
    const netDy = last.y - first.y;
    if (sumAbsDx >= sumAbsDy) {
      const sign = Math.abs(netDx) >= DIALS.swipeMinPx / 2 ? netDx : lastDx;
      return { kind: 'horizontal', dir: sign >= 0 ? 'right' : 'left', ...base };
    }
    const sign = Math.abs(netDy) >= DIALS.swipeMinPx / 2 ? netDy : lastDy;
    return { kind: 'vertical', dir: sign >= 0 ? 'down' : 'up', ...base };
  }

  // speeds: px/s of recent swipes (newest last). shake: smoothed motion (m/s^2).
  function swipeActivity({ speeds = [], shake = 0 }) {
    const latest = speeds.length ? speeds[speeds.length - 1] : 0;
    const speed = clamp01(latest / DIALS.swipeFastPxPerSec);
    let uneven = 0;
    if (speeds.length >= 3) {
      const recent = speeds.slice(-6);
      const mean = recent.reduce((a, b) => a + b, 0) / recent.length;
      const sd = Math.sqrt(recent.reduce((a, v) => a + (v - mean) ** 2, 0) / recent.length);
      uneven = clamp01(mean > 0 ? sd / mean : 0);
    }
    const motion = clamp01(shake / DIALS.motionFull);
    return clamp01(0.6 * speed + 0.25 * uneven + 0.15 * motion);
  }

  // Chance that one swipe makes a card jump. A swipe counts as secondsPerSwipe of shuffling.
  function swipeJumpChance(activity) {
    return 1 - Math.exp(-jumperRatePerSec(activity) * DIALS.secondsPerSwipe);
  }

  function secureUnitFloat() {
    return root.crypto.getRandomValues(new Uint32Array(1))[0] / 0x100000000;
  }

  const api = {
    DIALS,
    chachaBlock,
    bytesToWords,
    createRng,
    randomInt,
    sha256,
    secureRandomBytes,
    secureUnitFloat,
    makeSessionSeed,
    makeDealSeed,
    toHex,
    createReading,
    computeActivity,
    jumperRatePerSec,
    shouldJump,
    classifyStroke,
    swipeActivity,
    swipeJumpChance,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SpiritEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
