#!/usr/bin/env python3
"""Print edition of a Graded Repertoire book: cover, how-to page, contents, one piece per page (two for long pieces), sources.

  python3 tools/make_repertoire_pdf.py repertoire/books/level-1-baroque-classical.json --code GR1-0000 [--out book.pdf]

The music is engraved by LilyPond from the same per-bar ABC the player uses (repertoire/src/*.json), so print and player
always agree. Text pages, headers, QR codes and footers are drawn with ReportLab; pypdf merges the lot. The code is passed
on the command line and never stored in the repository."""
import io, json, math, os, re, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from make_repertoire import TOKEN, keysig, KEYS
import qrcode
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# ---------------------------------------------------------------- series design (shared by every Alex Attard Music book)
SLATE, AMBER, TINT, MUTED, RULE = "#2F3E4E", "#D4922A", "#FBF1E1", "#6B7785", "#D9DEE3"
STRANDS = {"Baroque & Classical": "#D4922A", "Romantic & Early Modern": "#B5533C", "Études": "#3E8E7E", "Scales & Technique": "#4A78B0"}
GF, DJ = "/usr/share/fonts/truetype/google-fonts/", "/usr/share/fonts/truetype/dejavu/"
for n, f in [("Pop-B", GF + "Poppins-Bold.ttf"), ("Pop-M", GF + "Poppins-Medium.ttf"), ("Pop", GF + "Poppins-Regular.ttf"), ("Pop-L", GF + "Poppins-Light.ttf"),
             ("DJ", DJ + "DejaVuSans.ttf"), ("DJ-B", DJ + "DejaVuSans-Bold.ttf"), ("DJ-I", DJ + "DejaVuSans-Oblique.ttf")]:
    pdfmetrics.registerFont(TTFont(n, f))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ-I", boldItalic="DJ-B")
W, H, M = 612.0, 792.0, 54.0
HDR = 118.0                                    # points kept clear above the first system of a piece, for its heading
PLAY = "https://alexattardmusic.com/play/"
METRE = {"2/4": "2/4", "3/4": "3/4", "4/4": "4/4"}

def mixed(c, x, y, text, font, size, right=False, centre=False):
    """Poppins has no flat, sharp or middle-dot-free music glyphs: switch to DejaVu for those."""
    alt = "DJ-B" if font in ("Pop-B", "Pop-M") else "DJ"; parts = [p for p in re.split("([♭♯♩])", text) if p]
    wd = sum(pdfmetrics.stringWidth(p, alt if p in "♭♯♩" else font, size) for p in parts)
    if right: x -= wd
    if centre: x -= wd / 2
    for p in parts:
        f = alt if p in "♭♯♩" else font; c.setFont(f, size); c.drawString(x, y, p); x += pdfmetrics.stringWidth(p, f, size)
    return wd

def nice(s): return s.replace("E-flat", "E♭").replace("B-flat", "B♭")
def keyname(k): return (k[:-1] if k.endswith("m") else k).replace("b", "♭") + (" minor" if k.endswith("m") else " major")

def qr_img(url, colour=SLATE):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1); q.add_data(url); q.make(fit=True)
    return ImageReader(q.make_image(fill_color=colour, back_color="white").get_image())

def para(c, text, x, y, w, style):
    p = Paragraph(text, style); _, h = p.wrap(w, 1000); p.drawOn(c, x, y - h); return y - h

def footer(c, book, n):
    c.setStrokeColor(HexColor(RULE)); c.setLineWidth(0.6); c.line(M, 40, W - M, 40)
    c.setFillColor(HexColor(MUTED)); c.setFont("Pop", 8)
    c.drawString(M, 27, "%s  ·  Level %s  ·  %s" % (book["series"], book["level"], book["strand"]))
    c.setFont("Pop-B", 9); c.setFillColor(HexColor(SLATE)); c.drawRightString(W - M, 27, str(n))

