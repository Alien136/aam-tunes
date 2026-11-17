#!/usr/bin/env python3
"""Alex Attard Music — Saxophone Welcome Booklet.

Text pages: ReportLab.  Music pages: LilyPond.  Merged with pypdf, then a shared footer is stamped on.
Usage: python3 build_book.py [alto|tenor]
"""
import os, re, subprocess, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # gen_study.py (from the lead-sheet skill) sits next to this file
from gen_study import Note, spell_degree  # noqa: E402

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph, Frame, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader, PdfWriter

EDITION = sys.argv[1] if len(sys.argv) > 1 else "alto"
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

SLATE, AMBER, TINT, MUTED, RULE = "#2F3E4E", "#D4922A", "#FBF1E1", "#6B7785", "#D9DEE3"
GF = "/usr/share/fonts/truetype/google-fonts/"
DJ = "/usr/share/fonts/truetype/dejavu/"
for name, path in [("Pop-B", GF + "Poppins-Bold.ttf"), ("Pop-M", GF + "Poppins-Medium.ttf"),
                   ("Pop-L", GF + "Poppins-Light.ttf"), ("Pop", GF + "Poppins-Regular.ttf"),
                   ("DJ", DJ + "DejaVuSans.ttf"), ("DJ-B", DJ + "DejaVuSans-Bold.ttf"), ("DJ-I", DJ + "DejaVuSans-Oblique.ttf")]:
    pdfmetrics.registerFont(TTFont(name, path))

from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('DJ', normal='DJ', bold='DJ-B', italic='DJ-I', boldItalic='DJ-B')
W, H = letter
M = 54  # 0.75 in margins

body = ParagraphStyle("body", fontName="DJ", fontSize=10.5, leading=15.5, textColor=HexColor(SLATE), spaceAfter=8)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=14, bulletIndent=2, spaceAfter=4)
h2 = ParagraphStyle("h2", fontName="Pop-B", fontSize=13, leading=18, textColor=HexColor(SLATE), spaceBefore=10, spaceAfter=6)


def draw_mixed(c, x, y, text, font, size):
    """Draw text in a Poppins font, switching to DejaVu for glyphs Poppins lacks (♭ ♯ ♩)."""
    alt = "DJ-B" if font in ("Pop-B", "Pop-M") else "DJ"
    for part in re.split("([♭♯♩])", text):
        if not part:
            continue
        f = alt if part in "♭♯♩" else font
        c.setFont(f, size); c.drawString(x, y, part)
        x += pdfmetrics.stringWidth(part, f, size)


def header(c, kicker, title, y=H - M):
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 9)
    c.drawString(M, y - 10, " ".join(kicker.upper()))
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 26)
    c.drawString(M, y - 42, title)
    c.setStrokeColor(HexColor(AMBER)); c.setLineWidth(2.5)
    c.line(M, y - 54, M + 60, y - 54)
    return y - 70


def flow(c, items, top, bottom=M + 20):
    f = Frame(M, bottom, W - 2 * M, top - bottom, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0)
    f.addFromList(items, c)


