"""Theory · Prep · Units 3 to 8 and the review page. Called by build_theory.py, which holds the page furniture (Page) and Units 1 and 2.

Staff positions count from 0 = the bottom line, 1 = the first space ... 8 = the top line. Clefs and the quarter rest come from the
FreeSerif font's music symbols; noteheads, stems, half and whole rests, bar lines and time signatures are drawn here."""
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph

FS = "/usr/share/fonts/truetype/freefont/"
pdfmetrics.registerFont(TTFont("Mus", FS + "FreeSerif.ttf")); pdfmetrics.registerFont(TTFont("Dyn", FS + "FreeSerifBoldItalic.ttf"))
LET = "CDEFGAB"; FIRST = {"treble": 2, "bass": 4}              # the letter on the bottom line: E in the treble clef, G in the bass clef
name_of = lambda clef, pos: LET[(FIRST[clef] + pos) % 7]


import random
RNG = random.Random(2026)                                   # the book is the same every time it is built


def setup(B):
    """Take the page furniture from build_theory.py."""
    global Page, INK, ACC, ACC_TEXT, TINT, MUTED, RULE, W, H, M, P, BODY, BOTTOM
    Page, INK, ACC, ACC_TEXT, TINT, MUTED, RULE, W, H, M, P, BODY, BOTTOM = B.Page, B.INK, B.ACC, B.ACC_TEXT, B.TINT, B.MUTED, B.RULE, B.W, B.H, B.M, B.P, B.BODY, B.BOTTOM


# ---------------------------------------------------------------- drawing
def clef(p, x, kind):
    c = p.c; c.setFillColor(HexColor(INK)); c.setFont("Mus", p.sp * 4); c.drawString(x, p.base, "\U0001D11E" if kind == "treble" else "\U0001D122")


def free(p, y, sp=15):                                     # draw notes with no staff: "line 3" is at y
    p.sp, p.base = sp, y - 2 * sp


def note(p, x, pos, kind="w", color=None):
    c = p.c; sp = p.sp; y = p.base + pos * sp / 2; col = HexColor(color or INK); c.setStrokeColor(col); c.setLineWidth(1.2)
    for q in list(range(-2, pos - 1, -2)) + list(range(10, pos + 1, 2)): c.line(x - sp * 0.95, p.base + q * sp / 2, x + sp * 0.95, p.base + q * sp / 2)   # ledger lines
    c.saveState(); c.translate(x, y); c.rotate(18); c.setFillColor(col if kind == "q" else white); c.setLineWidth(1.2 if kind == "q" else 2.4)
    c.ellipse(-sp * 0.6, -sp * 0.39, sp * 0.6, sp * 0.39, fill=1, stroke=1); c.restoreState()
    if kind in "qh":
        c.setLineWidth(1.5)
        if pos < 4: c.line(x + sp * 0.62, y + 2, x + sp * 0.62, y + sp * 3.4)
        else: c.line(x - sp * 0.62, y - 2, x - sp * 0.62, y - sp * 3.4)


def rest(p, x, kind):
    c = p.c; sp = p.sp; c.setFillColor(HexColor(INK))
    if kind == "q": c.setFont("Mus", sp * 4); c.drawCentredString(x, p.base + sp * 0.45, "\U0001D13D")
    elif kind == "h": c.rect(x - sp * 0.6, p.base + 2 * sp, sp * 1.2, sp * 0.5, fill=1, stroke=0)          # sits on line 3
    else: c.rect(x - sp * 0.6, p.base + 2.5 * sp, sp * 1.2, sp * 0.5, fill=1, stroke=0)                    # hangs from line 4


def sym(p, x, s, pos=2):                                    # "q" "h" "w" = notes, "qr" "hr" "wr" = rests
    rest(p, x, s[0]) if s.endswith("r") else note(p, x, pos, s)


BEATS = {"q": 1, "h": 2, "w": 4}
beats = lambda s: BEATS[s[0]]


def bar(p, x, final=False):
    c = p.c; c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.2); c.line(x, p.base, x, p.base + 4 * p.sp)
    if final: c.setLineWidth(3.2); c.line(x + 5, p.base, x + 5, p.base + 4 * p.sp)