BODY = ParagraphStyle("b", fontName="DJ", fontSize=10.5, leading=15.5, textColor=HexColor(SLATE))
SMALL = ParagraphStyle("s", fontName="DJ", fontSize=8.6, leading=12.2, textColor=HexColor(MUTED))

# ---------------------------------------------------------------- ABC (one string per bar) -> LilyPond
DUR = {0.25: "32", 0.5: "16", 0.75: "16.", 1: "8", 1.5: "8.", 2: "4", 3: "4.", 4: "2", 6: "2.", 8: "1"}
def eighths(txt):
    if not txt: return 1.0
    num, _, den = txt.partition("/")
    return (int(num) if num else 1) / (int(den) if den else (2 if "/" in txt else 1))
def ly_pitch(acc, letter, octs, ks, alt):
    L = letter.upper(); name = (L, letter.islower(), octs)
    if acc: alt[name] = {"_": -1, "=": 0, "^": 1}[acc]
    a = alt.get(name, ks.get(L, 0)); o = 4 + (1 if letter.islower() else 0) + octs.count("'") - octs.count(",")
    return L.lower() + {1: "is", -1: "es", 0: ""}[a] + ("'" * (o - 3) if o >= 3 else "," * (3 - o))
def ly_hand(bars, key, show_dyn):
    ks, out = keysig(key), []
    for bar in bars:
        pos, alt, toks, trip, dyn = 0, {}, [], 0, ""
        while pos < len(bar):
            m = TOKEN.match(bar, pos); pos = m.end(); tok = m.group(0)
            if m.group(1):
                if m.group(1) in ("pp", "p", "mp", "mf", "f", "ff") and show_dyn: dyn = "\\" + m.group(1)
                continue
            if tok == "(3": toks.append("\\tuplet 3/2 {"); trip = 3; continue
            chord, single = m.group(2), m.group(7)
            if not chord and not single: continue
            dtxt, tie = (m.group(3), m.group(4)) if chord else (m.group(9), m.group(10))
            d = DUR[eighths(dtxt)]
            if chord: n = "<" + " ".join(ly_pitch(a, l, o, ks, alt) for a, l, o in re.findall(r"([_=^]?)([A-Ga-g])([,']*)", chord)) + ">" + d
            elif single == "z": n = "r" + d
            else: n = ly_pitch(m.group(6), single, m.group(8), ks, alt) + d + ("-." if m.group(5) else "")
            if dyn and not n.startswith("r"): n += dyn; dyn = ""
            toks.append(n + ("~" if tie else ""))
            if trip:
                trip -= 1
                if not trip: toks.append("}")
        out.append(" ".join(toks))
    return " |\n    ".join(out) + ' \\bar "|."'

def ly_key(key):
    t = key.rstrip("m"); return t[0].lower() + ("es" if t.endswith("b") else "is" if t.endswith("#") else "") + (" \\minor" if key.endswith("m") else " \\major")

def plan(p):
    """Pages and staff size for a piece: beginners get large notes, and no page is left half empty."""
    n = len(p["rh"]); dense = max(len(b) for b in p["rh"]) > 22
    if n <= 24 and not (dense and n > 20):
        systems = math.ceil(n / 4); return 1, systems, {4: 25, 5: 23.5, 6: 21.5}.get(systems, 21.5)
    systems = math.ceil(n / (3 if dense else 4)); systems += systems % 2
    return 2, systems, 22 if systems <= 8 else 20

