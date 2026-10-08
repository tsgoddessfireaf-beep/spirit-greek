import sys, math
from PIL import Image, ImageDraw, ImageOps
import numpy as np
from scipy import ndimage

SRC, OUT = sys.argv[1], sys.argv[2]
src = Image.open(SRC).convert('RGB')
a = np.asarray(src); g = np.asarray(ImageOps.grayscale(src))
CREAM = np.median(a[g > 200], axis=0)
INK = np.median(a[g < 60], axis=0)

TW, TH = 958, 1642
PX_MM = TW / 70.0
BLEED, BAND, GAP, KEY = round(3 * PX_MM), round(4 * PX_MM), 10, 4
ART_INSET = BAND + GAP + KEY + 10
crop = src.crop((37, 33, 920, 1609))               # art inside the old border
CCX, CCY = 441.5, 788.0                             # rotation centre (continuous, crop coords)
BX, BY, BW, BH = 291, 638, 301, 300                 # work box centred on it
S = 4                                               # supersampling for drawn elements
rng = np.random.default_rng(11)

def rot(x): return x[::-1, ::-1]
def noise(shape, cell):
    gh, gw = shape[0] // cell + 3, shape[1] // cell + 3
    n = np.asarray(Image.fromarray(rng.standard_normal((gh, gw)).astype(np.float32), 'F')
                   .resize((shape[1], shape[0]), Image.BICUBIC))
    return n / (n.std() + 1e-6)
def even(n): return (n + rot(n)) / math.sqrt(2)     # same after a 180-degree turn
def odd(n): return (n - rot(n)) / math.sqrt(2)      # displacement that stays symmetric

import os
def roughen(mask, strength=1.0, specks=True):
    if os.environ.get('ROUGH') == '0':
        return (mask > 0.5).astype(np.float32)
    """Hand-inked look: wobbly path, uneven weight, ragged edges. Keeps 180-degree symmetry."""
    H, W = mask.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = odd(noise((H, W), 110)) * 5.0 * strength, odd(noise((H, W), 110)) * 5.0 * strength
    m = ndimage.map_coordinates(mask, [yy + dy, xx + dx], order=1, mode='constant')
    m = ndimage.gaussian_filter(m, 3.0)
    near = np.clip(m * 3.0, 0, 1)                    # texture only on and beside the lines
    v = m + near * strength * (0.20 * even(noise((H, W), 180)) + 0.10 * even(noise((H, W), 5)))
    hard = ((v > 0.5) & (m > 0.08)).astype(np.float32)
    if specks:
        sp = (even(noise((H, W), 3)) > 2.7) & (m < 0.85)      # tiny dry-brush gaps near edges
        hard[sp] = 0
    return hard

def canvas4():
    im = Image.new('L', (BW * S, BH * S), 0)
    return im, ImageDraw.Draw(im), BW * S / 2, BH * S / 2   # centre (602, 600)

def to_alpha(mask4):
    return np.asarray(Image.fromarray((mask4 * 255).astype(np.uint8)).resize((BW, BH), Image.LANCZOS)) / 255.0

# ---------- A: Vesica Piscis, roughened ----------
def vesica():
    im, d, cx, cy = canvas4()
    R, lw, thin = 78, 4.5, 3.0
    def circ(x, y, r, w): d.ellipse([cx + (x - r) * S, cy + (y - r) * S, cx + (x + r) * S, cy + (y + r) * S], outline=255, width=round(w * S))
    def line(p, q, w): d.line([cx + p[0] * S, cy + p[1] * S, cx + q[0] * S, cy + q[1] * S], fill=255, width=round(w * S))
    def dot(x, y, r): d.ellipse([cx + (x - r) * S, cy + (y - r) * S, cx + (x + r) * S, cy + (y + r) * S], fill=255)
    circ(0, -R / 2, R, lw); circ(0, R / 2, R, lw)
    hw = R * math.sqrt(3) / 2
    line((0, -R * 1.5), (0, R * 1.5), thin); line((-hw, 0), (hw, 0), thin)
    for p, q in [((0, -R / 2), (hw, 0)), ((hw, 0), (0, R / 2)), ((0, R / 2), (-hw, 0)), ((-hw, 0), (0, -R / 2))]:
        line(p, q, thin)
    dot(0, -R / 2, 4.5); dot(0, R / 2, 4.5); dot(0, 0, 3.5)
    m = np.asarray(im) / 255.0
    m = np.maximum(m, rot(m))
    return to_alpha(roughen(m))