def tip_box(c, x, y, w, title, lines):
    """Amber-tinted box with a title and bullet lines; returns bottom y."""
    paras = [Paragraph(f"<font name='Pop-B' color='{SLATE}'>{title}</font>", ParagraphStyle("t", parent=body, fontSize=11, spaceAfter=6))]
    paras += [Paragraph(l, bullet, bulletText="•") for l in lines]
    hgt = sum(p.wrap(w - 28, 1000)[1] + p.getSpaceAfter() for p in paras) + 22
    c.setFillColor(HexColor(TINT)); c.setStrokeColor(HexColor(AMBER)); c.setLineWidth(0)
    c.roundRect(x, y - hgt, w, hgt, 8, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.rect(x, y - hgt, 4, hgt, fill=1, stroke=0)
    f = Frame(x + 16, y - hgt + 8, w - 28, hgt - 14, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f.addFromList(paras, c)
    return y - hgt


# ---------------------------------------------------------------- drawn saxophone (original illustration)
import math


def _bez(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n + 1):
        t = i / n; m = 1 - t
        out.append((m**3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t**3 * p3[0],
                    m**3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t**3 * p3[1]))
    return out


def _tube(pts, widths):
    L, R = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        w = widths[i] / 2
        L.append((x + nx * w, y + ny * w)); R.append((x - nx * w, y - ny * w))
    return L + R[::-1]


def draw_sax(c, ox, oy, s, body=AMBER, dark="#8A5A12", pearl=TINT, tenor=False):
    """Stylised saxophone; (ox, oy) = bottom-left of a 100 x 200 unit box, s = points per unit."""
    P = lambda x, y: (ox + x * s, oy + y * s)
    neck = _bez((14, 186), (30, 196), (44, 192), (50, 176), 20) if tenor else _bez((14, 188), (32, 192), (46, 186), (50, 172), 20)
    bodyl = _bez((50, 172), (51, 130), (50, 90), (48, 52), 30)
    bow = _bez((48, 52), (46, 18), (78, 10), (82, 40), 30)
    bell = _bez((82, 40), (84, 60), (84, 80), (86, 104), 20)
    pts = neck + bodyl[1:] + bow[1:] + bell[1:]
    n1, n2, n3 = len(neck), len(bodyl) - 1, len(bow) - 1
    widths = []
    for i in range(len(pts)):
        if i < n1:
            w = 3.6 + 2.6 * i / n1
        elif i < n1 + n2:
            w = 6.2 + 7.8 * (i - n1) / n2
        elif i < n1 + n2 + n3:
            w = 14.0 + 3.0 * (i - n1 - n2) / n3
        else:
            t = (i - n1 - n2 - n3) / (len(pts) - n1 - n2 - n3)
            w = 17.0 + 21.0 * t ** 2.2
        widths.append(w)
    poly = [P(x, y) for x, y in _tube(pts, widths)]
    p = c.beginPath(); p.moveTo(*poly[0])
    for q in poly[1:]:
        p.lineTo(*q)
    p.close()
    c.setFillColor(HexColor(body)); c.setStrokeColor(HexColor(dark)); c.setLineWidth(0.6 * s)
    c.drawPath(p, fill=1, stroke=1)
    bx, by = P(86, 104)
    c.setFillColor(HexColor(dark)); c.ellipse(bx - 19.5 * s, by - 3.4 * s, bx + 19.5 * s, by + 3.4 * s, fill=1, stroke=0)
    c.setFillColor(HexColor(body)); c.ellipse(bx - 19.5 * s, by - 1.2 * s, bx + 19.5 * s, by + 3.4 * s, fill=1, stroke=0)
    mx, my = P(14, 186 if tenor else 188)
    c.setFillColor(HexColor("#1E2833"))
    c.saveState(); c.translate(mx, my); c.rotate(10)
    c.roundRect(-13 * s, -2.6 * s, 14 * s, 5.2 * s, 2.4 * s, fill=1, stroke=0)
    c.setFillColor(HexColor(dark)); c.rect(-4 * s, -3 * s, 2.2 * s, 6 * s, fill=1, stroke=0)
    c.restoreState()
    for t in [0.12, 0.22, 0.32, 0.47, 0.57, 0.67]:
        x, y = bodyl[int(t * 30)]
        X, Y = P(x - 3.4 - t * 4.2, y)
        c.setFillColor(HexColor(dark)); c.circle(X, Y, 2.9 * s, fill=1, stroke=0)
        c.setFillColor(HexColor(pearl)); c.circle(X, Y, 1.9 * s, fill=1, stroke=0)
    for t in [0.8, 0.9]:
        x, y = bodyl[int(t * 30)]
        X, Y = P(x + 4.5, y)
        c.setFillColor(HexColor(dark)); c.circle(X, Y, 3.6 * s, fill=1, stroke=0)
        c.setFillColor(HexColor(body)); c.circle(X, Y, 2.4 * s, fill=1, stroke=0)
    for t in [0.35, 0.6, 0.85]:
        x, y = bell[int(t * 20)]
        X, Y = P(x - 8 - t * 9, y)
        c.setFillColor(HexColor(dark)); c.circle(X, Y, 3.4 * s, fill=1, stroke=0)
        c.setFillColor(HexColor(body)); c.circle(X, Y, 2.2 * s, fill=1, stroke=0)
    c.setStrokeColor(HexColor(dark)); c.setLineWidth(1.0 * s)
    a, b = P(*neck[6]), P(*neck[16])
    c.line(a[0], a[1] + 3 * s, b[0] + 2 * s, b[1] + 3 * s)


# ---------------------------------------------------------------- cover staff (engraved, clef follows the instrument)
INSTRUMENT = "saxophone"  # this book; other books set their own
CLEF_BY_INSTRUMENT = {"saxophone": "treble", "clarinet": "treble", "flute": "treble", "oboe": "treble", "trumpet": "treble",
                      "violin": "treble", "piano": "grand", "trombone": "bass", "bassoon": "bass", "cello": "bass", "tuba": "bass"}


def _rgb(hexcol):
    h = hexcol.lstrip("#")
    return "(rgb-color " + " ".join(f"{int(h[i:i + 2], 16) / 255:.3f}" for i in (0, 2, 4)) + ")"


def cover_staff_png(instrument=INSTRUMENT):
    """Amber clef and beamed eighth notes on soft slate staff lines, transparent PNG for the cover."""
    clef = CLEF_BY_INSTRUMENT.get(instrument, "treble")
    ink, line = _rgb(AMBER), _rgb("#5A6E82")
    colors = ("\\override NoteHead.color = #" + ink + " \\override Stem.color = #" + ink + " \\override Beam.color = #" + ink
              + " \\override Staff.Clef.color = #" + ink + " \\override Flag.color = #" + ink + " \\override Staff.BarLine.color = #" + ink
              + " \\override Staff.StaffSymbol.color = #" + line + " \\override Staff.StaffSymbol.thickness = #1.3" + " \\override Staff.LedgerLineSpanner.color = #" + line
              + " \\override Staff.SystemStartBar.color = #" + ink + " \\override Stem.thickness = #1.6 \\override Beam.beam-thickness = #0.55")
    treble = "\\clef treble \\cadenzaOn e'8[ g' b' d''] f''[ e'' d'' c''] b'[ d'' g'' f''] e''4 \\bar \"|\""
    bass = "\\clef bass \\cadenzaOn c4 g, a, e, f, g, c \\bar \"|\""
    if clef == "grand":
        music = ("\\new PianoStaff \\with { \\override SystemStartBrace.color = #" + ink + " \\override SpanBar.color = #" + ink + " } << \\new Staff { " + colors + " "
                 + treble + " } \\new Staff { " + colors + " " + bass + " } >>")
    elif clef == "bass":
        music = "\\new Staff { " + colors + " " + bass + " }"
    else:
        music = "\\new Staff { " + colors + " " + treble + " }"
    src = ('\\version "2.24.0"\n#(set-global-staff-size 26)\n\\paper { indent = 0 line-width = 88\\mm ragged-right = ##f tagline = ##f }\n'
           '\\layout { \\context { \\Staff \\remove Time_signature_engraver } }\n' + music + "\n")
    p = f"{OUT}/cover_staff_{clef}"
    open(p + ".ly", "w").write(src)
    subprocess.run(["lilypond", "-s", "--png", "-dpixmap-format=pngalpha", "-dresolution=400", "-dcrop", "-o", p, p + ".ly"], check=True)
    return p + ".cropped.png", clef


# ---------------------------------------------------------------- play-along QR codes
# book_player.py publishes the exercises and writes out/qr_<edition>.json: {"code", "first", "pages": {page: slug}}
import json
QR_PATH = os.path.join(OUT, "qr_%s.json" % EDITION)
QR = json.load(open(QR_PATH)) if os.path.exists(QR_PATH) else None
PLAY = "https://alexattardmusic.com/play/"


def qr_image(slug):
    """QR for one exercise; a scan opens it and unlocks the whole booklet."""
    import qrcode
    from reportlab.lib.utils import ImageReader
    q = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(PLAY + "?t=" + slug + "&c=" + re.sub(r"[^A-Z0-9]", "", QR["code"].upper())); q.make(fit=True)
    buf = io.BytesIO(); q.make_image(fill_color=SLATE, back_color="white").save(buf, format="PNG"); buf.seek(0)
    return ImageReader(buf)


# ---------------------------------------------------------------- cover
def cover(path):
    c = canvas.Canvas(path, pagesize=letter)
    band = H * 0.58
    c.setFillColor(HexColor(SLATE)); c.rect(0, H - band, W, band, fill=1, stroke=0)
    # engraved staff on the left (clef follows the instrument), saxophone on the right
    from reportlab.lib.utils import ImageReader
    png, clef = cover_staff_png()
    im = ImageReader(png); iw, ih = im.getSize()
    sw = 290
    sh = sw * ih / iw
    c.drawImage(im, M, H - band + (48 if clef != "grand" else 30), sw, sh, mask="auto")
    draw_sax(c, 345, H - band + 36, 1.95, tenor=(EDITION == "tenor"))
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 11)
    c.drawString(M, H - 110, " ".join("ALEX ATTARD MUSIC"))
    c.setFillColor(white); c.setFont("Pop-B", 50)
    c.drawString(M, H - 198, "Saxophone")
    c.setFont("Pop-L", 38)
    c.drawString(M, H - 244, "Welcome Booklet")
    # edition under the title
    ed = {"alto": "E♭ Alto Saxophone", "tenor": "B♭ Tenor Saxophone"}[EDITION]
    c.setFillColor(HexColor(AMBER))
    draw_mixed(c, M, H - 284, ed, "Pop-M", 17)
    # welcome note (lower half)
    top, bot = H - band - 44, 92
    c.setFillColor(HexColor(TINT)); c.roundRect(M, bot, W - 2 * M, top - bot, 10, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.rect(M, bot, 5, top - bot, fill=1, stroke=0)
    big = ParagraphStyle("wb", parent=body, fontSize=11.8 if QR else 13.5, leading=18 if QR else 21, spaceAfter=10)   # smaller beside the QR
    note = [Paragraph(f"<font name='Pop-B' size='20' color='{SLATE}'>Welcome to lessons!</font>", ParagraphStyle("w", parent=body, leading=26, spaceAfter=12)),
            Paragraph("This booklet is your home base for everything we build together: a beautiful sound, fast and even fingers "
                      "in every key, and your first jazz vocabulary. Keep it on your music stand, practice a little every day, "
                      "and bring it to every lesson. Each week we'll choose the next page together.", big),
            Paragraph(f"<font name='Pop-M' size='14' color='{SLATE}'>Alex</font>", ParagraphStyle("sig", parent=body, spaceBefore=4))]
    qw = 150 if QR else 0                                   # room on the right for the play-along code
    hgt = sum(x.wrap(W - 2 * M - 60 - qw, 1000)[1] + x.getSpaceAfter() + x.getSpaceBefore() for x in note)
    pad = (top - bot - hgt) / 2
    f = Frame(M + 30, bot + pad - 4, W - 2 * M - 60 - qw, hgt + 8, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f.addFromList(note, c)
    if QR:
        qs = 104; qx = W - M - 24 - qs; mid = (top + bot) / 2; qy = mid - qs / 2 + 30
        c.setFillColor(white); c.roundRect(qx - 6, qy - 6, qs + 12, qs + 12, 8, fill=1, stroke=0)
        c.drawImage(qr_image(QR["first"]), qx, qy, qs, qs)
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 8.5); c.drawCentredString(qx + qs / 2, qy - 22, " ".join("PLAY ALONG"))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 15); c.drawCentredString(qx + qs / 2, qy - 41, QR["code"])
        c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 7.4)
        c.drawCentredString(qx + qs / 2, qy - 55, "Scan, or type this code at")
        c.drawCentredString(qx + qs / 2, qy - 65, "alexattardmusic.com/play")
    c.setFillColor(HexColor(AMBER)); c.rect(0, 0, W, 6, fill=1, stroke=0)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 11)
    c.drawString(M, 40, "Alex Attard Music")
    c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 10)
    c.drawRightString(W - M, 40, "alexattardmusic.com")
    c.showPage(); c.save()


# ---------------------------------------------------------------- start pages
TOC_INFO = {  # title -> (badge, description)
    "How to Use This Book": ("", "The TEA model and how to get faster, one tempo at a time"),
    "Your Practice Routine": ("", "How to split your practice time and climb the tempo ladder"),
    "Long Tones": ("1", "Sound, tuning and air: middle B down to low B♭, then up to high F"),
    "Chromatic Scale": ("2", "Every note on the saxophone, low B♭ to high F and back"),
    "Major Scales": ("3", "All 12 keys, in chromatic order and around the circle of fourths"),
    "Harmonic Minor Scales": ("3", "All 12 minor keys, same loop, both key orders"),
    "Scales in Thirds": ("4", "Major and harmonic minor scales in thirds, all 12 keys"),
    "Arpeggios": ("5", "Major and minor triads on every root"),
    "Four-Note Patterns": ("6", "1-2-3-4 groups through every major scale"),
    "ii–V–I Licks": ("7", "Four different licks over the same ii–V–I in C"),
    "Transposing a Lick": ("7", "One lick in five keys: C, G, D, F and B♭"),
    "Blues": ("7", "A 12-bar jazz blues: chord tones, scales and your own chorus"),
    "Fingering Chart": ("?", "Every note from low B♭ to high F, with palm, side and pinky keys"),
}


