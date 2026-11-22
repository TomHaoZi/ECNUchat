# -*- coding: utf-8 -*-
"""Simplification pass: less text, bigger fonts, same native shapes.
Rewrites selected shapes with condensed text; styles (bold/color/alignment)
are inherited from each shape's existing runs."""
from pptx import Presentation
from pptx.util import Pt

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)

def style_of(run):
    c = None
    try:
        if run.font.color and run.font.color.type is not None:
            c = run.font.color.rgb
    except Exception:
        pass
    return (run.font.bold or False, c)

def set_text(shape, paras):
    """paras: list of paragraphs; each = list of (text, size)."""
    tf = shape.text_frame
    old = []
    for p in tf.paragraphs:
        styles = [style_of(r) for r in p.runs] or [(False, None)]
        old.append((p.alignment, styles))
    # clear all paragraphs
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

def bump(shape, delta, cap=30.0):
    if shape.has_text_frame:
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size:
                    r.font.size = Pt(min(r.font.size.pt + delta, cap))
    if shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                for p in cell.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size:
                            r.font.size = Pt(min(r.font.size.pt + delta, cap))

def S(n):
    return prs.slides[n - 1]

def shp(n, idx):
    return S(n).shapes[idx]

# ---------- global furniture: labels 9->10.5, titles 19->23, page nums 9->10.5 ----------
for s in prs.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if not t:
            continue
        y, x = sh.top.inches, sh.left.inches
        if abs(y - 0.34) < 0.05 and abs(x - 1.12) < 0.05 and len(t) < 30:
            bump(sh, 1.5)
        elif abs(y - 0.62) < 0.05 and abs(x - 1.12) < 0.05:
            bump(sh, 4.0)
        elif abs(y - 0.34) < 0.08 and abs(x - 8.55) < 0.05:
            bump(sh, 1.5)
        elif abs(y - 0.30) < 0.05 and abs(x - 8.55) < 0.05:
            bump(sh, 1.5)

# ---------- Slide 2 · outline ----------
for idx in (3, 6, 9, 12, 15, 18):
    bump(shp(2, idx), 4.0)
for idx in (4, 7, 10, 13, 16, 19):
    bump(shp(2, idx), 2.0)
for idx in (5, 8, 11, 14, 17, 20):
    bump(shp(2, idx), 1.5)

# ---------- Slide 3 · background ----------
set_text(shp(3, 3), [[("即时通讯的默认形态是「服务器能看明文」。本项目把信任从服务器手里拿回来：", 14)]])
set_text(shp(3, 7), [[("X25519 椭圆曲线 DH：不传私钥，双方算出同一段共享秘密", 12)]])
set_text(shp(3, 11), [[("每条消息一把独立钥匙：保密 + 完整性，改一字节即被发现", 12)]])
set_text(shp(3, 15), [[("Ed25519 只签名不协商：签预密钥、签初始消息、签登录挑战", 12)]])
for idx in (6, 10, 14):
    bump(shp(3, idx), 2.0)
set_text(shp(3, 16), [
    [("▪ ", 12.5), ("安全目标：防窃听、防篡改、防冒充；密钥泄露时把损失限制在最小时间窗", 12.5)],
    [("▪ ", 12.5), ("设计立场：服务器只存公钥、转发密文——看得到谁在和谁通信，看不懂内容", 12.5)],
])

# ---------- Slide 4 · requirements ----------
bump(shp(4, 5), 2.0); bump(shp(4, 9), 2.0)
set_text(shp(4, 6), [
    [("账户与身份：口令解锁保险库，登录用签名挑战应答", 12)],
    [("一对一私聊：离线消息暂存、上线补投", 12)],
    [("群聊：8 人以内，成员变更可验证", 12)],
    [("富媒体：图片 / 文件（≤8GiB）、语音消息、语音通话", 12)],
    [("双端一致：桌面端与终端端共用同一引擎", 12)],
])
set_text(shp(4, 10), [
    [("机密性：服务器与窃听者不可见正文与文件", 12)],
    [("完整性与认证：逐条 AEAD 校验 + Ed25519 签名", 12)],
    [("前向安全：单条消息钥泄露不殃及其余", 12)],
    [("破密恢复：状态泄露后随往返自动恢复", 12)],
    [("抗重放 / 抗篡改 / 抗降级", 12)],
    [("目录安全：指纹核对 + 身份钉住防换包", 12)],
])
set_text(shp(4, 11), [
    [("▪ ", 12), ("需求来源：课程题目三点逐项展开；威胁假设：服务器可作恶、网络可窃听篡改、终端可能被短时攻破", 12)],
    [("▪ ", 12), ("范围约束：单设备使用；社交元数据保护不在本期范围（已知边界）", 12)],
])