# ---------- B: rose pair, cut from the corner rose ----------
def rose_pair():
    poly = [(39,34),(100,34),(115,50),(175,55),(180,71),(210,71),(217,85),(235,115),(235,170),
            (195,210),(175,245),(155,265),(120,260),(105,305),(50,315),(39,305)]
    m = Image.new('L', src.size, 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    dark = (255 - np.asarray(ImageOps.grayscale(src)).astype(np.float32)) / 255.0
    dark = np.clip((dark - 0.06) / 0.9, 0, 1) * (np.asarray(m) / 255.0)
    lab, n = ndimage.label(dark > 0.5)
    sizes = ndimage.sum(dark > 0.5, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, sz in enumerate(sizes) if sz >= 400])
    keep = ndimage.binary_dilation(keep, iterations=2)
    dark = dark * keep
    ys, xs = np.nonzero(dark > 0.1)
    rose = dark[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    target_h = 116
    sc = target_h / rose.shape[0]
    rim = Image.fromarray((rose * 255).astype(np.uint8)).resize(
        (round(rose.shape[1] * sc), target_h), Image.LANCZOS)
    A = np.zeros((BH, BW), np.float32)
    r = np.asarray(rim) / 255.0
    top = 150 - 4 - target_h                       # top rose sits in the upper cranium
    left = round(150.5 - r.shape[1] / 2)
    A[top:top + r.shape[0], left:left + r.shape[1]] = r
    return np.maximum(A, rot(A))

# ---------- C: NOON ambigram ----------
def noon():
    im, d, cx, cy = canvas4()
    k = 0.92
    def P(pts, ox, oy): return [(cx + (ox + x * k) * S, cy + (oy + y * k) * S) for x, y in pts]
    w, h, st, dt, sf = 38, 56, 6, 13, 5
    # N built from its own 180-degree-symmetric parts (top-left box at ox, oy)
    def N(ox, oy):
        parts = [
            [(0, 0), (st, 0), (st, h), (0, h)],                      # left stem
            [(w - st, 0), (w, 0), (w, h), (w - st, h)],              # right stem
            [(0, 0), (dt, 0), (w, h), (w - dt, h)],                  # thick diagonal
            [(-sf, h - 3.5), (st + sf, h - 3.5), (st + sf, h), (-sf, h)],          # foot serif
            [(w - st - sf, 0), (w + sf, 0), (w + sf, 3.5), (w - st - sf, 3.5)],    # its partner
            [(-sf, 0), (st, 0), (st, 3.5), (-sf, 3.5)],              # head spur
            [(w - st, h - 3.5), (w + sf, h - 3.5), (w + sf, h), (w - st, h)],      # its partner
        ]
        for p in parts: d.polygon(P(p, ox, oy), fill=255)
    # O as a pointed almond (a vesica shape), thick sides, fine tips
    def O(ocx, oy):
        aw, bh = 17, 28
        def lens(a_, b_):
            ys = np.linspace(-b_, b_, 120)
            xs = a_ * (1 - (np.abs(ys) / b_) ** 1.8)
            return [(x, y) for x, y in zip(xs, ys)] + [(-x, y) for x, y in zip(xs[::-1], ys[::-1])]
        d.polygon(P(lens(aw, bh), ocx, oy), fill=255)
        d.polygon(P(lens(aw - 8.5, bh - 5), ocx, oy), fill=0)
    gapx = 8
    n1x = -(w + gapx + 34 + gapx / 2) * 1.0            # left edge of first N
    N(n1x, -h / 2)
    O(n1x + w + gapx + 17, 0)
    m = np.asarray(im) / 255.0
    m = np.maximum(m, rot(m))                         # right half = left half turned over
    # rules with a diamond above and below the word
    im2, d2, cx2, cy2 = canvas4()
    for sgn in (-1, 1):
        y = sgn * 46
        d2.line([cx2 - 62 * S, cy2 + y * S, cx2 + 62 * S, cy2 + y * S], fill=255, width=round(2.6 * S))
        dm = 6
        d2.polygon([(cx2, cy2 + (y - dm) * S), (cx2 + dm * S, cy2 + y * S), (cx2, cy2 + (y + dm) * S), (cx2 - dm * S, cy2 + y * S)], fill=255)
        for ex in (-66, 66):
            d2.ellipse([cx2 + (ex - 2.5) * S, cy2 + (y - 2.5) * S, cx2 + (ex + 2.5) * S, cy2 + (y + 2.5) * S], fill=255)
    m = np.maximum(m, np.asarray(im2) / 255.0)
    return to_alpha(roughen(m))

def card(alpha):
    art = np.asarray(crop).astype(np.float32).copy()
    reg = art[BY:BY + BH, BX:BX + BW]
    if isinstance(alpha, tuple):
        alpha, cover = alpha
        reg = reg * (1 - cover[..., None]) + CREAM * cover[..., None]
    art[BY:BY + BH, BX:BX + BW] = reg * (1 - alpha[..., None]) + INK * alpha[..., None]
    art = Image.fromarray(np.clip(art, 0, 255).astype(np.uint8))
    s = min((TW - 2 * ART_INSET) / art.width, (TH - 2 * ART_INSET) / art.height)
    art = art.resize((round(art.width * s), round(art.height * s)), Image.LANCZOS)
    sx, sy = art.width / crop.width, art.height / crop.height
    W, H = TW + 2 * BLEED, TH + 2 * BLEED
    cv = Image.new('RGB', (W, H), tuple(int(v) for v in INK))
    dd = ImageDraw.Draw(cv)
    dd.rectangle([BLEED + BAND, BLEED + BAND, W - 1 - BLEED - BAND, H - 1 - BLEED - BAND], fill=tuple(int(v) for v in CREAM))
    k0 = BLEED + BAND + GAP
    dd.rectangle([k0, k0, W - 1 - k0, H - 1 - k0], outline=tuple(int(v) for v in INK), width=KEY)
    cv.paste(art, (round(W / 2 - CCX * sx), round(H / 2 - CCY * sy)))
    return cv


# ---------- B2: a new rose, seen from above, same both ways ----------
def rose_top():
    """Top-view rose. Returns (ink_alpha, cover_alpha): cover = where the bloom hides the art behind it."""
    im, d, cx, cy = canvas4()                   # ink
    cov, dc, _, _ = canvas4()                   # bloom/leaf silhouette
    def P(x, y): return (cx + x * S, cy + y * S)
    def box(ox, oy, r): return [cx + (ox - r) * S, cy + (oy - r) * S, cx + (ox + r) * S, cy + (oy + r) * S]
    def leaf(ang_deg, base, tip, half):
        ang = math.radians(ang_deg); ux, uy = math.cos(ang), math.sin(ang); vx, vy = -uy, ux
        def L(s_, o_): return P(ux * s_ + vx * o_, uy * s_ + vy * o_)
        def outline(inset):
            pts = []
            for sgn in (1, -1):
                rng_ = range(41) if sgn == 1 else range(40, -1, -1)
                for i in rng_:
                    f = i / 40; s_ = base + inset + (tip - base - 2 * inset) * f
                    pts.append(L(s_, sgn * (half - inset) * math.sin(math.pi * f) ** 0.8))
            return pts
        d.polygon(outline(0), fill=255); d.polygon(outline(4.5), fill=0)
        dc.polygon(outline(0), fill=255)
        d.line([L(base - 2, 0), L(tip - 6, 0)], fill=255, width=round(2.6 * S))
        for f in (0.3, 0.5, 0.7):
            s_ = base + (tip - base) * f
            for sg in (-1, 1):
                d.line([L(s_, 0), L(s_ + 10, sg * (half - 6))], fill=255, width=round(1.8 * S))
    # leaves first (they sit behind the bloom); partner leaves come from the 180-degree copy
    leaf(-115, 52, 122, 17)
    leaf(-58, 60, 112, 13)
    def petal(ox, oy, r, lw, lip_ang=None, lip=0):
        d.ellipse(box(ox, oy, r), fill=0, outline=255, width=round(lw * S))
        dc.ellipse(box(ox, oy, r), fill=255)
        if lip:
            d.arc(box(ox, oy, r - lip), lip_ang - 38, lip_ang + 38, fill=255, width=round(lw * 0.75 * S))
    def ring(n, rho, r, phase, lw, lip):
        half_n = n // 2
        for k in range(half_n):                 # paint opposite petals together: keeps 180-degree symmetry
            for kk in (k, k + half_n):
                al = phase + kk * 360 / n
                petal(rho * math.cos(math.radians(al)), rho * math.sin(math.radians(al)), r, lw, al, lip)
    ring(6, 41, 35, 0, 4.8, 8)
    ring(6, 25, 28, 30, 4.4, 7)
    ring(4, 12, 21, 15, 4.0, 6)
    d.ellipse(box(0, 0, 15), fill=0, outline=255, width=round(3.8 * S))
    dc.ellipse(box(0, 0, 15), fill=255)
    for arm in (0, math.pi):                     # bud: two open, interlocking curls
        pts = []
        for i in range(120):
            tt = i / 119; r_ = 3.0 + 8.0 * tt; th = arm + tt * 2 * math.pi * 0.62
            pts.append(P(r_ * math.cos(th), r_ * math.sin(th)))
        d.line(pts, fill=255, width=round(2.6 * S), joint='curve')
    m = np.asarray(im) / 255.0; c = np.asarray(cov) / 255.0
    # a petal drawn later must also win on the other half: rebuild symmetric by rotating the painted result
    m = np.maximum(m, rot(m)) * np.maximum(c, rot(c))
    c = np.maximum(c, rot(c))
    return to_alpha(roughen(m, strength=0.7)), to_alpha(c)

# ---------- C2: AEONIC / ARTS, with its upside-down twin below ----------
def name_pair():
    from PIL import ImageFont
    im, d, cx, cy = canvas4()
    font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', round(38 * S))
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', round(28 * S))
    def tracked(text, font, y_mid, track):
        widths = [d.textlength(ch, font=font) for ch in text]
        total = sum(widths) + track * S * (len(text) - 1)
        x = cx - total / 2
        for ch, w_ in zip(text, widths):
            d.text((x, cy + y_mid * S), ch, font=font, fill=255, anchor='lm')
            x += w_ + track * S
    tracked('AEONIC', font_big, -78, 3.5)
    tracked('ARTS', font_small, -40, 7)
    # small flourish between ARTS and the centre
    for ex in (-46, 46):
        d.line([cx + (ex - 14 * (1 if ex > 0 else -1)) * S, cy - 40 * S, cx + ex * S, cy - 40 * S],
               fill=255, width=round(2.2 * S))
    m = np.asarray(im) / 255.0
    # centre divider: rule with a diamond, symmetric by itself
    im2, d2, cx2, cy2 = canvas4()
    d2.line([cx2 - 56 * S, cy2, cx2 + 56 * S, cy2], fill=255, width=round(2.6 * S))
    dm = 6
    d2.polygon([(cx2, cy2 - dm * S), (cx2 + dm * S, cy2), (cx2, cy2 + dm * S), (cx2 - dm * S, cy2)], fill=255)
    for ex in (-60, 60):
        d2.ellipse([cx2 + (ex - 2.5) * S, cy2 - 2.5 * S, cx2 + (ex + 2.5) * S, cy2 + 2.5 * S], fill=255)
    m = np.maximum(np.maximum(m, rot(m)), np.asarray(im2) / 255.0)
    return to_alpha(roughen(m, strength=0.45, specks=False))

BUILDS = {'A_vesica-piscis-inked': vesica, 'B_rose-pair': rose_pair, 'C_noon-ambigram': noon,
          'B2_new-rose': rose_top, 'C2_aeonic-arts': name_pair}
for name in (sys.argv[3:] or list(BUILDS)):
    card(BUILDS[name]()).save(f'{OUT}/design1_{name}_print-with-bleed.png', dpi=(348, 348))
    print('built', name)
