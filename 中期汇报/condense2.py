# -*- coding: utf-8 -*-
"""Round 2: even bigger fonts, even less text. Same helpers as condense.py."""
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

def bump(shape, delta, cap=34.0):
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

def set_cell(shape, ri, ci, text, size):
    cell = shape.table.rows[ri].cells[ci]
    for pa in cell.text_frame.paragraphs:
        if pa.runs:
            pa.runs[0].text = text
            for extra in pa.runs[1:]:
                extra.text = ""
            pa.runs[0].font.size = Pt(size)

def S(n):
    return prs.slides[n - 1]

def shp(n, idx):
    return S(n).shapes[idx]

# ---------- global: titles 23->26, labels/pagenums 10.5->12 ----------
for s in prs.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if not t:
            continue
        y, x = sh.top.inches, sh.left.inches
        if abs(y - 0.62) < 0.05 and abs(x - 1.12) < 0.05:
            bump(sh, 3.0)
        elif abs(y - 0.34) < 0.08 or abs(y - 0.30) < 0.05:
            bump(sh, 1.5)

# ---------- S2 outline ----------
for idx in (3, 6, 9, 12, 15, 18):
    bump(shp(2, idx), 6.0)
for idx in (4, 7, 10, 13, 16, 19):
    bump(shp(2, idx), 2.5)
descs2 = {5: "题目三句话 · 功能与安全需求", 8: "十篇论文构成的证据链", 11: "密钥体系 · 双棘轮 · 群聊",
          14: "威胁模型 · 中间人", 17: "双层后量子 · 逐人信封", 20: "功能与测试 · 期末路线"}
for idx, txt in descs2.items():
    set_text(shp(2, idx), [[(txt, 15)]])

# ---------- S3 background ----------
set_text(shp(3, 3), [[("即时通讯默认是「服务器能看明文」。本项目把信任从服务器手里拿回来：", 15.5)]])
for idx in (6, 10, 14):
    bump(shp(3, idx), 2.0)
set_text(shp(3, 7), [[("X25519：不传私钥，双方算出同一段共享秘密", 13.5)]])
set_text(shp(3, 11), [[("每条消息一把独立钥匙，改一字节即被发现", 13.5)]])
set_text(shp(3, 15), [[("Ed25519 只签名：签预密钥、签初始消息、签登录", 13.5)]])
set_text(shp(3, 16), [
    [("▪ ", 14), ("安全目标：防窃听、防篡改、防冒充；泄露时损失只限最小时间窗", 14)],
    [("▪ ", 14), ("设计立场：服务器只存公钥、转发密文，看不懂内容", 14)],
])

# ---------- S4 requirements ----------
bump(shp(4, 5), 2.5); bump(shp(4, 9), 2.5)
set_text(shp(4, 6), [
    [("账户与身份：口令解锁，签名挑战登录", 13.5)],
    [("一对一私聊：离线暂存、上线补投", 13.5)],
    [("群聊：8 人以内，成员变更可验证", 13.5)],
    [("富媒体：图片 / 文件（≤8GiB）、语音、通话", 13.5)],
    [("双端一致：桌面与终端共用同一引擎", 13.5)],
])
set_text(shp(4, 10), [
    [("机密性：服务器看不见正文与文件", 13.5)],
    [("完整性与认证：AEAD 校验 + 签名认人", 13.5)],
    [("前向安全：单条钥泄露不殃及其余", 13.5)],
    [("破密恢复：泄露后随往返自动恢复", 13.5)],
    [("抗重放 / 抗篡改 / 抗降级", 13.5)],
    [("目录安全：指纹核对 + 身份钉住", 13.5)],
])
set_text(shp(4, 11), [
    [("▪ ", 13.5), ("需求来源：课程题目三点逐项展开；假设服务器可作恶、网络可窃听篡改", 13.5)],
    [("▪ ", 13.5), ("范围约束：单设备；社交元数据不在本期范围（已知边界）", 13.5)],
])

# ---------- S5 literature table ----------
bump(shp(5, 3), 0.5)
set_cell(shp(5, 3), 2, 1, "Cohn-Gordon 等, CSF 2016（PCS 定义）", 11.5)
set_text(shp(5, 4), [[("读法：", 12.5), ("先证明 → 再扩展（后量子 / 群）→ 后原语；每篇都对应已实现的代码。", 12.5)]])
sh5 = shp(5, 4)
from pptx.util import Inches
sh5.top = Inches(5.14)

