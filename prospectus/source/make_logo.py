#!/usr/bin/env python3
"""ECNUchat logo v2: navy tile, white chat bubble, ECNU-red keyhole + lockup."""
from PIL import Image, ImageDraw, ImageFont

NAVY = (10, 37, 64, 255)
RED = (166, 30, 54, 255)
WHITE = (255, 255, 255, 255)
S = 4  # supersample factor

def draw_mark(px):
    """Draw the mark at px*S then downscale to px."""
    u = px * S
    img = Image.new("RGBA", (u, u), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    def k(v): return int(v * u / 1000)  # coords in per-mille of tile
    d.rounded_rectangle([0, 0, u, u], radius=k(210), fill=NAVY)
    d.rounded_rectangle([k(26), k(26), k(974), k(974)], radius=k(188), outline=(255, 255, 255, 46), width=k(6))
    # chat bubble
    d.rounded_rectangle([k(215), k(215), k(785), k(660)], radius=k(120), fill=WHITE)
    # tail: top edge buried inside the bubble so the joint is invisible
    d.polygon([(k(335), k(600)), (k(525), k(600)), (k(350), k(815))], fill=WHITE)
    # keyhole
    cx, cy = k(500), k(395)
    d.ellipse([cx - k(78), cy - k(78), cx + k(78), cy + k(78)], fill=RED)
    d.polygon([(cx - k(52), cy + k(45)), (cx + k(52), cy + k(45)), (cx + k(78), cy + k(185)), (cx - k(78), cy + k(185))], fill=RED)
    return img.resize((px, px), Image.LANCZOS)

mark = draw_mark(1000)
mark.save("/home/hatch/workspace/ecnuchat-prospectus/logo-mark.png")

# ---- horizontal lockup, final size 2800x720 ----
FW, FH = 2800, 720
W, H = FW * S, FH * S
lock = Image.new("RGBA", (W, H), (0, 0, 0, 0))
lock.alpha_composite(draw_mark(640 * S // S * 1) if False else Image.new("RGBA", (1, 1)), (0, 0))  # no-op guard
m = draw_mark(640)
# draw_mark returns 640px image; upscale path: redraw at full res
m_big = draw_mark(640 * S)
lock.alpha_composite(m_big, (40 * S, 40 * S))
d = ImageDraw.Draw(lock)
bold = "/home/hatch/workspace/ruanzhu/fonts/NotoSansSC-Bold.ttf"
serif = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
tx = 740 * S
# wordmark: fit width ~1850 final px
size = 200
while size > 40:
    f = ImageFont.truetype(bold, size * S)
    w = d.textlength("ECNUCHAT", font=f)
    if w <= 1850 * S: break
    size -= 5
d.text((tx, 118 * S), "ECNUCHAT", font=f, fill=NAVY)
# tagline letterspaced, fit same width
tag = "END-TO-END ENCRYPTED MESSAGING"
tsize = 54
while tsize > 20:
    f2 = ImageFont.truetype(serif, tsize * S)
    w2 = sum(d.textlength(ch, font=f2) for ch in tag) + (len(tag) - 1) * tsize * S * 0.42
    if w2 <= 1850 * S: break
    tsize -= 2
x = tx
tracking = tsize * S * 0.42
for ch in tag:
    d.text((x, 400 * S), ch, font=f2, fill=RED)
    x += d.textlength(ch, font=f2) + tracking
lock = lock.resize((FW, FH), Image.LANCZOS)
lock.save("/home/hatch/workspace/ecnuchat-prospectus/logo-full.png")
print("logo v2 done")
