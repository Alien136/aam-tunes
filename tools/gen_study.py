#!/usr/bin/env python3
"""Generate a chord/scale study lead sheet (LilyPond) from concert chord changes.

Usage: python3 gen_study.py spec.json out.ly
Spec keys:
  title, subtitle (optional), concert_key ("F" major / "Gm" minor),
  instrument: alto | tenor | soprano | bari | clarinet | trumpet | flute | piano | concert
  tempo_text (e.g. "Medium Swing"), blues (bool: adds blues scale), home_scale (bool: adds the key's scale),
  form: optional [["A", 1], ["B", 17], ...] rehearsal letters at bar numbers,
  bars: list of bars in 4/4, each a list of 1 chord (whole bar) or 2 chords (two beats each), concert pitch.
  recordings: optional list of {"artist", "album", "year", "note"}, printed as a "Listen" list after Section 2.
  staff_size, text_size (pt), s2_text_size (pt), s2_staff_size: optional sizes; fit_study.py sets the first three.
  lh_voicing (piano): "guide" (default: 3rd + 7th, lower note C3-Ab3) | "root7" (root + 7th, root G2-F#3).
  original_tune: {"composer", "similar_tune", "why"} for an original chart with no findable recordings: the Listen
    section says so and presents the recordings as versions of similar_tune.
  listen_explainer / search_hint: optional overrides for the Listen explainer text.
  target_pages (fit_study), s1_split / s3_split (bar number that starts page 2 of Section 1 / 3), s1_staff_size,
    s3_staff_size: long piano tunes.
  licks ({"id", "label", "bars", "rh", "res"}; "rh" may be a list of bars for a multi-bar lick), lick_groups, lick_chorus, licks_intro, lick_chorus_note, licks_practice ([[step, text], ...]), licks_text_size, s4_staff_size,
    s5_split, s5_staff_size: adds "ii-V-I Licks" and "Lick Chorus" sections (piano or woodwinds; woodwinds get the licks
    transposed). lick_chorus_choruses (default 1; 2 adds a final bar so a lick can resolve over the turnaround);
    licks_after_your_chorus (default false: licks are Sections 4-5 and Your Chorus is 6; true: Your Chorus stays 4).
  practice_tip: optional replacement for the closing practice tip.
  fill_pages: true spreads every page's systems to the bottom margin (use with the lick pages).
  s3_mode: "auto" (default: pattern chorus when half or more of the bars hold two chords) | "scale" | "pattern".
Chord qualities: maj7 6 7 9 13 7b9 m7 m9 m6 m7b5 (also M7 ^7 -7 ø, and m = minor 7th).
"""
import json, re, sys

LETTERS = "CDEFGAB"
NAT = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]

INSTRUMENTS = {  # (letter steps, semitones) from concert up to written, label
    "alto": (5, 9, "E♭ Alto Saxophone"),
    "bari": (5, 9, "E♭ Baritone Saxophone"),
    "tenor": (1, 2, "B♭ Tenor Saxophone"),
    "soprano": (1, 2, "B♭ Soprano Saxophone"),
    "clarinet": (1, 2, "B♭ Clarinet"),
    "trumpet": (1, 2, "B♭ Trumpet"),
    "concert": (0, 0, "Concert Pitch (C instruments)"),
    "flute": (0, 0, "Flute"),
    "piano": (0, 0, "Piano"),
}


class Note:
    def __init__(self, letter, acc, octave=4):
        self.letter, self.acc, self.octave = letter, acc, octave

    @property
    def pc(self):
        return (NAT[self.letter] + self.acc) % 12

    @property
    def midi(self):
        return 12 * (self.octave + 1) + NAT[self.letter] + self.acc

    def name(self):
        return self.letter + {-2: "𝄫", -1: "♭", 0: "", 1: "♯", 2: "𝄪"}[self.acc]

    def ly(self):
        s = self.letter.lower() + ("is" * self.acc if self.acc > 0 else "es" * -self.acc)
        d = self.octave - 3
        return s + ("'" * d if d > 0 else "," * -d)


def parse_note(s):
    letter, rest = s[0].upper(), s[1:]
    acc = rest.count("#") - rest.count("b")
    return Note(letter, acc)


def transpose(n, steps, semis):
    li = LETTERS.index(n.letter) + steps
    letter, oct_shift = LETTERS[li % 7], li // 7
    target = NAT[n.letter] + n.acc + semis
    acc = target - (NAT[letter] + 12 * oct_shift)
    return Note(letter, acc, n.octave + oct_shift)


def spell_degree(root, degree, alter):
    """Return Note for scale degree (1-7) of root with alteration (relative to major), octave relative to root."""
    li = LETTERS.index(root.letter) + degree - 1
    letter, oshift = LETTERS[li % 7], li // 7
    target = NAT[root.letter] + root.acc + MAJOR_STEPS[degree - 1] + alter
    acc = target - (NAT[letter] + 12 * oshift)
    return Note(letter, acc, root.octave + oshift)


# quality -> (lily chordmode suffix, kind)
QUALITIES = {
    "maj7": (":maj7", "maj7"), "M7": (":maj7", "maj7"), "^7": (":maj7", "maj7"), "6": (":6", "maj6"), "": ("", "maj7"),
    "7": (":7", "dom7"), "9": (":9", "dom7"), "13": (":13", "dom7"), "7b9": (":7.9-", "dom7"),
    "m7": (":m7", "min7"), "-7": (":m7", "min7"), "m9": (":m9", "min7"), "m": (":m", "min7"),
    "m6": (":m6", "min6"), "m7b5": (":m7.5-", "half"), "ø": (":m7.5-", "half"),
}

SCALES = {  # name -> list of alterations for degrees 1..7, chord-tone degrees
    "Ionian (major)": ([0, 0, 0, 0, 0, 0, 0], [1, 3, 5, 7]),
    "Lydian": ([0, 0, 0, 1, 0, 0, 0], [1, 3, 5, 7]),
    "Natural minor": ([0, 0, -1, 0, 0, -1, -1], [1, 3, 5, 7]),
    "Mixolydian": ([0, 0, 0, 0, 0, 0, -1], [1, 3, 5, 7]),
    "Dorian": ([0, 0, -1, 0, 0, 0, -1], [1, 3, 5, 7]),
    "Melodic minor": ([0, 0, -1, 0, 0, 0, 0], [1, 3, 5, 6]),
    "Locrian": ([0, -1, -1, 0, -1, -1, -1], [1, 3, 5, 7]),
    "Phrygian dominant": ([0, -1, 0, 0, 0, -1, -1], [1, 3, 5, 7]),
    "Harmonic minor": ([0, 0, -1, 0, 0, -1, 0], [1, 3, 5, 7]),
}

EXPLAIN = {
    "Mixolydian": "a major scale with a lowered 7th, which matches the ♭7 of a dominant chord.",
    "Dorian": "a minor scale with a natural 6th. The bright, smooth minor sound for ii chords.",
    "Ionian (major)": "the plain major scale. Lean on 3 and 7 and treat 4 as a passing note.",
    "Melodic minor": "a minor scale with a natural 6th and 7th. The classic sound for a tonic minor 6 chord.",
    "Locrian": "the half-diminished sound (lowered 2, 3, 5, 6 and 7). Used on the ii chord of a minor ii–V.",
    "Lydian": "a major scale with a raised 4th. The natural sound of a major 7 chord built on IV (or ♭VI in a minor key).",
    "Phrygian dominant": "for a dominant chord that resolves to a minor chord. Its ♭9 and ♭13 pull you into the next chord.",
    "Harmonic minor": "minor with a raised 7th.",
}