# ---------- Slide 5 · literature table ----------
bump(shp(5, 3), 2.0)
bump(shp(5, 4), 2.0)

# ---------- Slide 6 · architecture content ----------
set_text(shp(6, 3), [
    [("▪ ", 12.5), ("界面层只显示与输入，不接触链钥匙；ChatEngine 决定何时建会话、何时换链", 12.5)],
    [("▪ ", 12.5), ("密码模块纯字节进出、可离线单测；服务器只存公钥与离线信封，按用户名转发", 12.5)],
])
for idx in (4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 18, 19, 20, 21, 22):
    bump(shp(6, idx), 1.0)

# ---------- Slide 7 · architecture diagram ----------
for idx in range(3, 23):
    try:
        bump(shp(7, idx), 2.0)
    except Exception:
        pass

# ---------- Slide 8 · keys content ----------
set_text(shp(8, 3), [
    [("三把长期钥", 13.5)],
    [("IK_sign（Ed25519）只签名；IK_dh（X25519）只协商；SPK 用前先验签。", 13)],
    [("一次性钥", 13.5)],
    [("OPK ×20：用完即删，少于 5 把补满。后量子再加 PQK + PQOPK ×8（ML-KEM-768）。", 13)],
])
set_text(shp(8, 4), [
    [("▪ ", 12.5), ("验签三时机：注册入库前、发起会话前、登录挑战应答——服务器不保存口令", 12.5)],
    [("▪ ", 12.5), ("私钥落盘：PBKDF2-HMAC-SHA256（60 万次）派生钥，AES-256-GCM 封存", 12.5)],
    [("▪ ", 12.5), ("身份钉住：身份公钥首次取得后本地固定，之后变化即拒绝并告警", 12.5)],
])
for idx in (5, 6, 7, 8):
    bump(shp(8, idx), 1.5)
set_text(shp(8, 9), [[("落盘：", 10.5), ("口令经 PBKDF2（60 万次）派生密钥，AES-256-GCM 封存全部私钥", 10.5)]])

# ---------- Slide 9 · keys diagram ----------
trims9 = {
    3: [[("IK_sign", 14)], [("长期「签名」身份钥", 11)], [("Ed25519。签 SPK、签初始消息、签群状态；指纹 = 公钥的 SHA-256", 10)]],
    4: [[("IK_dh", 14)], [("长期「协商」身份钥", 11)], [("X25519。只做 DH 协商、从不签名，与 IK_sign 分开", 10)]],
    5: [[("SPK", 14)], [("签名预密钥", 11)], [("被 IK_sign 签名；用前先验签，失败直接拒绝握手", 10)]],
    6: [[("OPK", 14)], [("一次性预密钥", 11)], [("用完即删；少于 5 把自动补满；私钥延迟到首条密文认证成功才删", 10)]],
    7: [[("PQK", 14)], [("长期后量子公钥", 11)], [("ML-KEM-768。握手与每条新棘轮链都向它封装", 10)]],
    8: [[("PQOPK", 14)], [("一次性后量子预密钥", 11)], [("握手优先用它，用完即删；缺了才退到长期 PQK", 10)]],
}
for idx, paras in trims9.items():
    set_text(shp(9, idx), paras)
bump(shp(9, 9), 1.0)

# ---------- Slide 10 · X3DH content ----------
set_text(shp(10, 3), [
    [("▪ ", 12.5), ("DH1 绑长期身份与已签名 SPK——服务器塞不进无背书的预密钥", 12.5)],
    [("▪ ", 12.5), ("DH3 让长期钥日后泄露也重算不出；DH4 用掉一把一次性预密钥（有才算）", 12.5)],
    [("▪ ", 12.5), ("SK = HKDF-SHA256（DH1‖DH2‖DH3[‖DH4]，info = “x3dh-v1”）；SK 只启动双棘轮", 12.5)],
])
for idx in (4, 6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 21, 22, 23):
    bump(shp(10, idx), 2.0)
