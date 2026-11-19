#!/usr/bin/env python3
"""Alex Attard Music: Saxophone Beginner Booklet (one edition for alto and tenor: both read the same written notes).

  python3 tools/build_beginner.py                                   ->  tools/out/Sax_Beginner_Booklet.pdf (no QR codes)
  python3 tools/build_beginner.py alto --code SBA-0000 [--publish /path/to/aam-tunes]
                                                                    ->  tools/out/Sax_Beginner_Booklet_Alto.pdf, with a QR on the cover
                                                                        and on every unit; --publish also writes one player tune per
                                                                        numbered line and the booklet's shelf in index.json
The code is given on the command line and never stored in the repository (index.json keeps only its hash).

The book before the Welcome Booklet. Eight units; each one adds one to three notes (with the fingering diagram from the
Welcome Booklet's chart), long tones on the new notes, short drills, then tunes that use only the notes learned so far.
New ideas sit in colour-coded boxes at the top of the unit: amber = new note, blue = new rhythm, green = key signature,
red = new word. All of it is one ReportLab canvas; every line of music is engraved by LilyPond to a PNG and placed.
The curriculum is the UNITS list below: edit a line there and rebuild.
"""
import hashlib, io, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[1:]
ED = ARGS[0] if ARGS and ARGS[0] in ("alto", "tenor") else None
CODE = ARGS[ARGS.index("--code") + 1] if "--code" in ARGS else None
REPO = ARGS[ARGS.index("--publish") + 1] if "--publish" in ARGS else None
sys.argv = [sys.argv[0], ED or "alto"]
import build_book as B                                              # fonts, colours, key diagram, drawn saxophone
import publish_exercise as PX                                       # ABC spelling for the player
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from PIL import Image

W, H, M = B.W, B.H, B.M
CW = W - 2 * M
SLATE, AMBER, TINT, MUTED, RULE = B.SLATE, B.AMBER, B.TINT, B.MUTED, B.RULE
KIND = {"note": (AMBER, "#FBF1E1", "NEW NOTE"), "rhythm": ("#4A78B0", "#EAF1F8", "NEW RHYTHM"),
        "key": ("#3E8E7E", "#E6F3F0", "NEW KEY"), "word": ("#B5533C", "#F8EAE6", "NEW WORD"),
        "symbol": ("#7A5AA6", "#F0EBF7", "NEW SYMBOL"), "skill": ("#2E8C9E", "#E4F2F5", "SAX SKILL")}
PILL = {"CLAP": "#4A78B0", "WRITE": "#B5533C", "DUET": "#7A5AA6", "SCALE": "#3E8E7E", "ROUND": "#7A5AA6"}
CACHE = os.path.join(B.OUT, "beg"); os.makedirs(CACHE, exist_ok=True)
STAFF = 21
LINE_MM = 176.0

# ---------------------------------------------------------------- the curriculum
# music: LilyPond, absolute pitch, bars separated by "|".  names: print letter names under the notes.
# hl: notes to print in amber (the new notes, where they first appear).  bpl: bars per line.  src: where the tune was checked.
def L(title, music, sub="", key="c", time="4/4", names=False, hl=(), bpl=4, partial=None, lyr=None, src=None, tempo=None, slug=None,
      b=None, rhythm=False, quiz=None, badge=None, pill=None, repeat=False, about=None, tempo_word=None):
    # slug: give the OLD title here when you rename a line, so QR codes on copies already printed keep working
    # b: a second part (duet).  rhythm: a line to clap, on a one-line staff.  quiz: "names" | "counts" | "bars" (a written exercise).
    # badge: "CLAP" / "WRITE" lines carry a badge instead of a number and are not in the player.  pill: a small label after the number.
    return dict(slug=slug, b=b, rhythm=rhythm, quiz=quiz, badge=badge, pill=pill, repeat=repeat, about=about, tempo_word=tempo_word, type="line", title=title, music=music, sub=sub, key=key, time=time, names=names, hl=set(hl), bpl=bpl, partial=partial, lyr=lyr, src=src, tempo=tempo)

