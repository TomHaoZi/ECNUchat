# -*- coding: utf-8 -*-
"""Round 3: de-listify. Bullet blocks -> single takeaway lines;
lists -> chip grids / flow boxes (all native editable shapes)."""
import copy
from pptx import Presentation
from pptx.util import Pt, Inches, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)

RED = RGBColor(0xA6, 0x1E, 0x36)
INK = RGBColor(0x26, 0x26, 0x26)
GRAY = RGBColor(0x59, 0x59, 0x59)
CHIP_FILL = RGBColor(0xFB, 0xF3, 0xF4)
REDFILL = RGBColor(0xFD, 0xEC, 0xEA)
GREENFILL = RGBColor(0xE9, 0xF5, 0xEC)
GRAYFILL = RGBColor(0xF2, 0xF2, 0xF2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

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

def remove(shape):
    shape._element.getparent().remove(shape._element)

def _font(run, size, bold, color):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = "Microsoft YaHei"
    if color is not None:
        run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', "Microsoft YaHei")

def add_box(slide, x, y, w, h, fill, line_color=RED, line_w=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        sh.adjustments[0] = 0.08
    except Exception:
        pass
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line_color is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line_color; sh.line.width = Pt(line_w)
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ("margin_left", "margin_right"):
        setattr(tf, m, Inches(0.08))
    for m in ("margin_top", "margin_bottom"):
        setattr(tf, m, Inches(0.03))
    return sh

def box_text(sh, lines, align=PP_ALIGN.CENTER):
    """lines: list of (text, size, bold, color) paragraphs."""
    tf = sh.text_frame
    for i, (text, size, bold, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = 1.12
        p.space_after = Pt(2)
        r = p.add_run(); r.text = text
        _font(r, size, bold, color)

def add_arrow(slide, x, y, w=0.24):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.4))
    tf = tb.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "→"
    _font(r, 15, True, RED)
    return tb

def S(n):
    return prs.slides[n - 1]

def shp(n, idx):
    return S(n).shapes[idx]

# ---------- single-line takeaways replacing bullet blocks ----------
set_text(shp(3, 16), [[("▪ ", 14), ("安全目标：防窃听、防篡改、防冒充；服务器只存公钥、转发密文，看不懂内容", 14)]])
set_text(shp(6, 3), [[("▪ ", 14), ("界面层不接触链钥匙；密码模块可离线单测；服务器只存公钥与信封", 14)]])
set_text(shp(10, 3), [[("▪ ", 14), ("SK = HKDF（DH1‖DH2‖DH3‖DH4）—— 只启动双棘轮，不直接加密", 14)]])
set_text(shp(13, 3), [[("▪ ", 14), ("逐条换钥 = 前向安全；回复换链 = 破密恢复", 14)]])
set_text(shp(16, 4), [[("▪ ", 14), ("签名哈希链管名单：每次只增一人，群消息带状态哈希，伪造即暴露", 14)]])
set_text(shp(21, 5), [[("▪ ", 14), ("约 2 万行 Python；文件第二层加密；社交数据明文存放（已知边界）", 14)]])

# ---------- S15 / S20 card bodies: shorter ----------
set_text(shp(15, 6), [[("每条新链再对 PQK 做一次 ML-KEM 封装；缺 pq_ct 直接拒绝。", 14)]])
set_text(shp(15, 10), [[("超前先缓存中间 MK（上限 40）；迟到取出即删。", 14)]])
set_text(shp(15, 14), [[("已处理的再现直接拒绝；改任一字节，GCM 失败。", 14)]])
set_text(shp(15, 18), [[("先在副本试算，成功才提交；伪造包烧不掉钥匙。", 14)]])
set_text(shp(20, 6), [[("每条新链都混入 ML-KEM 封装，优先 PQOPK，拒绝降级。", 14)]])
set_text(shp(20, 10), [[("以 O(n) 换回逐对前向安全与破密恢复。", 14)]])
set_text(shp(20, 14), [[("签名覆盖全部握手材料；身份公钥钉住，换钥即拒。", 14)]])
set_text(shp(20, 18), [[("副本试算、成功才提交；OPK 私钥延迟删除。", 14)]])

# ---------- S19 prose block: shorter ----------
set_text(shp(19, 7), [[("挑战应答只能证明你持有服务器当初收下的私钥——注册时被换钥，证明链从源头就断。Signal 同样靠安全码核对。", 13)]])

# ---------- S4: lists -> chip grids ----------
s4 = S(4)
old_left, old_right = shp(4, 6), shp(4, 10)
remove(old_left); remove(old_right)
func_chips = ["账户与身份", "一对一私聊", "群聊 ≤ 8 人", "富媒体 · 通话"]
sec_chips = ["机密性", "完整性与认证", "前向安全", "破密恢复", "抗重放 · 篡改 · 降级", "目录安全"]
def chip_grid(slide, x0, chips, wide_last=False):
    for i, label in enumerate(chips):
        col, row = i % 2, i // 2
        x = x0 + col * 1.74
        w = 1.66
        if wide_last and i == len(chips) - 1 and len(chips) % 2 == 1:
            x, w = x0, 3.40
        sh = add_box(slide, x, 2.00 + row * 0.64, w, 0.54, CHIP_FILL)
        box_text(sh, [(label, 13, True, INK)])
chip_grid(s4, 1.36, func_chips)
sh = add_box(s4, 1.36, 2.00 + 2 * 0.64, 3.40, 0.54, CHIP_FILL)
box_text(sh, [("双端一致（桌面 + 终端）", 13, True, INK)])
chip_grid(s4, 5.36, sec_chips)

# ---------- S11: bullets -> 2x2 chip grid ----------
s11 = S(11)
remove(shp(11, 6))
chips11 = [("PQOPK 优先", "用完即删，取不到退到长期 PQK"),
           ("拒绝降级", "缺 KEM 的握手直接拒绝"),
           ("签名全覆盖", "封装公钥与密文都在签名内"),
           ("ML-KEM-768", "域标签 x3dh-v1 / pqxdh-v1")]
for i, (title, sub) in enumerate(chips11):
    col, row = i % 2, i // 2
    sh = add_box(s11, 1.12 + col * 4.00, 3.30 + row * 1.02, 3.85, 0.92, CHIP_FILL)
    box_text(sh, [(title, 14.5, True, RED), (sub, 12, False, INK)], align=PP_ALIGN.LEFT)

# ---------- S18: bullets -> 3 flow boxes ----------
s18 = S(18)
remove(shp(18, 3))
flow18 = [("攻击", "服务器换公钥配自签身份，与 Alice 建会话", REDFILL),
          ("防线", "指纹核对后钉住公钥，再换即拒", GREENFILL),
          ("验证", "掉包后 SK = 攻击者的 ≠ Bob 的", GRAYFILL)]
for i, (title, body, fill) in enumerate(flow18):
    sh = add_box(s18, 1.12 + i * 2.91, 4.16, 2.70, 1.30, fill)
    box_text(sh, [(title, 13.5, True, RED), (body, 11.5, False, INK)])
add_arrow(s18, 3.84, 4.62)
add_arrow(s18, 6.75, 4.62)

# ---------- S22: roadmap bullets -> 3 flow boxes ----------
s22 = S(22)
remove(shp(22, 16))
road = [("v2 落地", "生产部署 · 桌面打包"),
        ("协议补强", "语音媒体面 · 密封发送者 · Triple Ratchet 评估"),
        ("已知缺口", "无多设备 · 无头加密 · 元数据可见")]
for i, (title, body) in enumerate(road):
    sh = add_box(s22, 1.12 + i * 2.68, 3.86, 2.48, 1.50, CHIP_FILL)
    box_text(sh, [(title, 14, True, RED), (body, 11.5, False, INK)])
add_arrow(s22, 3.62, 4.42)
add_arrow(s22, 6.30, 4.42)

prs.save(SRC)
print("round-3 deck saved")