def parse_chord(sym):
    i = 1
    while i < len(sym) and sym[i] in "#b":
        i += 1
    root, qual = parse_note(sym[:i]), sym[i:]
    if qual not in QUALITIES:
        raise ValueError(f"Unsupported chord quality in '{sym}'")
    suffix, kind = QUALITIES[qual]
    return root, kind, suffix


def choose_scale(kind, root, nxt, key_pc=None, minor=False):
    if kind == "maj7" and key_pc is not None and (root.pc - key_pc) % 12 == (8 if minor else 5):
        return "Lydian"
    if kind == "dom7" and nxt is not None:
        nroot, nkind = nxt
        if nkind in ("min7", "min6", "half") and (nroot.pc - root.pc) % 12 == 5:
            return "Phrygian dominant"
    return {"maj7": "Ionian (major)", "maj6": "Ionian (major)", "dom7": "Mixolydian", "min7": "Dorian",
            "min6": "Melodic minor", "half": "Locrian", "dim7": "Harmonic minor"}[kind]


def place_root(root):
    """Put the root so it sits between written D4 and C#5 (comfortable for every instrument here)."""
    n = Note(root.letter, root.acc, 4)
    while n.midi < 62:
        n.octave += 1
    while n.midi > 73:
        n.octave -= 1
    return n


def scale_notes(root, scale):
    alters, ctones = SCALES[scale]
    notes = [spell_degree(root, d, alters[d - 1]) for d in range(1, 8)]
    top = Note(root.letter, root.acc, root.octave + 1)
    return notes + [top], ctones


# Left-hand voicings (piano): two notes, kept clear of the low register.
# Research basis:
# - Reach (PASK / Boyle, Boyle & Booker 2015): an octave needs about a 21.6 cm hand span and adult women average
#   20.1 cm, so student left hands never stretch an octave. Both modes below stay within a 7th.
# - Mud (arranging "low interval limits"): close intervals turn muddy when they sit too low. Lowest note for each
#   interval: m3 C3, M3 Bb2, P4 Bb2, tritone B2, P5 Bb1, m6 G2, M6/m7/M7 F2. Root + 3rd shells break these limits
#   in the usual left-hand register (F2-A2, A2-C3), so they are not used.
# - Guide tones (3rd + 7th) sound best in the middle register, about C3 to C5, and are the standard two-note
#   left hand when a bass player covers the root.
#   "guide" (default): 3rd + 7th, alternating 3-7 and 7-3 so they move by half step or stay put. Lower note C3-Ab3.
#   "root7": root + 7th (6th on a m6 chord), root G2-F#3. For solo practice without a bass; the right hand has the 3rd.
LH_VOICING = "guide"
LOW_LIMIT = {3: 48, 4: 46, 5: 46, 6: 47, 7: 34, 8: 43, 9: 41, 10: 41, 11: 41}  # interval (semitones) -> lowest MIDI


def shell_voicings(flat):
    """Two-note left-hand voicings, voice-led so the notes move as little as possible."""
    prev = None
    for c in flat:
        alters, ct = SCALES[c["scale"]]
        r = Note(c["root"].letter, c["root"].acc, 2)
        third = spell_degree(r, ct[1], alters[ct[1] - 1])
        seventh = spell_degree(r, ct[3], alters[ct[3] - 1])
        options = []
        if LH_VOICING == "guide":
            for o in range(-2, 4):
                t = Note(third.letter, third.acc, third.octave + o)
                sv = Note(seventh.letter, seventh.acc, seventh.octave + o)
                sv_down = Note(seventh.letter, seventh.acc, seventh.octave + o - 1)
                for v in ([t, sv], [sv_down, t]):
                    if 48 <= v[0].midi <= 56:
                        options.append(v)
        elif LH_VOICING == "root7":
            for o in range(-1, 3):
                rr = Note(r.letter, r.acc, r.octave + o)
                if 43 <= rr.midi <= 54:
                    options.append([rr, Note(seventh.letter, seventh.acc, seventh.octave + o)])
        else:
            raise ValueError(f"lh_voicing must be 'guide' or 'root7', not {LH_VOICING!r}")
        if prev is None:
            best = min(options, key=lambda v: abs(v[0].midi - 50))
        else:
            best = min(options, key=lambda v: abs(v[0].midi - prev[0].midi) + abs(v[1].midi - prev[1].midi))
        span = best[1].midi - best[0].midi
        assert 0 < span <= 11, (c["root"].name(), [n.ly() for n in best])
        assert best[0].midi >= LOW_LIMIT.get(span, 41), ("too low, will sound muddy", c["root"].name(), [n.ly() for n in best])
        c["shell"] = best
        prev = best


LH_SHORT = {  # the left-hand line of the Section 1 note (one line)
    "guide": "guide tones, the 3rd and 7th. They hold or move a half step.",
    "root7": "the root and 7th. The right hand has the 3rd.",
}
GUIDE_RGB = "(rgb-color 0.05 0.47 0.73)"   # Your Chorus guide-tone line and the ii-V-I lesson (blue; licks are orange)

LH_TEXT = {
    "guide": "Left hand: guide tones, the 3rd and 7th of each chord (the two notes that make it major, minor or dominant), held through the chord. They move by a half step or stay put from chord to chord. The bass player covers the root.",
    "root7": "Left hand: the root and 7th of each chord, held through the chord. The right hand supplies the 3rd.",
}


def lily_note(n, dur, grey=False):
    s = n.ly() + dur
    if grey:
        s = "\\tweak color #grey \\tweak Accidental.color #grey " + s
    return s


TEXT_PT = 11     # body text size (pt) for Sections 1, 3, 4; set per build from the spec
S2_TEXT_PT = 11  # body text size (pt) for the Section 2 page (scale notes + recordings)


def ww(bold, text, italic=False, pt=None):
    q = lambda t: " ".join('"%s"' % w.replace('"', '\\"') for w in t.split())
    b = f"\\bold {{ {q(bold)} }} " if bold else ""
    body = f"\\italic {{ {q(text)} }}" if italic else q(text)
    return f"\\abs-fontsize #{pt or TEXT_PT} \\wordwrap {{ {b}{body} }}"


def heading(text, pt=None):
    return f'\\abs-fontsize #{(pt or TEXT_PT) + 5} \\bold "{text}"'