bump(shp(10, 24), 2.0)

# ---------- Slide 11 · PQXDH ----------
set_text(shp(11, 3), [[("威胁：「先记录、后解密」——今天存下握手密文，等量子计算机成熟后打破 X25519。对策：在经典 DH 之外再并入一次后量子封装。", 13.5)]])
bump(shp(11, 5), 1.5)
set_text(shp(11, 6), [
    [("▪ ", 13), ("优先一次性 PQOPK，用完即删；取不到才退到长期 PQK", 13)],
    [("▪ ", 13), ("防降级：双方都支持 PQ 时，缺 KEM 的握手直接拒绝", 13)],
    [("▪ ", 13), ("签名全覆盖：封装公钥与 KEM 密文都在签名范围内", 13)],
    [("▪ ", 13), ("实现：ML-KEM-768（Python cryptography ≥44）；域标签 x3dh-v1 / pqxdh-v1 分离", 13)],
])

# ---------- Slide 12 · handshake diagram ----------
for idx in (3, 4, 5, 6, 7, 8):
    bump(shp(12, idx), 1.5)
set_text(shp(12, 3), [[("1 · 取公钥包　", 12), ("Alice 向服务器取 Bob 的 bundle（五类公钥）", 11.5)]])
set_text(shp(12, 5), [[("3 · 生成临时钥 EK　", 12), ("只用一次，私钥用完即弃", 11.5)]])
bump(shp(12, 9), 1.5); bump(shp(12, 10), 1.5)

# ---------- Slide 13 · ratchet content ----------
set_text(shp(13, 3), [
    [("▪ ", 12.5), ("对称棘轮：MK = HMAC(ck, 0x01)，用后即删 —— 前向安全", 12.5)],
    [("▪ ", 12.5), ("DH 棘轮：新 DH 输出换出新根钥与新链 —— 破密恢复", 12.5)],
    [("▪ ", 12.5), ("AAD 绑定双方、序号与棘轮公钥：挪窝、改序号、换公钥都会 GCM 失败", 12.5)],
])
for idx in (4, 5, 6, 7, 8, 9):
    bump(shp(13, idx), 1.5)

# ---------- Slide 14 · ratchet diagram ----------
bump(shp(14, 3), 1.5); bump(shp(14, 10), 1.5)
for idx in (4, 6, 8, 11, 13, 15):
    bump(shp(14, idx), 1.5)
set_text(shp(14, 9), [
    [("破密恢复（自愈）成立时点：", 11.5), ("对方刚回复、双方都换过棘轮公钥之后。混合棘轮（pq-dr-v1）：每条新链再对对方 PQK 做一次新鲜 ML-KEM 封装。", 11.5)],
])
bump(shp(14, 16), 1.0)

# ---------- Slide 15 · hybrid + message layer ----------
for idx in (5, 9, 13, 17):
    bump(shp(15, idx), 2.0)
set_text(shp(15, 6), [[("每开一条新发送链，除 DH 输出外再对对方 PQK 做一次新鲜 ML-KEM 封装；新链缺 pq_ct 直接拒绝，防剥封装降级。", 12.5)]])
set_text(shp(15, 10), [[("超前消息先把中间 MK 算出缓存（上限 40 把）；迟到消息取出即删；超限拒绝，防「巨大序号」耗尽攻击。", 12.5)]])
set_text(shp(15, 14), [[("已处理的 (dh_pub, n) 再次出现直接拒绝；改密文 / nonce / AAD 任一字节，GCM 认证失败并给出安全提示。", 12.5)]])
set_text(shp(15, 18), [[("解密先在状态副本上试算，GCM 成功才提交；伪造包烧不掉合法消息的钥匙；OPK 私钥同样延迟删除。", 12.5)]])

# ---------- Slide 16 · group table ----------
bump(shp(16, 3), 2.0)
set_text(shp(16, 4), [
    [("▪ ", 12.5), ("签名哈希链：每次拉人纪元 +1、只增一人、前驱哈希指向上状态、签署者须为现有成员", 12.5)],
    [("▪ ", 12.5), ("群消息带所用状态哈希：伪造名单、幽灵成员、名单分歧都会暴露", 12.5)],
])