def timesig(p, x, top, bottom=4):
    c = p.c; c.setFillColor(HexColor(INK)); c.setFont("Pop-B", p.sp * 2.25)
    if top: c.setFont("Pop-B", p.sp * 2.0); c.drawCentredString(x, p.base + 2 * p.sp + p.sp * 0.28, str(top)); c.drawCentredString(x, p.base + p.sp * 0.28, str(bottom))
    else: c.setStrokeColor(HexColor(MUTED)); c.setLineWidth(1); c.setDash(3, 3); c.setFillColor(white); c.rect(x - p.sp, p.base - 3, p.sp * 2, 4 * p.sp + 6, fill=1, stroke=1); c.setDash()


def label(p, x, y, text, size=11, bold=False, color=None):
    c = p.c; c.setFillColor(HexColor(color or INK)); c.setFont("Pop-B" if bold else "Pop", size); c.drawCentredString(x, y, text)


def box(p, x, w=50):
    c = p.c; c.setStrokeColor(HexColor(MUTED)); c.setLineWidth(1); c.setDash(3, 3); c.rect(x - w / 2, p.base - 8, w, 4 * p.sp + 16, fill=0, stroke=1); c.setDash()


# ---------------------------------------------------------------- exercise shapes
def ex_name(p, n, text, kind, poss, sp=16, done=0, groups=None):
    """Notes on a staff with a blank under each. groups = sizes of note groups, divided by bar lines (words to spell)."""
    if not groups and len(poss) < 14: poss = list(poss) + [RNG.choice([q for q in range(9) if q != poss[-1]]) for _ in range(14 - len(poss))]     # a full line on the wider page
    p.ask(n, text); p.gap(8); p.staff(M, W - 2 * M, sp); clef(p, M + 6, kind)
    x0 = M + sp * 4.2; step = (W - M - x0 - 14) / len(poss); edges = []
    if groups:
        k = 0
        for g in groups[:-1]: k += g; edges.append(k)
    for k, pos in enumerate(poss):
        x = x0 + step * (k + 0.5); note(p, x, pos)
        if k < done: label(p, x, p.base - 30, name_of(kind, pos), 14, True)
        else: p.blank(x, p.base - 30, min(26, step * 0.6))
        if k in edges: bar(p, x0 + step * k)
    p.gap(4 * sp + 43)


def ex_draw(p, n, text, kind, labels, sp=16):
    p.ask(n, text); p.gap(8); p.staff(M, W - 2 * M, sp)
    if kind: clef(p, M + 6, kind)
    x0 = M + sp * 4.6; step = (W - M - x0 - 10) / len(labels)
    for k, t in enumerate(labels):
        x = x0 + step * (k + 0.5); box(p, x, min(52, step - 12)); label(p, x, p.base - 30, t, 12 if len(t) > 3 else 15, True)
    p.gap(4 * sp + 40)


def rhythm(p, measures, top=4, counts=None, bars=True, sp=15, blanks=True):
    """A rhythm on line 2 of a staff. counts: None, or how many measures have their counts written in (the rest get blanks)."""
    p.gap(8); p.staff(M, W - 2 * M, sp); timesig(p, M + sp * 1.6, top)
    x0 = M + sp * 3.6; total = sum(beats(s) for m in measures for s in m); bw = (W - M - x0 - 16) / total; b = 0
    for mi, m in enumerate(measures):
        for s in m:
            x = x0 + bw * (b + 0.45); sym(p, x, s)
            if counts is not None:
                for j in range(beats(s)):
                    xx = x0 + bw * (b + j + 0.45); num = (b + j - sum(beats(t) for mm in measures[:mi] for t in mm)) + 1
                    if mi < counts: label(p, xx, p.base - 28, str(num), 13, True)
                    elif blanks: p.blank(xx, p.base - 28, 16)
            b += beats(s)
        if bars and mi < len(measures) - 1: bar(p, x0 + bw * b - bw * 0.08)
    bar(p, W - M - 6, final=True)
    p.gap(4 * sp + (42 if counts is not None else 18))


