"""Print-ready MakePlayingCards (MPC) files for the Aeonic Arts tarot.

    python3 -I print/mpc_print.py <out-dir> --fit safe|original [--back <full-size-back.png>]
                                  [--scale 0.91] [--faces cards/aeonic] [--only 00,40,77]

MPC's tarot rules (print/mpc-guide.html): every card is a 897 x 1497 pixel image at
300 dpi; 36 px of bleed is cut away on each side; a further 36 px inside the cut is
the safe area. For each of the 78 faces this program:

  1. finds the card in the 1909 scan (drops the scanner background and the worn edge),
  2. fits it to the 825 x 1425 cut size without stretching it,
       --fit original  keeps the 1909 proportions,
       --fit safe      shrinks the art (one factor for the whole deck) so the frame lines
                       sit inside the safe line,
  3. fills paper, coloured from the card's own margin, into the worn corners, any
     padding and the bleed, so a drifting blade never shows white,
  4. saves NN.jpg (quality 95, full colour detail, 300 dpi).

With --back it also makes back.png from the full-size card back (kept out of this
public repository): corners filled, widened to the card shape, bleed added, and made
exactly identical after a half turn, so it never reveals a reversed card. PNG keeps that
exact; JPEG would not.

check-sheet.jpg shows every card with its cut line (solid) and safe line (dashed).
The report lists the scale, padding and any frame line still outside the safe line.
Exit status is 1 if a self-check fails.
"""
import sys, os, argparse, importlib.util
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('aeonic', os.path.join(HERE, '..', 'cards', 'aeonic-tools', 'aeonic.py'))
aeonic = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(aeonic)
lum, flood, frame_lines = aeonic.lum, aeonic.flood, aeonic.frame_lines

W, H = 897, 1497                       # MPC tarot file, bleed included
BLEED = 36                             # cut away on each side
TW, TH = W - 2 * BLEED, H - 2 * BLEED  # 825 x 1425: the finished card
SAFE = 2 * BLEED                       # safe line, from the file edge
SPARE = 4                              # --fit safe keeps frame lines this far inside the safe line
K_FLOOR = 0.95                         # --fit safe never shrinks the art more than this
INSET = 3                              # px trimmed off the scan's worn card edge
WARM, INK = 12, 150                    # paper is warm (red minus blue > WARM); the scanner background is
                                       # neutral white or grey, or bluish after recolouring; ink is darker than INK

def warmth(a): return a[..., 0] - a[..., 2]


def card_box(a):
    """The card inside a scan: (x0, y0, x1, y1), exclusive ends, and the background mask."""
    L = lum(a); h, w = L.shape
    seeds = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
    bg = flood((warmth(a) < WARM) & (L > 120), seeds)
    card = ~bg
    cols = np.nonzero(card[int(h * .3):int(h * .7)].mean(0) > .5)[0]
    rows = np.nonzero(card[:, int(w * .3):int(w * .7)].mean(1) > .5)[0]
    return (cols[0] + INSET, rows[0] + INSET, cols[-1] + 1 - INSET, rows[-1] + 1 - INSET), bg


def corner_fill(crop, bg):
    """Pixels to replace with paper in a cropped card: scanner background (the worn corners)
    and anything else that is not paper touching a corner (dark specks, edge shadow), plus a 3 px fringe."""
    L = lum(crop); h, w = L.shape; warm = warmth(crop)
    # The repair zone: a strip EDGE px wide along each side, and the area a rounded corner of
    # radius R could cover. Its deepest point is R(1 - 1/sqrt 2) = 15 px in, short of every frame line.
    EDGE, R = 8, 50
    yy, xx = np.mgrid[0:h, 0:w]
    dx = np.minimum(xx, w - 1 - xx); dy = np.minimum(yy, h - 1 - yy)
    corner = (dx < R) & (dy < R) & ((R - dx) ** 2 + (R - dy) ** 2 > R ** 2)
    edge = np.minimum(dx, dy) < EDGE
    odd = (edge & (warm < WARM) & (L > INK)) | (corner & ((warm < WARM) | (L < INK)))
    seeds = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
    fill = bg | flood(odd, seeds) | corner | (np.minimum(dx, dy) < 4)   # the worn outline itself goes too
    grown = fill.copy()
    for dy in range(-3, 4):
        for dx in range(-3, 4): grown |= np.roll(np.roll(fill, dy, 0), dx, 1)
    return grown