# ---------- S6 architecture content ----------
set_text(shp(6, 3), [
    [("▪ ", 14), ("界面层只显示与输入，不接触链钥匙；引擎决定何时建会话、何时换链", 14)],
    [("▪ ", 14), ("密码模块纯字节进出、可离线单测；服务器只存公钥与信封", 14)],
])
for idx in (4, 11, 18):
    bump(shp(6, idx), 1.0)
mini6 = {5: "只显示已解开的明文", 6: "登录、收发信封、保存会话", 7: "每条消息 AES-256-GCM", 8: "口令封存私钥与状态",
         12: "身份公钥、签名、预密钥", 13: "按用户名转发信封", 14: "对方不在线先暂存", 15: "口令、私钥、明文、SK、MK",
         19: "用私钥重算共享秘密", 20: "签名不对、重放、篡改都拒", 21: "每条一把，用完即删", 22: "口令解开本地状态接着收"}
for idx, body in mini6.items():
    sh = shp(6, idx)
    head = sh.text_frame.paragraphs[0].runs[0].text
    set_text(sh, [[(head, 10)], [(body, 9.5)]])
for idx in (10, 17):
    bump(shp(6, idx), 1.0)

# ---------- S7 architecture diagram ----------
for idx in (3, 8, 13):
    bump(shp(7, idx), 1.5)
bodies7 = {4: "GUI / TUI，不接触链钥匙", 5: "会话与消息编排", 6: "纯字节进出，可离线单测",
           7: "PBKDF2 60 万次，AES-GCM 封存", 9: "只有公钥，没有私钥", 10: "密文暂存，按用户名转发",
           11: "好友关系、朋友圈（已知边界）", 12: "没有私钥，解不开信封", 14: "与左侧相同结构",
           15: "双方各自保管私钥", 16: "服务器没有任一方的私钥", 17: "区别只在身份钥"}
for idx, body in bodies7.items():
    sh = shp(7, idx)
    head = sh.text_frame.paragraphs[0].runs[0].text
    set_text(sh, [[(head + "　", 14), (body, 12)]])
set_text(shp(7, 21), [[("客户端 ↔ 服务器只走两类东西：取公钥包与离线信封，全程密文 · 附件走二进制帧", 13)]])
set_text(shp(7, 22), [[("▪ ", 14), ("服务器看不到正文、文件、语音与私钥；能看到的只有元数据", 14)]])

# ---------- S8 keys content ----------
set_text(shp(8, 3), [
    [("三把长期钥", 15.5)],
    [("IK_sign 只签名；IK_dh 只协商；SPK 用前先验签", 14.5)],
    [("一次性钥", 15.5)],
    [("OPK ×20 用完即删；后量子加 PQK + PQOPK ×8", 14.5)],
])
set_text(shp(8, 4), [
    [("▪ ", 14), ("验签三时机：注册入库前、发起会话前、登录挑战应答", 14)],
    [("▪ ", 14), ("私钥落盘：PBKDF2（60 万次）派生钥，AES-256-GCM 封存", 14)],
    [("▪ ", 14), ("身份钉住：身份公钥首次取得后固定，变化即拒绝告警", 14)],
])
for idx in (5, 6, 7, 8):
    sh = shp(8, idx)
    for pi, pa in enumerate(sh.text_frame.paragraphs):
        for r in pa.runs:
            if r.font.size:
                r.font.size = Pt(r.font.size.pt + 1.5)
set_text(shp(8, 9), [[("落盘：", 12), ("口令经 PBKDF2（60 万次）派生，AES-256-GCM 封存私钥", 12)]])

# ---------- S9 keys diagram ----------
bodies9 = {3: "Ed25519。签 SPK、初始消息、群状态；指纹 = 公钥 SHA-256",
           4: "X25519。只做 DH、从不签名，与 IK_sign 分开",
           5: "被 IK_sign 签名；用前验签，失败拒绝握手",
           6: "用完即删；少于 5 把补满；认证成功才删私钥",
           7: "ML-KEM-768。握手与每条新链都向它封装",
           8: "握手优先用它，用完即删；缺了退到 PQK"}
for idx, body in bodies9.items():
    sh = shp(9, idx)
    paras = sh.text_frame.paragraphs
    name = paras[0].runs[0].text
    head = paras[1].runs[0].text if len(paras) > 1 else ""
    set_text(sh, [[(name, 16)], [(head, 12.5)], [(body, 11.5)]])
