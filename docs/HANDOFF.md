# Handoff: Intuitive Shuffle (spirit-greek)

Session: 2026-10-03 · https://claude.ai/code/session_01EZiuLfRxaFpT2ZhkYNEjy4
Session Log entry (Notion): https://app.notion.com/p/3ee4084c23c281b69b5ac0f8101e8cfc

## Where things stand

A phone-friendly 78-card tarot shuffle for aeonicarts.com is built, merged into
`main`, and published with GitHub Pages:

- Live page: https://tsgoddessfireaf-beep.github.io/spirit-greek/
- PR #1 (merged): hold and tap shuffle modes, personal seed, jumpers, receipt, fairness tests.
- PR #2 (merged): swipe mode with animations, Celtic Cross in Dolores's order,
  face-down cards that turn over on tap.
- Tests: `node --test` → 12 of 12 pass. No installs needed (Node 18+).

**Device test (Dolores, 2026-10-03, PR #3 comment):** works on her Android (Motorola)
phone and on her iPad (9:31 a.m.). She loves the shuffling animation and says it
feels intuitive. On iPad, allowing motion worked with no issues. Not yet tested on
an iPhone.

## How it works (plain English)

1. The reader types an optional question and picks a spread (1 card, 3 cards, Celtic Cross).
2. They shuffle in one of three ways (Settings → How to shuffle):
   - **Hold**: hold the deck, let go on the intuitive "ding".
   - **Tap**: tap to start, tap again on the ding.
   - **Swipe**: swipe across the deck like a hand shuffle; **double-tap** on the ding.
     Side-to-side swipes push packets across; circles swirl the deck (a wash);
     up/down swipes riffle (two halves lift and cascade).
3. **Jumpers**: now and then a card flies out of the deck and fills the next empty
   position. Rare and random. Movement, uneven taps, faster shuffling and a longer
   wait raise the chance; nothing guarantees one. In swipe mode, cards only jump
   during swipes. If jumpers fill the spread, the shuffle stops by itself.
4. On the ding, empty positions are dealt from the top of the deck.
5. All cards land **face down**. After the ding, tapping a card turns it over
   sideways (so a reversed card stays reversed). Tapping a face-up card shows a close-up.
6. A **receipt** fingerprint is shown; "Copy full receipt" copies everything needed
   to replay the exact reading.
7. Nothing leaves the phone: no server, no cookies, no tracking.

## Decisions already made (do not reopen without Dolores)

| Decision | Why |
|---|---|
| **Seed drift only, never outcome drift.** The reader's question, ding moment, hold time, motion, taps and swipes are mixed with secure randomness into the seed. They decide *which* reading, never the odds. | Keeps every card at 1-in-78 in every position. Hidden steering would be deceptive (FTC Section 5 risk) and would damage the brand. Dolores learned and approved this. |
| No use of browser analytics or cookies to tilt cards. | Same reason. A site can only read its own cookies anyway. |
| Jumpers: rare, random; each fills the next empty position; face up/down landing has no meaning. | Dolores's rule from her own practice. Proven fair by the tests. |
| Swipe mode: ding = **double tap**; jumpers **only during swipes**; one swipe counts as 1.5 s of shuffling. | Dolores's choices. 20 swipes ≈ the 30-second rarity table. |
| Celtic Cross order: 1 center · 2 across 1 · **3 below · 4 left · 5 above** · 6 right · staff 7→10 on the right, bottom to top. Each spot keeps its traditional Waite name. | Matches Dolores's photo of how she lays the cards (not Waite's printed order). |
| Cards stay face down until tapped; turn over sideways. | Dolores's request; sideways preserves reversals. |
| **Yes / No spread** (issue #6): 3 piles, each stops at an Ace or 13 cards; upright Ace = yes, reversed = no; jumpers go on top of the pile being built and count; reversals always on. Answer combines majority (direction) and number of Aces (strength); table in README. | Dolores's method and her answers ("combine one and two"). |
| Card names only. No meanings, no images, no Dusty White text. | Copyright. Meanings must come from Dolores's verified library or public-domain sources. |
| Plain HTML/JS, no framework, no build step. | Small, easy to embed in aeonicarts.com later. |

## Open items, in priority order

1. **Follow-ups from the device test.** Android and iPad passed, and she approved the
   shuffle animation and the intuitive feel. Not yet reported:
   - whether the up/down animation matches her "French shuffle" (built as a
     riffle-and-bridge).
   - an iPhone test.
   - jumper rarity (tune `DIALS` in `engine.js`: `rateStillPerSec`, `rateCapPerSec`,
     `secondsPerSwipe`).
   - tapping **card 1 in the Celtic Cross**: card 2 lies across its middle, so only
     its top/bottom ends (~30 px) are tappable. Offered fix if fiddly: tapping card 2
     turns over card 1 first, then itself.
   - position names for spots 3/4/5 (Beneath / Behind / Crowns) — her wording may differ.
2. **Repository visibility.** Dolores asked about going private. Free GitHub Pages
   needs a public repo. Options given: stay public; private + GitHub Pro; private +
   free host (Netlify / Cloudflare Pages / Vercel, recommended); fold into
   aeonicarts.com later. Not decided. Nothing was changed.
3. **Project page.** The Session Log filed this under System/Admin as
   "🆕 POSSIBLE NEW PROJECT: Intuitive Shuffle". No Projects-database page exists.
   Create one only if Dolores directs it.
4. **Later builds** (not started): card meanings from her verified library, card art
   (Rider-Waite 1910 images are public domain), integration into aeonicarts.com,
   optional reading history ("this card appeared 4 times in your last 10 readings",
   opt-in, stored on the device).
5. **Yes / No spread**: phone test pending; answer wording ("Likely yes", "Maybe no",
   "No clear answer") may need her words.
6. **Card backs** (`card-backs/`, skill `.claude/skills/ambigram/`): card #3 made
   exactly symmetric; skull options A (smoothed) and B (flowing lines) via
   `card-backs/skull.py`; ambigram draft v1 (a↔s and e↔t weak). Her choices pending.

## How Dolores works (read before starting)

- Explain in plain English first, then developer detail. Define terms. Lead with the conclusion.
- **No skills and no helper agents/subagents** — she said they eat her usage.
- For builds: **plan mode first, with a self-evaluation table (pros, cons, reason) for every step**.
  Wait for her approval.
- Branch from `main` (branch name `claude/randomizer-card-scripts-s7zjs0`), push,
  open a **draft** PR. **Dolores merges.** Never push to `main`.
- Evidence rule: any claim of writing/creating in Notion or elsewhere must include
  the returned URL or ID, or say "NOT WRITTEN — reason".
- Session close trigger ("QED", "wrap up"): run the APEX Log Protocol v2.0 pinned on
  the 📓 AEONIC APEX LOG Notion page, show the entry, wait for her OK, then write.

## Developer detail

| File | Job |
|---|---|
| `index.html` | The page: UI, hold/tap/swipe input, swipe animations, Celtic Cross grid, face-down cards, close-up, receipt |
| `engine.js` | `DIALS` (all tuning), ChaCha20 (RFC 8439), seeds (SHA-256), `createReading` (jumpers + Fisher–Yates deal), activity/jumper chance, `classifyStroke`, `swipeActivity`, `swipeJumpChance` |
| `deck.js` | 78 card names (Waite 1910), spread positions (Celtic Cross in Dolores's order) |
| `test/engine.test.js` | 12 tests: RFC vector, 200,000-reading chi-square fairness per position, no repeats, rarity tables, receipt replay, stroke recognition, Celtic order |
| `README.md` | User-facing description, phone setup, tuning table |

Seeds: session seed = SHA-256(32 secure bytes ‖ question) drives jumper picks;
deal seed = SHA-256(session seed ‖ ding time ‖ hold ms ‖ trace) drives the deal.
`addJumper` still draws a `landedFaceUp` bit that the page no longer uses. Keep it:
removing it changes the random stream, so receipts saved before the change would
no longer replay.

Testing tips:
- Browser checks: serve with `python3 -m http.server`, drive with Playwright
  (installed globally; `NODE_PATH=$(npm root -g)`). Chromium is at `/opt/pw-browsers`.
- To force jumpers in a browser test: `SpiritEngine.DIALS.rateStillPerSec = 8`.
- Don't stop the test server with `pkill -f "http.server …"` inside a longer
  command line: the pattern matches the shell itself and kills it.
- GitHub deletes the branch automatically after each merge. Reset the branch to
  `origin/main` and push fresh; `--force-with-lease` fails with "stale info" on a
  deleted remote branch (run `git fetch --prune` first).
- This environment cannot open `*.github.io` (proxy). Check Pages deploys through
  the GitHub Actions run list ("pages build and deployment").

Sources consulted: Dusty White, *The Easiest Way to Learn the Tarot—EVER!!* and
*Advanced Tarot Secrets* (Dolores's Google Drive). The "ding" comes from *Advanced
Tarot Secrets* ("Call Your Card"; reading process step 2). Ideas only, no text used.
