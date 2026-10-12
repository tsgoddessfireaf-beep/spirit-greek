# Print: MakePlayingCards files for the Aeonic tarot

`mpc-guide.html` is the research: MakePlayingCards' (MPC) tarot rules, how our scans
measure against them, and how to order and sell. `mpc_print.py` turns the 78 card faces
in `cards/aeonic/` and the full-size card back into files MPC accepts.

## Making the files

```
python3 -I print/mpc_print.py <out-dir> --back <full-size-back.png>
```

Requirements: Python 3 with Pillow and NumPy (`pip install pillow numpy`).

- **`<out-dir>`**: any folder **outside this repository**. The repository is public. The full-size back is © Dolores Puckett, and the print files contain it, so neither is committed.
- **`--back`**: the finished, symmetric full-size back (the one with the copyright notice at both ends). Leave it out to make the faces only.
- **`--only 00,40,77`**: makes just those cards, for a quick look.

The whole deck takes under a minute.

## What each card looks like

- **Smith's picture fills the card,** cut exactly at the outer edge of its frame. The worn 1909 paper around it is gone.
- **Every card has the same clean cream border** after cutting: 40 px (3.4 mm) at the sides and 61 px (5.2 mm) at the top and bottom. The frame sits inside MPC's safe area.
- **A crisp teal edge** is drawn on Smith's frame line.
- **Crooked scans are straightened first** (up to about 1 degree).
- **One shared box:** Smith's frames differ in shape by a few per cent, and each picture is fitted to the same box. The widest change in the deck is 3.6%, which can't be seen.

## What comes out

| File | What it is |
|---|---|
| `00.jpg` … `77.jpg` | the 78 faces in deck order: 897 × 1497 px, 300 dpi, JPEG quality 95 |
| `back.png` | the back: 897 × 1497 px, 300 dpi, exactly identical after a half turn (PNG keeps that exact) |
| `check-sheet.jpg` | every card with the cut line (solid) and safe line (dashed red) drawn on |

The report on screen gives each card's straightening, its change in width, and how clearly its frame was found.
- **`CHECK`:** marks a card to look at by eye (frame edge unclear, or shape changed more than 5%). The current deck has none.
- **`FAILED`:** a size or symmetry check failed. The program says so and exits with status 1.

## Checked
- `node --test` runs the program on three cards and a stand-in back, and checks the sizes, the symmetric back and that no card needs checking.
