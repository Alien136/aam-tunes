#!/usr/bin/env python3
"""Publish the Saxophone Welcome Booklet's exercises to the play-along library, one booklet per edition.

Usage: python3 book_player.py alto|tenor CODE /path/to/aam-tunes
Writes out/booklet_<edition>.json (also read by build_book.py for the QR codes), the tune files and index.json.
Scale-type exercises are written once, in written E♭ (the octave the booklet uses), and the player takes them through
the keys: the chromatic-order page starts on B♭ (start_key -5), the circle-of-fourths page on C (start_key -3).
"""
import json, os, re, subprocess, sys
ED, CODE, REPO = sys.argv[1], sys.argv[2], sys.argv[3]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], ED]
import build_book as B                                             # noqa: E402
import gen_study as g                                              # noqa: E402

BELOW = {"alto": 9, "tenor": 14}[ED]
PCS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
NAME = {"alto": "Alto", "tenor": "Tenor"}[ED]
PRE = "sax-welcome-" + ED + "-"
PDF = {"id": "sax-welcome-" + ED, "title": "Saxophone Welcome Booklet · " + NAME, "code": CODE}
DUR = {"8": .5, "4": 1, "4.": 1.5, "2": 2, "2.": 3, "2..": 3.5, "1": 4}


def concert(written_midi):
    return PCS[(written_midi - BELOW) % 12]


