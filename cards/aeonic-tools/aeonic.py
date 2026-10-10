"""Aeonic Arts edition of the 1909 Waite-Smith deck (work in progress, sample cards).
Palette -> silver cups/coins, gold swords -> new coin faces -> carved stone figure ->
copper outline, teal lettering -> 'COINS' titles."""
import sys, math, json
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

INK, PAPER = np.array([54, 45, 40.]), np.array([218, 197, 163.])
TEAL_INK, CREAM = np.array([14, 52, 58.]), np.array([234, 223, 205.])
TEAL = (12, 69, 76)                 # outline, coin circles (card-back teal)
COPPER = (176, 101, 56)             # coin hexagon and Y (card-back copper)
LETTER = (150, 80, 40)              # lettering: deeper copper, readable on cream (contrast 4.6)
SILVER = (np.array([104, 112, 118.]), np.array([236, 238, 240.]))
GOLD = (np.array([140, 94, 30.]), np.array([238, 198, 98.]))
KNOTS = np.array([[0, 0], [35, 35], [45, 39], [62, 41], [80, 120], [110, 165], [150, 178], [200, 188], [260, 198], [300, 300], [360, 360]])

def tone(a): return TEAL_INK + (a - INK) * (CREAM - TEAL_INK) / (PAPER - INK)

def palette(a):
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('HSV')
    h, s, v = [np.asarray(c).astype(float) for c in im.split()]
    deg = h / 255 * 360
    new = np.interp(deg, KNOTS[:, 0], KNOTS[:, 1]) % 360
    w = np.clip((s - 70) / 50, 0, 1)
    deg = deg + w * (((new - deg + 180) % 360) - 180)
    yellow = np.clip(1 - np.abs(deg - 40) / 12, 0, 1) * w
    s = s * (1 - 0.22 * yellow); v = v * (1 - 0.06 * yellow)
    out = Image.merge('HSV', [Image.fromarray(np.uint8((deg % 360) / 360 * 255)), Image.fromarray(np.uint8(np.clip(s, 0, 255))), Image.fromarray(np.uint8(np.clip(v, 0, 255)))])
    return tone(np.asarray(out.convert('RGB')).astype(float))

def lum(a): return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114

def hsv_of(a):
    h, s, v = [np.asarray(c).astype(float) for c in Image.fromarray(a.astype(np.uint8)).convert('HSV').split()]
    return h / 255 * 360, s, v

def shape_mask(size, shapes):
    m = Image.new('L', size, 0); d = ImageDraw.Draw(m)
    for sh in shapes:
        t = sh[0]
        if t == 'poly': d.polygon([tuple(p) for p in sh[1]], fill=255)
        elif t == 'box': d.rectangle(sh[1], fill=255)
        elif t == 'ellipse': cx, cy, rx, ry = sh[1]; d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
        elif t == 'line': (x0, y0), (x1, y1), hw = sh[1], sh[2], sh[3]; d.line([(x0, y0), (x1, y1)], fill=255, width=int(2 * hw)); d.ellipse((x0 - hw, y0 - hw, x0 + hw, y0 + hw), fill=255); d.ellipse((x1 - hw, y1 - hw, x1 + hw, y1 + hw), fill=255)
    return np.asarray(m) > 0

def flood(allowed, seeds):
    H, W = allowed.shape; seen = np.zeros_like(allowed); q = deque()
    for y, x in seeds:
        if 0 <= y < H and 0 <= x < W and allowed[y, x] and not seen[y, x]: seen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < H and 0 <= nx < W and allowed[ny, nx] and not seen[ny, nx]: seen[ny, nx] = True; q.append((ny, nx))
    return seen

def metal(out, a0, mask, kind):
    lo, hi = SILVER if kind == 'silver' else GOLD
    t = np.clip((lum(a0) - 70) / 165, 0, 1)[..., None] ** 0.9
    out[mask] = (lo + (hi - lo) * t)[mask]

