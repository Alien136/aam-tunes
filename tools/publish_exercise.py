"""Publish a booklet (a PDF with several exercises) to the play-along tune folder.

Usage: python3 publish_exercise.py booklet.json /path/to/aam-tunes
Writes one tunes/<slug>.json per exercise and one PDF entry, with its chapters, in index.json. Then commit and push.
Needs gen_study.py in the same folder (for chord scales and transposition).

booklet.json:
{
  "pdf": {"id": "sax-welcome-alto", "title": "Saxophone Welcome Booklet · Alto", "code": "SW-1234"},
  "instrument": "alto",                      # alto | tenor | soprano | bari | clarinet | trumpet | flute | concert | piano (single staff only)
  "contents": [
    {"title": "Long Tones", "items": [
      {"slug": "sax-welcome-alto-long-tones", "title": "Long Tones", "page": 3,
       "style": "drone",                     # "drone": held root + fifth and a click. "click": a click only. "swing": the band.
       "keys": "off",                        # "off" | "chromatic" (up a half step each time) | "fourths" (round the circle)
       "start_key": -5,                      # optional: begin this many semitones from the written key (-5 .. 6), e.g. a booklet page that starts on B♭
       "tempo": 60, "concert_key": "D",       # add "written_key": "C" for an exercise that should have no key signature
       "hide": ["chords", "solo", "names"],  # what the exercise has no use for: the chord chart, the blank solo page, chord names over the notes
       "tab": "Notes",                       # name of the notation tab
       "bars": [["D"], ["D"]],               # CONCERT chords, one or two per bar (what the drone or band plays)
       "rh": ["b'1~", "b'2 r2"]}             # the WRITTEN notes on the student's page, one string per bar (LilyPond pitches:
    ]}                                       #   c' = middle C; durations 1 2 4 8, dotted 2. 4.; r = rest; ~ = tie to the next note; "(3" before three eighth notes = a triplet)
  ]
}
The QR on each page: https://alexattardmusic.com/play/?t=<slug>&c=<code without the dash>. One code unlocks the whole booklet.
"""
import json, os, re, sys, hashlib
import gen_study as g

SOUNDS_BELOW = {"alto": 9, "bari": 21, "tenor": 14, "soprano": 2, "clarinet": 2, "trumpet": 2, "flute": 0, "concert": 0, "piano": 0}
SHORT = {"alto": "Alto Sax", "bari": "Bari Sax", "tenor": "Tenor Sax", "soprano": "Soprano Sax", "clarinet": "Clarinet", "trumpet": "Trumpet",
         "flute": "Flute", "concert": "Concert Pitch", "piano": "Piano"}
NOTE = re.compile(r"^([a-g])((?:is|es)*)([',]*)(\d+\.*)?(~)?$")
DUR = {"8": .5, "4": 1.0, "4.": 1.5, "2": 2.0, "2.": 3.0, "2..": 3.5, "1": 4.0}
LEN = {0.5: "", 1.0: "2", 1.5: "3", 2.0: "4", 3.0: "6", 3.5: "7", 4.0: "8"}
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


