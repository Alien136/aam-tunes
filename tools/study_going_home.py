#!/usr/bin/env python3
"""Chord & scale study for the solo section of "Going Home" (Mark Lockheart, arr. Pete Churchill), alto saxophone.

  python3 tools/study_going_home.py                       ->  tools/out/Going_Home_Alto.pdf (no QR code)
  python3 tools/study_going_home.py --code GHA-0000 --publish /path/to/aam-tunes
                                                          also writes four player tunes and the PDF's shelf in index.json

The tune is in 3/4 and gen_study.py is 4/4 only, so this study is written out by hand. It covers the eight-bar solo section
(bars 25 to 32 of the ABRSM Grade 3 alto part), in the alto's written key, with the chord symbols as the part prints them.
No melody is written here: every line is our own exercise over the changes. The code is never stored in the repository.
"""
import hashlib, json, os, re, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
CODE = ARGS[ARGS.index("--code") + 1] if "--code" in ARGS else None
REPO = ARGS[ARGS.index("--publish") + 1] if "--publish" in ARGS else None
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
SLUG = "going-home-alto"
TEMPO = 88

# the solo section as the alto part prints it (written pitch): one bar each, the last bar holds two chords
CH = ["B♭△", "Gm7", "B♭m6/C♯", "Cm7", "B♭△", "Am7", "Em7", ("F7sus", "F♯7sus")]
ARP = ["bes'4 d'' f''", "g'4 bes' d''", "bes'4 des'' f''", "c''4 ees'' g''", "bes'4 d'' f''", "a'4 c'' e''", "e'4 g' b'", "f'4 bes' fis'"]
ARP7 = ["bes'4 d'' f''8 a''", "g'4 bes' d''8 f''", "bes'4 des'' f''8 g''", "c''4 ees'' g''8 bes''", "bes'4 d'' f''8 a''", "a'4 c'' e''8 g''", "e'4 g' b'8 d''",
        "f'8 bes' c'' ees'' fis' b'"]
SCALE = ["bes'8 c'' d'' ees'' f'' g''", "g'8 a' bes' c'' d'' ees''", "bes'8 c'' des'' ees'' f'' g''", "c''8 d'' ees'' f'' g'' a''", "bes'8 c'' d'' ees'' f'' g''",
         "a'8 b' c'' d'' e'' fis''", "e'8 fis' g' a' b' c''", "f'8 g' a' bes' fis' gis'"]
# three two-bar licks, each landing on the first beat of the bar after it (lick, landing note, where)
L1 = (["d''4 f''8 d'' bes'4", "bes'4 d''8 f'' d''4"], "des''2.")       # bars 1-2 -> bar 3: D natural falls to D flat, the note that changes
L2 = (["des''4 f''8 g'' f''4", "ees''4 g''8 ees'' c''4"], "d''2.")      # bars 3-4 -> bar 5: back up to D natural, the 3rd of the home chord
L3 = (["e''4 c''8 e'' g''4", "g''4 e''8 d'' b'4"], "c''2 cis''4")       # bars 6-7 -> bar 8: B rises a half step to C, then C sharp for the last chord
# the Lick Chorus: two times through. (bar text, label, is it a lick?)
LICK_CHORUS = [(L1[0][0], "Lick 1", 1), (L1[0][1], "", 1), (L1[1], "", 1), (ARP[3], "arp", 0), (SCALE[4], "scale", 0), (L3[0][0], "Lick 3", 1), (L3[0][1], "", 1), (L3[1], "", 1),
               (ARP7[0], "arp", 0), (SCALE[1], "scale", 0), (L2[0][0], "Lick 2", 1), (L2[0][1], "", 1), (L2[1], "", 1), (ARP[5], "arp", 0), (SCALE[6], "scale", 0), (ARP[7], "arp", 0)]