def coin_face(rx, ry):
    S = int(max(rx, ry) * 2 * 4); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    g = np.linspace(0, 1, S)[:, None] * 0.6 + np.linspace(0, 1, S)[None, :] * 0.4
    col = (np.array([232, 235, 237]) * (1 - g[..., None]) + np.array([150, 157, 162]) * g[..., None]).astype(np.uint8)
    disc = Image.fromarray(np.dstack([col, np.full((S, S), 255, np.uint8)]), 'RGBA')
    m = Image.new('L', (S, S), 0); ImageDraw.Draw(m).ellipse((0, 0, S - 1, S - 1), fill=255); im.paste(disc, (0, 0), m)
    w = max(4, S // 60); c = S / 2
    d.ellipse((w, w, S - w, S - w), outline=tuple(int(v) for v in TEAL_INK), width=w)
    r = S * 0.075; ang = [math.pi / 2 + k * math.pi / 3 for k in range(6)]
    inner = [(c + 2 * r * math.cos(a), c - 2 * r * math.sin(a)) for a in ang]
    outer = [(c + 4 * r * math.cos(a), c - 4 * r * math.sin(a)) for a in ang]
    for x, y in [(c, c)] + inner + outer: d.ellipse((x - r, y - r, x + r, y + r), outline=TEAL, width=max(2, w // 2))
    cw = max(4, int(w * 1.5))
    d.line(outer + [outer[0]], fill=COPPER, width=cw, joint='curve')
    for v in (outer[1], outer[5], outer[3]): d.line([(c, c), v], fill=COPPER, width=cw)
    return im.resize((max(2, int(2 * rx)), max(2, int(2 * ry))), Image.LANCZOS)

def ring_profile(g, cx, cy, rmax):
    ang = np.linspace(0, 2 * np.pi, 180, endpoint=False); prof = []
    for r in range(rmax):
        xs = (cx + r * np.cos(ang)).astype(int); ys = (cy + r * np.sin(ang)).astype(int)
        prof.append(g[ys, xs].mean())
    return np.array(prof)

def carve(out, a0, circles):
    """Replace carved pentagrams: black disc, stone hexagon + Y with dark edges."""
    g = lum(a0); stone = np.median(out[(g > 170)], axis=0); dark = TEAL_INK
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
    for cx, cy, rguess in circles:
        best = None
        for dx in range(-6, 7, 2):
            for dy in range(-6, 7, 2):
                p = ring_profile(g, cx + dx, cy + dy, int(rguess * 1.4))
                k = int(np.argmax(p[int(rguess * 0.7):])) + int(rguess * 0.7)
                if best is None or p[k] > best[0]: best = (p[k], cx + dx, cy + dy, k, p)
        _, X, Y, R, p = best
        inner = R - 1
        while inner > R * 0.6 and p[inner] > (p[R] + p[int(R * 0.5)]) / 2: inner -= 1
        rin = inner - 1; band = max(5, int(R * 0.14)); edge = max(2, band // 3)
        d.ellipse((X - R + 2, Y - R + 2, X + R - 2, Y + R - 2), fill=tuple(int(v) for v in stone))   # clean stone ring (old star points)
        layer = Image.new('RGB', img.size, tuple(int(v) for v in dark)); ld = ImageDraw.Draw(layer)
        rr = rin - 1; ang = [math.pi / 2 + k * math.pi / 3 for k in range(6)]
        hexa = [(X + rr * math.cos(a), Y - rr * math.sin(a)) for a in ang]
        segs = [(hexa[k], hexa[(k + 1) % 6]) for k in range(6)] + [((X, Y), hexa[1]), ((X, Y), hexa[5]), ((X, Y), hexa[3])]
        for a, b in segs: ld.line([a, b], fill=tuple(int(v) for v in dark), width=band + 2 * edge)
        for a, b in segs: ld.line([a, b], fill=tuple(int(v) for v in stone), width=band)
        disc = Image.new('L', img.size, 0); ImageDraw.Draw(disc).ellipse((X - rin, Y - rin, X + rin, Y + rin), fill=255)
        img.paste(layer, (0, 0), disc)                  # carving trimmed to the circle
        d = ImageDraw.Draw(img)
        d.ellipse((X - rin, Y - rin, X + rin, Y + rin), outline=tuple(int(v) for v in dark), width=edge)
        print(f'  carved circle at ({X},{Y}) ring r={R} inner r={rin}')
    out[:] = np.asarray(img).astype(float)

def find_banner(a0):
    """Title banner: a strip with lettering between two solid lines near the bottom.
    Returns (line_top, line_end, text_top, text_bottom) or None."""
    H, W = a0.shape[:2]; dark = lum(a0) < 125; ink = lum(a0) < 95
    frac = dark[:, int(W * .2):int(W * .8)].mean(1)
    groups = []
    for y in range(int(H * .80), H):
        if frac[y] > .65:
            if groups and y == groups[-1][1] + 1: groups[-1][1] = y
            else: groups.append([y, y])
    for i in range(len(groups) - 1, 0, -1):       # lowest strip with lettering across its middle rows
        bot = groups[i]; prev = groups[i - 1]
        inside = ink[prev[1] + 1:bot[0], int(W * .05):int(W * .95)]
        if bot[0] - prev[1] > H * .03 and inside.size and .03 < inside.mean() < .35:
            h = inside.shape[0]; mid = inside[h // 4:3 * h // 4]
            if mid.mean() > .06: return prev[0], prev[1], prev[1] + 1, bot[0]
    return None

def line_groups(frac, lo, hi, thr=.6):
    g = []
    for i in range(lo, hi):
        if frac[i] > thr:
            if g and i == g[-1][1] + 1: g[-1][1] = i
            else: g.append([i, i])
    return g

def frame_lines(a0):
    """The printed frame: for each side, the outermost solid line with blank card margin outside it.
    Returns (top, bottom, left, right) as [start, end] index ranges, and the line thickness."""
    H, W = a0.shape[:2]; dark = lum(a0) < 125
    rowf = dark[:, int(W * .2):int(W * .8)].mean(1); colf = dark[int(H * .2):int(H * .8), :].mean(0)
    def pick(groups, frac, n, outward_low):
        for g in (groups if outward_low else groups[::-1]):
            outside = frac[:g[0]] if outward_low else frac[g[1] + 1:]
            if (outside < .1).sum() >= n * .008: return g
        return None
    top = pick(line_groups(rowf, 0, int(H * .14)), rowf, H, True)
    bot = pick(line_groups(rowf, int(H * .86), H), rowf, H, False)
    lef = pick(line_groups(colf, 0, int(W * .14)), colf, W, True)
    rig = pick(line_groups(colf, int(W * .86), W), colf, W, False)
    ts = [g[1] - g[0] + 1 for g in (lef, rig) if g]
    t = int(np.clip(np.median(ts) if ts else 6, 3, W * .02)) + 1
    def clamp(g, outward_low):                        # a line merged with dark art keeps only its outer t pixels
        if not g: return None
        return [g[0], min(g[1], g[0] + t + 2)] if outward_low else [max(g[0], g[1] - t - 2), g[1]]
    return clamp(top, True), clamp(bot, False), clamp(lef, True), clamp(rig, False), t

def frame_and_letters(out, a0, has_title=True):
    H, W = a0.shape[:2]; ink = lum(a0) < 95; dk = lum(a0) < 125
    band = np.zeros((H, W), bool)
    top, bot, lef, rig, t = frame_lines(a0)
    x0 = lef[0] if lef else 0; x1 = rig[1] + 1 if rig else W
    y0 = top[0] if top else 0; y1 = bot[1] + 1 if bot else H
    def trace(line, outward):                        # follow a (slightly skewed) line: outermost dark run in a window
        idx = np.nonzero(line)[0]
        if not len(idx): return None
        start = idx[0] if outward else idx[-1]
        if outward:
            e = start
            while e + 1 < len(line) and line[e + 1] and e - start < t + 3: e += 1
            return start, e
        e = start
        while e - 1 >= 0 and line[e - 1] and start - e < t + 3: e -= 1
        return e, start
    win = 16
    for y in range(y0, y1):
        if lef:
            a_, b_ = max(0, lef[0] - win), min(W, lef[1] + 6); r = trace(dk[y, a_:b_], True)
            if r: band[y, a_ + r[0]:a_ + r[1] + 1] = True
        if rig:
            a_, b_ = max(0, rig[0] - 6), min(W, rig[1] + win); r = trace(dk[y, a_:b_], False)
            if r: band[y, a_ + r[0]:a_ + r[1] + 1] = True
    for x in range(x0, x1):
        if top:
            a_, b_ = max(0, top[0] - win), min(H, top[1] + 6); r = trace(dk[a_:b_, x], True)
            if r: band[a_ + r[0]:a_ + r[1] + 1, x] = True
        if bot:
            a_, b_ = max(0, bot[0] - 6), min(H, bot[1] + win); r = trace(dk[a_:b_, x], False)
            if r: band[a_ + r[0]:a_ + r[1] + 1, x] = True
    x0 = max(0, x0 - win); x1 = min(W, x1 + win)
    fb = find_banner(a0) if has_title else None; banner = None
    if fb:
        ys0 = max(fb[0], fb[1] - t + 1)
        band[ys0:fb[1] + 1, x0:x1] |= dk[ys0:fb[1] + 1, x0:x1]
        banner = (fb[2], fb[3])
    out[band] = TEAL
    letters = np.zeros((H, W), bool)
    if banner:
        letters[banner[0]:banner[1], int(W * .04):int(W * .96)] = True
    ty0 = int(H * .02); ty1 = int(H * .085); tx0, tx1 = int(W * .3), int(W * .7)
    if ink[ty0:ty1, tx0:tx1].mean() < .25: letters[ty0:ty1, tx0:tx1] = True
    near = band.copy()                               # pixels touching the frame line belong to the frame
    for d_ in range(1, 4):
        near |= np.roll(band, d_, 1) | np.roll(band, -d_, 1) | np.roll(band, d_, 0) | np.roll(band, -d_, 0)
    out[letters & dk & near & ~band] = TEAL
    lm = letters & ink & ~near
    out[lm] = LETTER
    return banner, t

def inpaint(out, mask, iters=60):
    """Fill masked pixels from their unmasked neighbours, working inward."""
    m = mask.copy(); o = out
    for _ in range(iters):
        if not m.any(): break
        acc = np.zeros_like(o); cnt = np.zeros(m.shape)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == dx == 0: continue
                ok = ~np.roll(np.roll(m, dy, 0), dx, 1)
                acc += np.roll(np.roll(o, dy, 0), dx, 1) * ok[..., None]; cnt += ok
        edge = m & (cnt > 2)
        o[edge] = acc[edge] / cnt[edge][:, None]; m &= ~edge

def glyph_alpha(a, box):
    """Alpha mask of the largest piece of ink in box (x0,y0,x1,y1) of image a."""
    x0, y0, x1, y1 = box; L = lum(a[y0:y1, x0:x1])
    paper = np.percentile(L, 90); inkv = np.percentile(L, 3)
    al = np.clip((paper - 12 - L) / (paper - 12 - inkv), 0, 1)
    core = al > .45; best = None; seen = np.zeros_like(core)
    for y, x in zip(*np.nonzero(core)):
        if seen[y, x]: continue
        comp = flood(core & ~seen, [(y, x)]); seen |= comp
        if best is None or comp.sum() > best.sum(): best = comp
    keep = best.copy()
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2): keep |= np.roll(np.roll(best, dy, 0), dx, 1)
    al = al * keep; ys, xs = np.nonzero(al > .3)
    return al[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def retitle(out, a0, spec, src_dir, interior):
    """Replace the suit word: erase the title, set prefix + new letters, centred."""
    (bx0, bx1), (ty0, ty1) = interior
    px0, px1 = spec['prefix']
    prefix = glyph_alpha_region(a0, (px0, ty0, px1, ty1))
    core = prefix > .45; keep = np.zeros_like(core); seen = np.zeros_like(core)
    for y, x in zip(*np.nonzero(core)):                # letters only: drop pieces that touch the box sides (frame line)
        if seen[y, x]: continue
        comp = flood(core & ~seen, [(y, x)]); seen |= comp
        xs_ = np.nonzero(comp.any(0))[0]
        ys_ = np.nonzero(comp.any(1))[0]
        sliver = (xs_.max() - xs_.min() < 7) and (ys_.max() - ys_.min() > .8 * core.shape[0])
        if comp.sum() > 20 and not sliver: keep |= comp
    grow = keep.copy()
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2): grow |= np.roll(np.roll(keep, dy, 0), dx, 1)
    prefix = prefix * grow
    glyphs = []
    for src, *box in spec['glyphs']:
        a = a0 if src is None else np.asarray(Image.open(f'{src_dir}/{src}.jpg').convert('RGB')).astype(float)
        glyphs.append(glyph_alpha(a, box))
    dsrc = spec.get('dot_src'); da = a0 if not dsrc else np.asarray(Image.open(f'{src_dir}/{dsrc}.jpg').convert('RGB')).astype(float)
    dot = glyph_alpha(da, spec['dot'])
    cap = spec['cap']                                   # cap height of this card's lettering
    scaled = []
    for g in glyphs:
        k = cap / g.shape[0]
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((max(1, round(g.shape[1] * k)), cap), Image.LANCZOS)
        scaled.append(np.asarray(im) / 255.)
    gap, word = spec.get('gap', 7), spec.get('word', 22)
    total = prefix.shape[1] + word + sum(g.shape[1] for g in scaled) + gap * (len(scaled) - 1) + 3 + dot.shape[1]
    # erase the old lettering, filling with real paper texture from the card's bottom margin
    H, W = out.shape[:2]
    _t, _b, lef, rig, _th = frame_lines(a0)
    ex0 = (lef[1] + 4) if lef else bx0; ex1 = (rig[0] - 4) if rig else bx1
    f = (lum(a0[ty0 + 1:ty1 - 2]) < 175).mean(0)      # the frame line where it crosses the title (it can drift):
    for x in range(int(W * .14), -1, -1):               # the first solid column met going outward from the title
        if f[x] >= .95: ex0 = x + 1; break
    for x in range(int(W * .86), W):
        if f[x] >= .95: ex1 = x; break
    region = np.zeros((H, W), bool); region[ty0 + 1:ty1 - 2, ex0:ex1] = True
    region &= ~(out == TEAL).all(-1)                    # never erase the frame already drawn
    erase = region & (lum(a0) < 175); grown = erase.copy()
    for dy in (-2, -1, 0, 1, 2):
        for dx in (-2, -1, 0, 1, 2): grown |= np.roll(np.roll(erase, dy, 0), dx, 1)
    erase = grown & region
    local = np.median(out[region & ~erase], axis=0)
    rng = np.random.default_rng(1)
    ys, xs = np.nonzero(erase)
    out[ys, xs] = local + rng.normal(0, 5, (len(ys), 1))      # plain paper with a fine grain
    base = spec['baseline']; x = int((bx0 + bx1) / 2 - total / 2)
    def put(al, x, ytop):
        h, w = al.shape; sl = out[ytop:ytop + h, x:x + w]
        sl[:] = sl * (1 - al[..., None]) + np.array(LETTER) * al[..., None]
    put(prefix, x, ty0 + spec['prefix_dy']); x += prefix.shape[1] + word
    for g in scaled: put(g, x, base - g.shape[0]); x += g.shape[1] + gap
    x += 3 - gap; put(dot, x, base - dot.shape[0])

def glyph_alpha_region(a, box):
    x0, y0, x1, y1 = box; L = lum(a[y0:y1, x0:x1])
    paper = np.percentile(L, 90); inkv = np.percentile(L, 3)
    return np.clip((paper - 12 - L) / (paper - 12 - inkv), 0, 1)

def titled(card):
    i = int(card[:2]); return i < 22 or (i - 22) % 14 in (0, 10, 11, 12, 13)

def process(card, marks, src_dir, dst):
    a0 = np.asarray(Image.open(f'{src_dir}/{card}.jpg').convert('RGB')).astype(float)
    H, W = a0.shape[:2]; out = palette(a0); ink = lum(a0) < 95
    h, s, v = hsv_of(a0)
    yellowish = (h > 28) & (h < 70) & (s > 100) & (v > 120)   # paper is s~65, gilt objects s~150+
    from PIL import ImageFilter
    def blur(x, r=4):
        c = np.cumsum(np.cumsum(np.pad(x, ((r + 1, r), (r + 1, r)), mode='edge'), 0), 1)
        k = 2 * r + 1
        return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
    wgt = (lum(a0) >= 115).astype(float); bw = blur(wgt) + 1e-6
    sm = np.dstack([blur(a0[..., c] * wgt) / bw for c in range(3)])
    hs = hsv_of(np.clip(sm, 0, 255))[0]
    warm = ((h < 25) | (h > 330) | ((h >= 25) & (h < 70))) & (s > 75)
    for ob in marks.get('objects', []):
        reg = shape_mask((W, H), ob['shapes'])
        if ob['filter'] == 'yellow': m = reg & yellowish
        elif ob['filter'] == 'nonink': m = reg & ~ink
        elif ob['filter'] == 'cool': m = reg & ~ink & ~warm
        elif ob['filter'] == 'sword':
            # areas closed in by the sword's own outlines, inside the marked band
            dk = lum(a0) < 115; cl = dk.copy()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1): cl |= np.roll(np.roll(dk, dy, 0), dx, 1)
            mode = ob.get('color', 'nowarm')
            if mode == 'blue': colr = (((hs > 140) & (hs < 250)) | (s < 40))
            elif mode == 'any': colr = np.ones_like(reg)
            else: colr = ~(((hs < 70) | (hs > 320)) & (s > 70))
            allowed = reg & ~cl & colr
            edge = reg & ~np.roll(reg, 1, 0) | reg & ~np.roll(reg, -1, 0) | reg & ~np.roll(reg, 1, 1) | reg & ~np.roll(reg, -1, 1)
            ed = edge.copy()
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2): ed |= np.roll(np.roll(edge, dy, 0), dx, 1)
            seedm = np.zeros_like(reg)
            for sh in ob['shapes']:
                if sh[0] == 'line':                     # only the long sides of a band: never its ends
                    (x0_, y0_), (x1_, y1_), hw = sh[1], sh[2], sh[3]
                    L_ = max(1.0, math.hypot(x1_ - x0_, y1_ - y0_)); nx_, ny_ = -(y1_ - y0_) / L_, (x1_ - x0_) / L_
                    for tt in np.linspace(0, 1, int(L_) + 1):
                        for sg in (-1, 1):
                            px = int(round(x0_ + tt * (x1_ - x0_) + sg * nx_ * (hw - 1))); py = int(round(y0_ + tt * (y1_ - y0_) + sg * ny_ * (hw - 1)))
                            if 0 <= py < H and 0 <= px < W: seedm[py, px] = True
                else:
                    seedm |= shape_mask((W, H), [sh]) & edge
            outside = flood(allowed, list(zip(*np.nonzero(seedm & ed & allowed))))
            m = allowed & ~outside
            grow = m.copy()
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2): grow |= np.roll(np.roll(m, dy, 0), dx, 1)
            m = grow & reg & ~outside & (lum(a0) >= 95) & colr
            if ob.get('direct'):                         # blue-grey steel on a background of another colour
                m |= reg & (lum(a0) >= 95) & (hs > 140) & (hs < 250) & (s > ob.get('dsat', 30))
                if ob.get('grey'): m |= reg & (lum(a0) >= 120) & (s < ob['grey'])
        elif ob['filter'] == 'gilt':                    # every gilt pixel in the shapes (open ornaments on a non-gilt background)
            m = reg & yellowish & (hs > ob.get('hue', 42))
            if ob.get('dark'):                          # shaded, olive-gold parts of the object too
                m |= reg & (h > 30) & (h < 75) & (s > 70) & (v > ob.get("dark_v", 95))
        elif ob['filter'] == 'cup':
            # areas enclosed by the drawn outline inside the box, that are gilt yellow (smoothed hue keeps hands out)
            x0, y0, x1, y1 = ob['box']; full_ink = lum(a0) < 115
            ft, fb_, fl, fr, _t = frame_lines(a0)
            for g in (ft, fb_):
                if g: full_ink[max(0, g[0] - 4):g[1] + 5, :] = False
            for g in (fl, fr):
                if g: full_ink[:, max(0, g[0] - 4):g[1] + 5] = False
            sub_ink = full_ink[y0:y1, x0:x1]
            closed = sub_ink.copy()
            for dy in (-2, -1, 0, 1, 2):
                for dx in (-2, -1, 0, 1, 2):
                    if dy * dy + dx * dx <= 5: closed |= np.roll(np.roll(sub_ink, dy, 0), dx, 1)
            free = ~closed; h_, w_ = free.shape
            border = [(0, x) for x in range(w_)] + [(h_ - 1, x) for x in range(w_)] + [(y, 0) for y in range(h_)] + [(y, w_ - 1) for y in range(h_)]
            outside = flood(free, border)
            inside = free & ~outside
            if ob.get('not_inside'):                     # enclosed background pockets to leave alone
                pk = flood(inside, [(y - y0, x - x0) for x, y in ob['not_inside']]); inside &= ~pk
            grown = inside.copy()
            for dy in (-3, -2, -1, 0, 1, 2, 3):
                for dx in (-3, -2, -1, 0, 1, 2, 3): grown |= np.roll(np.roll(inside, dy, 0), dx, 1)
            m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = grown & ~outside
            m &= yellowish & (hs > ob.get('hue', 42)) & reg
            if ob.get('grow'):
                ok = yellowish & (hs > ob.get('hue', 42)) & reg & ~ink
                m = flood(ok, list(zip(*np.nonzero(m & ok)))) | m
        elif ob['filter'] == 'flood':
            allowed = reg & ~ink
            seeds = [(int(y), int(x)) for (x, y) in ob['seeds']]
            m = flood(allowed, seeds)
        if ob.get('exclude'): m = m & ~shape_mask((W, H), ob['exclude'])   # e.g. a hand holding the object
        metal(out, a0, m, ob['metal'])
    for cn in marks.get('coins', []):
        cx, cy, rx, ry = cn['face']
        before = out.copy()
        rk = cn.get('ring', 1.12)
        reg = shape_mask((W, H), [('ellipse', [cx, cy, rx * rk, ry * rk + cn.get('thick', 0)])])
        metal(out, a0, reg & yellowish, 'silver')
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)); face = coin_face(rx, ry)
        img.paste(face, (int(cx - face.size[0] / 2), int(cy - face.size[1] / 2)), face); out[:] = np.asarray(img).astype(float)
        # whatever lies on top of the coin (hands, feet, tools) stays: inside the face, any pixel
        # that is neither coin-yellow nor ink is foreground, plus the ink lines touching it
        disc = shape_mask((W, H), [('ellipse', [cx, cy, rx, ry])])
        coin_y = (hs > 38) & (h > 30) & (h < 75) & (s > cn.get('yel_s', 75))
        fg = disc & ~coin_y & ~ink
        fg = flood(fg, list(zip(*np.nonzero(fg & ~shape_mask((W, H), [('ellipse', [cx, cy, rx * .97, ry * .97])])))))   # reaching in from outside
        near = fg.copy()
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2): near |= np.roll(np.roll(fg, dy, 0), dx, 1)
        keep = fg | (disc & ink & near)
        if cn.get('keep_ink'): keep |= shape_mask((W, H), cn['keep_ink']) & (lum(a0) < 120)   # tools drawn in ink on the coin
        out[keep] = before[keep]
    if marks.get('carve'): carve(out, a0, marks['carve'])
    banner, t = frame_and_letters(out, a0, titled(card))
    if marks.get('retitle') and banner:
        sp = marks['retitle']; retitle(out, a0, sp, src_dir, ((sp['interior'][0], sp['interior'][1]), (banner[0] + 3, banner[1] - 3)))
    Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8)).save(dst, quality=92)
    return banner

if __name__ == '__main__':
    marks = json.load(open(sys.argv[1])); src, dstdir = sys.argv[2], sys.argv[3]
    for card in sys.argv[4:]:
        b = process(card, marks.get(card, {}), src, f'{dstdir}/{card}.jpg'); print(card, 'banner rows', b)
