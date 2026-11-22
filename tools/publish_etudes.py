"""Publish an étude volume (Blues Études and the series after it) to the play-along player, one tune per étude per instrument.

Usage: python3 tools/publish_etudes.py /path/to/etude_data.py /path/to/aam-tunes --codes codes.json [--check]
       python3 tools/publish_etudes.py /path/to/etude_data.py /path/to/aam-tunes --links        (print the QR links, write nothing)

etude_data.py is the volume's data file from the Blues Études Build Kit: VOLUME = {"number": 1, "subtitle": "...", ...} and
ETUDES = [{"n", "title", "player", "key", "bpm", "chords": 12 bars, "bars": 25 LilyPond strings in CONCERT pitch inside \\fixed c',
"alto_bars"/"tenor_bars"/"flute_bars": {bar number: replacement} for an edition's own bars}, ...]. Optional VOLUME keys:
"series" (default "Blues Études"), "prefix" (default "be": slugs are be<number>-<n>-<edition>), "sample" (étude numbers in the
free sample, default [4]), "editions" (default alto, tenor, flute).

codes.json (never committed; the codes are written only in the Build Desk's Library table):
  {"alto": {"code": "B1A-1234", "sample": "S1A-1234"}, "tenor": {...}, "flute": {...}}
Each edition is its own product with its own code (Alex, 22 Nov 2026: the editions are sold separately); the sample code opens
only the sample études. A code already used by another booklet is refused. Codes and slugs never change once a PDF is printed.

What each tune holds, the same as every other tune the player reads today (see publish_tune.py and publish_exercise.py):
  instrument, concert_key, native   so the tuner, Learn mode and the fingering diagrams know what the student reads;
  the music in WRITTEN pitch for that instrument, as the PDF prints it, with written chord names; the band in concert pitch;
  keys "off"                        the étude is played in the key on the page (no key button);
  one section, "Étude", and the chord chart. Grace notes, falls and trills stay in the PDF: the player shows and listens for
  the main notes only.
--check builds every tune in memory and reports, without touching the repository (the product bots run it before a PDF goes out).
"""
import argparse, hashlib, importlib.util, json, os, re, sys
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_study as g

SOUNDS_BELOW = {"alto": 9, "tenor": 14, "flute": 0, "clarinet": 2, "soprano": 2, "bari": 21, "trumpet": 2, "concert": 0}
OCTAVE_UP = {"flute": 1}                                     # the flute edition is printed an octave above the concert line
SHORT = {"alto": "Alto Sax", "tenor": "Tenor Sax", "flute": "Flute", "clarinet": "Clarinet", "soprano": "Soprano Sax", "bari": "Bari Sax",
         "trumpet": "Trumpet", "concert": "Concert Pitch"}
DEGS = {"Mixolydian": [0, 2, 4, 5, 7, 9, 10], "Phrygian dominant": [0, 1, 4, 5, 7, 8, 10], "Dorian": [0, 2, 3, 5, 7, 9, 10], "Melodic minor": [0, 2, 3, 5, 7, 9, 11],
        "Locrian": [0, 1, 3, 5, 6, 8, 10], "Ionian (major)": [0, 2, 4, 5, 7, 9, 11], "Diminished": [0, 2, 3, 5, 6, 8, 9]}      # the names the player's comping table reads
QUAL = {"7": "7", "m7": "m7", "m7.5-": "m7b5", "dim7": "°7", "maj7": "maj7", "6": "6", "m6": "m6", "9": "9", "13": "13", "m9": "m9"}
TOK = re.compile(r'\\tuplet\s+(?P<tn>\d+)/(?P<td>\d+)\s*\{|\}|\\(?:acciaccatura|grace|appoggiatura)\b|\\bendAfter\s+#-?\d+|\^"[^"]*"|_"[^"]*"|\(|\)|~|->|-\.|--|-\^|-_|'
                 r"\\[a-zA-Z]+|(?P<name>[a-g](?:is|es)*|r)(?P<octs>[',]*)(?P<dur>\d*)(?P<dots>\.*)")
ascii_name = lambda n: n.letter + ("#" * n.acc if n.acc > 0 else "b" * -n.acc)