def contents_page(c, toc):
    y = header(c, "Start here", "What's Inside")
    row_h = (y - 56) / len(toc)
    for i, (title, page) in enumerate(toc):
        badge, desc = TOC_INFO.get(title.split(" in ")[0] if title.startswith("Blues") else title, ("", ""))
        top = y - i * row_h
        mid = top - row_h / 2
        # badge
        if badge:
            c.setFillColor(HexColor(AMBER if badge != "?" else SLATE))
            c.roundRect(M, mid - 13, 26, 26, 6, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("Pop-B", 12)
            c.drawCentredString(M + 13, mid - 4.3, badge if badge != "?" else "i")
        else:
            c.setStrokeColor(HexColor(AMBER)); c.setLineWidth(1.4)
            c.roundRect(M + 0.7, mid - 12.3, 24.6, 24.6, 6, fill=0, stroke=1)
            c.setFillColor(HexColor(AMBER)); c.circle(M + 13, mid, 3, fill=1, stroke=0)
        # title, description
        c.setFillColor(HexColor(SLATE))
        draw_mixed(c, M + 40, mid + 2, title, "Pop-B", 13)
        tw = sum(pdfmetrics.stringWidth(p, "DJ-B" if p in "♭♯" else "Pop-B", 13) for p in re.split("([♭♯])", title) if p)
        c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 9.3)
        c.drawString(M + 40, mid - 12.5, desc)
        # dotted leader + page number
        c.setStrokeColor(HexColor(RULE)); c.setLineWidth(1.1); c.setDash(1, 3)
        c.line(M + 40 + tw + 8, mid + 4, W - M - 30, mid + 4)
        c.setDash()
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 14)
        c.drawRightString(W - M, mid + 1, str(page))
        if i < len(toc) - 1:
            c.setStrokeColor(HexColor("#EEF0F2")); c.setLineWidth(0.6)
            c.line(M + 40, top - row_h, W - M, top - row_h)


def _para(c, text, style, x, y, w):
    p = Paragraph(text, style)
    _, h = p.wrap(w, 1000)
    p.drawOn(c, x, y - h)
    return y - h - style.spaceAfter


def tea_card(c, x, y, w, h, letter_, word, text):
    c.setFillColor(HexColor("#F3F5F7")); c.roundRect(x, y - h, w, h, 8, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 30); c.drawString(x + 12, y - 38, letter_)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(x + 42, y - 31, word)
    st = ParagraphStyle("tc", parent=body, fontSize=9.6, leading=13, spaceAfter=0)
    _para(c, text, st, x + 12, y - 48, w - 24)


def practice_pages(path, toc):
    c = canvas.Canvas(path, pagesize=letter)
    contents_page(c, toc)
    c.showPage()

    # ---- How to Use This Book
    y = header(c, "Start here", "How to Use This Book")
    y = _para(c, "This booklet is your technique toolkit: long tones for a beautiful sound, scales and arpeggios in all 12 keys "
                 "for fast, even fingers, and your first jazz vocabulary. Every saxophone reads the same written notes with the "
                 "same fingerings, so these pages work on soprano, alto, tenor and baritone. Only the blues pages are written "
                 "for your instrument.", body, M, y, W - 2 * M)
    y = tip_box(c, M, y - 2, W - 2 * M, "How each page works", [
        "<b>Start slow:</b> ♩ = 60, one note per beat, until every note passes the TEA test below.",
        "<b>Fill in the TEA tracker</b> at the top of each page with your best clean tempo.",
        "<b>Read it as written, count it your way.</b> The page never changes: one, two or four notes per beat happens in your head.",
        "<b>Play everything twice:</b> once slurred, once tongued.",
        "<b>Two key orders.</b> Every exercise appears in <b>chromatic order</b> (B♭, B, C, D♭ …) and around the "
        "<b>circle of fourths</b> (C, F, B♭, E♭ … the order jazz tunes move through).",
    ])
    y -= 16
    y = _para(c, "The TEA model", h2, M, y, W - 2 * M)
    y = _para(c, "Every scale, pattern and arpeggio in this booklet has one goal: play it <b>as fast as you can</b> while it still "
                 "passes all three parts of TEA. If any one slips, slow down.", body, M, y, W - 2 * M)
    cw, ch = (W - 2 * M - 20) / 3, 92
    for k, (l, word, txt) in enumerate([("T", "Tone", "A full, steady, in-tune sound on every note, from low B♭ to high F."),
                                        ("E", "Even", "Every note the same length and volume, locked to the metronome click."),
                                        ("A", "Accurate", "The right notes with the right fingers, every time, with no slips.")]):
        tea_card(c, M + k * (cw + 10), y, cw, ch, l, word, txt)
    y -= ch + 14
    y = _para(c, "Getting faster: 60 to 120, then double", h2, M, y, W - 2 * M)
    y = _para(c, "Keep the metronome between ♩ = 60 and ♩ = 120. Each day an exercise passes TEA, raise the tempo a little "
                 "(4 to 8 beats per minute). When you reach 120, go back to 60 and <b>double the notes per beat</b>. "
                 "120 at one note per beat is exactly the same speed as 60 at two, so you never jump: you just count it differently.",
              body, M, y, W - 2 * M)
    # stage graphic
    sw, sh, arrow = (W - 2 * M - 2 * 26) / 3, 74, 26
    stages = [("Stage 1", "1 note per beat", "♩"), ("Stage 2", "2 notes per beat", "♫"), ("Stage 3", "4 notes per beat", "♬♬")]
    for k, (st, npb, glyph) in enumerate(stages):
        x = M + k * (sw + arrow)
        c.setFillColor(HexColor(TINT)); c.roundRect(x, y - sh, sw, sh, 8, fill=1, stroke=0)
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 9); c.drawString(x + 12, y - 18, " ".join(st.upper()))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 12.5); c.drawString(x + 12, y - 36, npb)
        c.setFont("DJ", 10); c.setFillColor(HexColor(MUTED)); c.drawString(x + 12, y - 56, "♩ = 60  →  120")
        c.setFillColor(HexColor(SLATE)); c.setFont("DJ-B", 20); c.drawRightString(x + sw - 12, y - 60, glyph)
        if k < 2:
            ax = x + sw + 4
            c.setFillColor(HexColor(AMBER)); c.setFont("DJ-B", 16); c.drawCentredString(ax + 9, y - sh / 2 - 6, "→")
    c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 8.6)
    c.drawString(M, y - sh - 13, "At each arrow: back to ♩ = 60 with twice the notes per beat. The written notes never change.")
    c.showPage()

    # ---- Your Practice Routine
    y = header(c, "Every day", "Your Practice Routine")
    items = [Paragraph("I can show you what to play, but you improve in the six days between lessons. Twenty focused minutes every "
                       "day beats two hours once a week. Split your time into thirds: technique builds the skills, études put them "
                       "into music, and your big piece is where it all comes together.", body), Spacer(1, 4)]
    data = [["", "30 min", "45 min", "60 min"],
            ["Technique: long tones and scales from this booklet", "10", "15", "20"],
            ["Études and method-book pieces", "10", "15", "20"],
            ["Your big piece (from your lesson or school band)", "10", "15", "20"],
            ["Jazz bonus: improvise on your current tune or a blues", "+5", "+10", "+10"]]
    rows = [[Paragraph(f"<font name='Pop-M' color='{SLATE}'>{r[0]}</font>" if i else "", body)] +
            [Paragraph(f"<para alignment='center'><font name='{'Pop-B' if i == 0 else 'DJ'}'>{v}</font></para>", body) for v in r[1:]]
            for i, r in enumerate(data)]
    t = Table(rows, colWidths=[W - 2 * M - 3 * 70, 70, 70, 70])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), HexColor(TINT)), ("BACKGROUND", (0, 4), (-1, 4), HexColor("#F3F5F7")),
                           ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor(RULE)), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    items += [t, Paragraph("How to practice well", h2)]
    for tip in ["<b>Warm up with long tones</b> before anything fast. Your sound is the first thing people hear.",
                "<b>Practice the hard bar, not the whole piece.</b> Loop it slowly until you play it right five times in a row.",
                "<b>Slow is fast.</b> If you miss a note, lower the tempo, not your standard.",
                "<b>Use a tuner and a drone</b> (a held reference note) to train your ear, not just your eyes.",
                "<b>Record yourself once a week</b> and listen back the way a teacher would.",
                "<b>Stop while you're still focused.</b> Two short sessions beat one tired one."]:
        items.append(Paragraph(tip, bullet, bulletText="•"))
    items.append(Paragraph("The tempo ladder", h2))
    items.append(Paragraph("Start each exercise on the bottom rung. Each day it passes TEA, climb one rung. If it falls apart, "
                           "step back down; that's normal. At the top, start again at 60 with twice as many notes per beat.", body))
    flow(c, items, y)
    by, gap = 96, 7
    rungs = [str(t) for t in range(60, 121, 10)] + ["×2"]
    bw = (W - 2 * M - gap * (len(rungs) - 1)) / len(rungs)
    for i, label in enumerate(rungs):
        x = M + i * (bw + gap)
        last = label == "×2"
        c.setFillColor(HexColor(AMBER if last else (TINT if i % 2 == 0 else "#F3F5F7")))
        c.roundRect(x, by + i * 13, bw, 50, 6, fill=1, stroke=0)
        c.setFillColor(white if last else HexColor(SLATE)); c.setFont("Pop-B", 14)
        c.drawCentredString(x + bw / 2, by + i * 13 + 28, label)
        if last:
            c.setFont("Pop-M", 7.5); c.drawCentredString(x + bw / 2, by + i * 13 + 12, "back to 60")
        else:
            c.setStrokeColor(HexColor(AMBER)); c.setLineWidth(1)
            c.rect(x + bw / 2 - 6, by + i * 13 + 8, 12, 12, fill=0, stroke=1)
    c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 9)
    c.drawString(M, by - 16, "beats per minute: tick each rung when it passes TEA")
    c.showPage(); c.save()