WIKI = "checked against the notation in Wikipedia"
MEM = "written from memory: check"
UNITS = [
 dict(title="Your first three notes", notes=[("b'", "B", "One finger: left index."), ("a'", "A", "Add your left middle finger."), ("g'", "G", "Add your left ring finger.")],
  boxes=[("rhythm", "Whole, half and quarter notes", "A <b>whole note</b> lasts 4 beats, a <b>half note</b> 2 beats and a <b>quarter note</b> 1 beat. A <b>rest</b> is silence: count it just as carefully."),
         ("word", "Long tone", "One note held as long and as steady as you can. Long tones build your sound, so every unit starts with them.")],
  lines=[L("Count, then play", "b'1 | b'2 b'2 | b'4 b' b' b' | b'1", "Say the counts out loud first.", lyr=["1-2-3-4", "1-2", "3-4", "1", "2", "3", "4", "1-2-3-4"]),
         L("Long tone: B", "b'1 | r1 | b'1 | r1", "Start with your tongue: \"too\". Keep the sound still.", names=True, hl=["b'"]),
         L("Long tone: A", "a'1 | r1 | a'1 | r1", names=True, hl=["a'"]),
         L("Long tone: G", "g'1 | r1 | g'1 | r1", names=True, hl=["g'"]),
         L("Stepping down, stepping up", "b'2 a'2 | g'1 | g'2 a'2 | b'1", names=True),
         L("Quarter notes", "b'4 b' b' b' | a' a' a' a' | g' g' g' g' | g'1", "Tongue every note."),
         L("Hot Cross Buns", "b'4 a' g'2 | b'4 a' g'2 | g'4 g' a' a' | b'4 a' g'2", "English traditional", src=WIKI + " (\"Hot Cross Buns\", simple version; bar 3 in quarter notes)"),
         L("Au Clair de la Lune", "g'4 g' g' a' | b'2 a'2 | g'4 b' a' a' | g'1", "French traditional", src=WIKI + " (French article)"),
         L("Three-Note March", "b'4 g' a' b' | a'2 g'2 | b'4 g' a' b' | a'4 a' g'2", "Exercise"),
         dict(type="create", title="Your turn", sub="Write four bars of your own with B, A and G. Then play them."),
         dict(type="check", items=["I can hold B, A and G for four steady beats.", "I start every note with my tongue.", "I can play Hot Cross Buns without looking at my fingers."])]),
 dict(title="C and D: five notes", notes=[("c''", "C", "Middle finger only. Lift the index finger."), ("d''", "D", "All six fingers down, plus the octave key under your left thumb.")],
  boxes=[("word", "Octave key", "The key under your left thumb. Press it and the same fingering sounds one octave higher. D is your first note that uses it."),
         ("word", "Breath mark", "A comma above the staff shows a good place to breathe. Breathe quickly through the corners of your mouth.")],
  lines=[L("Long tone: C", "c''1 | r1 | c''1 | r1", names=True, hl=["c''"]),
         L("B to C", "b'2 c''2 | b'2 c''2 | b'4 c'' b' c'' | b'1", "Two fingers swap places. Go slowly.", names=True),
         L("Long tone: D", "d''1 | r1 | d''1 | r1", "Thumb on the octave key.", names=True, hl=["d''"]),
         L("Over the break", "c''2 d''2 | c''2 d''2 | c''4 d'' c'' d'' | d''1", "All the fingers land together."),
         L("Five notes up and down", "g'4 a' b' c'' | d''1 | d''4 c'' b' a' | g'1"),
         L("Mary Had a Little Lamb", "b'4 a' g' a' | b' b' b'2 | a'4 a' a'2 | b'4 d'' d''2 | b'4 a' g' a' | b' b' b' b' | a' a' b' a' | g'1", "American traditional", src=MEM),
         L("Buzz, Buzz, Buzz", "d''2 c''2 | b'2 r2 | a'4 b' c'' a' | g'2 r2 | b'4 c'' d'' b' | a' b' c'' a' | b' c'' d'' b' | a' b' c'' a' | d''2 c''2 | b'2 r2 | a'4 b' c'' a' | g'2 r2", "Bohemian folk song", src=WIKI + " (German article \"Summ, summ, summ\"; note lengths doubled)"),
         L("Lightly Row", "d''4 b' b'2 | c''4 a' a'2 | g'4 a' b' c'' | d'' d'' d''2 | d''4 b' b'2 | c''4 a' a'2 | g'4 b' d'' d'' | g'1 | a'4 a' a' a' | a' b' c''2 | b'4 b' b' b' | b' c'' d''2 | d''4 b' b'2 | c''4 a' a'2 | g'4 b' d'' d'' | g'1", "German folk song", src=WIKI + " (German article \"Hänschen klein\"; note lengths doubled)"),
         L("Jingle Bells", "b'4 b' b'2 | b'4 b' b'2 | b'4 d'' g' a' | b'1 | c''4 c'' c'' c'' | c'' b' b' b' | b' a' a' b' | a'2 d''2 | b'4 b' b'2 | b'4 b' b'2 | b'4 d'' g' a' | b'1 | c''4 c'' c'' c'' | c'' b' b' b' | d'' d'' c'' a' | g'1", "J. Pierpont (chorus, easy rhythm)", src=MEM),
         dict(type="check", items=["I can move from C to D without a bump in the sound.", "I can play five notes up and down in one breath.", "I can play one of these tunes from memory."])]),
 dict(title="The right hand: F, E and D", notes=[("f'", "F", "Left hand stays down. Add your right index finger."), ("e'", "E", "Add your right middle finger."), ("d'", "Low D", "Add your right ring finger. Six fingers, no octave key.")],
  boxes=[("rhythm", "Dotted half note", "A dot adds half of the note's length. A half note is 2 beats, so a <b>dotted half note</b> is 3 beats."),
         ("word", "Pick-up notes", "Notes before the first full bar. Count the missing beats, then come in.")],
  lines=[L("Long tones: F and E", "f'1 | r1 | e'1 | r1", "Use warm, slow air for low notes.", names=True, hl=["f'", "e'"]),
         L("Long tone: low D", "d'1 | r1 | d'1 | r1", "Keep your jaw loose.", names=True, hl=["d'"]),
         L("Right-hand walk", "g'2 f'2 | e'2 d'2 | d'4 e' f' g' | g'1", names=True),
         L("Two Ds", "d'2 d''2 | d'2 d''2 | d'1 | d''1", "Same fingers. Only your thumb moves."),
         L("Three beats", "g'2. g'4 | f'2. f'4 | e'2. e'4 | d'1", lyr=["1-2-3", "4", "1-2-3", "4", "1-2-3", "4", "1-2-3-4"]),
         L("Old MacDonald Had a Farm", "g'4 g' g' d' | e' e' d'2 | b'4 b' a' a' | g'2. d'4 | g'4 g' g' d' | e' e' d'2 | b'4 b' a' a' | g'1", "American traditional", src=MEM),
         L("Low Tide", "d'4 e' f' g' | a'2 g'2 | f'4 e' d' e' | f'2. r4 | d'4 e' f' g' | a'2 b'2 | a'4 g' f' e' | d'1", "Exercise"),
         L("When the Saints Go Marching In", "g'4 b' c'' | d''1 | r4 g' b' c'' | d''1 | r4 g' b' c'' | d''2 b'2 | g'2 b'2 | a'1 | r4 b' b' a' | g'1 | b'2 d''2 | d''4 c''2. | r2 b'4 c'' | d''2 b'2 | g'2 a'2 | g'1", "American spiritual", partial="4*3", src=WIKI + " (German article; note lengths doubled)"),
         dict(type="create", title="Your turn", sub="Write four bars that go down to low D and come back up."),
         dict(type="check", items=["My low D speaks without a squeak or a gurgle.", "I can count a dotted half note.", "I can come in after pick-up notes."])]),
 dict(title="F sharp and the key of G", notes=[("fis'", "F♯", "Like F, but use your right MIDDLE finger instead of the index.")],
  boxes=[("key", "Sharps and key signatures", "A <b>sharp</b> (♯) raises a note by a half step. A sharp at the start of every line is a <b>key signature</b>: here it means every F is F♯."),
         ("word", "Half step", "The smallest step in music: from one note to its very next neighbor, like F to F♯.")],
  lines=[L("Long tone: F sharp", "fis'1 | r1 | fis'1 | r1", "No key signature yet: the sharp is written in.", names=True, hl=["fis'"]),
         L("F or F sharp?", "f'2 fis'2 | f'2 fis'2 | e'4 fis' g'2 | g'1", "Switch fingers, not hands.", names=True),
         L("Five notes from D", "d'4 e' fis' g' | a'1 | a'4 g' fis' e' | d'1", "Now with the key signature.", key="g"),
         L("Twinkle, Twinkle, Little Star", "d'4 d' a' a' | b' b' a'2 | g'4 g' fis' fis' | e' e' d'2 | a'4 a' g' g' | fis' fis' e'2 | a'4 a' g' g' | fis' fis' e'2 | d'4 d' a' a' | b' b' a'2 | g'4 g' fis' fis' | e' e' d'2", "French traditional", key="g", src=WIKI),
         L("Aura Lee", "d'4 g' fis' g' | a' e' a'2 | g'4 fis' e' fis' | g'1 | d'4 g' fis' g' | a' e' a'2 | g'4 fis' e' fis' | g'1", "G. R. Poulton (easy rhythm)", key="g", src=WIKI + " (\"Aura Lea\"; even quarter notes instead of the dotted rhythm)"),
         L("Au Clair de la Lune (complete)", "g'4 g' g' a' | b'2 a'2 | g'4 b' a' a' | g'1 | g'4 g' g' a' | b'2 a'2 | g'4 b' a' a' | g'1 | a'4 a' a' a' | e'2 e'2 | a'4 g' fis' e' | d'1 | g'4 g' g' a' | b'2 a'2 | g'4 b' a' a' | g'1", "French traditional", key="g", src=WIKI + " (French article)"),
         L("Yankee Doodle", "g'4 g' a' b' | g' b' a' d' | g' g' a' b' | g'2 fis'2 | g'4 g' a' b' | c'' b' a' g' | fis' d' e' fis' | g'2 g'2", "American traditional", key="g", src=MEM),
         dict(type="check", items=["I use my middle finger for F♯ every time.", "I check the key signature before I play.", "I can play Twinkle with a steady beat."])]),
 dict(title="Higher: E, F sharp and G", notes=[("e''", "Upper E", "Low E plus the octave key."), ("fis''", "Upper F♯", "Low F♯ plus the octave key."), ("g''", "Upper G", "Low G plus the octave key.")],
  boxes=[("rhythm", "Eighth notes", "Two <b>eighth notes</b> fit in one beat. Count \"1 and 2 and\". They are joined by a beam."),
         ("word", "Scale", "Eight notes in a row, step by step, from a note to the same note one octave higher.")],
  lines=[L("Octaves", "e'2 e''2 | fis'2 fis''2 | g'2 g''2 | g''1", "Only the thumb moves. Blow faster air for the high note.", key="g", hl=["e''", "fis''", "g''"]),
         L("Long tones going up", "d''1 | e''1 | fis''1 | g''1", key="g", names=True),
         L("G major scale", "g'4 a' b' c'' | d'' e'' fis'' g'' | g'' fis'' e'' d'' | c'' b' a' g'", "Your first scale.", key="g"),
         L("One and two and", "g'4 g'8 g' a'4 a'8 a' | b'4 b'8 b' c''4 c''8 c'' | d''8 d'' d'' d'' d''4 r4 | g'1", key="g", lyr=["1", "2", "and", "3", "4", "and", "1", "2", "and", "3", "4", "and", "1", "and", "2", "and", "3", "1-2-3-4"]),
         L("Frère Jacques", "g'4 a' b' g' | g' a' b' g' | b' c'' d''2 | b'4 c'' d''2 | d''8 e'' d'' c'' b'4 g' | d''8 e'' d'' c'' b'4 g' | g' d' g'2 | g'4 d' g'2", "French traditional", key="g", src=WIKI),
         L("All My Little Ducklings", "g'8 a' b' c'' d''4 d'' | e''8 e'' e'' e'' d''2 | e''8 e'' e'' e'' d''2 | c''8 c'' c'' c'' b'4 b' | a'8 a' a' a' g'2", "German traditional", key="g", bpl=3, src=WIKI + " (German article \"Alle meine Entchen\")"),
         L("Twinkle, up high", "g'4 g' d'' d'' | e'' e'' d''2 | c''4 c'' b' b' | a' a' g'2 | d''4 d'' c'' c'' | b' b' a'2 | d''4 d'' c'' c'' | b' b' a'2 | g'4 g' d'' d'' | e'' e'' d''2 | c''4 c'' b' b' | a' a' g'2", "The tune you know, in a new key.", key="g", src=WIKI),
         dict(type="create", title="Your turn", sub="Write four bars that use eighth notes and at least one high note."),
         dict(type="check", items=["My high notes start cleanly, without biting.", "I can play the G major scale up and down.", "I can count eighth notes out loud."])]),
 dict(title="B flat and the key of F", notes=[("bes'", "B♭", "Left index finger presses B and the small bis key just below it, together."), ("f''", "Upper F", "Low F plus the octave key.")],
  boxes=[("key", "Flats and the key of F", "A <b>flat</b> (♭) lowers a note by a half step. One flat in the key signature means every B is B♭."),
         ("rhythm", "Three-four time", "The top number changes to 3: three beats in every bar. A dotted half note fills a whole bar.")],
  lines=[L("Long tone: B flat", "bes'1 | r1 | bes'1 | r1", "One finger covers two keys.", names=True, hl=["bes'"]),
         L("A, B flat, C", "a'2 bes'2 | c''1 | c''2 bes'2 | a'1", "Now with the key signature.", key="f"),
         L("F major scale", "f'4 g' a' bes' | c'' d'' e'' f'' | f'' e'' d'' c'' | bes' a' g' f'", key="f", hl=["f''"]),
         L("Three in a bar", "f'2. | a'2. | c''4 c'' c'' | f'2.", key="f", time="3/4", lyr=["1-2-3", "1-2-3", "1", "2", "3", "1-2-3"]),
         L("Cuckoo", "c''4 a' r | c'' a' r | g' f' g' | f'2. | g'4 g' a' | bes'2 g'4 | a' a' bes' | c''2 a'4 | c''2 a'4 | c''2 a'4 | bes' a' g' | f'2.", "German traditional", key="f", time="3/4", src=WIKI + " (German article \"Kuckuck, Kuckuck, ruft's aus dem Wald\", moved to F)"),
         L("Mary Moves to F", "a'4 g' f' g' | a' a' a'2 | g'4 g' g'2 | a'4 c'' c''2 | a'4 g' f' g' | a' a' a' a' | g' g' a' g' | f'1", "Same tune, new key: this is called transposing.", key="f", src=MEM),
         L("Lightly Row in F", "c''4 a' a'2 | bes'4 g' g'2 | f'4 g' a' bes' | c'' c'' c''2 | c''4 a' a'2 | bes'4 g' g'2 | f'4 a' c'' c'' | f'1", "German folk song", key="f", src=WIKI + " (German article \"Hänschen klein\")"),
         dict(type="check", items=["I press B and the bis key with one finger.", "I can feel three beats in a bar.", "I can play the F major scale."])]),
 dict(title="Low C and the dotted quarter", notes=[("c'", "Low C", "Six fingers down, then your right pinky on the lower of its two keys.")],
  boxes=[("rhythm", "Dotted quarter note", "A <b>dotted quarter note</b> lasts one and a half beats. It is almost always followed by one eighth note: \"1 (2) and\"."),
         ("word", "Tie", "A curved line joining two notes of the same pitch. Play the first and hold it through the second.")],
  lines=[L("Long tone: low C", "c'1 | r1 | c'1 | r1", "Slow, warm air. Drop your jaw a little.", names=True, hl=["c'"]),
         L("Pinky push-ups", "d'2 c'2 | d'2 c'2 | d'4 c' d' c' | c'1", "Keep the other fingers still."),
         L("C major scale", "c'4 d' e' f' | g' a' b' c'' | c'' b' a' g' | f' e' d' c'"),
         L("Long, short", "g'4. g'8 g'2 | a'4. a'8 a'2 | b'4. a'8 g'4 a' | g'1", lyr=["1-2", "and", "3-4", "1-2", "and", "3-4", "1-2", "and", "3", "4", "1-2-3-4"]),
         L("London Bridge", "g'4. a'8 g'4 f' | e' f' g'2 | d'4 e' f'2 | e'4 f' g'2 | g'4. a'8 g'4 f' | e' f' g'2 | d'2 g'2 | e'4 c'2.", "English traditional", src=WIKI + " (note lengths doubled)"),
         L("Michael, Row the Boat Ashore", "c'4 e' | g'4. e'8 g'4 a' | g'2 e'4 g' | a'1 | g'2 e'4 g' | g'4. e'8 f'4 e' | d'2 c'4 d' | e'2 d'2 | c'2", "American spiritual", partial="2", src=WIKI),
         L("Alouette", "g'4. a'8 b'4 b' | a'8 g' a' b' g'4 d' | g'4. a'8 b'4 b' | a'8 g' a' b' g'2", "French-Canadian traditional", key="g", src=WIKI + " (first section)"),
         L("Ode to Joy", "b'4 b' c'' d'' | d'' c'' b' a' | g' g' a' b' | b'4. a'8 a'2 | b'4 b' c'' d'' | d'' c'' b' a' | g' g' a' b' | a'4. g'8 g'2 | a'4 a' b' g' | a' b'8 c'' b'4 g' | a' b'8 c'' b'4 a' | g' a' d' b' ~ | b' b' c'' d'' | d'' c'' b' a' | g' g' a' b' | a'4. g'8 g'2", "L. van Beethoven", key="g", src=WIKI),
         dict(type="check", items=["My low C speaks on the first try.", "I can clap and count a dotted quarter note.", "I hold a tied note for its full length."])]),
 dict(title="C sharp and the key of D", notes=[("cis''", "C♯", "No fingers at all. Balance the sax with your thumbs and the strap.")],
  boxes=[("key", "The key of D", "Two sharps in the key signature: every F is F♯ and every C is C♯."),
         ("skill", "Open C sharp", "With no fingers down the saxophone can wobble. Let the strap and both thumbs hold it, and keep your fingers hovering over their keys.")],
  lines=[L("Long tone: C sharp", "cis''1 | r1 | cis''1 | r1", "Open notes go sharp easily. Listen and keep the air steady.", names=True, hl=["cis''"]),
         L("B, C sharp, D", "b'2 cis''2 | d''1 | d''2 cis''2 | b'1", "From no fingers to all fingers.", key="d"),
         L("D major scale", "d'4 e' fis' g' | a' b' cis'' d'' | d'' cis'' b' a' | g' fis' e' d'", key="d"),
         L("Slur two, tongue two", "d'4( e') fis' g' | a'( b') cis'' d'' | d''( cis'') b' a' | g'( fis') e' d'", key="d"),
         L("Amazing Grace", "d'4 | g'2 b'8( g') | b'2 a'4 | g'2 e'4 | d'2 d'4 | g'2 b'8( g') | b'2 a'4 | d''2 b'4 | d''4.( b'8) d''( b') | g'2 d'4 | e'4.( g'8) g'( e') | d'2 d'4 | g'2 b'8( g') | b'2 a'4 | g'2.", "American traditional", key="g", time="3/4", partial="4", src=WIKI),
         L("Happy Birthday to You", "d'8 d' | e'4 d' g' | fis'2 d'8 d' | e'4 d' a' | g'2 d'8 d' | d''4 b' g' | fis' e' c''8 c'' | b'4 g' a' | g'2", "M. and P. Hill (easy rhythm)", key="g", time="3/4", partial="4", src=WIKI + " (pick-ups as even eighth notes)"),
         L("Auld Lang Syne", "c'4 | f'4. f'8 f'4 a' | g'4. f'8 g'4 a' | f'4. f'8 a'4 c'' | d''2. d''4 | c''4. a'8 a'4 f' | g'4. f'8 g'4 a' | f'4.( d'8) d'4( c') | f'2. d''4 | c''4.( a'8) a'4( f') | g'4. f'8 g'4 d'' | c''4.( a'8) a'4( c'') | d''2. d''4 | c''4. a'8 a'4 f' | g'4. f'8 g'4 a' | f'4.( d'8) d'4( c') | f'2.", "Scottish traditional", key="f", partial="4", src=WIKI),
         dict(type="check", items=["I can play C♯ in tune with nothing to hold on to.", "I can slur without stopping the air.", "I can perform one of these tunes for someone."])]),
]
# ---------------------------------------------------------------- second edition: what the leading band methods all include
def _u(k): return UNITS[k - 1]
def _line(k, title): return next(it for it in _u(k)["lines"] if it.get("title") == title and it["type"] == "line")
def _after(k, title, *items):
    ls = _u(k)["lines"]; i = next(i for i, it in enumerate(ls) if it.get("title") == title); ls[i + 1:i + 1] = list(items)