# ---------- Slide 17 · group diagram ----------
for idx in (3, 5, 7, 9, 12, 14, 16):
    bump(shp(17, idx), 1.5)
set_text(shp(17, 10), [
    [("代价与边界（主动声明）", 12.5)],
    [("成本 O(n)：每条消息发 n−1 封 → 群上限 8 人；换回逐对前向安全 + 破密恢复；文件只传一份密文，钥逐人分发", 11)],
])
bump(shp(17, 11), 1.5); bump(shp(17, 17), 1.0)

# ---------- Slide 18 · threat model ----------
for idx in (4, 5):
    bump(shp(18, idx), 1.5)
set_text(shp(18, 3), [
    [("▪ ", 12.5), ("攻击：服务器换掉 Bob 的公钥再配自签身份，Alice 就会与攻击者建会话（中间人）", 12.5)],
    [("▪ ", 12.5), ("防线：指纹线下核对后身份公钥被钉住，再换即被拒；服务器只剩转发", 12.5)],
    [("▪ ", 12.5), ("验证：攻击演示已实际运行——掉包后 Alice 的 SK 等于攻击者的、不等于 Bob 的", 12.5)],
])

# ---------- Slide 19 · fingerprint diagram ----------
for idx in (3, 4, 5):
    bump(shp(19, idx), 1.5)
bump(shp(19, 6), 1.5)
set_text(shp(19, 7), [[("挑战应答只能证明「你持有服务器当初收下的那把私钥」——第一次注册时公钥若被换掉，证明链从源头就断了。Signal 也靠安全码线下核对；我们把攻击窗口压缩到「第一次接触之前」，并在报告中明说。", 11.5)]])

# ---------- Slide 20 · innovation ----------
for idx in (5, 9, 13, 17):
    bump(shp(20, idx), 2.0)
set_text(shp(20, 6), [[("基线 PQXDH 只保护握手。我们连每条新发送链都混入新鲜 ML-KEM 封装（pq-dr-v1），优先一次性 PQOPK，客户端拒绝降级。", 12.5)]])
set_text(shp(20, 10), [[("基线 Sender Keys 群链无 DH 棘轮、名单由服务器说了算。我们以 O(n) 成本换回逐对前向安全与破密恢复，成员变更可独立验签。", 12.5)]])
set_text(shp(20, 14), [[("初始消息签名覆盖全部握手材料（经典 + PQ）；身份公钥首次取得后本地钉住，目录换钥即被拒并告警。", 12.5)]])
set_text(shp(20, 18), [[("解密先在副本上试算、GCM 成功才原子提交；OPK 私钥延迟到首条密文认证成功后才删，堵住实现层攻击面。", 12.5)]])

# ---------- Slide 21 · progress ----------
bump(shp(21, 4), 2.0)
set_text(shp(21, 5), [
    [("▪ ", 12.5), ("规模：Python 源码约 2 万行；文件走第二层 AES-256-GCM（随机文件钥 + 8 MiB 分片）", 12.5)],
    [("▪ ", 12.5), ("诚实边界：社交数据（好友、朋友圈）在服务器明文存放——加密的是聊天正文与文件字节", 12.5)],
])

# ---------- Slide 22 · testing & roadmap ----------
for idx in (5, 9, 13):
    bump(shp(22, idx), 2.5)
set_text(shp(22, 6), [[("19 个测试文件：握手两条路径、棘轮乱序 / 重放 / 篡改、PQ 混合、群、附件、通话与安全回归", 12)]])
set_text(shp(22, 10), [[("公钥掉包中间人、伪造成员表、论文—代码对应三个演示，均已实际运行验证", 12)]])
set_text(shp(22, 14), [[("JS 端（PWA）与 v1 引擎后量子互操作全通；经典端连 PQ 对端被拒降级", 12)]])
bump(shp(22, 15), 2.0)
set_text(shp(22, 16), [
    [("▪ ", 12.5), ("v2 落地：生产部署（Cloudflare 中继 + WSS + 中继鉴权）、桌面打包", 12.5)],
    [("▪ ", 12.5), ("协议补强：语音媒体面、密封发送者、评估 Triple Ratchet", 12.5)],
    [("▪ ", 12.5), ("已知缺口：无多设备同步、无头加密、社交元数据可见、Triple Ratchet 未实现", 12.5)],
])

prs.save(SRC)
print("condensed deck saved")
