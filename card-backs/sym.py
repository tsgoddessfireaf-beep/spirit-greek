import sys
from PIL import Image, ImageChops, ImageOps
import numpy as np
out = sys.argv[1]
for i, p in enumerate(sys.argv[2:], 1):
    im = ImageOps.grayscale(Image.open(p))
    a = np.asarray(im, dtype=np.float32) / 255
    ink = a < 0.5
    rot = np.rot90(ink, 2)
    mir = ink[:, ::-1]
    def score(other):
        both = (ink & other).sum(); either = (ink | other).sum()
        return both / either
    print(f"Design {i}: size {im.size}, ink {ink.mean():.1%}, "
          f"180-rotation match {score(rot):.1%}, left-right mirror match {score(mir):.1%}")
    # where top and rotated-bottom disagree
    diff = (ink ^ rot)
    h = diff.shape[0]
    print(f"   mismatch by band (top/middle/bottom thirds): "
          + ", ".join(f"{diff[k*h//3:(k+1)*h//3].mean():.1%}" for k in range(3)))
    vis = np.full(ink.shape + (3,), 255, np.uint8)
    vis[ink & rot] = (40, 40, 40)
    vis[ink & ~rot] = (220, 40, 40)   # only in original
    vis[~ink & rot] = (40, 90, 220)   # only in rotated
    Image.fromarray(vis).save(f"{out}/design{i}_rotation_diff.png")