set_text(shp(9, 9), [[("本地保险库：", 13), ("全部私钥 + 棘轮状态加密落盘——PBKDF2-HMAC-SHA256（60 万次 + 16 字节盐）派生钥，AES-256-GCM 封存", 13)]])
bump(shp(9, 10), 1.5)
set_text(shp(9, 11), [[("▪ ", 13), ("公钥可以公开（放在服务器目录里）；私钥永远只留在自己设备的保险库里", 13)]])

# ---------- S10 X3DH ----------
for idx in (4, 6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 21, 22, 23):
    bump(shp(10, idx), 1.5)
set_text(shp(10, 24), [[("SK = HKDF-SHA256（DH1‖DH2‖DH3‖DH4，x3dh-v1）", 11.5)]])
set_text(shp(10, 3), [
    [("▪ ", 14), ("DH1 绑长期身份与已签名 SPK——塞不进无背书的预密钥", 14)],
    [("▪ ", 14), ("DH3 让长期钥泄露也重算不出；DH4 用掉一次性预密钥", 14)],
    [("▪ ", 14), ("SK 只启动双棘轮，不直接加密内容", 14)],
])

# ---------- S11 PQXDH ----------
set_text(shp(11, 3), [[("威胁：「先记录、后解密」——今天存下密文，等量子计算机成熟后打破 X25519。对策：经典 DH 之外再并入后量子封装。", 15)]])
bump(shp(11, 5), 1.0)
set_text(shp(11, 6), [
    [("▪ ", 14.5), ("优先一次性 PQOPK，用完即删；取不到退到长期 PQK", 14.5)],
    [("▪ ", 14.5), ("防降级：都支持 PQ 时，缺 KEM 的握手直接拒绝", 14.5)],
    [("▪ ", 14.5), ("签名全覆盖：封装公钥与 KEM 密文都在签名内", 14.5)],
    [("▪ ", 14.5), ("实现：ML-KEM-768；域标签 x3dh-v1 / pqxdh-v1 分离", 14.5)],
])

# ---------- S12 handshake diagram ----------
steps12 = {3: "Alice 向服务器取 Bob 的 bundle（五类公钥）",
           4: "用 IK_sign 验证 SPK 签名；验不过 → 拒绝",
           5: "只用一次，私钥用完即弃",
           6: "DH1 身份↔SPK · DH2 临时↔身份 · DH3 临时↔SPK · DH4 临时↔OPK",
           7: "对 PQOPK（优先）或 PQK 做 ML-KEM 封装，得共享秘密 ss 与 ct",
           8: "DH 材料 ‖ PQ 秘密 ‖ SHA-256（封装公钥），经 HKDF 派生"}
for idx, body in steps12.items():
    sh = shp(12, idx)
    head = sh.text_frame.paragraphs[0].runs[0].text
    set_text(sh, [[(head + "　", 13.5), (body, 12.5)]])
set_text(shp(12, 9), [[("初始消息", 14.5)], [("EK 公钥 + ct + 第一条棘轮密文，整份材料被 IK_sign 签名覆盖", 12.5)]])
set_text(shp(12, 10), [[("Bob 同算", 14.5)], [("用私钥做同样的四次 DH + 解封装，算出同一把 SK", 12.5)]])
set_text(shp(12, 11), [[("▪ ", 13), ("SK 只是双棘轮的「种子」：它从不直接加密任何一条消息", 13)]])

# ---------- S13 ratchet content ----------
set_text(shp(13, 3), [
    [("▪ ", 14), ("对称棘轮：MK = HMAC(ck, 0x01)，用后即删 —— 前向安全", 14)],
    [("▪ ", 14), ("DH 棘轮：新 DH 输出换新根钥与新链 —— 破密恢复", 14)],
    [("▪ ", 14), ("AAD 绑定双方、序号与棘轮公钥：改动即 GCM 失败", 14)],
])
bodies13 = {4: "SK 初始化发送链，MK1 加密后立即丢弃", 5: "同一条链再走一步，MK2 与 MK1 不同",
            6: "生成自己的棘轮钥，做一次 DH 棘轮换链", 7: "旧链钥泄露也解不开新消息，破密恢复"}
for idx, body in bodies13.items():
    sh = shp(13, idx)
    paras = sh.text_frame.paragraphs
    num = paras[0].runs[0].text
    head = paras[1].runs[0].text if len(paras) > 1 else ""
    set_text(sh, [[(num, 16)], [(head, 11.5)], [(body, 10.5)]])
