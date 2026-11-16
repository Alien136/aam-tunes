"""Publish a piano study to the play-along tune folder (the aam-tunes repository).

Usage: python3 publish_tune.py spec.json /path/to/aam-tunes --slug winter-wonderland-piano --code WW-2193 [--subtitle "..."] [--pdf-title "..."] [--tempo 132] [--first-bar 1]
Writes tunes/<slug>.json (format aam-tune/1) and adds the PDF and tune to index.json. Then commit and push the repository.
Needs gen_study.py in the same folder.
"""
import argparse, json, os, re, sys, hashlib
import gen_study as g
ap = argparse.ArgumentParser()
ap.add_argument("spec"); ap.add_argument("repo"); ap.add_argument("--slug", required=True); ap.add_argument("--code", required=True)
ap.add_argument("--subtitle"); ap.add_argument("--pdf-title"); ap.add_argument("--tempo", type=int, default=132); ap.add_argument("--first-bar", type=int, default=1)
A = ap.parse_args()
spec = json.load(open(A.spec))
assert spec.get("instrument") == "piano", "notation and demos are concert pitch: piano studies only for now"
g.build(dict(spec)); L = g.LAST
SLUG = A.slug
ck = spec["concert_key"]; minor = ck.endswith("m"); kn = g.parse_note(ck.rstrip("m"))
major_pc = (kn.pc + 3) % 12 if minor else kn.pc                      # key signature = the relative major's
NSHARP = {0: 0, 7: 1, 2: 2, 9: 3, 4: 4, 11: 5, 5: -1, 10: -2, 3: -3, 8: -4, 1: -5, 6: -6}[major_pc]
KEYSIG = {l: 1 for l in "FCGDAEB"[:max(NSHARP, 0)]}; KEYSIG.update({l: -1 for l in "BEADGCF"[:max(-NSHARP, 0)]})
KEY_PC = major_pc
NOTE = re.compile(r"^(GREY:)?([a-g])((?:is|es)*)([',]*)(\d+)?$")
DUR = {"8": .5, "4": 1.0, "2": 2.0, "1": 4.0}

def clean(s):
    s = re.sub(r'\\mark \\markup \\box \\bold "[^"]*"', "", s).replace('\\bar "||"', "").replace("|", " ")
    return s.replace("\\tweak color #grey \\tweak Accidental.color #grey ", "GREY:")