def listen_block(spec):
    """'Recordings to check out': numbered list of {artist, album, year, note}."""
    recs = spec.get("recordings") or []
    if not recs:
        return ""
    q = lambda t: " ".join('"%s"' % w.replace('"', '\\"') for w in t.split())
    rows = []
    for i, r in enumerate(recs, start=1):
        head = q(str(i) + ". " + r["artist"] + " —")
        album = q(r["album"])
        year = q("(" + str(r["year"]) + ").")
        note = q(r.get("note", ""))
        rows.append(f"\\abs-fontsize #{S2_TEXT_PT} \\wordwrap {{ \\bold {{ {head} }} \\italic {{ {album} }} {year} {note} }}")
    body = "\n  \\vspace #0.3\n  ".join(rows)
    hint = spec.get("search_hint") or f"the artist's name plus \"{spec['title']}\""
    orig = spec.get("original_tune")
    if orig:
        hint = f"the artist's name plus \"{orig['similar_tune']}\""
        by = f" by {orig['composer']}" if orig.get("composer") else ""
        spec.setdefault("listen_explainer",
            f"{spec['title']} is an original tune{by}, and no recordings of it could be found. {orig['why']} "
            f"These are recordings of \"{orig['similar_tune']}\" to learn the sound from: search {hint} on YouTube, Spotify, Apple Music "
            "or any streaming service. Listen through once for the feel, then listen to how the soloist plays over the chords that match your tune.")
    explainer = spec.get("listen_explainer") or (f"Find these on YouTube, Spotify, Apple Music or any streaming service: search {hint}. "
                 "Listen through once just for the feel, then play the "
                 "Section 1 arpeggios along with the recording and notice how the soloist uses the same chord tones.")
    return f'''\\markup \\column {{
  \\vspace #1.4
  \\override #'(thickness . 1.5) \\draw-hline
  \\fill-line {{ \\line {{ {heading(f"Listen: {len(recs)} Recordings of {orig['similar_tune']}" if orig else f"Listen: {len(recs)} Recordings to Check Out", S2_TEXT_PT)} }} \\null }}
  \\vspace #0.2
  {ww("", explainer, italic=True, pt=S2_TEXT_PT)}
  \\vspace #0.5
  {body}
}}'''


LICK_RGB = "(rgb-color 0.78 0.42 0.05)"
SCALE_PATTERN_TEXT = ("One-bar chords run their whole scale from the root up, 8 notes. Two-beat chords are too quick for a whole scale, "
                      "so they play the 1-2-3-5 pattern: root, 2nd, 3rd and 5th of the scale. It outlines the chord, skips the 4th (the note "
                      "that clashes most) and leaves you a step or two from the next chord. Where 1-2-3-5 would repeat a note across the "
                      "change, it runs 5-3-2-1 instead.")
PATTERN_TEXT = ("The chords here change every two beats, which is too fast to run a whole scale: playing 1-2-3-4 would often land "
                "on the next chord's root and repeat it. So each two-beat chord gets the 1-2-3-5 pattern: root, 2nd, 3rd and 5th of its "
                "scale. It outlines the chord, skips the 4th (the note that clashes most), and leaves you a step or two from the next "
                "chord, so the line never stops on a repeated note. Where 1-2-3-5 would still repeat a note, it runs 5-3-2-1 instead. "
                "Chords that last a whole bar get the full scale.")


LAST = {}  # the last build's per-bar music (concert for piano), used by playalong.py

LY_NOTE = re.compile(r"^([a-g])((?:is|es)*)([',]*)\d*\.*~?$")


def ly_mean_midi(music):
    """Average MIDI pitch of the plain notes in a LilyPond string (absolute octaves, c' = C4)."""
    vals = []
    for tok in music.split():
        m = LY_NOTE.match(tok)
        if m:
            pc = NAT[m.group(1).upper()] + len(m.group(2)) // 2 * (1 if "is" in m.group(2) else -1)
            vals.append(48 + pc + 12 * (m.group(3).count("'") - m.group(3).count(",")))
    return sum(vals) / len(vals)


def ii_v_i_lesson(kroot, minor, key_ly):
    """'How the changes connect': the ii-V-I of the home key as two guide-tone voices (written pitch).
    Upper voice 7 -> 3 -> 1: the ii's 7th falls to the V's 3rd, which climbs a half step to the root of I.
    Lower voice 3 -> 7 -> 3: the ii's 3rd holds as the V's 7th, which falls a step to the 3rd of I."""
    t = place_root(kroot)
    ii, v = spell_degree(t, 2, 0), spell_degree(t, 5, 0)
    if minor:
        ii_alt, ii_sym, i_sym, i3 = SCALES["Locrian"][0], ":m7.5-", ":m6", -1
    else:
        ii_alt, ii_sym, i_sym, i3 = SCALES["Dorian"][0], ":m7", ":maj7", 0
    dom = SCALES["Mixolydian"][0]
    up = [spell_degree(ii, 7, ii_alt[6]), spell_degree(v, 3, dom[2]), Note(t.letter, t.acc, t.octave)]
    lo = [spell_degree(ii, 3, ii_alt[2]), spell_degree(v, 7, dom[6]), spell_degree(t, 3, i3)]

    def near(n, ref):
        n = Note(n.letter, n.acc, n.octave)
        while n.midi - ref > 6:
            n.octave -= 1
        while ref - n.midi > 6:
            n.octave += 1
        return n
    u0 = Note(up[0].letter, up[0].acc, up[0].octave)
    while u0.midi < 67:
        u0.octave += 1
    while u0.midi > 77:
        u0.octave -= 1
    ups = [u0]
    for n in up[1:]:
        ups.append(near(n, ups[-1].midi))
    los = [near(lo[0], u0.midi - 5)]
    for n in lo[1:]:
        los.append(near(n, los[-1].midi))
    for a, b in zip(ups, los):
        while b.midi >= a.midi:
            b.octave -= 1
    lab = lambda txt, d: d + '\\markup \\abs-fontsize #9 \\bold \\with-color #' + GUIDE_RGB + ' "' + txt + '"'
    upper = " ".join(n.ly() + "1" + lab(x, "^") for n, x in zip(ups, ["7", "3", "1"]))
    lower = " ".join(n.ly() + "1" + lab(x, "_") for n, x in zip(los, ["3", "7", "3"]))
    bare = lambda n: n.ly().rstrip("',")
    chords = bare(ii) + "1" + ii_sym + " " + bare(v) + "1:7 " + bare(t) + "1" + i_sym
    return ("\\score {\n  << \\new ChordNames \\chordmode { " + chords + " }\n"
            "     \\new Staff { \\clef treble \\key " + key_ly + " \\omit Staff.TimeSignature \\override NoteHead.color = #" + GUIDE_RGB + "\n"
            "       << { \\voiceOne " + upper + ' \\bar "||" } \\\\ { \\voiceTwo ' + lower + " } >> } >>\n"
            "  \\layout { #(layout-set-staff-size 20) indent = 0 ragged-right = ##f \\context { \\Score \\omit BarNumber } }\n}")


def guide_targets(bars):
    """The guide tones of a chorus: one note on beat 1 and one on beat 4 of every bar.
    Each change from beat 4 into beat 1 moves by voice leading: the 7th falls a step to the next chord's 3rd, or, on a V-I,
    the 3rd climbs a half step to the root. Returns (arrive, depart): per bar, (Note, degree label) for beat 1 and for beat 4."""
    def tones(c):
        alters, ct = SCALES[c["scale"]]
        r = c["root"]
        return {"3": spell_degree(r, ct[1], alters[ct[1] - 1]), "7": spell_degree(r, ct[3], alters[ct[3] - 1]), "1": r}

    def place(n, ref, lo=62, hi=77):
        best = None
        for o in range(2, 7):
            m = Note(n.letter, n.acc, o)
            if lo <= m.midi <= hi and (best is None or abs(m.midi - ref) < abs(best.midi - ref)):
                best = m
        return best

    n = len(bars)
    arrive, depart = [None] * n, [None] * n   # (note, degree) on beat 1 / beat 4 of each bar
    for i in range(n):
        A, B = bars[i][-1], bars[(i + 1) % n][0]
        ta, tb = tones(A), tones(B)
        v_i = A["kind"] == "dom7" and (B["root"].pc - A["root"].pc) % 12 == 5
        here = arrive[i][0].midi if arrive[i] else 70
        best = None
        for da in ("3", "7"):
            a = place(ta[da], here)
            for db in ("3", "7") + (("1",) if v_i else ()):
                b = place(tb[db], a.midi)
                d = b.midi - a.midi
                if da == "7" and db == "3" and d in (-1, -2):
                    cost = 0            # 7 falls a step to the next 3rd
                elif da == "3" and db == "1" and d == 1:
                    cost = 0.05         # V-I: the 3rd climbs a half step to the root
                elif d == 0:
                    cost = 1.0          # common tone: allowed, but the lesson is the step
                else:
                    cost = 1 + 0.3 * abs(d)
                cost += 0.05 * abs(a.midi - here)   # a leap inside the bar is fine
                if best is None or cost < best[0]:
                    best = (cost, (a, da), (b, db))
        depart[i] = best[1]
        arrive[(i + 1) % n] = best[2]
    return arrive, depart


