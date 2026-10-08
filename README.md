# Intuitive Shuffle

A 78-card tarot shuffle for Aeonic Arts (aeonicarts.com). You hold the deck while
you hold your question, and you let go when you feel the "ding" (Dusty White,
*Advanced Tarot Secrets*).

## How it works

- **Three ways to shuffle** (Settings → How to shuffle):
  - **Hold**: hold the deck, let go on the ding.
  - **Tap**: tap to start, tap again on the ding.
  - **Swipe**: swipe across the deck like a hand shuffle, **double-tap** on the ding.
    Each swipe plays an animation that matches its shape:
    - side-to-side: packets pushed across left→right or right→left and stuffed back
    - circle: the deck swirls around (a wash), clockwise or counter-clockwise
    - up or down: a riffle, two halves lift and cascade back together

    Arrow keys also swipe, and Enter deals.
- **Personal seed.** Your question, the ding moment, how long you held, and your
  hand's movement and taps are blended with real randomness into a seed (a starting
  number). The seed decides *which* reading you get. It never changes the odds, so
  every card keeps the same 1-in-78 chance in every position.
- **Jumpers.** Now and then a card jumps out mid-shuffle. In swipe mode a card can
  only jump during a swipe; faster or more uneven swipes raise the chance. Jumpers are rare and
  random. Movement, uneven taps on the table, a faster shuffle and a longer wait make
  one more likely, but never certain. Each jumper fills the next empty position. If
  jumpers fill the whole spread, the shuffle stops by itself.
- **Receipt.** Each reading shows a short fingerprint. "Copy full receipt" copies
  everything needed to replay the exact same reading.
- **Private.** Nothing is stored or sent anywhere: no server, no cookies, no tracking.

Spreads: one card, three cards (Past / Present / Future), and the Celtic Cross,
laid out like the table: 1 center, 2 across 1, 3 below, 4 left, 5 above, 6 right,
then the staff 7–10 on the right from bottom to top. Each position keeps its
traditional name.

Cards stay **face down** for the reading. After the ding, tap a card to turn it
over. It flips sideways, the way you'd turn a card on the table, so a reversed card
stays reversed. Tap a face-up card to see it large with its position. In the Celtic
Cross, card 1 is turned by tapping its top or bottom end, since card 2 lies across it.
Reversed cards are optional (Settings).

### Yes / No

Three piles. Cards go onto pile 1 until an **Ace** lands or the pile holds **13
cards**, then onto pile 2, then pile 3 (at most 39 cards). A jumper goes right on
top of the pile being built and counts like any card. Reversed cards are always on
for this spread. Tap a pile to turn its cards over one by one; "Turn all piles"
turns the rest. Each pile votes: an upright Ace = yes, a reversed Ace = no, no Ace =
blank.

| Upright Aces | Reversed Aces | Answer |
|---|---|---|
| 3 | 0 | Yes |
| 2 | 0 or 1 | Likely yes |
| 1 | 0 | Maybe yes |
| 1 | 1, or 0 / 0 | No clear answer: read the other cards as a story |
| 0 | 1 | Maybe no |
| 0 or 1 | 2 | Likely no |
| 0 | 3 | No |

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

In swipe mode each swipe counts as `secondsPerSwipe` (1.5 s) of shuffling, so
**20 swipes ≈ the 30-second column** above.

## Files

| File | Job |
|---|---|
| `index.html` | The page: question, spread, deck, settings |
| `engine.js` | Seed blending, ChaCha20 generator, fair dealing, jumper chance, swipe recognition |
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
receipt replays the same reading. For Yes / No it checks that piles stop at an Ace
or after 13 cards, that jumpers land on top of the pile being built, every answer in
the table, and 200,000 readings against the exact odds (no Ace in a 13-card pile:
C(74,13) / C(78,13) ≈ 47.5 %). The tests use fixed seeds, so results are the
same on every run.