def build_item(it, inst, pdf_title, chapter):
    steps, semis, _ = g.INSTRUMENTS[inst]
    ck = it["concert_key"]; minor = ck.endswith("m"); kn = g.parse_note(ck.rstrip("m"))
    wk = g.transpose(kn, steps, semis)
    if it.get("written_key"): wk = g.parse_note(it["written_key"].rstrip("m"))    # e.g. "C" for a chromatic exercise that wants no key signature
    sp = Abc(keysig(wk, minor))
    flat = [(sym, 4 // len(b)) for b in it["bars"] for sym in b]
    assert len(it["rh"]) == len(it["bars"]), (it["slug"], "one rh string per bar")
    bars, i = [], 0
    for b in it["bars"]:
        row = []
        for sym in b:
            r, kind, _ = g.parse_chord(sym)
            nr, nk, _ = g.parse_chord(flat[(i + 1) % len(flat)][0])
            scale = g.choose_scale(kind, r, (nr, nk), kn.pc, minor)
            alters, _ct = g.SCALES[scale]
            row.append(dict(sym=sym, beats=4 // len(b), root=r.pc, degs=[g.MAJOR_STEPS[d] + alters[d] for d in range(7)], scale=scale))
            i += 1
        bars.append(row)
    ev, abc, marks, held = [], [], [], None
    for bi, text in enumerate(it["rh"]):
        sp.bar(); t, s, mk, dur, trip, fresh = 0.0, "", "", None, 0, False
        for tok in text.split():
            if tok == "(3":                                              # the next three eighth notes are a triplet (one beat)
                s += (" " if s and not s.endswith(" ") else "") + "(3"; trip, fresh = 3, True; continue
            m = re.match(r"^r(\d+\.?)$", tok)
            if m:
                s += " z" + LEN[DUR[m.group(1)]] + " "; t += DUR[m.group(1)]; held = None; continue
            m = NOTE.match(tok); assert m, (it["slug"], tok)
            if m.group(4): dur = m.group(4)
            acc = (len(m.group(2)) // 2) * (1 if "is" in m.group(2) else -1)
            n = g.Note(m.group(1).upper(), acc, 3 + m.group(3).count("'") - m.group(3).count(","))
            d = DUR[dur]
            if trip: assert d == 0.5, (it["slug"], "triplets are eighth notes"); d = 1 / 3
            sounding = n.midi - SOUNDS_BELOW[inst]
            if s and not s.endswith(" ") and not trip and (d >= 1 or t == 2.0 or s[-1].isdigit() or s[-1] == "-"): s += " "   # eighths beam in pairs of beats; longer notes stand alone
            s += sp.note(n) + ("" if trip else LEN[d]) + ("-" if m.group(5) else ""); mk += "."
            if trip:
                trip -= 1
                if not trip: s += " "
            if held and held[1] == sounding: held[2] += d                 # the second half of a tie: one long sound
            else: held = [bi * 4 + t, sounding, d, 90]; ev.append(held)
            if not m.group(5): held = None
            t = round(t + d, 6)
        assert abs(t - 4) < 1e-5, (it["slug"], "bar %d is %s beats long" % (bi + 1, t))
        abc.append(" ".join(s.split())); marks.append(mk)
    tab = it.get("tab", "Notes")
    sec = dict(id="notes", title=tab, tab=tab, desc=it.get("desc", "").rstrip("."), rh=ev, lh=[], abc=dict(rh=abc, marks=marks))
    T = it.get("tempo", 80)
    tune = dict(format="aam-tune/1", slug=it["slug"], title=it["title"], subtitle=it.get("subtitle") or (pdf_title + (" · " + chapter if chapter and chapter != it["title"] else "")),
                instrument=inst, concert_key=ck, native=semis % 12, style=it.get("style", "click"), keys=it.get("keys", "off"), hide=it.get("hide", ["solo"]),
                first_bar=1, chart_tempo=T, tempo_presets=[T, min(T + 20, 200), min(T + 40, 220)], form=[], bars=bars, sections=[sec],
                notation=dict(key=ascii_name(wk) + ("m" if minor else ""), staves="treble"))
    if it.get("page"): tune["page"] = it["page"]
    if it.get("start_key"): tune["start_key"] = it["start_key"]     # semitones from the written key where the exercise begins (-5 .. 6)
    return tune


def main(spec_path, repo):
    spec = json.load(open(spec_path)); inst = spec.get("instrument", "alto"); pdf = spec["pdf"]
    os.makedirs(os.path.join(repo, "tunes"), exist_ok=True)
    ip = os.path.join(repo, "index.json")
    idx = json.load(open(ip)) if os.path.exists(ip) else dict(format="aam-index/1", owner="aam", pdfs=[], tunes={})
    norm = re.sub(r"[^A-Z0-9]", "", pdf["code"].upper())
    h = hashlib.sha256(("aam:" + norm).encode()).hexdigest()
    clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == h and p["id"] != pdf["id"]]
    assert not clash, "that code is already used by " + clash[0]
    contents, slugs = [], []
    for ch in spec["contents"]:
        items = []
        for it in ch["items"]:
            tune = build_item(it, inst, pdf["title"], ch.get("title", ""))
            json.dump(tune, open(os.path.join(repo, "tunes", it["slug"] + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
            idx["tunes"][it["slug"]] = dict(title=tune["title"], subtitle=tune["subtitle"])
            items.append(it["slug"]); slugs.append(it["slug"])
            print("  %s  ->  https://alexattardmusic.com/play/?t=%s&c=%s" % (it["title"], it["slug"], norm))
        contents.append(dict(title=ch.get("title", ""), items=items))
    idx["pdfs"] = [p for p in idx["pdfs"] if p["id"] != pdf["id"]] + [dict(id=pdf["id"], title=pdf["title"], hash=h, tunes=slugs, contents=contents)]
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    print("wrote %d exercises for %s (code %s)" % (len(slugs), pdf["title"], pdf["code"].upper()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
