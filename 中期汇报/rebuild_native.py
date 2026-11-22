# -*- coding: utf-8 -*-
"""Rebuild every diagram in the midterm deck as native editable shapes/text.
Keeps: slide order, furniture, text boxes, template art (slides 1/23),
and the real app screenshot on slide 21. Removes: all diagram pictures."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

RED = RGBColor(0xA6, 0x1E, 0x36)
INK = RGBColor(0x26, 0x26, 0x26)
GRAY = RGBColor(0x59, 0x59, 0x59)
LGRAY = RGBColor(0x8C, 0x8C, 0x8C)
FILL = RGBColor(0xF7, 0xF7, 0xF7)
FILLD = RGBColor(0xED, 0xF0, 0xF4)
BORD = RGBColor(0xBF, 0xBF, 0xBF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
REDF = RGBColor(0xFB, 0xF0, 0xF1)
REDB = RGBColor(0xC0, 0x50, 0x4D)
GRNF = RGBColor(0xEF, 0xF5, 0xEF)
GRNB = RGBColor(0x7A, 0x9A, 0x7A)
BLUB = RGBColor(0x4A, 0x6F, 0xA5)
FONT = "Microsoft YaHei"
SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"

prs = Presentation(SRC)

def _font(run, size, bold, color):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.name = FONT; f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        e = rPr.find(qn("a:" + tag))
        if e is None:
            e = rPr.makeelement(qn("a:" + tag), {}); rPr.append(e)
        e.set("typeface", FONT)

def fill_text(tf, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
              ml=0.09, mr=0.09, mt=0.05, mb=0.04, space_after=3, ls=1.1):
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(ml); tf.margin_right = Inches(mr)
    tf.margin_top = Inches(mt); tf.margin_bottom = Inches(mb)
    for i, runs in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space_after); p.line_spacing = ls
        for (t, sz, b, c) in runs:
            r = p.add_run(); r.text = t; _font(r, sz, b, c)

def tx(s, x, y, w, h, paras, **kw):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    fill_text(box.text_frame, paras, **kw)
    return box

def bx(s, x, y, w, h, paras, fill=FILL, line=BORD, lw=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, **kw):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try: sp.adjustments[0] = 0.055
        except Exception: pass
    if fill is None: sp.fill.background()
    else: sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb = line; sp.line.width = Pt(lw)
    sp.shadow.inherit = False
    fill_text(sp.text_frame, paras, **kw)
    return sp

def arrow_r(s, x, y, w=0.34, h=0.16, color=GRAY):
    sp = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def arrow_d(s, x, y, w=0.16, h=0.30, color=GRAY):
    sp = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid(); sp.fill.fore_color.rgb = color
    sp.line.fill.background(); sp.shadow.inherit = False
    return sp

def remove_pictures(s, names=("Picture 4", "Picture 1")):
    removed = []
    for sh in list(s.shapes):
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE and sh.name in names:
            removed.append((sh.left.inches, sh.top.inches, sh.width.inches, sh.height.inches))
            sh._element.getparent().remove(sh._element)
    return removed

def furniture(s, label, title):
    tx(s, 1.12, 0.34, 4.50, 0.30, [[(label, 9, False, LGRAY)]])
    tx(s, 1.12, 0.62, 8.30, 0.62, [[(title, 19, True, RED)]])

def takeaway(s, text, y=5.06):
    tx(s, 0.50, y, 9.05, 0.55, [[("▪ ", 11.5, True, RED), (text, 11.5, False, INK)]], ls=1.15)

def slide(i):
    return prs.slides[i - 1]

# ============ EMBEDDED DIAGRAMS (content slides) ============
# ---- Slide 6 · architecture mini (was 2.76,1.48,4.49x2.95) ----
s = slide(6); remove_pictures(s)
cols = [
    ("Alice 的电脑", [("桌面窗口 / 终端", "只显示已解开的明文"), ("ChatEngine", "登录、收发信封、保存会话"),
                      ("X3DH 与双棘轮", "每条消息 AES-256-GCM"), ("本地加密数据库", "口令封存私钥与状态")]),
    ("服务器", [("公钥目录", "身份公钥、签名与一次性预密钥"), ("转发", "按用户名交信封给收件人"),
                 ("离线队列", "对方不在线先暂存"), ("服务器看不到", "口令、私钥、明文、SK、MK")]),
    ("Bob 的电脑", [("同一套客户端", "用自己的私钥重算共享秘密"), ("先验签，再解密", "签名不对、重放、篡改都拒绝"),
                     ("独立的消息密钥", "每条一把，用完即删"), ("重启后续", "口令解开本地状态接着收")]),
]
for ci, (head, rows) in enumerate(cols):
    x = 2.62 + ci * 1.62
    bx(s, x, 1.50, 1.30, 2.90, [[(head, 9.5, True, RED)]], fill=FILLD, align=PP_ALIGN.CENTER)
    for ri, (h, b) in enumerate(rows):
        bx(s, x + 0.05, 1.86 + ri * 0.63, 1.20, 0.58,
           [[(h, 8, True, INK)], [(b, 7, False, GRAY)]], fill=WHITE, space_after=1, ls=1.02)
    if ci < 2:
        arrow_r(s, x + 1.33, 2.80, 0.26, 0.13, RED)
        tx(s, x + 1.28, 2.58, 0.36, 0.2, [[("信封", 7.5, False, RED)]], align=PP_ALIGN.CENTER)

# ---- Slide 8 · key system mini (was 1.12,1.50,4.70x2.55) ----
s = slide(8); remove_pictures(s)
keys = [("IK_sign", "身份签名钥匙", "Ed25519，只签名"),
        ("IK_dh", "身份协商钥匙", "X25519，只做 DH"),
        ("SPK", "签名预密钥", "用前必须先验签"),
        ("OPK", "一次性预密钥", "备 20 把，用完即删")]
for i, (n, h, b) in enumerate(keys):
    x = 1.12 + i * 1.19
    bx(s, x, 1.52, 1.13, 1.86,
       [[(n, 10.5, True, RED)], [(h, 8.5, True, INK)], [(b, 7.5, False, GRAY)]],
       fill=FILL, space_after=3, ls=1.08)
bx(s, 1.12, 3.50, 4.70, 0.52,
   [[("落盘：", 8.5, True, INK), ("口令经 PBKDF2-HMAC-SHA256（60 万次）派生密钥，AES-256-GCM 封存全部私钥", 8.5, False, INK)]],
   fill=GRNF, line=GRNB, ls=1.1)

# ---- Slide 10 · X3DH mini ----
s = slide(10); bb = remove_pictures(s)
X, Y, W, H = bb[0]
rows = [("Alice 的 IK_dh 私钥", "DH1", "Bob 的 SPK 公钥", "长期身份绑到已签名的预密钥"),
        ("Alice 的临时钥 EK", "DH2", "Bob 的 IK_dh 公钥", "新鲜临时钥绑到长期协商身份"),
        ("Alice 的临时钥 EK", "DH3", "Bob 的 SPK 公钥", "长期钥以后泄露也重算不出"),
        ("Alice 的临时钥 EK", "DH4", "Bob 的 OPK 公钥", "可选：一次性钥用完即删")]
rh = (H - 0.52) / 4
for i, (a, d, b, note) in enumerate(rows):
    y = Y + i * rh
    bx(s, X, y + 0.02, 1.30, rh - 0.06, [[(a, 7.5, True, INK)]], fill=FILL,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, ls=1.05)
    arrow_r(s, X + 1.36, y + rh / 2 - 0.07, 0.30, 0.13, BLUB)
    tx(s, X + 1.30, y + 0.02, 0.42, 0.2, [[(d, 7.5, True, BLUB)]], align=PP_ALIGN.CENTER)
    bx(s, X + 1.72, y + 0.02, 1.22, rh - 0.06, [[(b, 7.5, True, INK)]], fill=FILL,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, ls=1.05)
    tx(s, X + 3.00, y + 0.04, W - 3.02, rh - 0.06, [[(note, 7.5, False, GRAY)]], ls=1.05)
bx(s, X, Y + H - 0.46, W, 0.44,
   [[("SK = HKDF-SHA256（DH1‖DH2‖DH3‖DH4，info=“x3dh-v1”）", 8, True, INK)]],
   fill=FILLD, line=BLUB, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ---- Slide 13 · ratchet mini ----
s = slide(13); bb = remove_pictures(s)
X, Y, W, H = bb[0]
steps = [("1", "Alice 发第一条", "SK 初始化发送链，MK1 加密后立即丢弃"),
         ("2", "Alice 再发一条", "同一条链再走一步，MK2 与 MK1 不同"),
         ("3", "Bob 第一次回复", "生成自己的棘轮钥，做一次 DH 棘轮换链"),
         ("4", "双方都换过公钥", "旧链钥泄露也解不开新消息，破密恢复")]
cw = (W - 0.24) / 4
for i, (n, h, b) in enumerate(steps):
    x = X + i * (cw + 0.08)
    bx(s, x, Y, cw, H * 0.60,
       [[(n, 13, True, RED)], [(h, 8.5, True, INK)], [(b, 7.5, False, GRAY)]],
       fill=FILL, align=PP_ALIGN.CENTER, space_after=2, ls=1.08)
bx(s, X, Y + H * 0.66, W / 2 - 0.05, H * 0.32,
   [[("前向安全：", 8.5, True, INK), ("MK 用完即删，链钥泄露也倒推不回已删的 MK", 8.5, False, INK)]],
   fill=GRNF, line=GRNB, ls=1.1)
bx(s, X + W / 2 + 0.05, Y + H * 0.66, W / 2 - 0.05, H * 0.32,
   [[("破密恢复：", 8.5, True, INK), ("对方回复、双方都换过棘轮公钥后，旧链钥推不出新消息", 8.5, False, INK)]],
   fill=REDF, line=REDB, ls=1.1)

# ---- Slide 18 · fingerprint mini ----
s = slide(18); bb = remove_pictures(s)
X, Y, W, H = bb[0]
left = ["Alice 向服务器要 Bob 的预密钥包", "服务器把公钥换成攻击者的", "验签能通过（签名是攻击者自签）",
        "Alice 的 SK ≠ 真实 Bob 的 SK", "攻击者与真 Bob 另建会话，两边可见"]
right = ["双方线下比对 16 组指纹无误", "客户端钉住身份公钥，再变就拒绝", "服务器只能继续转发密文信封",
         "它没有消息钥匙，读不出内容", "改一个密文字节，接收方 GCM 失败"]
for side, (head, items, f, ln) in enumerate([
        ("还没核对指纹", left, REDF, REDB), ("已经核对指纹", right, GRNF, GRNB)]):
    x = X + side * (W / 2 + 0.03)
    w = W / 2 - 0.06
    paras = [[(head, 9.5, True, RED if side == 0 else RGBColor(0x2E, 0x7D, 0x32))]]
    for j, it in enumerate(items):
        paras.append([(f"{j+1}. {it}", 7.8, False, INK)])
    bx(s, x, Y, w, H, paras, fill=f, line=ln, space_after=4, ls=1.08)

# ============ FULL-SLIDE DIAGRAMS ============
# ---- Slide 7 · architecture ----
s = slide(7); remove_pictures(s)
furniture(s, "03 · 协议设计", "总体架构：四层客户端 + 只做「邮局」的中继服务器")
def arch_col(x, head, rows, w=2.72):
    bx(s, x, 1.34, w, 0.40, [[(head, 11.5, True, WHITE)]], fill=INK, line=None,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    for i, (h, b) in enumerate(rows):
        bx(s, x, 1.84 + i * 0.72, w, 0.64,
           [[(h, 10.5, True, INK), ("　" + b, 9.5, False, GRAY)]], fill=FILL, ls=1.05)
arch_col(0.50, "客户端（Alice）", [
    ("界面层", "桌面 GUI（PySide6）/ 终端 TUI（rich），不接触链钥匙"),
    ("会话引擎 ChatEngine", "会话状态与消息编排"),
    ("密码模块", "纯字节进出，不导入网络与数据库，可离线单测"),
    ("本地保险库", "PBKDF2 60 万次派生，AES-256-GCM 封存私钥与状态")])
arch_col(3.64, "中继服务器（只做邮局）", [
    ("公钥目录 + 预密钥池", "保存 bundle：只有公钥，没有私钥"),
    ("离线信封队列", "密文暂存，按用户名转发"),
    ("社交数据（明文）", "好友关系、朋友圈 —— 已知边界，主动声明"),
    ("它解析不出明文", "没有私钥、没有 SK，解不开任何信封")])
arch_col(6.78, "对方客户端（Bob）", [
    ("界面层", "与左侧完全相同的四层结构"),
    ("会话引擎 ChatEngine", "双方各自保管自己的私钥"),
    ("密码模块", "服务器手里没有任何一方的私钥"),
    ("本地保险库", "（与 Alice 的区别只在身份钥）")])
for (x, lab) in [(3.28, "取 bundle"), (3.28, "上传信封")]:
    pass
arrow_r(s, 3.26, 2.14, 0.34, 0.15, RED); tx(s, 3.02, 1.90, 0.82, 0.22, [[("取 bundle", 8.5, False, RED)]], align=PP_ALIGN.CENTER)
arrow_r(s, 3.26, 2.86, 0.34, 0.15, RED); tx(s, 3.02, 3.08, 0.82, 0.22, [[("上传信封", 8.5, False, RED)]], align=PP_ALIGN.CENTER)
arrow_r(s, 6.40, 2.50, 0.34, 0.15, RED); tx(s, 6.16, 2.26, 0.82, 0.22, [[("转发信封", 8.5, False, RED)]], align=PP_ALIGN.CENTER)
bx(s, 0.50, 4.68, 9.00, 0.34,
   [[("客户端 ↔ 服务器只走两类东西：取公钥包（bundle）与离线信封，全程密文 · 聊天帧上限 64 KB · 附件走二进制帧", 10, False, INK)]],
   fill=FILLD, line=None, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
takeaway(s, "服务器看不到：消息正文 · 文件与文件名 · 语音内容 · 私钥 · SK/MK；能看到：谁给谁发 · 时间 · 信封大小 · 全部公钥（元数据未保护）")

# ---- Slide 9 · key system ----
s = slide(9); remove_pictures(s)
furniture(s, "03 · 协议设计", "密钥体系：签名与协商从生成起就是两把钥")
cards = [
    ("IK_sign", "长期「签名」身份钥", "Ed25519。签 SPK、签初始消息、签群状态；指纹 = 这把公钥的 SHA-256"),
    ("IK_dh", "长期「协商」身份钥", "X25519。只做 DH 协商、从不签名，与 IK_sign 职责与泄露面分开"),
    ("SPK", "签名预密钥", "中期预密钥，被 IK_sign 签名；对方用前先验签，失败直接拒绝握手"),
    ("OPK", "一次性预密钥", "用完即删；池中少于 5 把自动补满；私钥延迟到首条密文认证成功才删"),
    ("PQK", "长期后量子公钥", "ML-KEM-768。握手与每条新棘轮链都向它封装"),
    ("PQOPK", "一次性后量子预密钥", "握手优先用它，用完即删；缺了它才退到长期 PQK"),
]
for i, (n, h, b) in enumerate(cards):
    x = 0.50 + i * 1.53
    bx(s, x, 1.36, 1.44, 2.20,
       [[(n, 12.5, True, RED)], [(h, 9.5, True, INK)], [(b, 8.5, False, GRAY)]],
       fill=FILL, space_after=3, ls=1.12)
bx(s, 0.50, 3.74, 9.00, 0.62,
   [[("本地保险库：", 10.5, True, INK),
     ("全部私钥 + 全部棘轮状态一起加密落盘 —— 口令经 PBKDF2-HMAC-SHA256（600,000 次迭代 + 16 字节随机盐）派生 32 字节密钥，再以 AES-256-GCM 封存", 10.5, False, INK)]],
   fill=GRNF, line=GRNB, ls=1.15)
tx(s, 0.50, 4.48, 9.00, 0.35,
   [[("服务器不保存口令：口令遗忘即保险库无法打开，这是端到端设计的固有代价。", 10, False, GRAY)]])
takeaway(s, "公钥可以公开（放在服务器目录里）；私钥永远只留在自己设备的保险库里")

# ---- Slide 12 · handshake ----
s = slide(12); remove_pictures(s)
furniture(s, "03 · 协议设计", "第一次握手：X3DH（四次 DH）+ PQXDH（后量子封装）→ 同一把 SK")
steps = [
    ("1 · 取公钥包", "Alice 向服务器取 Bob 的 bundle：IK / SPK / OPK / PQK / PQOPK 的公钥"),
    ("2 · 先验签", "用 IK_sign 验证 SPK 上的签名；验不过 → 拒绝（防服务器塞无背书的预密钥）"),
    ("3 · 生成临时钥 EK", "Alice 生成只用一次的临时钥，EK 私钥用完即弃，给本次握手加「一次性」"),
    ("4 · 四次 DH", "DH1 身份↔SPK · DH2 临时↔身份 · DH3 临时↔SPK · DH4 临时↔OPK（有 OPK 时）"),
    ("5 · 后量子封装", "对 PQOPK（优先）或 PQK 做 ML-KEM 封装，得到后量子共享秘密与封装密文 ct"),
    ("6 · 合成 SK", "DH 材料 ‖ PQ 秘密 ‖ SHA-256（封装公钥），经 HKDF-SHA256 派生 SK"),
]
for i, (h, b) in enumerate(steps):
    y = 1.34 + i * 0.60
    bx(s, 0.50, y, 6.55, 0.52,
       [[(h + "　", 10.5, True, RED), (b, 9.8, False, INK)]], fill=FILL, ls=1.05,
       anchor=MSO_ANCHOR.MIDDLE)
    if i < 5:
        arrow_d(s, 1.05, y + 0.50, 0.13, 0.12, GRAY)
bx(s, 7.25, 1.34, 2.25, 2.30,
   [[("初始消息", 11.5, True, INK)],
    [("EK 公钥 + ct + 第一条棘轮密文，整份握手材料被 IK_sign 的签名覆盖", 9.5, False, GRAY)]],
   fill=FILLD, line=BLUB, space_after=3, ls=1.15)
bx(s, 7.25, 3.80, 2.25, 1.10,
   [[("Bob 同算", 11.5, True, INK)],
    [("用私钥做同样的四次 DH + 解封装，算出同一把 SK（双方字节级一致）", 9.5, False, GRAY)]],
   fill=GRNF, line=GRNB, space_after=3, ls=1.15)
takeaway(s, "SK 只是双棘轮的「种子」：它从不直接加密任何一条消息")

# ---- Slide 14 · ratchet ----
s = slide(14); remove_pictures(s)
furniture(s, "03 · 协议设计", "双棘轮：DH 棘轮管「换链自愈」，对称棘轮管「逐条换钥」")
tx(s, 0.50, 1.30, 9.00, 0.32, [[("DH 棘轮（换链）：对方一回复，双方各换一把新的临时棘轮钥", 11.5, True, INK)]])
chain = [("RK0", "由 SK 初始化"), ("RK1", "新 DH 输出经 HKDF（dr-v1）"), ("RK2", "再回复，再换链 ……")]
for i, (n, b) in enumerate(chain):
    x = 0.50 + i * 3.05
    bx(s, x, 1.68, 2.55, 0.62,
       [[(n + "　", 12, True, RED), (b, 9.5, False, GRAY)]], fill=FILL,
       anchor=MSO_ANCHOR.MIDDLE, ls=1.05)
    if i < 2:
        arrow_r(s, x + 2.60, 1.90, 0.36, 0.16, RED)
tx(s, 0.50, 2.44, 9.00, 0.55,
   [[("破密恢复（自愈）成立的准确时间点：", 10.5, True, INK),
     ("对方刚回复、双方都换过新棘轮公钥之后。混合棘轮（pq-dr-v1）：每条新链除 DH 输出外，再对对方长期 PQK 做一次新鲜 ML-KEM 封装。", 10.5, False, INK)]], ls=1.15)
tx(s, 0.50, 3.06, 9.00, 0.32, [[("对称棘轮（同一链内逐条滚动）：链钥 CK 像一次性楼梯，只能向前、不能倒退", 11.5, True, INK)]])
sym = [("链钥 CK", "当前链状态"), ("MK（消息钥）", "HMAC 0x01 推出，用一条删一条"), ("密文", "AES-256-GCM 加密后发出")]
for i, (n, b) in enumerate(sym):
    x = 0.50 + i * 3.05
    bx(s, x, 3.44, 2.55, 0.62,
       [[(n + "　", 11, True, RED), (b, 9.5, False, GRAY)]], fill=FILL,
       anchor=MSO_ANCHOR.MIDDLE, ls=1.05)
    if i < 2:
        arrow_r(s, x + 2.60, 3.66, 0.36, 0.16, RED)
tx(s, 0.50, 4.18, 9.00, 0.35,
   [[("HMAC 是单向的：今天的链钥泄露，也倒推不回昨天已删除的 MK —— 这就是前向安全。", 10.5, False, INK)]])
takeaway(s, "消息层三件套：乱序 MK 进「跳过缓存」（上限 40）· 已处理序号重放直接拒绝 · 解密先在副本上试算，GCM 成功才提交状态（原子提交）")

# ---- Slide 17 · group ----
s = slide(17); remove_pictures(s)
furniture(s, "03 · 协议设计", "群聊：逐人信封（不用 Sender Keys）+ 签名哈希链管成员名单")
bx(s, 0.50, 1.36, 2.20, 1.30,
   [[("Alice 的一条群消息", 11.5, True, INK)],
    [("同一段明文，逐人各加密一份，每份走与收件人的两人双棘轮", 9.5, False, GRAY)]],
   fill=FILLD, line=BLUB, space_after=3, ls=1.15)
for i, name in enumerate(["Bob", "Carol", "Dave"]):
    y = 1.36 + i * 0.50
    arrow_r(s, 2.78, y + 0.10, 0.32, 0.14, RED)
    bx(s, 3.16, y, 2.30, 0.42,
       [[(f"信封 → {name}", 10.5, True, INK), ("（只有 ta 能解开）", 9, False, GRAY)]],
       fill=FILL, anchor=MSO_ANCHOR.MIDDLE)
bx(s, 5.75, 1.36, 3.75, 1.42,
   [[("代价与边界（主动声明）", 11, True, RED)],
    [("成本 O(n)：n 人群每条消息发 n−1 封 → 群上限 8 人；换回逐对前向安全 + 破密恢复；文件只上传一份密文，文件钥逐人分发", 9.5, False, INK)]],
   fill=REDF, line=REDB, space_after=3, ls=1.15)
tx(s, 0.50, 2.98, 9.00, 0.32,
   [[("成员名单：签名哈希链 —— 服务器说了不算，客户端自己验", 11.5, True, INK)]])
states = [("状态 0（创世）", "创建者签名 · 成员：Alice、Bob"),
          ("状态 1（纪元 +1）", "拉 Carol 进群（只增一人）· 带前驱哈希 · 现成员签名"),
          ("状态 2（纪元 +1）", "拉 Dave 进群 · 带前驱哈希 · 现成员签名")]
for i, (n, b) in enumerate(states):
    x = 0.50 + i * 3.05
    bx(s, x, 3.36, 2.55, 0.72,
       [[(n, 10.5, True, RED)], [(b, 9, False, GRAY)]], fill=FILL, space_after=2, ls=1.1)
    if i < 2:
        arrow_r(s, x + 2.60, 3.64, 0.36, 0.16, RED)
tx(s, 0.50, 4.24, 9.00, 0.55,
   [[("每条群消息都带「所用状态的哈希」：伪造名单、幽灵成员、名单分歧 → 哈希对不上或签名不对 → 客户端直接拒绝。", 10.5, False, INK)]], ls=1.15)
takeaway(s, "回应 EuroS&P 2018《More is Less》：Sender Keys 让名单与正文都失去端到端保护 —— 我们两条都补上")

# ---- Slide 19 · fingerprint ----
s = slide(19); remove_pictures(s)
furniture(s, "04 · 安全分析", "指纹核对：不核对时服务器能做什么，核对后还剩什么")
panels = [
    ("① 诚实目录（正常情况）", FILL, BORD,
     ["Alice 拿到 Bob 的真公钥包", "双方算出同一把 SK", "服务器只转发，看不懂"]),
    ("② 换包攻击（从不核对指纹）", REDF, REDB,
     ["服务器把 Bob 的公钥整套换成攻击者 M 的", "Alice↔M 一条会话、M↔Bob 另一条", "M 居中转发，两边明文都可读"]),
    ("③ 防线：指纹 + 本地钉住", GRNF, GRNB,
     ["指纹 = IK_sign 公钥的 SHA-256，16 组十六进制", "线下核对（当面 / 电话）", "首次取得后钉住，再变 → 拒绝 + 告警"]),
]
for i, (h, f, ln, items) in enumerate(panels):
    x = 0.50 + i * 3.05
    paras = [[(h, 11, True, RED if i == 1 else INK)]]
    for it in items:
        paras.append([("· " + it, 9.8, False, INK)])
    bx(s, x, 1.36, 2.90, 1.95, paras, fill=f, line=ln, space_after=4, ls=1.15)
tx(s, 0.50, 3.52, 9.00, 0.35,
   [[("为什么这是所有无中心目录的 E2EE 共同软肋", 11.5, True, INK)]])
tx(s, 0.50, 3.88, 9.00, 0.95,
   [[("挑战应答登录只能证明「你持有服务器当初收下的那把私钥」—— 若第一次注册时公钥就被换掉，证明链从源头就断了。所以 Signal 也靠安全码线下核对；我们能做的是把攻击窗口压缩到「第一次接触之前」，并在 README 与报告中明说。", 10.5, False, INK)]], ls=1.2)
takeaway(s, "核对完指纹之后，服务器就只剩下「转发」和「漏投」两种能力，读不到、改不了、冒充不了")

# ============ NOTES: remove live-demo language ============
REPL = [
    ("——有个演示脚本能把论文结论逐条对到函数，老师感兴趣可以现场跑", "，并与实现逐项对应"),
    ("这一段有现场演示：demo_attack.py，掉包之后 Alice 算出的 SK 等于攻击者的、不等于 Bob 的，一跑就明白。",
     "我们用攻击演示验证过这一段：掉包之后，Alice 算出的 SK 等于攻击者的、不等于 Bob 的，结论与威胁模型一致。"),
    ("三个可现场跑的攻击演示", "三个攻击演示"),
    ("我们有一个演示脚本，现场可以跑：", "我们做过换包攻击的演示验证："),
]
for s in prs.slides:
    if not s.has_notes_slide:
        continue
    tf = s.notes_slide.notes_text_frame
    for p in tf.paragraphs:
        for r in p.runs:
            for old, new in REPL:
                if old in r.text:
                    r.text = r.text.replace(old, new)
    full = tf.text
    for old, new in REPL:
        if old in full:  # phrase spans runs: fall back to whole-text rewrite
            tf.text = full.replace(old, new)
            break

prs.save(SRC)
print("deck rebuilt and saved")