GUIDE_LAB = lambda txt: '^\\markup \\abs-fontsize #8 \\bold \\with-color #' + GUIDE_RGB + ' "' + txt + '"'


def guide_line(bars):
    """The older Your Chorus: the guide tones alone, the beats between left empty for the student ("sample_solo": false)."""
    arrive, depart = guide_targets(bars)
    n = len(bars)
    lab = lambda txt: '^\\markup \\abs-fontsize #8 \\bold \\with-color #' + GUIDE_RGB + ' "' + txt + '"'
    out = []
    for i in range(n):
        (a1, l1), (a4, l4) = arrive[i], depart[i]
        out.append("\\guideOn " + a1.ly() + "4" + lab(l1) + " s2 " + a4.ly() + "4" + lab(l4) + " \\guideOff |")
    return out


def sample_solo(bars, seed=""):
    """The Sample Solo (Alex, 23 Nov 2026): a written chorus that shows how a solo is built from the study's own material.
    Beat 1 and beat 4 of every bar are the guide tones (blue, as in guide_targets); beats 2 and 3 are filled in black:
    in the first half of the form from each chord's ARPEGGIO, in the second half from each chord's SCALE. The fill is
    chosen so the line moves by neighbours and arrives next to the beat-4 guide tone. Returns per-bar LilyPond."""
    import random
    arrive, depart = guide_targets(bars)
    n = len(bars); half = (n + 1) // 2
    rnd = random.Random("solo:" + seed)
    LO, HI = 59, 83

    def pool(c, arp):
        alters, ct = SCALES[c["scale"]]
        degs = ct if arp else range(1, 8)
        out = []
        for d in degs:
            x = spell_degree(c["root"], d, alters[d - 1])
            out += [Note(x.letter, x.acc, o) for o in range(2, 7)]
        return sorted((m for m in out if LO <= m.midi <= HI), key=lambda m: m.midi)

    # beats 2 and 3 as four eighth-note slots: (first slot, length in eighths), or ("r", length) for a rest
    RHY_ARP = [[(0, 1), (1, 1), (2, 1), (3, 1)], [(0, 1), (1, 1), (2, 2)], [(0, 1), (1, 1), (2, 1), (3, 1)], [("r", 1), (1, 1), (2, 1), (3, 1)],
               [(0, 1), (1, 1), (2, 1), (3, 1)], [(0, 2), (2, 1), (3, 1)], [(0, 1), (1, 1), (2, 1), (3, 1)], [("r", 2), (2, 1), (3, 1)]]
    RHY_SC = [[(0, 1), (1, 1), (2, 1), (3, 1)], [(0, 1), (1, 1), (2, 1), (3, 1)], [("r", 1), (1, 1), (2, 1), (3, 1)], [(0, 1), (1, 1), (2, 1), (3, 1)],
              [(0, 1), (1, 1), (2, 1), (3, 1)], [(0, 1), (1, 1), (2, 2)], [(0, 1), (1, 1), (2, 1), (3, 1)], [("r", 2), (2, 1), (3, 1)]]
    out = []
    for i, b in enumerate(bars):
        arp = i < half
        (a1, l1), (a4, l4) = arrive[i], depart[i]
        rhy = (RHY_ARP if arp else RHY_SC)[(i if arp else i - half) % 8]

        def chord_at(slot):                                  # slot 0..3 = the eighths of beats 2 and 3
            beat, t = 1 + slot // 2, 0
            for c in b:
                t += c["beats"]
                if beat < t: return c
            return b[-1]
        slots = [(st, ln) for st, ln in rhy if st != "r"]
        pools = [pool(chord_at(st), arp) for st, _ in slots]
        best = [None, None]

        def walk(k, cur, prev, cost, acc):
            if best[0] is not None and cost >= best[0]: return
            if k == len(slots):
                gap = abs(cur - a4.midi)
                end = 5 if gap == 0 else (0 if gap <= (4 if arp else 2) else 1.2 if gap <= (5 if arp else 4) else 4 + gap * 0.3)
                if best[0] is None or cost + end < best[0]: best[0], best[1] = cost + end, list(acc)
                return
            P = pools[k]
            up = [m for m in P if m.midi > cur][:2]; down = [m for m in P if m.midi < cur][-2:][::-1]
            for rank, m in [(0, x) for x in up[:1] + down[:1]] + [(1, x) for x in up[1:] + down[1:]]:
                c = cost + rank * (1.5 if arp else 1.2) + rnd.random() * 0.35
                if m.midi == a4.midi: c += 2                                  # do not land on the guide tone early
                if prev is not None and m.midi == prev: c += 0.9               # no see-saw between two notes
                if prev is not None and (m.midi - cur) * (cur - prev) < 0: c += 0.3
                if m.midi < 62 or m.midi > 79: c += 0.6
                walk(k + 1, m.midi, cur, c, acc + [m])
        walk(0, a1.midi, None, 0.0, [])
        fill, it = [], iter(best[1])
        for st, ln in rhy:
            d = {1: "8", 2: "4"}[ln]
            fill.append("r" + d if st == "r" else next(it).ly() + d)
        mark = ""
        if i == 0: mark = '_\\markup \\abs-fontsize #8 \\italic "arpeggio notes"'
        if i == half: mark = '_\\markup \\abs-fontsize #8 \\italic "scale notes"'
        out.append("\\guideOn " + a1.ly() + "4" + GUIDE_LAB(l1) + mark + " \\guideOff " + " ".join(fill) + " \\guideOn " + a4.ly() + "4" + GUIDE_LAB(l4) + " \\guideOff |")
    return out


