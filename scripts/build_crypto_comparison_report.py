"""Build the local Chinese report and its standalone mechanism figure from measured data."""

import json
import os
import statistics
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/benchmarks"
OUT = ROOT / "output/pdf"
INK, MUTED, RULE = "#182F40", "#4E6270", "#C7D3D7"
BLUE, AMBER, TEAL = "#315C7B", "#895020", "#076A61"
W, H = A4
M = 44
WIDTH = W - 2 * M


def read(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


wire = read("three-schemes-wire.json")
core = read("three-schemes-compute.json")
browser = read("three-schemes-renderer.json")


def samples(data, arm, *keys):
    rows = [row for row in data["runs"] if row["arm"] == arm]
    for key in keys:
        rows = [row[key] for row in rows]
    return rows


def byte_count(arm, phase):
    return int(statistics.median(samples(wire, arm, phase, "http_bytes")))


def byte_cell(arm, phase):
    v = samples(wire, arm, phase, "http_bytes")
    return f"{statistics.median(v):,.0f}", f"{min(v):,} – {max(v):,}"


def change(a, b, phase):
    base = byte_count(a, phase)
    delta = byte_count(b, phase) - base
    return (f"{delta:+,} B", f"{100 * delta / base:+.2f}%")


def time_median(data, arm, phase):
    return statistics.median(samples(data, arm, phase))


def time_cell(data, arm, phase):
    lo, median, hi = statistics.quantiles(samples(data, arm, phase), n=4, method="inclusive")
    return f"{median:.2f}", f"{lo:.2f} – {hi:.2f}"


def ms_diff(data, a, b, phase):
    return f"{time_median(data, b, phase) - time_median(data, a, phase):+.2f}"


def color(hex_code):
    return colors.HexColor(hex_code)


def label(c, x, top, text, size=10, face="Sans", ink=INK, align="left", limit=None):
    if limit is not None:
        assert pdfmetrics.stringWidth(text, face, size) <= limit, text
    c.setFillColor(color(ink))
    c.setFont(face, size)
    y = c._pagesize[1] - top - size
    {"left": c.drawString, "right": c.drawRightString, "center": c.drawCentredString}[align](x, y, text)


def box(c, x, top, width, height, fill, stroke=None, radius=0):
    c.setFillColor(color(fill))
    if stroke:
        c.setStrokeColor(color(stroke))
        c.setLineWidth(0.7)
    c.roundRect(x, c._pagesize[1] - top - height, width, height, radius, fill=1, stroke=int(bool(stroke)))


def line(c, x1, y1, x2, y2, ink=RULE, thick=0.7):
    c.setStrokeColor(color(ink))
    c.setLineWidth(thick)
    h = c._pagesize[1]
    c.line(x1, h - y1, x2, h - y2)


def para(c, top, text, size=10.5, leading=17.4, x=M, width=WIDTH, ink=INK):
    style = ParagraphStyle("text", fontName="Sans", fontSize=size, leading=leading,
                           wordWrap="CJK", textColor=color(ink))
    p = Paragraph(escape(text), style)
    _, height = p.wrap(width, 2000)
    p.drawOn(c, x, c._pagesize[1] - top - height)
    return top + height


def page_header(c, subject, page):
    c.setPageSize(A4)
    label(c, M, 23, "ECNUchat   /   端到端加密系统实验", 9, "Bold", BLUE)
    label(c, W - M, 23, "本地实验报告   ·   2026 年 11 月 26 日", 8.5, ink=MUTED, align="right")
    line(c, M, 42, W - M, 42)
    line(c, M, H - 43, W - M, H - 43)
    label(c, M, H - 35, subject, 8.5, ink=MUTED)
    label(c, W - M, H - 35, f"{page} / 5", 9, "Bold", BLUE, "right")


def title(c, text, sub):
    label(c, M, 58, text, 23, "Bold", limit=WIDTH)
    return para(c, 99, sub, 11, 18.5, ink=MUTED) + 18


def section(c, top, text):
    label(c, M, top, text, 13, "Bold", limit=WIDTH)
    return top + 23


def table(c, top, widths, headers, rows, row_h=40, right=(), size=10.4):
    xs = [M]
    for width in widths:
        xs.append(xs[-1] + width)
    assert abs(xs[-1] - (W - M)) < 0.01
    box(c, M, top, WIDTH, 26, "#E4EDF0")
    for i, name in enumerate(headers):
        align = "right" if i in right else "left"
        x = xs[i + 1] - 8 if i in right else xs[i] + 8
        label(c, x, top + 6, name, 9, "Bold", BLUE, align, widths[i] - 16)
    top += 26
    for n, row in enumerate(rows):
        if n % 2 == 0:
            box(c, M, top, WIDTH, row_h, "#F5F8F8")
        for i, cell in enumerate(row):
            align = "right" if i in right else "left"
            x = xs[i + 1] - 8 if i in right else xs[i] + 8
            values = cell if isinstance(cell, tuple) else (cell,)
            offset = (row_h - (size + (15 if len(values) == 2 else 0))) / 2
            label(c, x, top + offset, values[0], size, "Bold" if i == 0 or len(values) == 2 else "Sans",
                  INK, align, widths[i] - 16)
            if len(values) == 2:
                label(c, x, top + offset + 16, values[1], 8.6, ink=MUTED, align=align, limit=widths[i] - 16)
        top += row_h
    line(c, M, top, W - M, top)
    return top + 9


def first_page(c):
    page_header(c, "同一目录策略下的通信流量", 1)
    y = title(c, "混合加密的通信与计算开销", "ECNUchat 经典双棘轮、完整混合封装与确认后引用的本机对照实验")
    y = section(c, y + 3, "摘要")
    y = para(c, y, "在相同的版本化设备目录缓存下，加入 ML-KEM-768 并启用封装引用后，首次联系的 HTTP 流量从传统方案的 20,609 B 增至 97,016 B。已确认的同一发送链再发 10 条消息，差距缩至 860 B（2.93%）。引用摊薄了重复传输的成本，首次建链仍需完成混合密钥协商、签名检查和预密钥交换。")
    y = section(c, y + 22, "表 1    统一目录缓存后的双向 HTTP 流量")
    names = {"F": ("传统双棘轮  F", "X25519 / X3DH"),
             "E": ("完整封装混合  E", "原封装策略，加同款缓存"),
             "C": ("确认后引用混合  C", "当前本地方案")}
    rows = [(names[a], byte_cell(a, "cold"), byte_cell(a, "warm"),
             f"{statistics.median(samples(wire, a, 'warm_envelope_request_bytes')):,.0f}") for a in "FEC"]
    y = table(c, y, [153, 123, 123, WIDTH - 399],
              ["主比较组", "首次建链（B）", "后续 10 条（B）", "10 个上行信封（B）"],
              rows, row_h=47, right=(1, 2, 3))
    y = para(c, y, "每组 6 次独立会话。粗体流量为中位数，下行为最小至最大值。末列只计发送端的信封请求体，已含在后续 10 条总量中。B 表示字节，1 B = 8 bit。", 9, 14.8, ink=MUTED)
    y = section(c, y + 24, "相对传统方案，多花在哪里？")
    y = para(c, y, "首次建链　完整封装混合比传统多 73,091 B（+354.66%）。现方案还要完成引用协商和回执，相对传统多 76,407 B（+370.75%），总量约为传统方案的 4.71 倍。")
    y = para(c, y + 11, "后续连发　若每条仍携带完整封装，10 条比传统多 29,011 B（+98.91%）。改传引用后，双向 HTTP 平均每条多 86 B，其中发送端信封平均每条多 43 B。")
    y = para(c, y + 23, "测量窗口　首次从添加好友开始，包含第一条 128 B 正文、两端查收及适用的回执。后续从同链已就绪开始，单向连发 10 条 128 B 正文并完成两端查收。两列互不重叠。", 9.7, 16.2, ink=MUTED)
    assert y < H - 51
    c.showPage()


def arrow(c, x, y, length, ink):
    line(c, x, y, x + length, y, ink, 1.45)
    line(c, x + length - 5, y - 3.5, x + length, y, ink, 1.45)
    line(c, x + length - 5, y + 3.5, x + length, y, ink, 1.45)


def figure(c):
    w, h = landscape(A4)
    c.setPageSize((w, h))
    label(c, 35, 22, "ECNUchat   /   图 1", 10, "Bold", BLUE)
    label(c, 35, 42, "同一目录缓存下，三种方案怎样发送消息", 22, "Bold")
    label(c, 35, 78, "首次建链与同链后续分开。每条正文均派生新的消息密钥，并使用 AES-256-GCM 加密和认证。", 11, ink=MUTED)
    box(c, 35, 111, w - 70, 58, "#E7F2F0", radius=5)
    label(c, 49, 120, "三组共用同一目录缓存", 11, "Bold", TEAL)
    label(c, 49, 142, "读取本地已核验设备与版本", 10)
    arrow(c, 192, 149, 19, TEAL)
    label(c, 223, 142, "投递时随信封带上版本", 10)
    arrow(c, 349, 149, 19, TEAL)
    label(c, 380, 142, "中继核对版本再入队", 10)
    label(c, 514, 142, "版本已变时刷新目录，重新核对设备指纹。", 10, ink=TEAL)
    label(c, 39, 184, "方案", 11, "Bold", MUTED)
    label(c, 180, 184, "首次建链与首封", 13, "Bold")
    label(c, 506, 184, "后续同链单向连发", 13, "Bold")
    rows = [
        (BLUE, "#EFF4F8", "传统双棘轮", "F   传统基线",
         "经典 X3DH 握手", "用 X25519 建立棘轮，发送首条认证密文。",
         "逐条传棘轮头和正文密文", "同一链上继续派生消息密钥。"),
        (AMBER, "#FAF4ED", "完整封装混合", "E   原封装策略",
         "混合 PQXDH 握手 + 新链封装", "握手和首条发送链各做一次 ML-KEM-768 封装。",
         "每条重复发送 1,088 B 链封装", "同链复用封装结果，仍逐条加密正文。"),
        (TEAL, "#EDF6F3", "确认后引用混合", "C   当前方案",
         "相同混合握手与完整链封装", "收端认证首封、保存状态，再发 HMAC 回执。",
         "发端验回执后，每条带 32 B 引用", "摘要标识已有封装，正文仍随信封发送。"),
    ]
    for index, (ink, fill, name, desc, cold, cold_note, warm, warm_note) in enumerate(rows):
        top = 212 + index * 90
        box(c, 35, top, 128, 75, fill, radius=4)
        box(c, 35, top + 6, 3, 63, ink)
        label(c, 47, top + 16, name, 13, "Bold", ink, limit=111)
        label(c, 47, top + 42, desc, 9.5, ink=MUTED)
        arm = "FEC"[index]
        for x, heading, note, phase in [(178, cold, cold_note, "cold"), (503, warm, warm_note, "warm")]:
            box(c, x, top, 298, 75, "#FFFFFF", RULE, radius=4)
            label(c, x + 12, top + 8, heading, 12, "Bold", ink, limit=274)
            label(c, x + 12, top + 30, note, 9.8, ink=INK, limit=274)
            traffic_label = "首次双向 HTTP" if phase == "cold" else "10 条双向 HTTP"
            label(c, x + 12, top + 52, f"{traffic_label}    {byte_count(arm, phase):,} B", 9.7, "Bold", ink)
        arrow(c, 479, top + 36, 19, ink)
    line(c, 35, 485, w - 35, 485)
    label(c, 35, 498, "换链或未获确认", 11, "Bold", TEAL)
    label(c, 144, 498, "当前方案继续携带完整封装。换链生成新封装，上一条链的确认不能沿用。", 10.5)
    label(c, 35, 525, "1,088 B 和 32 B 为二进制字段长度。双向 HTTP 为 6 次实测中位数，含编码、HTTP 头和收件箱下行。每条正文 128 B。", 9.6, ink=MUTED)
    label(c, 35, 550, "旧版 B 逐条查询目录。后续 10 条从 B 到 E 仅加缓存，省 168,949 B。从 E 到 C 加入引用，再省 28,151 B。", 10.1, "Bold", INK)


def attribution(c):
    page_header(c, "单项优化的流量归因", 3)
    y = title(c, "目录缓存与封装引用，各省多少流量？", "实际旧版 B 逐条查目录并携带完整封装，首次建链用 129,896 B，后续 10 条用 227,290 B。下表从 B 出发，先只更换目录策略，再只更换信封策略。")
    y = section(c, y + 1, "表 2    同一聊天负载的单项改动与组合效果")
    rows = []
    for a, b, desc in [("B", "E", "只加目录缓存，完整封装不变"), ("E", "C", "只加封装引用，目录缓存不变"),
                       ("B", "C", "旧版到现版，两项合计")]:
        rows.append(((a + " → " + b, desc), change(a, b, "cold"), change(a, b, "warm")))
    y = table(c, y, [218, 144, WIDTH - 362], ["比较与固定条件", "首次建链的变化", "后续 10 条的变化"],
              rows, row_h=47, right=(1, 2))
    y = para(c, y, "变化量为终点组中位数减起点组中位数，正号表示增加，负号表示节省。百分比以该行起点为分母。两步字节差可以相加，百分比须分别解读。", 9.4, 15, ink=MUTED)
    y = section(c, y + 20, "目录缓存减少了十次完整设备查询")
    y = para(c, y, "B 的完整设备目录携带公钥与预密钥池。改用缓存后，热阶段的完整目录查询由 10 次降至 0 次，HTTP 请求由 22 次降至 12 次。B 的 227,290 B 降到 E 的 58,341 B，10 个发送信封本身均合计 20,471 B。传统方案单独启用相同缓存，热阶段也从 62,728 B 降至 29,330 B。")
    y = section(c, y + 18, "封装引用减少了上行和收件箱下行的重复字节")
    y = para(c, y, "同链封装由 1,088 B 密文改为 32 B 的 SHA-256 摘要。经 Base64 编码分别为 1,452 和 44 个字符。算入 JSON 字段，每个上行信封节省 1,407 B，10 个共省 14,070 B。收件箱响应也随之变小，双向 HTTP 合计节省 28,151 B。首条仍须完整封装，新增协商字段、回执和相应 HTTP 开销使首次建链增加 3,316 B。")
    y = section(c, y + 18, "交叉核对")
    y = para(c, y, "若先启用引用、仍逐条读取目录（D），再加缓存（D → C），热阶段从 199,279 B 降至 30,190 B，单步节省 169,089 B（84.85%）。两条路径的旧版到现版总节省均为 197,100 B（86.72%）。")
    y = para(c, y + 15, "首次建链还包含接收端核验发送方的公钥材料，以及消费一次性预密钥后向中继重新登记公钥包。仅预密钥获取接口的 HTTP 中位数，传统 F 为 3,011 B，混合 E 为 21,576 B。", 9.6, 15.8, ink=MUTED)
    assert y < H - 51
    c.showPage()


def computations(c):
    page_header(c, "计算耗时与测量边界", 4)
    y = title(c, "计算耗时集中在哪里？", "两个独立实验均以毫秒计量。表 3 测密码处理路径耗时，表 4 测聊天界面的主线程任务时间。两者覆盖的工作不同，数值不能相加。")
    y = section(c, y, "表 3    双端密码处理路径耗时（ms）")
    names = {"F": "F   传统双棘轮＋缓存", "E": "E   完整混合封装＋缓存",
             "C": "C   确认后引用＋缓存", "B": "B   历史完整封装＋逐条查目录"}
    widths = [200, 150, WIDTH - 350]
    def timing_rows(data, arms):
        return [(names[a], time_cell(data, a, "cold_ms"), time_cell(data, a, "warm_ten_ms")) for a in arms]
    y = table(c, y, widths, ["配置", "首次建链及首条", "后续 10 条合计"],
              timing_rows(core, "FEC"), right=(1, 2), row_h=36)
    y = para(c, y, "同一 Node.js 进程串行运行收发两端，计入公钥包验签、建链、加解密、信封 JSON 往返以及适用回执的生成、验证。身份与预密钥池预生成，计时排除目录 I/O、网络、界面和写盘。每组 24 次。两张表均为中位数，下行为第 25 至 75 百分位。", 9.3, 14.8, ink=MUTED)
    y = para(c, y + 9, f"完整混合封装较传统首次多 {ms_diff(core, 'F', 'E', 'cold_ms')[1:]} ms，现方案较传统首次多 {ms_diff(core, 'F', 'C', 'cold_ms')[1:]} ms。后续同链发送沿用已有封装，三组 10 条耗时的四分位区间重叠。这组结果不足以支持后量子加密提升计算速度。", 10.4, 16.6)
    y = section(c, y + 17, "表 4    聊天界面双端渲染主线程的任务时间（ms）")
    y = table(c, y, widths, ["配置", "首次建链及首条", "后续 10 条合计"],
              timing_rows(browser, "FECB"), right=(1, 2), row_h=35)
    y = para(c, y, "独立复跑聊天表单，每组 6 次。Chrome 的 TaskDuration 使用 threadTicks，累加双方渲染主线程运行任务的时间，含脚本、界面与测试驱动在页面执行的操作。其他线程、网络等待及中继 CPU 用时均在此指标之外。", 9.3, 14.8, ink=MUTED)
    y = para(c, y + 10, f"按中位数之差，单加目录缓存（B → E）首次 {ms_diff(browser, 'B', 'E', 'cold_ms')} ms、后续 10 条 {ms_diff(browser, 'B', 'E', 'warm_ten_ms')} ms。固定缓存后再加引用（E → C），两阶段分别为 {ms_diff(browser, 'E', 'C', 'cold_ms')} 和 {ms_diff(browser, 'E', 'C', 'warm_ten_ms')} ms。该组差值描述这台主机上的观察，未测整机能耗或用户等待时间。", 10.3, 16.5)
    assert y < H - 51, y
    c.showPage()


def methods(c):
    page_header(c, "方法、适用范围与复现材料", 5)
    y = title(c, "实验方法、适用边界与复现", "样本单位为独立会话。每条会话只有一对设备，所有流量实验在本机回环中继完成。")
    y = section(c, y, "实验环境与统计方法")
    y = para(c, y, "Windows 11，Intel Core i7-14650HX，Chrome 158.0.8127.38，Node.js 24.22.3。流量与浏览器计时各使用 6 个区组，每组轮换六种配置的执行顺序，各配置占每个位置一次。每个配置使用新中继和两份隔离浏览器身份。流量样本的 360 条后续消息均逐条核对解密结果。Node.js 计时先按配置预热两次，再将三种方案的六种顺序各重复四轮，每次重建测试身份。", 10.1, 16.7)
    y = para(c, y + 8, "流量计数覆盖双方与中继的 HTTP/1.1 请求行、状态行、头、正文及实际预检。初始注册与网页资源在窗口外，首条后的公钥包重新登记在窗口内。后续阶段接收方暂时离线，十条消息入队后重连，双方各查收一次。字节数排除 TLS、TCP/IP 和链路重传。", 10.1, 16.7)
    y = section(c, y + 16, "确认、换链与故障恢复")
    y = para(c, y, "引用仅在发端验过本链回执后启用。回执绑定双方设备地址、链公钥和封装摘要，收端先认证消息并保存状态，再发送回执。回执丢失时继续发送完整封装。既有本地用例覆盖乱序、重放拒绝和保留会话状态下的进程重启。确认后若接收方清除本机状态，旧引用可能无法解密。", 10.1, 16.7)
    y = para(c, y + 8, "轮流回复会频繁换链。既有实验中，两端逐条交替发送 100 条，含回执的信封请求体由 209,621 B 增至 263,121 B（+25.52%）。首次联系即离线积压 10 条，同一指标增加 195.50%。这是信封级计量，适用条件和统计范围与表 1 不同。", 10.1, 16.7)
    y = para(c, y + 8, "目录版本由中继在入队时检查。版本冲突返回 409 并触发刷新，新设备或被替换的签名身份须重新核验指纹。回归测试提供了这些行为的证据，尚无对本项目扩展协议的独立安全审计。", 10.1, 16.7)
    y = section(c, y + 17, "数据与复现")
    for entry in [
        "流量记录　docs/benchmarks/three-schemes-wire.json（复用已核对源码摘要的 36 次实测）",
        "密码计时　docs/benchmarks/three-schemes-compute.json（本次新增 72 次）",
        "界面计时　docs/benchmarks/three-schemes-renderer.json（本次新增 36 次）",
        "协议边界　docs/benchmarks/pq-reference.md、directory-cache.md 与配套原始记录",
    ]:
        y = para(c, y, entry, 9.2, 15)
    y += 4
    for cmd in ["python -m v2.tests.benchmark_three_schemes", "node scripts/benchmark_crypto_phases.js",
                "python -m v2.tests.benchmark_browser_compute"]:
        label(c, M + 2, y, cmd, 8.5, "Courier", BLUE)
        y += 12.3
    y = section(c, y + 11, "协议背景文献")
    y = para(c, y, "Bienstock et al.  A More Complete Analysis of the Signal Double Ratchet Algorithm. CRYPTO 2022, ePrint 2022/355.", 8.8, 13.8, ink=MUTED)
    y = para(c, y + 2, "Fiedler and Günther.  Security Analysis of Signal’s PQXDH Handshake. PKC 2025, ePrint 2024/702.", 8.8, 13.8, ink=MUTED)
    assert y < H - 51, y
    c.showPage()


def main():
    # The explanatory text refers to this particular browser data set.
    snapshot = {"F": (20609, 29330), "E": (93700, 58341), "C": (97016, 30190),
                "B": (129896, 227290), "D": (133242, 199279), "A": (26308, 62728)}
    for arm, expected in snapshot.items():
        assert tuple(byte_count(arm, phase) for phase in ("cold", "warm")) == expected
        assert samples(wire, arm, "delivered") == [10] * 6
        assert len(samples(browser, arm, "cold_ms")) == 6
    for arm in "FEC":
        assert len(samples(core, arm, "cold_ms")) == 24
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for face, name in [("Sans", "msyh.ttc"), ("Bold", "msyhbd.ttc")]:
        pdfmetrics.registerFont(TTFont(face, str(fonts / name), subfontIndex=0))
    OUT.mkdir(parents=True, exist_ok=True)
    scratch = ROOT / "tmp/pdfs"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        tmp = Path(tmp)
        pdf = tmp / "report.pdf"
        c = Canvas(str(pdf), pagesize=A4, pageCompression=1)
        c.setTitle("ECNUchat 混合加密的通信与计算开销")
        c.setAuthor("ECNUchat")
        c.setSubject("同一目录缓存下的首次建链、同链连发与单项优化实测")
        first_page(c)
        figure(c)
        c.showPage()
        attribution(c)
        computations(c)
        methods(c)
        c.save()
        figure_path = tmp / "figure"
        subprocess.run(["pdftoppm", "-f", "2", "-l", "2", "-singlefile", "-r", "240",
                        "-png", str(pdf), str(figure_path)], check=True)
        pdf.replace(OUT / "ECNUchat-通信流量优化报告.pdf")
        figure_path.with_suffix(".png").replace(OUT / "ECNUchat-三种方案机理对比.png")


if __name__ == "__main__":
    main()
