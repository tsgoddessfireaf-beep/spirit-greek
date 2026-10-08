"""Softer skulls for card back #3 (cream, teal, gold).

Option A, "smoothed": the skull's outline redrawn along a smoothed copy of its shape;
the thorns and cracks removed; eye sockets, nose and teeth softened.
Option B, "flowing": option A plus tapered strokes in the style of the card's ribbons.

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

def paint(a, ink, where):
    """Inside `where` (grown by 2 px to catch soft edge pixels): cream paper with teal ink."""
    cream, tcol = card_colours(a)
    w = soft(nd.binary_dilation(where, iterations=2), 1.0)[..., None]
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
