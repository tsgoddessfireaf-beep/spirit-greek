"""Softer skulls for card back #3 (cream, teal, gold).

Option A, "smoothed": the skull's outline redrawn along a smoothed copy of its shape;
the thorns and cracks removed; eye sockets, nose and teeth softened.
Option B, "flowing": option A plus tapered strokes in the style of the card's ribbons.
Option C, "logo": the skull redrawn with one smooth outline, like the Aeonic Arts logo.

Only the top skull is changed. The bottom half of the card is then rebuilt as the
top half turned over, so the card stays exactly the same upside down.

    python3 -I skull.py skulls <symmetric-card.png> <outdir>
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage as nd

def rot(x): return x[::-1, ::-1]

# Card #3, after symmetrize.py --dx 0 (958 x 1642 px). The top skull sits inside this ellipse.
SKULL_C, SKULL_R = (478.5, 556.0), (185.0, 270.0)        # centre (x, y), radii (x, y)
MID_X = 478.5                                             # the card's vertical centre line
OUTLINE_W = 7.5                                           # the skull's outline width, px

def ink_masks(a):
    g = a.mean(axis=2)
    return (g < 120) & (a[..., 2] > a[..., 0] + 12)      # teal ink

def card_colours(a):
    flat = a.reshape(-1, 3)
    g = flat.mean(axis=1)
    cream = np.median(flat[g > 215], axis=0)
    teal = np.median(flat[(g < 70) & (flat[:, 2] > flat[:, 0])], axis=0)
    return cream, teal

def soft(m, s):
    return nd.gaussian_filter(m.astype(np.float32), s)

def silhouette(teal):
    """The top skull's filled outline shape."""
    H, W = teal.shape
    yy, xx = np.mgrid[0:H, 0:W]
    ell = ((xx - SKULL_C[0]) / SKULL_R[0]) ** 2 + ((yy - SKULL_C[1]) / SKULL_R[1]) ** 2 <= 1
    S = nd.binary_fill_holes(teal & ell)
    lab, _ = nd.label(S)
    return lab == lab[int(SKULL_C[1]) + 40, int(SKULL_C[0])]

def smoothed(a, sigma=7.0):
    """Option A. The outline is redrawn along a smoothed copy of the skull's shape; inside,
    only the central features stay (eye sockets, nose, the small diamond, the tooth row),
    softened. The thorns and cracks along the cheeks and cranium are removed.
    Returns (image, ink, skull shape)."""
    teal = ink_masks(a)
    S = silhouette(teal)
    Ss = soft(S, sigma) > 0.5
    depth = nd.distance_transform_edt(Ss)
    outline = np.clip(OUTLINE_W - depth + 0.5, 0, 1) * (depth > 0)
    interior = teal & nd.binary_erosion(S, iterations=10)
    lab, n = nd.label(interior)
    idx = range(1, n + 1)
    area = nd.sum(interior, lab, idx)
    centre = nd.center_of_mass(interior, lab, idx)
    keep = np.zeros_like(interior)
    for i in range(n):
        if area[i] > 200 and abs(centre[i][1] - MID_X) < 40:
            keep |= lab == i + 1
    kept = np.clip((soft(keep, 1.4) - 0.5) * 3 + 0.5, 0, 1)
    ink = np.maximum(outline, kept)
    return paint(a, ink, Ss | S), ink, Ss

def paint(a, ink, where, grow=4):
    """Inside `where` (grown by `grow` px to catch soft edge pixels): cream paper with teal ink."""
    cream, tcol = card_colours(a)
    w = soft(nd.binary_dilation(where, iterations=grow), 1.0)[..., None]
    tgt = ink[..., None] * tcol + (1 - ink[..., None]) * cream
    return a * (1 - w) + tgt * w

# ---------- Option B: flowing strokes in the ribbon style ----------
SS = 4                                                    # supersampling for strokes

def spline(pts, n=40):
    p = np.asarray(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2])
    return np.array(out)

def swoosh(draw, pts, width, ends=(1, 1)):
    """A tapered stroke like the card's ribbons: full width in the middle, pointed ends.
    ends: 1 = pointed, 0 = blunt, at the start and end."""
    c = spline(pts)
    d = np.gradient(c, axis=0)
    nrm = np.c_[-d[:, 1], d[:, 0]] / (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9)
    t = np.linspace(0, 1, len(c))
    prof = np.ones_like(t)
    if ends[0]: prof = np.minimum(prof, np.sin(np.clip(t, 0, 0.5) * np.pi) ** 0.7)
    if ends[1]: prof = np.minimum(prof, np.sin(np.clip(1 - t, 0, 0.5) * np.pi) ** 0.7)
    half = (width / 2 * prof)[:, None] * nrm
    poly = np.vstack([c + half, (c - half)[::-1]]) * SS
    draw.polygon([tuple(q) for q in poly], fill=255)

def mirrored(pts):
    return [(2 * MID_X - x, y) for x, y in pts]