# ---------------------------------------------------------------- LilyPond music pages
LY_HEAD = r'''\version "2.24.0"
#(set-global-staff-size 19)
\paper {
  #(set-paper-size "letter")
  #(define fonts (set-global-fonts #:roman "DejaVu Sans" #:sans "Poppins" #:factor (/ staff-height pt 20)))
  indent = 0 left-margin = 19\mm right-margin = 19\mm top-margin = 19\mm bottom-margin = 22\mm
  print-page-number = ##f tagline = ##f
  markup-system-spacing.basic-distance = #6
  system-system-spacing.basic-distance = #12
  score-markup-spacing.basic-distance = #11
  ragged-bottom = ##t ragged-last-bottom = ##t
}
\layout { \context { \Score \omit BarNumber } }
'''


def ly_header(kicker, title, intro):
    k = " ".join(kicker.upper())
    return rf'''\markup \column {{
  \with-color "{AMBER}" \sans \bold \fontsize #-1 "{k}"
  \vspace #0.3
  \with-color "{SLATE}" \sans \bold \fontsize #8 "{title}"
  \vspace #0.2
  \with-color "{AMBER}" \override #'(thickness . 3) \draw-line #'(22 . 0)
  \vspace #0.6
  \with-color "{SLATE}" \wordwrap-string #"{intro}"
  \vspace #0.4
}}
'''


def ly_label(name, extra="", right="♩ = ______   ______   ______"):
    return rf'''\markup \fill-line {{ \line {{ \with-color "{SLATE}" \sans \bold \fontsize #2 "{name}" \hspace #1 \with-color "{MUTED}" \italic "{extra}" }} \with-color "{MUTED}" \line {{ "{right}" }} }}
'''


def lily(n):
    return n.ly()


def long_tones():
    BAR = '\\bar "|."'

    # each note: 6 beats (whole tied to half), breathe, the same note for a half note = 2 bars
    def cell(n, i, per):
        brk = " \\break" if (i + 1) % per == 0 else ""
        return n + "1 ~ | " + n + "2 \\breathe " + n + "2 |" + brk

    down = ["b'", "bes'", "a'", "aes'", "g'", "ges'", "f'", "e'", "ees'", "d'", "des'", "c'", "b", "bes"]
    up = ["b'", "c''", "cis''", "d''", "dis''", "e''", "f''", "fis''", "g''", "gis''", "a''", "ais''", "b''",
          "c'''", "cis'''", "d'''", "dis'''", "e'''", "f'''"]

    def music(notes, per=4):
        return " ".join(cell(n, i, per) for i, n in enumerate(notes))

    def finish(n):
        # hold the last note as long as you can, three times
        return (" " + n + "1\\fermata^\\markup \\italic \\small \"as long as you can, ×3\" \\breathe "
                + n + "1\\fermata \\breathe " + n + "1\\fermata")

    def score(notes):
        return ("\\score { \\new Staff { \\key c \\major \\time 4/4 \\omit Staff.TimeSignature \\accidentalStyle forget "
                "\\tempo 4 = 60 " + music(notes) + finish(notes[-1]) + " " + BAR + " } \\layout { ragged-last = ##t } }\n")

    s = LY_HEAD.replace("#(set-global-staff-size 19)", "#(set-global-staff-size 19)").replace("ragged-bottom = ##t ragged-last-bottom = ##t", "ragged-bottom = ##f ragged-last-bottom = ##f")
    s += ly_header("Part 1 · Sound", "Long Tones",
                   "Long tones build your sound, your tuning and the air support behind everything else. Set the metronome to ♩ = 60. "
                   "Hold each note for 6 beats (six seconds), take a breath, play the same note again for 2 beats, then move to the next note "
                   "and repeat. Keep the sound full and steady, with no wobble in the pitch: check it with a tuner. "
                   "Finish each exercise on the fermatas: hold the last note as long as you can, three times.")
    s += ly_label("1. Down to the bottom", "middle B to low B♭, then hold low B♭ ×3", "")
    s += score(down)
    s += ly_label("2. Up to the top", "middle B to high F, then hold high F ×3", "")
    s += score(up)
    return s


BAR = '\\bar "|."'
CHROMATIC = ["Bb", "B", "C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A"]
CIRCLE = ["C", "F", "Bb", "Eb", "Ab", "Db", "F#", "B", "E", "A", "D", "G"]
CHROMATIC_MIN = ["Bb", "B", "C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A"]
CIRCLE_MIN = ["A", "D", "G", "C", "F", "Bb", "Eb", "G#", "C#", "F#", "B", "E"]
MAJOR = [0, 0, 0, 0, 0, 0, 0]
HARM_MIN = [0, 0, -1, 0, 0, -1, 0]
NAME = lambda k: k[0] + k[1:].replace("b", "♭").replace("#", "♯")
ORDERS = {
    "chromatic": ("Chromatic order", "Every key from low B♭ upward, a half step at a time (B♭, B, C, D♭ …). The advanced way: all 12 keys with no gaps."),
    "circle": ("Circle of fourths", "C, F, B♭, E♭ and on round the circle: the order jazz tunes move through, so it trains your ears as well as your fingers."),
}
TEMPO_LINE = ('\\markup \\fill-line { \\with-color "' + AMBER + '" \\sans \\bold "TEA GOAL  ♩ = 60–120" '
              '\\with-color "' + MUTED + '" \\line { "1 per beat ♩ = _____    2 per beat ♩ = _____    4 per beat ♩ = _____" } }\n')


def root_note(name):
    """Lowest written root (at or above low B♭) for a one-octave exercise."""
    n = Note(name[0], name[1:].count("#") - name[1:].count("b"), 3)
    while n.midi < 58:
        n.octave += 1
    return n


def deg(root, d, alters):
    """Scale degree d: 0 = the 7th below the root, 1-7, 8 = octave, 9 = 9th."""
    if d == 0:
        m = spell_degree(root, 7, alters[6])
        m.octave -= 1
        return m
    base = (d - 1) % 7 + 1
    m = spell_degree(root, base, alters[base - 1])
    m.octave += (d - 1) // 7
    return m


def loop_ok(root, alters):
    return deg(root, 0, alters).midi >= 58  # the 7th below must exist (no low A on saxophone)


def bars_fill(notes_8ths, final):
    """Eighth notes, then the final root lasting to the end of the bar."""
    rest = 8 - (len(notes_8ths) % 8)
    dur = {8: "1", 7: "2..", 6: "2.", 5: "2 r8", 4: "2", 3: "4.", 2: "4", 1: "8"}[rest]
    return " ".join(n.ly() + "8" for n in notes_8ths) + " " + final.ly() + dur


def pat_scale(root, alters):
    seq = list(range(1, 10)) + list(range(8, 0, -1))  # 1..9, 8..1
    if loop_ok(root, alters):
        seq.append(0)
    else:
        seq = seq[:-1]  # no 7th below (low B♭): the final held note is the root
    return bars_fill([deg(root, d, alters) for d in seq], root)


def pat_thirds(root, alters):
    up = [x for i in range(1, 8) for x in (i, i + 2)]          # 1 3, 2 4 ... 7 9
    down = [x for i in range(8, 1, -1) for x in (i, i - 2)]    # 8 6, 7 5 ... 2 0
    if not loop_ok(root, alters):
        down = down[:-1]                                         # no 7th below: ... 3 1 2, then the root
    return bars_fill([deg(root, d, alters) for d in up + down], root)


def pat_fours(root, alters):
    up = [x for s in range(1, 7) for x in range(s, s + 4)]           # 1234 ... 6789
    down = [x for s in range(8, 2, -1) for x in range(s, s - 4, -1)]  # 8765 ... 3210
    if not loop_ok(root, alters):
        down = down[:-1]
    return bars_fill([deg(root, d, alters) for d in up + down], root)


def pat_arp(root, alters):
    """Triad arpeggio in eighth-note triplets: 1 3 5 | 8 5 3 | 1 (half note)."""
    t = [deg(root, d, alters) for d in (1, 3, 5, 8, 5, 3)]
    a = " ".join(n.ly() + "8" for n in t[:3])
    b = " ".join(n.ly() + "8" for n in t[3:])
    return "\\tuplet 3/2 { " + a + " } \\tuplet 3/2 { " + b + " } " + root.ly() + "2"


def key_ly(root, mode="major"):
    return root.ly().rstrip("',") + " \\" + mode


def staff(name, music, root, mode):
    return ('\\score { \\new Staff \\with { instrumentName = \\markup \\with-color "' + SLATE + '" \\sans \\bold "' + name + '" } '
            '{ \\key ' + key_ly(root, mode) + ' \\time 4/4 \\omit Staff.TimeSignature ' + music + ' ' + BAR + ' } '
            '\\layout { indent = 15\\mm ragged-right = ##f } }\n')


