#!/usr/bin/env python3
"""Flute data for the Beginner Booklet (tools/build_beginner.py flute).

The flute book is the saxophone book's curriculum, line for line: the flute reads the same written notes in the same range, and
the order B A G, then C and D, then the right hand, suits it as well. What differs lives here, as data:

  KEYS, FINGERINGS, draw_keys, key_map, fingering_pages   the flute's own fingering diagram and chart (low C to upper C)
  draw_flute                                               the cover drawing
  NOTE_TIPS, BOXES, SUBS, CHECKS, patch(UNITS)             the words that talk about fingers, air and the instrument
  START, CARE                                              the Getting started page

Every fingering here is the standard Boehm-flute fingering. Alex checks the chart before a student sees it.
"""
import os, re, subprocess
import build_book as B
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
from PIL import Image

W, H, M = B.W, B.H, B.M
SLATE, AMBER, TINT, MUTED = B.SLATE, B.AMBER, B.TINT, B.MUTED

# ---------------------------------------------------------------- the key diagram
# The flute held out in front of you, mouth end at the top: the six main fingers down the middle, the left thumb's two keys on
# the left, the pinky keys on the right. Same box as the saxophone diagram, so both fit the same cards.
# (id, shape, x, y, a, b, main?)  c=circle(r=a)  e=ellipse(rx=a, ry=b)  r=rounded rect(w=a, h=b)
KEYS = [
    ("Tb", "r", -1.55, 1.0, 0.9, 0.5, False),            # the thumb's B flat lever
    ("T", "e", -1.55, 2.15, 0.5, 0.62, False),           # the thumb's B key
    ("L1", "c", 0, 1.2, 0.66, 0, True),
    ("L2", "c", 0, 3.1, 0.66, 0, True),
    ("L3", "c", 0, 5.0, 0.66, 0, True),
    ("Gs", "r", 1.65, 5.75, 1.1, 0.5, False),            # left pinky
    ("R1", "c", 0, 7.8, 0.66, 0, True),
    ("R2", "c", 0, 9.7, 0.66, 0, True),
    ("R3", "c", 0, 11.6, 0.66, 0, True),
    ("Eb", "r", 1.65, 12.2, 1.1, 0.5, False),            # right pinky: its home key
    ("Cs", "r", 1.33, 12.95, 0.55, 0.5, False),          # right pinky: the two keys on the footjoint
    ("C", "r", 1.97, 12.95, 0.55, 0.5, False),
]
KY_MIN, KY_MAX, KX_MIN, KX_MAX = -0.95, 13.35, -2.1, 2.5

def draw_keys(c, cx, ytop, u, pressed, legend=False):
    """Draw the flute key diagram. cx = x of the main column, ytop = top edge."""
    def P(x, y): return cx + x * u, ytop - (y - KY_MIN) * u
    c.setStrokeColor(HexColor(MUTED)); c.setLineWidth(0.6)
    x1, y1 = P(-1.0, 6.4); x2, _ = P(1.0, 6.4); c.line(x1, y1, x2, y1)             # the line between the hands
    pos = {}
    for kid, shape, x, y, a, b, main in KEYS:
        X, Y = P(x, y); pos[kid] = (X, Y, a, b, shape); on = kid in pressed
        fill = (HexColor(SLATE) if main else HexColor(AMBER)) if (on or legend) else white
        c.setFillColor(fill); c.setStrokeColor(HexColor(SLATE) if main else HexColor("#8A6A3A")); c.setLineWidth(0.9 if main else 0.7)
        if shape == "c": c.circle(X, Y, a * u, fill=1, stroke=1)
        elif shape == "e": c.ellipse(X - a * u, Y - b * u, X + a * u, Y + b * u, fill=1, stroke=1)
        else: c.roundRect(X - a * u / 2, Y - b * u / 2, a * u, b * u, min(a, b) * u * 0.45, fill=1, stroke=1)
    return pos