SLATE, MUTED, ORANGE = "#2F3E4E", "#6B7785", "(rgb-color 0.82 0.42 0.05)"
def chord(sym): return '^\\markup \\override #\'(font-name . "DejaVu Sans Bold") \\fontsize #0.5 "%s"' % sym
def with_chords(bars, k0=0, labels=None, licks=None):
    """Put each bar's chord symbol over its first note (the second chord of bar 8 over beat 3)."""
    out = []
    for k, bar in enumerate(bars):
        sym = CH[(k0 + k) % 8]; toks = bar.split(); first = 0
        def tag(i, text):
            toks[i] = toks[i] + text
        if isinstance(sym, tuple):
            tag(0, chord(sym[0])); beat, t = 0.0, None
            dur = "4"
            for i, tok in enumerate(toks):                      # find the note that starts beat 3
                m = re.search(r"(\d+\.?)", tok)
                if m: dur = m.group(1)
                if abs(beat - 2.0) < 1e-6: t = i; break
                beat += {"8": .5, "4": 1, "2": 2, "2.": 3}[dur]
            if t is not None and t != 0: tag(t, chord(sym[1]))
        else: tag(0, chord(sym))
        if labels and labels[k]: toks[0] += '_\\markup \\italic \\fontsize #-2 \\with-color "%s" "%s"' % (MUTED, labels[k])
        text = " ".join(toks)
        if licks and licks[k]: text = "\\lickOn " + text + " \\lickOff"
        out.append(text)
    return out

def staff(bars, per=4, end='\\bar "|."', blank=False):
    body = ""
    for k, b in enumerate(bars):
        body += b + (" \\break\n" if (k + 1) % per == 0 and k < len(bars) - 1 else " | ")
    return ('\\score { \\new Staff { \\clef treble \\key bes \\major \\time 3/4 \\accidentalStyle Score.modern %s %s %s }\n'
            '  \\layout { indent = 0 ragged-right = ##f ragged-last = ##f \\context { \\Score \\override BarNumber.font-size = #-2 } } }\n') % (
                "\\override Staff.NoteHead.transparent = ##t \\override Staff.Stem.transparent = ##t " if blank else "", body.rstrip(" |"), end)

def section(n, title, note=""):
    s = ('\\markup \\column { \\vspace #0.6 \\override #\'(thickness . 1.4) \\draw-line #\'(104 . 0) \\vspace #0.25 '
         '\\line { \\bold \\fontsize #3 "%s" \\hspace #1 \\bold \\fontsize #3 "%s" } }\n' % (n, title))
    if note: s += '\\markup \\column { \\vspace #0.2 \\override #\'(line-width . 104) \\wordwrap-string #"%s" \\vspace #0.5 }\n' % note
    return s
def para(text, italic=False): return '\\markup \\column { \\override #\'(line-width . 104) %s\\wordwrap-string #"%s" \\vspace #0.35 }\n' % ("\\italic " if italic else "", text)
def bold_para(head, text): return '\\markup \\column { \\override #\'(line-width . 104) \\wordwrap { \\bold "%s" %s } \\vspace #0.3 }\n' % (head, " ".join(text.split()))