def pairs(p, n, text, items, sp=16, hint=None):
    """Pairs of notes in the treble clef with a blank under each pair."""
    p.ask(n, text); p.gap(8); p.staff(M, W - 2 * M, sp); clef(p, M + 6, "treble")
    x0 = M + sp * 4.2; step = (W - M - x0 - 10) / len(items)
    for k, (a, b) in enumerate(items):
        x = x0 + step * (k + 0.5); note(p, x - sp * 1.1, a); note(p, x + sp * 1.1, b)
        if k == 0 and hint: label(p, x, p.base - 30, hint, 14, True)
        else: p.blank(x, p.base - 30, 34)
        if k < len(items) - 1: bar(p, x0 + step * (k + 1))
    p.gap(4 * sp + 43)


def figure(p, rows, h=64):
    """A row of small labelled pictures inside a tinted band (the note-length chart)."""
    c = p.c; c.setFillColor(HexColor(TINT)); c.rect(M, p.y - h - 44, W - 2 * M, h + 44, fill=1, stroke=0); cw = (W - 2 * M) / len(rows)
    for k, (s, title, sub) in enumerate(rows):
        x = M + cw * (k + 0.5); free(p, p.y - h / 2 - 6, 15); sym(p, x, s, 3)
        label(p, x, p.y - h - 14, title, 13, True); label(p, x, p.y - h - 32, sub, 12)
    p.gap(h + 44 + 18)


