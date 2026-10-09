# Card backs (Aeonic Arts tattoo tarot)

Scripts that build the deck's card backs. A card back must look the same after a half
turn, so nobody can spot a reversed card from its back. The artwork itself is **not**
in this repository (it is public); pass your image file to each script.

The card-back art is © 2026 Dolores Puckett, Aeonic Arts, all rights reserved
(see `COPYRIGHT.md`). Every finished back carries the notice
"© 2026 DOLORES PUCKETT · AEONIC ARTS" in the top frame and, turned upside down,
in the bottom frame: `notice.py` adds it and keeps the back exactly symmetric.

Requirements: Python 3 with Pillow, NumPy and SciPy (`pip install pillow numpy scipy`).

| Script | What it does |
|---|---|
| `notice.py` | Writes the copyright notice in the top frame and an upside-down copy in the bottom frame; the back stays exactly symmetric. `--band`, `--color` and `--size` place it on other designs. |
| `symmetrize.py` | Makes a finished card back exactly symmetric: keeps one half, turns a copy over for the other half, joins them along a hidden seam. |
| `skull.py` | Softer skulls for card #3: A smoothed (thorns removed, outline rounded), B flowing (A plus ribbon-style strokes), C logo (redrawn smooth like the Aeonic Arts logo skull, with its third eye). |
| `ambigram.py` | Ambigram workbench: letter-pair sheet, pen-stroke drawing, word sheet, card mock-ups. |
| `glyphs_aeonicarts.py` | The designed left half of the "aeonicarts" ambigram. |
| `build2.py` | Round 1–3 builds for design 1 (Vesica Piscis, rose, mirrored name). |
| `sheet3.py`, `sym.py` | Comparison sheets and symmetry scores for those builds. |

## Card #3 (cream, teal, gold)

```
python3 -I symmetrize.py card3.png out --dx 0
```
Writes `card3_symmetric-from-top.png` and `card3_symmetric-from-bottom.png`.
Each prints its largest difference from its upside-down copy (0 = exact).

```
python3 -I skull.py skulls out/card3_symmetric-from-top.png out
```
Writes `card3_skull-A-smoothed.png`, `card3_skull-B-flowing.png` and `card3_skull-C-logo.png`.

## "Aeonic Arts" ambigram

```
python3 -I ambigram.py pairs out "aeonic arts"
python3 -I ambigram.py word  out v1
python3 -I ambigram.py card  out v1 out/card3_symmetric-from-top.png
```

The method is written up in `.claude/skills/ambigram/SKILL.md`.
