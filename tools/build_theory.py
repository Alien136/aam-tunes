#!/usr/bin/env python3
"""Alex Attard Music · Theory workbooks. FIRST SAMPLE: Prep, Units 1 and 2 (four pages), to settle the look before the whole book is written.

  python3 tools/build_theory.py            writes tools/out/Theory_Prep_sample.pdf

The look (Alex, 21-22 Nov 2026): cut to the chase, never kiddy. A short "Learn" box, then exercises straight away. Black and white
with one accent color, no cartoons. Prep (age 7) uses large type and a large staff; each level steps down. Piano first. US terms only.
Everything on these pages is drawn here (keyboards, staves, notes): no music engraver is needed until the clefs arrive in Unit 3."""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
INK, ACC, TINT, MUTED, RULE = "#1B2430", "#D4922A", "#FBF1E1", "#5F6B78", "#C9D1D9"
GF, DJ = "/usr/share/fonts/truetype/google-fonts/", "/usr/share/fonts/truetype/dejavu/"
for n, p in [("Pop-B", GF + "Poppins-Bold.ttf"), ("Pop-M", GF + "Poppins-Medium.ttf"), ("Pop", GF + "Poppins-Regular.ttf"), ("DJ", DJ + "DejaVuSans.ttf"), ("DJ-B", DJ + "DejaVuSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(n, p))
pdfmetrics.registerFontFamily("Pop", normal="Pop", bold="Pop-B")
W, H = letter; M = 50
BODY = 14.5                                            # Prep: large type. Later levels step this down.
P = ParagraphStyle("p", fontName="Pop", fontSize=BODY, leading=BODY * 1.42, textColor=HexColor(INK))


class Page:
    def __init__(self, c, level, unit, title, n):
        self.c, self.y = c, H - M
        c.setFillColor(HexColor(ACC)); c.setFont("Pop-B", 10); c.drawString(M, self.y - 8, " ".join((level + "  ·  UNIT " + str(unit)).upper()))
        c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 27); c.drawString(M, self.y - 40, title)
        c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.6); c.line(M, self.y - 52, W - M, self.y - 52)
        c.setFont("Pop", 10); c.setFillColor(HexColor(MUTED)); c.drawString(M, 30, "Alex Attard Music  ·  Theory  ·  " + level); c.drawRightString(W - M, 30, str(n))
        c.drawRightString(W - M, self.y - 8, "Name ______________________")
        self.y -= 72

    def learn(self, text):                                 # the one box that teaches; everything else on the page is doing
        c = self.c; p = Paragraph(text, P); w = W - 2 * M - 32; _, h = p.wrap(w, 400); bh = h + 40
        c.setFillColor(HexColor(TINT)); c.rect(M, self.y - bh, W - 2 * M, bh, fill=1, stroke=0)
        c.setFillColor(HexColor(ACC)); c.rect(M, self.y - bh, 5, bh, fill=1, stroke=0)
        c.setFont("Pop-B", 10); c.drawString(M + 18, self.y - 18, "L E A R N")
        p.drawOn(c, M + 18, self.y - 28 - h); self.y -= bh + 20

    def ask(self, n, text):                                # a numbered instruction
        c = self.c; c.setFillColor(HexColor(INK)); c.circle(M + 11, self.y - 9, 11, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 12); c.drawCentredString(M + 11, self.y - 13.5, str(n))
        p = Paragraph(text, P); _, h = p.wrap(W - 2 * M - 34, 200); p.drawOn(c, M + 32, self.y - h + 3); self.y -= max(h, 22) + 12

    def gap(self, h): self.y -= h

    # ---- the piano. white keys are numbered from 0 = C
    def keyboard(self, x, octaves=2, kw=24, kh=92, start=0, shade=None, labels=None, extra=0):
        c = self.c; n = octaves * 7 + extra; top = self.y; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.3)
        for i in range(n):
            c.setFillColor(HexColor(ACC) if shade == i else white); c.rect(x + i * kw, top - kh, kw, kh, fill=1, stroke=1)
            if labels and i in labels: c.setFillColor(HexColor(INK)); c.setFont("Pop-B", kw * 0.55); c.drawCentredString(x + i * kw + kw / 2, top - kh + 9, labels[i])
        c.setFillColor(HexColor(INK))
        for i in range(n - 1):
            if (i + start) % 7 in (0, 1, 3, 4, 5): c.rect(x + (i + 1) * kw - kw * 0.3, top - kh * 0.6, kw * 0.6, kh * 0.6, fill=1, stroke=0)
        return n * kw

    # ---- the staff. positions count from 0 = the bottom line, 1 = the first space, 2 = the second line ...
    def staff(self, x, w, sp=15):
        c = self.c; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.2); self.base, self.sp = self.y - 4 * sp, sp
        for i in range(5): c.line(x, self.base + i * sp, x + w, self.base + i * sp)
        c.setLineWidth(1.8); c.line(x, self.base, x, self.base + 4 * sp); c.line(x + w, self.base, x + w, self.base + 4 * sp)

    def note(self, x, pos, fill=False):
        c = self.c; sp = self.sp; y = self.base + pos * sp / 2; c.saveState(); c.translate(x, y); c.rotate(18)
        c.setStrokeColor(HexColor(INK)); c.setFillColor(HexColor(INK) if fill else white); c.setLineWidth(2.6); c.ellipse(-sp * 0.62, -sp * 0.4, sp * 0.62, sp * 0.4, fill=1, stroke=1); c.restoreState()

    def blank(self, x, y, w=30):
        c = self.c; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1); c.line(x - w / 2, y, x + w / 2, y)

    def checks(self, items):
        c = self.c; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.4); c.setFont("Pop-B", 10); c.setFillColor(HexColor(ACC)); c.drawString(M, self.y, "C H E C K")
        self.y -= 24
        for t in items:
            c.setFillColor(white); c.rect(M, self.y - 3, 15, 15, fill=1, stroke=1); c.setFillColor(HexColor(INK)); c.setFont("Pop", BODY - 1); c.drawString(M + 26, self.y, t); self.y -= 26


