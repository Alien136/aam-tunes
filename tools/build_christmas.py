#!/usr/bin/env python3
"""Alex Attard Music: Christmas Tunes for Beginner Flute.

Eight public-domain carols, one to a page, each inside the notes the Flute Beginner Booklet teaches. Every page shows the notes
the tune needs with their fingerings, chord symbols for a parent or teacher, and a QR code that opens the tune in the player,
where a piano plays along (switch the flute off to play with the piano alone).

  python3 tools/build_christmas.py                                  # the PDF, no QR codes
  AAM_CODE=<teacher code> python3 tools/build_christmas.py --code <book code> --publish <repo>

Melodies: checked against the engraved scores in "A Collection of Christmas Carols" (Benjamin Bloomfield, public domain,
github.com/bbloomf/christmas-carols) and the Mutopia Project; see each tune's `src`. Keys, easy rhythms, chords and the piano
part are ours. The book's code is never written in the repository."""
import hashlib, io, json, os, re, subprocess, sys
ARGS = sys.argv[1:]
CODE = ARGS[ARGS.index("--code") + 1] if "--code" in ARGS else None
REPO = ARGS[ARGS.index("--publish") + 1] if "--publish" in ARGS else None
sys.argv = [sys.argv[0], "flute"] + (["--code", CODE] if CODE else [])
import build_beginner as BB                                           # the flute fingerings, note names, the player's note parser
B, FL, PX = BB.B, BB.FL, BB.PX
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from PIL import Image

W, H, M = B.W, B.H, B.M
CW = W - 2 * M
SLATE, AMBER, TINT, MUTED, RULE = B.SLATE, B.AMBER, B.TINT, B.MUTED, B.RULE
BOOK_ID, BOOK_TITLE, EDITION = "flute-christmas", "Christmas Tunes for Flute", "Edition 1 · November 2026"
BBC = "checked against the score in A Collection of Christmas Carols (B. Bloomfield, public domain)"
MUT = "checked against the Mutopia Project score (public domain)"
NAMES = {}
for _u in BB.UNITS:
    for _ly, _name, _tip in _u["notes"]: NAMES[_ly] = _name