T = {"T"}; LH3 = {"L1", "L2", "L3"}; RH3 = {"R1", "R2", "R3"}; E = {"Eb"}
# (lilypond notes, name, keys pressed, note line)
FINGERINGS = [
    ("c'", "Low C", T | LH3 | RH3 | {"Cs", "C"}, "RH pinky: both low keys"),
    ("cis' des'", "Low C♯ / D♭", T | LH3 | RH3 | {"Cs"}, "RH pinky: low C♯ key"),
    ("d'", "Low D", T | LH3 | RH3, "RH pinky up"),
    ("dis' ees'", "Low D♯ / E♭", T | LH3 | RH3 | E, ""),
    ("e'", "E", T | LH3 | {"R1", "R2"} | E, ""),
    ("f'", "F", T | LH3 | {"R1"} | E, ""),
    ("fis' ges'", "F♯ / G♭", T | LH3 | {"R3"} | E, "RH ring finger"),
    ("g'", "G", T | LH3 | E, ""),
    ("gis' aes'", "G♯ / A♭", T | LH3 | {"Gs"} | E, "LH pinky: G♯ key"),
    ("a'", "A", T | {"L1", "L2"} | E, ""),
    ("ais' bes'", "A♯ / B♭", T | {"L1", "R1"} | E, "B plus RH index"),
    ("b'", "B", T | {"L1"} | E, ""),
    ("c''", "C", {"L1"} | E, "Thumb off"),
    ("cis'' des''", "C♯ / D♭", set(E), "Only the RH pinky"),
    ("d''", "Upper D", T | {"L2", "L3"} | RH3, "LH index up, pinky up"),
    ("dis'' ees''", "Upper D♯ / E♭", T | {"L2", "L3"} | RH3 | E, "LH index up"),
    ("e''", "Upper E", T | LH3 | {"R1", "R2"} | E, ""),
    ("f''", "Upper F", T | LH3 | {"R1"} | E, ""),
    ("fis'' ges''", "Upper F♯ / G♭", T | LH3 | {"R3"} | E, "RH ring finger"),
    ("g''", "Upper G", T | LH3 | E, ""),
    ("gis'' aes''", "Upper G♯ / A♭", T | LH3 | {"Gs"} | E, "LH pinky: G♯ key"),
    ("a''", "Upper A", T | {"L1", "L2"} | E, ""),
    ("ais'' bes''", "Upper A♯ / B♭", T | {"L1", "R1"} | E, "B plus RH index"),
    ("b''", "Upper B", T | {"L1"} | E, ""),
    ("c'''", "Upper C", {"L1"} | E, "Thumb off"),
    ("cis''' des'''", "Upper C♯ / D♭", set(E), "Only the RH pinky"),
]
# a second fingering shown on its own card, straight after the note it belongs to
EXTRA = {"ais' bes'": ("B♭ with the thumb", {"Tb", "T", "L1"} | E, "Thumb on its B♭ lever")}

KEY_LABELS_LEFT = [("Tb", 0.7, "Thumb B♭ lever"), ("T", 2.5, "Left thumb (B key)")]
KEY_LABELS_RIGHT = [("L1", 1.2, "1 · left index"), ("L2", 3.1, "2 · left middle"), ("L3", 4.7, "3 · left ring"), ("Gs", 5.9, "G♯ key (left pinky)"),
                    ("R1", 7.8, "1 · right index"), ("R2", 9.5, "2 · right middle"), ("R3", 10.9, "3 · right ring"),
                    ("Eb", 12.0, "E♭ key (right pinky)"), ("C", 13.1, "Low C♯ and low C keys")]

