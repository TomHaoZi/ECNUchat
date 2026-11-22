# -*- coding: utf-8 -*-
"""Round 6: merge content+figure slide pairs (23 -> 19 pages),
enrich the progress slide with real running screenshots, renumber."""
import re
from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn

SRC = "/home/hatch/workspace/ecnuchat-midterm/ECNUchat-中期汇报.pptx"
prs = Presentation(SRC)
RED = RGBColor(0xA6, 0x1E, 0x36)
GRAY = RGBColor(0x59, 0x59, 0x59)
IMG = "/home/hatch/workspace/ecnuchat/docs/images"

NOTES = {
    7: ("客户端四层各管一段，密码部分被单独关起来写；服务器只有公钥和密文。",
        "【2:25–3:00】系统分四层看。最上面是界面层，桌面端和终端端两套界面，共用同一个会话引擎 ChatEngine，界面层不接触链钥匙（链钥就是聊天中途不断滚动的那把钥匙）。核心是密码模块，只有三个文件：x3dh 管握手、double_ratchet 管棘轮、prekeys 管预存钥匙。这三个文件有个硬规矩：不许导入网络和数据库，只做纯字节进出——好处是能离线单测，每一步都能单独拿出来验。服务器只存三样东西：公钥、预存钥匙池、离线信封，按用户名转发，解析不出明文。聊天帧超过 64KB 直接拒绝，附件走单独的二进制帧通道。"),
    9: ("每把钥只干一件事：印章管签名，配钥匙的管协商，一次性的用完就扔。",
        "【3:00–3:40】先把钥匙串讲清，后面都用得上。原则一句话：签名钥和协商钥从生成起就是两把，不学 Signal 那种一把钥两用。IK_sign 是 Ed25519，只管签名——相当于本人的印章；IK_dh 是 X25519，长期协商身份，只管配钥匙。SPK 是中期预密钥，放在服务器上供对方取用，它身上有 IK_sign 的签名，对方用之前先验章，验不过直接拒绝。OPK 是一次性预密钥，一共 20 把，用掉一把少一把，少于 5 把自动补满。后量子再加两把：长期的 PQK 和 8 把一次性的 PQOPK，都是 ML-KEM-768。所有私钥都不裸奔：存在本地保险库里，用口令熬出来的钥加密——PBKDF2 把口令迭代 60 万次才派生出钥，就是故意让猜口令变贵。"),
    14: ("棘轮就是只能往前转的齿轮：钥匙只能向前变，所以偷到今天的也解不开昨天的；对方一回复，整套换新，安全长回来。",
         "【5:10–5:55】双棘轮是两种滚动配合。先说对称棘轮，管同一条链里的连续消息：链钥 CK 用 HMAC 算一下（带钥匙的哈希，只能正着算、反推不回），0x01 出口出消息钥 MK、0x02 出口出下一把链钥。MK 加密一条消息就立刻删除。所以前向安全的道理特别朴素：昨天的 MK 早扔了，今天链钥泄露也倒推不回来。再说 DH 棘轮，管换链：对方一回复，消息里带着他的新棘轮公钥，双方各换一把新的临时棘轮钥，新算出的 DH 结果经 HKDF 换出新根钥和新链。这就是破密恢复，时间点要说准：对方刚回复、双方都换过新钥之后才成立，不是泄露的当下；对方没回复之前，那一段只有前向安全。另外每条消息的加密还把收发双方、序号、棘轮公钥都绑进 GCM 的认证标签（这叫 AAD，附加认证数据：不加密，但改了就解密报错），防调包。"),
    19: ("全系统最薄弱的一环在“第一次拿公钥”：不核对指纹，服务器能把公钥整套换掉，做成中间人；核对之后，它就只剩转发。",
         "【7:15–7:55】安全分析讲最要紧的一个攻击：中间人。软肋在目录环节：公钥包存在服务器上，如果 Alice 从不核对指纹，服务器可以把 Bob 的公钥整套换成攻击者的。Alice 以为在跟 Bob 建会话，其实钥匙是和攻击者配的；攻击者再回头跟真 Bob 建另一条，两边转发——两条都是“加密”的，但明文在攻击者那里全过一遍。防线是指纹：把对方签名公钥算一个 SHA-256，显示成 16 组十六进制，两人线下（当面或电话）对一遍。对上之后，客户端把这把身份公钥本地钉住——第一次见到就记死，以后再变直接拒绝并告警。所以攻击窗口只剩“第一次接触之前”。我们用攻击演示验证过这一段：掉包之后，Alice 算出的 SK 等于攻击者的、不等于 Bob 的，结论与威胁模型一致。"),
}
for n, (one, script) in NOTES.items():
    prs.slides[n - 1].notes_slide.notes_text_frame.text = f"【一句话】{one}\n\n{script}"

# title fix on keys figure slide (was 9)
s9 = prs.slides[8]
for sh in s9.shapes:
    if sh.has_text_frame and "密钥体系图解" in sh.text_frame.text:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.text = r.text.replace("密钥体系图解：六把钥匙与保险库", "密钥体系：六把钥匙与保险库")

# ---- progress slide (21): screenshot grid ----
s21 = prs.slides[20]
for sh in list(s21.shapes):
    if sh.shape_type == 13:
        sh._element.getparent().remove(sh._element)
for sh in s21.shapes:
    if sh.has_text_frame and "实现进展" in sh.text_frame.text and sh.top.inches < 1.0:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                r.text = r.text.replace("实现进展：v1 功能完整，双界面同一引擎", "实现进展：v1 功能完整 · 真实运行界面")
    if sh.has_table:
        sh.left, sh.width = Inches(6.00), Inches(3.42)
shots = [("desktop-gui.png", "桌面端 · 深色"), ("ui-three-clients.png", "三端同聊"),
         ("ui-wechat.png", "桌面端 · 微信风"), ("ui-terminal.png", "终端端")]
for i, (fn, cap) in enumerate(shots):
    col, row = i % 2, i // 2
    x = 1.12 + col * 2.33
    y = 1.50 + row * 1.50
    s21.shapes.add_picture(f"{IMG}/{fn}", Inches(x), Inches(y), Inches(2.25), Inches(1.41))
    tb = s21.shapes.add_textbox(Inches(x), Inches(y + 1.42), Inches(2.25), Inches(0.20))
    tf = tb.text_frame
    tf.word_wrap = False
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, 0)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = cap
    r.font.size = Pt(9.5); r.font.name = "Microsoft YaHei"; r.font.color.rgb = GRAY
    rPr = r._r.get_or_add_rPr()
    ea = rPr.makeelement(qn('a:ea'), {}); ea.set('typeface', "Microsoft YaHei"); rPr.append(ea)

# ---- delete slides 18, 13, 8, 6 (descending) ----
def delete_slide(idx0):
    sldIdLst = prs.slides._sldIdLst
    sldId = sldIdLst[idx0]
    prs.part.drop_rel(sldId.rId)
    sldIdLst.remove(sldId)

for idx0 in (17, 12, 7, 5):
    delete_slide(idx0)

# ---- renumber page labels NN / 23 -> NN / 19 ----
pat = re.compile(r"^\s*\d+\s*/\s*23\s*$")
for i, s in enumerate(prs.slides, 1):
    for sh in s.shapes:
        if sh.has_text_frame and pat.match(sh.text_frame.text):
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.text = f"{i} / 19"

prs.save(SRC)
print("merged deck:", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