# music: LilyPond, absolute pitch, bars separated by "|".  chords: one entry per bar, "G" or "C:2 D7:2" (chord:beats).
TUNES = [
    dict(title="Jingle Bells", by="James Pierpont, 1857", key="g", time="4/4", tempo=100, bpl=4, marks={0: "Chorus", 16: "Verse"},
         music="b'4 b' b'2 | b'4 b' b'2 | b'4 d'' g' a' | b'1 | c''4 c'' c'' c'' | c'' b' b' b' | b' a' a' b' | a'2 d''2 | "
               "b'4 b' b'2 | b'4 b' b'2 | b'4 d'' g' a' | b'1 | c''4 c'' c'' c'' | c'' b' b' b' | d'' d'' c'' a' | g'1 | "
               "d'4 b' a' g' | d'2. r4 | d'4 b' a' g' | e'2. r4 | e'4 c'' b' a' | fis'2. r4 | fis'4 e'' d'' c'' | b'2. r4 | "
               "d'4 b' a' g' | d'2. r4 | d'4 b' a' g' | e'2. r4 | e'4 c'' b' a' | fis' d'' cis'' d'' | e'' d'' c'' a' | g'1",
         chords="G|G|G|G|C|G|A7|D7|G|G|G|G|C|G|D7|G|G|G|G|C|Am|D7|D7|G|G|G|G|C|Am|D7|D7|G",
         tip="Start with the chorus: it uses only five notes. The verse dips down to low D, so keep your air slow and warm there. Play the chorus once more to finish.",
         src="Verse " + BBC + ", moved to G, note lengths doubled. Chorus: the tune as it is sung today, easy rhythm, written from memory: check (the 1857 print has a different chorus)."),
    dict(title="Jolly Old Saint Nicholas", by="American, 1860s", key="c", time="4/4", tempo=96, bpl=4,
         music="e''4 e'' e'' e'' | d'' d'' d''2 | c''4 c'' c'' c'' | e''1 | a'4 a' a' a' | g' g' c''2 | b'4 c'' d'' e'' | d''1 | "
               "e''4 e'' e'' e'' | d'' d'' d''2 | c''4 c'' c'' c'' | e''1 | a'4 a' a' a' | g' g' c''2 | d''4 c'' d'' e'' | c''1",
         chords="C|G|Am|Em|F|C|G|G7|C|G|Am|Em|F|C|G7|C",
         tip="Lots of repeated notes: tongue each one lightly with \"too\". Take a breath every two bars, after the long notes.",
         src=BBC + ", moved to C, note lengths doubled."),
    dict(title="Away in a Manger", by="James R. Murray, 1887", key="g", time="3/4", tempo=84, bpl=4, partial=1,
         music="d''4 | d''4. c''8 b'4 | b'4. a'8 g'4 | g' fis' e' | d'2 d'4 | d'4. e'8 d'4 | d' a' fis' | e' d' g' | b'2 d''4 | "
               "d''4. c''8 b'4 | b'4.( a'8) g'4 | g' fis' e' | d'2 d'4 | c''4. b'8 a'4 | b' a' g' | a' e' fis' | g'2",
         chords="-|G|G|C|G|D7|D7|G|G|G|G|C|G|D7|G|D7|G",
         tip="Three beats in a bar: count 1-2-3 and lean a little on beat 1. Hold each dotted quarter note for a beat and a half.",
         src=BB.WIKI + " and against A Collection of Christmas Carols; moved to G."),
    dict(title="Silent Night", by="Franz Gruber, 1818", key="d", time="3/4", tempo=80, bpl=4,
         music="a'4. b'8 a'4 | fis'2. | a'4. b'8 a'4 | fis'2. | e''2 e''4 | cis''2. | d''2 d''4 | a'2. | "
               "b'2 b'4 | d''4. cis''8 b'4 | a'4. b'8 a'4 | fis'2. | b'2 b'4 | d''4. cis''8 b'4 | a'4. b'8 a'4 | fis'2. | "
               "e''2 e''4 | g''4. e''8 cis''4 | d''2. | fis''2. | d''4. a'8 fis'4 | a'4. g'8 e'4 | d'2.~ | d'2.",
         chords="D|D|D|D|A7|A7|D|D|G|G|D|D|G|G|D|D|A7|A7|D|D|D|A7|D|D",
         tip="A slow tune for your best sound. Breathe every four bars and let each long note sing to its full length. The top G near the end needs faster air, not more force.",
         src=MUT + " and against A Collection of Christmas Carols; moved to D and written in 3/4 (the original is in 6/8)."),
    dict(title="We Wish You a Merry Christmas", by="English traditional", key="g", time="3/4", tempo=104, bpl=4, partial=1,
         music="d'4 | g'4 g'8 a' g' fis' | e'4 e' e' | a'4 a'8 b' a' g' | fis'4 d' d' | b'4 b'8 c'' b' a' | g'4 e' d'8 d' | e'4 a' fis' | g'2 d'4 | "
               "g'4 g' g' | fis'2 fis'4 | g'4 fis' e' | d'2 a'4 | b'4 a' g' | d''4 d' d'8 d' | e'4 a' fis' | g'2",
         chords="-|G|C|A7|D|B7|Em|Am:2 D7:1|G|G|D|Em|D|G|G|Am:2 D7:1|G",
         tip="Each line starts one step higher than the last. Practice the eighth notes slowly first, then play the first eight bars again to finish.",
         src=BBC + ", moved to G."),
    dict(title="Deck the Halls", by="Welsh traditional", key="f", time="4/4", tempo=100, bpl=4,
         music="c''4. bes'8 a'4 g' | f' g' a' f' | g'8 a' bes' g' a'4. g'8 | f'4 e' f'2 | c''4. bes'8 a'4 g' | f' g' a' f' | g'8 a' bes' g' a'4. g'8 | f'4 e' f'2 | "
               "g'4. a'8 bes'4 g' | a'4. bes'8 c''4 g' | a'8 b' c''4 d''8 e'' f''4 | e'' d'' c''2 | c''4. bes'8 a'4 g' | f' g' a' f' | d''8 d'' d'' d'' c''4. bes'8 | a'4 g' f'2",
         chords="F|F|C7:2 F:2|F:1 C7:1 F:2|F|F|C7:2 F:2|F:1 C7:1 F:2|C7|F|F:2 G7:2|C:1 G7:1 C:2|F|F|Bb:2 F:2|F:1 C7:1 F:2",
         tip="Every B is B flat, except one: bar 11 has a B natural on the way up to the top F. The dotted quarter and eighth is the \"Deck the\" rhythm: long, short.",
         src=BBC + " (the key and rhythm of the score)."),
    dict(title="Joy to the World", by="Lowell Mason, 1839", key="d", time="4/4", tempo=104, bpl=4,
         music="d''2 cis''4. b'8 | a'2. g'4 | fis'2 e' | d'2. a'4 | b'2. b'4 | cis''2. cis''4 | d''2. d''4 | d'' cis'' b' a' | a'4. g'8 fis'4 d'' | "
               "d'' cis'' b' a' | a'4. g'8 fis'4 fis' | fis' fis' fis' fis'8 g' | a'2. g'8 fis' | e'4 e' e' e'8 fis' | g'2. fis'8 e' | d'4( d''2) b'4 | "
               "a'4. g'8 fis'4 g' | fis'2 e' | d'1",
         chords="D|D|D:2 A7:2|D|G|A7|D|D|D|D|D|D|D|A7|A7|D:3 G:1|D|D:2 A7:2|D",
         tip="The first eight notes are the D major scale coming down: say the note names before you play. F and C are both sharp all the way through.",
         src=MUT + " and against A Collection of Christmas Carols (the key of the score), note lengths doubled."),
    dict(title="O Come, All Ye Faithful", by="John Francis Wade, about 1743", key="g", time="4/4", tempo=92, bpl=4, partial=1,
         music="g'4 | g'2 d'4 g' | a'2 d'2 | b'4 a' b' c'' | b'2 a'4 g' | g'2 fis'4 e' | fis'( g') a' b' | fis'2( e'4.) d'8 | d'1 | "
               "d''2 c''4 b' | c''2 b'2 | a'4 b' g' a' | fis'2 d'4 g' | g' fis' g' a' | g'2 d'4 b' | b' a' b' c'' | b'2 a'4 b' | c'' b' a' g' | "
               "fis'2 g'4( c'') | b'2( a'4.) g'8 | g'2.",
         chords="-|G|D|G|G:2 D:2|G:2 D:2|D|D:2 A7:2|D|G|Am:2 G:2|D|D:3 G:1|G|G|G|G:2 D:2|C:2 G:2|D:2 G:1 C:1|G:2 D7:2|G",
         tip="The longest tune in the book, so learn it four bars at a time. Slurred notes share one breath of air: tongue only the first one.",
         src=BB.WIKI + " and against A Collection of Christmas Carols."),
]
for _k, _t in enumerate(TUNES): _t["no"] = _k + 1; _t["slug"] = BOOK_ID + "-" + re.sub(r"[^a-z0-9]+", "-", _t["title"].lower()).strip("-")

PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
def bpb_of(t): return int(t["time"][0])
def chord_bars(t):
    """[[(symbol, beats), ...] or [] for the pick-up bar] per bar."""
    out = []
    for bar in t["chords"].split("|"):
        if bar.strip() == "-": out.append([]); continue
        segs = [(p.split(":")[0], float(p.split(":")[1]) if ":" in p else None) for p in bar.split()]
        if len(segs) == 1 and segs[0][1] is None: segs = [(segs[0][0], float(bpb_of(t)))]
        out.append(segs)
    short = bar_beats(t["music"].split("|")[-1])                           # a short last bar: its chord lasts only as long as the bar
    if short < bpb_of(t) and len(out[-1]) == 1: out[-1] = [(out[-1][0][0], short)]
    return out
def bar_beats(bar):
    tot, dur = 0.0, "4"
    for tok in bar.split():
        m = re.match(r"^(?:[a-g](?:is|es)?[',]*|r)(\d*\.*)", BB.STRIP.sub("", tok))
        if m:
            dur = m.group(1) or dur; tot += BB.BEATS[dur]
    return tot
def chord_tones(sym):
    m = re.match(r"^([A-G])(b|#)?(m)?(7)?$", sym); assert m, sym
    root = (PC[m.group(1)] + {"b": -1, "#": 1, None: 0}[m.group(2)]) % 12
    third = 3 if m.group(3) else 4
    return root, ([third, 7, 10] if m.group(4) else [0, third, 7])