def keysig(written_key, minor):
    major_pc = (written_key.pc + 3) % 12 if minor else written_key.pc
    ns = {0: 0, 7: 1, 2: 2, 9: 3, 4: 4, 11: 5, 5: -1, 10: -2, 3: -3, 8: -4, 1: -5, 6: -6}[major_pc]
    ks = {l: 1 for l in "FCGDAEB"[:max(ns, 0)]}; ks.update({l: -1 for l in "BEADGCF"[:max(-ns, 0)]})
    return ks


class Abc:
    """Spells notes for a key signature, accidentals carried inside the bar and restated in the next bar."""
    def __init__(self, ks): self.ks = ks; self.prev = {}; self.cur = {}; self.alt = {}
    def bar(self): self.prev = self.alt; self.cur = {}; self.alt = {}
    def note(self, n):
        k = self.ks.get(n.letter, 0); key = (n.letter, n.octave); a = n.acc; pre = ""
        if a != self.cur.get(key, k) or (n.letter in self.prev and self.prev[n.letter] != a and key not in self.cur):
            pre = {-2: "__", -1: "_", 0: "=", 1: "^", 2: "^^"}[a]
        self.cur[key] = a
        if a != k: self.alt[n.letter] = a
        o = n.octave - 3
        return pre + (n.letter + "," * (1 - o) if o <= 1 else n.letter.lower() + "'" * (o - 2))


def abc_len(eighths):
    f = F(eighths).limit_denominator(16)
    if f == 1: return ""
    if f.denominator == 1: return str(f.numerator)
    return ("" if f.numerator == 1 else str(f.numerator)) + "/" + str(f.denominator)


def parse_bar(text, where):
    """One concert bar -> [dict(rest, name, octs, nominal (beats as printed), dur (beats as played), tie, deco, text, tup)]."""
    out, dur, dots, tup, grace = [], "8", "", None, False
    for m in TOK.finditer(text):
        t = m.group(0)
        if t.startswith("\\tuplet"): tup = [F(int(m.group("td")), int(m.group("tn"))), len(out)]; continue
        if t == "}":
            if tup: n = len(out) - tup[1]; [x.__setitem__("tup", (i, n)) for i, x in enumerate(out[tup[1]:])]
            tup = None; continue
        if re.match(r"\\(acciaccatura|grace|appoggiatura)", t): grace = True; continue
        if t in ("(", ")") or t.startswith("\\bendAfter"): continue          # slurs and falls stay in the PDF
        if t == "~":
            if out: out[-1]["tie"] = True
            continue
        if t in ("->", "-.", "--", "-^", "-_"):
            if out and not out[-1]["rest"]: out[-1]["deco"] += {"->": "!>!", "-.": ".", "--": "!tenuto!", "-^": "!^!", "-_": "!tenuto!"}[t]
            continue
        if t[0] in "^_" and t[1] == '"':
            if out: out[-1]["text"] = t[2:-1]
            continue
        if m.group("name") is None: continue                                 # \parenthesize, \trill and other marks: PDF only
        if m.group("dur"): dur, dots = m.group("dur"), m.group("dots")
        elif m.group("dots"): dots = m.group("dots")
        if grace: grace = False; continue                                    # a grace note is not counted or listened for
        nominal = F(4, int(dur)) * (F(3, 2) if dots == "." else F(7, 4) if dots == ".." else 1)
        out.append(dict(rest=m.group("name") == "r", name=m.group("name"), octs=m.group("octs"), nominal=nominal, dur=nominal * (tup[0] if tup else 1),
                        tie=False, deco="", text="", tup=None))
    total = sum(x["dur"] for x in out)
    assert total == 4, "%s is %s beats long" % (where, total)
    return out


