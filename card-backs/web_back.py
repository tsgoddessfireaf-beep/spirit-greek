"""Make the app's card-back image from a finished, symmetric card back.

    python3 -I web_back.py <card-back.png> <out.jpg> [--trim PX]

Trims the card's outer edge, fills its rounded corners with paper, widens the paper on both sides (mirrored from
the paper next to it) to the app's card shape, shrinks it to 704 x 1200 and
saves a JPEG. Both sizes are multiples of 16, so JPEG compression treats the
two halves alike; full colour detail (no chroma subsampling) keeps them alike. Prints the largest difference from its own half turn.
"""
import sys
import numpy as np
from PIL import Image

W_OUT, H_OUT = 704, 1200

def rot(x): return x[::-1, ::-1]

src, out = sys.argv[1], sys.argv[2]
trim = int(sys.argv[sys.argv.index('--trim') + 1]) if '--trim' in sys.argv else 10
a = np.asarray(Image.open(src).convert('RGB'))
a = a[:, trim:a.shape[1] - trim]                      # drop the card's outer edge
a = a.copy(); h, w = a.shape[:2]
# The scan's rounded corners show the white page behind the card. Cover each
# corner with plain paper from the side margin (outside the frame); the app
# rounds the corners itself.
t, side, reach = 50, 48, 130             # top margin, side margin, length of each strip
top = a[:t, w // 3:w // 3 + reach]                   # plain paper above the frame
left = a[h // 3:h // 3 + reach, :side]               # plain paper beside the frame
for flip in (lambda x: x, lambda x: x[::-1, ::-1]):  # top-left/bottom-right, then the others
    b = flip(a)
    b[:t, :reach] = top; b[:reach, :side] = left
    b[:t, w - reach:] = top[:, ::-1]; b[:reach, w - side:] = left[:, ::-1]
pad = (round(h * W_OUT / H_OUT) - w) // 2
if pad > 0:                                           # widen with mirrored paper
    a = np.pad(a, ((0, 0), (pad, pad), (0, 0)), mode='reflect')
im = Image.fromarray(a).resize((W_OUT, H_OUT), Image.LANCZOS)
b = np.asarray(im).copy()
b[H_OUT // 2:] = rot(b[:H_OUT // 2])                  # keep it exactly symmetric
Image.fromarray(b).save(out, quality=86, subsampling=0, optimize=True)
c = np.asarray(Image.open(out).convert('RGB')).astype(int)
print(f"{out}: {W_OUT}x{H_OUT}, padded {pad}px each side; "
      f"largest difference from its half turn after JPEG: {np.abs(c - rot(c)).max()}")