def build():
    out = os.path.join(OUT, "Theory_Prep_sample.pdf"); c = canvas.Canvas(out, pagesize=letter); c.setTitle("Theory · Prep · sample"); c.setAuthor("Alex Attard Music")
    kbx = lambda n, kw: (W - n * kw) / 2

    # ------------------------------------------------ Unit 1, page 1
    p = Page(c, "Prep", 1, "The keyboard", 1)
    p.learn("The black keys come in groups of <b>2</b> and groups of <b>3</b>, all the way along the piano. "
            "Sounds get <b>lower</b> as you move to the left and <b>higher</b> as you move to the right.")
    p.ask(1, "Circle every group of <b>2</b> black keys."); p.keyboard(kbx(22, 23), 3, 23, 96, extra=1); p.gap(96 + 26)
    p.ask(2, "Put an <b>X</b> on every group of <b>3</b> black keys."); p.keyboard(kbx(22, 23), 3, 23, 96, extra=1); p.gap(96 + 26)
    p.ask(3, "Write <b>L</b> on the lowest key and <b>H</b> on the highest key. Then play them both on your piano.")
    p.keyboard(kbx(22, 23), 3, 23, 96, extra=1); p.gap(96 + 10)
    c.showPage()

    # ------------------------------------------------ Unit 1, page 2
    p = Page(c, "Prep", 1, "The musical alphabet", 2)
    p.learn("Music uses seven letters: <b>A B C D E F G</b>. After G comes A again. "
            "<b>C</b> is the white key just to the left of the 2 black keys. <b>F</b> is the white key just to the left of the 3 black keys.")
    p.ask(4, "Fill in the missing letters."); p.gap(10)
    c.setFont("Pop-B", 22); c.setFillColor(HexColor(INK))
    for row in ("A B _ D _ F _ A", "C _ E _ G _ B _", "G _ _ C _ E _ G"):
        x = M + 40
        for ch in row.split():
            if ch == "_": p.blank(x + 8, p.y - 4, 26)
            else: c.drawCentredString(x + 8, p.y - 2, ch)
            x += 62
        p.gap(32)
    p.ask(5, "The first seven keys are named for you. Write the name on every other white key.")
    p.keyboard(kbx(22, 23), 3, 23, 74, extra=1, labels=dict(enumerate("CDEFGAB"))); p.gap(74 + 18)
    p.ask(6, "Name the orange key.")
    for k, s in enumerate((0, 3, 4, 8, 6, 2)):
        x = M + 12 + (k % 3) * 176; y0 = p.y - (k // 3) * 84; keep = p.y; p.y = y0; p.keyboard(x, 1, 13, 50, shade=s, extra=3)
        p.blank(x + 65, y0 - 68, 44); p.y = keep
    c.showPage()

    # ------------------------------------------------ Unit 2, page 1
    p = Page(c, "Prep", 2, "The staff", 3)
    p.learn("Music is written on a <b>staff</b>. A staff has <b>5 lines</b> and <b>4 spaces</b>. We count them from the <b>bottom</b> up: "
            "line 1 is the lowest line, and space 1 is the lowest space.")
    p.ask(1, "Number the lines from 1 to 5. Start at the bottom."); p.gap(6); p.staff(M + 70, W - 2 * M - 140, 18)
    for i in range(5): c.setStrokeColor(HexColor(INK)); c.setFillColor(white); c.setLineWidth(1.2); c.circle(M + 44, p.base + i * 18, 8, fill=1, stroke=1)
    p.gap(4 * 18 + 15)
    p.ask(2, "Number the spaces from 1 to 4. Start at the bottom."); p.gap(6); p.staff(M + 70, W - 2 * M - 140, 18)
    for i in range(4): c.setStrokeColor(HexColor(INK)); c.setFillColor(white); c.circle(M + 44, p.base + i * 18 + 9, 7.5, fill=1, stroke=1)
    p.gap(4 * 18 + 15)
    p.learn("A <b>line note</b> has a line running through its middle. A <b>space note</b> sits between two lines.")
    p.ask(3, "Write <b>L</b> under each line note and <b>S</b> under each space note."); p.gap(8); p.staff(M, W - 2 * M, 17)
    for k, pos in enumerate((2, 5, 0, 7, 4, 1, 8, 3)):
        x = M + 44 + k * 59; p.note(x, pos); p.blank(x, p.base - 26, 30)
    c.showPage()

    # ------------------------------------------------ Unit 2, page 2
    p = Page(c, "Prep", 2, "Lines and spaces", 4)
    p.ask(4, "Where is each note? Write the number of its line or space. The first one is done for you."); p.gap(12); p.staff(M, W - 2 * M, 18)
    for k, pos in enumerate((4, 1, 6, 0, 3, 8, 5, 2)):
        x = M + 44 + k * 59; p.note(x, pos); word = "Line" if pos % 2 == 0 else "Space"
        c.setFont("Pop", 11); c.setFillColor(HexColor(INK)); c.drawCentredString(x - 10, p.base - 30, word)
        if k == 0: c.setFont("Pop-B", 13); c.drawString(x + 10, p.base - 30, "3")
        else: p.blank(x + 20, p.base - 31, 16)
    p.gap(4 * 18 + 54)
    p.ask(5, "Draw a note in each box, on the line or in the space it asks for."); p.gap(10); p.staff(M, W - 2 * M, 18)
    for k, (word, num) in enumerate((("Line", 2), ("Space", 3), ("Line", 5), ("Space", 1), ("Line", 4), ("Space", 4))):
        x = M + 54 + k * 80; c.setStrokeColor(HexColor(RULE)); c.setLineWidth(1); c.setDash(3, 3); c.rect(x - 26, p.base - 8, 52, 4 * 18 + 16, fill=0, stroke=1); c.setDash()
        c.setFont("Pop-M", 12); c.setFillColor(HexColor(INK)); c.drawCentredString(x, p.base - 30, "%s %d" % (word, num))
    p.gap(4 * 18 + 54)
    p.ask(6, "Higher notes sit higher on the staff. Circle the <b>higher</b> note in each pair."); p.gap(12); p.staff(M, W - 2 * M, 18)
    for k, (a, b) in enumerate(((1, 5), (6, 2), (3, 4), (8, 7))):
        x = M + 70 + k * 122; p.note(x - 20, a); p.note(x + 24, b)
        if k < 3: c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.2); c.line(x + 62, p.base, x + 62, p.base + 4 * 18)
    p.gap(4 * 18 + 40)
    p.checks(["I can find groups of 2 and 3 black keys, and every C and F.", "I can say the musical alphabet forward from any letter.", "I can number the lines and spaces of the staff from the bottom."])
    c.showPage(); c.save(); print(out)


if __name__ == "__main__":
    build()
