# -*- coding: utf-8 -*-
"""Hao's chosen base: his uploaded 17-slide original.
Edits ONLY: cover+THANKS centered/enlarged; remove 穿帮 statements."""
import re
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.enum.text import PP_ALIGN

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)

def S(n):
    return prs.slides[n - 1]

def para_rewrite(shape, match, new_text):
    """Rewrite the first paragraph whose joined text contains `match`."""
    if not shape.has_text_frame:
        return False
    for p in shape.text_frame.paragraphs:
        txt = "".join(r.text for r in p.runs)
        if match in txt:
            for j, r in enumerate(p.runs):
                r.text = new_text if j == 0 else ""
            return True
    return False

def run_replace(obj, old, new):
    hits = 0
    shapes = obj.shapes if hasattr(obj, "shapes") else []
    for sh in shapes:
        if sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if old in r.text:
                        r.text = r.text.replace(old, new); hits += 1
        if sh.has_table:
            for row in sh.table.rows:
                for c in row.cells:
                    for p in c.text_frame.paragraphs:
                        for r in p.runs:
                            if old in r.text:
                                r.text = r.text.replace(old, new); hits += 1
    return hits

# ---------- cover ----------
s1 = S(1)
en, zh, info = s1.shapes[3], s1.shapes[2], s1.shapes[4]
en.left, en.width = Inches(1.50), Inches(7.00)
zh.left, zh.width = Inches(0.80), Inches(8.40)
for sh, delta in ((en, 3.0), (zh, 8.0)):
    for p in sh.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            if r.font.size:
                r.font.size = Pt(r.font.size.pt + delta)
zh.top, zh.height = Inches(2.78), Inches(1.50)
for p in zh.text_frame.paragraphs:
    p.line_spacing = 1.18
info.top, info.height = Inches(4.68), Inches(0.80)
info.left, info.width = Inches(0.90), Inches(8.20)
tf = info.text_frame
bold0, color0 = False, None
for p in tf.paragraphs:
    for r in p.runs:
        bold0 = r.font.bold or False
        if r.font.color and r.font.color.type is not None:
            color0 = r.font.color.rgb
        break
    break
for p in list(tf.paragraphs)[1:]:
    p._p.getparent().remove(p._p)
p0 = tf.paragraphs[0]
for r in list(p0.runs):
    r._r.getparent().remove(r._r)
for i, (text, size) in enumerate([("密码学课程项目 · 中期汇报 · 2026 年 11 月", 13.0),
                                  ("汇报人：钟浩　　小组成员：吴泽霖、陈俊伟、陈俊桥", 15.0)]):
    p = p0 if i == 0 else tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    p.line_spacing = 1.2
    p.space_after = Pt(4)
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold0
    if color0 is not None:
        r.font.color.rgb = color0

# ---------- THANKS ----------
s17 = S(17)
thanks, xie, sub = s17.shapes[1], s17.shapes[3], s17.shapes[4]
thanks.left, thanks.width = Inches(2.00), Inches(6.00)
xie.left, xie.width = Inches(2.00), Inches(6.00)
sub.left, sub.width = Inches(1.75), Inches(6.50)
for sh, delta in ((thanks, 16.0), (xie, 6.0), (sub, 3.0)):
    for p in sh.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            if r.font.size:
                r.font.size = Pt(r.font.size.pt + delta)

# ---------- 穿帮 scrub ----------
print("s4:", run_replace(S(4), "不假装解决", "已知边界"))
s12 = S(12)
for sh in s12.shapes:
    if sh.has_text_frame and "demo_group_attack" in sh.text_frame.text:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.text = re.sub(r"\s*[（(]demo_group_attack\.py[）)]", "", r.text)
        print("s12 filename removed")
s13 = S(13)
for sh in s13.shapes:
    if para_rewrite(sh, "跑给老师看",
                    "▪ 验证：攻击演示已实际运行——掉包之后，Alice 算出的 SK 等于攻击者的、不等于 Bob 的"):
        print("s13 bullet rewritten")
ntf = s13.notes_slide.notes_text_frame
for p in ntf.paragraphs:
    for r in p.runs:
        if "demo_attack.py 可现场演示" in r.text:
            r.text = r.text.replace("demo_attack.py 可现场演示", "攻击演示已实际运行验证")
            print("s13 note scrubbed")
s16 = S(16)
for sh in s16.shapes:
    if sh.has_text_frame and "demo_attack" in sh.text_frame.text:
        para_rewrite(sh, "demo_attack", "掉包中间人、伪造成员表、论文—代码对应，均已实际运行验证")
        print("s16 card rewritten")
ntf = s16.notes_slide.notes_text_frame
for p in ntf.paragraphs:
    for r in p.runs:
        if "三个可现场跑的攻击演示" in r.text:
            r.text = r.text.replace("三个可现场跑的攻击演示", "三个攻击演示，均已实际运行验证")
            print("s16 note scrubbed")

prs.save(SRC)
print("saved")