def build_licks(spec, bars, arp_c, sc_c, chord_ly, music, lines, marked, steps, semis, kroot, minor, section,
                piano=True, lh=None, nums=("4", "5")):
    """ii-V-I licks in the tune's keys, then a Lick Chorus mixing arpeggios, scales/patterns and licks.
    Licks are written in concert pitch; woodwind editions transpose them to written pitch in a comfortable octave.
    lick_chorus_choruses > 1 writes that many choruses plus a final bar, so a lick can resolve across the turnaround."""
    global TEXT_PT
    saved_text_pt = TEXT_PT
    TEXT_PT = spec.get("licks_text_size") or TEXT_PT  # the lick pages can have their own text size
    licks = {L["id"]: L for L in spec["licks"]}
    lab = lambda t, size=8.5: f'\\abs-fontsize #{size} \\italic \\with-color #(rgb-color 0.45 0.45 0.45) "{t}"'
    llab = lambda t, size=9.5: f'\\abs-fontsize #{size} \\bold \\with-color #{LICK_RGB} "{t}"'

    def label(L):
        """Lick label; "{key}" becomes the written key of the chord the lick resolves to (e.g. Lick 1 in G for alto)."""
        if "{key}" not in L["label"]:
            return L["label"]
        r, kind, _ = parse_chord(L["bars"][-1][0])   # the chord it resolves to (the last bar, also for a multi-bar lick)
        return L["label"].replace("{key}", transpose(r, steps, semis).name())

    def lead(L):
        """The lick's bars before the resolution: one bar (a string) or several (a list, e.g. a two-bar long turnaround)."""
        return L["rh"] if isinstance(L["rh"], list) else [L["rh"]]

    def tr(L, part, m=None):
        """The lick's notes for this edition: concert for piano, transposed (octave chosen near the arpeggios) otherwise."""
        m = L[part] if m is None else m
        if piano:
            return m
        base = ly_mean_midi(" ".join(lead(L))) + semis
        o = min((-2, -1, 0, 1), key=lambda k: (abs(base + 12 * k - 70), abs(k)))
        t = transpose(Note("C", 0, 4), steps, semis)
        t.octave += o
        return f"\\transpose c' {t.ly()} {{ {m} }}"

    def chords_from(rows_syms):
        rows = []
        for bar in rows_syms:
            beats = 4 // len(bar)
            row = []
            for sym in bar:
                r, kind, suffix = parse_chord(sym)
                wr = transpose(r, steps, semis)
                row.append({"root": place_root(wr), "kind": kind, "suffix": suffix, "beats": beats})
            rows.append(row)
        fl = [c for b in rows for c in b]
        for i, c in enumerate(fl):
            nxt = fl[i + 1] if i + 1 < len(fl) else None
            c["scale"] = choose_scale(c["kind"], c["root"], (nxt["root"], nxt["kind"]) if nxt else None, kroot.pc, minor)
        if piano:
            shell_voicings(fl)
        return rows

    def lh_of(rows):
        return " ".join(" ".join("<" + " ".join(n.ly() for n in c["shell"]) + ">" + ("1" if len(b) == 1 else "2") for c in b) + " |" for b in rows)

    key_ly = kroot.ly().rstrip("',") + (" \\minor" if minor else " \\major")
    acc = "\\accidentalStyle Score.piano" if piano else "\\accidentalStyle Score.modern"
    common = f"\\clef treble \\key {key_ly} \\time 4/4 {acc}"
    s4_size = spec.get("s4_staff_size") or 17
    out = ["\\pageBreak", section(nums[0], spec.get("licks_title", "ii–V–I Licks"), spec.get("licks_intro", ""))]
    if spec.get("voice_leading", True):   # how a ii-V-I connects: 7 -> 3 and 3 -> 1, shown on the home key's ii-V-I
        rows_vl = [("How the changes connect:", "every chord has two guide tones, its 3rd and 7th."),
                   ("7 → 3:", "the 7th of each chord falls a step to the 3rd of the next."),
                   ("3 → 1:", "on the V–I, the 3rd of the V climbs a half step to the root of I."),
                   ("Listen for it:", "land on these notes at each change and your line spells out the harmony. Lick 1 does exactly this.")]
        out.append("\\markup \\column { " + " \\vspace #0.1 ".join(ww(b, t) for b, t in rows_vl) + " \\vspace #0.3 }")
        out.append(ii_v_i_lesson(kroot, minor, key_ly))
    for g in spec["lick_groups"]:
        rows_syms, rh, dyn = [], [], []
        for lid in g["items"]:
            L = licks[lid]
            rows_syms += L["bars"]
            bars_l = lead(L)
            assert len(L["bars"]) == len(bars_l) + 1, (L["id"], "bars must be the lead bars plus the target bar")
            rh += [("\\lickOn " if i == 0 else "") + tr(L, "rh", x) + " \\noBreak |" for i, x in enumerate(bars_l)]
            rh += [f"{tr(L, 'res')} \\lickOff r2 \\noBreak |"]  # each example stays on one line
            dyn += [f"s1^\\markup {llab(label(L))}"] + ["s1"] * len(bars_l)
        rows = chords_from(rows_syms)
        chords = " ".join(" ".join(chord_ly(c) for c in b) for b in rows)
        if piano:
            staves = (f'\\new PianoStaff << \\new Staff {{ {common} \\omit Staff.TimeSignature {" ".join(rh)} \\bar "||" }}\n'
                      f'                        \\new Staff {{ \\clef bass \\key {key_ly} \\omit Staff.TimeSignature {lh_of(rows)} }} >>')
        else:
            staves = f'\\new Staff {{ {common} \\omit Staff.TimeSignature {" ".join(rh)} \\bar "||" }}'
        out.append(f'''\\markup \\column {{ \\vspace #0.6 {ww(g["title"] + ":", g["note"])} \\vspace #0.2 }}
\\score {{
  << \\new ChordNames \\chordmode {{ {chords} }}
     \\new Dynamics {{ {" ".join(dyn)} }}
     {staves} >>
  \\layout {{ #(layout-set-staff-size {s4_size}) \\context {{ \\Score \\omit BarNumber }} }}
}}''')
    if spec.get("licks_practice"):  # optional practice steps under the licks
        steps_md = " ".join(f"\\vspace #0.25 {ww(h + ':', t)}" for h, t in spec["licks_practice"])
        out.append(f'''\\markup \\column {{ \\vspace #1.0 \\override #'(thickness . 1.2) \\draw-hline \\vspace #0.2
  \\abs-fontsize #{TEXT_PT + 2} \\bold "How to practise a lick" {steps_md} }}''')
    # the lick chorus: one or more choruses (plus a final bar when more than one)
    n = len(bars)
    nch = spec.get("lick_chorus_choruses", 1)
    first = dict(bars[0][0], beats=4)
    ext = [bars[i % n] for i in range(n * nch)] + ([[first]] if nch > 1 else [])
    ext_syms = [spec["bars"][i % n] for i in range(n * nch)] + ([[spec["bars"][0][0]]] if nch > 1 else [])
    ext_arp = [arp_c[i % n] for i in range(n * nch)] + ([[arp_c[0][0] + ("" if len(bars[0]) == 1 else " r2")]] if nch > 1 else [])
    ext_sc = [sc_c[i % n] for i in range(n * nch)] + ([[sc_c[0][0] + ("" if len(bars[0]) == 1 else " r2")]] if nch > 1 else [])
    ext_lh = None
    if piano:
        ext_lh = [lh[i % n] for i in range(n * nch)]
        if nch > 1:
            ext_lh.append("<" + " ".join(x.ly() for x in bars[0][0]["shell"]) + ">1 |")
    starts = {e["bar"]: e["lick"] for e in spec["lick_chorus"]}
    rh, dyn, free = [], [], 0
    b = 1
    while b <= len(ext):
        if b in starts:
            L = licks[starts[b]]
            bars_l = lead(L)
            k = len(bars_l)
            assert b - 1 + k < len(ext) and all(L["bars"][i] == ext_syms[b - 1 + i] for i in range(k)) \
                and L["bars"][k][0] == ext_syms[b - 1 + k][0], (b, L["id"], ext_syms[b - 1:b + k])
            for i, x in enumerate(bars_l):
                rh.append(f"\\lickOn {tr(L, 'rh', x)} \\lickOff |")
                dyn.append(f"s1^\\markup {llab(label(L))}" if i == 0 else "s1")
            r = b - 1 + k  # the resolution bar (0-based)
            if len(ext[r]) == 1:
                rh.append(f"\\lickOn {tr(L, 'res')} \\lickOff r2 |")
                dyn.append("s1")
            else:
                rh.append(f"\\lickOn {tr(L, 'res')} \\lickOff {ext_arp[r][1]} |")
                dyn.append(f"s2 s2^\\markup {lab('arp')}")
            b += k + 1
            continue
        use_arp = free % 2 == 0
        free += 1
        rh.append(" ".join((ext_arp if use_arp else ext_sc)[b - 1]) + " |")
        sc_label = "pattern" if (len(ext[b - 1]) == 2 and spec.get("_pattern_mode")) else "scale"
        dyn.append(f"s1^\\markup {lab('arp' if use_arp else sc_label)}")
        b += 1
    if nch > 1:  # the final bar joins the last line instead of sitting alone
        rh[-2:] = [rh[-2] + " " + rh[-1]]
        if ext_lh:
            ext_lh[-2:] = [ext_lh[-2] + " " + ext_lh[-1]]
    if nch > 1 and not spec.get("form"):
        for k in range(nch):
            rh[k * n] = (('\\bar "||" ' if k else "") + f'\\mark \\markup \\box \\bold "Chorus {k + 1}" ') + rh[k * n]
    chord_line = " ".join(" ".join(chord_ly(c) for c in row) + " |" for row in ext)
    s5_size = spec.get("s5_staff_size")
    s5_layout = f"\\layout {{ #(layout-set-staff-size {s5_size}) }}" if s5_size else ""
    out.append("\\pageBreak")
    out.append(section(nums[1], "Lick Chorus", spec.get("lick_chorus_note", "")))
    out.append(f'''\\score {{
  << \\new ChordNames \\chordmode {{ {chord_line} }}
     \\new Dynamics {{ {" ".join(dyn)} }}
     {music(rh, split=spec.get("s5_split"), lh_items=ext_lh)} >>
  {s5_layout}
}}''')
    TEXT_PT = saved_text_pt
    LAST.update(lick_rh=rh, lick_lh=ext_lh, lick_bars=ext)
    return "\n".join(out)


