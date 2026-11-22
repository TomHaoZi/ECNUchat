# -*- coding: utf-8 -*-
"""Round 5: remove red label squares + left vertical bars (Hao: ugly);
rebuild slide 5 around the TWO core papers with their own figures."""
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)
RED = RGBColor(0xA6, 0x1E, 0x36)
INK = RGBColor(0x26, 0x26, 0x26)
GRAY = RGBColor(0x59, 0x59, 0x59)
FRAMEGRAY = RGBColor(0x8C, 0x8C, 0x8C)

def remove(sh):
    sh._element.getparent().remove(sh._element)

def near(v, target, tol=0.03):
    return abs(v - target) < tol

# ---- remove squares (0.96,0.415,0.10,0.10) and vertical bars (0.99,1.50,0.035,3.85) ----
killed = 0
for s in prs.slides:
    for sh in list(s.shapes):
        if sh.shape_type != 1:
            continue
        x, y, w, h = sh.left.inches, sh.top.inches, sh.width.inches, sh.height.inches
        is_square = near(x, 0.96) and near(y, 0.415) and near(w, 0.10) and near(h, 0.10)
        is_vbar = near(x, 0.99) and near(y, 1.50) and near(w, 0.035) and near(h, 3.85)
        if is_square or is_vbar:
            remove(sh); killed += 1
print("removed squares/bars:", killed)

def style_of(run):
    c = None
    try:
        if run.font.color and run.font.color.type is not None:
            c = run.font.color.rgb
    except Exception:
        pass
    return (run.font.bold or False, c)

def set_text(shape, paras):
    tf = shape.text_frame
    old = []
    for p in tf.paragraphs:
        styles = [style_of(r) for r in p.runs] or [(False, None)]
        old.append((p.alignment, styles))
    for p in list(tf.paragraphs)[1:]:
        p._p.getparent().remove(p._p)
    p0 = tf.paragraphs[0]
    for r in list(p0.runs):
        r._r.getparent().remove(r._r)
    for i, runs in enumerate(paras):
        p = p0 if i == 0 else tf.add_paragraph()
        align, styles = old[min(i, len(old) - 1)] if old else (None, [(False, None)])
        if align is not None:
            p.alignment = align
        p.space_after = Pt(4)
        p.line_spacing = 1.15
        for j, (text, size) in enumerate(runs):
            r = p.add_run(); r.text = text
            bold, color = styles[min(j, len(styles) - 1)]
            r.font.size = Pt(size); r.font.bold = bold
            if color is not None:
                r.font.color.rgb = color

def _font(run, size, bold, color):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.name = "Microsoft YaHei"
    if color is not None:
        run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {}); rPr.append(ea)
    ea.set('typeface', "Microsoft YaHei")

def add_text(slide, x, y, w, h, lines, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    for i, (text, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = 1.15
        p.space_after = Pt(2)
        r = p.add_run(); r.text = text
        _font(r, size, bold, color)
    return tb

def add_panel(slide, x, y, w, h):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.background()
    sh.line.color.rgb = FRAMEGRAY; sh.line.width = Pt(1.0)
    sh.shadow.inherit = False
    if sh.has_text_frame:
        sh.text_frame.text = ""
    return sh

# ---- Slide 5 rebuild ----
s5 = prs.slides[4]
set_text(s5.shapes[2], [[("文献基础：两篇核心论文", 26)]])
table = None
for sh in s5.shapes:
    if sh.has_table:
        table = sh
assert table is not None
remove(table)
set_text(s5.shapes[3], [[("▪ ", 14), ("两篇主论文撑起握手与棘轮；其余原语（HKDF、AES-GCM、Ed25519）按标准规范实现", 14)]])

add_panel(s5, 1.12, 1.50, 4.05, 3.42)
add_panel(s5, 5.37, 1.50, 4.05, 3.42)
add_text(s5, 1.28, 1.60, 3.73, 0.34, [("Fiedler & Günther（PKC 2025）", 14, True, RED)])
add_text(s5, 5.53, 1.60, 3.73, 0.34, [("Bienstock 等（CRYPTO 2022）", 14, True, RED)])
# PQXDH figure: ratio 1.397 -> h 2.24, w 3.13
s5.shapes.add_picture("/home/hatch/workspace/ecnuchat-midterm/paperfigs/paper-fig-pqxdh.png",
                      Inches(1.58), Inches(2.00), Inches(3.13), Inches(2.24))
# DR figure: ratio 2.418 -> w 3.73, h 1.54, vertically centered in image zone
s5.shapes.add_picture("/home/hatch/workspace/ecnuchat-midterm/paperfigs/paper-fig-dr.png",
                      Inches(5.53), Inches(2.35), Inches(3.73), Inches(1.54))
add_text(s5, 1.28, 4.30, 3.73, 0.58,
         [("论文图 10：PQXDH 协议原图，深灰 = 新增的后量子部分；我们的握手按此构造。", 11.5, False, INK)])
add_text(s5, 5.53, 4.30, 3.73, 0.58,
         [("论文图 1：双棘轮钥匙演化（红根钥、蓝链钥、绿消息钥）；已知小窗口未修，主动声明。", 11.5, False, INK)])

# ---- Slide 2 outline wording ----
s2 = prs.slides[1]
for sh in s2.shapes:
    if sh.has_text_frame and "十篇论文构成的证据链" in sh.text_frame.text:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if "十篇论文构成的证据链" in r.text:
                    r.text = r.text.replace("十篇论文构成的证据链", "两篇核心论文")

# ---- Slide 5 speaker notes: two-paper version ----
new_note = ("【一句话】设计不凭空来：握手与棘轮各有一篇主论文撑着，构造对齐，我们没重跑证明。\n\n"
            "【1:45–2:25】文献只讲两篇最要紧的。左边 Fiedler 与 Günther（PKC 2025）分析 Signal 的 PQXDH 握手——图是论文里的协议原图，"
            "深灰部分就是相比 X3DH 新增的后量子环节；我们的握手按这个构造做：四次 DH 之外再并入 ML-KEM-768 封装，防的是先存后解。"
            "右边 Bienstock 等（CRYPTO 2022）是第一篇完整分析双棘轮的论文——图是它的钥匙演化图：红点根钥、蓝点链钥、绿点消息钥。"
            "我们的棘轮按它实现；也要主动声明：这篇指出的已知小窗口（dhs_priv）我们没修，Triple Ratchet 也没实现。"
            "其余原语——HKDF、AES-GCM、Ed25519——用的是标准规范，不单列。立场一句：我们是构造对齐被证明过的拼法，没有在自己代码上重跑形式化证明。")
s5.notes_slide.notes_text_frame.text = new_note

prs.save(SRC)
print("slide 5 rebuilt; notes synced")
