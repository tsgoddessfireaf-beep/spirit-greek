# Intuitive Shuffle

A 78-card tarot shuffle for Aeonic Arts (aeonicarts.com). You hold the deck while
you hold your question, and you let go when you feel the "ding" (Dusty White,
*Advanced Tarot Secrets*).

## How it works

- **Hold to shuffle, let go on the ding.** The moment you let go becomes part of
  the reading. There is also a tap mode: tap to start, tap again on the ding.
- **Personal seed.** Your question, the ding moment, how long you held, and your
  hand's movement and taps are blended with real randomness into a seed (a starting
  number). The seed decides *which* reading you get. It never changes the odds, so
  every card keeps the same 1-in-78 chance in every position.
- **Jumpers.** Now and then a card jumps out mid-shuffle. Jumpers are rare and
  random. Movement, uneven taps on the table, a faster shuffle and a longer wait make
  one more likely, but never certain. Each jumper fills the next empty position. If
  jumpers fill the whole spread, the shuffle stops by itself.
- **Receipt.** Each reading shows a short fingerprint. "Copy full receipt" copies
  everything needed to replay the exact same reading.
- **Private.** Nothing is stored or sent anywhere: no server, no cookies, no tracking.

Spreads: one card, three cards (Past / Present / Future), Celtic Cross (Waite 1910
positions). Reversed cards are optional (Settings).

## Try it on your phone

The page must be opened over **https** (secure hashing and the motion sensor
require it). The free way: GitHub Pages.

1. On GitHub: **Settings → Pages**.
2. Under "Branch", choose **main** and **/ (root)**, then **Save**.
3. After a minute, open `https://tsgoddessfireaf-beep.github.io/spirit-greek/`.

On iPhone, open **Settings** on the page and tap **Allow** so the deck can feel
your hand's movement.

Free GitHub Pages needs the repository to be public.

## Tuning jumper rarity

All dials are in one place: `DIALS` at the top of `engine.js`.

| Phone during shuffling | Average | Chance of a jumper in a 30-second shuffle |
|---|---|---|
| Still, speed "Slow" | about 1 per 5 minutes | about 10% |
| Still, speed "Normal" (default) | about 1 per 2.6 minutes | about 17% |
| Very shaky / fast (cap) | about 1 per 30 seconds | about 63% |

Holding longer slowly raises the chance a little more (the "waiting" bonus).

## Files

| File | Job |
|---|---|
| `index.html` | The page: question, spread, deck, settings |
| `engine.js` | Seed blending, ChaCha20 generator, fair dealing, jumper chance |
| `deck.js` | The 78 card names and the spread positions |
| `test/engine.test.js` | Fairness proof |

## Fairness test

Requires Node.js 18 or newer. No installs.

```
node --test
```

It checks the generator against the official RFC 8439 test vector, and runs
200,000 simulated Celtic Cross readings to confirm every card is equally likely in
every position, both for jumpers and for dealt cards. It also checks that no card
repeats within a spread, that jumper rarity matches the table above, and that a
receipt replays the same reading. The tests use fixed seeds, so results are the
same on every run.
