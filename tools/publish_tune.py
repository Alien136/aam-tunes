"""Publish a chord & scale study to the play-along tune folder (the aam-tunes repository).

Usage: python3 publish_tune.py spec.json /path/to/aam-tunes --slug winter-wonderland-alto --code WA-1234
                               [--subtitle "..."] [--pdf-title "..."] [--tempo 132] [--first-bar 1]
Writes tunes/<slug>.json (format aam-tune/1) and adds the PDF and tune to index.json. Then commit and push the repository.
Needs gen_study.py in the same folder.

Works for every instrument gen_study knows. Piano gets a grand staff in concert pitch. Woodwinds and trumpet get a single
treble staff in WRITTEN pitch with written chord names (what the student's PDF shows), while the band and the "Hear it"
notes sound in concert pitch.
"""
import argparse, json, os, re, hashlib
import gen_study as g

ap = argparse.ArgumentParser()
ap.add_argument("spec"); ap.add_argument("repo"); ap.add_argument("--slug", required=True); ap.add_argument("--code", required=True)
ap.add_argument("--subtitle"); ap.add_argument("--pdf-title"); ap.add_argument("--tempo", type=int, default=132); ap.add_argument("--first-bar", type=int, default=1)
A = ap.parse_args()
spec = json.load(open(A.spec))
INST = spec.get("instrument", "alto")
PIANO = INST == "piano"
STEPS, SEMIS, _ = g.INSTRUMENTS[INST]                       # concert -> written, as the PDF is written
# how far the written note sits above the note that sounds (tenor and bari sound an octave lower than gen_study's interval)
SOUNDS_BELOW = {"alto": 9, "bari": 21, "tenor": 14, "soprano": 2, "clarinet": 2, "trumpet": 2, "flute": 0, "concert": 0, "piano": 0}[INST]
SHORT = {"alto": "Alto Sax", "bari": "Bari Sax", "tenor": "Tenor Sax", "soprano": "Soprano Sax", "clarinet": "Clarinet", "trumpet": "Trumpet",
         "flute": "Flute", "concert": "Concert Pitch", "piano": "Piano"}[INST]
g.build(dict(spec)); L = g.LAST
SLUG = A.slug

ck = spec["concert_key"]; minor = ck.endswith("m"); kn = g.parse_note(ck.rstrip("m"))
wk = g.transpose(kn, STEPS, SEMIS)                          # the written key
ascii_name = lambda n: n.letter + ("#" * n.acc if n.acc > 0 else "b" * -n.acc)
major_pc = (wk.pc + 3) % 12 if minor else wk.pc             # key signature = the relative major's
NSHARP = {0: 0, 7: 1, 2: 2, 9: 3, 4: 4, 11: 5, 5: -1, 10: -2, 3: -3, 8: -4, 1: -5, 6: -6}[major_pc]
KEYSIG = {l: 1 for l in "FCGDAEB"[:max(NSHARP, 0)]}; KEYSIG.update({l: -1 for l in "BEADGCF"[:max(-NSHARP, 0)]})

NOTE = re.compile(r"^(GREY:)?([a-g])((?:is|es)*)([',]*)(\d+)?$")
DUR = {"8": .5, "4": 1.0, "2": 2.0, "1": 4.0}


def clean(s):
    s = re.sub(r'\\mark \\markup \\box \\bold "[^"]*"', "", s).replace('\\bar "||"', "").replace("|", " ")
    s = re.sub(r'[\^_]\\markup \\abs-fontsize #\d+ (?:\\bold |\\italic )*(?:\\with-color #\(rgb-color [^)]*\) )?"[^"]*"', "", s)   # the Sample Solo's printed labels (3, 7, "arpeggio notes")
    return s.replace("\\tweak color #grey \\tweak Accidental.color #grey ", "GREY:")