def _before_check(k, *items):
    ls = _u(k)["lines"]; i = next(i for i, it in enumerate(ls) if it["type"] == "check"); ls[i:i] = list(items)
def _breathe(k, title, bars):
    it = _line(k, title); bs = [b.strip() for b in it["music"].split("|")]
    for n in bars: bs[n - 1] += " \\breathe"
    it["music"] = " | ".join(bs)
def CLAP(music, lyr, time="4/4", bpl=4): return L("Clap and count", music, "Clap the notes. Stay silent on the rests.", time=time, rhythm=True, badge="CLAP", lyr=lyr, bpl=bpl)
def WRITE(title, sub, music, quiz, key="c", time="4/4", bpl=4): return L(title, music, sub, key=key, time=time, quiz=quiz, badge="WRITE", bpl=bpl)
def EAR(text): return dict(type="ear", text=text)
DUET = "Learn both parts, then swap with a partner or the player."

# Unit 1
_u(1)["boxes"].append(("skill", "Tonguing", "Start every note with the tip of your tongue on the reed, as if saying \"too\". The air keeps flowing: only the tongue moves."))
_u(1)["lines"].insert(0, CLAP("c'4 c' c' c' | c'2 c'2 | c'4 r c' r | c'1", ["1", "2", "3", "4", "1-2", "3-4", "1", "3", "1-2-3-4"]))
_line(1, "Hot Cross Buns")["about"] = "An old English street cry: sellers sang it to sell hot buns."
_line(1, "Au Clair de la Lune")["about"] = "A French folk song from the 1700s. The title means \"By the light of the moon\"."
_after(1, "Three-Note March",
       L("Hot Cross Buns duet", "b'4 a' g'2 | b'4 a' g'2 | g'4 g' a' a' | b'4 a' g'2", DUET, b="g'4 a' b'2 | g'4 a' b'2 | b'4 b' a' a' | g'4 a' b'2", pill="DUET"),
       WRITE("Name the notes", "Write the letter name under each note.", "b'1 | g'1 | a'1 | b'2 g'2 | a'2 b'2 | g'1", "names", bpl=6))
# Unit 2
_u(2)["boxes"].append(("symbol", "Repeat sign", "Two dots before a double bar line: go back to the beginning and play it one more time."))
_u(2)["lines"].insert(0, CLAP("c'4 c' c' r | c'2 r2 | r4 c' c' c' | c'1", ["1", "2", "3", "1-2", "2", "3", "4", "1-2-3-4"]))
_line(2, "Five notes up and down").update(repeat=True, sub="Play it twice: there is a repeat sign.")
_line(2, "Mary Had a Little Lamb")["about"] = "The words were printed in Boston in 1830. In 1877 Thomas Edison spoke them as the first words ever recorded."
_line(2, "Jingle Bells")["about"] = "James Lord Pierpont published it in 1857 as \"One Horse Open Sleigh\"."
_breathe(2, "Mary Had a Little Lamb", [4]); _breathe(2, "Lightly Row", [4, 8, 12]); _breathe(2, "Jingle Bells", [4, 8, 12])
_after(2, "Mary Had a Little Lamb",
       L("Ode to Joy duet", "b'4 b' c'' d'' | d'' c'' b' a' | g' g' a' b' | b'2 a'2 | b'4 b' c'' d'' | d'' c'' b' a' | g' g' a' b' | a'2 g'2", DUET,
         b="g'4 g' a' b' | b' a' g' a' | b' b' c'' d'' | d''2 c''2 | g'4 g' a' b' | b' a' g' a' | b' b' c'' d'' | c''2 b'2", pill="DUET", src=WIKI + " (part A, easy rhythm; part B is ours)",
         about="From Beethoven's Ninth Symphony (1824). He was deaf when he wrote it."))
_before_check(2, WRITE("Name the notes", "Write the letter name under each note.", "g'2 c''2 | d''2 a'2 | b'2 d''2 | c''2 g'2", "names"),
              EAR("Find \"Rain, Rain, Go Away\" without any music. It starts on D and uses only D and B."))
# Unit 3
_u(3)["boxes"] += [("symbol", "Dynamics", "How loud to play. <b>f</b> (forte) means loud and <b>p</b> (piano) means soft. Loud is more air, not a tighter mouth."),
                   ("skill", "Low notes", "Low notes need warm, slow air and a loose jaw, as if you were fogging up a window.")]
_u(3)["lines"].insert(0, CLAP("c'2. c'4 | c'4 c'2. | c'2. r4 | c'1", ["1-2-3", "4", "1", "2-3-4", "1-2-3", "1-2-3-4"]))
_line(3, "Low Tide")["music"] = "d'4\\p e' f' g' | a'2 g'2 | f'4 e' d' e' | f'2. r4 | d'4\\f e' f' g' | a'2 b'2 | a'4 g' f' e' | d'1"
_line(3, "Low Tide")["sub"] = "Exercise. Soft the first time, loud the second."
_line(3, "When the Saints Go Marching In")["about"] = "A spiritual from the American South that New Orleans jazz bands made famous."
_after(3, "Old MacDonald Had a Farm",
       L("Old MacDonald duet", "g'4 g' g' d' | e' e' d'2 | b'4 b' a' a' | g'2. d'4 | g'4 g' g' d' | e' e' d'2 | b'4 b' a' a' | g'1", DUET,
         b="b'4 b' b' b' | c'' c'' b'2 | d''4 d'' c'' c'' | b'2. b'4 | b'4 b' b' b' | c'' c'' b'2 | d''4 d'' c'' c'' | b'1", pill="DUET"))
_before_check(3, WRITE("Write the counts", "Write the beats under each note, like the lines above.", "g'2. g'4 | f'2 e'2 | d'4 e' f'2 | g'1", "counts"))
# Unit 4
_u(4)["boxes"] += [("symbol", "Slur", "A curved line over different notes: tongue only the first one and keep the air moving through the rest."),
                   ("word", "Tempo", "How fast the beat goes. <b>Andante</b> is walking pace, <b>Moderato</b> is medium and <b>Allegro</b> is quick.")]
_u(4)["lines"].insert(0, CLAP("c'4 c'2 c'4 | c'2. c'4 | r4 c' c'2 | c'1", ["1", "2-3", "4", "1-2-3", "4", "2", "3-4", "1-2-3-4"]))
_after(4, "Five notes from D", L("Smooth pairs", "d'4( e') fis'( g') | a'( g') fis'( e') | d'( e') fis' g' | a'1", "Slur two notes at a time: one tongue, two notes.", key="g"))
_line(4, "Twinkle, Twinkle, Little Star").update(tempo_word="Andante", about="The tune is a French song from 1761. Mozart wrote twelve variations on it.")
_line(4, "Aura Lee").update(tempo_word="Moderato", about="An American song from 1861. Elvis Presley used the tune for \"Love Me Tender\".")
_line(4, "Yankee Doodle")["tempo_word"] = "Allegro"
_after(4, "Twinkle, Twinkle, Little Star",
       L("Twinkle duet", "d'4 d' a' a' | b' b' a'2 | g'4 g' fis' fis' | e' e' d'2 | a'4 a' g' g' | fis' fis' e'2 | a'4 a' g' g' | fis' fis' e'2 | d'4 d' a' a' | b' b' a'2 | g'4 g' fis' fis' | e' e' d'2", DUET, key="g",
         b="d'4 d' fis' fis' | g' g' fis'2 | e'4 e' d' d' | g' g' fis'2 | fis'4 fis' e' e' | d' d' g'2 | fis'4 fis' e' e' | d' d' g'2 | d'4 d' fis' fis' | g' g' fis'2 | e'4 e' d' d' | g' g' fis'2", pill="DUET"))
_before_check(4, WRITE("Draw the bar lines", "Four beats in every bar. Draw a bar line after each group of four beats.", "d'4 e' fis' g' | a'2 g'2 | fis'4 fis' e'2 | d'1", "bars", key="g"),
              EAR("Find \"Happy Birthday\" without any music, starting on low D. You already know every note it needs."))
# Unit 5
_u(5)["boxes"] += [("skill", "High notes", "Blow faster air and keep your throat open, as if saying \"ee\". Never bite the mouthpiece."),
                   ("word", "Round", "A tune that fits with itself. The second player starts the same tune a little later than the first.")]
_line(5, "G major scale")["pill"] = "SCALE"
_after(5, "G major scale", L("G major arpeggio", "g'4 b' d''2 | g''4 d'' b'2 | g'4 b' d'' g'' | d'' b' g'2", "Notes 1, 3, 5 and 8 of the scale.", key="g", pill="SCALE"))
_line(5, "Frère Jacques").update(pill="ROUND", about="A French round. The second player starts at the beginning when the first player reaches bar 3.")
_before_check(5, WRITE("Write the counts", "Use \"and\" for the second eighth note in a beat.", "g'4 a'8 b' c''4 d'' | e''8 e'' d''4 c''2 | b'8 c'' d''4 g'2", "counts", key="g", bpl=3))
# Unit 6
_u(6)["boxes"] += [("symbol", "Crescendo and decrescendo", "A wedge that opens means get louder little by little (crescendo). A wedge that closes means get softer little by little."),
                   ("symbol", "mf and mp", "Between loud and soft: <b>mf</b> (mezzo forte) is medium loud and <b>mp</b> (mezzo piano) is medium soft.")]
_u(6)["lines"].insert(0, CLAP("c'2. | c'2 c'4 | c'4 c' c' | c'4 r c' | c'8 c' c'4 c' | c'2.", ["1-2-3", "1-2", "3", "1", "2", "3", "1", "3", "1", "and", "2", "3", "1-2-3"], time="3/4", bpl=6))
_line(6, "F major scale")["pill"] = "SCALE"
_after(6, "F major scale", L("F major arpeggio", "f'4 a' c''2 | f''4 c'' a'2 | f'4 a' c'' f'' | c'' a' f'2", key="f", pill="SCALE"))
_line(6, "Cuckoo")["music"] = "c''4\\mf a' r | c'' a' r | g' f' g' | f'2. | g'4\\< g' a' | bes'2 g'4 | a' a' bes' | c''2\\f a'4 | c''2 a'4 | c''2\\> a'4 | bes' a' g' | f'2.\\p"
_after(6, "Cuckoo", L("Cuckoo duet", "c''4 a' r | c'' a' r | g' f' g' | f'2. | g'4 g' a' | bes'2 g'4 | a' a' bes' | c''2 a'4 | c''2 a'4 | c''2 a'4 | bes' a' g' | f'2.", DUET, key="f", time="3/4",
                           b="a'4 f' r | a' f' r | e' d' e' | a'2. | e'4 e' f' | g'2 e'4 | f' f' g' | a'2 f'4 | a'2 f'4 | a'2 f'4 | g' f' e' | f'2.", pill="DUET"))
_before_check(6, WRITE("Name the notes", "Check the key signature first: one of these is a B flat.", "f'2 bes'2 | a'2 c''2 | bes'2 g'2 | f'1", "names", key="f"),
              EAR("Find \"Jingle Bells\" without any music in the key of F. It starts on A."))
# Unit 7
_u(7)["boxes"] += [("symbol", "Fermata", "A dot under an arc. Hold the note longer than its written length."),
                   ("skill", "Quiet fingers", "Keep your fingers close to the keys. Let your right pinky roll to its key: don't lift the hand.")]