def pattern_page(part, title, order, keys, mode, pattern, alters, explain, split=None):
    oname, odesc = ORDERS[order]
    s = LY_HEAD.replace("system-system-spacing.basic-distance = #12", "system-system-spacing.basic-distance = #10")
    s = s.replace("score-markup-spacing.basic-distance = #11", "score-markup-spacing.basic-distance = #4")
    s = s.replace("#(set-global-staff-size 19)", "#(set-global-staff-size 17)")
    s += ly_header(part + " · " + oname, title, explain + " " + odesc)
    s += TEMPO_LINE
    if split:
        s = s.replace("ragged-bottom = ##t ragged-last-bottom = ##t", "ragged-bottom = ##f ragged-last-bottom = ##f")
    for i, k in enumerate(keys):
        if split and i == split:
            s += "\\pageBreak\n" + cont_header(part + " · " + oname, title)
        r = root_note(k)
        s += staff(NAME(k), pattern(r, alters), r, mode)
    return s


def cont_header(kicker, title):
    k = " ".join(kicker.upper())
    return ('\\markup \\column { \\with-color "' + AMBER + '" \\sans \\bold \\fontsize #-1 "' + k + '" \\vspace #0.2 '
            '\\with-color "' + SLATE + '" \\sans \\bold \\fontsize #5 "' + title + ' (continued)" \\vspace #0.6 }\n')


def chromatic_scale():
    up = ["bes", "b", "c'", "cis'", "d'", "dis'", "e'", "f'", "fis'", "g'", "gis'", "a'", "ais'", "b'",
          "c''", "cis''", "d''", "dis''", "e''", "f''", "fis''", "g''", "gis''", "a''", "ais''", "b''",
          "c'''", "cis'''", "d'''", "dis'''", "e'''", "f'''"]
    down = ["e'''", "ees'''", "d'''", "des'''", "c'''", "b''", "bes''", "a''", "aes''", "g''", "ges''", "f''", "e''",
            "ees''", "d''", "des''", "c''", "b'", "bes'", "a'", "aes'", "g'", "ges'", "f'", "e'", "ees'", "d'", "des'",
            "c'", "b"]
    seq = up + down  # 62 eighths, then low B♭ as a quarter = 8 bars
    music = " ".join(n + "8" + (" \\break" if (i + 1) % 16 == 0 else "") for i, n in enumerate(seq)) + " bes4"
    s = LY_HEAD
    s += ly_header("Part 2 · Fingers", "Chromatic Scale",
                   "Every note on the saxophone, from low B♭ to high F and back down. Sharps on the way up, flats on the way down: "
                   "same fingerings, different names. Keep your fingers close to the keys and the eighth notes perfectly even, "
                   "and check the fingering chart at the back for any note you're unsure of.")
    s += TEMPO_LINE.replace("\\markup \\fill-line", "\\markup \\fontsize #-2 \\fill-line")
    s += ("\\score { \\new Staff { \\key c \\major \\time 4/4 \\omit Staff.TimeSignature \\accidentalStyle forget "
          + music + " " + BAR + " } \\layout { } }\n")
    return s


MINOR_NAME = {"Db": "C#", "Ab": "G#", "Gb": "F#"}


def pat_fours_split(root, alters):
    """Four-note groups; 49 notes = 7 bars, broken after bar 4."""
    up = [x for s_ in range(1, 7) for x in range(s_, s_ + 4)]
    down = [x for s_ in range(8, 2, -1) for x in range(s_, s_ - 4, -1)]
    if not loop_ok(root, alters):
        down = down[:-1]
    notes = [deg(root, d, alters) for d in up + down]
    parts = []
    for i, n in enumerate(notes):
        parts.append(n.ly() + "8")
        if i == 31:
            parts.append("\\break")
    rest = 8 - (len(notes) % 8)
    dur = {8: "1", 7: "2..", 6: "2.", 4: "2", 2: "4", 1: "8"}.get(rest, "1")
    return " ".join(parts) + " " + root.ly() + dur


def arp_page(order):
    keys = CHROMATIC if order == "chromatic" else CIRCLE
    oname, odesc = ORDERS[order]
    s = LY_HEAD.replace("#(set-global-staff-size 19)", "#(set-global-staff-size 17)")
    s = s.replace("system-system-spacing.basic-distance = #12", "system-system-spacing.basic-distance = #10")
    s = s.replace("score-markup-spacing.basic-distance = #11", "score-markup-spacing.basic-distance = #4")
    s += ly_header("Part 5 · " + oname, "Arpeggios",
                   "Each line is a major arpeggio, then a minor arpeggio on the same root: 1-3-5 up to the octave and back down, in eighth-note "
                   "triplets, landing on the root. Keep the triplets even and the big leaps smooth. " + odesc)
    s += TEMPO_LINE
    for k in keys:
        rM = root_note(k)
        mk = MINOR_NAME.get(k, k)
        rm = root_note(mk)
        bar1 = pat_arp(rM, MAJOR)
        bar2 = pat_arp(rm, HARM_MIN)
        # label each bar above its first note
        bar1 = bar1.replace("8", "8^\\markup \\with-color \"" + MUTED + "\" \\small \\italic \"" + NAME(k) + " major\"", 1)
        bar2 = bar2.replace("8", "8^\\markup \\with-color \"" + MUTED + "\" \\small \\italic \"" + NAME(mk) + " minor\"", 1)
        music = bar1 + " | " + bar2
        s += ('\\score { \\new Staff \\with { instrumentName = \\markup \\with-color "' + SLATE + '" \\sans \\bold "' + NAME(k) + '" } '
              '{ \\key c \\major \\time 4/4 \\omit Staff.TimeSignature ' + music + ' ' + BAR + ' } '
              '\\layout { indent = 15\\mm ragged-right = ##f } }\n')
    return s


# ---------------------------------------------------------------- ii–V–I licks (original lines, written pitch)
LICK_CHORDS = "d1:m7 g:7 c:maj7 c:maj7"
LICKS = [
    ("1", "Step-down line",
     "Scale steps only. The 7th of each chord falls to the 3rd of the next: C to B, then F to E.",
     "r8 d'' f'' e'' d'' c'' a' c'' | b'8 a' g' a' b' d'' f''4 | e''4. d''8 c''4 g' | a'8 b' c''2."),
    ("2", "Arpeggio to the 9th",
     "Dm7 and G7 arpeggios from the root up to the 9th, then down into the 3rd of Cmaj7.",
     "d'8 f' a' c'' e''4 c''8 a' | b'8 d'' f'' a'' g''4 f''8 d'' | e''8 c'' b' g' e'4 g' | c''2. r4"),
    ("3", "Scale down, arpeggio up",
     "Run down D Dorian, climb G7 to its 9th, then outline Cmaj7 (E G B).",
     "a''8 g'' f'' e'' d'' c'' b' a' | g'8 b' d'' f'' a''4 g''8 f'' | e''8 g'' b'' g'' e''4 d''8 c'' | e''2. r4"),
    ("4", "Enclosure and ♭9",
     "C and A♯ surround B, the 3rd of G7; the A♭ (♭9) gives a darker pull into C.",
     "c''8 d'' e'' f'' a''4 f''8 d'' | c''8 ais' b' d'' f'' aes'' g'' f'' | e''8 g'' b'' a'' g''4 e'' | d''8 e'' c''2 r4"),
]
# (transpose target with octave, label, key-signature note)
LICK_KEYS = [
    ("c", "C major", "no sharps or flats"),
    ("g,", "G major", "1 sharp: F♯"),
    ("d", "D major", "2 sharps: F♯, C♯"),
    ("f", "F major", "1 flat: B♭"),
    ("bes,", "B♭ major", "2 flats: B♭, E♭"),
]
LICK_LAYOUT = ('\\layout { ragged-right = ##f \\context { \\ChordNames majorSevenSymbol = \\markup { "maj7" } '
               'chordNameExceptions = #(append (sequential-music-to-chord-exceptions chExceptionMusic #t) ignatzekExceptions) } }')


def lick_score(music, to="c"):
    inner = ('<< \\new ChordNames \\with { \\override ChordName.font-size = #0.5 } \\chordmode { ' + LICK_CHORDS + ' } '
             '\\new Staff { \\key c \\major \\time 4/4 \\omit Staff.TimeSignature ' + music + ' ' + BAR + ' } >>')
    if to != "c":
        inner = "\\transpose c " + to + " " + inner
    return "\\score { " + inner + " " + LICK_LAYOUT + " }\n"