# Strokes for the top skull (card px). Each is drawn on the left and mirrored to the right.
FLOW = [
    # long crescent inside each side of the cranium, where the thorns were
    ([(347, 585), (338, 640), (346, 698), (370, 746), (404, 778)], 7.0, (1, 1)),
    # a second, shorter crescent inside it
    ([(372, 640), (370, 680), (384, 716), (404, 738)], 4.0, (1, 1)),
    # cheekbone sweep from the outline over the eye socket toward the nose
    ([(328, 493), (356, 478), (392, 476), (424, 488), (446, 506)], 6.0, (0, 1)),
]

def flowing(a, sigma=7.0):
    """Option B: option A plus tapered ribbon-style strokes in place of the thorns."""
    out, ink, Ss = smoothed(a, sigma)
    H, W = ink.shape
    im = Image.new('L', (W * SS, H * SS), 0)
    from PIL import ImageDraw
    dr = ImageDraw.Draw(im)
    for pts, w, ends in FLOW:
        swoosh(dr, pts, w, ends)
        swoosh(dr, mirrored(pts), w, ends)
    strokes = np.asarray(im.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255
    strokes *= Ss                                         # keep strokes inside the skull
    ink2 = np.maximum(ink, strokes)
    return paint(a, ink2, Ss | silhouette(ink_masks(a)))

# ---------- Option C: one smooth outline, like the Aeonic Arts logo skull ----------
# Drawn upright on the bottom skull (card px); the top skull is its turned copy.
BOT_C = (2 * MID_X - SKULL_C[0], 1641 - SKULL_C[1])      # the bottom skull's centre

def closed_spline(pts, n=30):
    p = np.asarray(pts, float)
    p = np.vstack([p[-1], p, p[0], p[1]])
    return _closed(p, n)

def _closed(p, n):
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)

def both_sides(right):
    """Right-half points from top centre to bottom centre -> the whole closed shape."""
    left = [(2 * MID_X - x, y) for x, y in right[-2:0:-1]]
    return right + left

LOGO = {
    # outer outline, right half, top centre -> chin
    'outline': [(MID_X, 827), (540, 832), (595, 852), (633, 893), (652, 950), (655, 1010),
                (649, 1060), (641, 1098), (643, 1126), (635, 1151), (615, 1171), (605, 1214),
                (593, 1262), (573, 1297), (541, 1317), (501, 1324), (MID_X, 1325)],
    'eye': [(364, 1078), (398, 1062), (440, 1064), (460, 1084), (458, 1118), (436, 1138),
            (396, 1141), (368, 1126), (358, 1100)],
    # nose like the logo's: a heart pointing up, two rounded lobes at the bottom
    'nose': [(MID_X, 1116), (488, 1136), (500, 1160), (495, 1176), (484, 1178), (MID_X, 1170),
             (473, 1178), (462, 1176), (457, 1160), (469, 1136)],
    'cheek': [(633, 1150), (600, 1170), (566, 1194), (547, 1210)],
    'temple': [(626, 948), (640, 1000), (636, 1052), (624, 1088)],
    'mouth': (404, 1200, 553, 1266),                     # x0, y0, x1, y1 of the tooth rows
    'third_eye': (MID_X, 1000),
}

