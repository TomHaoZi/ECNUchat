# -*- coding: utf-8 -*-
"""Round 4: academic paper-presentation frame system.
Title double-rules, red section squares, left accent bars, diagram frames,
outline row rules, centered + enlarged cover and THANKS pages."""
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)

RED = RGBColor(0xA6, 0x1E, 0x36)
GRAYLINE = RGBColor(0xBF, 0xBF, 0xBF)
FRAMEGRAY = RGBColor(0x8C, 0x8C, 0x8C)

def add_rect(slide, x, y, w, h, fill=None, line=None, line_w=1.0):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(line_w)
    sh.shadow.inherit = False
    if sh.has_text_frame:
        sh.text_frame.text = ""
    return sh

def S(n):
    return prs.slides[n - 1]

FIGURE = {7: 3.32, 9: 3.10, 12: 3.64, 14: 3.32, 17: 3.58, 19: 3.58}
CONTENT = [3, 4, 5, 6, 8, 10, 11, 13, 15, 16, 18, 20, 21, 22]

for n in range(2, 23):
    s = S(n)
    # red square before the section label
    add_rect(s, 0.96, 0.415, 0.10, 0.10, fill=RED)
    if n in FIGURE:
        # frame around the diagram; its top edge doubles as the title rule
        add_rect(s, 0.38, 1.30, 9.24, FIGURE[n], fill=None, line=FRAMEGRAY, line_w=1.0)
    else:
        # title double rule: thick red + thin gray
        add_rect(s, 1.12, 1.28, 8.30, 0.045, fill=RED)
        add_rect(s, 1.12, 1.352, 8.30, 0.014, fill=GRAYLINE)
    if n in CONTENT:
        # left vertical accent bar
        add_rect(s, 0.99, 1.50, 0.035, 3.85, fill=RED)

# outline row separators (slide 2)
for y in (2.04, 2.66, 3.28, 3.90, 4.52):
    add_rect(S(2), 1.12, y, 8.30, 0.012, fill=GRAYLINE)

# ---------- Cover (slide 1): centered + bigger ----------
s1 = S(1)
en, zh, info = s1.shapes[3], s1.shapes[2], s1.shapes[4]
en.left, en.width = Inches(1.50), Inches(7.00)
zh.left, zh.width = Inches(0.80), Inches(8.40)
info.left, info.width = Inches(1.00), Inches(8.00)
for sh, delta in ((en, 3.0), (zh, 8.0), (info, 2.0)):
    for p in sh.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            if r.font.size:
                r.font.size = Pt(r.font.size.pt + delta)

# ---------- THANKS (slide 23): centered + bigger ----------
s23 = S(23)
thanks, xie, sub = s23.shapes[1], s23.shapes[3], s23.shapes[4]
thanks.left, thanks.width = Inches(2.00), Inches(6.00)
xie.left, xie.width = Inches(2.00), Inches(6.00)
sub.left, sub.width = Inches(1.75), Inches(6.50)
for sh, delta in ((thanks, 16.0), (xie, 6.0), (sub, 3.0)):
    for p in sh.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            if r.font.size:
                r.font.size = Pt(r.font.size.pt + delta)

prs.save(SRC)
print("academic restyle saved")
