"""Print-ready MakePlayingCards (MPC) files for the Aeonic Arts tarot.

    python3 -I print/mpc_print.py <out-dir> [--back <full-size-back.png>] [--faces cards/aeonic] [--only 00,40,77]

MPC's tarot rules (print/mpc-guide.html): every card is a 897 x 1497 pixel image at
300 dpi; 36 px of bleed is cut away on each side; a further 36 px inside the cut is
the safe area. For each of the 78 faces this program:

  1. finds the card in the 1909 scan and straightens it, using its frame lines,
  2. cuts it exactly at the outer edge of Smith's frame (the worn old paper goes),
  3. fits the picture to one box, the same for every card, so every card has the same
     clean cream border: 40 px (3.4 mm) at the sides, 61 px (5.2 mm) top and bottom
     after cutting, with the frame inside the safe area,
  4. draws a crisp teal edge on Smith's frame line and saves NN.jpg (quality 95,
     full colour detail, 300 dpi).

Smith's frames differ in shape by a few per cent from card to card; fitting them to one
box squeezes or stretches a picture by that much, which the report lists.

With --back it also makes back.png from the full-size card back (kept out of this
public repository): corners filled, widened to the card shape, bleed added, and made
exactly identical after a half turn, so it never reveals a reversed card. PNG keeps that
exact; JPEG would not.

check-sheet.jpg shows every card with its cut line (solid) and safe line (dashed).
Exit status is 1 if a self-check fails.
"""
import sys, os, argparse, importlib.util
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('aeonic', os.path.join(HERE, '..', 'cards', 'aeonic-tools', 'aeonic.py'))
aeonic = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(aeonic)
lum, flood = aeonic.lum, aeonic.flood

W, H = 897, 1497                       # MPC tarot file, bleed included
BLEED = 36                             # cut away on each side
TW, TH = W - 2 * BLEED, H - 2 * BLEED  # 825 x 1425: the finished card
SAFE = 2 * BLEED                       # safe line, from the file edge
SIDE = 76                              # frame's outer edge from the file edge, left and right: 40 px border after the cut
BOX_ASPECT = 0.572                     # the box every picture is fitted to (width / height): the deck's median frame
BW = W - 2 * SIDE; BH = round(BW / BOX_ASPECT); TOP = (H - BH) // 2
PAPER = (228, 217, 201)                # border cream: between the title-strip paper and the back's paper
TEAL = aeonic.TEAL                     # the deck's frame colour
BACK_SCALE = 0.95                      # the back's art, so its copper frame and notice sit inside the safe line
INSET = 3                              # px trimmed off the scan's worn card edge
WARM = 12                              # paper is warm (red minus blue > WARM); the scanner background is
                                       # neutral white or grey, or bluish after recolouring

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


def first_dark(dark):
    """Per row: the first dark pixel from the left (nan where there is none)."""
    idx = np.argmax(dark, 1).astype(float); idx[~dark.any(1)] = np.nan
    return idx


def mode_edge(v):
    """The position most rows (or columns) agree on, and the share that agree."""
    v = v[~np.isnan(v)]
    hist, e = np.histogram(v, bins=np.arange(v.min(), v.max() + 3, 2))
    i = hist.argmax(); sel = v[(v >= e[i] - 2) & (v <= e[i + 1] + 2)]
    return float(np.median(sel)), sel.size / v.size


def fit_slope(t, v, centre):
    ok = ~np.isnan(v) & (np.abs(v - centre) < 6); t, v = t[ok], v[ok]
    return np.polyfit(t, v, 1)[0] if t.size > 50 else 0.


def frame_box(c):
    """Outer edges of Smith's frame (left, top, right, bottom), how many rows/columns agree on
    each, and the tilt of the left, right and top lines. The bottom is the title box's line."""
    h, w = c.shape[:2]; dark = lum(c) < 110
    e = 8; dark[:e] = dark[-e:] = False; dark[:, :e] = dark[:, -e:] = False   # the scan's dark edge is not the frame
    rows = np.arange(int(h * .15), int(h * .85)); cols = np.arange(int(w * .15), int(w * .85))
    nx, ny = int(w * .12), int(h * .12)
    L = first_dark(dark[rows, :nx]); R = w - 1 - first_dark(dark[rows, ::-1][:, :nx])
    T = first_dark(dark[:ny, cols].T); B = h - 1 - first_dark(dark[::-1][:ny, cols].T)
    (l, fl), (r, fr), (t, ft), (b, fb) = mode_edge(L), mode_edge(R), mode_edge(T), mode_edge(B)
    return (l, t, r, b), (fl, fr, ft, fb), (fit_slope(rows, L, l), fit_slope(rows, R, r), -fit_slope(cols, T, t))


def make_face(path, seed):
    """One card face: straightened, cut at the frame, fitted to the deck's box on clean paper."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(float)
    (x0, y0, x1, y1), bg = card_box(a)
    c = a[y0:y1, x0:x1].copy(); c[bg[y0:y1, x0:x1]] = PAPER
    tilt = float(np.degrees(np.median(frame_box(c)[2])))
    c = np.asarray(Image.fromarray(c.astype(np.uint8)).rotate(tilt, resample=Image.BICUBIC, fillcolor=PAPER))
    (l, t, r, b), agree, _ = frame_box(c.astype(float))
    art = Image.fromarray(c).crop((round(l) + 1, round(t) + 1, round(r), round(b))).resize((BW, BH), Image.LANCZOS)
    rng = np.random.default_rng(seed)                  # a faint grain, so the border prints as paper, not flat plastic
    out = Image.fromarray(np.clip(np.array(PAPER, float) + rng.normal(0, 1.5, (H, W, 1)), 0, 255).astype(np.uint8))
    out.paste(art, (SIDE, TOP))
    ImageDraw.Draw(out).rectangle((SIDE, TOP, SIDE + BW - 1, TOP + BH - 1), outline=TEAL, width=3)
    return out, tilt, agree, (r - l) / (b - t)


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
    ap.add_argument('--back', help='full-size finished card back (not kept in the repository)')
    ap.add_argument('--faces', default=os.path.join(HERE, '..', 'cards', 'aeonic'))
    ap.add_argument('--only', help='comma-separated card numbers, e.g. 00,40,77')
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    names = sorted(f for f in os.listdir(args.faces) if f[:2].isdigit() and f.endswith('.jpg'))
    if args.only: names = [f for f in names if f[:2] in args.only.split(',')]
    fails, outs = [], []
    print(f"every picture fitted to {BW}x{BH} px; border after the cut {SIDE - BLEED} px at the sides, {TOP - BLEED} px top and bottom")

    for f in names:
        out, tilt, agree, aspect = make_face(os.path.join(args.faces, f), seed=int(f[:2]))
        dst = os.path.join(args.out_dir, f[:2] + '.jpg')
        out.save(dst, quality=95, subsampling=0, dpi=(300, 300), optimize=True)
        outs.append(dst)
        stretch = (BOX_ASPECT / aspect - 1) * 100       # + = picture made wider, - = narrower
        flag = '  CHECK: frame edge unclear' if min(agree) < .15 else ''
        flag += f'  CHECK: shape changed {stretch:+.1f}%' if abs(stretch) > 5 else ''
        print(f"{f[:2]}  straightened {tilt:+.2f} deg; width {stretch:+.1f}%; frame edges agreed by "
              f"{', '.join(f'{x:.0%}' for x in agree)} of rows/columns{flag}")

    if args.back:
        b, rect = make_back(args.back, BACK_SCALE)
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