_line(7, "C major scale")["pill"] = "SCALE"
_after(7, "C major scale", L("C major arpeggio", "c'4 e' g'2 | c''4 g' e'2 | c'4 e' g' c'' | g' e' c'2", pill="SCALE"))
_line(7, "Michael, Row the Boat Ashore").update(music="c'4 e' | g'4. e'8 g'4 a' | g'2 e'4 g' | a'1 | g'2 e'4 g' | g'4. e'8 f'4 e' | d'2 c'4 d' | e'2 d'2 | c'2\\fermata",
                                                about="A spiritual first written down in 1867 on the Sea Islands of South Carolina.")
_line(7, "Ode to Joy")["about"] = "The full tune, with Beethoven's own rhythm and the tied note in bar 12."
_after(7, "London Bridge", L("London Bridge duet", "g'4. a'8 g'4 f' | e' f' g'2 | d'4 e' f'2 | e'4 f' g'2 | g'4. a'8 g'4 f' | e' f' g'2 | d'2 g'2 | e'4 c'2.", DUET,
                                  b="e'4. f'8 e'4 d' | c' d' e'2 | b'4 c'' d''2 | c'4 d' e'2 | e'4. f'8 e'4 d' | c' d' e'2 | f'2 e'2 | c'4 e'2.", pill="DUET"))
_before_check(7, WRITE("Write the counts", "A dotted quarter note lasts one and a half beats.", "g'4. a'8 b'2 | c''4. b'8 a'4 g' | e'4. f'8 g'2", "counts", bpl=3))
# Unit 8
_u(8)["boxes"] += [("symbol", "Accent", "A small arrowhead over a note: give the start of it an extra push of air."),
                   ("word", "Accompaniment", "The part that supports the melody. In the finale a piano, or the player, accompanies you.")]
_u(8)["lines"].insert(0, CLAP("c'4. c'8 c'4 c' | c'8 c' c' c' c'2 | c'4 r c'8 c' c'4 | c'1", ["1-2", "and", "3", "4", "1", "and", "2", "and", "3-4", "1", "3", "and", "4", "1-2-3-4"]))
_line(8, "D major scale")["pill"] = "SCALE"
_after(8, "D major scale", L("D major arpeggio", "d'4 fis' a'2 | d''4 a' fis'2 | d'4 fis' a' d'' | a' fis' d'2", key="d", pill="SCALE"))
_line(8, "Amazing Grace")["about"] = "Words by John Newton, an English clergyman, in 1772. The tune is American."
_line(8, "Happy Birthday to You")["about"] = "Two sisters, Patty and Mildred Hill, wrote the tune in 1893 as \"Good Morning to All\"."
_line(8, "Auld Lang Syne")["about"] = "A Scottish song with words by Robert Burns (1788), sung around the world at New Year."
_before_check(8, WRITE("Draw the bar lines", "Three beats in every bar this time.", "d'4 fis' a' | d''2 a'4 | b'4 a' g' | fis'2.", "bars", key="d", time="3/4"),
              EAR("Pick any tune you love and find it without music. Then write its first four bars on the staff paper your teacher gives you."))

# ---------------------------------------------------------------- the finale: a solo with piano accompaniment
# Sax part in written pitch; piano part written in the same frame (as if the sax were in C) and transposed for each edition.
FINALE = dict(title="Jupiter", sub="Gustav Holst, from The Planets (easy rhythm)", key="c", time="3/4", tempo=76, tempo_word="Andante maestoso",
    about="Holst wrote The Planets between 1914 and 1917. This is the great tune from the middle of \"Jupiter, the Bringer of Jollity\".",
    src=WIKI + " (\"Thaxted\"; the dotted eighth and sixteenth written as two even eighth notes). The piano part is ours.",
    music="r2. | r2 e'8(\\mf g') | a'4. c''8 b' g' | c''8( d'') c''4 b' | a'8 b' a'4 g' | e'2 e'8( g') | a'4. c''8 b' g' | c''8( d'') e''4 e'' | e''8( d'') c''4 d'' | c''2 e'8(\\f g') | "
          "a'4. c''8 b' g' | c''8( d'') c''4 b' | a'8 b' a'4 g' | e'2 e'8( g') | a'4. c''8 b' g' | c''8( d'') e''4 e'' | e''8( d'') c''4 d'' | c''2. ~ | c''2.\\fermata",
    rh=["<c' e' g'>2.", "<b d' f'>2.", "<c' f' a'>2 <b d' g'>4", "<c' e' g'>2 <b d' g'>4", "<c' f' a'>2 <c' e' g'>4", "<c' e' a'>2 <b d' g'>4", "<c' f' a'>2 <b d' g'>4", "<c' e' g'>4 <c' e' a'>2", "<c' f' a'>2 <b d' f'>4", "<c' e' g'>2 <b d' g'>4",
        "r4 <c' f' a'>4 <b d' g'>4", "r4 <c' e' g'>4 <b d' g'>4", "r4 <c' f' a'>4 <c' e' g'>4", "r4 <c' e' a'>4 <b d' g'>4", "r4 <c' f' a'>4 <b d' g'>4", "r4 <c' e' a'>4 <c' e' a'>4", "r4 <c' f' a'>4 <b d' f'>4", "<c' e' g'>2.", "<c' e' g' c''>2."],
    lh=["c2.", "g,2.", "f,2 g,4", "c2 g,4", "f,2 c4", "a,2 g,4", "f,2 g,4", "c4 a,2", "f,2 g,4", "c2 g,4",
        "f,2 g,4", "c2 g,4", "f,2 c4", "a,2 g,4", "f,2 g,4", "c4 a,2", "f,2 g,4", "c2.", "<c, c>2."])
FINALE_LINE = L(FINALE["title"], FINALE["music"], FINALE["sub"], key="c", time="3/4", tempo=FINALE["tempo"], tempo_word=FINALE["tempo_word"], about=FINALE["about"], src=FINALE["src"], pill="SOLO")
PILL["SOLO"] = "#D4922A"
RHYTHM_GYM = [L("Level 1", "c'4 c' c'2 | c'2 c'4 c' | c'4 r c' r | c'2. r4 | c'1 | r2 c'2", "Quarter, half, dotted half and whole notes.", rhythm=True, badge="CLAP", bpl=6),
              L("Level 2", "c'8 c' c'4 c'2 | c'4 c'8 c' c'4 c' | c'8 c' c' c' c'4 r | c'2 c'8 c' c'4 | r4 c'8 c' c'2 | c'1", "Add eighth notes.", rhythm=True, badge="CLAP", bpl=6),
              L("Level 3", "c'4. c'8 c'2 | c'4 c'4. c'8 c'4 | c'4. c'8 c'4. c'8 | c'8 c' c'4. c'8 c'4 | c'2 ~ c'8 c' c'4 | c'1", "Add dotted quarter notes and a tie.", rhythm=True, badge="CLAP", bpl=6),
              L("Level 4", "c'4 r c'8 c' r4 | r4 c' r c' | c'8 c' r4 c'2 | r2 c'4 c' | c'4. c'8 r4 c' | c'1", "Rests in new places.", rhythm=True, badge="CLAP", bpl=6),
              L("Level 5", "c'2. | c'4 c'2 | c'8 c' c'4 c' | c'4. c'8 c'4 | c'4 r c'8 c' | c'2.", "Three beats in a bar.", time="3/4", rhythm=True, badge="CLAP", bpl=6),
              L("Level 6", "c'4. c'8 c'4 | c'2. ~ | c'4 c'8 c' c'4 | r4 c' c' | c'4. c'8 c' c' | c'2.", "Three beats, with a tie and a dotted quarter.", time="3/4", rhythm=True, badge="CLAP", bpl=6)]

SCALES = [("G major", "g", "g'4 a' b' c'' | d'' e'' fis'' g'' | g'' fis'' e'' d'' | c'' b' a' g' | g'4 b' d'' g'' | d'' b' g'2"),
          ("F major", "f", "f'4 g' a' bes' | c'' d'' e'' f'' | f'' e'' d'' c'' | bes' a' g' f' | f'4 a' c'' f'' | c'' a' f'2"),
          ("C major", "c", "c'4 d' e' f' | g' a' b' c'' | c'' b' a' g' | f' e' d' c' | c'4 e' g' c'' | g' e' c'2"),
          ("D major", "d", "d'4 e' fis' g' | a' b' cis'' d'' | d'' cis'' b' a' | g' fis' e' d' | d'4 fis' a' d'' | a' fis' d'2")]
SCALE_LINES = [L(name + " scale and arpeggio", music, key=key, bpl=3, tempo=60) for name, key, music in SCALES]
CHART = ["c'", "d'", "e'", "f'", "fis'", "g'", "a'", "bes'", "b'", "c''", "cis''", "d''", "e''", "f''", "fis''", "g''"]

# ---------------------------------------------------------------- LilyPond helpers
TOK = re.compile(r"^([a-g])(is|es)?([',]*)(\d*\.*)(.*)$")
def note_name(tok):
    m = TOK.match(tok)
    return m and (m.group(1).upper() + {"is": "♯", "es": "♭", None: ""}[m.group(2)])
def pitch_of(tok):
    m = TOK.match(tok); return m and m.group(1) + (m.group(2) or "") + m.group(3)

def _part(music, it, breaks=True, hl=True):
    bars = [b.strip() for b in music.split("|")]; npick = 1 if it.get("partial") else 0
    out, names, tied = [], [], False
    for i, b in enumerate(bars):
        toks = []
        for t in b.split():
            p = pitch_of(t)
            if p:
                if not tied: names.append(note_name(t))
                tied = "~" in t
                if hl and p in it.get("hl", ()): t = "\\once \\override NoteHead.color = #hi \\once \\override Stem.color = #hi " + t
            elif t == "~": tied = True
            toks.append(t)
        out.append(" ".join(toks)); n = i + 1 - npick
        if i < len(bars) - 1: out.append("\\break" if breaks and n > 0 and n % it.get("bpl", 4) == 0 else "|")
    return " ".join(out), names

def ly_line(it, blank=False):
    """One numbered line as a LilyPond file: a single staff, a one-line rhythm staff, a written exercise, or a two-part duet."""
    music, names = ("s1 | s1 | s1 | s1", []) if blank else _part(it["music"], it)
    quiz = it.get("quiz")
    lyr = ["____"] * len(names) if quiz in ("names", "counts") else it.get("lyr") or (names if it.get("names") else None)
    lyrics = ('\\new Lyrics \\lyricsto "m" { \\lyricmode { ' + " ".join('"%s"' % x for x in lyr) + " } }") if lyr else ""
    partial = "\\partial %s " % it["partial"] if it.get("partial") else ""
    key = it.get("key", "c"); kly = key[0] + ("es" if key.endswith("b") else "") + " \\major"
    tempo = '\\tempo "%s" ' % it["tempo_word"] if it.get("tempo_word") else ""
    start = '\\bar ".|:" ' if it.get("repeat") else ""
    end = '\\bar ":|."' if it.get("repeat") else '\\bar "|."'
    if quiz == "bars": start += "\\override Staff.BarLine.stencil = ##f "; end = "\\revert Staff.BarLine.stencil " + end
    head = "\\clef treble \\key %s \\time %s %s%s%s" % (kly, it.get("time", "4/4"), tempo, partial, start)
    if it.get("rhythm"):
        staves = '\\new RhythmicStaff { \\new Voice = "m" { \\time %s %s %s } } %s' % (it.get("time", "4/4"), music, end, lyrics)
    elif it.get("b"):
        second, _ = _part(it["b"], it, breaks=False, hl=False)
        staves = ('\\new StaffGroup << \\new Staff \\with { instrumentName = \\markup \\bold "A" shortInstrumentName = \\markup \\bold "A" } { \\new Voice = "m" { %s %s %s } } '
                  '\\new Staff \\with { instrumentName = \\markup \\bold "B" shortInstrumentName = \\markup \\bold "B" } { %s %s %s } >>' % (head, music, end, head, second, end))
    else:
        staves = '\\new Staff { \\new Voice = "m" { %s %s %s } } %s' % (head, music, end, lyrics)
    indent = "indent = 7\\mm short-indent = 7\\mm" if it.get("b") else "indent = 0"
    return r"""\version "2.24.0"
#(set-global-staff-size %d)
#(define hi (rgb-color 0.78 0.48 0.05))
\header { tagline = ##f }
\paper { %s line-width = %.1f\mm ragged-right = ##f ragged-last = ##f system-system-spacing.basic-distance = #%d system-system-spacing.padding = #2.5 }
\layout { \context { \Score \remove "Bar_number_engraver" %s \override MetronomeMark.font-size = #-1 }
  \context { \Lyrics \override LyricText.font-name = "DejaVu Sans Bold" \override LyricText.font-size = #-1.5 \override LyricText.color = #(rgb-color 0.42 0.47 0.52) } }
\score { << %s >> }
""" % (STAFF, indent, LINE_MM, 15 if lyr else 13, "\\override TimeSignature.stencil = ##f" if blank else "", staves)

