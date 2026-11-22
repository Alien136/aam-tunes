#!/usr/bin/env python3
"""Alex Attard Music · Theory workbooks. The Prep book (age 7 to 8, piano): a cover, eight units and a review, 18 pages.
Units 1 and 2 are in this file; Units 3 to 8 are in theory_prep_units.py.

  python3 tools/build_theory.py            writes tools/out/Theory_Prep.pdf

The look (Alex, 21-22 Nov 2026): cut to the chase, never kiddy. A short "Learn" box, then exercises straight away. Black and white
with one accent color (the website's blue), no cartoons. Prep (age 7) uses large type and a large staff; each level steps down. Piano first. US terms only.
Everything on these pages is drawn here (keyboards, staves, notes): no music engraver is needed until the clefs arrive in Unit 3."""
import os, sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
INK, ACC, TINT, MUTED, RULE = "#1B2430", "#428AD2", "#EAF2FB", "#5F6B78", "#C9D1D9"      # ACC is the blue of alexattardmusic.com (Alex, 22 Nov)
ACC_TEXT = "#2466B0"                                   # the same blue, deepened so small labels stay readable in print
GF, DJ = "/usr/share/fonts/truetype/google-fonts/", "/usr/share/fonts/truetype/dejavu/"
for n, p in [("Pop-B", GF + "Poppins-Bold.ttf"), ("Pop-M", GF + "Poppins-Medium.ttf"), ("Pop", GF + "Poppins-Regular.ttf"), ("DJ", DJ + "DejaVuSans.ttf"), ("DJ-B", DJ + "DejaVuSans-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(n, p))
pdfmetrics.registerFontFamily("Pop", normal="Pop", bold="Pop-B")
RW, RH = letter
K = 0.71                                               # everything inside a page is drawn on a larger sheet and scaled down by K: type 14.5 -> 10.3 pt, the staff to 11 pt spaces (0.76 at first; Alex asked for 20% more on a page)
W, H = RW / K, RH / K; M = 50                          # (Alex, 22 Nov: the first draft's type was too big; size it like the Beginner Booklets and fit more on a page)
BOTTOM = 62
# Type and staff size by level (Alex, 22 Nov): Level 1 steps up QUICKLY to a mature page. Lower K for later levels.
LEVEL_K = {"Prep": 0.71, "Level 1": 0.66, "Level 2": 0.63, "Level 3": 0.6}
BODY = 14.5
P = ParagraphStyle("p", fontName="Pop", fontSize=BODY, leading=BODY * 1.42, textColor=HexColor(INK))


class Page:
    """One unit. It flows: every block asks for the room it needs and a new page starts by itself when there is none left."""
    count = 2                                              # the cover and the contents page come first

    def __init__(self, c, level, unit, title, n=None):
        self.c, self.level, self.unit, self.title, self.num = c, level, unit, title, 0; self.head()

    def head(self):
        Page.count += 1; c = self.c; c.scale(K, K); self.y = H - M
        c.setFillColor(HexColor(ACC)); c.rect(0, H - 14, W, 14, fill=1, stroke=0)
        c.setFillColor(HexColor(ACC_TEXT)); c.setFont("Pop-B", 10); c.drawString(M, self.y - 8, " ".join((self.level + "  ·  UNIT " + str(self.unit)).upper()))
        c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 27); c.drawString(M, self.y - 40, self.title)
        c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.6); c.line(M, self.y - 52, W - M, self.y - 52)
        c.setFont("Pop", 10); c.setFillColor(HexColor(MUTED)); c.drawString(M, 30, "Alex Attard Music  ·  Theory  ·  " + self.level); c.drawRightString(W - M, 30, str(Page.count))
        c.drawRightString(W - M, self.y - 8, "Name ______________________")
        self.y -= 72; self.top = self.y

    def need(self, h):                                     # room for a block of this height, or a new page
        title = getattr(self, "pending", None)
        if self.y - h - (54 if title else 0) < BOTTOM: self.c.showPage(); self.head()
        if title:                                          # a section heading waits for the block under it, so it is never left alone at the foot of a page
            self.pending = None
            if self.y < self.top - 5: self.y -= 10
            c = self.c; c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 20); c.drawString(M, self.y - 16, title)
            c.setStrokeColor(HexColor(ACC)); c.setLineWidth(2.5); c.line(M, self.y - 26, M + 46, self.y - 26); self.y -= 44

    def section(self, title):                              # a second topic inside the unit
        self.pending = title

    def learn(self, text):                                 # the one box that teaches; everything else on the page is doing
        c = self.c; p = Paragraph(text, P); w = W - 2 * M - 32; _, h = p.wrap(w, 400); bh = h + 40; self.need(bh + 186)
        c.setFillColor(HexColor(TINT)); c.rect(M, self.y - bh, W - 2 * M, bh, fill=1, stroke=0)
        c.setFillColor(HexColor(ACC)); c.rect(M, self.y - bh, 5, bh, fill=1, stroke=0)
        c.setFillColor(HexColor(ACC_TEXT)); c.setFont("Pop-B", 10); c.drawString(M + 18, self.y - 18, "L E A R N")
        p.drawOn(c, M + 18, self.y - 28 - h); self.y -= bh + 15

    def ask(self, n, text, reserve=140):                   # a numbered instruction (numbered by the unit, whatever n says)
        p = Paragraph(text, P); _, h = p.wrap(W - 2 * M - 34, 200); self.need(max(h, 22) + 9 + reserve); self.num += 1
        c = self.c; c.setFillColor(HexColor(INK)); c.circle(M + 11, self.y - 9, 11, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 12); c.drawCentredString(M + 11, self.y - 13.5, str(self.num))
        p.drawOn(c, M + 32, self.y - h + 3); self.y -= max(h, 22) + 9

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
        self.need(26 * len(items) - 6)                    # the checklist may sit a little into the foot margin sooner than go alone onto a new page
        c = self.c; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.4); c.setFont("Pop-B", 10); c.setFillColor(HexColor(ACC_TEXT)); c.drawString(M, self.y, "C H E C K")
        self.y -= 24
        for t in items:
            c.setFillColor(white); c.rect(M, self.y - 3, 15, 15, fill=1, stroke=1); c.setFillColor(HexColor(INK)); c.setFont("Pop", BODY - 1); c.drawString(M + 26, self.y, t); self.y -= 26

    def finish(self, filler, items):                       # end of a unit: more practice until the page is full, then the checklist
        room = 30 + 26 * len(items); k = 0
        while filler and self.y - BOTTOM - room > 150 and k < 10: filler(self); k += 1
        self.y = min(self.y, BOTTOM + room + 2)           # the checklist sits at the foot of the unit's last page
        self.checks(items)


