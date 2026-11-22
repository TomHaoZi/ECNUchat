#!/usr/bin/env python3
"""Build the ECNUchat, Inc. preliminary prospectus PDF (S-1 style)."""
import sys
sys.path.insert(0, "/home/hatch/workspace/ecnuchat-prospectus")
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, Image,
                                KeepTogether, HRFlowable)
import content_a, content_b, content_c, content_d

FDIR = "/usr/share/fonts/truetype/noto/"
pdfmetrics.registerFont(TTFont("Serif", FDIR + "NotoSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", FDIR + "NotoSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", FDIR + "NotoSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BoldItalic", FDIR + "NotoSerif-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold",
                              italic="Serif-Italic", boldItalic="Serif-BoldItalic")

NAVY = colors.HexColor("#0A2540")
RED = colors.HexColor("#A61E36")
GRAY = colors.HexColor("#555555")

S = {}
S["body"] = ParagraphStyle("body", fontName="Serif", fontSize=10.5, leading=15.2,
                           alignment=TA_JUSTIFY, spaceAfter=7)
S["bodyIndent"] = ParagraphStyle("bodyIndent", parent=S["body"], firstLineIndent=18)
S["h1"] = ParagraphStyle("h1", fontName="Serif-Bold", fontSize=13.5, leading=17,
                         alignment=TA_CENTER, spaceBefore=6, spaceAfter=12,
                         textColor=NAVY)
S["h2"] = ParagraphStyle("h2", fontName="Serif-Bold", fontSize=11, leading=14.5,
                         spaceBefore=10, spaceAfter=5, textColor=colors.black)
S["bullet"] = ParagraphStyle("bullet", parent=S["body"], leftIndent=22,
                             bulletIndent=8, spaceAfter=4)
S["center"] = ParagraphStyle("center", parent=S["body"], alignment=TA_CENTER)
S["small"] = ParagraphStyle("small", fontName="Serif", fontSize=8.6, leading=11.8,
                            alignment=TA_JUSTIFY, spaceAfter=6)
S["smallCenter"] = ParagraphStyle("smallCenter", parent=S["small"], alignment=TA_CENTER)
S["caption"] = ParagraphStyle("caption", fontName="Serif-Italic", fontSize=9,
                              leading=12, alignment=TA_CENTER, spaceAfter=8,
                              textColor=GRAY)
S["tcell"] = ParagraphStyle("tcell", fontName="Serif", fontSize=9.6, leading=13)
S["tcellB"] = ParagraphStyle("tcellB", fontName="Serif-Bold", fontSize=9.6, leading=13)
S["tcellR"] = ParagraphStyle("tcellR", parent=S["tcell"], alignment=2)
S["toc"] = ParagraphStyle("toc", fontName="Serif", fontSize=10.5, leading=17)

SECTION_PAGES = {}

class Doc(BaseDocTemplate):
    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and getattr(fl, "_is_h1", False):
            SECTION_PAGES[fl.getPlainText()] = self.page

def footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont("Serif", 8.2)
        canvas.setFillColor(GRAY)
        canvas.drawString(0.95 * inch, 0.55 * inch, "ECNUchat, Inc.")
        canvas.drawCentredString(LETTER[0] / 2, 0.55 * inch, "Subject to Completion")
        canvas.drawRightString(LETTER[0] - 0.95 * inch, 0.55 * inch, str(doc.page))
    canvas.restoreState()

def cover_footer(canvas, doc):
    pass

def render_blocks(blocks, story):
    for b in blocks:
        kind = b[0]
        if kind == "h1x":
            story.append(PageBreak()); story.append(Paragraph(b[1], S["h1"]))
            story.append(HRFlowable(width="100%", thickness=0.8, color=NAVY,
                                    spaceAfter=10))
        elif kind == "h1":
            p = Paragraph(b[1], S["h1"]); p._is_h1 = True
            story.append(PageBreak()); story.append(p)
            story.append(HRFlowable(width="100%", thickness=0.8, color=NAVY,
                                    spaceAfter=10))
        elif kind == "h2":
            story.append(Paragraph(b[1], S["h2"]))
        elif kind == "p":
            story.append(Paragraph(b[1], S["body"]))
        elif kind == "pi":
            story.append(Paragraph(b[1], S["bodyIndent"]))
        elif kind == "risk":
            story.append(Paragraph("<b>%s</b> %s" % (b[1], b[2]), S["body"]))
        elif kind == "bullet":
            story.append(Paragraph(b[1], S["bullet"], bulletText="•"))
        elif kind == "center":
            story.append(Paragraph(b[1], S["center"]))
        elif kind == "small":
            story.append(Paragraph(b[1], S["small"]))
        elif kind == "caption":
            story.append(Paragraph(b[1], S["caption"]))
        elif kind == "sp":
            story.append(Spacer(1, b[1]))
        elif kind == "table":
            rows, widths = b[1], b[2]
            data = []
            for ri, row in enumerate(rows):
                cells = []
                for ci, cell in enumerate(row):
                    st = S["tcellB"] if ri == 0 else (S["tcellR"] if ci > 0 and cell.strip().startswith(("$", "[", "—", "(")) or (ci > 0 and ri > 0 and cell.replace(",", "").replace(".", "").strip().isdigit()) else S["tcell"])
                    cells.append(Paragraph(cell, st))
                data.append(cells)
            t = Table(data, colWidths=widths, repeatRows=1, hAlign="CENTER")
            t.setStyle(TableStyle([
                ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
                ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t); story.append(Spacer(1, 8))
        elif kind == "img":
            story.append(Image(b[1], width=b[2], height=b[3], hAlign="CENTER"))
        elif kind == "legend":
            inner = [[Paragraph(b[1], ParagraphStyle("lg", parent=S["small"],
                        textColor=RED, alignment=TA_JUSTIFY))]]
            t = Table(inner, colWidths=[6.4 * inch], hAlign="CENTER")
            t.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 1.1, RED),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
            ]))
            story.append(t); story.append(Spacer(1, 10))