def render(src, tag, transparent=False):
    h = hashlib.md5((src + tag).encode()).hexdigest()[:14]; base = os.path.join(CACHE, h); png = base + ".png"
    if not os.path.exists(png):
        open(base + ".ly", "w").write(src)
        r = subprocess.run(["lilypond", "-s", "--png", "-dresolution=300", "-dcrop", "-o", base, base + ".ly"], capture_output=True, text=True)
        crop = base + ".cropped.png"
        assert os.path.exists(crop), r.stderr[-800:] + "\n" + src
        im = Image.open(crop)
        if transparent:
            g = im.convert("L"); out = Image.new("RGBA", g.size, (0, 0, 0, 0)); out.putalpha(g.point(lambda v: 255 - v)); out.save(png)
        else: im.convert("RGB").save(png)
    return png

def note_png(ly):
    src = ('\\version "2.24.0"\n\\header { tagline = ##f }\n\\paper { indent = 0 line-width = 27\\mm ragged-right = ##f }\n'
           '\\layout { \\context { \\Staff \\remove Time_signature_engraver } }\n{ \\clef treble \\accidentalStyle forget ' + ly + '1 }\n')
    return render(src, "note", transparent=True)

FING = {}
for _ly, _name, _keys, _n in B.FINGERINGS:
    for part in _ly.split(): FING[part] = _keys
FING["bes'"] = {"L1", "bis"}

# ---------------------------------------------------------------- drawing
P_BODY = ParagraphStyle("pb", parent=B.body, fontSize=9.6, leading=13.4, spaceAfter=0)
def para_h(text, w, style=P_BODY):
    p = Paragraph(text, style); return p, p.wrap(w, 2000)[1]

class Page:
    """Collects blocks (height, draw) for one unit and flows them over pages, spreading spare room between blocks."""
    def __init__(self, c, book): self.c, self.book, self.blocks = c, book, []
    def add(self, h, draw, gap=10, it=None): self.blocks.append((h, draw, gap, it))
    def flush(self, kicker, title, qr=None):
        """Fewest pages that fit (gaps may shrink a little), blocks shared out evenly, spare room spread between blocks."""
        import itertools
        c, hs, gs = self.c, [b[0] for b in self.blocks], [b[2] for b in self.blocks]
        R = (H - M - 70 + 8) - 58; n = len(hs); MINF = 0.45
        def need(i, j, f=1.0): return sum(hs[i:j]) + f * sum(gs[i + 1:j])
        pages, i = 1, 0
        for j in range(1, n + 1):
            if need(i, j, MINF) > R: pages += 1; i = j - 1
        best = None
        for cuts in itertools.combinations(range(1, n), pages - 1):
            edges = [0] + list(cuts) + [n]
            if any(need(a, b, MINF) > R for a, b in zip(edges, edges[1:])): continue
            score = max(need(a, b) for a, b in zip(edges, edges[1:]))
            if best is None or score < best[0]: best = (score, edges)
        edges = best[1]
        for k, (a, b) in enumerate(zip(edges, edges[1:])):
            ytop = B.header(c, kicker, title if k == 0 else title + " (continued)") + 8
            if k == 0 and qr: qr(c)
            nat = need(a, b); f, extra = 1.0, 0.0
            if nat > R: f = (R - sum(hs[a:b])) / max(1e-9, sum(gs[a + 1:b]))
            elif b - a > 1: extra = min(26, (R - nat) / (b - a - 1))
            y = ytop
            for q in range(a, b):
                h, draw, gap, it = self.blocks[q]
                if q > a: y -= gap * f + extra
                if it is not None: it["_page"] = self.book.n
                draw(c, y); y -= h
            self.book.footer(); c.showPage()
        self.blocks = []

class Book:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=letter); self.n = 1; self.line_no = 0; self.toc = []
        self.c.setTitle("Saxophone Beginner Booklet"); self.c.setAuthor("Alex Attard Music")
    def footer(self):
        c = self.c
        c.setStrokeColor(HexColor(RULE)); c.setLineWidth(0.6); c.line(M, 40, W - M, 40)
        c.setFont("Pop-M", 8.5); c.setFillColor(HexColor(SLATE)); c.drawString(M, 28, "Alex Attard Music  ·  Saxophone Beginner Booklet")
        c.setFont("Pop-B", 9); c.setFillColor(HexColor(AMBER)); c.drawRightString(W - M, 28, str(self.n)); self.n += 1

def note_card(c, x0, ytop, w, h, ly, name, tip, tint=TINT):
    c.setFillColor(HexColor(tint)); c.roundRect(x0, ytop - h, w, h, 8, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 6.8); c.drawString(x0 + 10, ytop - 14, " ".join("NEW NOTE"))
    c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, x0 + 10, ytop - 33, name, "Pop-B", 17)
    top, bot = ytop - 12, ytop - h + (30 if tip else 10)
    u = (top - bot) / (B.KY_MAX - B.KY_MIN); dw = (B.KX_MAX - B.KX_MIN) * u
    right = x0 + w - 12
    B.draw_keys(c, right - dw - B.KX_MIN * u, top, u, FING[ly])
    im = ImageReader(note_png(ly)); iw, ih = im.getSize(); tw = min(64, right - dw - 12 - (x0 + 8)); th = tw * ih / iw
    c.drawImage(im, x0 + 8, (top + bot) / 2 - th / 2 - 8, tw, th, mask="auto")
    if tip:
        p, ph = para_h(tip, w - 20, ParagraphStyle("tip", parent=P_BODY, fontSize=7.9, leading=10.2)); p.drawOn(c, x0 + 10, ytop - h + 7 + max(0, (20 - ph) / 2))

def concept(c, x0, ytop, w, kind, title, text):
    col, tint, label = KIND[kind]
    p, ph = para_h(text, w - 26); h = ph + 36
    c.setFillColor(HexColor(tint)); c.roundRect(x0, ytop - h, w, h, 7, fill=1, stroke=0)
    c.setFillColor(HexColor(col)); c.roundRect(x0, ytop - h, 5, h, 2, fill=1, stroke=0)
    c.setFont("Pop-B", 6.8); c.drawString(x0 + 16, ytop - 14, " ".join(label))
    c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, x0 + 16, ytop - 28, title, "Pop-B", 10.6)
    p.drawOn(c, x0 + 16, ytop - h + 7)
    return h
def concept_h(w, text): return para_h(text, w - 26)[1] + 36

def _pill(c, x, y, text, col):
    w = pdfmetrics.stringWidth(text, "Pop-B", 7.2) + 12
    c.setFillColor(HexColor(col)); c.roundRect(x, y - 14, w, 14, 4, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Pop-B", 7.2); c.drawString(x + 6, y - 10.3, text); return w
def music_block(book, pg, it, png):
    im = ImageReader(png); iw, ih = im.getSize(); w = iw * 72 / 300; h = ih * 72 / 300
    badge = it.get("badge"); no = None
    if not badge: book.line_no += 1; no = book.line_no; it["_no"] = no
    ap = para_h(it["about"], CW - 27, ParagraphStyle("ab", parent=P_BODY, fontName="DJ-I", fontSize=8.2, leading=10.6, textColor=HexColor(MUTED))) if it.get("about") else None
    top = 18 + (ap[1] + 3 if ap else 0)
    def draw(c, y, no=no):
        x = M
        if badge: x += _pill(c, x, y, badge, PILL[badge]) + 7
        else:
            c.setFillColor(HexColor(SLATE)); c.roundRect(M, y - 14, 20, 14, 4, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("Pop-B", 8.4); c.drawCentredString(M + 10, y - 10.6, str(no)); x += 27
        c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, x, y - 11, it["title"], "Pop-B", 11)
        x += sum(pdfmetrics.stringWidth(ch, "DJ-B" if ch in "♭♯" else "Pop-B", 11) for ch in it["title"]) + 8
        if it.get("pill"): x += _pill(c, x, y, it["pill"], PILL[it["pill"]]) + 8
        if it.get("sub"):
            c.setFillColor(HexColor(MUTED)); B.draw_mixed(c, x, y - 11, it["sub"], "DJ", 8.4)
        if badge != "WRITE":
            c.setStrokeColor(HexColor("#B9C2CB")); c.setLineWidth(0.9); c.roundRect(W - M - 12, y - 13.5, 12, 12, 2.5, fill=0, stroke=1)   # tick it when you can play it
        if ap: ap[0].drawOn(c, M + 27, y - 16 - ap[1])
        c.drawImage(im, M - 1, y - top - h, w, h)
    pg.add(top + h, draw, gap=9, it=it)

def ear_block(pg, it):
    p, ph = para_h(it["text"], CW - 110); hh = max(ph + 14, 28)
    def draw(c, y):
        col, tint, _ = KIND["skill"]
        c.setFillColor(HexColor(tint)); c.roundRect(M, y - hh, CW, hh, 7, fill=1, stroke=0)
        _pill(c, M + 10, y - (hh - 14) / 2, "PLAY BY EAR", col); p.drawOn(c, M + 96, y - hh + (hh - ph) / 2)
    pg.add(hh, draw, gap=12)

def blank_staff_png():
    return render(ly_line(dict(music="", key="c", time="4/4"), blank=True), "blank")

def build_unit(book, k, u):
    c = book.c; pg = Page(c, book); book.toc.append(("Unit %d" % (k + 1), u["title"], book.n))
    notes = u["notes"]; gap = 10; nw = (CW - gap * (len(notes) - 1)) / len(notes) if len(notes) >= 2 else (CW - gap * 2) / 3
    one = len(notes) == 1; bw1 = CW - nw - gap; beside = u["boxes"][:2] if one else []; below = u["boxes"][2:] if one else u["boxes"]
    nh = max(122, sum(concept_h(bw1, b[2]) for b in beside) + 8 * (len(beside) - 1)) if one else 122
    def draw_notes(c, y):
        x = M
        for i, (ly, name, tip) in enumerate(notes):
            note_card(c, x, y, nw, nh, ly, name, tip, TINT); x += nw + gap
        yy = y
        for kind, title, text in beside: yy -= concept(c, x, yy, bw1, kind, title, text) + 8     # the room beside a single note card holds two idea boxes
    pg.add(nh, draw_notes, gap=10)
    for r in range(0, len(below), 2):                        # the other idea boxes, two to a row
        row = below[r:r + 2]; bw = (CW - gap) / 2 if len(row) == 2 else CW; bh = max(concept_h(bw, b[2]) for b in row)
        pg.add(bh, lambda c, y, row=row, bw=bw: [concept(c, M + i * (bw + gap), y, bw, *b) for i, b in enumerate(row)], gap=10)
    for it in u["lines"]:
        if it["type"] == "line": music_block(book, pg, it, PNGS[id(it)])
        elif it["type"] == "ear": ear_block(pg, it)
        elif it["type"] == "create":
            im = ImageReader(blank_staff_png()); iw, ih = im.getSize(); w = iw * 72 / 300; h = ih * 72 / 300
            def draw(c, y, it=it, im=im, w=w, h=h):
                col = KIND["word"][0]
                c.setFillColor(HexColor("#3E8E7E")); c.roundRect(M, y - 14, 44, 14, 4, fill=1, stroke=0)
                c.setFillColor(white); c.setFont("Pop-B", 7.4); c.drawCentredString(M + 22, y - 10.3, "CREATE")
                c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 11); c.drawString(M + 51, y - 11, it["title"])
                c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 8.4); c.drawString(M + 51 + pdfmetrics.stringWidth(it["title"], "Pop-B", 11) + 9, y - 11, it["sub"])
                c.drawImage(im, M - 1, y - 20 - h, w, h)
            pg.add(20 + h, draw, gap=10)
        else:
            items = it["items"]; hh = 26 + 15 * len(items)
            def draw(c, y, items=items, hh=hh):
                c.setFillColor(HexColor("#F3F5F7")); c.roundRect(M, y - hh, CW, hh, 7, fill=1, stroke=0)
                c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 10.6); c.drawString(M + 14, y - 17, "Checkpoint")
                c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 8.4); c.drawString(M + 84, y - 17, "Tick each one when it is true. Then you are ready for the next unit.")
                for i, t in enumerate(items):
                    yy = y - 33 - 15 * i
                    c.setStrokeColor(HexColor(SLATE)); c.setLineWidth(0.9); c.setFillColor(white); c.roundRect(M + 14, yy - 2, 10, 10, 2, fill=1, stroke=1)
                    c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, M + 31, yy, t, "DJ", 9.4)
            pg.add(hh, draw, gap=12)
    first = next(it for it in u["lines"] if it["type"] == "line" and not it.get("badge"))
    pg.flush("Unit %d" % (k + 1), u["title"], qr=(lambda c: unit_qr(c, first)) if CODE else None)