def parse_rh(bar):
    out, lick, dur = [], False, None
    for tok in clean(bar).split():
        if tok == "\\lickOn": lick = True; continue
        if tok == "\\lickOff": lick = False; continue
        m = re.match(r"^r(\d+)$", tok)
        if m: out.append(dict(rest=True, dur=DUR[m.group(1)])); continue
        m = NOTE.match(tok); assert m, (tok, bar)
        if m.group(5): dur = m.group(5)
        acc = (len(m.group(3)) // 2) * (1 if "is" in m.group(3) else -1)
        o = m.group(4).count("'") - m.group(4).count(",")
        out.append(dict(letter=m.group(2).upper(), acc=acc, oct=o, dur=DUR[dur], mark="l" if lick else ("g" if m.group(1) else ".")))
    assert abs(sum(n["dur"] for n in out) - 4) < 1e-9, bar
    return out

def parse_lh(bar):
    out = []
    for m in re.finditer(r"<([^>]*)>(\d)", bar):
        ns = []
        for tok in m.group(1).split():
            k = NOTE.match(tok); acc = (len(k.group(3)) // 2) * (1 if "is" in k.group(3) else -1)
            ns.append(dict(letter=k.group(2).upper(), acc=acc, oct=k.group(4).count("'") - k.group(4).count(",")))
        out.append(dict(notes=ns, dur=DUR[m.group(2)]))
    assert abs(sum(c["dur"] for c in out) - 4) < 1e-9, bar
    return out

midi = lambda n: 48 + g.NAT[n["letter"]] + n["acc"] + 12 * n["oct"]

class Abc:
    """Spells notes for K:Eb with accidentals carried inside the bar and restated in the next bar (courtesy)."""
    def __init__(self): self.prev = {}; self.cur = {}; self.alt = {}
    def bar(self): self.prev = self.alt; self.cur = {}; self.alt = {}
    def note(self, n):
        k = KEYSIG.get(n["letter"], 0); key = (n["letter"], n["oct"]); a = n["acc"]
        pre = ""
        if a != self.cur.get(key, k) or (n["letter"] in self.prev and self.prev[n["letter"]] != a and key not in self.cur):
            pre = {-2: "__", -1: "_", 0: "=", 1: "^", 2: "^^"}[a]
        self.cur[key] = a
        if a != k: self.alt[n["letter"]] = a
        o = n["oct"]
        body = n["letter"] + "," * (1 - o) if o <= 1 else n["letter"].lower() + "'" * (o - 2)
        return pre + body

def ln(d): return {0.5: "", 1.0: "2", 2.0: "4", 4.0: "8"}[d]

def section(sid, title, desc, rh_bars, lh_bars, chords):
    rh_ev, lh_ev, abc_rh, abc_lh, marks = [], [], [], [], []
    sr, sl = Abc(), Abc()
    for i, (rb, lb) in enumerate(zip(rh_bars, lh_bars)):
        sr.bar(); sl.bar()
        t, s, mk = 0.0, "", ""
        starts = {}; x = 0
        for c in chords[i]: starts[x] = c["sym"]; x += c["beats"]
        for n in parse_rh(rb):
            if s and (t in starts or t == 2.0 or n["dur"] >= 1 or s[-1].isdigit()): s += " "
            if t in starts: s += '"%s"' % starts[t]
            if n.get("rest"): s += "z" + ln(n["dur"])
            else:
                s += sr.note(n) + ln(n["dur"]); mk += n["mark"]
                rh_ev.append([i * 4 + t, midi(n), n["dur"], 90])
            t += n["dur"]
        abc_rh.append(s); marks.append(mk)
        t, parts = 0.0, []
        for c in parse_lh(lb):
            parts.append("[" + "".join(sl.note(n) for n in c["notes"]) + "]" + ln(c["dur"]))
            for n in c["notes"]: lh_ev.append([i * 4 + t, midi(n), c["dur"], 90])
            t += c["dur"]
        abc_lh.append(" ".join(parts))
    return dict(id=sid, title=title, desc=desc, rh=rh_ev, lh=lh_ev, abc=dict(rh=abc_rh, marks=marks, lh=abc_lh))

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
        row.append(dict(sym=sym, beats=4 // len(b), root=r.pc, degs=[g.MAJOR_STEPS[d] + alters[d] for d in range(7)], scale=scale))
        i += 1
    bars.append(row)

n = len(bars)
secs = [section("arpeggios", "Section 1 · Chord-Tone Arpeggios", "Every chord 1-3-5-7, guide tones in the left hand", L["arp"], L["lh"], bars)]
if L["pattern_mode"]:
    secs.append(section("patterns", "Section 3 · Pattern Chorus", "1-2-3-5 on the two-beat chords, scales on the long ones", L["sc"], L["lh"], bars))
else:
    secs.append(section("scales", "Section 3 · Scale Chorus", "Each chord's scale from the root", L["sc"], L["lh"], bars))
if L.get("lick_rh") and len(L["lick_bars"]) == n:      # a one-chorus Lick Chorus only (a 2-chorus blues one is longer than the form)
    secs.append(section("licks", "Section 5 · Lick Chorus", "The ii–V–I licks dropped into the form", L["lick_rh"], L["lick_lh"] or L["lh"], bars))
T = A.tempo
tune = dict(format="aam-tune/1", slug=SLUG, title=spec["title"], subtitle=A.subtitle or f"{n}-bar form · Piano",
            instrument="piano", first_bar=A.first_bar, chart_tempo=T, tempo_presets=sorted({max(60, round(T * 0.68 / 5) * 5), max(70, round(T * 0.84 / 5) * 5), T}),
            form=[[a, b - 1] for a, b in spec.get("form", [])], bars=bars, sections=secs,
            notation=dict(key=ck, staves="piano", lh=secs[0]["abc"]["lh"]))
norm = re.sub(r"[^A-Z0-9]", "", A.code.upper())
pdf = dict(id=SLUG, title=A.pdf_title or spec["title"] + " · Piano", hash=hashlib.sha256(("aam:" + norm).encode()).hexdigest(), tunes=[SLUG])
os.makedirs(os.path.join(A.repo, "tunes"), exist_ok=True)
json.dump(tune, open(os.path.join(A.repo, "tunes", SLUG + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
ip = os.path.join(A.repo, "index.json")
idx = json.load(open(ip))
idx["pdfs"] = [p for p in idx["pdfs"] if p["id"] != pdf["id"]] + [pdf]
idx["tunes"][SLUG] = dict(title=tune["title"], subtitle=tune["subtitle"])
json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
for s in secs: assert len("".join(s["abc"]["marks"])) == len(s["rh"])
print("wrote tunes/%s.json and index.json" % SLUG)
print("QR link: https://alexattardmusic.com/play/?t=%s&c=%s   printed code: %s" % (SLUG, norm, A.code.upper()))
