#!/usr/bin/env python3
"""The free public demo: five public-domain melodies, a major scale and a four-bar blues riff, written in concert pitch.
Writes tunes/demo-*.json and the "demo" shelf (free: no code needed) in index.json.   python3 tools/make_demo.py

Every melody here is out of copyright (Beethoven 1824; "Jingle Bells" 1857; traditional songs); the blues riff is original.
Melodies are typed in ABC, one string per bar (L:1/8), in the tune's key; chords are concert names, "/"-separated when
two share a bar."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
KEYSIG = {"F": {"B": -1}, "Bb": {"B": -1, "E": -1}}
QUAL = {"6": ([0, 2, 4, 5, 7, 9, 9], "Major (6th)"),          # 7th slot holds the 6th, so the piano plays a 6/9 chord under a tonic melody note
        "maj7": ([0, 2, 4, 5, 7, 9, 11], "Ionian (major)"), "": ([0, 2, 4, 5, 7, 9, 11], "Ionian (major)"),
        "7": ([0, 2, 4, 5, 7, 9, 10], "Mixolydian"), "m7": ([0, 2, 3, 5, 7, 9, 10], "Dorian")}

def chord(sym, beats):
    m = re.match(r"^([A-G])([b#]?)(.*)$", sym); root = (PC[m.group(1)] + {"b": -1, "#": 1, "": 0}[m.group(2)]) % 12
    degs, scale = QUAL[m.group(3)]
    return {"sym": sym, "beats": beats, "root": root, "degs": degs, "scale": scale}

def notes(bar, key, at):
    """One ABC bar -> [[start beat, midi, beats, 90], ...] and the number of notes."""
    out, t, alt = [], 0.0, {}
    for acc, letter, octs, num in re.findall(r"([_=^]?)([A-Ga-gz])([,']*)(\d*)", bar):
        dur = (int(num) if num else 1) / 2.0
        if letter != "z":
            L = letter.upper(); name = L + ("5" if letter.islower() else "4") + octs
            if acc: alt[name] = {"_": -1, "=": 0, "^": 1}[acc]
            a = alt.get(name, KEYSIG[key].get(L, 0))
            midi = 60 + PC[L] + a + (12 if letter.islower() else 0) + 12 * octs.count("'") - 12 * octs.count(",")
            out.append([at + t, midi, dur, 90])
        t += dur
    assert abs(t - 4) < 1e-9, ("bar is not 4 beats", bar, t)
    return out

def tune(slug, title, sub, key, tempos, bars, chords, desc, style=None, hide=None, reps=None, tab="Melody", feel=None):
    assert len(bars) == len(chords), (slug, len(bars), len(chords))
    rh = []
    for i, b in enumerate(bars): rh += notes(b, key, 4 * i)
    cb = []
    for c in chords:
        parts = c.split("/"); cb.append([chord(p, 4 // len(parts)) for p in parts])
    marks = ["." * len(notes(b, key, 0)) for b in bars]
    t = {"format": "aam-tune/1", "slug": slug, "title": title, "subtitle": sub, "instrument": "", "concert_key": key, "native": 0,
         "first_bar": 1, "chart_tempo": tempos[-1], "tempo_presets": tempos, "form": [], "bars": cb,
         "sections": [{"id": "melody", "title": tab, "tab": tab, "desc": desc, "rh": rh, "lh": [], "abc": {"rh": bars, "marks": marks}}],
         "notation": {"key": key, "staves": "treble"}, "open_on": "melody", "demo": True}
    if style: t["style"] = style
    if hide: t["hide"] = hide
    if reps: t["reps"] = reps
    if feel: t["feel"] = feel
    json.dump(t, open(os.path.join(ROOT, "tunes", slug + ".json"), "w"), ensure_ascii=False)
    return slug

A = ["d2 d2 e2 f2", "f2 e2 d2 c2", "B2 B2 c2 d2"]
ode = A + ["d3 c c4"] + A + ["c3 B B4", "c2 c2 d2 B2", "c2 de d2 B2", "c2 de d2 c2", "B2 c2 F4"] + A + ["c3 B B4"]
ode_ch = ["Bb6", "F7", "Bb6", "Cm7/F7", "Bb6", "F7", "Bb6", "F7/Bb6", "F7/Bb6", "F7/Bb6", "F7/Bb6", "C7/F7", "Bb6", "F7", "Bb6", "F7/Bb6"]

saints = ["z2 F2 A2 B2", "c8", "z2 F2 A2 B2", "c8", "z2 F2 A2 B2", "c4 A4", "F4 A4", "G8",
          "z2 A2 A2 G2", "F6 F2", "A4 c4", "c2 B6", "z4 A2 B2", "c4 A4", "F4 G4", "F8"]
saints_ch = ["F6", "F6", "F6", "F6", "F6", "F6", "F6", "C7", "C7", "F6", "F7", "Bb6", "F6", "F6/D7", "Gm7/C7", "F6"]

J = ["A2 A2 A4", "A2 A2 A4", "A2 c2 F3 G", "A8", "B2 B2 B3 B", "B2 A2 A2 AA"]
jingle = J + ["A2 G2 G2 A2", "G4 c4"] + J + ["c2 c2 B2 G2", "F8"]
jingle_ch = ["F6", "F6", "F6", "F6/F7", "Bb6", "F6", "G7", "C7", "F6", "F6", "F6", "F6/F7", "Bb6", "F6", "C7", "F6"]

T1 = ["F2 F2 c2 c2", "d2 d2 c4", "B2 B2 A2 A2", "G2 G2 F4"]; T2 = ["c2 c2 B2 B2", "A2 A2 G4"]
twinkle = T1 + T2 + T2 + T1
twinkle_ch = ["F6", "Bb6/F6", "Bb6/F6", "C7/F6"] + ["F6/Bb6", "F6/C7"] * 2 + ["F6", "Bb6/F6", "Bb6/F6", "C7/F6"]

auld = ["z6 F2",
        "B3 B B2 d2", "c3 B c2 d2", "B3 B d2 f2", "g6 g2", "f3 d d2 B2", "c3 B c2 d2", "B3 G G2 F2", "B6 g2",
        "f3 d d2 B2", "c3 B c2 g2", "f3 d d2 f2", "g6 b2", "f3 d d2 B2", "c3 B c2 d2", "B3 G G2 F2", "B8"]
auld_ch = ["F7"] + ["Bb6", "F7", "Bb6/Bb7", "Eb6", "Bb6", "F7", "Cm7/F7", "Bb6"] * 2

made = [
  tune("demo-jingle-bells", "Jingle Bells", "James Pierpont, 1857 · free demo", "F", [140, 100, 176], jingle, jingle_ch, "The chorus, with a band behind you", feel="straight"),
  tune("demo-ode-to-joy", "Ode to Joy", "Beethoven · free demo", "Bb", [96, 72, 120], ode, ode_ch, "The melody everyone knows, with a band behind you", feel="straight"),
  tune("demo-when-the-saints", "When the Saints Go Marching In", "Traditional · free demo", "F", [132, 100, 160], saints, saints_ch, "A New Orleans classic: three notes up and hold"),
  tune("demo-twinkle", "Twinkle, Twinkle, Little Star", "Traditional · free demo", "F", [100, 72, 132], twinkle, twinkle_ch, "A first tune, with a real band", feel="straight"),
  tune("demo-auld-lang-syne", "Auld Lang Syne", "Traditional · free demo", "Bb", [88, 66, 112], auld, auld_ch, "Verse and chorus. The first bar is the pick-up note", feel="straight"),
  tune("demo-major-scale", "Major Scale", "Warm-up · free demo", "F", [72, 60, 100], ["F2 G2 A2 B2", "c2 d2 e2 f2", "f2 e2 d2 c2", "B2 A2 G2 F2"], ["F"] * 4,
       "Up and down, one note to a beat, over a drone", style="drone", hide=["chords", "solo", "names"], reps=2, tab="Scale"),
  tune("demo-blues-riff", "Blues Riff", "The first four bars of a B♭ blues · free demo", "Bb", [100, 80, 126], ["z2 df g2 f2", "z2 _de g2 e2", "z2 df g2 b2", "_a2 f2 d2 B2"],
       ["Bb7", "Eb7", "Bb7", "Bb7"], "A call-and-response riff. Loop it, then make up your own answer", reps=4, tab="Riff"),
]
p = os.path.join(ROOT, "index.json"); idx = json.load(open(p))
idx["pdfs"] = [x for x in idx["pdfs"] if x["id"] != "demo"] + [{"id": "demo", "title": "Free demo", "free": True, "tunes": made}]
for sl in made:
    t = json.load(open(os.path.join(ROOT, "tunes", sl + ".json")))
    idx["tunes"][sl] = {"title": t["title"], "subtitle": t["subtitle"]}
json.dump(idx, open(p, "w"), ensure_ascii=False, indent=1)
print("wrote", len(made), "demo tunes")