# ---------------------------------------------------------------- the player: one tune per numbered line
PLAY = "https://alexattardmusic.com/play/"
BELOW = {"alto": 9, "tenor": 14}
PCS = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
SLUGS = {}
def slug_of(it):
    if id(it) not in SLUGS:
        base = "sax-beginner-%s-" % ED + re.sub(r"[^a-z0-9]+", "-", (it.get("slug") or it["title"]).lower().replace("♯", " sharp").replace("♭", " flat").replace("è", "e")).strip("-")
        s, k = base, 2
        while s in SLUGS.values(): s = "%s-%d" % (base, k); k += 1
        SLUGS[id(it)] = s
    return SLUGS[id(it)]
def qr_img(slug):
    import qrcode
    q = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(PLAY + "?t=" + slug + "&c=" + re.sub(r"[^A-Z0-9]", "", CODE.upper())); q.make(fit=True)
    buf = io.BytesIO(); q.make_image(fill_color=SLATE, back_color="white").save(buf, format="PNG"); buf.seek(0); return ImageReader(buf)
def unit_qr(c, first):
    qs = 62; qx = W - M - qs + 3; qy = H - 30 - qs
    c.drawImage(qr_img(slug_of(first)), qx, qy, qs, qs)
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 5.6); c.drawCentredString(qx + qs / 2, qy - 5, " ".join("PLAY ALONG") + "  ·  " + CODE)

LTOK = re.compile(r"^([a-g])(is|es)?([',]*)(\d*\.*)([~()]*)$")
BEATS = {"1": 4.0, "2": 2.0, "2.": 3.0, "4": 1.0, "4.": 1.5, "8": 0.5}
def rest_abc(d):
    out = []
    for step in (4.0, 3.0, 2.0, 1.0, 0.5):
        while d >= step - 1e-9: out.append("z" + PX.LEN[step]); d -= step
    return out
STRIP = re.compile(r"\\(?:[a-zA-Z]+|[<>!])|-[.>]")
def parse_part(it, music, bpb, wk, below):
    """Written notes -> (events in sounding pitch, one ABC string per bar, marks, the first sounding pitch class of each bar)."""
    import gen_study as g
    sp = PX.Abc(PX.keysig(wk, False)); ev, abc, marks, roots, held, dur = [], [], [], [], None, "4"
    for bi, toks in enumerate([b.split() for b in music.split("|")]):
        sp.bar(); t, parts, mk, prev8, root, notes = 0.0, [], "", None, None, []
        for tok in toks:
            if tok == "~": notes[-1][2] = True; continue
            tok = STRIP.sub("", tok)
            if not tok: continue
            m = re.match(r"^r(\d+\.?)?$", tok)
            if m: dur = m.group(1) or dur; notes.append(["r", BEATS[dur], False, "", ""]); continue
            m = LTOK.match(tok); assert m, (it["title"], tok)
            if m.group(4): dur = m.group(4)
            n = g.Note(m.group(1).upper(), {"is": 1, "es": -1, None: 0}[m.group(2)], 3 + m.group(3).count("'") - m.group(3).count(","))
            notes.append([n, BEATS[dur], "~" in m.group(5), "(" if "(" in m.group(5) else "", ")" if ")" in m.group(5) else ""])
        total = sum(x[1] for x in notes)
        if total < bpb - 1e-9:                                       # a pick-up bar gets rests in front, a short last bar gets them behind
            pad = [["r", d, False, "", ""] for d in [{"z8": 4.0, "z6": 3.0, "z4": 2.0, "z2": 1.0, "z": 0.5}[z] for z in rest_abc(bpb - total)]]
            notes = pad + notes if bi == 0 else notes + pad
        assert abs(sum(x[1] for x in notes) - bpb) < 1e-9, (it["title"], "bar %d" % (bi + 1))
        for n, d, tie, so, sc in notes:
            if n == "r":
                parts.append("z" + PX.LEN[d]); held = None; prev8 = None
            else:
                sounding = n.midi - below
                if root is None: root = sounding % 12
                txt = so + sp.note(n) + PX.LEN[d] + ("-" if tie else "") + sc; mk += "."
                if d == 0.5 and prev8 is not None and int(prev8) == int(t): parts[-1] += txt       # two eighths in one beat share a beam
                else: parts.append(txt)
                prev8 = t if d == 0.5 else None
                if held and held[1] == sounding: held[2] += d
                else: held = [bi * bpb + t, sounding, d, 90]; ev.append(held)
                if not tie: held = None
            t = round(t + d, 6)
        abc.append(" ".join(parts)); marks.append(mk); roots.append(root)
    return ev, abc, marks, roots

PIANO = re.compile(r"<([^>]+)>(\d+\.?)|([a-g](?:is|es)?[',]*)(\d+\.?)|r(\d+\.?)")
def piano_events(bars, bpb, shift):
    import gen_study as g
    def midi(nm):
        m = re.match(r"^([a-g])(is|es)?([',]*)$", nm); return g.Note(m.group(1).upper(), {"is": 1, "es": -1, None: 0}[m.group(2)], 3 + m.group(3).count("'") - m.group(3).count(",")).midi + shift
    ev = []
    for bi, bar in enumerate(bars):
        t = 0.0
        for m in PIANO.finditer(bar):
            d = BEATS[m.group(2) or m.group(4) or m.group(5)]
            for nm in (m.group(1).split() if m.group(1) else [m.group(3)] if m.group(3) else []): ev.append([bi * bpb + t, midi(nm), d, 64])
            t += d
        assert abs(t - bpb) < 1e-9, ("piano bar", bi + 1, bar)
    return ev

def to_tune(it, chapter):
    """One numbered line as a player tune: the written notes on screen, a click (or a drone under long tones), and the notes played back."""
    import gen_study as g
    bpb = int(it["time"][0]); wkey = it["key"].upper(); below = BELOW[ED]; wk = g.parse_note(wkey)
    drone = it["title"].lower().startswith("long tone"); tune_like = bool(it.get("src")) or bool(it.get("b"))
    music = it["music"] + (" | " + it["music"] if it.get("repeat") else "")
    ev, abc, marks, roots = parse_part(it, music, bpb, wk, below)
    chords, last = [], (wk.pc - below) % 12
    for r in roots:
        if r is not None: last = r
        rr = last if drone else (wk.pc - below) % 12
        chords.append([dict(sym=PCS[rr], beats=bpb, root=rr, degs=[0, 2, 4, 5, 7, 9, 11], scale="Ionian (major)")])
    T = it.get("tempo") or (60 if drone else (84 if bpb == 3 else 76) if tune_like else 66)   # the player opens at this tempo; the presets go up from it
    sec = dict(id="notes", title="Notes", tab="Notes", desc=(it.get("about") or it.get("sub") or "").rstrip("."), rh=ev, lh=[], abc=dict(rh=abc, marks=marks))
    tune = dict(format="aam-tune/1", slug=slug_of(it), title="%d · %s" % (it["_no"], it["title"]), subtitle="Saxophone Beginner Booklet · " + chapter,
                instrument=ED, concert_key=PCS[(wk.pc - below) % 12], native=g.INSTRUMENTS[ED][1] % 12, style="drone" if drone else "click", keys="off",
                hide=["chords", "solo", "names"], hear=True, first_bar=1, chart_tempo=T, tempo_presets=[T, T + 20, T + 40], form=[], bars=chords, sections=[sec],
                notation=dict(key=wkey, staves="treble"), page=it["_page"])
    if it.get("b"):                                                  # a duet: part B on a second treble staff, with its own on/off button
        evb, abcb, _, _ = parse_part(it, it["b"], bpb, wk, below)
        sec["lh"] = evb; sec["abc"]["lh"] = abcb; tune["notation"].update(lh=["z" + PX.LEN[float(bpb)]] * len(abc), lh_clef="treble"); tune["hand_labels"] = ["Part A", "Part B"]
    if it is FINALE_LINE:                                            # the solo: the piano accompaniment plays under the written saxophone part
        sec["lh"] = piano_events(FINALE["rh"], bpb, {"alto": 3, "tenor": -2}[ED]) + piano_events(FINALE["lh"], bpb, {"alto": 3, "tenor": -2}[ED])
        sec["lh"].sort(); tune["hand_labels"] = ["Saxophone", "Piano"]
        sec["desc"] = "Switch off Saxophone to play with the piano alone. The piano plays two bars first"
    if bpb != 4: tune["meter"] = [bpb, 4]
    if it.get("src"): tune["source"] = it["src"]
    return tune