def make_story(toc_pages=None):
    story = []
    # ---------- COVER ----------
    story.append(Spacer(1, 26))
    story.append(Image("/home/hatch/workspace/ecnuchat-prospectus/logo-full.png",
                       width=4.5 * inch, height=4.5 * inch * 720 / 2800, hAlign="CENTER"))
    story.append(Spacer(1, 16))
    story.append(Paragraph("Subject to Completion", ParagraphStyle("c0", parent=S["center"], fontName="Serif-Italic", textColor=RED)))
    story.append(Paragraph("Preliminary Prospectus dated November 20, 2026", ParagraphStyle("c0b", parent=S["center"], fontName="Serif-Italic", textColor=RED)))
    story.append(Spacer(1, 30))
    story.append(Paragraph("50,000,000 Shares", ParagraphStyle("c1", parent=S["center"], fontSize=15, leading=19)))
    story.append(Spacer(1, 8))
    story.append(Paragraph("ECNUchat, Inc.", ParagraphStyle("c2", parent=S["center"], fontName="Serif-Bold", fontSize=25, leading=30, textColor=NAVY)))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Class A Common Stock", ParagraphStyle("c3", parent=S["center"], fontSize=15, leading=19)))
    story.append(Spacer(1, 26))
    for blk in content_a.COVER_PARAS:
        story.append(Paragraph(blk, S["body"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph("We have applied to list our Class A common stock on the Nasdaq Global Market under the symbol “<b>ECNC</b>.”", S["center"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Investing in our Class A common stock involves a high degree of risk. You should carefully consider the risks described under “Risk Factors” beginning on page 10 of this prospectus before making a decision to invest in our Class A common stock.</b>", S["body"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Neither the Securities and Exchange Commission nor any state securities commission has approved or disapproved of these securities or determined if this prospectus is truthful or complete. Any representation to the contrary is a criminal offense.", S["body"]))
    story.append(Spacer(1, 16))
    render_blocks(content_a.COVER_TABLE, story)
    story.append(Paragraph("The underwriters expect to deliver the shares against payment in New York, New York on or about November 25, 2026.", S["small"]))
    story.append(Spacer(1, 26))
    story.append(Paragraph("Northgate Securities &nbsp;&nbsp;•&nbsp;&nbsp; Harborline Capital &nbsp;&nbsp;•&nbsp;&nbsp; Summit Peak Securities", ParagraphStyle("uw", parent=S["center"], fontSize=12)))
    story.append(Paragraph("Joint Book-Running Managers", S["smallCenter"]))
    story.append(Spacer(1, 22))
    story.append(Paragraph("Prospectus dated November 20, 2026", S["center"]))
    # ---------- INSIDE FRONT: LEGEND ----------
    story.append(PageBreak())
    render_blocks(content_a.INSIDE_FRONT, story)
    # ---------- TABLE OF CONTENTS ----------
    story.append(PageBreak())
    story.append(Paragraph("TABLE OF CONTENTS", S["h1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=NAVY, spaceAfter=10))
    toc_rows = []
    for title in content_a.TOC_TITLES:
        pg = ""
        if toc_pages and title in toc_pages:
            pg = str(toc_pages[title])
        toc_rows.append([Paragraph(title, S["tcell"]), Paragraph(pg, S["tcellR"])])
    t = Table(toc_rows, colWidths=[5.6 * inch, 0.7 * inch], hAlign="CENTER")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2.2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]))
    story.append(t)
    # ---------- SECTIONS ----------
    for mod in (content_a, content_b, content_c):
        for title, blocks in mod.SECTIONS:
            render_blocks([("h1", title)] + blocks, story)
    # ---------- END OF PART I: DEALER OBLIGATION, THEN PART II ----------
    render_blocks(content_d.DEALER, story)
    story.append(PageBreak())
    render_blocks(content_d.PARTII_INTRO, story)
    render_blocks(content_d.ITEMS, story)
    render_blocks(content_d.SIGNATURES, story)
    return story

def build(out):
    doc = Doc(out, pagesize=LETTER, leftMargin=0.95 * inch, rightMargin=0.95 * inch,
              topMargin=0.8 * inch, bottomMargin=0.8 * inch,
              title="ECNUchat, Inc. — Nasdaq Prospectus (Form S-1)",
              author="ECNUchat, Inc.")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=footer)])
    doc.build(make_story())
    pages = dict(SECTION_PAGES)
    SECTION_PAGES.clear()
    doc2 = Doc(out, pagesize=LETTER, leftMargin=0.95 * inch, rightMargin=0.95 * inch,
               topMargin=0.8 * inch, bottomMargin=0.8 * inch,
               title="ECNUchat, Inc. — Nasdaq Prospectus (Form S-1)",
               author="ECNUchat, Inc.")
    doc2.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=footer)])
    doc2.build(make_story(toc_pages=pages))
    print("built:", out)

if __name__ == "__main__":
    build("/home/hatch/workspace/ecnuchat-prospectus/ECNUchat-Form-S-1-Prospectus.pdf")
