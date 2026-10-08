"""Rotational ambigram workbench: words that read the same after a half turn.

Only the left half of the word is drawn. The right half is the left half turned
180 degrees about the word's centre, so the finished word is exactly symmetric.
Readability is the design work; symmetry is automatic.

Coordinates: one unit = 1/100 of the x-height. Baseline y = 0, x-height y = 100,
y points up. The word turns about (0, 50): a point (x, y) lands on (-x, 100 - y).

    python3 -I ambigram.py pairs <outdir> <word>           letter-pair sheet from fonts
    python3 -I ambigram.py word  <outdir> [glyph-set name]  draw a designed word
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def rot(x): return x[::-1, ::-1]

# ---------------------------------------------------------------- letter pairs
def pairs(word):
    """Letter i must turn into letter n-1-i. A middle letter must turn into itself."""
    w = word.replace(' ', '').lower()
    n = len(w)
    out = [(w[i], w[n - 1 - i]) for i in range(n // 2)]
    if n % 2:
        out.append((w[n // 2], w[n // 2]))
    return out

FONTS = [
    ('DejaVu Serif Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'),
    ('Liberation Serif Italic', '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'),
    ('FreeSerif Bold Italic', '/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf'),
    ('Liberation Sans Bold', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
]

def pair_sheet(word, path):
    """Each pair: the left letter as written beside the right letter turned over.
    The closer the two look, the less drawing that pair needs."""
    ps = pairs(word)
    cell, pad, lab = 150, 16, 26
    W = lab * 3 + len(FONTS) * 2 * (cell * 2 + pad)
    H = lab + len(ps) * (cell + pad) + pad
    sheet = Image.new('RGB', (W, H), (246, 236, 214))
    d = ImageDraw.Draw(sheet)
    x0 = lab * 3
    for j, (name, f) in enumerate(FONTS):
        for c, case in enumerate(('lower', 'UPPER')):
            x = x0 + (j * 2 + c) * (cell * 2 + pad)
            d.text((x, 6), f'{name} {case}', fill=(120, 60, 20))
    font_small = ImageFont.truetype(FONTS[0][1], 18)
    for i, (a, b) in enumerate(ps):
        y = lab + i * (cell + pad)
        d.text((6, y + cell // 2 - 10), f'{a}~{b}', fill=(8, 60, 60), font=font_small)
        for j, (name, f) in enumerate(FONTS):
            font = ImageFont.truetype(f, int(cell * 0.8))
            for c, case in enumerate((str.lower, str.upper)):
                x = x0 + (j * 2 + c) * (cell * 2 + pad)
                for k, ch in enumerate((case(a), case(b))):
                    g = Image.new('L', (cell, cell), 0)
                    gd = ImageDraw.Draw(g)
                    gd.text((cell / 2, cell / 2), ch, fill=255, font=font, anchor='mm')
                    if k == 1:
                        g = g.rotate(180)
                    col = Image.new('RGB', (cell, cell), (8, 72, 72) if k == 0 else (184, 120, 56))
                    sheet.paste(col, (x + k * cell, y), g)
    sheet.save(path)

# ---------------------------------------------------------------- pen strokes
PEN_ANGLE = math.radians(35)        # broad-nib pen; a half turn leaves the nib angle unchanged
NIB, HAIR = 17.0, 3.2               # nib width and hairline width, in units

def spline(pts, n=24):
    """Smooth curve through the points (Catmull-Rom)."""
    p = np.asarray(pts, dtype=float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    out = np.array(out)
    # even spacing along the curve, so the pen leaves no gaps
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(out, axis=0).T))]
    t = np.arange(0, seg[-1], 0.35)
    return np.c_[np.interp(t, seg, out[:, 0]), np.interp(t, seg, out[:, 1])]

def nib_polygon(x, y, scale, nib, hair):
    """Outline of the pen tip: a thin ellipse turned to the pen angle."""
    a = np.linspace(0, 2 * math.pi, 18, endpoint=False)
    ex, ey = nib / 2 * np.cos(a), hair / 2 * np.sin(a)
    ca, sa = math.cos(PEN_ANGLE), math.sin(PEN_ANGLE)
    return [(x + (ex[i] * ca - ey[i] * sa) * scale, y + (ex[i] * sa + ey[i] * ca) * scale) for i in range(len(a))]

class Pen:
    """Draws on two layers: ink (the letters) and accent (stars and chosen strokes)."""
    def __init__(self, width_u, height_u, scale):
        self.s = scale
        self.W, self.H = int(width_u * scale), int(height_u * scale)
        self.layers = {k: Image.new('L', (self.W, self.H), 0) for k in ('ink', 'accent')}
        self.draw = {k: ImageDraw.Draw(v) for k, v in self.layers.items()}
        self.cx, self.cy = self.W / 2, self.H / 2       # word centre (0, 50) sits here

    def xy(self, x, y):
        return self.cx + x * self.s, self.cy - (y - 50) * self.s

    def stroke(self, pts, nib=NIB, hair=HAIR, taper=(0.0, 0.0), layer='ink'):
        c = spline(pts)
        L = len(c)
        d = self.draw[layer]
        for i, (x, y) in enumerate(c):
            t = i / max(1, L - 1)
            k = 1.0
            if taper[0] and t < taper[0]: k = 0.35 + 0.65 * t / taper[0]
            if taper[1] and t > 1 - taper[1]: k = min(k, 0.35 + 0.65 * (1 - t) / taper[1])
            X, Y = self.xy(x, y)
            d.polygon(nib_polygon(X, Y, self.s, nib * k, max(hair, hair * k)), fill=255)

    def star(self, x, y, r, layer='accent'):
        """Four-pointed star (the i's dot)."""
        X, Y = self.xy(x, y)
        R = r * self.s
        d = self.draw[layer]
        d.polygon([(X, Y - R * 1.4), (X + R * 0.45, Y), (X, Y + R * 1.4), (X - R * 0.45, Y)], fill=255)
        d.polygon([(X - R, Y), (X, Y - R * 0.3), (X + R, Y), (X, Y + R * 0.3)], fill=255)

# ---------------------------------------------------------------- the word
def draw_word(glyphs, pitch, scale=8):
    """Draws the designed left-half glyphs, then adds their half-turned copies.
    Returns (ink, accent) masks, each exactly the same after a half turn."""
    n = len(glyphs)
    pen = Pen((2 * n + 2) * pitch, 300, scale)
    for k, g in enumerate(glyphs):
        gx = (k - n + 0.5) * pitch           # left-half slots; the word's centre is x = 0
        for st in g['strokes']:
            pts = [(gx + x, y) for x, y in st['pts']]
            pen.stroke(pts, nib=st.get('nib', NIB), hair=st.get('hair', HAIR),
                       taper=st.get('taper', (0, 0)), layer='accent' if st.get('accent') else 'ink')
        for (x, y, r) in g.get('dots', []):
            pen.star(gx + x, y, r)
    out = []
    for k in ('ink', 'accent'):
        a = np.asarray(pen.layers[k], dtype=np.float32) / 255
        out.append(np.maximum(a, rot(a)))    # right half = left half turned over
    ink, acc = out
    return np.clip(ink - acc, 0, 1), acc     # accent sits on top of ink

def trim(ink, acc, margin=40):
    """Crop both masks to the drawing, keeping even sizes so the centre stays on a pixel edge."""
    both = np.maximum(ink, acc) > 0.02
    ys, xs = np.where(both)
    h, w = both.shape
    my = max(0, min(ys.min(), h - 1 - ys.max()) - margin)     # same margin top and bottom
    mx = max(0, min(xs.min(), w - 1 - xs.max()) - margin)
    return ink[my:h - my, mx:w - mx], acc[my:h - my, mx:w - mx]

def paint(ink, acc, colors, size=None):
    paper, inkc, accc = colors
    h, w = ink.shape
    im = Image.new('RGB', (w, h), paper)
    for m, c in ((ink, inkc), (acc, accc)):
        im.paste(Image.new('RGB', (w, h), c), (0, 0), Image.fromarray((m * 255).astype(np.uint8)))
    return im.resize(size, Image.LANCZOS) if size else im

TEAL, GOLD, CREAM = (8, 62, 62), (186, 118, 52), (246, 232, 204)

def sheet_word(ink, acc, path, label=''):
    """The word as drawn above the same word turned upside down."""
    h, w = ink.shape
    up = paint(ink, acc, (CREAM, TEAL, GOLD), (w // 4, h // 4))
    down = up.rotate(180)
    pad = 30
    S = Image.new('RGB', (up.width + 2 * pad, 2 * up.height + 3 * pad + 20), CREAM)
    S.paste(up, (pad, pad + 20)); S.paste(down, (pad, 2 * pad + 20 + up.height))
    ImageDraw.Draw(S).text((pad, 6), label + '   top: as drawn   bottom: turned upside down', fill=(120, 60, 20))
    S.save(path)

def on_card(card, ink, acc, centre, width, banner=False):
    """Places the word on a card centred at `centre`, `width` px wide, then adds the
    half-turned copy of the whole overlay, so the card stays exactly symmetric."""
    a = np.asarray(card.convert('RGB')).astype(np.float32)
    H, W = a.shape[:2]
    h, w = ink.shape
    tw = int(round(width / 2)) * 2
    th = int(round(h * tw / w / 2)) * 2
    def fit(m):
        return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS),
                          dtype=np.float32) / 255
    layers = []
    for m in (ink, acc):
        full = np.zeros((H, W), np.float32)
        y0, x0 = int(round(centre[1] - th / 2)), int(round(centre[0] - tw / 2))
        full[y0:y0 + th, x0:x0 + tw] = fit(m)
        layers.append(np.maximum(full, rot(full)))
    if banner:
        # ribbon with notched ends behind the word: cream fill, teal edge, gold keyline
        word = np.maximum(*layers) > 0.3
        ys, xs = np.where(word)
        cx, cy = (W - 1) / 2, (H - 1) / 2
        hw = max(cx - xs.min(), xs.max() - cx) + 34
        hh = max(cy - ys.min(), ys.max() - cy) + 8
        def ribbon(inset):
            w, h, n = hw - inset, hh - inset, 22 - inset * 0.4
            return [(cx - w, cy - h), (cx + w, cy - h), (cx + w - n, cy), (cx + w, cy + h),
                    (cx - w, cy + h), (cx - w + n, cy)]
        S = 4
        def poly_mask(pts, outline=0):
            im = Image.new('L', (W * S, H * S), 0)
            ImageDraw.Draw(im).polygon([(x * S + S / 2, y * S + S / 2) for x, y in pts], fill=255)
            m = np.asarray(im.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255
            return np.maximum(m, rot(m))
        outer, inner = poly_mask(ribbon(0)), poly_mask(ribbon(5))
        key_o, key_i = poly_mask(ribbon(9)), poly_mask(ribbon(11))
        a = a * (1 - outer[..., None]) + np.array(TEAL_CARD) * outer[..., None]
        a = a * (1 - inner[..., None]) + np.array(CREAM_CARD) * inner[..., None]
        key = np.clip(key_o - key_i, 0, 1)
        a = a * (1 - key[..., None]) + np.array(GOLD_CARD) * key[..., None]
    for m, c in zip(layers, (TEAL_CARD, GOLD_CARD)):
        a = a * (1 - m[..., None]) + np.array(c) * m[..., None]
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8))