def publish(repo):
    pdf_id = "sax-beginner-" + ED; title = "Saxophone Beginner Booklet · " + {"alto": "Alto", "tenor": "Tenor"}[ED]
    ip = os.path.join(repo, "index.json"); idx = json.load(open(ip))
    h = hashlib.sha256(("aam:" + re.sub(r"[^A-Z0-9]", "", CODE.upper())).encode()).hexdigest()
    clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == h and p["id"] != pdf_id]; assert not clash, "that code is already used by " + clash[0]
    contents, slugs = [], []
    groups = [("Unit %d · %s" % (k + 1, u["title"]), [it for it in u["lines"] if it["type"] == "line" and not it.get("badge")]) for k, u in enumerate(UNITS)]
    groups += [("Finale · A solo with piano", [FINALE_LINE]), ("Finish · Four scales", SCALE_LINES)]
    old = next((p for p in idx["pdfs"] if p["id"] == pdf_id), None)
    for ch, lines in groups:
        items = []
        for it in lines:
            t = to_tune(it, ch); json.dump(t, open(os.path.join(repo, "tunes", t["slug"] + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
            idx["tunes"][t["slug"]] = dict(title=t["title"], subtitle=t["subtitle"]); items.append(t["slug"]); slugs.append(t["slug"])
        contents.append(dict(title=ch, items=items))
    kept = [x for x in (old["tunes"] if old else []) if x not in slugs]      # lines dropped from the book stay playable: a student may hold an earlier printing
    entry = dict(id=pdf_id, title=title, hash=h, tunes=slugs + kept, contents=contents)
    rest = [p for p in idx["pdfs"] if p["id"] != pdf_id]; at = next((i for i, p in enumerate(rest) if p.get("free")), len(rest))
    idx["pdfs"] = rest[:at] + [entry] + rest[at:]
    json.dump(idx, open(ip, "w"), ensure_ascii=False, indent=1)
    print("published %d tunes for %s" % (len(slugs), title))

# ---------------------------------------------------------------- front and back pages
def cover(book):
    c = book.c; band = H * 0.58
    c.setFillColor(HexColor(SLATE)); c.rect(0, H - band, W, band, fill=1, stroke=0)
    png, clef = B.cover_staff_png(); im = ImageReader(png); iw, ih = im.getSize(); sw = 290
    c.drawImage(im, M, H - band + 48, sw, sw * ih / iw, mask="auto")
    B.draw_sax(c, 345, H - band + 36, 1.95)
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 11); c.drawString(M, H - 110, " ".join("ALEX ATTARD MUSIC"))
    c.setFillColor(white); c.setFont("Pop-B", 50); c.drawString(M, H - 198, "Saxophone")
    c.setFont("Pop-L", 38); c.drawString(M, H - 244, "Beginner Booklet")
    c.setFillColor(HexColor(AMBER)); c.setFont("Pop-M", 17); B.draw_mixed(c, M, H - 284, {"alto": "E♭ Alto Saxophone", "tenor": "B♭ Tenor Saxophone", None: "Alto and Tenor Saxophone"}[ED], "Pop-M", 17)
    top, bot = H - band - 44, 92
    c.setFillColor(HexColor(TINT)); c.roundRect(M, bot, CW, top - bot, 10, fill=1, stroke=0)
    c.setFillColor(HexColor(AMBER)); c.rect(M, bot, 5, top - bot, fill=1, stroke=0)
    y = top - 46
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 20); c.drawString(M + 30, y, "Your first notes start here.")
    p, ph = para_h("This book takes you from your very first sound to real tunes, one or two new notes at a time. Every unit starts with long tones, "
                   "adds a new idea, and ends with music you already know. Keep it on your stand, play a little every day, and bring it to every lesson.",
                   CW - 60 - (150 if CODE else 0), ParagraphStyle("cv", parent=B.body, fontSize=11.8 if CODE else 13, leading=18 if CODE else 20)); p.drawOn(c, M + 30, y - 18 - ph)
    if CODE:
        qs = 104; qx = W - M - 24 - qs; qy = (top + bot) / 2 - qs / 2 + 30
        c.setFillColor(white); c.roundRect(qx - 6, qy - 6, qs + 12, qs + 12, 8, fill=1, stroke=0)
        c.drawImage(qr_img(slug_of(next(it for it in UNITS[0]["lines"] if it["type"] == "line" and not it.get("badge")))), qx, qy, qs, qs)
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 8.5); c.drawCentredString(qx + qs / 2, qy - 22, " ".join("PLAY ALONG"))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 15); c.drawCentredString(qx + qs / 2, qy - 41, CODE)
        c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 7.4); c.drawCentredString(qx + qs / 2, qy - 55, "Scan, or type this code at"); c.drawCentredString(qx + qs / 2, qy - 65, "alexattardmusic.com/play")
        c.setFillColor(HexColor(SLATE))
    c.setFont("Pop-M", 14); c.drawString(M + 30, y - 18 - ph - 28, "Alex")
    c.setFillColor(HexColor(AMBER)); c.rect(0, 0, W, 6, fill=1, stroke=0)
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 11); c.drawString(M, 40, "Alex Attard Music")
    c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 10); c.drawRightString(W - M, 40, "alexattardmusic.com")
    c.showPage(); book.n += 1

def how_page(book):
    c = book.c; y = B.header(c, "Start here", "How this book works")
    p, ph = para_h("There are eight units and a finale. Each unit adds one, two or three notes and a few new ideas. Work through a unit in order, top to bottom, "
                   "and don't move on until its Checkpoint is ticked. Everything new arrives in a colored box, and the color tells you what kind of thing it is.", CW, ParagraphStyle("hb", parent=B.body, fontSize=10.5, leading=15.5)); p.drawOn(c, M, y - ph); y -= ph + 14
    bw = (CW - 10) / 2
    demo = [("note", "A note you haven't played before", "Shows the note on the staff and which keys to press. Its first appearances in the music are printed in amber."),
            ("rhythm", "A new note length or time signature", "Clap and count it first. A CLAP line gives you the rhythm on its own."),
            ("key", "A new key signature or scale", "Tells you which notes are sharp or flat for the whole piece."),
            ("symbol", "A new sign in the music", "Marks such as repeat signs, dynamics, slurs and fermatas."),
            ("word", "A new word", "The musical terms you need, in plain English. They are all in the glossary at the back."),
            ("skill", "A saxophone skill", "How to do something on the instrument: tonguing, low notes, high notes.")]
    for r in range(0, 6, 2):
        hh = max(concept_h(bw, d[2]) for d in demo[r:r + 2])
        for i, d in enumerate(demo[r:r + 2]): concept(c, M + i * (bw + 10), y, bw, *d)
        y -= hh + 9
    y -= 8
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y - 12, "The labels on the lines"); y -= 28
    rows = [("12", SLATE, "<b>A numbered line.</b> Play these in order. Tick the box at its end when you can play it three times in a row without a mistake. Every numbered line is in the player."),
            ("CLAP", PILL["CLAP"], "<b>Rhythm only.</b> Clap it and count out loud before you play the lines that follow."),
            ("SCALE", PILL["SCALE"], "<b>A scale or arpeggio.</b> Learn it by heart. Scales are the alphabet of every tune."),
            ("DUET", PILL["DUET"], "<b>Two parts, A and B.</b> Learn both. A teacher or friend plays the other part, or the player does. A ROUND is one tune that two players start at different times."),
            ("WRITE", PILL["WRITE"], "<b>Pencil work.</b> Name notes, write counts or draw bar lines."),
            ("PLAY BY EAR", KIND["skill"][0], "<b>No music.</b> Find a tune you know by listening and trying."),
            ("CREATE", "#3E8E7E", "<b>Your turn.</b> Write a few bars of your own, then play them.")]
    for badge, col, text in rows:
        bwid = 70
        c.setFillColor(HexColor(col)); c.roundRect(M, y - 13, bwid, 15, 4, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 7.6); c.drawCentredString(M + bwid / 2, y - 8.8, badge)
        p, ph = para_h(text, CW - bwid - 12); p.drawOn(c, M + bwid + 12, y + 2 - ph); y -= max(ph, 15) + 8
    book.footer(); c.showPage()
    # practice and progress
    y = B.header(c, "Start here", "Practice and progress")
    y = B.tip_box(c, M, y, CW, "A good practice session (15 minutes)", ["<b>3 minutes:</b> long tones from the unit you are on.", "<b>2 minutes:</b> a scale you know, by heart.",
                                                                           "<b>5 minutes:</b> the next two or three numbered lines, slowly.", "<b>5 minutes:</b> a tune you are learning, then one you already know, just for fun."]) - 18
    y = B.tip_box(c, M, y, CW, "Practicing with the player", ["Scan the code at the top of a unit, or type your booklet code at alexattardmusic.com/play.",
                                                               "Every numbered line plays at any tempo. Start slow, and speed up only when it is easy.",
                                                               "<b>Hear it</b> plays the line for you. Switch it off to play on your own with the metronome.",
                                                               "In a duet, switch off <b>Part A</b> or <b>Part B</b> and play that part yourself."]) - 18
    y = B.tip_box(c, M, y, CW, "For teachers and parents", ["Each unit works as two or three weekly lessons. The Checkpoint is the signal to move on.",
                                                             "Part B of every duet stays inside the notes the student already knows, so two students can swap parts.",
                                                             "The finale has a piano accompaniment. The piano score is printed after the solo, in concert pitch for this edition."]) - 24
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y, "My progress"); y -= 12
    cw = (CW - 16) / 2; rh = min(24, (y - 60) / 5)
    for i, (ku, title, pgn) in enumerate(book.toc):
        x = M + (i // 5) * (cw + 16); yy = y - (i % 5) * rh - 12
        c.setStrokeColor(HexColor(SLATE)); c.setLineWidth(0.9); c.setFillColor(white); c.roundRect(x, yy - 2, 10, 10, 2, fill=1, stroke=1)
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 8.4); c.drawString(x + 18, yy, ku.upper())
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 9.6); c.drawString(x + 60, yy, title)
        c.setFillColor(HexColor(MUTED)); c.setFont("DJ", 8.4); c.drawRightString(x + cw, yy, "page %d" % pgn)
    book.footer(); c.showPage()

def start_page(book):
    c = book.c; y = B.header(c, "Before the first note", "Getting started")
    cols = [("Put it together", ["Put the thin end of the reed in your mouth for a minute to wet it.", "Put the neck strap on.", "Push the neck into the body with a gentle twist and tighten the screw.",
                                  "Twist the mouthpiece about halfway onto the cork.", "Lay the reed flat on the mouthpiece. Its tip sits just below the mouthpiece tip. Tighten the ligature until it is snug.",
                                  "Hook the saxophone onto the strap."]),
            ("Hold it", ["Sit or stand tall. Bring the saxophone to you: don't lean down to it.", "Shorten the strap until the mouthpiece meets your mouth. The strap carries the weight.",
                         "Left hand on top, right hand below. Left thumb on its button, right thumb under its hook.", "Curve your fingers and rest the pads on the pearl keys."]),
            ("Make a sound", ["Rest your top teeth on the mouthpiece, about a fingernail's width from the tip.", "Roll your bottom lip slightly over your bottom teeth as a cushion.",
                              "Close your lips around the mouthpiece like a drawstring bag, as if saying \"oo\".", "Breathe in low and deep. Blow fast, steady air.",
                              "Start the note by touching the tip of your tongue to the reed and letting go: \"too\".", "Try it first with just the mouthpiece and neck. Aim for four steady beats."])]
    cw = (CW - 20) / 3; ymin = y
    for i, (title, steps) in enumerate(cols):
        x = M + i * (cw + 10); yy = y
        c.setFillColor(HexColor(AMBER)); c.circle(x + 11, yy - 9, 11, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 11); c.drawCentredString(x + 11, yy - 13, str(i + 1))
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 12.5); c.drawString(x + 28, yy - 13.5, title); yy -= 30
        for s in steps:
            p, ph = para_h(s, cw - 12, ParagraphStyle("st", parent=P_BODY, fontSize=9, leading=12.4))
            c.setFillColor(HexColor(AMBER)); c.circle(x + 3, yy - 6, 1.8, fill=1, stroke=0); p.drawOn(c, x + 11, yy - ph); yy -= ph + 6
        ymin = min(ymin, yy)
    y = ymin - 12
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y, "How to read a fingering diagram"); y -= 10
    mh = y - 150
    B.key_map(c, M, y, CW, mh); y -= mh + 12
    B.tip_box(c, M, y, CW, "Look after it", ["Pull a swab through the body and the neck after every session.", "Take the reed off, dry it and keep it flat in a reed case.", "Never lift the saxophone by its neck or its keys."])
    book.footer(); c.showPage()

def reading_page(book):
    c = book.c; y = B.header(c, "Before the first note", "Reading music") - 2
    rows = [("The staff and the treble clef", "Music is written on five lines called a <b>staff</b>. The sign at the start is the <b>treble clef</b>. A note higher on the staff sounds higher. These are your first five notes.",
             dict(music="g'1 | a'1 | b'1 | c''1 | d''1", names=True, bpl=5)),
            ("Bars and beats", "<b>Bar lines</b> divide the music into <b>bars</b>. The <b>time signature</b> 4/4 means four beats in every bar. Tap your foot once for each beat.",
             dict(music="b'4 b' b' b' | b' b' b' b' | b' b' b' b' | b'1", lyr=["1", "2", "3", "4"] * 3 + ["1-2-3-4"])),
            ("How long each note lasts", "A <b>whole note</b> is 4 beats, a <b>half note</b> is 2 and a <b>quarter note</b> is 1.",
             dict(music="b'1 | b'2 b'2 | b'4 b' b' b' | b'1", lyr=["4 beats", "2", "2", "1", "1", "1", "1", "4 beats"])),
            ("Rests", "A <b>rest</b> is a measured silence. Each note length has a rest of the same length. Keep counting through it.",
             dict(music="r1 | r2 b'2 | r4 b' r b' | b'1", lyr=["3-4", "2", "4", "1-2-3-4"]))]
    blocks = []
    for title, text, it in rows:
        png = render(ly_line(dict(key="c", time="4/4", **it)), "line"); im = ImageReader(png); iw, ih = im.getSize()
        p, ph = para_h(text, CW, ParagraphStyle("rb", parent=B.body, fontSize=10.2, leading=14.6, spaceAfter=0)); blocks.append((title, p, ph, im, iw * 72 / 300, ih * 72 / 300))
    used = sum(22 + b[2] + 8 + b[5] for b in blocks); gap = min(34, (y - 58 - used) / (len(blocks) - 1))
    for title, p, ph, im, w, h in blocks:
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y - 13, title)
        p.drawOn(c, M, y - 22 - ph); c.drawImage(im, M - 1, y - 30 - ph - h, w, h); y -= 30 + ph + h + gap
    book.footer(); c.showPage()