def piano(t):
    """A plain accompaniment: the bass note on the chord, the chord on the beats after it."""
    ev, bpb = [], bpb_of(t)
    for bi, segs in enumerate(chord_bars(t)):
        at = 0.0
        last = bi == len(chord_bars(t)) - 1
        for sym, beats in segs:
            root, tones = chord_tones(sym)
            bass = 36 + root + (12 if root < 4 else 0)                       # E2 to E flat 3
            notes = sorted(55 + ((root + x - 55) % 12) for x in tones)        # the chord between G3 and F sharp 4
            if last:
                ev.append([bi * bpb + at, bass, beats, 62]); ev += [[bi * bpb + at, n, beats, 50] for n in notes]
            else:
                for b in range(int(beats)):
                    if b == 0: ev.append([bi * bpb + at, bass, 1.0, 64])
                    elif bpb == 4 and b == 2 and beats == 4: ev.append([bi * bpb + at + b, bass + (7 if bass + 7 <= 52 else -5), 1.0, 58])
                    else: ev += [[bi * bpb + at + b, n, 0.9, 50] for n in notes]
            at += beats
    return sorted(ev)

def to_tune(t):
    import gen_study as g
    bpb = bpb_of(t); wkey = t["key"].capitalize(); wk = g.parse_note(wkey)
    it = dict(title=t["title"])
    ev, abc, marks, roots = BB.parse_part(it, t["music"], bpb, wk, 0); seq = BB.parse_part.seq
    T = t["tempo"] - 20
    chords = [[dict(sym=BB.PCS[wk.pc % 12], beats=bpb, root=wk.pc % 12, degs=[0, 2, 4, 5, 7, 9, 11], scale="Ionian (major)")] for _ in abc]
    sec = dict(id="notes", title="Notes", tab="Notes", desc="Switch off Flute to play with the piano alone", rh=ev, lh=piano(t), abc=dict(rh=abc, marks=marks), learn=seq)
    tune = dict(format="aam-tune/1", slug=t["slug"], title="%d · %s" % (t["no"], t["title"]), subtitle=BOOK_TITLE, instrument="flute",
                concert_key=BB.PCS[wk.pc % 12], native=g.INSTRUMENTS["flute"][1] % 12, style="click", keys="off", hide=["chords", "solo", "names"], hear=True, first_bar=1,
                chart_tempo=T, tempo_presets=[T, T + 20, T + 40], form=[], bars=chords, sections=[sec], notation=dict(key=wkey, staves="treble"),
                hand_labels=["Flute", "Piano"], page=t["page"], source=t["src"])
    if bpb != 4: tune["meter"] = [bpb, 4]
    return tune