def engrave(p, tmp):
    pages, systems, size = plan(p); gap = HDR * 4 / size
    src = r'''\version "2.24.0"
#(set-default-paper-size "letter")
#(set-global-staff-size %(size)s)
\paper { top-margin = 19\mm bottom-margin = 21\mm left-margin = 19\mm right-margin = 19\mm indent = 0
  print-page-number = ##f ragged-bottom = ##f ragged-last-bottom = ##f ragged-last = ##f
  system-count = %(systems)d page-count = %(pages)d
  markup-system-spacing.basic-distance = #4 markup-system-spacing.padding = #1
  system-system-spacing.basic-distance = #17 system-system-spacing.padding = #3 }
\header { tagline = ##f }
\markup \pad-to-box #'(0 . 0) #'(0 . %(gap).2f) \null
\score {
  \new PianoStaff \with { \override StaffGrouper.staff-staff-spacing.basic-distance = #11 } <<
    \new Staff { \clef treble \key %(key)s \time %(meter)s \accidentalStyle piano \override Score.BarNumber.color = #(rgb-color 0.42 0.47 0.52) \tempo 4 = %(tempo)d
    %(rh)s }
    \new Staff { \clef bass \key %(key)s \time %(meter)s \accidentalStyle piano
    %(lh)s }
  >>
  \layout { \context { \Score \override SpacingSpanner.common-shortest-duration = #(ly:make-moment 1/8) } }
}
''' % dict(size=size, systems=systems, pages=pages, gap=gap, key=ly_key(p["key"]), meter=p["meter"], tempo=p["tempo"],
           rh=ly_hand(p["rh"], p["key"], True), lh=ly_hand(p["lh"], p["key"], False))
    base = os.path.join(tmp, p["slug"]); open(base + ".ly", "w").write(src)
    r = subprocess.run(["lilypond", "-s", "-o", base, base + ".ly"], capture_output=True, text=True)
    assert os.path.exists(base + ".pdf"), r.stderr[-1500:]
    return PdfReader(base + ".pdf")

def cover_motif(tmp, colour):
    """A few engraved bars for the cover, in the strand colour on a transparent ground."""
    src = r'''\version "2.24.0"
#(set-global-staff-size 34)
\paper { indent = 0 line-width = 190\mm ragged-right = ##f top-margin = 4\mm bottom-margin = 4\mm left-margin = 4\mm }
\header { tagline = ##f }
\score { \new Staff \with { \remove "Time_signature_engraver" \remove "Bar_number_engraver" } { \clef treble \key g \major \time 3/4
  d''4 g'8 a' b' c'' | d''4 g' g' | e''4 c''8 d'' e'' fis'' | g''4 g' g' } \layout { } }'''
    base = os.path.join(tmp, "motif"); open(base + ".ly", "w").write(src)
    subprocess.run(["lilypond", "-s", "--png", "-dresolution=300", "-dcrop", "-o", base, base + ".ly"], capture_output=True)
    f = base + ".cropped.png" if os.path.exists(base + ".cropped.png") else base + ".png"
    im = Image.open(f).convert("L"); rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
    out = Image.new("RGBA", im.size, rgb + (0,)); out.putalpha(im.point(lambda v: 255 - v)); return ImageReader(out), im.size