def midi(tok):
    m = re.match(r"^([a-g])((?:is|es)*)([',]*)", tok)
    acc = (len(m.group(2)) // 2) * (1 if "is" in m.group(2) else -1)
    return g.Note(m.group(1).upper(), acc, 3 + m.group(3).count("'") - m.group(3).count(",")).midi


def to_bars(ly):
    """A LilyPond string with a duration on every note -> one string per 4-beat bar."""
    bars, cur, t = [], [], 0.0
    for tok in ly.replace("|", " ").split():
        d = DUR[re.search(r"(\d+\.*)$", tok).group(1)]
        cur.append(tok); t += d
        if abs(t - 4) < 1e-9: bars.append(" ".join(cur)); cur, t = [], 0.0
    assert not cur, ly
    return bars


def scale_item(slug, title, page, order, pattern, alters, minor, desc, tempo=60):
    root = B.root_note("Eb")                                       # E♭4: twelve keys from here stay between low B♭ and high F
    rh = to_bars(pattern(root, alters).replace("\\break", ""))
    ck = concert(root.midi)
    return dict(slug=PRE + slug, title=title, page=page, style="drone", keys=order, start_key=-5 if order == "chromatic" else -3,
                tempo=tempo, concert_key=ck + ("m" if minor else ""), hide=["chords", "solo", "names"], tab="Notes", desc=desc,
                bars=[[ck + ("m6" if minor else "maj7")]] * len(rh), rh=rh)


def arp_item(slug, title, page, order):
    root = B.root_note("Eb")
    def bar(alters):
        t = [B.deg(root, d, alters).ly() + "8" for d in (1, 3, 5, 8, 5, 3)]
        return "(3 " + " ".join(t[:3]) + " (3 " + " ".join(t[3:]) + " " + root.ly() + "2"
    ck = concert(root.midi)
    return dict(slug=PRE + slug, title=title, page=page, style="drone", keys=order, start_key=-5 if order == "chromatic" else -3, tempo=60,
                concert_key=ck, hide=["chords", "solo", "names"], tab="Notes",
                desc="A major arpeggio, then the minor arpeggio on the same root, in triplets. Each time through moves to the next key.",
                bars=[[ck + "maj7"], [ck + "m6"]], rh=[bar(B.MAJOR), bar(B.HARM_MIN)])


def long_tone_item(slug, title, page, notes, desc):
    bars, rh = [], []
    for n in notes:
        c = concert(midi(n)); bars += [[c], [c]]; rh += [n + "1~", n + "2 " + n + "2"]
    c = concert(midi(notes[-1]))
    for _ in range(3): bars.append([c]); rh.append(notes[-1] + "1")
    return dict(slug=PRE + slug, title=title, page=page, style="drone", keys="off", tempo=60, concert_key=concert(midi(notes[0])), written_key="C",
                hide=["chords", "solo", "names"], tab="Notes", desc=desc, bars=bars, rh=rh)


DOWN = ["b'", "bes'", "a'", "aes'", "g'", "ges'", "f'", "e'", "ees'", "d'", "des'", "c'", "b", "bes"]
UP = ["b'", "c''", "cis''", "d''", "dis''", "e''", "f''", "fis''", "g''", "gis''", "a''", "ais''", "b''", "c'''", "cis'''", "d'''", "dis'''", "e'''", "f'''"]
CHROM_UP = ["bes", "b", "c'", "cis'", "d'", "dis'", "e'", "f'", "fis'", "g'", "gis'", "a'", "ais'", "b'", "c''", "cis''", "d''", "dis''", "e''", "f''",
            "fis''", "g''", "gis''", "a''", "ais''", "b''", "c'''", "cis'''", "d'''", "dis'''", "e'''", "f'''"]
CHROM_DOWN = ["e'''", "ees'''", "d'''", "des'''", "c'''", "b''", "bes''", "a''", "aes''", "g''", "ges''", "f''", "e''", "ees''", "d''", "des''", "c''",
              "b'", "bes'", "a'", "aes'", "g'", "ges'", "f'", "e'", "ees'", "d'", "des'", "c'", "b"]


def chromatic_item(page):
    rh = to_bars(" ".join(n + "8" for n in CHROM_UP + CHROM_DOWN) + " bes4")
    c = concert(midi("bes"))
    return dict(slug=PRE + "chromatic", title="Chromatic Scale", page=page, style="click", keys="off", tempo=60, concert_key=c, written_key="C",
                hide=["chords", "solo", "names"], tab="Notes", desc="Low B♭ to high F and back: sharps on the way up, flats on the way down.",
                bars=[[c]] * len(rh), rh=rh)


def lick_item(k, page, keys="off", slug=None, title=None, desc=None):
    num, name, d, music = B.LICKS[k]
    rh = []
    for bar in music.split("|"):                                   # sticky durations -> a duration on every note
        out, dur = [], "4"
        for tok in bar.split():
            m = re.search(r"(\d+\.*)$", tok)
            if m: dur = m.group(1)
            else: tok += dur
            out.append(tok)
        rh.append(" ".join(out))
    ck = concert(60)                                               # written C
    two, five = concert(62), concert(67)
    return dict(slug=PRE + (slug or "lick-" + num), title=title or "Lick " + num + " · " + name, page=page, style="swing", keys=keys, tempo=90,
                concert_key=ck, hide=["solo"], tab="Lick", desc=desc or d,
                bars=[[two + "m7"], [five + "7"], [ck + "maj7"], [ck + "maj7"]], rh=rh)


def page_map():
    """First page of each section, counted the way build_book.py assembles the book."""
    return dict(long=5, chrom=6, major=(7, 8), minor=(9, 10), th_maj=(11, 12), th_min=(13, 14), arps=(15, 16), fours=(17, 19), licks=21, transpose=22, blues=23)


def booklet():
    P = page_map()
    T = B.PARTS_TXT
    loop = " Each time through moves to the next key."
    orders = (("chromatic", "Chromatic order", "chr"), ("fourths", "Circle of fourths", "4ths"))
    def pair(key, slug, title, pattern, alters, minor, desc):
        return [scale_item(slug + "-" + s, title + " · " + oname, P[key][i], o, pattern, alters, minor, desc + loop) for i, (o, oname, s) in enumerate(orders)]
    return {"pdf": PDF, "instrument": ED, "contents": [
        {"title": "Part 1 · Long Tones", "items": [
            long_tone_item("long-tones-down", "Long Tones · Down to the bottom", P["long"], DOWN, "Middle B down to low B♭. Hold each note for six beats, breathe, then two more beats. Finish with three long low B♭s."),
            long_tone_item("long-tones-up", "Long Tones · Up to the top", P["long"], UP, "Middle B up to high F. Hold each note for six beats, breathe, then two more beats. Finish with three long high Fs.")]},
        {"title": "Part 2 · Chromatic Scale", "items": [chromatic_item(P["chrom"])]},
        {"title": "Part 3 · Scales", "items": pair("major", "major", "Major Scales", B.pat_scale, B.MAJOR, False, "Up to the 9th, back down to the root, then the note below it.")
            + pair("minor", "minor", "Harmonic Minor Scales", B.pat_scale, B.HARM_MIN, True, "Harmonic minor: up to the 9th, back to the root, then the raised 7th below.")},
        {"title": "Part 4 · Thirds", "items": pair("th_maj", "thirds-major", "Major Scales in Thirds", B.pat_thirds, B.MAJOR, False, "1-3, 2-4, 3-5 up to the 9th, then back down in thirds.")
            + pair("th_min", "thirds-minor", "Harmonic Minor in Thirds", B.pat_thirds, B.HARM_MIN, True, "The harmonic minor scale in thirds.")},
        {"title": "Part 5 · Arpeggios", "items": [arp_item("arpeggios-" + s, "Arpeggios · " + oname, P["arps"][i], o) for i, (o, oname, s) in enumerate(orders)]},
        {"title": "Part 6 · Four-Note Patterns", "items": pair("fours", "fours", "Four-Note Patterns", B.pat_fours, B.MAJOR, False, "1-2-3-4, 2-3-4-5 up to 6-7-8-9, then back down in fours.")},
        {"title": "Part 7 · ii–V–I Licks", "items": [lick_item(k, P["licks"]) for k in range(4)]
            + [lick_item(0, P["transpose"], keys="fourths", slug="lick-1-keys", title="Transposing a Lick · Lick 1 through the keys",
                         desc="Lick 1 in every key, round the circle of fourths. The page shows C, G, D, F and B♭: tap the key button to pick one.")]},
    ]}


def main():
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    spec = booklet()
    path = os.path.join(HERE, "out", "booklet_%s.json" % ED)
    # the blues pages: the same study the booklet prints, published as a tune and listed as the last chapter
    blues_slug = PRE + "blues"
    bspec = {"title": "Blues", "concert_key": "F", "instrument": ED, "tempo_text": "Medium Swing", "blues": True,
             "bars": [["F7"], ["Bb7"], ["F7"], ["Cm7", "F7"], ["Bb7"], ["Bb7"], ["F7"], ["Am7b5", "D7b9"], ["Gm7"], ["C7"], ["F7", "D7b9"], ["Gm7", "C7"]]}
    bpath = os.path.join(HERE, "out", "blues_spec_%s.json" % ED)
    json.dump(bspec, open(bpath, "w"))
    subprocess.run([sys.executable, os.path.join(HERE, "publish_tune.py"), bpath, REPO, "--slug", blues_slug, "--code", "TMP-" + CODE,
                    "--subtitle", PDF["title"] + " · 12-bar jazz blues", "--tempo", "120"], check=True)
    ip = os.path.join(REPO, "index.json")
    idx = json.load(open(ip)); idx["pdfs"] = [p for p in idx["pdfs"] if p["id"] != blues_slug]; json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    json.dump(spec, open(path, "w"), ensure_ascii=False, indent=1)
    subprocess.run([sys.executable, os.path.join(HERE, "publish_exercise.py"), path, REPO], check=True)
    idx = json.load(open(ip))
    for p in idx["pdfs"]:
        if p["id"] == PDF["id"]:
            p["tunes"].append(blues_slug); p["contents"].append({"title": "Part 7 · Blues", "items": [blues_slug]})
    t = json.load(open(os.path.join(REPO, "tunes", blues_slug + ".json"))); t["page"] = page_map()["blues"]
    json.dump(t, open(os.path.join(REPO, "tunes", blues_slug + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    # QR targets for build_book.py: page number -> slug
    P = page_map()
    qr = {P["long"]: PRE + "long-tones-down", P["chrom"]: PRE + "chromatic", P["licks"]: PRE + "lick-1", P["transpose"]: PRE + "lick-1-keys", P["blues"]: blues_slug}
    for key, slug in (("major", "major"), ("minor", "minor"), ("th_maj", "thirds-major"), ("th_min", "thirds-minor"), ("arps", "arpeggios"), ("fours", "fours")):
        qr[P[key][0]] = PRE + slug + "-chr"; qr[P[key][1]] = PRE + slug + "-4ths"
    json.dump({"code": CODE, "first": PRE + "long-tones-down", "pages": qr}, open(os.path.join(HERE, "out", "qr_%s.json" % ED), "w"), indent=1)
    print("booklet published:", PDF["title"], CODE)


if __name__ == "__main__":
    main()