def publish(repo):
    ip = os.path.join(repo, "index.json"); idx = json.load(open(ip))
    h = hashlib.sha256(("aam:" + re.sub(r"[^A-Z0-9]", "", CODE.upper())).encode()).hexdigest()
    clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == h and p["id"] != BOOK_ID]; assert not clash, "that code is already used by " + clash[0]
    slugs = []
    for t in TUNES:
        tune = to_tune(t); json.dump(tune, open(os.path.join(repo, "tunes", t["slug"] + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
        idx["tunes"][t["slug"]] = dict(title=tune["title"], subtitle=tune["subtitle"]); slugs.append(t["slug"])
    old = next((p for p in idx["pdfs"] if p["id"] == BOOK_ID), None)
    kept = [x for x in (old["tunes"] if old else []) if x not in slugs]
    entry = dict(id=BOOK_ID, title=BOOK_TITLE, hash=h, tunes=slugs + kept, contents=[dict(title="Eight Christmas tunes", items=slugs)])
    rest = [p for p in idx["pdfs"] if p["id"] != BOOK_ID]; at = next((i for i, p in enumerate(rest) if p.get("free")), len(rest))
    idx["pdfs"] = rest[:at] + [entry] + rest[at:]
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    print("published %d tunes for %s" % (len(slugs), BOOK_TITLE))

# ---------------------------------------------------------------- engraving
def tune_ly(t, size, space=15):
    bpb = bpb_of(t); bars = [b.strip() for b in t["music"].split("|")]; out = []; full = 0
    for i, b in enumerate(bars):
        pick = bool(t.get("partial")) and i == 0
        idx = i - (1 if t.get("partial") else 0)
        if not pick and idx in t.get("marks", {}):
            b = re.sub(r"^(\S+)", lambda m: m.group(1) + '^\\markup \\with-color "' + AMBER + '" \\sans \\bold "' + t["marks"][idx] + '"', b, count=1)
        out.append(b)
        if not pick:
            full += 1
            if full % t["bpl"] == 0 and i < len(bars) - 1: out.append("\\break")
            else: out.append("|")
        else: out.append("|")
    ch = []
    for bi, segs in enumerate(chord_bars(t)):
        if not segs: ch.append("s4" if t["partial"] == 1 else "s2"); continue
        for sym, beats in segs:
            ch.append(_lychord(sym, beats, bpb))
    return ('\\version "2.24.0"\n#(set-global-staff-size %s)\n\\header { tagline = ##f }\n'
            '\\paper { indent = 0 paper-width = 180\\mm line-width = 176\\mm left-margin = 2\\mm top-margin = 4\\mm paper-height = 600\\mm ragged-bottom = ##t ragged-last-bottom = ##t print-page-number = ##f\n'
            '  #(define fonts (set-global-fonts #:roman "DejaVu Sans" #:sans "Poppins" #:factor (/ staff-height pt 20)))\n'
            '  system-system-spacing = #\'((basic-distance . %s) (minimum-distance . %s) (padding . 1.2) (stretchability . 0)) }\n'
            '\\layout { ragged-last = ##f \\context { \\Score \\omit BarNumber } \\context { \\ChordNames \\override ChordName.font-size = #1 \\override ChordName.color = #(rgb-color 0.184 0.243 0.306) } }\n'
            '<< \\new ChordNames \\chordmode { %s }\n   \\new Staff { \\key %s \\major \\time %s %s %s \\bar "|." } >>\n'
            % (size, space, space - 2, " ".join(ch), t["key"], t["time"], ("\\partial 4 " if t.get("partial") else ""), " ".join(out).rstrip("| ")))
def render(src):
    """Engrave on one tall page and trim the white: the spacing between the lines is then ours to set."""
    h = hashlib.md5(src.encode()).hexdigest()[:14]; base = os.path.join(BB.CACHE, "x" + h); png = base + ".t.png"
    if not os.path.exists(png):
        open(base + ".ly", "w").write(src)
        r = subprocess.run(["lilypond", "-s", "--png", "-dresolution=300", "-o", base, base + ".ly"], capture_output=True, text=True)
        assert os.path.exists(base + ".png"), r.stderr[-800:]
        im = Image.open(base + ".png").convert("RGB"); bb = Image.eval(im.convert("L"), lambda v: 255 - v).getbbox()
        im.crop((0, max(0, bb[1] - 6), im.width, bb[3] + 6)).save(png)
    return png
def _lychord(sym, beats, bpb):
    m = re.match(r"^([A-G])(b|#)?(m)?(7)?$", sym)
    dur = {4.0: "1", 3.0: "2.", 2.0: "2", 1.0: "4"}[min(beats, float(bpb))]
    q = (":m7" if m.group(4) else ":m") if m.group(3) else (":7" if m.group(4) else "")
    return m.group(1).lower() + {"b": "es", "#": "is", None: ""}[m.group(2)] + dur + q

def last_bar_fix(t):
    """The chord under a short last bar lasts only as long as the bar."""
    bpb = bpb_of(t); bars = t["music"].split("|"); segs = chord_bars(t)
    assert len(segs) == len(bars), (t["title"], len(segs), len(bars))

def pitches(t):
    seen = []
    for tok in t["music"].replace("|", " ").split():
        m = BB.LTOK.match(BB.STRIP.sub("", tok))
        if m:
            p = m.group(1) + (m.group(2) or "") + m.group(3)
            if p not in seen: seen.append(p)
    import gen_study as g
    def midi(p):
        m = re.match(r"^([a-g])(is|es)?([',]*)$", p); return g.Note(m.group(1).upper(), {"is": 1, "es": -1, None: 0}[m.group(2)], 3 + m.group(3).count("'")).midi
    return sorted(seen, key=midi)

P_TIP = ParagraphStyle("tip", parent=B.body, fontSize=10.2, leading=14.6, spaceAfter=0)
P_BODY = ParagraphStyle("pb", parent=B.body, fontSize=10.6, leading=15.4, spaceAfter=7)
def footer(c, n):
    c.setStrokeColor(HexColor(RULE)); c.setLineWidth(0.6); c.line(M, 40, W - M, 40)
    c.setFont("Pop-M", 8.5); c.setFillColor(HexColor(SLATE)); c.drawString(M, 28, "Alex Attard Music")
    c.setFont("DJ", 7.4); c.setFillColor(HexColor(MUTED)); c.drawCentredString(W / 2, 28, BOOK_TITLE + "  ·  " + EDITION)
    c.setFont("Pop-B", 9); c.setFillColor(HexColor(AMBER)); c.drawRightString(W - M, 28, str(n))
def qr(c, slug, y=H - M):
    if not CODE: return
    qs = 62; qx = W - M - qs + 3; qy = y - qs + 6
    c.drawImage(BB.qr_img(slug), qx, qy, qs, qs)
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 5.8); c.drawCentredString(qx + qs / 2, qy - 5, " ".join("PLAY ALONG") + "  ·  " + CODE)
def star(c, x, y, r, col=AMBER):
    import math
    p = c.beginPath()
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.42
        (p.moveTo if k == 0 else p.lineTo)(x + rr * math.cos(a), y + rr * math.sin(a))
    p.close(); c.setFillColor(HexColor(col)); c.drawPath(p, fill=1, stroke=0)

def note_strip(c, y, notes):
    """The notes this tune uses, low to high: name, the note on the staff, the fingering."""
    n = len(notes); gap = 5; cw = min(62, (CW - gap * (n - 1)) / n); ch = 112
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 7.2); c.drawString(M, y - 8, " ".join("NOTES YOU NEED"))
    y -= 15
    for k, ly in enumerate(notes):
        x0 = M + k * (cw + gap)
        c.setFillColor(HexColor(TINT if k % 2 == 0 else "#F3F5F7")); c.roundRect(x0, y - ch, cw, ch, 6, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); name = NAMES[ly]; fs = 8.6 if len(name) < 8 else 7.0
        B._centred_mixed(c, x0 + cw / 2, y - 12, name, "Pop-B", fs) if hasattr(B, "_centred_mixed") else B.draw_mixed(c, x0 + 4, y - 12, name, "Pop-B", fs)
        im = ImageReader(BB.note_png(ly)); iw, ih = im.getSize(); tw = min(cw - 8, 40); th = tw * ih / iw
        if th > 36: th = 36; tw = th * iw / ih
        c.drawImage(im, x0 + (cw - tw) / 2, y - 17 - 36 + (36 - th) / 2, tw, th, mask="auto")
        top, bot = y - 56, y - ch + 5; u = (top - bot) / (FL.KY_MAX - FL.KY_MIN); dw = (FL.KX_MAX - FL.KX_MIN) * u
        FL.draw_keys(c, x0 + (cw - dw) / 2 - FL.KX_MIN * u, top, u, BB.FING[ly])
    return y - ch

def tune_page(c, t, n):
    y = B.header(c, "Tune %d of %d  ·  %s major" % (t["no"], len(TUNES), t["key"].upper()), t["title"])
    c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 9.4); c.drawString(M, y + 2, t["by"])
    qr(c, t["slug"])
    y = note_strip(c, y - 12, pitches(t)) - 12
    # the tip sits at the foot of the page; the music takes the largest staff size that fits between
    p = Paragraph("<font name='Pop-B' color='%s'>Practice tip.</font> %s" % (SLATE, t["tip"]), P_TIP); _, ph = p.wrap(CW - 30, 400)
    box_h = ph + 20; box_y = 54
    room = y - (box_y + box_h + 12)
    for size in (23, 22, 21, 20, 19, 18, 17, 16, 15, 14):
        png = render(tune_ly(t, size, 11)); iw, ih = Image.open(png).size; h = CW * 180 / 176 * ih / iw
        if h <= room: break
    for space in (40, 36, 32, 29, 26, 23, 21, 19, 17, 15, 13):                   # then open the lines up until the page is full
        png2 = render(tune_ly(t, size, space)); iw2, ih2 = Image.open(png2).size; h2 = CW * 180 / 176 * ih2 / iw2
        if h2 <= room: png, h = png2, h2; break
    c.drawImage(ImageReader(png), M - CW * 2 / 176, y - h - max(0, (room - h) * 0.35), CW * 180 / 176, h)
    c.setFillColor(HexColor(TINT)); c.roundRect(M, box_y, CW, box_h, 8, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.rect(M, box_y, 4, box_h, fill=1, stroke=0)
    p.drawOn(c, M + 16, box_y + 10)
    footer(c, n); c.showPage()
    return size, round(100 * h / room)

def cover(c):
    band = H * 0.58
    c.setFillColor(HexColor(SLATE)); c.rect(0, H - band, W, band, fill=1, stroke=0)
    for x, y, r in [(330, H - 70, 7), (392, H - 120, 4), (300, H - 150, 3.2), (470, H - 60, 4.5), (540, H - 150, 3), (250, H - 60, 3), (575, H - 90, 5.5), (430, H - 190, 2.6)]: star(c, x, y, r, "#E7C378")
    png, clef = B.cover_staff_png(); im = ImageReader(png); iw, ih = im.getSize(); sw = 290
    c.drawImage(im, M, H - band + 48, sw, sw * ih / iw, mask="auto")
    FL.draw_flute(c, 345, H - band + 36, 1.95)
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 11); c.drawString(M, H - 110, " ".join("ALEX ATTARD MUSIC"))
    c.setFillColor(white); c.setFont("Pop-B", 50); c.drawString(M, H - 198, "Christmas")
    c.setFont("Pop-L", 38); c.drawString(M, H - 244, "Tunes for Flute")
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-M", 17); c.drawString(M, H - 284, "Eight carols for beginners")
    top, bot = H - band - 44, 92
    c.setFillColor(HexColor(TINT)); c.roundRect(M, bot, CW, top - bot, 10, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.rect(M, bot, 5, top - bot, fill=1, stroke=0)
    y = top - 46
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 20); c.drawString(M + 30, y, "Play something everyone knows.")
    p = Paragraph("Eight Christmas tunes, easiest first, written with the notes you already know. Each page shows the fingerings you need, "
                  "and a piano plays along with you in the practice app. Learn one, then play it for your family.",
                  ParagraphStyle("cv", parent=B.body, fontSize=11.8 if CODE else 13, leading=18 if CODE else 20))
    _, ph = p.wrap(CW - 60 - (150 if CODE else 0), 400); p.drawOn(c, M + 30, y - 18 - ph)
    if CODE:
        qs = 104; qx = W - M - 24 - qs; qy = (top + bot) / 2 - qs / 2 + 30
        c.setFillColor(white); c.roundRect(qx - 6, qy - 6, qs + 12, qs + 12, 8, fill=1, stroke=0)
        c.drawImage(BB.qr_img(TUNES[0]["slug"]), qx, qy, qs, qs)
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 8.5); c.drawCentredString(qx + qs / 2, qy - 22, " ".join("PLAY ALONG"))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 15); c.drawCentredString(qx + qs / 2, qy - 41, CODE)
        c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 7.4); c.drawCentredString(qx + qs / 2, qy - 55, "Scan, or type this code at"); c.drawCentredString(qx + qs / 2, qy - 65, "alexattardmusic.com/play")
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 14); c.drawString(M + 30, y - 18 - ph - 28, "Alex")
    c.setFillColor(HexColor(AMBER)); c.rect(0, 0, W, 6, fill=1, stroke=0)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 11); c.drawString(M, 40, "Alex Attard Music")
    c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 10); c.drawRightString(W - M, 40, "alexattardmusic.com")
    c.showPage()

