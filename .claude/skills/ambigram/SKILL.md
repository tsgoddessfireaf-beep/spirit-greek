---
name: ambigram
description: Design a rotational ambigram (a word that reads the same turned upside down) or make card-back art exactly symmetric under a half turn, for the Aeonic Arts tattoo tarot deck. Use when Dolores asks for an ambigram, an upside-down-readable word, or a card back that must not reveal reversed cards.
---

# Ambigrams and half-turn symmetry (Aeonic Arts)

Card backs must look the same after a half turn (180°), so nobody can tell a reversed
card from its back. This skill covers two jobs:

1. **Fix a card back** so it is exactly symmetric: `card-backs/symmetrize.py`.
2. **Design a rotational ambigram**: `card-backs/ambigram.py` plus a glyph file such
   as `card-backs/glyphs_aeonicarts.py`.

Explain to Dolores in plain English first, then technical detail. Never claim a design
"reads" both ways without showing her the turned-over image; legibility is her call.

## Job 1: make a card back exactly symmetric

```
python3 -I card-backs/symmetrize.py <card.png> <outdir> [--keep top|bottom|both] [--dx 0]
```

- It finds how far the art sits off-centre in the strip where the halves will join,
  shifts it, keeps one half, turns a copy over for the other half, and joins them
  along a seam routed through places where both halves already agree.
- It prints the largest difference from the upside-down copy. **0 means exact.**
- Always zoom on the join (the middle strip) at 2x before showing Dolores. Look for
  steps in straight edges and notches where lines cross the join.
- Use `--dx 0` when the outer frame is already centred side to side (measure the
  frame edges first): a straight frame shows a step more than curved art does.
- Make both versions (`--keep both`) and let her choose the better-drawn half.

### Softening the skull on card #3
`python3 -I card-backs/skull.py skulls <symmetric-card.png> <outdir>` makes two options:
**A** redraws the outline along a smoothed copy of the skull's shape and keeps only the
central features (eyes, nose, small diamond, teeth); **B** adds tapered ribbon-style
strokes (`FLOW` list, drawn on the left and mirrored); **C** redraws the skull smooth
like Dolores's logo skull (one outline, outlined eyes and nose, two tooth rows, third
eye; shapes in the `LOGO` dict, drawn upright on the bottom skull). C clears the old
knobbly cheeks and `extend_lines()` pushes the background lines that ran behind them
straight on to the new outline. Each option edits one skull and rebuilds the other
half as its turned copy, so the result stays exact. Dolores's note: the AI-made card
art gave the skull knobbly sides to fit the busy pattern; she wants it smooth like her logo.

## Job 2: design a rotational ambigram

### Method
1. **Pair the letters**: `python3 -I card-backs/ambigram.py pairs <outdir> "<word>"`.
   Letter *i* must turn into letter *n−1−i*. A middle letter must turn into itself.
   A space only works if it falls at the centre (e.g. "aeonic arts" has to be drawn
   as one word, "aeonicarts").
2. The pair sheet shows each left letter beside its partner turned over, in the fonts
   installed here. That shows which pairs are close already and which need invention.
3. **Design only the left half.** Each slot is a list of pen strokes in local units
   (x about the slot centre, baseline y = 0, x-height y = 100). Turned over, a local
   point (x, y) becomes (−x, 100 − y), so plan every stroke for both readings.
4. The program draws the right half by turning the left half over. **Symmetry is
   automatic; readability is the work.** Render, look at both orientations, adjust.
5. The pen is a broad nib at 35°. A half turn leaves the nib angle unchanged, so thick
   and thin strokes stay consistent in both readings. Use hairlines (`'nib': 4–7`)
   for strokes that one reading needs and the other should ignore.

### Tricks that worked for "aeonicarts"
| Pair | Trick |
|---|---|
| i ↔ c | Straight stem with a lead-in flick and a ball foot becomes a narrow c. The dot becomes a star, which also appears under the c. |
| n ↔ a | An n with a hairline under its foot becomes a one-storey a. |
| o ↔ r | The o's right side is the r's stem; the o's bottom becomes the r's shoulder (end it with a small ball); the o's top must be a short hairline or the r turns into a c. |
| e ↔ t | The e's bar runs out to the left and the e's back runs down into a tail: turned over, the tail is the t's ascender and the bar crosses it. Weak: the t's foot curls left. |
| a ↔ s | Hardest. A one-storey a with a hairline slanted stem becomes a cursive s's up-stroke plus belly. Still reads partly as "ɒ". |

### Commands
```
python3 -I card-backs/ambigram.py word <outdir> v1          # sheet: as drawn + turned over, plus logo PNG
python3 -I card-backs/ambigram.py card <outdir> v1 <card>   # two mock-ups on a symmetric card
```
Each command prints `exact symmetry: True` or the largest pixel difference (0 = exact).

### Placements on a card
- **Middle banner**: ribbon with notched ends, centred on the card.
- **Top and bottom**: the word in the top band and its turned copy in the bottom
  band. Because the word is an ambigram, both read correctly from either end.

## Rules
- Do not commit Dolores's card artwork (the repository is public). Scripts only.
- Use the card's own colours (`card_colours()` samples cream, teal, gold).
- Report honestly which letters read weakly. Offer: another round with her
  feedback, or a lettering artist using the draft as a sketch.
- Requirements: Python 3 with Pillow, NumPy and SciPy.