# ---------------------------------------------------------------- pages
def cover(c, book, tmp, n):
    acc = STRANDS.get(book["strand"], AMBER); top = H * 0.60
    c.setFillColor(HexColor(SLATE)); c.rect(0, H - top, W, top, fill=1, stroke=0)
    c.setFillColor(HexColor(acc)); c.rect(0, H - top - 7, W, 7, fill=1, stroke=0)
    c.setFillColor(HexColor(acc)); c.setFont("Pop-B", 10.5); c.drawString(M, H - 78, " ".join("ALEX ATTARD MUSIC"))
    c.setFillColor(white); c.setFont("Pop-B", 50); c.drawString(M - 2, H - 150, "Graded"); c.drawString(M - 2, H - 204, "Repertoire")
    c.setFillColor(HexColor(acc)); c.setFont("Pop-M", 23); c.drawString(M, H - 246, book["strand"])
    c.setFillColor(HexColor("#C9D2DB")); c.setFont("Pop", 14); c.drawString(M, H - 272, book.get("instrument", "piano").capitalize())
    img, (iw, ih) = cover_motif(tmp, acc); mw = W - 2 * M - 150; mh = mw * ih / iw
    c.drawImage(img, M - 6, H - top + 46, mw, mh, mask="auto")
    r = 78; cx, cy = W - M - r + 6, H - top + 4                       # the level medallion sits across the edge of the band
    c.setFillColor(white); c.circle(cx, cy, r + 7, fill=1, stroke=0)
    c.setFillColor(HexColor(acc)); c.circle(cx, cy, r, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Pop-B", 11); c.drawCentredString(cx, cy + 40, " ".join("LEVEL"))
    c.setFont("Pop-B", 92); c.drawCentredString(cx, cy - 42, str(book["level"]))
    y = H - top - 70
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 15); c.drawString(M, y, "%d pieces, every one in the practice player" % n)
    y = para(c, "Scan the code beside any piece and it opens on your phone, tablet or computer. Slow it down, loop the hard bars, hear one hand at a time, and play along with the metronome.", M, y - 12, W - 2 * M - 190, BODY)
    c.setFillColor(HexColor(MUTED)); c.setFont("Pop-M", 9.5)
    comps = []; [comps.append(x) for x in book["_composers"] if x not in comps]
    c.drawString(M, 96, "  ·  ".join(comps))
    c.setStrokeColor(HexColor(RULE)); c.line(M, 80, W - M, 80)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 10); c.drawString(M, 60, "Alex Attard Music"); c.setFont("Pop", 9.5); c.setFillColor(HexColor(MUTED)); c.drawRightString(W - M, 60, "alexattardmusic.com")

def heading(c, kicker, title, acc):
    c.setFillColor(HexColor(acc)); c.setFont("Pop-B", 9); c.drawString(M, H - M - 10, " ".join(kicker.upper()))
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 27); c.drawString(M, H - M - 44, title)
    c.setStrokeColor(HexColor(acc)); c.setLineWidth(2.5); c.line(M, H - M - 57, M + 60, H - M - 57); return H - M - 82

def howto(c, book, code, first):
    acc = STRANDS.get(book["strand"], AMBER); y = heading(c, "Start here", "How this book works", acc)
    y = para(c, "Every piece in this book also lives in the Alex Attard Music practice player. You read the same notes on the page and on the screen, and the player plays them for you at any speed.", M, y, W - 2 * M - 150, BODY)
    q = 104; qy = H - M + 4 - q; c.drawImage(qr_img(PLAY + "?t=" + first + "&c=" + re.sub("[^A-Z0-9]", "", code.upper())), W - M - q, qy, q, q)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 8.5); c.drawCentredString(W - M - q / 2, qy - 11, "Scan to open the player")
    c.setFont("DJ", 8.5); c.setFillColor(HexColor(MUTED)); c.drawCentredString(W - M - q / 2, qy - 23, "Book code: " + code)
    y -= 30
    steps = [("Listen first", "Open the piece and press play. Follow the notes on screen while the player plays them."),
             ("One hand at a time", "In Practice settings, switch off Right hand or Left hand. Play the hand that is switched off while the player plays the other."),
             ("Loop the hard bars", "Press and hold the first bar of a tricky spot, slide to its last bar and let go. The player repeats just those bars."),
             ("Climb the tempo ladder", "Each piece shows three tempos. Start on the slowest. When you can play it three times in a row without a mistake, move up one step."),
             ("Play with the metronome only", "Tap the metronome button and choose Metronome only. Now the click keeps time and the music is all you.")]
    for i, (t, d) in enumerate(steps):
        c.setFillColor(HexColor(acc)); c.circle(M + 13, y - 9, 13, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 13); c.drawCentredString(M + 13, y - 13.5, str(i + 1))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M + 38, y - 6, t)
        y = para(c, d, M + 38, y - 14, W - 2 * M - 38, BODY) - 22
    bh = 96; c.setFillColor(HexColor(TINT)); c.roundRect(M, y - bh, W - 2 * M, bh, 8, fill=1, stroke=0); c.setFillColor(HexColor(acc)); c.rect(M, y - bh, 4, bh, fill=1, stroke=0)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 11.5); c.drawString(M + 18, y - 22, "A good practice session")
    para(c, "Ten focused minutes beat an hour of playing through. Pick one piece. Listen once. Play each hand alone on the slowest tempo. Loop the two hardest bars five times each. Then play the whole piece once, hands together, and stop there.", M + 18, y - 30, W - 2 * M - 36, BODY)