def key_map(c, x0, ytop, w, h):
    """Panel with a labelled key diagram on the left and how-to-read notes on the right."""
    body, bullet = B.body, B.bullet
    c.setFillColor(HexColor("#F3F5F7")); c.roundRect(x0, ytop - h, w, h, 8, fill=1, stroke=0)
    u = (h - 16) / (KY_MAX - KY_MIN); cx = x0 + 104 + (-KX_MIN) * u
    pos = draw_keys(c, cx, ytop - 8, u, set(), legend=True)
    for n, kid in [("1", "L1"), ("2", "L2"), ("3", "L3"), ("1", "R1"), ("2", "R2"), ("3", "R3")]:
        X, Y, *_ = pos[kid]; c.setFillColor(white); c.setFont("Pop-B", 6.5); c.drawCentredString(X, Y - 2.3, n)
    def ly(y): return ytop - 8 - (y - KY_MIN) * u
    lx = cx + KX_MIN * u - 8; rx = cx + KX_MAX * u + 8
    c.setLineWidth(0.4); c.setStrokeColor(HexColor(MUTED))
    for kid, y, txt in KEY_LABELS_LEFT:
        X, Y, a, b, shape = pos[kid]; edge = X - (a * u if shape != "r" else a * u / 2)
        c.line(lx + 2, ly(y) + 2.2, edge - 1, Y); c.setFillColor(HexColor(SLATE)); c.setFont("DJ", 6.6); c.drawRightString(lx, ly(y), txt)
    for kid, y, txt in KEY_LABELS_RIGHT:
        X, Y, a, b, shape = pos[kid]; edge = X + (a * u if shape != "r" else a * u / 2)
        c.line(edge + 1, Y, rx - 2, ly(y) + 2.2); c.setFillColor(HexColor(SLATE)); c.setFont("DJ", 6.6); c.drawString(rx, ly(y), txt)
    tx = x0 + 292
    items = [Paragraph(f"<font name='Pop-B' size='11.5' color='{SLATE}'>How to read the chart</font>", ParagraphStyle("kt", parent=body, spaceAfter=5))]
    small = ParagraphStyle("ks", parent=bullet, fontSize=8.5, leading=11, spaceAfter=3)
    for t in [f"Mouth end at the top. <font color='{SLATE}'><b>Dark keys</b></font>: left hand 1-2-3, then right hand 1-2-3. "
              f"<font color='{AMBER}'><b>Amber keys</b></font>: the left thumb and the pinkies.",
              "<b>Filled = press it.</b> Hollow = leave it open.",
              "<b>Your right pinky</b> stays on its E♭ key for almost every note. It lifts for D.",
              "<b>From upper E</b> the low fingerings repeat, with faster air."]:
        items.append(Paragraph(t, small, bulletText="•"))
    Frame(tx, ytop - h + 6, x0 + w - tx - 12, h - 18, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0).addFromList(items, c)

def _note_png(ly, tag):
    d = B.OUT + "/notes_flute"; os.makedirs(d, exist_ok=True); p = "%s/%s" % (d, tag)
    if not os.path.exists(p + ".t.png"):
        notes = " \\noBreak ".join(n + "1" for n in ly.split())
        src = ('\\version "2.24.0"\n\\paper { indent = 0 line-width = 27\\mm ragged-right = ##f tagline = ##f }\n'
               '\\layout { \\context { \\Staff \\remove Time_signature_engraver } \\context { \\Score \\override SpacingSpanner.shortest-duration-space = #1.0 } }\n'
               '{ \\clef treble \\accidentalStyle forget ' + notes + ' }\n')
        open(p + ".ly", "w").write(src)
        subprocess.run(["lilypond", "-s", "--png", "-dresolution=300", "-dcrop", "-o", p, p + ".ly"], check=True)
        g = Image.open(p + ".cropped.png").convert("L"); out = Image.new("RGBA", g.size, (0, 0, 0, 0)); out.putalpha(g.point(lambda v: 255 - v)); out.save(p + ".t.png")
    return p + ".t.png"

