# -*- coding: utf-8 -*-
"""ECNUchat, Inc. — Nasdaq listing introduction deck.
All content is native PowerPoint text/shapes/tables (fully editable).
Only the logo is a picture."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy

INK = RGBColor(0x0E, 0x11, 0x17)
RED = RGBColor(0xA6, 0x1E, 0x36)
DARK = RGBColor(0x26, 0x26, 0x26)
GRAY = RGBColor(0x59, 0x59, 0x59)
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
LGRAY = RGBColor(0xD9, 0xD9, 0xD9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Microsoft YaHei"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = 13.333, 7.5

def slide():
    return prs.slides.add_slide(BLANK)

def _set_font(run, size, bold=False, color=DARK, name=FONT):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.name = name
    f.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        e = rPr.find(qn("a:" + tag))
        if e is None:
            e = rPr.makeelement(qn("a:" + tag), {}); rPr.append(e)
        e.set("typeface", name)

def tx(s, x, y, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
       space_after=6, line_spacing=1.12):
    """lines: list of paragraphs; each is a list of (text, size, bold, color) runs
    or a dict {runs:[...], align:..., space_before:...}."""
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(lines):
        opts = {}
        if isinstance(para, dict):
            opts = para; runs = para["runs"]
        else:
            runs = para
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = opts.get("align", align)
        p.space_after = Pt(opts.get("space_after", space_after))
        if opts.get("space_before"):
            p.space_before = Pt(opts["space_before"])
        p.line_spacing = opts.get("line_spacing", line_spacing)
        for (t, sz, b, c) in runs:
            r = p.add_run(); r.text = t; _set_font(r, sz, b, c)
    return box

def rect(s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, line_w=0.75):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid(); sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line; sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    return sp

def shape_text(sp, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
               ml=0.14, mr=0.14, mt=0.10, mb=0.06, space_after=4, line_spacing=1.1):
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(ml); tf.margin_right = Inches(mr)
    tf.margin_top = Inches(mt); tf.margin_bottom = Inches(mb)
    for i, runs in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        for (t, sz, b, c) in runs:
            r = p.add_run(); r.text = t; _set_font(r, sz, b, c)

PAGE = [0]
def content_slide(title, subtitle=None):
    s = slide()
    rect(s, 0, 0, SW, SH, fill=WHITE)
    tx(s, 0.62, 0.42, 12.1, 0.62, [[(title, 25, True, INK)]])
    rect(s, 0.64, 1.12, 0.85, 0.045, fill=RED)
    y = 1.32
    if subtitle:
        tx(s, 0.62, y, 12.1, 0.4, [[(subtitle, 13, False, GRAY)]])
        y += 0.42
    PAGE[0] += 1
    rect(s, 0.62, 7.06, 12.09, 0.012, fill=LGRAY)
    tx(s, 0.62, 7.12, 6.0, 0.3, [[("ECNUchat, Inc.", 9, False, GRAY)]])
    tx(s, 11.2, 7.12, 1.5, 0.3, [[(str(PAGE[0] + 1), 9, False, GRAY)]],
       align=PP_ALIGN.RIGHT)
    return s, y

def bullets(items, size=13.5, gap=10, lh=1.18):
    out = []
    for head, body in items:
        runs = [("•  ", size, True, RED)]
        if head:
            runs.append((head, size, True, INK))
        runs.append((body, size, False, DARK))
        out.append({"runs": runs, "space_after": gap, "line_spacing": lh})
    return out

def styled_table(s, x, y, w, rows, col_w, header=True, fsize=12.5, row_h=0.44,
                 head_h=0.46):
    gt = s.shapes.add_table(len(rows), len(col_w), Inches(x), Inches(y),
                            Inches(w), Inches(row_h * len(rows))).table
    for i, cw in enumerate(col_w):
        gt.columns[i].width = Inches(cw)
    for ri, row in enumerate(rows):
        gt.rows[ri].height = Inches(head_h if (header and ri == 0) else row_h)
        for ci, val in enumerate(row):
            cell = gt.cell(ri, ci)
            cell.margin_left = Inches(0.12); cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if header and ri == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = INK
            elif ri % 2 == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = WHITE
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb = LIGHT
            tf = cell.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            r = p.add_run(); r.text = val
            if header and ri == 0:
                _set_font(r, fsize, True, WHITE)
            elif ci == 0:
                _set_font(r, fsize, True, INK)
            else:
                _set_font(r, fsize, False, DARK)
    return gt

LOGO = "/home/hatch/workspace/ecnuchat-prospectus/logo-mark.png"

# ---------------- 1 · COVER ----------------
s = slide()
rect(s, 0, 0, SW, SH, fill=WHITE)
rect(s, 0, 0, SW, 0.14, fill=INK)
s.shapes.add_picture(LOGO, Inches(5.92), Inches(0.95), Inches(1.5), Inches(1.5))
tx(s, 1.2, 2.72, 10.93, 0.9, [[("ECNUchat, Inc.", 40, True, INK)]],
   align=PP_ALIGN.CENTER)
tx(s, 1.2, 3.62, 10.93, 0.7,
   [[("首次公开发行股票并在纳斯达克上市项目介绍", 24, True, RED)]],
   align=PP_ALIGN.CENTER)
tx(s, 1.2, 4.42, 10.93, 0.45,
   [[("Initial Public Offering on the Nasdaq Global Market", 14, False, GRAY)]],
   align=PP_ALIGN.CENTER)
rect(s, 6.24, 5.14, 0.85, 0.045, fill=RED)
tx(s, 1.2, 5.42, 10.93, 0.4,
   [[("上市市场：纳斯达克全球市场（Nasdaq Global Market）　股票代码：ECNC", 13.5, False, DARK)]],
   align=PP_ALIGN.CENTER)
tx(s, 1.2, 6.55, 10.93, 0.4, [[("2026 年 11 月", 12, False, GRAY)]],
   align=PP_ALIGN.CENTER)

# ---------------- 2 · 公司简介 ----------------
s, y = content_slide("公司简介", "端到端加密通信平台")
tx(s, 0.62, y + 0.08, 7.35, 4.6, bullets([
    ("公司概况：", "ECNUchat, Inc. 于 2026 年 3 月在美国特拉华州注册成立，运营总部位于上海，专注于端到端加密通信技术与产品。"),
    ("核心产品：", "ECNUchat 端到端加密聊天平台，覆盖一对一聊天、群组聊天、加密附件与语音通话，服务器仅承担公钥分发与密文中继，不接触任何明文内容。"),
    ("技术路线：", "协议层完整实现 X3DH 密钥协商、PQXDH 后量子混合握手与双棘轮算法，采用经公开学术分析验证的协议构造。"),
    ("发展阶段：", "公司已完成第二代平台（v2）的开发，支持 PWA 与多中继部署，现正推进首次公开发行及上市工作。"),
], size=13.5, gap=12))
stats = [("2026 年 3 月", "公司成立"), ("上海", "运营总部"),
         ("纳斯达克全球市场", "上市市场"), ("ECNC", "股票代码")]
for i, (v, k) in enumerate(stats):
    bx = 8.35 + (i % 2) * 2.22
    by = y + 0.12 + (i // 2) * 1.62
    sp = rect(s, bx, by, 2.05, 1.42, fill=LIGHT)
    shape_text(sp, [[(v, 15.5, True, INK)], [(k, 11.5, False, GRAY)]],
               align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=3)

# ---------------- 3 · 发行概况 ----------------
s, y = content_slide("本次发行概况")
rows = [
    ["项目", "内容"],
    ["发行人", "ECNUchat, Inc."],
    ["发行股票类型", "A 类普通股（Class A Common Stock）"],
    ["发行股数", "50,000,000 股"],
    ["超额配售选择权", "7,500,000 股（承销商可于发行后 30 日内行使）"],
    ["发行价格区间", "每股 28.00 美元至 32.00 美元"],
    ["上市市场与代码", "纳斯达克全球市场（Nasdaq Global Market），代码 ECNC"],
    ["预计募集资金净额", "约 13.77 亿美元（按发行价中值 30.00 美元计算）"],
    ["发行后总股本", "600,000,000 股（A 类 200,000,000 股，B 类 400,000,000 股）"],
    ["发行后公司市值", "约 180 亿美元（按发行价中值计算）"],
]
styled_table(s, 0.62, y + 0.10, 12.09, rows, [3.1, 8.99], fsize=12.5, row_h=0.47)

# ---------------- 4 · 募集资金用途 ----------------
s, y = content_slide("募集资金用途", "本次发行募集资金净额拟用于以下方面")
uses = [
    ("研究与开发", "完成第二代平台建设，推进多设备支持与元数据保护功能，并委托独立第三方开展安全审计。"),
    ("中继基础设施", "扩充并加固全球中继节点网络，提升系统可用性与抗攻击能力。"),
    ("市场拓展", "开展销售、市场推广与用户拓展，扩大产品覆盖与品牌影响。"),
    ("营运资金及其他", "补充营运资金及用于其他一般公司用途；并可能用于收购或投资互补性业务、产品与技术。"),
]
for i, (h, b) in enumerate(uses):
    by = y + 0.18 + i * 1.16
    rect(s, 0.62, by + 0.05, 0.30, 0.30, fill=RED)
    tx(s, 0.62, by + 0.015, 0.30, 0.36, [[(str(i + 1), 13, True, WHITE)]],
       align=PP_ALIGN.CENTER)
    tx(s, 1.12, by, 11.6, 1.05, [
        [(h, 15, True, INK)],
        {"runs": [(b, 12.5, False, DARK)], "space_after": 0, "line_spacing": 1.15},
    ], space_after=2)

# ---------------- 5 · 技术体系 ----------------
s, y = content_slide("核心技术体系", "协议构造均有公开学术文献的安全分析支持")
cards = [
    ("密钥协商 · X3DH", "基于 X25519 的四次 Diffie-Hellman 运算完成异步密钥协商，配合 HKDF-SHA256 派生会话密钥，支持在对方离线时建立加密会话。"),
    ("后量子混合握手 · PQXDH", "在 X3DH 之上并入 ML-KEM-768 密钥封装，经典与后量子双算法混合，抵御“先存储、后解密”的未来量子攻击。"),
    ("双棘轮算法 · Double Ratchet", "每条消息使用独立密钥并即时销毁，兼具前向保密与破密恢复能力；支持乱序消息解密与跳跃密钥缓存。"),
    ("对称加密与签名", "消息与附件采用 AES-256-GCM 认证加密，身份与状态签名采用 Ed25519，附件实行第二层独立加密。"),
]
for i, (h, b) in enumerate(cards):
    bx = 0.62 + (i % 2) * 6.17
    by = y + 0.16 + (i // 2) * 2.28
    sp = rect(s, bx, by, 5.92, 2.08, fill=WHITE, line=LGRAY, line_w=1.0)
    rect(s, bx, by, 5.92, 0.07, fill=RED)
    shape_text(sp, [[(h, 15, True, INK)], [(b, 12, False, DARK)]],
               ml=0.2, mr=0.2, mt=0.22, space_after=5, line_spacing=1.18)

# ---------------- 6 · 产品与安全架构 ----------------
s, y = content_slide("产品与安全架构")
tx(s, 0.62, y + 0.06, 5.95, 4.9, bullets([
    ("一对一会话：", "经 X3DH/PQXDH 握手建立，双棘轮持续更新密钥。"),
    ("群组会话：", "按每位收件人分别以双棘轮信封投递，不使用共享发送者密钥。"),
    ("群状态保护：", "成员名单以签名加哈希链方式维护，中继服务器无法伪造或篡改。"),
    ("身份核验：", "每位用户设有安全指纹，可通过带外渠道核对，防范中间人攻击。"),
], size=13, gap=11))
tx(s, 6.85, y + 0.06, 5.85, 4.9, bullets([
    ("加密附件：", "在会话加密之外再施加一层 AES-256-GCM 加密，分块传输。"),
    ("语音通话：", "通话密钥经双棘轮信道协商派生，不经过服务器明文。"),
    ("密钥保管：", "本地密钥库采用 PBKDF2-HMAC-SHA256（600,000 次迭代）口令派生加密。"),
    ("服务器零明文：", "中继仅存储公钥与密文信封，登录采用挑战—应答方式，不传输口令。"),
], size=13, gap=11))

# ---------------- 7 · 研发与工程实力 ----------------
s, y = content_slide("研发与工程实力")
rstats = [("约 20,000 行", "核心代码规模（Python）"), ("95 个", "自动化测试用例"),
          ("12 / 12", "后量子互操作验证通过"), ("2 代", "平台版本迭代（v1 / v2）")]
for i, (v, k) in enumerate(rstats):
    bx = 0.62 + i * 3.10
    sp = rect(s, bx, y + 0.16, 2.90, 1.30, fill=LIGHT)
    shape_text(sp, [[(v, 17, True, RED)], [(k, 11, False, GRAY)]],
               align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=3)
tx(s, 0.62, y + 1.85, 12.09, 3.2, bullets([
    ("完整的协议实现：", "握手、棘轮、群聊、附件与通话模块均自主实现，关键协议细节与已发表的安全分析逐项对齐。"),
    ("严格的工程规范：", "状态变更实行原子提交——仅在密文验证成功后更新会话状态，避免异常状态被持久化。"),
    ("持续的安全验证：", "配套攻击演示与一致性测试套件，覆盖降级攻击、重放攻击与群状态伪造等场景。"),
], size=13.5, gap=11))

# ---------------- 8 · 管理团队 ----------------
s, y = content_slide("管理团队与公司治理")
rows = [
    ["姓名", "职务"],
    ["钟浩", "联合创始人、董事长兼首席执行官、首席架构师"],
    ["吴泽霖", "联合创始人、董事，客户端应用工程负责人"],
    ["陈俊伟", "联合创始人、董事，中继基础设施工程负责人"],
    ["陈俊桥", "联合创始人、董事，平台工程负责人"],
]
styled_table(s, 0.62, y + 0.12, 12.09, rows, [2.6, 9.49], fsize=13, row_h=0.56)
tx(s, 0.62, y + 3.30, 12.09, 1.4, bullets([
    ("治理结构：", "公司采用双重股权结构，董事会由四位创始人组成；重大事项按公司章程及上市地规则履行审议程序。"),
], size=13, gap=0))

# ---------------- 9 · 股权结构 ----------------
s, y = content_slide("股权结构（本次发行后）")
rows = [
    ["类别", "股数", "占总股本", "每股表决权", "合计表决权占比"],
    ["A 类普通股", "200,000,000", "33.3%", "1 票", "约 4.8%"],
    ["B 类普通股", "400,000,000", "66.7%", "10 票", "约 95.2%"],
    ["合计", "600,000,000", "100%", "—", "100%"],
]
styled_table(s, 0.62, y + 0.12, 12.09, rows, [2.2, 2.6, 1.8, 2.2, 3.29], fsize=12.5,
             row_h=0.52)
tx(s, 0.62, y + 2.45, 12.09, 2.6, bullets([
    ("创始人持股：", "B 类普通股由四位创始人全数持有，其中钟浩持有 220,000,000 股，吴泽霖、陈俊伟、陈俊桥各持有 60,000,000 股。"),
    ("转换安排：", "B 类普通股可按 1:1 随时转换为 A 类普通股；创始人团队合计持有约 95.2% 的表决权，保障公司战略与技术路线的长期稳定。"),
], size=13, gap=10))

# ---------------- 10 · 发展规划 ----------------
s, y = content_slide("发展规划")
phases = [
    ("近期", "完成上市与股份登记；第二代平台持续迭代；启动独立第三方安全审计；推进多设备支持。"),
    ("中期", "上线元数据保护与密封发送者能力；完善群组治理（成员变更全流程）；推出面向团队与企业的协作版本。"),
    ("长期", "建设开放的加密通信基础设施；拓展国际市场与合规布局；保持协议层研发的持续投入。"),
]
for i, (h, b) in enumerate(phases):
    by = y + 0.18 + i * 1.42
    sp = rect(s, 0.62, by, 1.55, 1.16, fill=INK)
    shape_text(sp, [[(h, 15, True, WHITE)]], align=PP_ALIGN.CENTER,
               anchor=MSO_ANCHOR.MIDDLE)
    tx(s, 2.42, by + 0.06, 10.3, 1.1, [[(b, 13, False, DARK)]],
       line_spacing=1.2)

# ---------------- 11 · 风险因素概要 ----------------
s, y = content_slide("风险因素概要", "公司主要风险因素摘要如下，完整内容见招股说明书“风险因素”章节")
tx(s, 0.62, y + 0.10, 12.09, 4.4, bullets([
    ("经营历史有限：", "公司成立时间较短，尚未产生规模化收入，未来盈利能力存在不确定性。"),
    ("行业竞争：", "加密通信与即时通信市场竞争激烈，大型平台厂商在用户规模与资源上具备优势。"),
    ("监管与合规：", "加密产品在不同司法辖区面临出口管制、数据与行业监管政策变化的风险。"),
    ("技术与安全：", "密码协议与实现需持续应对新型攻击手段，安全事件可能对公司声誉造成重大影响。"),
    ("双重股权结构：", "创始人团队集中持有表决权，可能影响公司治理事项中其他股东的意愿表达。"),
], size=13.5, gap=11))

# ---------------- 12 · 结尾 ----------------
s = slide()
rect(s, 0, 0, SW, SH, fill=WHITE)
rect(s, 0, 7.36, SW, 0.14, fill=INK)
s.shapes.add_picture(LOGO, Inches(6.17), Inches(1.55), Inches(1.35), Inches(1.35))
tx(s, 1.2, 3.25, 10.93, 0.8, [[("谢谢", 34, True, INK)]], align=PP_ALIGN.CENTER)
tx(s, 1.2, 4.15, 10.93, 0.5,
   [[("ECNUchat, Inc.　·　纳斯达克全球市场　·　ECNC", 14, False, DARK)]],
   align=PP_ALIGN.CENTER)
tx(s, 1.2, 4.85, 10.93, 0.45,
   [[("公司网站：www.ecnuchat.com　投资者关系：investors.ecnuchat.com", 12, False, GRAY)]],
   align=PP_ALIGN.CENTER)

prs.save("/home/hatch/workspace/ecnuchat-prospectus/ECNUchat-Nasdaq-Introduction.pptx")
print("saved")
