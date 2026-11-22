#!/usr/bin/env python3
"""ECNUchat official logo (design C, selected 2026-11-22):
black squircle, white chat-bubble glyph, keyhole punched out in black."""
from PIL import Image, ImageDraw, ImageFont

S = 4
INK = (14, 17, 23, 255)
RED = (166, 30, 54, 255)
WHITE = (255, 255, 255, 255)
OUT = "/home/hatch/workspace/ecnuchat-prospectus/"

def keyhole(d, cx, cy, r, stem_w, stem_h, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    d.polygon([(cx - stem_w * 0.55, cy + r * 0.45), (cx + stem_w * 0.55, cy + r * 0.45),
               (cx + stem_w, cy + r + stem_h), (cx - stem_w, cy + r + stem_h)], fill=color)

def draw_mark(px):
    u = px * S
    img = Image.new("RGBA", (u, u), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    def k(v): return v * u // 1000
    d.rounded_rectangle([k(40), k(40), k(960), k(960)], radius=k(250), fill=INK)
    d.rounded_rectangle([k(225), k(250), k(775), k(680)], radius=k(110), fill=WHITE)
    d.polygon([(k(330), k(630)), (k(510), k(630)), (k(345), k(800))], fill=WHITE)
    keyhole(d, k(500), k(415), k(72), k(60), k(105), INK)
    return img.resize((px, px), Image.LANCZOS)

draw_mark(1200).save(OUT + "logo-mark.png")

# horizontal lockup
FW, FH = 2800, 720
W, H = FW * S, FH * S
lock = Image.new("RGBA", (W, H), (0, 0, 0, 0))
lock.alpha_composite(draw_mark(640 * S), (40 * S, 40 * S))
d = ImageDraw.Draw(lock)
bold = "/home/hatch/workspace/ruanzhu/fonts/NotoSansSC-Bold.ttf"
serif = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
tx = 740 * S
size = 200
while size > 40:
    f = ImageFont.truetype(bold, size * S)
    if d.textlength("ECNUCHAT", font=f) <= 1850 * S: break
    size -= 5
d.text((tx, 118 * S), "ECNUCHAT", font=f, fill=INK)
tag = "END-TO-END ENCRYPTED MESSAGING"
tsize = 54
while tsize > 20:
    f2 = ImageFont.truetype(serif, tsize * S)
    w2 = sum(d.textlength(ch, font=f2) for ch in tag) + (len(tag) - 1) * tsize * S * 0.42
    if w2 <= 1850 * S: break
    tsize -= 2
x = tx; tracking = tsize * S * 0.42
for ch in tag:
    d.text((x, 400 * S), ch, font=f2, fill=RED)
    x += d.textlength(ch, font=f2) + tracking
lock.resize((FW, FH), Image.LANCZOS).save(OUT + "logo-full.png")
print("official logo (C) generated")