def build(spec):
    global TEXT_PT, S2_TEXT_PT, LH_VOICING
    LH_VOICING = spec.get("lh_voicing", "guide")
    TEXT_PT = spec.get("text_size") or 11
    S2_TEXT_PT = spec.get("s2_text_size") or TEXT_PT
    steps, semis, inst_label = INSTRUMENTS[spec.get("instrument", "alto")]
    # chords per bar, transposed
    bars = []
    for bar in spec["bars"]:
        beats = 4 // len(bar)
        row = []
        for sym in bar:
            r, kind, suffix = parse_chord(sym)
            wr = transpose(r, steps, semis)
            row.append({"root": place_root(wr), "kind": kind, "suffix": suffix, "beats": beats})
        bars.append(row)
    # key signature
    ck = spec["concert_key"]
    minor = ck.endswith("m")
    kroot = transpose(parse_note(ck.rstrip("m")), steps, semis)

    flat = [c for b in bars for c in b]
    for i, c in enumerate(flat):
        nxt = flat[(i + 1) % len(flat)]  # last chord turns around to the top
        c["scale"] = choose_scale(c["kind"], c["root"], (nxt["root"], nxt["kind"]) if nxt else None, kroot.pc, minor)
    key_ly = kroot.ly().rstrip("',") + (" \\minor" if minor else " \\major")
    key_name = kroot.name() + (" minor" if minor else "")

    def chord_ly(c):
        return c["root"].ly().rstrip("',") + str({4: 1, 2: 2, 1: 4}[c["beats"]]) + c["suffix"]

    changes = " ".join(" ".join(chord_ly(c) for c in b) + " |" for b in bars)

    # 1. arpeggios
    arp, arp_c = [], []
    for b in bars:
        out, per = [], []
        for c in b:
            notes, ct = scale_notes(c["root"], c["scale"])
            tones = [notes[d - 1] for d in ct]
            dur = {4: "4", 2: "8", 1: "8"}[c["beats"]]
            tones = tones if c["beats"] != 1 else tones[:2]
            out += [lily_note(n, dur) for n in tones]
            per.append(" ".join(lily_note(n, dur) for n in tones))
        arp_c.append(per)
        arp.append(" ".join(out) + " |")

    # 3. scale chorus / pattern chorus.
    # Slow changes (most chords a bar or longer): every chord's scale from the root (8 notes per bar, 4 per two beats).
    # Fast changes (half or more of the bars hold two chords): two-beat chords use the 1-2-3-5 pattern instead,
    # because 1-2-3-4 often ends on the next chord's root (F7 ... Bb into Bbm7) and there is no time for a whole scale.
    # If 1-2-3-5 would still repeat a note across the change, it runs 5-3-2-1. One-bar chords keep the full scale.
    mode = spec.get("s3_mode", "auto")
    two_beat_bars = sum(1 for b in bars if len(b) == 2)
    pattern_mode = mode == "pattern" or (mode == "auto" and two_beat_bars * 2 >= len(bars))
    flat_c = [c for b in bars for c in b]
    pieces, prev_last = [], None
    for idx, c in enumerate(flat_c):
        notes, ct = scale_notes(c["root"], c["scale"])
        if pattern_mode and c["beats"] == 2:
            nxt_first = flat_c[(idx + 1) % len(flat_c)]["root"].midi
            cands = [[1, 2, 3, 5], [5, 3, 2, 1]]
            ok = [d for d in cands if (prev_last is None or notes[d[0] - 1].midi != prev_last) and notes[d[-1] - 1].midi != nxt_first]
            degs = (ok or cands)[0]
        else:
            count = c["beats"] * 2
            degs = [(k % 7) + 1 for k in range(min(count, 8))]
            degs = [d if k < 7 else 8 for k, d in enumerate(degs)]
        seq = [(notes[d - 1], d) for d in degs]
        prev_last = seq[-1][0].midi
        pieces.append(" ".join(lily_note(n, "8", grey=(1 if d == 8 else d) not in ct) for n, d in seq))
    sc, sc_c, i = [], [], 0
    for b in bars:
        per = pieces[i:i + len(b)]
        i += len(b)
        sc_c.append(per)
        sc.append(" ".join(per) + " |")

    # 2. scale reference: one bar per unique (root, scale)
    seen, ref, ref_chords = [], [], []
    for c in flat:
        key = (c["root"].name(), c["scale"])
        if key in seen:
            continue
        seen.append(key)
        notes, ct = scale_notes(c["root"], c["scale"])
        ns = [lily_note(n, "8", grey=((i % 7) + 1) not in ct) for i, n in enumerate(notes)]
        ns[0] += f'^\\markup \\abs-fontsize #{S2_TEXT_PT} \\bold "{c["scale"]}"'
        ref.append(" ".join(ns) + " |")
        ref_chords.append(c["root"].ly().rstrip("',") + "1" + c["suffix"])
    if spec.get("home_scale"):
        t = place_root(kroot)
        hs = "Natural minor" if minor else "Ionian (major)"
        notes, ct = scale_notes(t, hs)
        ns = [lily_note(n, "8") for n in notes]
        ns[0] += f'^\\markup \\abs-fontsize #{S2_TEXT_PT} \\bold "{kroot.name()} {"natural minor" if minor else "major"} (whole tune)"'
        ref.append(" ".join(ns) + " |")
        ref_chords.append("s1")
        home_names = " ".join(n.name() for n in notes[:7])
    if spec.get("blues"):
        t = place_root(kroot)
        bl = [spell_degree(t, 1, 0), spell_degree(t, 3, -1), spell_degree(t, 4, 0), spell_degree(t, 4, 1),
              spell_degree(t, 5, 0), spell_degree(t, 7, -1), Note(t.letter, t.acc, t.octave + 1)]
        ns = [lily_note(n, "8") for n in bl[:-1]] + [lily_note(bl[-1], "4")]
        ns[0] += f'^\\markup \\abs-fontsize #{S2_TEXT_PT} \\bold "Blues scale (whole tune)"'
        ref.append(" ".join(ns) + ' \\bar "|."')
        ref_chords.append("s1")
    else:
        ref[-1] = ref[-1].rstrip("|") + ' \\bar "|."'

    form = {bar: label for label, bar in spec.get("form", [])}

    def marked(items):
        out = []
        for i, it in enumerate(items, start=1):
            pre = ""
            if i in form:
                if i > 1:
                    out[-1] = out[-1].rstrip("|").rstrip() + ' \\bar "||"'
                pre = f'\\mark \\markup \\box \\bold "{form[i]}" '
            out.append(pre + it)
        return out

    def lines(items, per=4, split=None):
        out = []
        for i in range(0, len(items), per):
            brk_cmd = " \\pageBreak" if (split and i + per == split - 1) else " \\break"
            out.append(" ".join(items[i:i + per]) + brk_cmd)
        return "\n  ".join(out)

    # explanations grouped by scale
    groups = {}
    for c in flat:
        sym = c["root"].name() + {"maj7": "maj7", "maj6": "6", "dom7": "7", "min7": "m7", "min6": "m6", "half": "m7♭5", "dim7": "°7"}[c["kind"]]
        groups.setdefault(c["scale"], [])
        if sym not in groups[c["scale"]]:
            groups[c["scale"]].append(sym)
    expl = []
    for sc_name, syms in groups.items():
        expl.append(ww(f'{", ".join(syms)} → {sc_name}:', EXPLAIN[sc_name], pt=S2_TEXT_PT))
    if spec.get("home_scale"):
        rel = transpose(kroot, 2, 3).name() + " major" if minor else ""
        extra = f" (same notes as {rel})" if minor else ""
        expl.append(ww(f"Whole tune → {kroot.name()} {'natural minor' if minor else 'major'} ({home_names}){extra}:",
                       "most of the tune lives in this one key, so it is your safe home base.", pt=S2_TEXT_PT))
    if spec.get("blues"):
        b = " ".join(n.name() for n in bl[:-1])
        expl.append(ww(f"Whole tune → {kroot.name()} blues scale ({b}):", "the bluesy sound; works over every bar.", pt=S2_TEXT_PT))

    concert = parse_note(ck.rstrip("m")).name() + (" minor" if minor else "")
    subtitle = spec.get("subtitle") or f"{inst_label} · written in {key_name} (concert {concert})"
    title = spec["title"]
    tempo = spec.get("tempo_text", "Medium Swing")

    def section(num, head, note, pt=None):
        """Section heading plus a short note: a string, or a list of (bold lead, text) lines, one per line."""
        rows_ = note if isinstance(note, list) else [("", note)]
        body = " \\vspace #0.1 ".join(ww(b, t, pt=pt) for b, t in rows_ if b or t)
        return f'''\\markup \\column {{
  \\vspace #1.2
  \\override #'(thickness . 1.5) \\draw-hline
  \\fill-line {{ \\line {{ {heading(f"{num}  {head}", pt)} }} \\null }}
  \\vspace #0.25
  {body}
  \\vspace #0.4
}}'''

    acc_style = "\\accidentalStyle Score.piano" if spec.get("instrument") == "piano" else "\\accidentalStyle Score.modern"
    staff_common = f"\\clef treble \\key {key_ly} \\time 4/4 {acc_style}"
    piano = spec.get("instrument") == "piano"
    if piano:
        shell_voicings(flat)
        lh = []
        for b in bars:
            dur = "1" if len(b) == 1 else "2"
            lh.append(" ".join("<" + " ".join(n.ly() for n in c["shell"]) + ">" + dur for c in b) + " |")
        subtitle = spec.get("subtitle") or f"Piano · key of {key_name}"

    def music(rh_items, extra_rh="", staff_with="", split=None, lh_items=None):
        rh = f"{{ {staff_common} {extra_rh}\n  {lines(marked(rh_items), split=split)}\n  \\bar \"|.\" }}"
        if not piano:
            return f"\\new Staff {staff_with} {rh}"
        lhm = f"{{ \\clef bass \\key {key_ly} \\time 4/4 {acc_style}\n  {lines(lh_items or lh)}\n  \\bar \"|.\" }}"
        return f"\\new PianoStaff << \\new Staff {staff_with} {rh} \\new Staff {lhm} >>"
    # Section notes: short, one idea per line (bold lead + a few words)
    LH_SAME = ("Left hand:", "same as Section 1.")
    guide = spec.get("yc_guide_tones", True)
    solo_on = spec.get("sample_solo", True)                  # the Sample Solo replaces the blank Your Chorus (Alex, 23 Nov 2026)
    yc_guide = ("Blue notes:", "guide tones, beat 4 into beat 1. The 7th falls to the next 3rd; on a V–I the 3rd climbs to the root.")
    if piano:
        s1_note = [("Right hand:", "1-3-5-7 of every chord."), ("Left hand:", LH_SHORT[LH_VOICING])]
        s3_note = [("Right hand:", "each chord's scale from the root, in time."), LH_SAME]
        if pattern_mode:
            s3_note = [("Right hand:", "1-2-3-5 on two-beat chords (no repeated notes), the full scale on one-bar chords."), LH_SAME]
        s4_note = ([yc_guide] if guide else []) + [("Your line:", "fill the empty beats. The left hand is written in.")]
    else:
        s1_note = [("Play:", "1-3-5-7 of every chord. Quarters on one-bar chords, eighths on two-beat chords.")]
        s3_note = [("Play:", "each chord's scale from the root, in time.")]
        if pattern_mode:
            s3_note = [("Play:", "1-2-3-5 on two-beat chords (no repeated notes), the full scale on one-bar chords.")]
        s4_note = ([yc_guide] if guide else []) + [("Your line:", "fill the empty beats with chord tones and scale notes, starting from the blue notes.")]
    if solo_on:
        nb = len(bars); hb = (nb + 1) // 2
        s4_note = [("How a solo is built:", "aim at the guide tones, then connect them."),
                   ("Blue notes:", "the guide tones, on beats 1 and 4. The number says which: 3, 7 or 1."),
                   ("Beat 4 into beat 1:", "the 7th falls a step to the next chord's 3rd."),
                   (f"Bars 1–{hb}:", "the black notes are arpeggio notes (Section 1)."),
                   (f"Bars {hb + 1}–{nb}:", "the black notes are scale notes (Section 3)."),
                   ("Make it yours:", "keep the blue notes and change the black ones" + (", or drop in a lick." if spec.get("licks") else "."))]
        if piano: s4_note.append(LH_SAME)
    s3_title = "Pattern Chorus" if pattern_mode else "Scale Chorus"
    if pattern_mode and two_beat_bars * 2 < len(bars):       # e.g. a blues: mostly one-bar chords
        s3_title = "Scale & Pattern Chorus"
        s3_note = [("Right hand:" if piano else "Play:", "the full scale on one-bar chords, 1-2-3-5 on two-beat chords.")] + ([LH_SAME] if piano else [])
    spec["_pattern_mode"] = pattern_mode
    lick_sections, lick_sections_after, yc_num = "", "", "4"
    if spec.get("licks"):
        after = spec.get("licks_after_your_chorus", False)
        built = build_licks(spec, bars, arp_c, sc_c, chord_ly, music, lines, marked, steps, semis, kroot, minor, section,
                            piano=piano, lh=lh if piano else None, nums=("5", "6") if after else ("4", "5"))
        if after:
            lick_sections_after = built
        else:
            lick_sections, yc_num = built, "6"
    solo = sample_solo(bars, title) if solo_on else None
    lh_midi = ("\\new Staff { \\clef bass " + " ".join(lh) + " " + " ".join(lh) + " }") if piano else ""
    long_form = len(bars) > 16
    brk = "\\pageBreak\n" if long_form else ""
    three = spec.get("target_pages") == 3
    brk2 = "\\pageBreak\n" if (long_form or three) else ""
    sys_space = (8 if piano else 13) if long_form else (11 if piano else 17)
    sys_space = spec.get("system_spacing") or sys_space      # tighter (about 11) when nine or more systems must share a page
    ragged = "##f" if (three or spec.get("s1_split") or spec.get("fill_pages")) else "##t"
    ragged_last = "##f" if spec.get("fill_pages") else "##t"
    staff_size = spec.get("staff_size") or ((14.5 if long_form else 16.5) if piano else 19)
    # Section 2 staff grows with its text so chord symbols, labels and notes stay in proportion
    s2_size = spec.get("s2_staff_size") or (round(S2_TEXT_PT * 1.75 * 2) / 2 if spec.get("s2_text_size") else staff_size)
    yc_size = f"#(layout-set-staff-size {spec['yc_staff_size']})" if spec.get("yc_staff_size") else ""   # Your Chorus staff, when it shares a page with the Lick Chorus
    s3_layout = f"\\layout {{ #(layout-set-staff-size {spec['s3_staff_size']}) }}" if spec.get("s3_staff_size") else ""
    s1_layout = f"\\layout {{ #(layout-set-staff-size {spec['s1_staff_size']}) }}" if spec.get("s1_staff_size") else ""
    ly = f'''\\version "2.24.0"
#(set-global-staff-size {staff_size})
\\header {{
  title = \\markup \\abs-fontsize #22 \\bold "{title}"
  subtitle = \\markup \\abs-fontsize #14 \\bold "{subtitle}"
  subsubtitle = \\markup \\abs-fontsize #12 "Chord & Scale Study"
  composer = \\markup \\abs-fontsize #11 "Alex Attard Music"
  tagline = "alexattardmusic.com"
}}
\\paper {{
  #(set-paper-size "letter")
  indent = 0
  top-margin = 12\\mm bottom-margin = 12\\mm left-margin = 16\\mm right-margin = 16\\mm
  markup-system-spacing.basic-distance = #6
  markup-markup-spacing.basic-distance = #1.6
  score-markup-spacing.basic-distance = #4
  system-system-spacing.basic-distance = #{sys_space}
  ragged-last-bottom = {ragged_last}
  ragged-bottom = {ragged}
}}
lickOn = {{ \\override NoteHead.color = #(rgb-color 0.78 0.42 0.05) \\override Stem.color = #(rgb-color 0.78 0.42 0.05) \\override Beam.color = #(rgb-color 0.78 0.42 0.05) \\override Accidental.color = #(rgb-color 0.78 0.42 0.05) \\override Dots.color = #(rgb-color 0.78 0.42 0.05) }}
guideOn = {{ \\override NoteHead.color = #{GUIDE_RGB} \\override Stem.color = #{GUIDE_RGB} \\override Accidental.color = #{GUIDE_RGB} }}
guideOff = {{ \\revert NoteHead.color \\revert Stem.color \\revert Accidental.color }}
lickOff = {{ \\revert NoteHead.color \\revert Stem.color \\revert Beam.color \\revert Accidental.color \\revert Dots.color }}
chExceptionMusic = {{ <c es ges bes>1-\\markup {{ "m" \\super "7♭5" }} }}
\\layout {{ \\context {{ \\Score \\override BarNumber.font-size = #-2 \\override RehearsalMark.self-alignment-X = #LEFT \\override RehearsalMark.break-align-symbols = #'(left-edge) }} \\context {{ \\ChordNames \\override ChordName.font-size = #1.5 majorSevenSymbol = \\markup {{ "maj7" }} chordNameExceptions = #(append (sequential-music-to-chord-exceptions chExceptionMusic #t) ignatzekExceptions) }} }}

changes = \\chordmode {{ {changes} }}

{section("1", "Chord-Tone Arpeggios", s1_note)}
\\score {{
  << \\new ChordNames \\changes
     {music(arp, extra_rh=f'\\tempo "{tempo}"', split=spec.get("s1_split"))} >>
  {s1_layout}
}}

{brk2}{section("2", "Scale Choices", [("One scale per chord.", "Black notes are chord tones, grey notes pass between them.")], S2_TEXT_PT)}
\\markup \\column {{ {" \\vspace #0.25 ".join(expl)} }}
\\markup \\vspace #0.6
\\score {{
  << \\new ChordNames \\chordmode {{ {" ".join(ref_chords)} }}
     \\new Staff \\with {{ \\override TextScript.padding = #1 }} {{ {staff_common} \\omit Staff.TimeSignature \\set Score.currentBarNumber = #1 \\omit Score.BarNumber
  {lines(ref)} }} >>
  \\layout {{ #(layout-set-staff-size {s2_size}) }}
}}
{"" if spec.get("listen_after_s3") else listen_block(spec)}

\\pageBreak
{section("3", s3_title, s3_note)}
\\score {{
  << \\new ChordNames \\changes
     {music(sc, split=spec.get("s3_split"))} >>
  {s3_layout}
}}
{listen_block(spec) if spec.get("listen_after_s3") else ""}

{lick_sections}
{brk}{section(yc_num, "Sample Solo" if solo_on else "Your Chorus", s4_note)}
\\score {{
  << \\new ChordNames \\changes
     {music(solo if solo_on else guide_line(bars) if guide else ["s1 |"] * len(bars), split=spec.get("yc_split") if solo_on else None, staff_with="" if piano else "\\with { \\override VerticalAxisGroup.default-staff-staff-spacing.basic-distance = #16 }")} >>
  \\layout {{ {yc_size} \\context {{ \\Score \\override BarNumber.break-visibility = ##(#f #f #t) }} }}
}}
\\markup \\column {{ \\vspace #1.2 {ww("Practice tip:", spec.get("practice_tip") or ("learn the Sample Solo slowly, then play it again and change the black notes: keep landing on a blue note on beats 1 and 4." if solo_on else "play Section 1 until the chord tones are automatic, then Section 3. Then write your own line in Section 4 and improvise over the changes, aiming for a chord tone on beats 1 and 3."))} }}
{lick_sections_after}

\\score {{
  << \\new Staff {{ {staff_common} {" ".join(arp)} {" ".join(sc)} }} {lh_midi} >>
  \\midi {{ \\tempo 4 = 112 }}
}}
'''
    LAST.update(arp=arp, sc=sc, lh=lh if piano else None, bars=bars, pattern_mode=pattern_mode, solo=solo, solo_num=yc_num)
    return ly


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    open(sys.argv[2], "w").write(build(spec))