def licks_page():
    s = LY_HEAD.replace("ragged-bottom = ##t ragged-last-bottom = ##t", "ragged-bottom = ##f ragged-last-bottom = ##f")
    s = s.replace("score-markup-spacing.basic-distance = #11", "score-markup-spacing.basic-distance = #8")
    s += 'chExceptionMusic = { <c es ges bes>1-\\markup { "m" \\super "7♭5" } }\n'
    # page 1: four licks, one key
    s += ly_header("Part 7 · Jazz · Four licks, one key", "ii–V–I Licks",
                   "The ii–V–I is the most common chord progression in jazz. Here are four different licks over the same "
                   "ii–V–I in C (Dm7, G7, Cmaj7), so you can hear how many ways there are through one set of changes. "
                   "Listen for the 7th of each chord resolving to the 3rd of the next. Swing the eighth notes and learn each lick by memory.")
    for num, name, desc, music in LICKS:
        s += ly_label("Lick " + num + " · " + name, "")
        s += '\\markup \\with-color "' + MUTED + '" \\italic \\wordwrap-string #"' + desc + '"\n'
        s += lick_score(music)
    # page 2: one lick, five keys
    s += "\\pageBreak\n"
    s += ly_header("Part 7 · Jazz · One lick, five keys", "Transposing a Lick",
                   "Lick 1 moved into five keys: C major, two sharp keys and two flat keys. The shape and the sound stay the same; "
                   "only the key signature changes. Learn it in C, then try each new key by ear before you read it. "
                   "When these feel easy, take Licks 2, 3 and 4 through the same five keys.")
    music1 = LICKS[0][3]
    for to, name, sig in LICK_KEYS:
        s += ly_label(name, sig)
        s += lick_score(music1, to)
    return s


# ---------------------------------------------------------------- blues (from the lead-sheet generator)
def blues_pages():
    import json, re
    import gen_study
    spec = {"title": "Blues", "concert_key": "F", "instrument": EDITION, "tempo_text": "Medium Swing", "blues": True,
            "bars": [["F7"], ["Bb7"], ["F7"], ["Cm7", "F7"], ["Bb7"], ["Bb7"], ["F7"], ["Am7", "D7"],
                     ["Gm7"], ["C7"], ["F7", "D7"], ["Gm7", "C7"]]}
    ly = gen_study.build(spec)
    ly = re.sub(r"\\header \{.*?\n\}\n", "\\\\header { tagline = ##f }\n", ly, count=1, flags=re.S)
    ly = ly.replace("#(set-global-staff-size 19)", "#(set-global-staff-size 18)")
    ly = ly.replace("\\paper {\n", "\\paper {\n  #(define fonts (set-global-fonts #:roman \"DejaVu Sans\" #:sans \"Poppins\" #:factor (/ staff-height pt 20)))\n"
                    "  print-page-number = ##f\n", 1)
    ly = ly.replace("  ragged-last-bottom = ##t\n", "  ragged-last-bottom = ##f\n", 1).replace("  ragged-bottom = ##t\n", "  ragged-bottom = ##f\n", 1)
    ly = ly.replace("top-margin = 12\\mm bottom-margin = 12\\mm left-margin = 16\\mm right-margin = 16\\mm",
                    "top-margin = 19\\mm bottom-margin = 22\\mm left-margin = 19\\mm right-margin = 19\\mm")
    key = {"alto": "D", "tenor": "G"}.get(EDITION, "F")
    head = ly_header("Part 7 · Jazz", "Blues in " + key,
                     "A 12-bar jazz blues, written in " + key + " for your saxophone (concert F, the key a band plays it in). "
                     "First learn the chord tones, then the scale for each chord, then write your own line over the changes.")
    first = ly.index("\\markup \\column {")
    ly = ly[:first] + head + ly[first:]
    ly = re.sub(r"\\score \{\n  << \\new Staff .*?\\midi .*?\}\n\}\n", "", ly, flags=re.S)
    return ly


# ---------------------------------------------------------------- fingering chart
LH3 = {"L1", "L2", "L3"}
ALL6 = LH3 | {"R4", "R5", "R6"}
O = {"oct"}
# (lilypond notes, name, keys pressed, note line)
FINGERINGS = [
    ("bes", "Low B♭", ALL6 | {"Bb", "C"}, "Pinkies: low B♭ + low C"),
    ("b", "Low B", ALL6 | {"B", "C"}, "Pinkies: low B + low C"),
    ("c'", "Low C", ALL6 | {"C"}, "RH pinky: low C"),
    ("cis' des'", "Low C♯ / D♭", ALL6 | {"Cs", "C"}, "Pinkies: low C♯ + low C"),
    ("d'", "Low D", ALL6, ""),
    ("dis' ees'", "Low D♯ / E♭", ALL6 | {"Eb"}, "RH pinky: E♭ key"),
    ("e'", "E", LH3 | {"R4", "R5"}, ""),
    ("f'", "F", LH3 | {"R4"}, ""),
    ("fis' ges'", "F♯ / G♭", LH3 | {"R5"}, ""),
    ("g'", "G", LH3, ""),
    ("gis' aes'", "G♯ / A♭", LH3 | {"Gs"}, "LH pinky: G♯ key"),
    ("a'", "A", {"L1", "L2"}, ""),
    ("ais' bes'", "A♯ / B♭", {"L1", "bis"}, ""),
    ("b'", "B", {"L1"}, ""),
    ("c''", "C", {"L2"}, ""),
    ("cis'' des''", "C♯ / D♭", set(), "All keys open"),
    ("d''", "Upper D", O | ALL6, "Octave key on"),
    ("dis'' ees''", "Upper D♯ / E♭", O | ALL6 | {"Eb"}, "RH pinky: E♭ key"),
    ("e''", "Upper E", O | LH3 | {"R4", "R5"}, ""),
    ("f''", "Upper F", O | LH3 | {"R4"}, ""),
    ("fis'' ges''", "Upper F♯ / G♭", O | LH3 | {"R5"}, ""),
    ("g''", "Upper G", O | LH3, ""),
    ("gis'' aes''", "Upper G♯ / A♭", O | LH3 | {"Gs"}, "LH pinky: G♯ key"),
    ("a''", "Upper A", O | {"L1", "L2"}, ""),
    ("ais'' bes''", "Upper A♯ / B♭", O | {"L1", "bis"}, ""),
    ("b''", "Upper B", O | {"L1"}, ""),
    ("c'''", "Upper C", O | {"L2"}, ""),
    ("cis''' des'''", "Upper C♯ / D♭", O, "Octave key only"),
    ("d'''", "High D", O | {"pD"}, "Palm D"),
    ("dis''' ees'''", "High D♯ / E♭", O | {"pD", "pEb"}, "Palm D + E♭"),
    ("e'''", "High E", O | {"pD", "pEb", "sE"}, "Palm D + E♭ + side E"),
    ("f'''", "High F", O | {"pD", "pEb", "pF", "sE"}, "Palm D, E♭, F + side E"),
]

# notes with a second (chromatic) fingering: card shows both diagrams, labelled
ALTERNATES = {
    "F♯ / G♭": [("Standard", LH3 | {"R5"}), ("Alternate", LH3 | {"R6"})],
    "A♯ / B♭": [("Bis key", {"L1", "bis"}), ("Side B♭", {"L1", "sBb"})],
    "C": [("Standard", {"L2"}), ("Side C", {"L1", "sC"})],
    "Upper F♯ / G♭": [("Standard", O | LH3 | {"R5"}), ("Alternate", O | LH3 | {"R6"})],
    "Upper A♯ / B♭": [("Bis key", O | {"L1", "bis"}), ("Side B♭", O | {"L1", "sBb"})],
    "Upper C": [("Standard", O | {"L2"}), ("Side C", O | {"L1", "sC"})],
}

# front view (as you look at the saxophone): palm keys and the LH pinky table on the right,
# side keys and the RH pinky keys on the left
# key geometry in units: (id, shape, x, y, a, b, main?)  c=circle(r=a)  e=ellipse(rx=a, ry=b)  r=rounded rect(w=a, h=b)
KEYS = [
    ("oct", "c", 0, -0.55, 0.4, 0, False),
    # palm keys as a triangle, like the horn: E♭ on top, the larger D below it, F on the inside next to the B key
    ("pEb", "e", 2.1, 0.7, 0.3, 0.4, False),
    ("pD", "e", 2.1, 1.85, 0.38, 0.48, False),
    ("pF", "e", 1.3, 1.25, 0.3, 0.4, False),
    ("L1", "c", 0, 1.2, 0.66, 0, True),
    ("bis", "c", 0, 2.35, 0.3, 0, False),
    ("L2", "c", 0, 3.5, 0.66, 0, True),
    ("L3", "c", 0, 5.4, 0.66, 0, True),
    ("Gs", "r", 1.85, 5.4, 1.2, 0.5, False),
    ("Cs", "r", 2.18, 6.1, 0.55, 0.5, False),
    ("B", "r", 1.52, 6.1, 0.55, 0.5, False),
    ("Bb", "r", 1.85, 6.8, 1.2, 0.5, False),
    ("sE", "e", -1.75, 7.0, 0.3, 0.4, False),
    ("sC", "e", -1.75, 7.9, 0.3, 0.4, False),
    ("sBb", "e", -1.75, 8.8, 0.3, 0.4, False),
    ("R4", "c", 0, 7.8, 0.66, 0, True),
    ("R5", "c", 0, 9.7, 0.66, 0, True),
    ("R6", "c", 0, 11.6, 0.66, 0, True),
    ("Eb", "r", -1.6, 12.4, 1.0, 0.5, False),
    ("C", "r", -1.6, 13.1, 1.0, 0.5, False),
]
KY_MIN, KY_MAX, KX_MIN, KX_MAX = -0.95, 13.35, -2.1, 2.5