def build_ly():
    s = r'''\version "2.24.0"
#(set-global-staff-size 21)
\paper { #(set-paper-size "letter") indent = 0 top-margin = 14\mm bottom-margin = 14\mm left-margin = 17\mm right-margin = 17\mm
  print-page-number = ##t tagline = ##f ragged-bottom = ##f ragged-last-bottom = ##t
  markup-system-spacing.basic-distance = #7 system-system-spacing.basic-distance = #15 score-markup-spacing.basic-distance = #7 }
\header { tagline = ##f }
lickOn = { \override NoteHead.color = #ORANGE \override Stem.color = #ORANGE \override Beam.color = #ORANGE \override Dots.color = #ORANGE \override Accidental.color = #ORANGE }
lickOff = { \revert NoteHead.color \revert Stem.color \revert Beam.color \revert Dots.color \revert Accidental.color }
'''.replace("#ORANGE", "#" + ORANGE)
    s += ('\\markup \\fill-line { \\center-column { \\bold \\fontsize #6 "Going Home" \\vspace #0.2 \\bold "Mark Lockheart, arr. Pete Churchill · solo section (bars 25 to 32)" '
          '"Chord & Scale Study · E♭ Alto Saxophone" } }\n\\markup \\fill-line { "" \\small "Alex Attard Music" }\n')
    s += section("1", "Chord-Tone Arpeggios", "Play: the first line is 1-3-5 of every chord, one note to a beat. The second line adds the top note of the chord on beat 3. "
                 "In the exam you solo over these eight bars once. Straight eighth notes, ♩ = 88, three beats in a bar.")
    s += staff(with_chords(ARP), per=4, end='\\bar "||"') + staff(with_chords(ARP7), per=4)
    s += section("2", "Scale Choices", "") + "\\markup \\vspace #0.3\n"
    s += bold_para("One home scale, two changes.", "Most of the solo section is the B♭ major scale. Two places leave it, and those are the notes that make your solo sound right.")
    s += bold_para("B♭△, Gm7, Cm7, F7sus → B♭ major scale", "(B♭ C D E♭ F G A). Bars 1, 2, 4, 5 and 8.")
    s += bold_para("B♭m6/C♯ → D becomes D♭.", "Bar 3. Play B♭ C D♭ E♭ F G: the B♭ minor sound. One note changes, and it is the note to aim for.")
    s += bold_para("Am7, Em7 → G major scale", "(G A B C D E F♯). Bars 6 and 7. B♭ becomes B natural, E♭ becomes E natural and F becomes F♯.")
    s += bold_para("F♯7sus → up a half step.", "The last beat of bar 8. Whatever you played on F7sus, play it a half step higher for one beat.")
    s += "\\pageBreak\n"
    s += section("3", "Scale Chorus", "Play: each chord's scale from its root, six eighth notes to a bar. Listen for D♭ in bar 3 and for B natural and F♯ in bars 6 and 7.")
    s += staff(with_chords(SCALE), per=4)
    s += section("4", "Licks", "Three short lines, each two bars long, landing on the first beat of the next bar. Orange notes are the lick. Each one teaches a note that changes.")
    for name, (bars, land), k0, why in [("Lick 1 · D falls to D♭", L1, 0, "bars 1 and 2, landing in bar 3. The line ends on D natural and drops a half step to D♭, the 3rd of the new chord."),
                                        ("Lick 2 · back to D", L2, 2, "bars 3 and 4, landing in bar 5. It starts on that D♭ and comes home to D natural, the 3rd of B♭△."),
                                        ("Lick 3 · B rises to C", L3, 5, "bars 6 and 7, landing in bar 8. B natural climbs a half step to C, then to C♯ for the last chord, which pulls you back to the top.")]:
        s += bold_para(name + ":", why)
        s += staff(with_chords(bars + [land], k0, licks=[1, 1, 1]), per=3, end='\\bar "||"').replace("indent = 0 ragged-right", "line-width = 150\\mm indent = 0 ragged-right")
    s += bold_para("How to practice a lick.", "Sing it first. Play it slowly with even eighth notes. Hold the landing note with a full sound. Then change one note or the rhythm and it is yours.")
    s += section("", "Listen", "")
    s += para("Perfect Houseplants: 'Going Home', from the album Perfect Houseplants (Ah-Um). This is the composer's own band, and the recording your exam book recommends. "
              "Find it on YouTube, Spotify or Apple Music. Listen once for the feel, then play the Section 1 arpeggios along with your backing track.", italic=True)
    s += "\\pageBreak\n"
    s += section("5", "Lick Chorus", "Twice through the solo section with everything put together. The licks are orange; the other bars are arpeggios and scales. Each bar is labelled.")
    s += staff(with_chords([b for b, _, _ in LICK_CHORUS], labels=[l for _, l, _ in LICK_CHORUS], licks=[k for _, _, k in LICK_CHORUS]), per=4)
    s += section("6", "Your Chorus", "Write your own eight bars. Aim for a chord tone on beat 1 of every bar, and use D♭ in bar 3 and B natural in bars 6 and 7.")
    blank = with_chords(["s4 s s"] * 6 + ["s4 s s"] + ["s4 s s"])
    s += staff(blank, per=4)
    s += bold_para("Practice tip:", "play Section 1 until you can do it without the page. Then play the Lick Chorus slowly. In your own solo, leave space: a ballad needs long notes and rests, not a stream of eighth notes.")
    s += '\\markup \\fill-line { \\small "alexattardmusic.com" }\n'
    return s