def card_colours(card):
    a = np.asarray(card.convert('RGB')).reshape(-1, 3).astype(float)
    g = a.mean(axis=1)
    cream = np.median(a[g > 215], axis=0)
    teal = np.median(a[(g < 70) & (a[:, 2] > a[:, 0])], axis=0)
    gold = np.median(a[(a[:, 0] > 150) & (a[:, 2] < 90)], axis=0)
    return tuple(cream), tuple(teal), tuple(gold)

if __name__ == '__main__':
    cmd, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    if cmd == 'pairs':
        word = sys.argv[3]
        pair_sheet(word, f'{outdir}/pairs_{word.replace(" ", "-")}.png')
        print(pairs(word))
    elif cmd in ('word', 'card'):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import glyphs_aeonicarts as G
        name = sys.argv[3] if len(sys.argv) > 3 else 'v1'
        gl = getattr(G, name)
        ink, acc = trim(*draw_word(gl['glyphs'], gl['pitch']))
        exact = all(((m > 0.5) == rot(m > 0.5)).all() for m in (ink, acc))
        print('word: exact symmetry:', exact)
        if cmd == 'word':
            sheet_word(ink, acc, f'{outdir}/ambigram_{name}.png', label=f'aeonicarts {name}')
            paint(ink, acc, (CREAM, TEAL, GOLD), (ink.shape[1] // 2, ink.shape[0] // 2)).save(
                f'{outdir}/ambigram_{name}_logo.png')
        else:
            card = Image.open(sys.argv[4])
            CREAM_CARD, TEAL_CARD, GOLD_CARD = card_colours(card)
            W, H = card.size
            base = os.path.splitext(os.path.basename(sys.argv[4]))[0]
            for tag, centre, width, banner in (('middle-banner', (W / 2, H / 2), 0.50 * W, True),
                                               ('top-and-bottom', (W / 2, 162), 0.30 * W, False)):
                out = on_card(card, ink, acc, centre, width, banner)
                o = np.asarray(out).astype(np.int16)
                print(f'{tag}: largest difference from its upside-down copy:',
                      int(np.abs(o - o[::-1, ::-1]).max()))
                out.save(f'{outdir}/{base}_ambigram-{tag}.png')