def scales_page(book):
    c = book.c; pg = Page(c, book); book.toc.append(("Finish", "Four scales, and what comes next", book.n))
    p, ph = para_h("You now know every note in four major scales. Play one each day as part of your warm-up: the scale up and down, then its <b>arpeggio</b> (notes 1, 3, 5 and 8). "
                   "When all four are easy at ♩ = 80, you are ready for the <b>Saxophone Welcome Booklet</b>: every key, faster fingers and your first jazz.", CW, ParagraphStyle("sb", parent=B.body, fontSize=10.4, leading=15))
    pg.add(ph, lambda c, y: p.drawOn(c, M, y - ph), gap=14)
    for it in SCALE_LINES: music_block(book, pg, it, render(ly_line(it), "line"))
    def cert(c, y):
        h = 96; c.setFillColor(HexColor(TINT)); c.roundRect(M, y - h, CW, h, 10, fill=1, stroke=0); c.setFillColor(HexColor(AMBER)); c.rect(M, y - h, 5, h, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 16); c.drawString(M + 24, y - 30, "Beginner Booklet complete")
        c.setFont("DJ", 10); c.drawString(M + 24, y - 56, "Student: ______________________________      Date: ________________")
        c.drawString(M + 24, y - 78, "Teacher: ______________________________")
    pg.add(96, cert, gap=18)
    pg.flush("Finish", "Four scales, and what comes next")

def finale_pages(book):
    c = book.c; pg = Page(c, book); book.toc.append(("Finale", "A solo with piano", book.n))
    p, ph = para_h("The last piece in the book is a <b>solo with piano</b>. A pianist, your teacher or the player plays the accompaniment while you play the tune. "
                   "The piano plays two bars on its own first: count them, and come in on beat 3 of the second bar. The whole tune comes twice. Make the second time bigger than the first.",
                   CW, ParagraphStyle("fb", parent=B.body, fontSize=10.4, leading=15))
    pg.add(ph, lambda c, y: p.drawOn(c, M, y - ph), gap=14)
    row = [("word", "Solo", "A piece for one player. Everyone else is there to support you, so play out."),
           ("word", "Andante maestoso", "A walking pace, played in a grand and stately way.")]
    bw = (CW - 10) / 2; bh = max(concept_h(bw, b[2]) for b in row)
    pg.add(bh, lambda c, y: [concept(c, M + i * (bw + 10), y, bw, *b) for i, b in enumerate(row)], gap=14)
    music_block(book, pg, FINALE_LINE, render(ly_line(FINALE_LINE), "line"))
    items = ["I can count the piano introduction and come in on time.", "The second time through is louder and grander than the first.", "I hold the last note until the piano stops.", "I have performed it for an audience, even an audience of one."]
    hh = 26 + 15 * len(items)
    def draw(c, y):
        c.setFillColor(HexColor(TINT)); c.roundRect(M, y - hh, CW, hh, 7, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 10.6); c.drawString(M + 14, y - 17, "Performance checklist")
        for i, t in enumerate(items):
            yy = y - 33 - 15 * i
            c.setStrokeColor(HexColor(SLATE)); c.setLineWidth(0.9); c.setFillColor(white); c.roundRect(M + 14, yy - 2, 10, 10, 2, fill=1, stroke=1)
            c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, M + 31, yy, t, "DJ", 9.4)
    pg.add(hh, draw, gap=16)
    pg.flush("Finale", "A solo with piano", qr=(lambda c: unit_qr(c, FINALE_LINE)) if CODE else None)
    # the pianist's score
    y = B.header(c, "For the pianist", FINALE["title"] + ": piano accompaniment")
    ed = {"alto": "E♭ alto saxophone", "tenor": "B♭ tenor saxophone", None: "E♭ alto saxophone"}[ED]
    p2, ph2 = para_h("The top staff is the solo part as the student reads it, for %s. The piano part is in concert pitch. %s" % (ed.replace("♭", "<font name='DJ'>♭</font>"), FINALE["sub"] + "."), CW, P_BODY)
    p2.drawOn(c, M, y - ph2); y -= ph2 + 12
    im = ImageReader(render(piano_score_ly(), "piano")); iw, ih = im.getSize(); w = CW; h = w * ih / iw
    if h > y - 58: h = y - 58; w = h * iw / ih
    c.drawImage(im, M, y - h, w, h); book.footer(); c.showPage()

def piano_score_ly():
    tr = {"alto": "ees", "tenor": "bes,", None: "ees"}[ED]; it = dict(FINALE_LINE); it["bpl"] = 4
    sax, _ = _part(it["music"], it)
    return r"""\version "2.24.0"
#(set-global-staff-size 16.5)
\header { tagline = ##f }
\paper { indent = 12\mm short-indent = 0 line-width = 176\mm ragged-last = ##f system-system-spacing.basic-distance = #22 system-system-spacing.padding = #5 }
\layout { \context { \Score \override BarNumber.font-size = #-1 } }
\score { <<
  \new Staff \with { instrumentName = "Sax" fontSize = #-2 \override StaffSymbol.staff-space = #(magstep -2) } { \clef treble \key c \major \time 3/4 \tempo "%s" 4 = %d %s \bar "|." }
  \new PianoStaff \with { instrumentName = "Piano" } <<
    \new Staff { \clef treble \transpose c %s { \key c \major %s } }
    \new Staff { \clef bass \transpose c %s { \key c \major %s } } >>
>> }
""" % (FINALE["tempo_word"], FINALE["tempo"], sax, tr, " | ".join(FINALE["rh"]), tr, " | ".join(FINALE["lh"]))

def rhythm_page(book):
    c = book.c; pg = Page(c, book); book.toc.append(("Practice", "Rhythm gym", book.n))
    p, ph = para_h("Rhythm is half of music. Use these lines at any point in the book: set the metronome to ♩ = 60, count out loud and clap. "
                   "Then play each line on one note you know. When a level is easy, raise the tempo.", CW, ParagraphStyle("rg", parent=B.body, fontSize=10.4, leading=15))
    pg.add(ph, lambda c, y: p.drawOn(c, M, y - ph), gap=14)
    for it in RHYTHM_GYM: music_block(book, pg, it, render(ly_line(it), "line"))
    steps = ["<b>Count</b> one empty bar out loud, then keep counting through the line.", "<b>Clap</b> the notes. Hold your hands together for long notes.",
             "<b>Play</b> the line on one note you know.", "<b>Speed up</b> by one notch only when it is easy three times in a row."]
    hh = 30 + 16 * len(steps)
    def tips(c, y):
        c.setFillColor(HexColor(KIND["rhythm"][1])); c.roundRect(M, y - hh, CW, hh, 7, fill=1, stroke=0); c.setFillColor(HexColor(KIND["rhythm"][0])); c.roundRect(M, y - hh, 5, hh, 2, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 10.6); c.drawString(M + 16, y - 18, "Four steps for any rhythm")
        for i, t in enumerate(steps):
            pp, ph = para_h("%d.  %s" % (i + 1, t), CW - 32); pp.drawOn(c, M + 16, y - 26 - 16 * i - ph)
    pg.add(hh, tips, gap=18)
    pg.flush("Practice", "Rhythm gym")

def glossary_page(book):
    c = book.c; y = B.header(c, "Reference", "Glossary"); book.toc.append(("Reference", "Glossary", book.n))
    ents = [(t, re.sub(r"<[^>]+>", "", x), k + 1) for k, u in enumerate(UNITS) for kind, t, x in u["boxes"]]
    ents += [("Solo", "A piece for one player.", 0), ("Arpeggio", "The notes of a chord played one at a time: notes 1, 3, 5 and 8 of a scale.", 5), ("Duet", "A piece for two players.", 1),
             ("Transposing", "Playing the same tune starting on a different note.", 6), ("Embouchure", "The way your mouth holds the mouthpiece.", 0), ("Metronome", "A device that clicks a steady beat at the tempo you set.", 0)]
    seen = set(); ents = [e for e in sorted(ents, key=lambda e: e[0].lower()) if not (e[0] in seen or seen.add(e[0]))]
    cols = 3; gw = (CW - 18 * (cols - 1)) / cols; st = ParagraphStyle("gl", parent=P_BODY, fontSize=7.9, leading=10.4)
    paras = [para_h("<font name='Pop-B' size='8.8' color='%s'>%s</font>%s<br/>%s" % (SLATE, t.replace("♯", "<font name='DJ-B'>♯</font>").replace("♭", "<font name='DJ-B'>♭</font>"),
                    ("  <font color='%s' size='7'>Unit %d</font>" % (AMBER, k)) if k else "", x), gw, st) for t, x, k in ents]
    total = sum(ph + 8 for _, ph in paras); col, yy, acc = 0, y, 0
    for pr, ph in paras:
        if col < cols - 1 and acc >= total * (col + 1) / cols - ph / 2: col += 1; yy = y
        pr.drawOn(c, M + col * (gw + 18), yy - ph); yy -= ph + 8; acc += ph + 8
        assert yy > 50, "glossary overflows"
    book.footer(); c.showPage()

def chart_page(book):
    c = book.c; y = B.header(c, "Reference", "Fingering chart: the notes in this book"); book.toc.append(("Reference", "Fingering chart", book.n))
    cols, rows, gap = 4, 4, 9; gw = (CW - (cols - 1) * gap) / cols; gh = (y - 60 - (rows - 1) * gap) / rows
    names = {}
    for u in UNITS:
        for ly, name, tip in u["notes"]: names[ly] = name
    for k, ly in enumerate(CHART):
        col, row = k % cols, k // cols; x0 = M + col * (gw + gap); y1 = y - row * (gh + gap)
        c.setFillColor(HexColor(TINT if (row + col) % 2 == 0 else "#F3F5F7")); c.roundRect(x0, y1 - gh, gw, gh, 8, fill=1, stroke=0)
        c.setFillColor(HexColor(SLATE)); B.draw_mixed(c, x0 + 10, y1 - 19, names[ly], "Pop-B", 12)
        top, bot = y1 - 12, y1 - gh + 10; u = (top - bot) / (B.KY_MAX - B.KY_MIN); dw = (B.KX_MAX - B.KX_MIN) * u; right = x0 + gw - 10
        B.draw_keys(c, right - dw - B.KX_MIN * u, top, u, FING[ly])
        im = ImageReader(note_png(ly)); iw, ih = im.getSize(); tw = right - dw - 8 - (x0 + 6); th = tw * ih / iw
        c.drawImage(im, x0 + 6, (top + bot) / 2 - th / 2 - 6, tw, th, mask="auto")
    book.footer(); c.showPage()

def sources_text():
    out = []
    for u in UNITS:
        for it in u["lines"]:
            if it["type"] == "line" and it.get("src"): out.append((it["title"], it["src"]))
    return out

PNGS = {}
def main():
    items = [it for u in UNITS for it in u["lines"] if it["type"] == "line"]
    with ThreadPoolExecutor(8) as ex:
        for it, png in zip(items, ex.map(lambda it: render(ly_line(it), "line"), items)): PNGS[id(it)] = png
    assert not (CODE or REPO) or ED, "give the edition (alto or tenor) with --code or --publish"
    out = os.path.join(B.OUT, "Sax_Beginner_Booklet%s.pdf" % ("_" + ED.capitalize() if ED else ""))
    # two passes: the first finds the page numbers for the progress table
    toc = []
    for final in (False, True):
        book = Book(out if final else os.path.join(CACHE, "pass1.pdf")); cover(book)
        book.toc = list(toc); how_page(book); book.toc = []
        start_page(book); reading_page(book)
        for k, u in enumerate(UNITS): build_unit(book, k, u)
        finale_pages(book); scales_page(book); rhythm_page(book); glossary_page(book); chart_page(book); book.c.save()
        toc = [t for t in book.toc if t[0].startswith("Unit") or t[0] == "Finale"]
    print(out, book.n - 1, "pages,", book.line_no, "numbered lines")
    if REPO: publish(REPO)
    if "--sources" in ARGS:
        for t, s in sources_text(): print("  %-34s %s" % (t, s))

if __name__ == "__main__":
    main()