def contents(c, book, rows):
    acc = STRANDS.get(book["strand"], AMBER); y = heading(c, "Level %s" % book["level"], "What's inside", acc) - 6
    for i, (p, pg) in enumerate(rows):
        c.setFillColor(HexColor(acc)); c.setFont("Pop-B", 13); c.drawRightString(M + 20, y, str(i + 1))
        c.setFillColor(HexColor(SLATE)); wd = mixed(c, M + 34, y, nice(p["title"]), "Pop-M", 12.5)
        c.setFont("Pop-B", 12.5); c.drawRightString(W - M, y, str(pg))
        c.setStrokeColor(HexColor(RULE)); c.setLineWidth(0.8); c.setDash(1, 3); c.line(M + 34 + wd + 8, y + 2, W - M - 22, y + 2); c.setDash()
        c.setFillColor(HexColor(MUTED)); mixed(c, M + 34, y - 14, "%s  ·  %s  ·  %s" % (p["composer"].split(",")[0].split(" (")[0], keyname(p["key"]), p["meter"]), "Pop", 8.8)
        y -= 44.5

def piece_header(c, p, i, book, code):
    acc = STRANDS.get(book["strand"], AMBER); top = H - M + 4
    c.setFillColor(HexColor(acc)); c.circle(M + 17, top - 21, 17, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Pop-B", 17 if i < 9 else 15); c.drawCentredString(M + 17, top - 27, str(i + 1))
    q = 62; tw = W - 2 * M - 48 - q - 14; title = nice(p["title"]); size = 21
    while pdfmetrics.stringWidth(title, "Pop-B", size) > tw and size > 13: size -= 0.5
    c.setFillColor(HexColor(SLATE)); mixed(c, M + 46, top - 20, title, "Pop-B", size)
    c.setFillColor(HexColor(MUTED)); c.setFont("Pop", 9.5); c.drawString(M + 46, top - 35, p["composer"])
    c.drawImage(qr_img(PLAY + "?t=" + p["slug"] + "&c=" + re.sub("[^A-Z0-9]", "", code.upper())), W - M - q, top - q + 2, q, q)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 6.6); c.drawCentredString(W - M - q / 2, top - q - 7, "SCAN TO PLAY")
    y = para(c, "<b>Practice note.</b> " + book.get("practice", {}).get(p["slug"][4:], ""), M, top - 50, W - 2 * M - q - 18, ParagraphStyle("pn", parent=BODY, fontSize=9.4, leading=13.2))
    t = p["tempo"]; x = M; c.setFont("Pop-B", 8); c.setFillColor(HexColor(acc)); c.drawString(x, y - 15, "TEMPO LADDER"); x += 78
    for k, v in enumerate([round(t * 0.6), round(t * 0.8), t]):
        c.setFillColor(HexColor(TINT)); c.roundRect(x, y - 20, 52, 15, 7.5, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); mixed(c, x + 26, y - 15.5, "♩ = %d" % v, "Pop-M", 8.5, centre=True); x += 58
        if k < 2: c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 9); c.drawString(x - 5, y - 15.5, "›"); x += 6