def inside_page(c, n):
    y = B.header(c, "Start here", "What's Inside")
    row = 37
    for k, t in enumerate(TUNES):
        top = y - k * row; mid = top - row / 2
        c.setFillColor(HexColor(AMBER)); c.roundRect(M, mid - 12, 24, 24, 6, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 12); c.drawCentredString(M + 12, mid - 4.3, str(t["no"]))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 12.5); c.drawString(M + 38, mid + 2, t["title"])
        tw = B.pdfmetrics.stringWidth(t["title"], "Pop-B", 12.5)
        ps = pitches(t); kn = t["key"].upper() if len(t["key"]) == 1 else t["key"][0].upper() + "♭"
        c.setFillColor(HexColor(MUTED))
        B.draw_mixed(c, M + 38, mid - 11.5, "%s major  ·  %d notes, from %s to %s  ·  %s time" % (kn, len(ps), NAMES[ps[0]], NAMES[ps[-1]], t["time"]), "DJ", 8.8)
        c.setStrokeColor(HexColor(RULE)); c.setLineWidth(1.1); c.setDash(1, 3); c.line(M + 38 + tw + 8, mid + 4, W - M - 28, mid + 4); c.setDash()
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 13); c.drawRightString(W - M, mid + 1, str(t["page"]))
    y -= len(TUNES) * row + 14
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y, "How to learn a tune"); y -= 10
    steps = ["<b>Check the notes.</b> The strip at the top of each page shows every note the tune uses. Finger each one before you play.",
             "<b>Clap and say it.</b> Clap the rhythm, then say the note names in time.",
             "<b>Play four bars at a time,</b> slowly. Only join them up when each four is easy.",
             "<b>Play along.</b> Scan the code on the page. Start at the slow tempo, then move up. Switch off Flute and the piano plays alone, so the tune is all yours."
             if True else ""]
    st = ParagraphStyle("st", parent=P_BODY, leftIndent=24, spaceAfter=6)
    for k, s in enumerate(steps):
        p = Paragraph(s, st); _, ph = p.wrap(CW, 400); y -= ph + 6; p.drawOn(c, M, y)
        c.setFillColor(HexColor(SLATE)); c.circle(M + 9, y + ph - 8, 8, fill=1, stroke=0); c.setFillColor(white); c.setFont("Pop-B", 9); c.drawCentredString(M + 9, y + ph - 11.2, str(k + 1))
    y -= 12
    y = B.tip_box(c, M, y, CW, "For a parent or teacher", [
        "The letters above the staff are chords. Play them on piano or guitar and you have a duet.",
        "In the practice app, <b>Learn the notes</b> listens to the flute and waits for each right note. The tuner shows the fingering of the note being played.",
        "All eight tunes are traditional or long out of copyright. The easy keys and rhythms are written for this book."])
    footer(c, n); c.showPage()

