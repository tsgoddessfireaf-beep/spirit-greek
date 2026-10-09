# Copyright notice for a card back: upright in the top frame, upside down in the bottom frame.
# Usage: python3 -I notice.py card-back.png out.png "© 2026 DOLORES PUCKETT · AEONIC ARTS"
import sys
from PIL import Image, ImageDraw, ImageFont
src, out, text = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(src).convert('RGB'); W, H = im.size
band_top, band_bot = 24, 88            # teal frame along the top edge
cream = im.getpixel((5, 5))            # the card's own cream
font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', 24)
spacing = 3                            # letter spacing, px
widths = [font.getlength(c) for c in text]
total = sum(widths) + spacing * (len(text) - 1)
d = ImageDraw.Draw(im)
x = (W - total) / 2; y = (band_top + band_bot) / 2
for c, w in zip(text, widths):
    d.text((x, y), c, font=font, fill=cream, anchor='lm'); x += w + spacing
# Exact half-turn symmetry: the bottom half is the top half turned upside down.
top = im.crop((0, 0, W, H // 2))
im.paste(top.rotate(180), (0, H - H // 2))
im.save(out)
print(f"text width {total:.0f}px of {W}px")