def sources(c, book, pieces):
    acc = STRANDS.get(book["strand"], AMBER); y = heading(c, "About this edition", "Sources", acc)
    y = para(c, "The music in this book is in the public domain. The notes were checked against the sources below; ornaments are left out at this level. Arrangements, practice notes and the edition as a whole are by Alex Attard Music.", M, y, W - 2 * M, BODY) - 12
    for i, p in enumerate(pieces):
        y = para(c, "<b>%d. %s.</b> %s" % (i + 1, nice(p["title"]), p.get("print_source") or p.get("source", "")), M, y, W - 2 * M, SMALL) - 5.5
    series_map(c, book, y - 26)

def series_map(c, book, y):
    """Where this book sits in the series: four strands by eight levels."""
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y, "The series"); y -= 14
    y = para(c, "Eight levels, four books at each level. This book is marked. More levels and strands are on the way.", M, y, W - 2 * M, SMALL) - 22
    x0, cw, rh = M + 150, (W - 2 * M - 150) / 8, 25
    c.setFillColor(HexColor(MUTED)); c.setFont("Pop-B", 8)
    for l in range(8): c.drawCentredString(x0 + cw * l + cw / 2, y + 6, "LEVEL %d" % (l + 1))
    for name, col in STRANDS.items():
        y -= rh; c.setFillColor(HexColor(col)); c.circle(M + 5, y + 9, 4.5, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 9.5); c.drawString(M + 16, y + 6, name)
        for l in range(8):
            here = name == book["strand"] and l + 1 == book["level"]
            c.setFillColor(HexColor(col if here else "#EEF1F4")); c.roundRect(x0 + cw * l + 3, y, cw - 6, rh - 6, 5, fill=1, stroke=0)
            if here: c.setFillColor(white); c.setFont("Pop-B", 6.2); c.drawCentredString(x0 + cw * l + cw / 2, y + 7, "THIS BOOK")

def overlay(draw):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(W, H)); draw(c); c.save(); buf.seek(0); return PdfReader(buf).pages[0]

def build(book_path, code, out):
    book = json.load(open(book_path)); pieces = [json.load(open(os.path.join(ROOT, "repertoire", "src", n + ".json"))) for n in book["pieces"]]
    book["_composers"] = [re.sub(r"^.*\b(Haydn|Beethoven|Mozart|Handel|Petzold)\b.*$", r"\1", p["composer"]) if re.search(r"Haydn|Beethoven|Mozart|Handel|Petzold", p["composer"]) else "The Anna Magdalena Notebook" for p in pieces]
    wr = PdfWriter()
    with tempfile.TemporaryDirectory() as tmp:
        music = [engrave(p, tmp) for p in pieces]
        pg, rows = 4, []
        for p, m in zip(pieces, music): rows.append((p, pg)); pg += len(m.pages)
        wr.add_page(overlay(lambda c: cover(c, book, tmp, len(pieces))))
        wr.add_page(overlay(lambda c: (howto(c, book, code, pieces[0]["slug"]), footer(c, book, 2))))
        wr.add_page(overlay(lambda c: (contents(c, book, rows), footer(c, book, 3))))
        n = 4
        for i, (p, m) in enumerate(zip(pieces, music)):
            for k, page in enumerate(m.pages):
                def draw(c, k=k, n=n, i=i, p=p):
                    if k == 0: piece_header(c, p, i, book, code)
                    else: c.setFillColor(HexColor(MUTED)); mixed(c, M, H - 38, "%d  ·  %s (continued)" % (i + 1, nice(p["title"])), "Pop-M", 9)
                    footer(c, book, n)
                page.merge_page(overlay(draw)); wr.add_page(page); n += 1
        wr.add_page(overlay(lambda c: (sources(c, book, pieces), footer(c, book, n))))
        wr.add_metadata({"/Title": "%s, Level %s: %s" % (book["series"], book["level"], book["strand"]), "/Author": "Alex Attard Music"})
        wr.write(out)
    print(out, len(wr.pages), "pages")

if __name__ == "__main__":
    a = sys.argv; build(a[1], a[a.index("--code") + 1], a[a.index("--out") + 1] if "--out" in a else "graded-repertoire.pdf")