def side_colours(img, known, rect):
    """Paper colour along each side of rect, sampled 6-20 px inside it, past the darkened
    worn edge. Only paper counts: light, cream (not yellow sky, not ink, not scanner grey)."""
    x0, y0, x1, y1 = rect; L = lum(img); warm = warmth(img)
    ok = known & (L > 190) & (warm > WARM) & (warm < 60)
    vals = np.where(ok[..., None], img, np.nan)
    def run(band, axis, n):
        with np.errstate(all='ignore'):
            import warnings; warnings.simplefilter('ignore')
            col = np.nanmedian(band, axis=axis)
        idx = np.arange(n)
        for ch in range(3):                            # fill gaps, then smooth along the side
            v = col[:, ch]; good = ~np.isnan(v)
            v = np.interp(idx, idx[good], v[good]) if good.any() else np.full(n, 225.)
            k = 61; pad = np.pad(v, k // 2, mode='edge')
            col[:, ch] = np.convolve(pad, np.ones(k) / k, mode='valid')
        return col
    a, b = 6, 21
    left = run(vals[y0:y1, x0 + a:x0 + b], 1, y1 - y0)
    right = run(vals[y0:y1, x1 - b:x1 - a], 1, y1 - y0)
    top = run(vals[y0 + a:y0 + b, x0:x1], 0, x1 - x0)
    bot = run(vals[y1 - b:y1 - a, x0:x1], 0, x1 - x0)
    band = ok.copy(); band[y0 + b:y1 - b, x0 + b:x1 - b] = False
    band[:y0] = band[y1:] = False; band[:, :x0] = band[:, x1:] = False
    grain = float(np.clip(np.std(L[band] - np.median(L[band])) if band.any() else 4., 2, 8))
    return left, right, top, bot, grain


def fill_paper(img, known, rect, seed):
    """Paint paper into every pixel that is not known: blend of the nearest sides' colours
    plus a fine grain, feathered a few px into the known edge."""
    x0, y0, x1, y1 = rect
    left, right, top, bot, grain = side_colours(img, known, rect)
    yy, xx = np.mgrid[0:H, 0:W]
    py = np.clip(yy, y0, y1 - 1) - y0; px = np.clip(xx, x0, x1 - 1) - x0
    cols = [left[py], right[py], top[px], bot[px]]
    dist = [np.abs(xx - x0), np.abs(xx - (x1 - 1)), np.abs(yy - y0), np.abs(yy - (y1 - 1))]
    wts = [1. / (d + 1.) ** 2 for d in dist]
    paper = sum(c * w[..., None] for c, w in zip(cols, wts)) / sum(wts)[..., None]
    rng = np.random.default_rng(seed)
    noise = Image.fromarray(np.clip(rng.normal(128, grain * 1.6, (H, W)), 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    paper += (np.asarray(noise).astype(float) - 128)[..., None]
    unknown = Image.fromarray((~known * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))
    alpha = np.clip(1 - np.asarray(unknown) / 255. * 1.3, 0, 1) * known
    return img * alpha[..., None] + paper * (1 - alpha[..., None])


def place(crop, holes, k):
    """Scale a cropped card to fit the cut size (times k), centre it, return canvas and masks."""
    h, w = crop.shape[:2]; s = min(TW / w, TH / h) * k
    nw, nh = round(w * s), round(h * s)
    art = np.asarray(Image.fromarray(crop.astype(np.uint8)).resize((nw, nh), Image.LANCZOS)).astype(float)
    hole = np.asarray(Image.fromarray((holes * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)) > 25
    ox, oy = (W - nw) // 2, (H - nh) // 2
    img = np.zeros((H, W, 3)); known = np.zeros((H, W), bool)
    img[oy:oy + nh, ox:ox + nw] = art; known[oy:oy + nh, ox:ox + nw] = ~hole
    return img, known, (ox, oy, ox + nw, oy + nh), s


def frame_k(geom):
    """Largest k (art scale) that keeps this card's detected frame lines SPARE px inside the safe line."""
    (x0, y0, x1, y1), (top, bot, lef, rig) = geom
    w, h = x1 - x0, y1 - y0; s = min(TW / w, TH / h); ks = [1.]
    lim_x, lim_y = W / 2 - SAFE - SPARE, H / 2 - SAFE - SPARE
    if lef: ks.append(lim_x / max(1e-6, (w / 2 - (lef[0] - x0)) * s))
    if rig: ks.append(lim_x / max(1e-6, ((rig[1] - x0) - w / 2) * s))
    if top: ks.append(lim_y / max(1e-6, (h / 2 - (top[0] - y0)) * s))
    if bot: ks.append(lim_y / max(1e-6, ((bot[1] - y0) - h / 2) * s))
    return min(ks)


def frame_gap(geom, k):
    """How far (px) the nearest detected frame line sits inside the safe line at art scale k;
    negative means it crosses the safe line into the zone the cut may reach."""
    (x0, y0, x1, y1), (top, bot, lef, rig) = geom
    w, h = x1 - x0, y1 - y0; s = min(TW / w, TH / h) * k; gaps = []
    if lef: gaps.append(W / 2 - (w / 2 - (lef[0] - x0)) * s - SAFE)
    if rig: gaps.append(W / 2 - ((rig[1] - x0) - w / 2) * s - SAFE)
    if top: gaps.append(H / 2 - (h / 2 - (top[0] - y0)) * s - SAFE)
    if bot: gaps.append(H / 2 - ((bot[1] - y0) - h / 2) * s - SAFE)
    return min(gaps) if gaps else float('inf')


def half_turn(b):
    """Make an image exactly identical to itself turned upside down (odd sizes allowed)."""
    b = b.copy(); h, w = b.shape[:2]; m = h // 2
    b[h - m:] = b[:m][::-1, ::-1]
    if h % 2: b[m, w - w // 2:] = b[m, :w // 2][::-1]
    return b


def make_back(path, k):
    """Full-size card back -> 897 x 1497, bleed added, exactly symmetric under a half turn."""
    a = np.asarray(Image.open(path).convert('RGB'))
    trim = 10
    a = a[:, trim:a.shape[1] - trim].copy(); h, w = a.shape[:2]
    # Same corner repair as card-backs/web_back.py: cover each rounded corner with plain paper.
    t, side, reach = 50, 48, 130
    top_strip = a[:t, w // 3:w // 3 + reach]; left_strip = a[h // 3:h // 3 + reach, :side]
    for flip in (lambda x: x, lambda x: x[::-1, ::-1]):
        b = flip(a)
        b[:t, :reach] = top_strip; b[:reach, :side] = left_strip
        b[:t, w - reach:] = top_strip[:, ::-1]; b[:reach, w - side:] = left_strip[:, ::-1]
    pad = (round(h * TW / TH) - w) // 2
    if pad > 0: a = np.pad(a, ((0, 0), (pad, pad), (0, 0)), mode='reflect')
    img, known, rect, _ = place(a.astype(float), np.zeros(a.shape[:2], bool), k)
    out = half_turn(fill_paper(img, known, rect, seed=79))
    return np.clip(out, 0, 255).round().astype(np.uint8), rect


def check_sheet(paths, dst, cols=10, scale=0.2):
    tw, th = round(W * scale), round(H * scale); gap = 8
    rows = -(-len(paths) // cols)
    sheet = Image.new('RGB', (cols * (tw + gap) + gap, rows * (th + gap + 14) + gap), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for i, p in enumerate(paths):
        x = gap + (i % cols) * (tw + gap); y = gap + (i // cols) * (th + gap + 14)
        sheet.paste(Image.open(p).convert('RGB').resize((tw, th), Image.LANCZOS), (x, y))
        c = BLEED * scale; sf = SAFE * scale
        d.rectangle((x + c, y + c, x + tw - c, y + th - c), outline=(20, 20, 20))
        for xa, ya, xb, yb in ((x + sf, y + sf, x + tw - sf, y + sf), (x + sf, y + th - sf, x + tw - sf, y + th - sf),
                               (x + sf, y + sf, x + sf, y + th - sf), (x + tw - sf, y + sf, x + tw - sf, y + th - sf)):
            n = int(max(abs(xb - xa), abs(yb - ya)) // 6)
            for j in range(0, n, 2):
                f0, f1 = j / n, min(1, (j + 1) / n)
                d.line((xa + (xb - xa) * f0, ya + (yb - ya) * f0, xa + (xb - xa) * f1, ya + (yb - ya) * f1), fill=(200, 60, 30))
        d.text((x, y + th + 2), os.path.basename(p).split('.')[0], fill=(40, 40, 40))
    sheet.save(dst, quality=88)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('out_dir')
    ap.add_argument('--fit', choices=['safe', 'original'], required=True)
    ap.add_argument('--back', help='full-size finished card back (not kept in the repository)')
    ap.add_argument('--faces', default=os.path.join(HERE, '..', 'cards', 'aeonic'))
    ap.add_argument('--only', help='comma-separated card numbers, e.g. 00,40,77')
    ap.add_argument('--scale', type=float, help=f'with --fit safe: art scale to use instead of the automatic one (which never goes below {K_FLOOR})')
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    names = sorted(f for f in os.listdir(args.faces) if f[:2].isdigit() and f.endswith('.jpg'))
    if args.only: names = [f for f in names if f[:2] in args.only.split(',')]
    fails = []

    # Pass 1: where is each card, and where are its frame lines?
    geoms = {}
    for f in names:
        a = np.asarray(Image.open(os.path.join(args.faces, f)).convert('RGB')).astype(float)
        (x0, y0, x1, y1), bg = card_box(a)
        crop = a[y0:y1, x0:x1].copy()
        crop[corner_fill(crop, bg[y0:y1, x0:x1])] = (232, 220, 200)   # plain paper, so the scan's edge shadow
        geoms[f] = ((0, 0, x1 - x0, y1 - y0), frame_lines(crop)[:4])  # is not mistaken for a frame line
    need = {f: frame_k(g) for f, g in geoms.items()}
    k = 1. if args.fit == 'original' else (args.scale or min(1., max(K_FLOOR, min(need.values()))))
    print(f"fit: {args.fit}; art scale {k:.3f} of the full cut size")

    # Pass 2: build each card.
    outs = []
    for f in names:
        a = np.asarray(Image.open(os.path.join(args.faces, f)).convert('RGB')).astype(float)
        (x0, y0, x1, y1), bg = card_box(a)
        crop = a[y0:y1, x0:x1]
        img, known, rect, s = place(crop, corner_fill(crop, bg[y0:y1, x0:x1]), k)
        out = np.clip(fill_paper(img, known, rect, seed=int(f[:2])), 0, 255).round().astype(np.uint8)
        dst = os.path.join(args.out_dir, f[:2] + '.jpg')
        Image.fromarray(out).save(dst, quality=95, subsampling=0, dpi=(300, 300), optimize=True)
        outs.append(dst)
        ring = np.ones((H, W), bool); ring[BLEED:H - BLEED, BLEED:W - BLEED] = False
        stray = int((warmth(out.astype(float))[ring] < WARM / 2).sum())   # scanner white or grey left in the bleed
        pad = (rect[0] - BLEED, rect[1] - BLEED)
        gap = frame_gap(geoms[f], k)
        flag = '' if gap >= 0 else f'  frame line {-gap:.0f} px past the safe line (scale {need[f]:.3f} would fix it)'
        print(f"{f[:2]}  scan {x1 - x0}x{y1 - y0} -> art {rect[2] - rect[0]}x{rect[3] - rect[1]} (x{s:.3f}), paper pad {pad[0]},{pad[1]} px; non-paper pixels in bleed {stray}{flag}")
        if stray > 50: fails.append(f'{f}: {stray} non-paper pixels in the bleed')

    if args.back:
        b, rect = make_back(args.back, k)
        dst = os.path.join(args.out_dir, 'back.png')
        Image.fromarray(b).save(dst, dpi=(300, 300), optimize=True)
        c = np.asarray(Image.open(dst).convert('RGB')).astype(int)
        diff = int(np.abs(c - c[::-1, ::-1]).max())
        print(f"back  -> art {rect[2] - rect[0]}x{rect[3] - rect[1]}; largest difference from its half turn: {diff}")
        if diff: fails.append(f'back is not symmetric (difference {diff})')
        outs.append(dst)
    else:
        print("back  skipped (no --back file given)")

    for p in outs:
        im = Image.open(p)
        if im.size != (W, H): fails.append(f'{p} is {im.size}, not {W}x{H}')
        if tuple(round(v) for v in im.info.get('dpi', (0, 0))) != (300, 300): fails.append(f'{p} is not marked 300 dpi')
    check_sheet(outs, os.path.join(args.out_dir, 'check-sheet.jpg'))
    print(f"{len(outs)} files in {args.out_dir}, plus check-sheet.jpg")
    for m in fails: print('FAILED:', m)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