def draw_keys(c, cx, ytop, u, pressed, legend=False):
    """Draw the saxophone key diagram. cx = x of the main column, ytop = top edge."""
    def P(x, y):
        return cx + x * u, ytop - (y - KY_MIN) * u
    c.setStrokeColor(HexColor(MUTED)); c.setLineWidth(0.6)
    x1, y1 = P(-1.0, 6.6); x2, _ = P(1.0, 6.6)
    c.line(x1, y1, x2, y1)
    pos = {}
    for kid, shape, x, y, a, b, main in KEYS:
        X, Y = P(x, y)
        pos[kid] = (X, Y, a, b, shape)
        on = kid in pressed
        if legend:
            fill = HexColor(SLATE) if main else HexColor(AMBER)
        else:
            fill = (HexColor(SLATE) if main else HexColor(AMBER)) if on else white
        c.setFillColor(fill)
        c.setStrokeColor(HexColor(SLATE) if main else HexColor("#8A6A3A"))
        c.setLineWidth(0.9 if main else 0.7)
        if shape == "c":
            c.circle(X, Y, a * u, fill=1, stroke=1)
        elif shape == "e":
            c.ellipse(X - a * u, Y - b * u, X + a * u, Y + b * u, fill=1, stroke=1)
        else:
            c.roundRect(X - a * u / 2, Y - b * u / 2, a * u, b * u, min(a, b) * u * 0.45, fill=1, stroke=1)
    return pos


KEY_LABELS_RIGHT = [("oct", -0.55, "Octave key (left thumb)"), ("pEb", 0.55, "Palm E♭"), ("pD", 2.15, "Palm D"),
                   ("pF", 1.35, "Palm F"), ("Gs", 4.95, "G♯ key"), ("Cs", 5.85, "Low C♯"), ("B", 6.75, "Low B"),
                   ("Bb", 7.65, "Low B♭"), ("R4", 8.7, "4 · F (RH index)"), ("R5", 9.7, "5 · E (RH middle)"),
                   ("R6", 11.6, "6 · D (RH ring)")]
KEY_LABELS_LEFT = [("L1", 1.2, "1 · B (LH index)"), ("bis", 2.35, "Bis key (B♭)"), ("L2", 3.5, "2 · A (LH middle)"),
                    ("L3", 5.4, "3 · G (LH ring)"), ("sE", 7.0, "Side E (high E)"), ("sC", 7.9, "Side C"),
                    ("sBb", 8.8, "Side B♭"), ("Eb", 12.3, "Low E♭ (RH pinky)"), ("C", 13.25, "Low C (RH pinky)")]


def key_map(c, x0, ytop, w, h):
    """Panel with a labelled key diagram on the left and how-to-read notes on the right."""
    c.setFillColor(HexColor("#F3F5F7")); c.roundRect(x0, ytop - h, w, h, 8, fill=1, stroke=0)
    u = (h - 16) / (KY_MAX - KY_MIN)
    cx = x0 + 104 + (-KX_MIN) * u
    pos = draw_keys(c, cx, ytop - 8, u, set(), legend=True)
    for n, kid in [("1", "L1"), ("2", "L2"), ("3", "L3"), ("4", "R4"), ("5", "R5"), ("6", "R6")]:
        X, Y, *_ = pos[kid]
        c.setFillColor(white); c.setFont("Pop-B", 6.5); c.drawCentredString(X, Y - 2.3, n)
    def ly(y):
        return ytop - 8 - (y - KY_MIN) * u
    lx = cx + KX_MIN * u - 8
    rx = cx + KX_MAX * u + 8
    c.setLineWidth(0.4); c.setStrokeColor(HexColor(MUTED))
    for kid, y, txt in KEY_LABELS_LEFT:
        X, Y, a, b, shape = pos[kid]
        edge = X - (a * u if shape != "r" else a * u / 2)
        c.line(lx + 2, ly(y) + 2.2, edge - 1, Y)
        c.setFillColor(HexColor(SLATE)); c.setFont("DJ", 6.6)
        c.drawRightString(lx, ly(y), txt)
    for kid, y, txt in KEY_LABELS_RIGHT:
        X, Y, a, b, shape = pos[kid]
        edge = X + (a * u if shape != "r" else a * u / 2)
        c.line(edge + 1, Y, rx - 2, ly(y) + 2.2)
        c.setFillColor(HexColor(SLATE)); c.setFont("DJ", 6.6)
        c.drawString(rx, ly(y), txt)
    # notes on the right
    tx = x0 + 292
    items = [Paragraph(f"<font name='Pop-B' size='11.5' color='{SLATE}'>How to read the chart</font>",
                       ParagraphStyle("kt", parent=body, spaceAfter=5))]
    small = ParagraphStyle("ks", parent=bullet, fontSize=8.5, leading=11, spaceAfter=3)
    for t in [f"<font color='{SLATE}'><b>Dark keys</b></font> are your six main fingers: left hand 1-2-3 on top, right hand 4-5-6 below. "
              f"<font color='{AMBER}'><b>Amber keys</b></font> are the octave, palm, side, bis and pinky keys.",
              "<b>Filled = press it.</b> Hollow = leave it open.",
              "<b>Two diagrams</b> = two fingerings for the same note (B♭, F♯ and C).",
              "<b>From upper D</b> the low fingerings repeat with the octave key added."]:
        items.append(Paragraph(t, small, bulletText="•"))
    f = Frame(tx, ytop - h + 6, x0 + w - tx - 12, h - 18, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f.addFromList(items, c)


def note_images():
    """Render each fingering-chart note on a small treble staff (PNG, cropped)."""
    d = OUT + "/notes"
    os.makedirs(d, exist_ok=True)
    paths = []
    for i, (ly, *_rest) in enumerate(FINGERINGS):
        notes = " \\noBreak ".join(n + "1" for n in ly.split())  # enharmonic pairs stay on one line
        src = ('\\version "2.24.0"\n\\paper { indent = 0 line-width = 27\\mm ragged-right = ##f tagline = ##f }\n'
               '\\layout { \\context { \\Staff \\remove Time_signature_engraver } '
               '\\context { \\Score \\override SpacingSpanner.shortest-duration-space = #1.0 } }\n'
               '{ \\clef treble \\accidentalStyle forget ' + notes + ' }\n')
        p = f"{d}/n{i}"
        open(p + ".ly", "w").write(src)
        subprocess.run(["lilypond", "-s", "--png", "-dresolution=300", "-dcrop", "-o", p, p + ".ly"], check=True)
        from PIL import Image
        im = Image.open(p + ".cropped.png").convert("LA")
        rgba = Image.new("RGBA", im.size)
        rgba.putdata([(0, 0, 0, 255 - l) for l, a in im.getdata()])  # ink only, transparent background
        rgba.save(p + ".t.png")
        paths.append(p + ".t.png")
    return paths


def _centred_mixed(c, xc, y, text, font, size):
    alt = "DJ-B" if font in ("Pop-B", "Pop-M") else "DJ"
    w = sum(pdfmetrics.stringWidth(p, alt if p in "♭♯♩" else font, size) for p in re.split("([♭♯♩])", text) if p)
    draw_mixed(c, xc - w / 2, y, text, font, size)


def fingering_pages(path):
    from reportlab.lib.utils import ImageReader
    imgs = note_images()
    c = canvas.Canvas(path, pagesize=letter)
    cols, rows, gap = 3, 4, 10
    gw = (W - 2 * M - (cols - 1) * gap) / cols
    layout = [(1, 9), (0, 12), (0, 12)]  # (key-map rows, cards) per page: 33 slots = 32 notes + 1 tip card
    idx = 0
    for page, (maprows, ncards) in enumerate(layout):
        y = header(c, "Reference", "Fingering Chart" + ("" if page == 0 else " (continued)"))
        gh = (y - 60 - (rows - 1) * gap) / rows
        if maprows:
            key_map(c, M, y, W - 2 * M, gh)
        for k in range(ncards):
            col, row = k % cols, k // cols + maprows
            x0 = M + col * (gw + gap)
            y1 = y - row * (gh + gap)
            c.setFillColor(HexColor(TINT if (row + col) % 2 == 0 else "#F3F5F7"))
            c.roundRect(x0, y1 - gh, gw, gh, 8, fill=1, stroke=0)
            if idx >= len(FINGERINGS):
                # closing tip card
                c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 11); c.drawString(x0 + 10, y1 - 18, "Chromatic fingerings")
                st = ParagraphStyle("tip", parent=body, fontSize=8.6, leading=11.8, spaceAfter=4)
                tip = [Paragraph("B♭, F♯ and C each have two fingerings. Pick the one that moves the fewest fingers "
                                 "from the note before and after.", st),
                       Paragraph("<b>Bis B♭</b> suits flat keys and B♭–A–G lines. <b>Side B♭</b> and <b>side C</b> "
                                 "keep chromatic runs and B–C–B moves smooth.", st)]
                f = Frame(x0 + 10, y1 - gh + 8, gw - 20, gh - 34, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
                f.addFromList(tip, c)
                idx += 1
                continue
            ly_, name, pressed, note = FINGERINGS[idx]
            alts = ALTERNATES.get(name, [("", pressed)])
            c.setFillColor(HexColor(SLATE))
            draw_mixed(c, x0 + 10, y1 - 17, name, "Pop-B", 10.5)
            # diagrams on the right: room for two; a single one is centred in that space
            top, bot = y1 - 25, y1 - gh + 17
            u = (top - bot) / (KY_MAX - KY_MIN)
            dw = (KX_MAX - KX_MIN) * u
            right = x0 + gw - 10
            area_l = right - 2 * dw - 12
            if len(alts) == 2:
                lefts = [area_l, right - dw]
            else:
                lefts = [area_l + (right - area_l - dw) / 2]
            for (label, keys), lx in zip(alts, lefts):
                draw_keys(c, lx - KX_MIN * u, top, u, keys)
                if label:
                    c.setFillColor(HexColor("#A86F14"))
                    _centred_mixed(c, lx + dw / 2, y1 - gh + 7, label, "Pop-M", 7.4)
            # note on a fixed-width staff (every card the same size), centred vertically on the left
            im = ImageReader(imgs[idx]); iw, ih = im.getSize()
            tw = area_l - (x0 + 8) - 6
            th = tw * ih / iw
            c.drawImage(im, x0 + 7, (top + bot) / 2 - th / 2, tw, th, mask="auto")
            if note and len(alts) == 1:
                c.setFillColor(HexColor("#A86F14"))
                draw_mixed(c, x0 + 10, y1 - gh + 7, note, "Pop-M", 7.4)
            idx += 1
        c.showPage()
    c.save()


def run_ly(name, src):
    p = f"{OUT}/{name}.ly"
    open(p, "w").write(src)
    subprocess.run(["lilypond", "-s", "-o", f"{OUT}/{name}", p], check=True)
    return f"{OUT}/{name}.pdf"


# ---------------------------------------------------------------- assemble
def footer_overlay(n_pages):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    for i in range(n_pages):
        if i > 0:
            c.setStrokeColor(HexColor(RULE)); c.setLineWidth(0.6)
            c.line(M, 40, W - M, 40)
            c.setFont("Pop-M", 8.5); c.setFillColor(HexColor(SLATE))
            c.drawString(M, 28, "Alex Attard Music")
            c.setFont("Pop-B", 9); c.setFillColor(HexColor(AMBER))
            c.drawRightString(W - M, 28, str(i + 1))
        slug = QR and QR["pages"].get(str(i + 1))
        if slug:                                            # top-right corner of the exercise's first page: 1 inch, so it scans from a print
            qs = 72; qx = W - M - qs + 4; qy = H - 26 - qs
            c.drawImage(qr_image(slug), qx, qy, qs, qs)
            c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 6.2); c.drawCentredString(qx + qs / 2, qy - 6, " ".join("PLAY ALONG") + "  ·  " + QR["code"])
        c.showPage()
    c.save(); buf.seek(0)
    return PdfReader(buf)


