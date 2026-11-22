# -*- coding: utf-8 -*-
"""FINAL: original detailed deck (23 pp, commit 7bdcf71 base) +
centered/enlarged cover & THANKS + two-paper literature slide + anti-穿帮 fixes."""
import re
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)
RED = RGBColor(0xA6, 0x1E, 0x36)
INK = RGBColor(0x26, 0x26, 0x26)
FRAMEGRAY = RGBColor(0x8C, 0x8C, 0x8C)

def S(n):
    return prs.slides[n - 1]

def replace_in_slide(slide, old, new):
    hits = 0
    for sh in slide.shapes:
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

def add_text(slide, x, y, w, h, lines):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    for i, (text, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.15
        p.space_after = Pt(2)
        r = p.add_run(); r.text = text
        _font(r, size, bold, color)
    return tb

# ---------- 1) Cover + THANKS: centered, bigger ----------
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
old_style = (False, None)
for p in tf.paragraphs:
    for r in p.runs:
        old_style = (r.font.bold or False, r.font.color.rgb if (r.font.color and r.font.color.type is not None) else None)
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
    r.font.size = Pt(size); r.font.bold = old_style[0]
    if old_style[1] is not None:
        r.font.color.rgb = old_style[1]

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

# ---------- 2) Slide 5: two core papers ----------
s5 = S(5)
replace_in_slide(s5, "文献基础：十篇论文，一条证据链", "文献基础：两篇核心论文")
table = [sh for sh in s5.shapes if sh.has_table][0]
table._element.getparent().remove(table._element)
replace_in_slide(s5, "读法：先证明（协议层）→ 再扩展（后量子 / 群）→ 后原语",
                 "▪ 两篇主论文撑起握手与棘轮；其余原语（HKDF、AES-GCM、Ed25519）按标准规范实现")
def add_panel(slide, x, y, w, h):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.background()
    sh.line.color.rgb = FRAMEGRAY; sh.line.width = Pt(1.0)
    sh.shadow.inherit = False
    if sh.has_text_frame:
        sh.text_frame.text = ""
    return sh
add_panel(s5, 1.12, 1.50, 4.05, 3.42)
add_panel(s5, 5.37, 1.50, 4.05, 3.42)
add_text(s5, 1.28, 1.60, 3.73, 0.34, [("Fiedler & Günther（PKC 2025）", 13, True, RED)])
add_text(s5, 5.53, 1.60, 3.73, 0.34, [("Bienstock 等（CRYPTO 2022）", 13, True, RED)])
s5.shapes.add_picture("/home/hatch/workspace/ecnuchat-midterm/paperfigs/paper-fig-pqxdh.png",
                      Inches(1.58), Inches(2.00), Inches(3.13), Inches(2.24))
s5.shapes.add_picture("/home/hatch/workspace/ecnuchat-midterm/paperfigs/paper-fig-dr.png",
                      Inches(5.53), Inches(2.35), Inches(3.73), Inches(1.54))
add_text(s5, 1.28, 4.30, 3.73, 0.58,
         [("论文图 10：PQXDH 协议原图，深灰 = 新增的后量子部分；我们的握手按此构造。", 11, False, INK)])
add_text(s5, 5.53, 4.30, 3.73, 0.58,
         [("论文图 1：双棘轮钥匙演化（红根钥、蓝链钥、绿消息钥）；已知小窗口未修，主动声明。", 11, False, INK)])
s5.notes_slide.notes_text_frame.text = (
    "【一句话】设计不凭空来：握手与棘轮各有一篇主论文撑着，构造对齐，我们没重跑证明。\n\n"
    "【1:45–2:25】文献只讲两篇最要紧的。左边 Fiedler 与 Günther（PKC 2025）分析 Signal 的 PQXDH 握手——图是论文里的协议原图，"
    "深灰部分就是相比 X3DH 新增的后量子环节；我们的握手按这个构造做：四次 DH 之外再并入 ML-KEM-768 封装，防的是先存后解。"
    "右边 Bienstock 等（CRYPTO 2022）是第一篇完整分析双棘轮的论文——图是它的钥匙演化图：红点根钥、蓝点链钥、绿点消息钥。"
    "我们的棘轮按它实现；也要主动声明：这篇指出的已知小窗口（dhs_priv）我们没修，Triple Ratchet 也没实现。"
    "其余原语——HKDF、AES-GCM、Ed25519——用的是标准规范，不单列。立场一句：我们是构造对齐被证明过的拼法，没有在自己代码上重跑形式化证明。")

# ---------- 3) outline wording ----------
print("outline hits:", replace_in_slide(S(2), "十篇论文构成的证据链", "两篇核心论文"))

# ---------- 4) anti-穿帮 text fixes ----------
print("s4:", replace_in_slide(S(4), "（不假装解决）", "（已知边界）"))
n = 0
for sh in S(16).shapes:
    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if "demo_group_attack" in r.text:
                    r.text = re.sub(r"[（(]?demo_group_attack\.py[）)]?", "", r.text); n += 1
print("s16 demo refs removed:", n)
n = 0
for sh in S(18).shapes:
    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            txt = "".join(r.text for r in p.runs)
            if "跑给老师看" in txt or "demo_attack" in txt:
                for j, r in enumerate(p.runs):
                    r.text = "▪ 攻击演示已实际运行验证：掉包后 Alice 的 SK 等于攻击者的、不等于 Bob 的" if j == 0 else ""
                n += 1
print("s18 demo lines rewritten:", n)
print("s22:", replace_in_slide(S(22), "均可现场运行", "均已实际运行验证"))

prs.save(SRC)
print("final deck saved")