def chart_page(c, n):
    y = B.header(c, "Reference", "Fingering chart: the notes in this book")
    notes = []
    for t in TUNES:
        for p in pitches(t):
            if p not in notes: notes.append(p)
    import gen_study as g
    notes = sorted(notes, key=lambda p: (lambda m: g.Note(m.group(1).upper(), {"is": 1, "es": -1, None: 0}[m.group(2)], 3 + m.group(3).count("'")).midi)(re.match(r"^([a-g])(is|es)?([',]*)$", p)))
    cols = 4; rows = -(-len(notes) // cols); gap = 9; gw = (CW - (cols - 1) * gap) / cols; gh = min(150, (y - 60 - (rows - 1) * gap) / rows)
    for k, ly in enumerate(notes):
        col, row = k % cols, k // cols; x0 = M + col * (gw + gap); y1 = y - row * (gh + gap)
        c.setFillColor(HexColor(TINT if (row + col) % 2 == 0 else "#F3F5F7")); c.roundRect(x0, y1 - gh, gw, gh, 8, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, x0 + 10, y1 - 19, NAMES[ly], "Pop-B", 12)
        top, bot = y1 - 12, y1 - gh + 10; u = (top - bot) / (FL.KY_MAX - FL.KY_MIN); dw = (FL.KX_MAX - FL.KX_MIN) * u; right = x0 + gw - 10
        FL.draw_keys(c, right - dw - FL.KX_MIN * u, top, u, BB.FING[ly])
        im = ImageReader(BB.note_png(ly)); iw, ih = im.getSize(); tw = right - dw - 8 - (x0 + 6); th = tw * ih / iw
        c.drawImage(im, x0 + 6, (top + bot) / 2 - th / 2 - 6, tw, th, mask="auto")
    footer(c, n); c.showPage()

def main():
    for k, t in enumerate(TUNES): t["page"] = 3 + k; last_bar_fix(t); to_tune(t)          # every tune must parse before anything is drawn
    out = os.path.join(B.OUT, "Flute_Christmas_Tunes.pdf")
    c = canvas.Canvas(out, pagesize=letter); c.setTitle(BOOK_TITLE); c.setAuthor("Alex Attard Music")
    cover(c); inside_page(c, 2)
    for t in TUNES:
        size, pct = tune_page(c, t, t["page"]); print("  page %2d  %-32s staff %s, fills %d%%, %d notes" % (t["page"], t["title"], size, pct, len(pitches(t))))
    chart_page(c, 3 + len(TUNES)); c.save()
    print(out, 3 + len(TUNES), "pages")
    if REPO:
        assert CODE, "give --code with --publish"
        publish(REPO)
        if os.environ.get("AAM_CODE"):
            import publish_pdf; publish_pdf.publish_pdf(out, BOOK_ID, CODE, EDITION, repo=REPO)
        else: print("AAM_CODE not set: the PDF in the player was NOT updated")

if __name__ == "__main__":
    main()