def chromatic_tips():
    tips = [
        "Learn it in three chunks first: low B♭ to low D (the pinky keys), middle D to high C♯ (the octave key), then high D to high F (the palm keys).",
        "Slur it first so you can hear every finger change, then tongue it.",
        "Keep your fingers close to the keys and roll your thumb onto the octave key; don't lift it off the thumb rest.",
        "Low pinky keys: slide, don't jump. Practice low B♭ to low C♯ and back on its own until it's smooth.",
        "Use the TEA system: ♩ = 60 to 120 at one note per beat, then two, then four.",
    ]
    s = '\\markup \\column { \\vspace #1.5 \\with-color "' + AMBER + '" \\sans \\bold \\fontsize #-1 "H O W   T O   P R A C T I C E   I T" \\vspace #0.5\n'
    for t in tips:
        s += ('  \\line { \\with-color "' + AMBER + '" "•" \\hspace #1 \\with-color "' + SLATE
              + '" \\override #\'(line-width . 82) \\wordwrap-string #"' + t + '" } \\vspace #0.3\n')
    return s + "}\n"


PARTS_TXT = {
    "scale": ("One octave and a bit: up to the 9th, back down to the root, then the leading note below it, which loops you straight "
              "back to the start. Play it slurred, then tongued, and repeat it without stopping."),
    "minor": ("The harmonic minor: a natural minor with a raised 7th, which gives it that exotic leap between the 6th and 7th. Same loop as "
              "the major scales: up to the 9th, back to the root, then the raised 7th below."),
    "thirds_maj": ("The major scale in thirds: 1-3, 2-4, 3-5 up to the 9th, then 8-6, 7-5 back down to the 7th below and home. Thirds train "
                   "your fingers to skip and your ears to hear chords inside the scale."),
    "thirds_min": ("The harmonic minor scale in thirds, same shape as the major page. Watch the raised 7th: it appears in the 5-7 and 7-9 pairs."),
    "fours": ("Four-note groups through each major scale: 1-2-3-4, 2-3-4-5 up to 6-7-8-9, then 8-7-6-5 back down to 3-2-1 and the 7th below. "
              "Accent the first note of each group so you can feel the beat."),
}


def main():
    cover(f"{OUT}/cover.pdf")
    fingering_pages(f"{OUT}/fingering.pdf")
    chrom = chromatic_scale().replace("#(set-global-staff-size 19)", "#(set-global-staff-size 22)") + chromatic_tips()
    chrom = chrom.replace("system-system-spacing.basic-distance = #12", "system-system-spacing.basic-distance = #17")
    P = "Part 3 · Scales"
    sections = []  # (toc title or None, pdf)
    sections.append(("Long Tones", run_ly("long_tones", long_tones())))
    sections.append(("Chromatic Scale", run_ly("chromatic", chrom)))
    for i, order in enumerate(("chromatic", "circle")):
        sections.append(("Major Scales" if i == 0 else None, run_ly(f"major_{order}", pattern_page(P, "Major Scales", order, CHROMATIC if order == "chromatic" else CIRCLE,
                                                           "major", pat_scale, MAJOR, PARTS_TXT["scale"]))))
    for i, order in enumerate(("chromatic", "circle")):
        sections.append(("Harmonic Minor Scales" if i == 0 else None, run_ly(f"minor_{order}", pattern_page(P, "Harmonic Minor Scales", order,
                                                           CHROMATIC_MIN if order == "chromatic" else CIRCLE_MIN,
                                                           "minor", pat_scale, HARM_MIN, PARTS_TXT["minor"]))))
    for i, order in enumerate(("chromatic", "circle")):
        sections.append(("Scales in Thirds" if i == 0 else None, run_ly(f"thirds_maj_{order}", pattern_page("Part 4 · Thirds", "Major Scales in Thirds", order,
                                                                CHROMATIC if order == "chromatic" else CIRCLE,
                                                                "major", pat_thirds, MAJOR, PARTS_TXT["thirds_maj"]))))
    for order in ("chromatic", "circle"):
        sections.append((None, run_ly(f"thirds_min_{order}", pattern_page("Part 4 · Thirds", "Harmonic Minor in Thirds", order,
                                                                CHROMATIC_MIN if order == "chromatic" else CIRCLE_MIN,
                                                                "minor", pat_thirds, HARM_MIN, PARTS_TXT["thirds_min"]))))
    for i, order in enumerate(("chromatic", "circle")):
        sections.append(("Arpeggios" if i == 0 else None, run_ly(f"arps_{order}", arp_page(order))))
    for i, order in enumerate(("chromatic", "circle")):
        sections.append(("Four-Note Patterns" if i == 0 else None, run_ly(f"fours_{order}", pattern_page("Part 6 · Patterns", "Four-Note Patterns", order,
                                                           CHROMATIC if order == "chromatic" else CIRCLE,
                                                           "major", pat_fours_split, MAJOR, PARTS_TXT["fours"], split=6))))
    sections.append(("ii–V–I Licks", run_ly("licks", licks_page())))
    key = {"alto": "D", "tenor": "G"}.get(EDITION, "F")
    sections.append((f"Blues in {key}", run_ly(f"blues_{EDITION}", blues_pages())))
    sections.append(("Fingering Chart", f"{OUT}/fingering.pdf"))
    # table of contents with real page numbers (cover = 1, practice pages = 2-3)
    toc, pg = [("How to Use This Book", 3), ("Your Practice Routine", 4)], 5
    for title, pdf in sections:
        if title:
            toc.append((title, pg))
            if title == "ii–V–I Licks":
                toc.append(("Transposing a Lick", pg + 1))
        pg += len(PdfReader(pdf).pages)
    practice_pages(f"{OUT}/practice.pdf", toc)
    parts = [f"{OUT}/cover.pdf", f"{OUT}/practice.pdf"] + [pdf for _, pdf in sections]
    w = PdfWriter()
    for p in parts:
        for page in PdfReader(p).pages:
            w.add_page(page)
    ov = footer_overlay(len(w.pages))
    for i, page in enumerate(w.pages):
        page.merge_page(ov.pages[i])
    out = f"{OUT}/Sax_Welcome_Booklet_{EDITION.capitalize()}.pdf"
    with open(out, "wb") as fh:
        w.write(fh)
    print(out, len(w.pages), "pages")
    for p in parts:
        print(os.path.basename(p), len(PdfReader(p).pages))


if __name__ == "__main__":
    main()
