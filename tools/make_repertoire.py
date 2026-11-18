#!/usr/bin/env python3
"""Build a Graded Repertoire book for the player: one tune file per piece (style "solo": the written piano part, both hands,
no band) and the book's shelf in index.json.

  python3 tools/make_repertoire.py repertoire/books/level-1-baroque-classical.json [--code GR1-1234]

Each piece is a file in repertoire/src/ (written by tools/import_ly_midi.py, then edited by hand): one ABC string per bar for
each hand. That ABC is the single source: the notation shown AND the notes played both come from it, so fingering (!1!),
dynamics (!p! !mf! !f!), staccato (.) and slurs added there show up in the player. The code is given once, when the book is
first published; after that the book keeps its hash, so students' codes keep working."""
import json, os, re, sys, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARPS, FLATS = "FCGDAEB", "BEADGCF"
KEYS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "F": -1, "Bb": -2, "Eb": -3, "Ab": -4, "Am": 0, "Em": 1, "Bm": 2, "Dm": -1, "Gm": -2, "Cm": -3, "Fm": -4}
DYN = {"pp": 52, "p": 66, "mp": 78, "mf": 92, "f": 106, "ff": 118}
TOKEN = re.compile(r"\s+|!([^!]+)!|\(3|\[([^\]]+)\]((?:\d+)?(?:/\d*)?)(-?)|(\.?)([_=^]?)([A-Ga-gz])([,']*)((?:\d+)?(?:/\d*)?)(-?)|[()|]")

def keysig(key):
    n = KEYS[key]
    return {l: 1 for l in SHARPS[:n]} if n > 0 else {l: -1 for l in FLATS[:-n]} if n < 0 else {}

def length(txt):                               # ABC length in eighths -> beats
    if not txt: return 0.5
    num, _, den = txt.partition("/")
    return (int(num) if num else 1) / (int(den) if den else (2 if "/" in txt else 1)) / 2

def pitch(acc, letter, octs, ks, alt):
    L = letter.upper(); name = (L, letter.islower(), octs)
    if acc: alt[name] = {"_": -1, "=": 0, "^": 1}[acc]
    return 60 + PC[L] + alt.get(name, ks.get(L, 0)) + (12 if letter.islower() else 0) + 12 * octs.count("'") - 12 * octs.count(",")

def events(bars, key, bpb):
    """[[start beat, midi, beats, loudness], ...] and the number of note heads per bar (ties merged into one sounding note)."""
    ks, out, counts, vel, open_ties = keysig(key), [], [], 90, {}
    for b, bar in enumerate(bars):
        t, alt, n, trip, pos = 0.0, {}, 0, 0, 0
        while pos < len(bar):
            m = TOKEN.match(bar, pos); assert m, ("cannot read", bar[pos:], "in bar", b + 1, bar)
            pos = m.end(); tok = m.group(0)
            if m.group(1): vel = DYN.get(m.group(1), vel); continue             # !mf! and friends; other marks (fingering) only show
            if tok == "(3": trip = 3; continue
            chord, single = m.group(2), m.group(7)
            if not chord and not single: continue
            dtxt, tie = (m.group(3), m.group(4)) if chord else (m.group(9), m.group(10))
            d = length(dtxt) * (2 / 3 if trip else 1); trip = max(0, trip - 1)
            stacc = bool(m.group(5)) and not chord
            notes = [] if single == "z" else [pitch(a, l, o, ks, alt) for a, l, o in re.findall(r"([_=^]?)([A-Ga-g])([,']*)", chord)] if chord else [pitch(m.group(6), single, m.group(8), ks, alt)]
            for p in notes:
                if p in open_ties: open_ties[p][2] += d; ev = open_ties.pop(p)   # the second half of a tie: lengthen the first note
                else: ev = [4.0 * 0 + bpb * b + t, p, d * (0.5 if stacc else 1), vel]; out.append(ev)
                if tie: open_ties[p] = ev
            n += 1 if notes else 0
            t += d
        assert abs(t - bpb) < 1e-6, ("bar %d is %.3f beats, not %d" % (b + 1, t, bpb), bar)
        counts.append(n)
    return [[round(s, 4), p, round(d, 4), v] for s, p, d, v in out], counts

def build(book_path, code=None):
    book = json.load(open(book_path)); idxp = os.path.join(ROOT, "index.json"); idx = json.load(open(idxp)); slugs = []
    for name in book["pieces"]:
        p = json.load(open(os.path.join(ROOT, "repertoire", "src", name + ".json")))
        bpb, unit = [int(x) for x in p["meter"].split("/")]; assert unit == 4 and bpb in (2, 3, 4), "the player takes 2/4, 3/4 and 4/4"
        assert len(p["rh"]) == len(p["lh"])
        rh, counts = events(p["rh"], p["key"], bpb); lh, _ = events(p["lh"], p["key"], bpb)
        tonic = p["key"].rstrip("m"); root = (PC[tonic[0]] + (-1 if tonic.endswith("b") else 0)) % 12
        minor = p["key"].endswith("m")
        degs, scale = ([0, 2, 3, 5, 7, 8, 10], "Natural minor") if minor else ([0, 2, 4, 5, 7, 9, 11], "Ionian (major)")
        t = {"format": "aam-tune/1", "slug": p["slug"], "title": p["title"], "subtitle": p["composer"] + " · " + book["short"], "instrument": book.get("instrument", "piano"),
             "concert_key": p["key"], "native": 0, "style": "solo", "meter": [bpb, 4], "hide": ["chords", "solo", "names"], "first_bar": 1,
             "chart_tempo": p["tempo"], "tempo_presets": [round(p["tempo"] * 0.6), round(p["tempo"] * 0.8), p["tempo"]],
             "form": [], "bars": [[{"sym": tonic + ("m" if minor else ""), "beats": bpb, "root": root, "degs": degs, "scale": scale}] for _ in p["rh"]],
             "sections": [{"id": "music", "title": "Music", "tab": "Music", "desc": p.get("note") or "Both hands are written out. In Practice settings, switch off Right hand or Left hand to hear one at a time", "rh": rh, "lh": lh,
                           "abc": {"rh": p["rh"], "lh": p["lh"], "marks": ["." * c for c in counts]}}],
             "notation": {"key": p["key"], "staves": "piano", "lh": ["z%d" % (bpb * 2)] * len(p["rh"])}, "source": p.get("source", "")}
        json.dump(t, open(os.path.join(ROOT, "tunes", p["slug"] + ".json"), "w"), ensure_ascii=False)
        idx["tunes"][p["slug"]] = {"title": t["title"], "subtitle": t["subtitle"]}; slugs.append(p["slug"])
        print("%-28s %d bars, %d notes right hand, %d left" % (p["slug"], len(p["rh"]), len(rh), len(lh)))
    old = [x for x in idx["pdfs"] if x["id"] == book["id"]]
    if code: h = hashlib.sha256(("aam:" + re.sub(r"[^A-Z0-9]", "", code.upper())).encode()).hexdigest()
    else: assert old, "first publication needs --code"; h = old[0]["hash"]
    entry = {"id": book["id"], "title": book["title"], "hash": h, "tunes": slugs}
    idx["pdfs"] = [entry if x["id"] == book["id"] else x for x in idx["pdfs"]] if old else [x for x in idx["pdfs"] if x["id"] != "demo"] + [entry] + [x for x in idx["pdfs"] if x["id"] == "demo"]
    json.dump(idx, open(idxp, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    code = sys.argv[sys.argv.index("--code") + 1] if "--code" in sys.argv else None
    build(sys.argv[1], code)
