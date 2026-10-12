# Print: MakePlayingCards files for the Aeonic tarot

`mpc-guide.html` is the research: MakePlayingCards' (MPC) tarot rules, how our scans
measure against them, the rules for our files, and how to order and sell.
`mpc_print.py` turns the 78 card faces in `cards/aeonic/` and the full-size card
back into files MPC accepts.

## Making the files

```
python3 -I print/mpc_print.py <out-dir> --fit safe     --back <full-size-back.png>
python3 -I print/mpc_print.py <out-dir> --fit original --back <full-size-back.png>
```

Requirements: Python 3 with Pillow and NumPy (`pip install pillow numpy`).

- **`<out-dir>`**: any folder **outside this repository**. The repository is public. The full-size back is © Dolores Puckett, and the print files contain it, so neither is committed.
- **`--back`**: the finished, symmetric full-size back (the one with the copyright notice at both ends). Leave it out to make the faces only.
- **`--fit safe`**: shrinks the art 5% (scale 0.950) inside a wider cream border, so the frame lines sit inside MPC's safe line. 12 of 78 cards still come within 0–5 px (under 0.5 mm) of crossing it. `--scale 0.91` puts every one inside, with a wider border.
- **`--fit original`**: keeps the 1909 proportions. On 67 cards a frame line crosses the safe line, by up to 25 px (about 2 mm), so borders may come out uneven if the cut drifts.
- **`--only 00,40,77`**: makes just those cards, for a quick look.

It takes about 3–4 minutes for the whole deck.

## What comes out

| File | What it is |
|---|---|
| `00.jpg` … `77.jpg` | the 78 faces in deck order: 897 × 1497 px, 300 dpi, JPEG quality 95 |
| `back.png` | the back: 897 × 1497 px, 300 dpi, exactly identical after a half turn (PNG keeps that exact) |
| `check-sheet.jpg` | every card with the cut line (solid) and safe line (dashed red) drawn on |

The report on screen gives, for every card:
- its size in the scan and as printed;
- how much paper was added around it;
- any non-paper pixels left in the bleed (should be 0);
- how far any frame line crosses the safe line.

It ends with how closely the back matches its half turn (should be 0). If a check fails, the program says FAILED and exits with status 1.

## What it does to each card

1. **Finds the card in the scan.** Card paper is warm cream. The scanner background is neutral white or grey, or slightly blue after recolouring. Anything not warm that touches the edge is background.
2. **Fits the card to the 825 × 1425 cut size without stretching.** The difference is made up with paper.
3. **Paints paper** into the worn round corners, the scan's edge shadow, any padding, and the 36 px bleed. The colour comes from the card's own margin, side by side, plus a fine grain.
4. **Saves the file.** The back is repaired the same way as `card-backs/web_back.py`, widened to the card shape, and then made exactly symmetric.

## Checked
- `node --test` runs the program on two cards and a stand-in back. It checks the sizes, the symmetric back and both fits.
- **Known imperfection:** a faint arc of the old worn corner shows on a few cards, for example the King of Coins' bottom-left. It sits inside the corner that MPC rounds off.