def sums(p, n, text, items):
    p.ask(n, text, reserve=70 * ((len(items) + 1) // 2)); c = p.c; cw = (W - 2 * M) / 2
    for k, parts in enumerate(items):
        x = M + 30 + (k % 2) * cw; y = p.y - 34 - (k // 2) * 70; free(p, y, 12)
        for j, s in enumerate(parts):
            sym(p, x + j * 50, s, 3)
            if j < len(parts) - 1: label(p, x + j * 50 + 25, y - 4, "+", 17, True)
        xe = x + (len(parts) - 1) * 50 + 30; label(p, xe, y - 4, "=", 17, True); p.blank(xe + 32, y - 8, 30); c.setFont("Pop", 12); c.setFillColor(HexColor(INK)); c.drawString(xe + 52, y - 5, "beats")
    p.gap(70 * ((len(items) + 1) // 2) + 4)


# ---------------------------------------------------------------- the pages
def build(c, first_page):
    n = first_page

    # ============ Unit 3 · the treble clef
    p = Page(c, "Prep", 3, "The treble clef", n); n += 1
    p.learn("The <b>treble clef</b> is for high notes. On the piano the <b>right hand</b> usually plays them. Its curl wraps around line 2, and line 2 is <b>G</b>. "
            "The line notes from the bottom are <b>E G B D F</b>. The space notes from the bottom spell <b>F A C E</b>.")
    ex_draw(p, 1, "Draw a <b>G</b> on line 2 in every box. Say “G” as you draw each one.", "treble", ["G"] * 6)
    ex_name(p, 2, "These are the five <b>line notes</b>. Name them. The first one is done for you.", "treble", (0, 2, 4, 6, 8, 4, 0, 6, 2, 8), done=1)
    ex_name(p, 3, "These are the four <b>space notes</b>. Name them.", "treble", (1, 3, 5, 7, 5, 1, 7, 3, 5, 1))
    p.section("Treble notes")
    ex_name(p, 4, "Lines and spaces together. Name each note.", "treble", (2, 5, 0, 7, 3, 8, 1, 6, 4, 2))
    ex_draw(p, 5, "Draw each note on the staff. Some letters have two places: either one is right.", "treble", list("GBEACFD"))
    ex_name(p, 6, "These notes spell words. Write the letters, then read the words.", "treble", (4, 3, 2, 1, 3, 5, 7, 6, 3, 6, 0, 2, 2), groups=(3, 4, 3, 3))
    p.finish(fill_name('treble'), ["I can say the line notes E G B D F and the space notes F A C E.", "I can name any note on the treble staff.", "I can draw the note for any letter."])
    c.showPage()

    # ============ Unit 4 · the bass clef
    p = Page(c, "Prep", 4, "The bass clef", n); n += 1
    p.learn("The <b>bass clef</b> is for low notes. On the piano the <b>left hand</b> usually plays them. Its two dots sit on each side of line 4, and line 4 is <b>F</b>. "
            "The line notes from the bottom are <b>G B D F A</b>. The space notes from the bottom are <b>A C E G</b>.")
    ex_draw(p, 1, "Draw an <b>F</b> on line 4 in every box. Say “F” as you draw each one.", "bass", ["F"] * 6)
    ex_name(p, 2, "These are the five <b>line notes</b>. Name them. The first one is done for you.", "bass", (0, 2, 4, 6, 8, 6, 2, 8, 0, 4), done=1)
    ex_name(p, 3, "These are the four <b>space notes</b>. Name them.", "bass", (1, 3, 5, 7, 3, 7, 1, 5, 3, 7))
    p.section("Bass notes")
    ex_name(p, 4, "Lines and spaces together. Name each note.", "bass", (4, 1, 6, 3, 8, 0, 5, 2, 7, 4))
    ex_draw(p, 5, "Draw each note on the staff. Some letters have two places: either one is right.", "bass", list("FCGDAEB"))
    ex_name(p, 6, "These notes spell words. Write the letters, then read the words.", "bass", (2, 1, 0, 1, 3, 5, 6, 5, 4, 3, 1, 7, 5), groups=(3, 3, 3, 4))
    p.finish(fill_name('bass'), ["I can say the line notes G B D F A and the space notes A C E G.", "I can name any note on the bass staff.", "I know which hand usually plays each clef."])
    c.showPage()

    # ============ Unit 5 · how long notes last
    p = Page(c, "Prep", 5, "How long notes last", n); n += 1
    p.learn("Music has a steady <b>beat</b>, like a clock ticking. The shape of a note tells you how many beats to hold it.")
    figure(p, [("q", "Quarter note", "1 beat"), ("h", "Half note", "2 beats"), ("w", "Whole note", "4 beats")])
    p.ask(1, "How many beats does each note get? Write the number."); p.gap(8); p.staff(M, W - 2 * M, 16)
    for k, s in enumerate("qhwhqwqhwq"):
        x = M + 44 + k * ((W - 2 * M - 30) / 10); note(p, x, 2, s); p.blank(x, p.base - 30, 24)
    p.gap(4 * 16 + 46)
    ex_draw(p, 2, "Draw each note on line 2. Color in the quarter notes. Add a stem to quarter and half notes.", None, ["Quarter", "Half", "Whole", "Half", "Quarter", "Whole"])
    p.section("Rests")
    p.learn("A <b>rest</b> is a silence. You count it just like a note, but you do not play. The half rest sits on line 3 like a hat. The whole rest hangs from line 4.")
    c.setFillColor(HexColor(TINT)); c.rect(M, p.y - 132, W - 2 * M, 132, fill=1, stroke=0); keep = p.y; p.y -= 16; p.staff(M + 30, W - 2 * M - 60, 15)
    for k, (s, t, sub) in enumerate((("qr", "Quarter rest", "1 beat of silence"), ("hr", "Half rest", "2 beats of silence"), ("wr", "Whole rest", "4 beats of silence"))):
        x = M + 30 + (W - 2 * M - 60) * (k + 0.5) / 3; rest(p, x, s[0]); label(p, x, p.base - 20, t, 13, True); label(p, x, p.base - 37, sub, 12)
        if k: bar(p, M + 30 + (W - 2 * M - 60) * k / 3)
    p.y = keep - 132 - 18
    p.ask(4, "How many beats does each note or rest get? Write the number."); p.gap(8); p.staff(M, W - 2 * M, 16)
    for k, s in enumerate(("q", "qr", "h", "hr", "w", "wr", "qr", "h", "hr", "q")):
        x = M + 44 + k * ((W - 2 * M - 30) / 10); sym(p, x, s); p.blank(x, p.base - 30, 24)
    p.gap(4 * 16 + 46)
    ex_draw(p, 5, "Draw the rest that lasts as long as each note.", None, ["Quarter note", "Half note", "Whole note", "Half note", "Quarter note"])
    p.section("Adding beats")
    sums(p, 6, "Add the beats.", [("q", "q"), ("h", "q"), ("h", "h"), ("q", "q", "q")])
    sums(p, 7, "Now with rests. A rest counts just like a note.", [("q", "qr"), ("h", "hr"), ("w", "qr"), ("hr", "q", "q")])
    p.ask(8, "Clap this line and count the beats out loud: “1, 2, 3, 4”. Hold your hands together on the long notes.")
    rhythm(p, [["q", "q", "h"], ["h", "h"], ["q", "q", "q", "q"], ["w"]], counts=4); p.gap(8)
    p.finish(fill_beats, ["I can say how many beats a quarter, half and whole note get.", "I can tell a half rest from a whole rest.", "I can add up beats."])
    c.showPage()

    # ============ Unit 6 · measures and counting
    p = Page(c, "Prep", 6, "Measures and counting", n); n += 1
    p.learn("<b>Bar lines</b> divide music into <b>measures</b>. The two numbers at the start are the <b>time signature</b>. The top number tells you how many beats are in every measure. "
            "In <b>4/4</b> there are four beats in a measure, so we count 1 2 3 4. A <b>double bar line</b> marks the end.")
    p.ask(1, "Write the counts under the notes. The first measure is done for you. Then clap it and count out loud.")
    rhythm(p, [["q", "q", "h"], ["h", "q", "q"], ["q", "q", "q", "q"], ["w"]], counts=1)
    p.ask(2, "Do the same with this line. A rest gets a count too.")
    rhythm(p, [["q", "qr", "q", "q"], ["h", "hr"], ["q", "q", "h"], ["w"]], counts=0)
    p.ask(3, "The bar lines are missing. Count four beats at a time and draw them in.")
    rhythm(p, [["h", "q", "q"], ["q", "q", "q", "q"], ["w"], ["q", "q", "h"]], bars=False)
    p.ask(4, "Clap this line and count out loud without stopping. Then play it on any one key of your piano.")
    rhythm(p, [["q", "q", "q", "q"], ["h", "h"], ["q", "qr", "q", "qr"], ["h", "q", "q"], ["w"]])
    p.section("Three beats in a measure")
    p.learn("In <b>3/4</b> there are three beats in every measure, so we count 1 2 3. The first beat of a measure is a little stronger than the others.")
    p.ask(4, "Write the counts. Then clap it: beat 1 is the strongest.")
    rhythm(p, [["q", "q", "q"], ["h", "q"], ["q", "h"], ["q", "q", "q"], ["h", "qr"]], top=3, counts=1)
    p.ask(5, "The bar lines are missing. Count three beats at a time and draw them in.")
    rhythm(p, [["q", "q", "q"], ["h", "q"], ["q", "q", "q"], ["q", "h"], ["h", "q"]], top=3, bars=False)
    p.ask(6, "Write the time signature in the box: 4/4 or 3/4.")
    rhythm(p, [["h", "q"], ["q", "q", "q"], ["q", "h"], ["h", "qr"]], top=None); p.gap(4)
    p.finish(fill_counts, ["I can say what the top number of a time signature means.", "I can count and clap in 4/4 and in 3/4.", "I can put bar lines in the right places."])
    c.showPage()

    # ============ Unit 7 · steps and skips
    p = Page(c, "Prep", 7, "Steps and skips", n); n += 1
    p.learn("A <b>step</b> moves from a line to the very next space, or from a space to the very next line. On the piano it is the next white key. "
            "A <b>skip</b> moves from a line to the next line, or from a space to the next space. It skips one key. A <b>repeat</b> stays on the same note.")
    pairs(p, 1, "Step, skip or repeat? Write the word under each pair.", ((2, 3), (1, 3), (4, 4), (6, 5), (7, 5), (0, 2)), hint="step")
    pairs(p, 2, "Does the second note go <b>up</b>, go <b>down</b> or stay the <b>same</b>? Write the word.", ((1, 2), (6, 4), (3, 3), (5, 7), (8, 7), (2, 0)), hint="up")
    p.ask(3, "Draw a note one <b>step up</b> from each note."); p.gap(8); p.staff(M, W - 2 * M, 16); clef(p, M + 6, "treble")
    for k, pos in enumerate((0, 3, 5, 2, 6, 1)):
        x = M + 130 + k * ((W - 2 * M - 110) / 6); note(p, x - 14, pos); box(p, x + 18, 32)
        if k < 5: bar(p, x + (W - 2 * M - 110) / 12 + 8)
    p.gap(4 * 16 + 34)
    p.section("Steps and skips on the piano")
    p.ask(4, "Draw a note one <b>skip down</b> from each note."); p.gap(8); p.staff(M, W - 2 * M, 16); clef(p, M + 6, "treble")
    for k, pos in enumerate((8, 5, 3, 6, 2, 7)):
        x = M + 130 + k * ((W - 2 * M - 110) / 6); note(p, x - 14, pos); box(p, x + 18, 32)
        if k < 5: bar(p, x + (W - 2 * M - 110) / 12 + 8)
    p.gap(4 * 16 + 34)
    p.ask(5, "Start on the blue key. Write <b>X</b> on the key a <b>step up</b>, and <b>O</b> on the key a <b>skip up</b>.", reserve=170)
    for k, s in enumerate((0, 3, 1, 4, 2, 5)):
        x = M + 30 + (k % 3) * ((W - 2 * M) / 3); y0 = p.y - (k // 3) * 78; keep = p.y; p.y = y0; p.keyboard(x, 1, 13, 54, shade=s, extra=3); p.y = keep
    p.gap(78 * 2 + 4)
    p.ask(6, "Follow the tune. Between each pair of notes write <b>S</b> for step, <b>K</b> for skip or <b>R</b> for repeat."); p.gap(8); p.staff(M, W - 2 * M, 16); clef(p, M + 6, "treble")
    tune = (2, 3, 4, 4, 6, 5, 3, 2, 2, 0)
    for k, pos in enumerate(tune):
        x = M + 110 + k * ((W - 2 * M - 90) / 10); note(p, x, pos)
        if k < len(tune) - 1: p.blank(x + (W - 2 * M - 90) / 20, p.base - 30, 22)
    p.gap(4 * 16 + 50)
    p.finish(fill_pairs, ["I can tell a step from a skip on the staff.", "I can play a step and a skip on the piano.", "I can say if a tune goes up, goes down or stays the same."])
    c.showPage()

    # ============ Unit 8 · first words
    p = Page(c, "Prep", 8, "Loud and soft, fast and slow", n); n += 1
    p.learn("Music uses Italian words to say <b>how</b> to play. The words for loud and soft are written under the notes as letters. The words for speed are written above the first measure.")
    p.need(27 * 7 + 30)
    rows = [("f", "forte", "loud"), ("p", "piano", "soft"), ("mf", "mezzo forte", "medium loud"), ("mp", "mezzo piano", "medium soft"), ("", "Allegro", "fast"), ("", "Andante", "walking speed"), ("", "Adagio", "slow")]
    c.setStrokeColor(HexColor(RULE)); c.setLineWidth(1)
    for k, (s, w, m) in enumerate(rows):
        y = p.y - 20 - k * 27; c.setFillColor(HexColor(INK)); c.setFont("Dyn", 22); c.drawCentredString(M + 40, y - 2, s)
        c.setFont("Pop-B", 14); c.drawString(M + 90, y, w); c.setFont("Pop", 14); c.drawString(M + 260, y, m); c.line(M, y - 9, W - M, y - 9)
    p.gap(27 * len(rows) + 16)
    p.ask(1, "Draw a line from each sign or word to what it means.", reserve=190)
    left = ["f", "Adagio", "mp", "Allegro", "p", "Andante", "mf"]; right = ["soft", "fast", "loud", "medium loud", "slow", "medium soft", "walking speed"]
    for k in range(7):
        y = p.y - 16 - k * 24; c.setFillColor(HexColor(INK))
        if len(left[k]) <= 2: c.setFont("Dyn", 20); c.drawRightString(M + 150, y - 2, left[k])
        else: c.setFont("Pop-B", 14); c.drawRightString(M + 150, y, left[k])
        c.circle(M + 166, y + 5, 3, fill=1, stroke=0); c.circle(W - M - 196, y + 5, 3, fill=1, stroke=0); c.setFont("Pop", 14); c.drawString(W - M - 182, y, right[k])
    p.gap(24 * 7 + 12)
    p.ask(2, "Write these four signs in order, from the softest to the loudest:")
    c.setFont("Dyn", 22); c.setFillColor(HexColor(INK)); c.drawString(M + 34, p.y - 20, "f        mp        p        mf")
    for k in range(4):
        p.blank(W - M - 216 + k * 64, p.y - 22, 44)
        if k < 3: c.setFont("Pop", 12); c.drawCentredString(W - M - 184 + k * 64, p.y - 20, "<")
    p.gap(40)

    # ============ review
    p.section("Prep review")
    ex_name(p, 1, "Name each note in the <b>treble clef</b>.", "treble", (2, 7, 0, 5, 3, 8, 1, 6, 4, 2), sp=16)
    ex_name(p, 2, "Name each note in the <b>bass clef</b>.", "bass", (6, 1, 4, 8, 3, 0, 5, 2, 7, 4), sp=16)
    p.ask(3, "Write the counts under the notes, then draw the missing bar lines.")
    rhythm(p, [["q", "q", "h"], ["h", "hr"], ["q", "qr", "q", "q"], ["w"]], counts=0, bars=False, sp=16)
    pairs(p, 4, "Step, skip or repeat?", ((3, 4), (2, 4), (5, 5), (7, 6), (6, 4), (1, 3)), sp=16)
    fs = [fill_keys, fill_beats, fill_counts, fill_ls, fill_name("treble"), fill_name("bass")]; k = 0
    while p.y - BOTTOM - 90 > 150 and k < 10: fs[k % len(fs)](p); k += 1
    p.y = min(p.y, BOTTOM + 70); c.setStrokeColor(HexColor(INK)); c.setLineWidth(1.4); c.setFillColor(HexColor(TINT)); c.rect(M, p.y - 66, W - 2 * M, 66, fill=1, stroke=0)
    c.setFillColor(HexColor(ACC)); c.rect(M, p.y - 66, 5, 66, fill=1, stroke=0)
    c.setFillColor(HexColor(INK)); c.setFont("Pop-B", 15); c.drawString(M + 20, p.y - 26, "I finished Prep. Next: Level 1.")
    c.setFont("Pop", 11.5); c.drawString(M + 20, p.y - 50, "Student ______________   Teacher ______________   Date _________")
    c.showPage()
    return n


# ---------------------------------------------------------------- "more practice": rows that fill the last page of a unit
def fill_keys(p):
    p.ask(0, "More practice. Name the blue key.", reserve=90); cw = (W - 2 * M) / 5
    for k in range(5):
        x = M + 14 + k * cw; p.keyboard(x, 1, 12, 50, shade=RNG.randrange(10), extra=3); p.blank(x + 60, p.y - 68, 44)
    p.gap(88)


def fill_ls(p):
    p.ask(0, "More practice. Write <b>L</b> under each line note and <b>S</b> under each space note."); p.gap(8); p.staff(M, W - 2 * M, 16)
    for k in range(14):
        x = M + 40 + k * ((W - 2 * M - 40) / 14); note(p, x, RNG.randrange(9)); p.blank(x, p.base - 28, 26)
    p.gap(4 * 16 + 44)


def fill_name(kind):
    return lambda p: ex_name(p, 0, "More practice. Name each note.", kind, [RNG.randrange(9)])


def fill_beats(p):
    p.ask(0, "More practice. How many beats? Write the number."); p.gap(8); p.staff(M, W - 2 * M, 16)
    for k in range(12):
        x = M + 44 + k * ((W - 2 * M - 30) / 12); sym(p, x, RNG.choice(["q", "h", "w", "qr", "hr", "wr"])); p.blank(x, p.base - 30, 24)
    p.gap(4 * 16 + 46)


def fill_counts(p):
    top = RNG.choice([4, 3]); pats = {4: [["q", "q", "h"], ["h", "q", "q"], ["q", "q", "q", "q"], ["h", "h"], ["q", "qr", "h"], ["w"]], 3: [["q", "q", "q"], ["h", "q"], ["q", "h"], ["h", "qr"]]}[top]
    p.ask(0, "More practice. Write the counts, then clap and count out loud."); rhythm(p, [RNG.choice(pats) for _ in range(5 if top == 3 else 4)], top=top, counts=0)


def fill_pairs(p):
    items = []
    for _ in range(8): a = RNG.randrange(1, 8); items.append((a, max(0, min(8, a + RNG.choice([-2, -1, 0, 1, 2])))))
    pairs(p, 0, "More practice. Step, skip or repeat?", items)