set_text(shp(13, 8), [[("前向安全：", 11.5), ("MK 用完即删，倒推不回已删的 MK", 11.5)]])
set_text(shp(13, 9), [[("破密恢复：", 11.5), ("双方换过棘轮公钥后，旧链钥推不出新消息", 11.5)]])

# ---------- S14 ratchet diagram ----------
set_text(shp(14, 3), [[("DH 棘轮（换链）：对方一回复，双方各换一把新棘轮钥", 14.5)]])
set_text(shp(14, 10), [[("对称棘轮（链内逐条滚动）：链钥像一次性楼梯，只能向前", 14.5)]])
for idx in (4, 6, 8, 11, 13, 15):
    bump(shp(14, idx), 1.5)
set_text(shp(14, 9), [
    [("破密恢复（自愈）成立时点：", 13), ("对方刚回复、双方都换过棘轮公钥之后。混合棘轮：每条新链再对 PQK 做一次 ML-KEM 封装。", 13)],
])
set_text(shp(14, 16), [[("HMAC 是单向的：今天的链钥泄露，也倒推不回昨天已删除的 MK —— 这就是前向安全。", 13)]])
set_text(shp(14, 17), [[("▪ ", 13), ("消息层三件套：跳过缓存（上限 40）· 重放拒绝 · 原子提交", 13)]])

# ---------- S15 hybrid + message layer ----------
for idx in (5, 9, 13, 17):
    bump(shp(15, idx), 2.0)
set_text(shp(15, 6), [[("每条新链除 DH 输出外，再对 PQK 做一次 ML-KEM 封装；缺 pq_ct 直接拒绝，防降级。", 14)]])
set_text(shp(15, 10), [[("超前消息先缓存中间 MK（上限 40）；迟到取出即删；超限拒绝，防耗尽攻击。", 14)]])
set_text(shp(15, 14), [[("已处理的 (dh_pub, n) 再现直接拒绝；改任一字节，GCM 认证失败。", 14)]])
set_text(shp(15, 18), [[("先在副本上试算，GCM 成功才提交；伪造包烧不掉合法钥匙。", 14)]])

# ---------- S16 group table ----------
bump(shp(16, 3), 1.0)
set_text(shp(16, 4), [
    [("▪ ", 14), ("签名哈希链：每次拉人纪元 +1、只增一人、前驱哈希指向上状态", 14)],
    [("▪ ", 14), ("群消息带所用状态哈希：伪造名单、幽灵成员都会暴露", 14)],
])

# ---------- S17 group diagram ----------
sh = shp(17, 3)
paras = sh.text_frame.paragraphs
set_text(sh, [[(paras[0].runs[0].text, 14.5)], [("同一段明文，逐人各加密一份，走各自的双棘轮", 12.5)]])
for idx in (5, 7, 9):
    bump(shp(17, idx), 1.5)
set_text(shp(17, 10), [
    [("代价与边界（主动声明）", 14)],
    [("成本 O(n)：每条发 n−1 封 → 上限 8 人；换回逐对前向安全 + 破密恢复", 12.5)],
])
set_text(shp(17, 11), [[("成员名单：签名哈希链 —— 服务器说了不算，客户端自己验", 14.5)]])
state17 = {12: "创建者签名 · 成员：Alice、Bob", 14: "拉 Carol 进群（只增一人）· 前驱哈希 · 现成员签名", 16: "拉 Dave 进群 · 前驱哈希 · 现成员签名"}
for idx, body in state17.items():
    sh = shp(17, idx)
    head = sh.text_frame.paragraphs[0].runs[0].text
    set_text(sh, [[(head, 13.5)], [(body, 12)]])
set_text(shp(17, 17), [[("每条群消息都带所用状态的哈希：名单对不上或签名不对 → 直接拒绝。", 13)]])
set_text(shp(17, 18), [[("▪ ", 13), ("回应《More is Less》：Sender Keys 让名单与正文都失去端到端保护——我们两条都补上", 13)]])

# ---------- S18 threat model ----------
items18a = ["还没核对指纹", "1. 向服务器要 Bob 的预密钥包", "2. 服务器把公钥换成攻击者的", "3. 验签通过（攻击者自签）", "4. Alice 的 SK ≠ 真实 Bob 的 SK", "5. 攻击者与真 Bob 另建会话"]
items18b = ["已经核对指纹", "1. 双方线下比对 16 组指纹无误", "2. 客户端钉住身份公钥，再变就拒绝", "3. 服务器只能继续转发密文信封", "4. 它没有消息钥匙，读不出内容", "5. 改一个密文字节，接收方 GCM 失败"]
for idx, items in ((4, items18a), (5, items18b)):
    set_text(shp(18, idx), [[(items[0], 12.5)]] + [[(t, 11)] for t in items[1:]])