# ---------------------------------------------------------------- the player: four exercises in 3/4, click only (the exam book has the backing track)
def publish(repo):
    sys.argv = [sys.argv[0]]; sys.path.insert(0, HERE)
    import build_beginner as G                                      # for parse_part: written notes -> sounding events and the notation the player draws
    import gen_study as g
    wk = g.parse_note("Bb"); below = 9; ck = "Db"; PCS = G.PCS
    items = [("arpeggios", "Arpeggios · 1-3-5", ARP, "One note to a beat: root, 3rd and 5th of every chord"),
             ("arpeggios-7", "Arpeggios · with the top note", ARP7, "Root and 3rd, then the 5th and the top note of the chord on beat 3"),
             ("scales", "Scale Chorus", SCALE, "Each chord's scale from its root, six eighth notes to a bar"),
             ("licks", "Lick Chorus", [b for b, _, _ in LICK_CHORUS], "Twice through the solo section: licks, arpeggios and scales")]
    ip = os.path.join(repo, "index.json"); idx = json.load(open(ip)); slugs = []
    h = hashlib.sha256(("aam:" + re.sub(r"[^A-Z0-9]", "", CODE.upper())).encode()).hexdigest()
    clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == h and p["id"] != SLUG]; assert not clash, "that code is already used by " + clash[0]
    for sl, title, bars, desc in items:
        it = dict(title=title); music = " | ".join(bars)
        ev, abc, marks, roots = G.parse_part(it, music, 3, wk, below); seq = G.parse_part.seq
        root = (wk.pc - below) % 12
        chords = [[dict(sym=PCS[root], beats=3, root=root, degs=[0, 2, 4, 5, 7, 9, 11], scale="Ionian (major)")] for _ in bars]
        tune = dict(format="aam-tune/1", slug=SLUG + "-" + sl, title=title, subtitle="Going Home · Alto Sax · solo section", instrument="alto", concert_key=ck, native=9, style="click", keys="off",
                    hide=["chords", "solo", "names"], hear=True, first_bar=1, chart_tempo=TEMPO, tempo_presets=[66, TEMPO, 100], form=[], bars=chords,
                    sections=[dict(id="notes", title="Notes", tab="Notes", desc=desc, rh=ev, lh=[], abc=dict(rh=abc, marks=marks), learn=seq)],
                    notation=dict(key="Bb", staves="treble"), meter=[3, 4])
        json.dump(tune, open(os.path.join(repo, "tunes", tune["slug"] + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
        idx["tunes"][tune["slug"]] = dict(title=title, subtitle=tune["subtitle"]); slugs.append(tune["slug"])
    entry = dict(id=SLUG, title="Going Home · Alto Sax", hash=h, tunes=slugs, contents=[dict(title="Solo section", items=slugs)])
    rest = [p for p in idx["pdfs"] if p["id"] != SLUG]; at = next((i for i, p in enumerate(rest) if p.get("free")), len(rest))
    idx["pdfs"] = rest[:at] + [entry] + rest[at:]
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    print("published %d exercises for Going Home · Alto Sax" % len(slugs))

def main():
    base = os.path.join(OUT, "going_home_alto"); open(base + ".ly", "w").write(build_ly())
    r = subprocess.run(["lilypond", "-s", "-o", base, base + ".ly"], capture_output=True, text=True)
    assert os.path.exists(base + ".pdf"), r.stderr[-1500:]
    out = os.path.join(OUT, "Going_Home_Alto.pdf")
    if CODE:
        link = "https://alexattardmusic.com/play/?t=%s-arpeggios&c=%s" % (SLUG, re.sub(r"[^A-Z0-9]", "", CODE.upper()))
        subprocess.run([sys.executable, os.path.join(HERE, "add_qr.py"), base + ".pdf", out, link, "--label", "Play-along code: " + CODE], check=True)
    else: os.replace(base + ".pdf", out)
    print(out)
    if REPO: publish(REPO)

if __name__ == "__main__":
    main()