def fingering_pages(path):
    """The complete chart at the back of the book: low C to upper C sharp, two pages of sixteen cards (the first row of page one is the key map)."""
    cards = []
    for i, (ly, name, pressed, note) in enumerate(FINGERINGS):
        cards.append((ly, name, pressed, note, "n%d" % i))
        if ly in EXTRA: nm, pr, nt = EXTRA[ly]; cards.append(("bes'", nm, pr, nt, "x%d" % i))
    cards.append(None)                                               # the closing tip card
    c = canvas.Canvas(path, pagesize=letter); cols, rows, gap = 4, 4, 9; gw = (W - 2 * M - (cols - 1) * gap) / cols; idx = 0
    for page, (maprows, ncards) in enumerate([(1, 12), (0, 16)]):
        y = B.header(c, "Reference", "Fingering Chart" + ("" if page == 0 else " (continued)")); gh = (y - 60 - (rows - 1) * gap) / rows
        if maprows: key_map(c, M, y, W - 2 * M, gh)
        for k in range(ncards):
            if idx >= len(cards): break
            col, row = k % cols, k // cols + maprows; x0 = M + col * (gw + gap); y1 = y - row * (gh + gap)
            c.setFillColor(HexColor(TINT if (row + col) % 2 == 0 else "#F3F5F7")); c.roundRect(x0, y1 - gh, gw, gh, 8, fill=1, stroke=0)
            card = cards[idx]; idx += 1
            if card is None:
                c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 10.5); c.drawString(x0 + 10, y1 - 18, "Good to know")
                st = ParagraphStyle("tip", parent=B.body, fontSize=7.8, leading=10.2, spaceAfter=3)
                tip = [Paragraph("<b>B♭ has two fingerings.</b> Learn B plus the right index finger first. Your teacher will show you when the thumb lever is better.", st),
                       Paragraph("<b>Upper D and E♭</b> lift the left index finger.", st)]
                Frame(x0 + 10, y1 - gh + 6, gw - 20, gh - 30, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0).addFromList(tip, c); continue
            ly, name, pressed, note, tag = card
            c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, x0 + 10, y1 - 17, name, "Pop-B", 9.6 if len(name) > 12 else 10.5)
            top, bot = y1 - 25, y1 - gh + 17; u = (top - bot) / (KY_MAX - KY_MIN); dw = (KX_MAX - KX_MIN) * u; right = x0 + gw - 8
            draw_keys(c, right - dw - KX_MIN * u, top, u, pressed)
            im = ImageReader(_note_png(ly, tag)); iw, ih = im.getSize(); tw = right - dw - 4 - (x0 + 6); th = tw * ih / iw
            c.drawImage(im, x0 + 6, (top + bot) / 2 - th / 2, tw, th, mask="auto")
            if note: c.setFillColor(HexColor("#A86F14")); B.draw_mixed(c, x0 + 10, y1 - gh + 7, note, "Pop-M", 7.2)
        c.showPage()
    c.save()