def logo_skull(a):
    """Option C: the old bottom skull is cleared and redrawn with one smooth outline,
    smooth filled eye sockets and nose, a neat tooth row and a third eye, like the
    Aeonic Arts logo. Returns the card with only the bottom skull changed."""
    from PIL import ImageDraw
    H, W = a.shape[:2]
    old = rot(silhouette(ink_masks(rot(a))))             # the bottom skull's old shape
    big = Image.new('L', (W * SS, H * SS), 0)
    fill = Image.new('L', (W * SS, H * SS), 0)
    d, f = ImageDraw.Draw(big), ImageDraw.Draw(fill)
    pts = lambda c: [(x * SS, y * SS) for x, y in c]
    outline = closed_spline(both_sides(LOGO['outline']))
    f.polygon(pts(outline), fill=255)
    def ring(shape, width):
        # an outlined shape like the logo's: the shape, minus a copy pulled in by `width` px
        c = closed_spline(shape)
        cx, cy = c.mean(axis=0)
        rx, ry = np.ptp(c[:, 0]) / 2, np.ptp(c[:, 1]) / 2
        inner = [(cx + (x - cx) * (1 - width / rx), cy + (y - cy) * (1 - width / ry)) for x, y in c]
        d.polygon(pts(c), fill=255)
        d.polygon(pts(inner), fill=0)
    for side in (lambda q: q, mirrored):
        ring(side(LOGO['eye']), 8)
        swoosh(d, side(LOGO['cheek']), 6.0, (0, 1))
        swoosh(d, side(LOGO['temple']), 5.0, (1, 1))
    ring(LOGO['nose'], 6)
    # teeth: two rows along a gentle smile, each tooth a rounded outline
    x0, y0, x1, y1 = LOGO['mouth']
    n = 10
    tw = (x1 - x0) / n
    for row, (ya, yb) in enumerate(((y0, (y0 + y1) / 2), ((y0 + y1) / 2, y1))):
        for k in range(n):
            u = (k + 0.5) / n - 0.5
            sag = 6 * (1 - (2 * u) ** 2)                 # the row curves down in the middle
            shrink = 0.10 * (2 * u) ** 2 * (yb - ya)     # outer teeth a little shorter
            tx0, tx1 = x0 + k * tw + 1, x0 + (k + 1) * tw - 1
            ty0 = ya + sag + (shrink if row == 0 else 0)
            ty1 = yb + sag - (shrink if row == 1 else 0)
            d.rounded_rectangle([tx0 * SS, ty0 * SS, tx1 * SS, ty1 * SS], radius=5 * SS, outline=255, width=3 * SS)
    # third eye: almond outline with a pupil
    cx, cy = LOGO['third_eye']
    almond = [(cx - 32, cy), (cx - 14, cy - 11), (cx, cy - 13), (cx + 14, cy - 11), (cx + 32, cy),
              (cx + 14, cy + 11), (cx, cy + 13), (cx - 14, cy + 11)]
    inner = [(cx + (x - cx) * 0.80, cy + (y - cy) * 0.62) for x, y in almond]
    d.polygon(pts(closed_spline(almond)), fill=255)
    d.polygon(pts(closed_spline(inner)), fill=0)
    r = 7
    d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=255)
    ink = np.asarray(big.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255
    shape = np.clip(np.asarray(fill.resize((W, H), Image.LANCZOS), dtype=np.float32) / 255, 0, 1)
    new = shape > 0.5
    # the outline: a band of even width just inside the smooth shape, soft at both edges
    depth = nd.distance_transform_edt(new)
    band = shape * np.clip(OUTLINE_W - depth + 0.5, 0, 1)
    # Where the old skull stuck out past the new outline (its knobbly cheeks), carry the
    # background in from just outside, so lines that ran behind the old skull now reach
    # the new outline instead of stopping short.
    covered = nd.binary_dilation(old, iterations=4)
    filled = extend_lines(a, covered, new)
    return paint(filled, np.maximum(ink, band), new, grow=1)

def extend_lines(a, covered, new, reach=60):
    """Clear the part of `covered` outside `new` to cream, then push every background
    line that ended at `covered` straight on along its own direction until it reaches
    `new`. Keeps each line's colour and thickness."""
    cream, _ = card_colours(a)
    H, W = covered.shape
    gap = covered & ~new
    out = a.copy()
    out[gap] = cream
    ink = np.abs(a - cream).max(axis=2) > 60               # any line: teal or gold
    near = nd.binary_dilation(covered, iterations=14) & ~covered
    touch = nd.binary_dilation(covered, iterations=2)
    lab, n = nd.label(ink & near)
    for i in range(1, n + 1):
        P = np.argwhere(lab == i)
        if len(P) < 12 or not touch[P[:, 0], P[:, 1]].any():
            continue
        c = P.mean(axis=0)
        u, sv, vt = np.linalg.svd(P - c, full_matrices=False)
        d = vt[0]
        contact = P[touch[P[:, 0], P[:, 1]]].mean(axis=0)
        if np.dot(contact - c, d) < 0:
            d = -d                                          # point toward the skull
        colour = np.median(a[P[:, 0], P[:, 1]], axis=0)
        end = P[np.dot(P - c, d) > np.dot(contact - c, d) - 8]   # the last few px of the line
        for k in range(1, reach):
            q = np.rint(end + k * d).astype(int)
            ok = (q[:, 0] >= 0) & (q[:, 0] < H) & (q[:, 1] >= 0) & (q[:, 1] < W)
            q = q[ok]
            g = gap[q[:, 0], q[:, 1]]
            if not g.any():
                if new[q[:, 0], q[:, 1]].all():
                    break
                continue
            out[q[g, 0], q[g, 1]] = colour
    # soften the new pixels' edges a little
    soft_out = nd.gaussian_filter(out, (0.6, 0.6, 0))
    return np.where(gap[..., None], soft_out, out)

def symmetric_from_bottom(a):
    """Rows of the top half = the bottom half turned over (exact)."""
    H = a.shape[0]
    out = a.copy()
    out[:H // 2] = rot(a)[:H // 2]
    return out

def symmetric_from_top(a):
    """Rows of the bottom half = the top half turned over (exact)."""
    H = a.shape[0]
    out = a.copy()
    out[H // 2:] = rot(a)[H // 2:]
    return out

def save(a, path):
    Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8)).save(path)

def check(path):
    o = np.asarray(Image.open(path).convert('RGB')).astype(np.int16)
    return int(np.abs(o - rot(o)).max())

if __name__ == '__main__':
    cmd, src, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
    if cmd == 'skulls':
        for tag, fn in (('A-smoothed', smoothed), ('B-flowing', flowing)):
            img = fn(a)
            img = img[0] if isinstance(img, tuple) else img
            p = f'{outdir}/card3_skull-{tag}.png'
            save(symmetric_from_top(img), p)
            print(f'{tag}: largest difference from its upside-down copy: {check(p)} (0 = exact)')
        p = f'{outdir}/card3_skull-C-logo.png'
        save(symmetric_from_bottom(logo_skull(a)), p)
        print(f'C-logo: largest difference from its upside-down copy: {check(p)} (0 = exact)')