def note_of(m):
    acc = (len(m.group(3)) // 2) * (1 if "is" in m.group(3) else -1)
    return g.Note(m.group(2).upper(), acc, 3 + m.group(4).count("'") - m.group(4).count(","))


def parse_rh(bar):
    """One bar of gen_study's right-hand LilyPond -> notes and rests. Handles the \\transpose c' X { ... } that wraps woodwind licks."""
    out, lick, dur, tr, guide = [], False, None, None, False
    toks = clean(bar).split(); i = 0
    while i < len(toks):
        tok = toks[i]; i += 1
        if tok == "\\lickOn": lick = True; continue
        if tok == "\\lickOff": lick = False; continue
        if tok == "\\guideOn": guide = True; continue                                  # the Sample Solo's guide tones (blue)
        if tok == "\\guideOff": guide = False; continue
        if tok == "\\transpose":
            to = note_of(NOTE.match(toks[i + 1])); i += 3                              # skip: c'  X  {
            tr = (g.LETTERS.index(to.letter) + 7 * (to.octave - 4), to.midi - 60); continue
        if tok == "}": tr = None; continue
        m = re.match(r"^r(\d+)$", tok)
        if m: out.append(dict(rest=True, dur=DUR[m.group(1)])); continue
        m = NOTE.match(tok); assert m, (tok, bar)
        if m.group(5): dur = m.group(5)
        n = note_of(m)
        if tr: n = g.transpose(n, tr[0], tr[1])
        out.append(dict(n=n, dur=DUR[dur], mark="l" if lick else "t" if guide else ("g" if m.group(1) else ".")))
    assert abs(sum(x["dur"] for x in out) - 4) < 1e-9, bar
    return out


def parse_lh(bar):
    out = []
    for m in re.finditer(r"<([^>]*)>(\d)", bar):
        out.append(dict(notes=[note_of(NOTE.match(tok)) for tok in m.group(1).split()], dur=DUR[m.group(2)]))
    assert abs(sum(c["dur"] for c in out) - 4) < 1e-9, bar
    return out


class Abc:
    """Spells notes for the key signature, with accidentals carried inside the bar and restated in the next bar (courtesy)."""
    def __init__(self): self.prev = {}; self.cur = {}; self.alt = {}
    def bar(self): self.prev = self.alt; self.cur = {}; self.alt = {}
    def note(self, n):
        k = KEYSIG.get(n.letter, 0); key = (n.letter, n.octave); a = n.acc
        pre = ""
        if a != self.cur.get(key, k) or (n.letter in self.prev and self.prev[n.letter] != a and key not in self.cur):
            pre = {-2: "__", -1: "_", 0: "=", 1: "^", 2: "^^"}[a]
        self.cur[key] = a
        if a != k: self.alt[n.letter] = a
        o = n.octave - 3                                     # LilyPond marks: c = C3, c' = C4 (ABC "C"), c'' = C5 (ABC "c")
        return pre + (n.letter + "," * (1 - o) if o <= 1 else n.letter.lower() + "'" * (o - 2))


def ln(d): return {0.5: "", 1.0: "2", 2.0: "4", 4.0: "8"}[d]


def section(sid, title, desc, rh_bars, lh_bars, chords):
    rh_ev, lh_ev, abc_rh, abc_lh, marks = [], [], [], [], []
    sr, sl = Abc(), Abc()
    for i, rb in enumerate(rh_bars):
        sr.bar(); sl.bar()
        t, s, mk = 0.0, "", ""
        starts = {}; x = 0
        for c in chords[i]: starts[x] = c.get("show", c["sym"]); x += c["beats"]
        for e in parse_rh(rb):
            if s and (t in starts or t == 2.0 or e["dur"] >= 1 or s[-1].isdigit()): s += " "
            if t in starts: s += '"%s"' % starts[t]
            if e.get("rest"): s += "z" + ln(e["dur"])
            else:
                s += sr.note(e["n"]) + ln(e["dur"]); mk += e["mark"]
                rh_ev.append([i * 4 + t, e["n"].midi - SOUNDS_BELOW, e["dur"], 90])   # what sounds, in concert pitch
            t += e["dur"]
        abc_rh.append(s); marks.append(mk)
        if lh_bars:
            t, parts = 0.0, []
            for c in parse_lh(lh_bars[i]):
                parts.append("[" + "".join(sl.note(n) for n in c["notes"]) + "]" + ln(c["dur"]))
                for n in c["notes"]: lh_ev.append([i * 4 + t, n.midi, c["dur"], 90])
                t += c["dur"]
            abc_lh.append(" ".join(parts))
    abc = dict(rh=abc_rh, marks=marks)
    if lh_bars: abc["lh"] = abc_lh
    assert len("".join(marks)) == len(rh_ev)
    return dict(id=sid, title=title, desc=desc, rh=rh_ev, lh=lh_ev, abc=abc)


bars = []
flat = [(sym, 4 // len(b)) for b in spec["bars"] for sym in b]
i = 0
for b in spec["bars"]:
    row = []
    for sym in b:
        r, kind, _ = g.parse_chord(sym)
        nr, nk, _ = g.parse_chord(flat[(i + 1) % len(flat)][0])
        scale = g.choose_scale(kind, r, (nr, nk), kn.pc, minor)
        alters, ct = g.SCALES[scale]
        c = dict(sym=sym, beats=4 // len(b), root=r.pc, degs=[g.MAJOR_STEPS[d] + alters[d] for d in range(7)], scale=scale)   # concert: what the band plays
        if SEMIS:                                            # the written chord name the student reads
            j = 1
            while j < len(sym) and sym[j] in "#b": j += 1
            c["show"] = ascii_name(g.transpose(r, STEPS, SEMIS)) + sym[j:]
        row.append(c); i += 1
    bars.append(row)

n = len(bars)
lh = L["lh"] if PIANO else None
secs = [section("arpeggios", "Section 1 · Chord-Tone Arpeggios", "Every chord 1-3-5-7" + (", guide tones in the left hand" if PIANO else ", from the root up"), L["arp"], lh, bars)]
if L["pattern_mode"]:
    secs.append(section("patterns", "Section 3 · Pattern Chorus", "1-2-3-5 on the two-beat chords, scales on the long ones", L["sc"], lh, bars))
else:
    secs.append(section("scales", "Section 3 · Scale Chorus", "Each chord's scale from the root", L["sc"], lh, bars))
if L.get("lick_rh") and len(L["lick_bars"]) == n:          # a one-chorus Lick Chorus
    secs.append(section("licks", "Section 5 · Lick Chorus", "The ii–V–I licks dropped into the form", L["lick_rh"], (L["lick_lh"] or lh) if PIANO else None, bars))
elif L.get("lick_rh") and len(L["lick_rh"]) // n >= 2 and len(L["lick_rh"]) % n <= 1 and not PIANO:   # a 2-chorus (blues) Lick Chorus: one tab per chorus, each loops on its own
    LR = [b.strip() for x in L["lick_rh"] for b in re.sub(r'\\bar "[^"]*"|\\mark \\markup \\box \\bold "[^"]*"', "", x).split("|") if b.strip()]   # the final bar is joined to the last one
    for k in range(len(LR) // n):
        s = section("licks" if k == 0 else "licks%d" % (k + 1), "Section 5 · Lick Chorus %d" % (k + 1), "The ii–V–I licks dropped into the form, chorus %d" % (k + 1), LR[k * n:(k + 1) * n], None, bars)
        s["tab"] = "Licks %d" % (k + 1); secs.append(s)
if L.get("solo") and len(L["solo"]) == n:                    # the Sample Solo takes the place of the blank "Your solo" page (Alex, 23 Nov 2026)
    s = section("samplesolo", "Section %s · Sample Solo" % L.get("solo_num", "4"), "Blue: the guide tones on beats 1 and 4. First half: arpeggio notes between them. Second half: scale notes", L["solo"], lh, bars)
    s["tab"] = "Solo"; secs.append(s)
T = A.tempo
notation = dict(key=ascii_name(wk) + ("m" if minor else ""), staves="piano" if PIANO else "treble")
if PIANO: notation["lh"] = secs[0]["abc"]["lh"]
tune = dict(format="aam-tune/1", slug=SLUG, title=spec["title"], subtitle=A.subtitle or f"{n}-bar form · {SHORT}",
            instrument=INST, concert_key=ck, native=SEMIS % 12, first_bar=A.first_bar,   # concert_key + native: the player's key and instrument switch works from these
 chart_tempo=T, tempo_presets=sorted({max(60, round(T * 0.68 / 5) * 5), max(70, round(T * 0.84 / 5) * 5), T}),
            form=[[a, b - 1] for a, b in spec.get("form", [])], bars=bars, sections=secs, notation=notation)
tune["hide"] = ["solo"]          # the blank "Your solo" page is retired (Alex, 22 Nov 2026); a study's Solo tab is its Sample Solo section, when it has one
norm = re.sub(r"[^A-Z0-9]", "", A.code.upper())
pdf = dict(id=SLUG, title=A.pdf_title or spec["title"] + " · " + SHORT, hash=hashlib.sha256(("aam:" + norm).encode()).hexdigest(), tunes=[SLUG])
os.makedirs(os.path.join(A.repo, "tunes"), exist_ok=True)
json.dump(tune, open(os.path.join(A.repo, "tunes", SLUG + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
ip = os.path.join(A.repo, "index.json")
idx = json.load(open(ip))
clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == pdf["hash"] and p["id"] != pdf["id"]]
assert not clash, "that code is already used by " + clash[0] + ": pick another"
idx["pdfs"] = [p for p in idx["pdfs"] if p["id"] != pdf["id"]] + [pdf]
idx["tunes"][SLUG] = dict(title=tune["title"], subtitle=tune["subtitle"])
json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
print("wrote tunes/%s.json and index.json (%s, written key %s)" % (SLUG, SHORT, notation["key"]))
print("QR link: https://alexattardmusic.com/play/?t=%s&c=%s   printed code: %s" % (SLUG, norm, A.code.upper()))