def build(e, V, ed):
    steps, semis, _ = g.INSTRUMENTS[ed]
    minor = e.get("mode") == "minor"
    lp = lambda s: g.Note(s[0].upper(), s[1:].count("is") - s[1:].count("es"), 4)
    kn = lp(e["key"]); wk = g.transpose(kn, steps, semis)
    sp = Abc(keysig(wk, minor))
    syms = [b.split() for b in e["chords"]]
    nbars = len(e["bars"])
    rows_src = (syms * (nbars // len(syms) + 1))[:nbars]
    flat = [s for b in rows_src for s in b]
    rows, i = [], 0
    for b in rows_src:
        row = []
        for s in b:
            root, q = s.split(":"); r = lp(root); sym = ascii_name(r) + QUAL[q]
            nroot, nq = flat[(i + 1) % len(flat)].split(":")
            if q in ("7", "9", "13"): scale = "Phrygian dominant" if nq in ("m7", "m7.5-", "m6", "m9") and (lp(nroot).pc - r.pc) % 12 == 5 else "Mixolydian"
            else: scale = {"m7": "Dorian", "m9": "Dorian", "m6": "Melodic minor", "m7.5-": "Locrian", "dim7": "Diminished", "maj7": "Ionian (major)", "6": "Ionian (major)"}[q]
            c = dict(sym=sym, beats=4 // len(b), root=r.pc, degs=DEGS[scale], scale=scale)
            if semis: c["show"] = ascii_name(g.transpose(r, steps, semis)) + QUAL[q]
            row.append(c); i += 1
        rows.append(row)
    own = {int(k): v for k, v in e.get(ed + "_bars", {}).items()}
    ev, abc, marks, held, lo, hi = [], [], [], None, 200, 0
    for bi in range(nbars):
        where = "%s étude %s bar %d (%s)" % (V["slug_base"], e["n"], bi + 1, ed)
        notes = parse_bar(own.get(bi + 1, e["bars"][bi]), where)
        sp.bar()
        fine = any(x["dur"] < F(1, 2) or x["tup"] for x in notes)                 # 16ths or triplets: beam beat by beat
        starts, x0 = {}, F(0)
        for c in rows[bi]: starts[x0] = c.get("show", c["sym"]); x0 += c["beats"]
        pending = sorted(starts)
        t, s, mk = F(0), "", ""
        quick = {int(t0) for t0, x in zip(_onsets(notes), notes) if x["dur"] < F(1, 2) and not x["tup"]}   # beats played in straight sixteenths
        for x in notes:
            first_of_tup = x["tup"] and x["tup"][0] == 0
            in_tup = x["tup"] and x["tup"][0] > 0
            if s and not in_tup and not s.endswith(" ") and (t == 2 or x["nominal"] >= 1 or x["rest"] or (fine and t.denominator == 1) or s[-1] == "-" or first_of_tup):
                s += " "
            sym = ""
            while pending and pending[0] <= t: sym = '"%s"' % starts[pending.pop(0)]
            if first_of_tup: s += sym + ("(3" if x["tup"][1] == 3 else "(%d:%d:%d" % (x["tup"][1], 2, x["tup"][1])); sym = ""
            if x["rest"]:
                s += sym + "z" + abc_len(x["nominal"] * 2); held = None
            else:
                n = g.transpose(g.Note(x["name"][0].upper(), x["name"][1:].count("is") - x["name"][1:].count("es"),
                                       4 + x["octs"].count("'") - x["octs"].count(",")), steps, semis)
                if OCTAVE_UP.get(ed): n = g.Note(n.letter, n.acc, n.octave + OCTAVE_UP[ed])
                lo, hi = min(lo, n.midi), max(hi, n.midi)
                s += sym + ('"^%s"' % x["text"] if x["text"] else "") + x["deco"] + sp.note(n) + abc_len(x["nominal"] * 2) + ("-" if x["tie"] else "")
                mk += "."
                sounding = n.midi - SOUNDS_BELOW[ed]
                if held and held[1] == sounding: held[2] = round(held[2] + float(x["dur"]), 4)          # the second half of a tie
                else:
                    f = t - int(t)
                    at = float(t) + (0.0102 if f == F(1, 2) and int(t) in quick else 0)   # the player swings a note exactly on the "and" (within 0.01 of it); a beat of sixteenths is played straight. Under 1/96 of a beat, so Learn mode still finds the note
                    held = [round(bi * 4 + at, 4), sounding, round(float(x["dur"]), 4), 104 if "!>!" in x["deco"] else 90]; ev.append(held)
                if not x["tie"]: held = None
            if x["tup"] and x["tup"][0] == x["tup"][1] - 1: s += " "
            t += x["dur"]
        abc.append(" ".join(s.split())); marks.append(mk)
    slug = "%s-%s-%s" % (V["slug_base"], e["n"], ed)
    T = e["bpm"]
    title = "Étude %s: %s" % (e["n"], e["title"])
    sec = dict(id="etude", title="Étude %s" % e["n"], tab="Étude", desc="%s, in the style of %s" % (e["title"], e["player"]), rh=ev, lh=[], abc=dict(rh=abc, marks=marks))
    tune = dict(format="aam-tune/1", slug=slug, title=title, subtitle="%s Vol. %s · %s · in the style of %s" % (V["series"], V["number"], SHORT[ed], e["player"]),
                instrument=ed, concert_key=ascii_name(kn) + ("m" if minor else ""), native=semis % 12, keys="off", hide=["solo"],
                first_bar=1, chart_tempo=T, tempo_presets=sorted({max(60, round(T * 0.5 / 5) * 5), max(70, round(T * 0.75 / 5) * 5), T}),
                form=[["Chorus %d" % (k + 1), k * len(syms)] for k in range(nbars // len(syms))], bars=rows, sections=[sec],
                notation=dict(key=ascii_name(wk) + ("m" if minor else ""), staves="treble"))
    if e.get("page"): tune["page"] = e["page"]
    return tune, (lo, hi)


def _onsets(notes):
    t = F(0)
    for x in notes:
        yield t
        t += x["dur"]


RANGE = {"alto": (58, 90), "tenor": (58, 90), "flute": (60, 96)}            # written: low B♭ to high F♯ on saxophone; low C to high C on flute


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data"); ap.add_argument("repo"); ap.add_argument("--codes"); ap.add_argument("--check", action="store_true"); ap.add_argument("--links", action="store_true")
    A = ap.parse_args()
    spec = importlib.util.spec_from_file_location("etude_data", A.data); D = importlib.util.module_from_spec(spec); spec.loader.exec_module(D)
    V = dict(D.VOLUME); V.setdefault("series", "Blues Études"); V["slug_base"] = "%s%s" % (V.get("prefix", "be"), V["number"])
    editions = V.get("editions", ["alto", "tenor", "flute"]); sample = V.get("sample", [4])
    codes = json.load(open(A.codes)) if A.codes else {}
    ip = os.path.join(A.repo, "index.json"); idx = json.load(open(ip))
    problems, wrote = [], 0
    for ed in editions:
        tunes = []
        for e in D.ETUDES:
            try:
                tune, (lo, hi) = build(e, V, ed)
            except AssertionError as err:
                problems.append(str(err)); continue
            if lo < RANGE[ed][0] or hi > RANGE[ed][1]: problems.append("%s: written range %d-%d is outside the instrument (%d-%d)" % (tune["slug"], lo, hi, *RANGE[ed]))
            tunes.append(tune)
        if A.links:
            for t in tunes: print("%s\thttps://alexattardmusic.com/play/?t=%s" % (t["title"], t["slug"]))
            continue
        if A.check or problems: continue
        assert ed in codes and codes[ed].get("code"), "codes.json has no code for the %s edition" % ed
        entries = [("%s-%s" % (V["slug_base"], ed), "%s Vol. %s · %s" % (V["series"], V["number"], SHORT[ed]), codes[ed]["code"], tunes)]
        if codes[ed].get("sample"):
            entries.append(("%s-%s-sample" % (V["slug_base"], ed), "%s Vol. %s · Free Sample · %s" % (V["series"], V["number"], SHORT[ed]), codes[ed]["sample"],
                            [t for t, e in zip(tunes, D.ETUDES) if e["n"] in sample]))
        for pid, title, code, ts in entries:
            norm = re.sub(r"[^A-Z0-9]", "", code.upper()); h = hashlib.sha256(("aam:" + norm).encode()).hexdigest()
            clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == h and p["id"] != pid]
            assert not clash, "that code is already used by " + clash[0] + ": pick another"
            slugs = [t["slug"] for t in ts]
            idx["pdfs"] = [p for p in idx["pdfs"] if p["id"] != pid] + [dict(id=pid, title=title, hash=h, tunes=slugs, contents=[dict(title="", items=slugs)])]
            print("%s: %d études, first link https://alexattardmusic.com/play/?t=%s&c=<code>" % (title, len(slugs), slugs[0]))
        for t in tunes:
            json.dump(t, open(os.path.join(A.repo, "tunes", t["slug"] + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
            idx["tunes"][t["slug"]] = dict(title=t["title"], subtitle=t["subtitle"]); wrote += 1
    for p in problems: print("PROBLEM: " + p)
    if problems: sys.exit(1)
    if A.check: print("CHECK: %d études x %d editions build cleanly for the player" % (len(D.ETUDES), len(editions))); return
    if not A.links:
        json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
        print("wrote %d tunes and index.json. Next: node tools/check_release.js --only %s, then python3 tools/guard.py, commit and push." % (wrote, V["slug_base"] + "-"))


if __name__ == "__main__":
    main()
