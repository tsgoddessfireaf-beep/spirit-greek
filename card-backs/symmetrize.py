"""Make a card back read exactly the same upside down.

Keeps one half of the card, turns a copy of it over to become the other half, and
joins the two along a seam that is itself symmetric, routed through the places
where both halves already agree. The art is first re-centred, so the join lines up.

    python3 -I symmetrize.py <card.png> <outdir> [--keep top|bottom|both] [--dx N]

--dx forces the sideways shift (in px). Use --dx 0 when the outer frame is already
centred side to side: a straight frame edge shows a step at the join more than art does.
"""
import sys, os
import numpy as np
from PIL import Image

def rot(x): return x[::-1, ::-1]

def best_shift(g, search=16, band=60):
    """Pixel shift (dy, dx) that best lines the art up with its own half-turned copy,
    measured in the strip around the middle row, where the two halves will be joined.
    Moving the image by half of it centres the art on the join."""
    r = rot(g)
    mid = g.shape[0] // 2
    best = None
    for dy in range(-2 * search, 2 * search + 1):
        for dx in range(-search // 2, search // 2 + 1):
            b = np.roll(np.roll(r, dy, 0), dx, 1)
            e = np.abs(g[mid - band:mid + band, 40:-40] - b[mid - band:mid + band, 40:-40]).mean()
            if best is None or e < best[0]:
                best = (e, dy, dx)
    return best[1], best[2]

def recentre(a, dy, dx):
    """Shift the image by (dy, dx) pixels, filling the uncovered edge with edge colour."""
    h, w = a.shape[:2]
    pad = np.pad(a, ((abs(dy), abs(dy)), (abs(dx), abs(dx)), (0, 0)), mode='edge')
    y0, x0 = abs(dy) - dy, abs(dx) - dx
    return pad[y0:y0 + h, x0:x0 + w]

def seam(a, band=40, stay=2.0):
    """Row of the join for every column. The seam is a path through the band around the
    middle, where the card and its half-turned copy differ least. The right half of the
    path is the left half turned over, so the finished card stays exactly symmetric."""
    h, w = a.shape[:2]
    cost = np.abs(a.astype(np.float32) - rot(a).astype(np.float32)).max(axis=2)
    mid = (h - 1) / 2
    lo, hi = int(mid - band), int(mid + band) + 1
    c = cost[lo:hi, :(w + 1) // 2]                       # left half only
    # prefer the middle row: lines that cross the middle (cusps, side bars) join cleanly there
    c = c + stay * np.abs(np.arange(lo, hi) - mid)[:, None]
    rows = c.shape[0]
    acc = c.copy(); back = np.zeros_like(c, dtype=np.int64)
    for x in range(1, c.shape[1]):
        prev = acc[:, x - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = cand.argmin(axis=0)
        acc[:, x] += cand[k, np.arange(rows)]
        back[:, x] = np.arange(rows) + k - 1
    # the path must meet its own turned copy at the centre column
    end = int(np.argmin(acc[:, -1] + np.abs(np.arange(rows) + lo - mid) * 1e-3))
    path = np.empty(c.shape[1], dtype=np.float64)
    y = end
    for x in range(c.shape[1] - 1, -1, -1):
        path[x] = y + lo
        y = back[y, x]
    full = np.empty(w)
    full[:len(path)] = path
    full[w - 1 - np.arange(len(path))] = (h - 1) - path   # turned copy for the right half
    return full

def join(a, keep='top', soft=3.0):
    """Top part from `a` (or from its turned copy for keep='bottom'), bottom part turned."""
    h, w = a.shape[:2]
    src = a if keep == 'top' else rot(a)
    s = seam(src)
    yy = np.arange(h)[:, None]
    t = np.clip((yy - s[None, :]) / soft + 0.5, 0, 1)     # 0 above the seam, 1 below
    # symmetric ramp: t at (y, x) and 1 - t at the turned position
    t = (t + 1 - rot(t)) / 2
    out = src.astype(np.float32) * (1 - t[..., None]) + rot(src).astype(np.float32) * t[..., None]
    return np.clip(np.rint(out), 0, 255).astype(np.uint8), s

def check(a):
    d = np.abs(a.astype(np.int16) - rot(a).astype(np.int16)).max()
    return int(d)

if __name__ == '__main__':
    src, outdir = sys.argv[1], sys.argv[2]
    keep = sys.argv[sys.argv.index('--keep') + 1] if '--keep' in sys.argv else 'both'
    os.makedirs(outdir, exist_ok=True)
    a = np.asarray(Image.open(src).convert('RGB'))
    g = a.mean(axis=2)
    dy, dx = best_shift(g)
    sy, sx = -int(round(dy / 2)), -int(round(dx / 2))
    if '--dx' in sys.argv:
        sx = int(sys.argv[sys.argv.index('--dx') + 1])
    print(f'art is off-centre by about ({-dy / 2:+.1f}, {-dx / 2:+.1f}) px; shifting by ({sy:+d}, {sx:+d})')
    a = recentre(a, sy, sx)
    base = os.path.splitext(os.path.basename(src))[0]
    for k in (['top', 'bottom'] if keep == 'both' else [keep]):
        out, s = join(a, k)
        Image.fromarray(out).save(f'{outdir}/{base}_symmetric-from-{k}.png')
        print(f'{k}: seam rows {s.min():.0f}-{s.max():.0f}; largest difference from its '
              f'upside-down copy: {check(out)} (0 = exact)')