def piano_art(c, x, y, w, h, white_keys=21, lit=()):
    """The cover's piano: a keyboard seen from the front, with a few keys lit in the website's blue."""
    kw = w / white_keys; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1)
    for i in range(white_keys):
        c.setFillColor(HexColor(ACC) if i in lit else white); c.rect(x + i * kw, y, kw, h, fill=1, stroke=1)
    c.setFillColor(HexColor(INK))
    for i in range(white_keys - 1):
        if i % 7 in (0, 1, 3, 4, 5): c.roundRect(x + (i + 1) * kw - kw * 0.29, y + h * 0.4, kw * 0.58, h * 0.6, 2, fill=1, stroke=0)
    c.rect(x, y + h, w, 10, fill=1, stroke=0)


def build():
    out = os.path.join(OUT, "Theory_Prep.pdf"); c = canvas.Canvas(out, pagesize=letter); c.setTitle("Theory · Prep"); c.setAuthor("Alex Attard Music")
    kbx = lambda n, kw: (W - n * kw) / 2

    import theory_prep_units as U                          # Units 3 to 8, the review, and the "more practice" rows
    U.setup(sys.modules[__name__])
    # ------------------------------------------------ cover (drawn at full size)
    c.setFillColor(HexColor("#F4F8FD")); c.rect(0, 0, RW, RH, fill=1, stroke=0)
    c.setFillColor(HexColor(ACC)); c.rect(0, RH - 10, RW, 10, fill=1, stroke=0)
    c.setFillColor(HexColor(ACC_TEXT)); c.setFont("Pop-B", 11); c.drawString(54, RH - 70, "A L E X   A T T A R D   M U S I C")
    c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 84); c.drawString(50, RH - 190, "Theory")
    c.setFillColor(HexColor(ACC)); c.setFont("Pop-B", 40); c.drawString(54, RH - 244, "Prep")
    c.setFillColor(HexColor(MUTED)); c.setFont("Pop", 15); c.drawString(54, RH - 276, "The first book  ·  Piano")
    sp = 13; base = RH - 400; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1)          # a staff running off both edges, with the first chord a pianist learns
    for i in range(5): c.line(0, base + i * sp, RW, base + i * sp)
    c.setFillColor(HexColor(INK)); c.setFont("Mus", sp * 4); c.drawString(54, base, "\U0001D11E")
    for x, pos in ((250, 0), (330, 2), (410, 4)):
        c.saveState(); c.translate(x, base + pos * sp / 2); c.rotate(18); c.setStrokeColor(HexColor(ACC)); c.setFillColor(HexColor("#F4F8FD")); c.setLineWidth(3); c.ellipse(-sp * 0.62, -sp * 0.4, sp * 0.62, sp * 0.4, fill=1, stroke=1); c.restoreState()
    piano_art(c, -12, 150, RW + 24, 170, 21, lit=(9, 11, 13))                                # E, G and B: the three notes on the staff above
    c.setFillColor(HexColor(INK)); c.setFont("Pop", 13); c.drawString(54, 96, "This book belongs to  ____________________________________")
    c.setFillColor(HexColor(MUTED)); c.setFont("Pop", 9.5); c.drawString(54, 50, "Edition 2  ·  November 2026  ·  alexattardmusic.com/theory"); c.showPage()

    # ------------------------------------------------ contents and how to use the book
    c.scale(K, K); y = H - M
    c.setFillColor(HexColor(ACC)); c.rect(0, H - 14, W, 14, fill=1, stroke=0)
    c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 27); c.drawString(M, y - 40, "In this book"); c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.6); c.line(M, y - 52, W - M, y - 52); y -= 92
    for k, (t, d) in enumerate((("The keyboard", "Black keys in twos and threes, and the seven letter names"), ("The staff", "Five lines, four spaces, line notes and space notes"),
                                ("The treble clef", "The right hand's notes: E G B D F and F A C E"), ("The bass clef", "The left hand's notes: G B D F A and A C E G"),
                                ("How long notes last", "Quarter, half and whole notes, and their rests"), ("Measures and counting", "Bar lines, 4/4 and 3/4"),
                                ("Steps and skips", "How a tune moves, on the staff and on the piano"), ("Loud and soft, fast and slow", "The first seven words every player needs"))):
        c.setFillColor(HexColor(ACC)); c.circle(M + 15, y + 5, 15, fill=1, stroke=0); c.setFillColor(white); c.setFont("Pop-B", 15); c.drawCentredString(M + 15, y, str(k + 1))
        c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 16); c.drawString(M + 46, y + 6, t); c.setFillColor(HexColor(MUTED)); c.setFont("Pop", 13); c.drawString(M + 46, y - 12, d); y -= 54
    y -= 16; c.setFillColor(HexColor(TINT)); c.rect(M, y - 250, W - 2 * M, 250, fill=1, stroke=0); c.setFillColor(HexColor(ACC)); c.rect(M, y - 250, 5, 250, fill=1, stroke=0)
    c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 18); c.drawString(M + 22, y - 34, "How to use this book")
    for k, t in enumerate(("<b>Read the blue Learn box first.</b> It is short on purpose. Read it out loud.", "<b>Then do the numbered exercises in pencil.</b> The first answer is often done for you.",
                           "<b>Sit at the piano.</b> When an exercise shows a key or a note, find it and play it.", "<b>Tick the Check boxes at the end of each unit</b> with your teacher.",
                           "<b>Practice between lessons</b> with the free flash cards at alexattardmusic.com/theory.")):
        pp = Paragraph(t, P); _, h = pp.wrap(W - 2 * M - 70, 100); pp.drawOn(c, M + 44, y - 60 - k * 38 - h + 14); c.setFillColor(HexColor(ACC)); c.circle(M + 28, y - 52 - k * 38, 4, fill=1, stroke=0)
    c.setFont("Pop", 10); c.setFillColor(HexColor(MUTED)); c.drawString(M, 30, "Alex Attard Music  ·  Theory  ·  Prep"); c.drawRightString(W - M, 30, "2"); c.showPage()
    Page.count = 2

    # ------------------------------------------------ Unit 1, page 1
    p = Page(c, "Prep", 1, "The keyboard", 1)
    p.learn("The black keys come in groups of <b>2</b> and groups of <b>3</b>, all the way along the piano. "
            "Sounds get <b>lower</b> as you move to the left and <b>higher</b> as you move to the right.")
    p.ask(1, "Circle every group of <b>2</b> black keys."); p.keyboard(kbx(29, 23), 4, 23, 92, extra=1); p.gap(96 + 26)
    p.ask(2, "Put an <b>X</b> on every group of <b>3</b> black keys."); p.keyboard(kbx(29, 23), 4, 23, 92, extra=1); p.gap(96 + 26)
    p.ask(3, "Write <b>L</b> on the lowest key and <b>H</b> on the highest key. Then play them both on your piano.")
    p.keyboard(kbx(29, 23), 4, 23, 92, extra=1); p.gap(96 + 10)
    p.gap(14); p.ask(4, "Write <b>2</b> or <b>3</b> under each group of black keys.")
    x0 = kbx(29, 23); p.keyboard(x0, 4, 23, 92, extra=1)
    for o in range(4): p.blank(x0 + (o * 7 + 1.5) * 23, p.y - 92 - 22, 22); p.blank(x0 + (o * 7 + 5) * 23, p.y - 92 - 22, 22)
    p.gap(92 + 40)
    p.section("The musical alphabet")
    p.learn("Music uses seven letters: <b>A B C D E F G</b>. After G comes A again. "
            "<b>C</b> is the white key just to the left of the 2 black keys. <b>F</b> is the white key just to the left of the 3 black keys.")
    p.ask(4, "Fill in the missing letters."); p.gap(10)
    c.setFont("Pop-B", 22); c.setFillColor(HexColor(INK))
    for row in ("A B _ D _ F _ A", "C _ E _ G _ B _", "G _ _ C _ E _ G"):
        x = M + 120
        for ch in row.split():
            if ch == "_": p.blank(x + 8, p.y - 4, 26)
            else: c.drawCentredString(x + 8, p.y - 2, ch)
            x += 62
        p.gap(32)
    p.ask(5, "The first seven keys are named for you. Write the name on every other white key.")
    p.keyboard(kbx(29, 23), 4, 23, 80, extra=1, labels=dict(enumerate("CDEFGAB"))); p.gap(74 + 18)
    p.ask(6, "Name the blue key.", reserve=180)
    for k, s in enumerate((0, 3, 4, 8, 6, 2)):
        x = M + 30 + (k % 3) * ((W - 2 * M) / 3); y0 = p.y - (k // 3) * 84; keep = p.y; p.y = y0; p.keyboard(x, 1, 13, 50, shade=s, extra=3)
        p.blank(x + 65, y0 - 68, 44); p.y = keep
    p.gap(84 * 2 + 6)
    p.finish(U.fill_keys, ["I can find groups of 2 and 3 black keys, and every C and F.", "I can say the musical alphabet forward from any letter.", "I can name any white key on the piano."])
    c.showPage()

    # ------------------------------------------------ Unit 2
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
        x = M + 60 + k * ((W - 2 * M - 80) / 8); p.note(x, pos); p.blank(x, p.base - 26, 30)
    p.gap(4 * 17 + 44); p.section("Lines and spaces")
    p.ask(4, "Where is each note? Write the number of its line or space. The first one is done for you."); p.gap(12); p.staff(M, W - 2 * M, 18)
    for k, pos in enumerate((4, 1, 6, 0, 3, 8, 5, 2)):
        x = M + 60 + k * ((W - 2 * M - 80) / 8); p.note(x, pos); word = "Line" if pos % 2 == 0 else "Space"
        c.setFont("Pop", 11); c.setFillColor(HexColor(INK)); c.drawCentredString(x - 10, p.base - 30, word)
        if k == 0: c.setFont("Pop-B", 13); c.drawString(x + 10, p.base - 30, "3")
        else: p.blank(x + 20, p.base - 31, 16)
    p.gap(4 * 18 + 54)
    p.ask(5, "Draw a note in each box, on the line or in the space it asks for."); p.gap(10); p.staff(M, W - 2 * M, 18)
    for k, (word, num) in enumerate((("Line", 2), ("Space", 3), ("Line", 5), ("Space", 1), ("Line", 4), ("Space", 4))):
        x = M + 80 + k * ((W - 2 * M - 80) / 6); c.setStrokeColor(HexColor(RULE)); c.setLineWidth(1); c.setDash(3, 3); c.rect(x - 26, p.base - 8, 52, 4 * 18 + 16, fill=0, stroke=1); c.setDash()
        c.setFont("Pop-M", 12); c.setFillColor(HexColor(INK)); c.drawCentredString(x, p.base - 30, "%s %d" % (word, num))
    p.gap(4 * 18 + 54)
    p.ask(6, "Higher notes sit higher on the staff. Circle the <b>higher</b> note in each pair."); p.gap(12); p.staff(M, W - 2 * M, 18)
    for k, (a, b) in enumerate(((1, 5), (6, 2), (3, 4), (8, 7))):
        x = M + 110 + k * ((W - 2 * M - 60) / 4); p.note(x - 20, a); p.note(x + 24, b)
        if k < 3: c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.2); c.line(x + 62, p.base, x + 62, p.base + 4 * 18)
    p.gap(4 * 18 + 40)
    p.finish(U.fill_ls, ["I can number the lines and spaces of the staff from the bottom.", "I can tell a line note from a space note.", "I can say which of two notes is higher."])
    c.showPage()
    U.build(c, 5)
    c.save(); print(out)


if __name__ == "__main__":
    build()