# ---------------------------------------------------------------- the cover drawing (original illustration)
def draw_flute(c, ox, oy, s):
    """A stylised flute lying across a 100 x 200 unit box from bottom left to top right; (ox, oy) = bottom-left corner, s = points per unit."""
    import math
    silver, edge, dark = "#E6EAEE", "#9AA5B1", "#5C6875"
    L, wd = 216.0, 7.0; ang = math.degrees(math.atan2(196, 92))
    c.saveState(); c.translate(ox + 4 * s, oy + 2 * s); c.rotate(ang); c.scale(s, s)
    def tube(x0, x1, w=wd, r=2.2):
        c.setFillColor(HexColor(silver)); c.setStrokeColor(HexColor(edge)); c.setLineWidth(0.5); c.roundRect(x0, -w / 2, x1 - x0, w, r, fill=1, stroke=1)
    tube(0, 34); tube(34, 150); tube(150, L)                          # footjoint, body, headjoint (the crown is at the far end)
    for x in (34, 150):                                               # the rings where the joints meet
        c.setFillColor(HexColor(AMBER)); c.rect(x - 1.6, -wd / 2 - 0.9, 3.2, wd + 1.8, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.roundRect(L - 4, -wd / 2 - 0.6, 5, wd + 1.2, 1.4, fill=1, stroke=0)   # crown
    c.setFillColor(HexColor(silver)); c.setStrokeColor(HexColor(edge)); c.ellipse(170, -6.2, 190, 6.2, fill=1, stroke=1)     # lip plate
    c.setFillColor(HexColor(dark)); c.ellipse(176.5, -2.6, 183.5, 2.6, fill=1, stroke=0)                                    # the hole you blow across
    c.setStrokeColor(HexColor(edge)); c.setLineWidth(0.9); c.line(8, wd / 2 + 2.2, 146, wd / 2 + 2.2)                         # the rod
    def cup(x, r=4.6, pearl=True):
        c.setFillColor(HexColor(dark)); c.circle(x, 0, r, fill=1, stroke=0)
        c.setFillColor(HexColor(TINT if pearl else silver)); c.circle(x, 0, r - 1.3, fill=1, stroke=0)
    for x in (10, 19, 28): cup(x, 4.2, False)                         # footjoint keys
    for x in (46, 57, 68): cup(x)                                     # right hand
    cup(79, 3.8, False)
    for x in (91, 102, 113): cup(x)                                   # left hand
    for x in (124, 133): cup(x, 3.6, False)
    for x in (51.5, 62.5):                                            # the two trill keys
        c.setFillColor(HexColor(AMBER)); c.roundRect(x - 1.2, wd / 2 + 1.2, 2.4, 4.4, 1, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.roundRect(84, -wd / 2 - 5.2, 8, 3.2, 1.2, fill=1, stroke=0)          # the G sharp lever
    c.roundRect(30, -wd / 2 - 4.6, 7, 3.2, 1.2, fill=1, stroke=0)                                           # the E flat key
    c.restoreState()

# ---------------------------------------------------------------- the words that differ from the saxophone book
NOTE_TIPS = {"b'": "Left thumb and left index finger. Right pinky on its key.", "a'": "Add your left middle finger.", "g'": "Add your left ring finger.",
             "c''": "Left index finger only. Lift your thumb.", "d''": "Lift your left index finger and your right pinky. Every other finger is down.",
             "f'": "Left hand stays down. Add your right index finger.", "e'": "Add your right middle finger.", "d'": "Add your right ring finger and lift your pinky.",
             "fis'": "Like F, but use your right RING finger instead of the index.",
             "e''": "The same fingers as low E. Faster air.", "fis''": "The same fingers as low F♯. Faster air.", "g''": "The same fingers as low G. Faster air.",
             "bes'": "The B fingering plus your right index finger.", "f''": "The same fingers as low F. Faster air.",
             "c'": "Low D, then your right pinky presses the two keys at the end of the flute.",
             "cis''": "Only your right pinky is down. Lift your thumb as well.",
             "a''": "The same fingers as low A. Faster air.", "b''": "The same fingers as low B. Faster air.", "c'''": "The same finger as middle C: left index only."}
# (unit, the saxophone box's title) -> the flute box (kind, title, text)
BOXES = {
    (1, "Tonguing"): ("skill", "Tonguing", "Start every note with the tip of your tongue behind your top teeth, as if saying \"too\". The air keeps flowing: only the tongue moves."),
    (2, "Octave key"): ("skill", "Three balance points", "For C your left thumb comes off. The flute rests on three points: your chin, the base of your left index finger and your right thumb."),
    (2, "Breath mark"): ("word", "Breath mark", "A comma above the staff shows a good place to breathe. Breathe in quickly through your mouth and keep the flute still."),
    (3, "Low notes"): ("skill", "Low notes", "Low notes need warm, slow air aimed a little more down into the flute. Keep your lips loose, as if you were fogging up a window."),
    (5, "High notes"): ("skill", "High notes", "The fingers stay the same: the air makes the octave. Blow faster air through a smaller opening in your lips. Never squeeze them tight."),
    (7, "Quiet fingers"): ("skill", "Quiet fingers", "Keep your fingers close to the keys. Let your right pinky slide from its key to the two low keys: don't lift the hand."),
    (8, "Open C sharp"): ("skill", "Open C sharp", "With almost no fingers down the flute can wobble. Balance it on your three points and keep your right pinky on its key."),
    (9, "The upper register"): ("skill", "The upper register", "Fast, steady air through a small opening in your lips. If a high note sounds thin or sharp, relax your lips and blow more air: never pinch."),
}
# (unit, line title) -> the words under the title
SUBS = {
    (2, "Long tones: C and D"): "Thumb off for C. For D, lift your left index finger.",
    (2, "B to C"): "Only your thumb lifts. Keep the flute steady.",
    (3, "Long tones: F, E and low D"): "Warm, slow air, aimed down a little for low notes.",
    (3, "Two Ds"): "Low D: left index down. Upper D: left index up and faster air.",
    (4, "F sharp ladder"): "Ring finger every time.",
    (5, "Octaves"): "Same fingers. Faster air through a smaller opening for the high note.",
    (5, "Crossing to upper E"): "Left index goes down, right ring finger lifts.",
    (6, "Long tones: B flat and upper F"): "B plus your right index finger makes B flat.",
    (7, "Long tone: low C"): "Slow, warm air. Press both pinky keys firmly.",
    (8, "B, C sharp, D"): "From almost no fingers to almost all of them.",
    (9, "Long tones: A, B and C"): "Fast air. Keep your lips relaxed.",
    (9, "Octaves again"): "Same fingers. Only the air changes.",
}
CHECKS = {"I use my middle finger for F♯ every time.": "I use my ring finger for F♯ every time.", "My high notes start cleanly, without biting.": "My high notes start cleanly, without squeezing my lips.",
          "I press B and the bis key with one finger.": "I add my right index finger for B♭ every time.", "I can play C♯ in tune with nothing to hold on to.": "I can play C♯ without the flute wobbling.",
          "My low D speaks without a squeak or a gurgle.": "My low D speaks clearly and does not jump up to the higher D."}
WORDS = ("sax", "octave key", "reed", "strap", "mouthpiece", "bis key", "jaw", "bite", "biting", "only the thumb", "thumb stays")     # none of these may be left in a flute book

def patch(units):
    """Turn the saxophone curriculum into the flute's: same music, the flute's own words. Refuses to leave a saxophone word behind."""
    done = set()
    for k, u in enumerate(units, 1):
        u["notes"] = [(ly, name, NOTE_TIPS[ly]) for ly, name, tip in u["notes"]]
        for i, (kind, title, text) in enumerate(u["boxes"]):
            if (k, title) in BOXES: u["boxes"][i] = BOXES[(k, title)]; done.add((k, title))
        for it in u["lines"]:
            if it["type"] == "line" and (k, it["title"]) in SUBS: it["sub"] = SUBS[(k, it["title"])]; done.add((k, it["title"]))
            if it["type"] == "check": it["items"] = [CHECKS.get(x, x) for x in it["items"]]
    missing = (set(BOXES) | set(SUBS)) - done; assert not missing, "the flute words name lines or boxes that are not in the book: %s" % sorted(missing)
    for k, u in enumerate(units, 1):
        texts = [t for n in u["notes"] for t in n[1:]] + [t for b in u["boxes"] for t in b[1:]]
        for it in u["lines"]: texts += [it.get("title") or "", it.get("sub") or "", it.get("about") or "", it.get("text") or ""] + list(it.get("items") or [])
        for t in texts:
            bad = [w for w in WORDS if re.search(r"\b" + w, t.lower())]; assert not bad, "Unit %d still has a saxophone word (%s): %r" % (k, bad[0], t)

START = [("Put it together", ["The flute has three parts: the headjoint, the body and the footjoint. Hold each one where there are no keys.",
                              "Twist the headjoint gently into the body. Line up the hole you blow across with the first key on the body.",
                              "Twist the footjoint on. Its rod lines up with the middle of the last key on the body.",
                              "Never squeeze the keys or the rods while you twist."]),
         ("Hold it", ["Sit or stand tall and keep your head level. Bring the flute up to you.", "The flute points to your right and slopes down a little.",
                      "Left hand nearest your mouth, palm facing you. The flute rests on the base of your left index finger, and your left thumb sits on its long key.",
                      "Right hand palm facing away. Right thumb under the flute, below your index finger. Right pinky on its key.",
                      "Curve your fingers and rest the pads on the middle of the keys."]),
         ("Make a sound", ["Start with the headjoint alone. Rest the lip plate in the dip under your bottom lip, with the hole in line with the middle of your lips.",
                           "Your bottom lip covers about a quarter of the hole.",
                           "Make a small opening in your lips, as if saying \"pooh\", and blow a thin, fast stream of air across the hole, like blowing across the top of a bottle.",
                           "Roll the headjoint a little toward you or away until the sound is clear.",
                           "Start the note with your tongue: \"too\". Aim for four steady beats. If you feel dizzy, sit down and rest for a minute."])]
CARE = ["Push a soft cloth through each part with the cleaning rod after every session.", "Wipe the fingerprints off the outside with a dry cloth.", "Keep the flute in its case: never on a chair, a bed or a music stand."]