set_text(shp(18, 3), [
    [("▪ ", 14), ("攻击：服务器换掉 Bob 的公钥配自签身份，Alice 与攻击者建会话", 14)],
    [("▪ ", 14), ("防线：指纹线下核对后钉住身份公钥，再换即被拒", 14)],
    [("▪ ", 14), ("验证：攻击演示已运行——掉包后 SK 等于攻击者的、不等于 Bob 的", 14)],
])

# ---------- S19 fingerprint diagram ----------
panels19 = {3: ["· Alice 拿到 Bob 的真公钥包", "· 双方算出同一把 SK", "· 服务器只转发，看不懂"],
            4: ["· 服务器把 Bob 的公钥换成攻击者 M 的", "· Alice 与 M 一条会话、M 与 Bob 另一条", "· M 居中转发，两边明文都可读"],
            5: ["· 指纹 = 公钥 SHA-256，16 组十六进制", "· 线下核对（当面 / 电话）", "· 首次取得后钉住，再变 → 拒绝 + 告警"]}
for idx, items in panels19.items():
    sh = shp(19, idx)
    head = sh.text_frame.paragraphs[0].runs[0].text
    set_text(sh, [[(head, 14)]] + [[(t, 12.5)] for t in items])
bump(shp(19, 6), 1.5)
set_text(shp(19, 7), [[("挑战应答只能证明「你持有服务器当初收下的私钥」——注册时公钥若被换，证明链从源头就断。Signal 也靠安全码核对；我们把窗口压缩到「第一次接触之前」。", 13)]])
set_text(shp(19, 8), [[("▪ ", 13), ("核对完指纹之后，服务器就只剩下「转发」和「漏投」两种能力，读不到、改不了、冒充不了", 13)]])

# ---------- S20 innovation ----------
for idx in (5, 9, 13, 17):
    bump(shp(20, idx), 2.0)
set_text(shp(20, 6), [[("基线只保护握手。我们每条新链都混入 ML-KEM 封装（pq-dr-v1），优先 PQOPK，拒绝降级。", 14)]])
set_text(shp(20, 10), [[("基线群链无 DH 棘轮、名单服务器说了算。我们以 O(n) 换回逐对前向安全与破密恢复。", 14)]])
set_text(shp(20, 14), [[("签名覆盖全部握手材料（经典 + PQ）；身份公钥本地钉住，换钥即拒。", 14)]])
set_text(shp(20, 18), [[("先在副本试算、GCM 成功才原子提交；OPK 私钥延迟删除，堵实现层攻击面。", 14)]])

# ---------- S21 progress ----------
bump(shp(21, 4), 1.0)
set_text(shp(21, 5), [
    [("▪ ", 14), ("规模：Python 源码约 2 万行；文件走第二层 AES-256-GCM（8 MiB 分片）", 14)],
    [("▪ ", 14), ("诚实边界：社交数据在服务器明文存放——加密的是正文与文件字节", 14)],
])

# ---------- S22 testing & roadmap ----------
for idx in (5, 9, 13):
    bump(shp(22, idx), 2.5)
set_text(shp(22, 6), [[("19 个测试文件：握手、棘轮乱序 / 重放 / 篡改、PQ、群、附件、通话", 13.5)]])
set_text(shp(22, 10), [[("掉包中间人、伪造成员表、论文—代码对应，均已运行验证", 13.5)]])
set_text(shp(22, 14), [[("JS 端（PWA）与 v1 引擎后量子互操作全通；经典端被拒降级", 13.5)]])
bump(shp(22, 15), 2.0)
set_text(shp(22, 16), [
    [("▪ ", 14), ("v2 落地：生产部署（Cloudflare 中继 + WSS）、桌面打包", 14)],
    [("▪ ", 14), ("协议补强：语音媒体面、密封发送者、评估 Triple Ratchet", 14)],
    [("▪ ", 14), ("已知缺口：无多设备、无头加密、元数据可见、Triple Ratchet 未实现", 14)],
])

prs.save(SRC)
print("round-2 deck saved")
