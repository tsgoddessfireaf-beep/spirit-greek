import sys
from PIL import Image, ImageDraw, ImageOps
import numpy as np
OUT = sys.argv[1]; B = 41
names = ['A_vesica-piscis-inked', 'B2_new-rose', 'C2_aeonic-arts']
labels = ['A. Vesica Piscis (inked)', 'B. New rose', 'C. Aeonic Arts']
trims, zooms = [], []
for n in names:
    im = Image.open(f'{OUT}/design1_{n}_print-with-bleed.png').convert('RGB')
    t = im.crop((B, B, im.width - B, im.height - B))
    g = np.asarray(ImageOps.grayscale(t)) < 128
    cy, cx = g.shape[0] // 2, g.shape[1] // 2
    c = g[cy - 130:cy + 130, cx - 130:cx + 130]
    full = (g & g[::-1, ::-1]).sum() / (g | g[::-1, ::-1]).sum()
    ctr = (c & c[::-1, ::-1]).sum() / (c | c[::-1, ::-1]).sum()
    print(f'{n}: whole card {full:.1%} | centre area {ctr:.1%}')
    trims.append(t.resize((t.width // 2, t.height // 2), Image.LANCZOS))
    zooms.append(t.crop((cx - 150, cy - 150, cx + 150, cy + 150)).resize((479, 479), Image.LANCZOS))
pad, lab = 24, 40
sheet = Image.new('RGB', (3 * trims[0].width + 4 * pad, lab + trims[0].height + 2 * pad + zooms[0].height + pad), (225, 220, 205))
d = ImageDraw.Draw(sheet)
for i, (t, z) in enumerate(zip(trims, zooms)):
    x = pad + i * (t.width + pad)
    d.text((x, 12), labels[i], fill=(20, 20, 20))
    sheet.paste(t, (x, lab)); sheet.paste(z, (x, lab + t.height + pad))
sheet.save(f'{OUT}/compare_round3.png')
