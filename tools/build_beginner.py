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
        "key": ("#3E8E7E", "#E6F3F0", "NEW KEY"), "word": ("#B5533C", "#F8EAE6", "NEW WORD")}
CACHE = os.path.join(B.OUT, "beg"); os.makedirs(CACHE, exist_ok=True)
STAFF = 21
LINE_MM = 176.0

# ---------------------------------------------------------------- the curriculum
# music: LilyPond, absolute pitch, bars separated by "|".  names: print letter names under the notes.
# hl: notes to print in amber (the new notes, where they first appear).  bpl: bars per line.  src: where the tune was checked.
def L(title, music, sub="", key="c", time="4/4", names=False, hl=(), bpl=4, partial=None, lyr=None, src=None, tempo=None, slug=None):
    # slug: give the OLD title here when you rename a line, so QR codes on copies already printed keep working
    return dict(slug=slug, type="line", title=title, music=music, sub=sub, key=key, time=time, names=names, hl=set(hl), bpl=bpl, partial=partial, lyr=lyr, src=src, tempo=tempo)

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
         ("word", "Slur", "A curved line over different notes. Tongue only the first one and keep the air moving through the rest.")],
  lines=[L("Long tone: C sharp", "cis''1 | r1 | cis''1 | r1", "Open notes go sharp easily. Listen and keep the air steady.", names=True, hl=["cis''"]),
         L("B, C sharp, D", "b'2 cis''2 | d''1 | d''2 cis''2 | b'1", "From no fingers to all fingers.", key="d"),
         L("D major scale", "d'4 e' fis' g' | a' b' cis'' d'' | d'' cis'' b' a' | g' fis' e' d'", key="d"),
         L("Slur two, tongue two", "d'4( e') fis' g' | a'( b') cis'' d'' | d''( cis'') b' a' | g'( fis') e' d'", key="d"),
         L("Amazing Grace", "d'4 | g'2 b'8( g') | b'2 a'4 | g'2 e'4 | d'2 d'4 | g'2 b'8( g') | b'2 a'4 | d''2 b'4 | d''4.( b'8) d''( b') | g'2 d'4 | e'4.( g'8) g'( e') | d'2 d'4 | g'2 b'8( g') | b'2 a'4 | g'2.", "American traditional", key="g", time="3/4", partial="4", src=WIKI),
         L("Happy Birthday to You", "d'8 d' | e'4 d' g' | fis'2 d'8 d' | e'4 d' a' | g'2 d'8 d' | d''4 b' g' | fis' e' c''8 c'' | b'4 g' a' | g'2", "M. and P. Hill (easy rhythm)", key="g", time="3/4", partial="4", src=WIKI + " (pick-ups as even eighth notes)"),
         L("Auld Lang Syne", "c'4 | f'4. f'8 f'4 a' | g'4. f'8 g'4 a' | f'4. f'8 a'4 c'' | d''2. d''4 | c''4. a'8 a'4 f' | g'4. f'8 g'4 a' | f'4.( d'8) d'4( c') | f'2. d''4 | c''4.( a'8) a'4( f') | g'4. f'8 g'4 d'' | c''4.( a'8) a'4( c'') | d''2. d''4 | c''4. a'8 a'4 f' | g'4. f'8 g'4 a' | f'4.( d'8) d'4( c') | f'2.", "Scottish traditional", key="f", partial="4", src=WIKI),
         dict(type="check", items=["I can play C♯ in tune with nothing to hold on to.", "I can slur without stopping the air.", "I can perform one of these tunes for someone."])]),
]
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

def ly_line(it, blank=False):
    bars = [b.strip() for b in it["music"].split("|")] if not blank else ["s1"] * 4
    first = [bars.pop(0)] if it.get("partial") else []
    out, names, tied = [], [], False
    for i, b in enumerate(first + bars):
        toks = []
        for t in b.split():
            p = pitch_of(t)
            if p and p[0] != "r" and TOK.match(t).group(1) in "abcdefg":
                if not tied: names.append(note_name(t))
                tied = "~" in t
                if p in it.get("hl", ()): t = "\\once \\override NoteHead.color = #hi \\once \\override Stem.color = #hi " + t
            toks.append(t)
        out.append(" ".join(toks))
        n = i + 1 - len(first)
        if n > 0 and n % it.get("bpl", 4) == 0 and i < len(first + bars) - 1: out.append("\\break")
        elif i < len(first + bars) - 1: out.append("|")
    lyr = it.get("lyr") or (names if it.get("names") else None)
    lyrics = ('\\new Lyrics \\lyricsto "m" { \\lyricmode { ' + " ".join('"%s"' % x for x in lyr) + " } }") if lyr else ""
    partial = "\\partial %s " % it["partial"] if it.get("partial") else ""
    key = it.get("key", "c"); kly = key[0] + ("es" if key.endswith("b") else "") + " \\major"
    return r'''\version "2.24.0"
#(set-global-staff-size %d)
#(define hi (rgb-color 0.78 0.48 0.05))
\header { tagline = ##f }
\paper { indent = 0 line-width = %.1f\mm ragged-right = ##f ragged-last = ##f system-system-spacing.basic-distance = #%d system-system-spacing.padding = #2.5 }
\layout { \context { \Score \remove "Bar_number_engraver" %s }
  \context { \Lyrics \override LyricText.font-name = "DejaVu Sans Bold" \override LyricText.font-size = #-1.5 \override LyricText.color = #(rgb-color 0.42 0.47 0.52) } }
\score { << \new Staff { \new Voice = "m" { \clef treble \key %s \time %s %s%s \bar "%s" } } %s >> }
''' % (STAFF, LINE_MM, 15 if lyr else 13, "\\override TimeSignature.stencil = ##f" if blank else "", kly, it.get("time", "4/4"), partial, " ".join(out), "|." , lyrics)

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

def music_block(book, pg, it, png):
    im = ImageReader(png); iw, ih = im.getSize(); w = iw * 72 / 300; h = ih * 72 / 300
    book.line_no += 1; no = book.line_no; it["_no"] = no
    def draw(c, y, no=no):
        c.setFillColor(HexColor(SLATE)); c.roundRect(M, y - 14, 20, 14, 4, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("Pop-B", 8.4); c.drawCentredString(M + 10, y - 10.6, str(no))
        c.setFillColor(HexColor(SLATE)); x = M + 27
        B.draw_mixed(c, x, y - 11, it["title"], "Pop-B", 11)
        tw = sum(pdfmetrics.stringWidth(ch, "DJ-B" if ch in "♭♯" else "Pop-B", 11) for ch in it["title"])
        if it.get("sub"):
            c.setFillColor(HexColor(MUTED)); B.draw_mixed(c, x + tw + 9, y - 11, it["sub"], "DJ", 8.4)
        c.setStrokeColor(HexColor("#B9C2CB")); c.setLineWidth(0.9); c.roundRect(W - M - 12, y - 13.5, 12, 12, 2.5, fill=0, stroke=1)   # tick it when you can play it
        c.drawImage(im, M - 1, y - 18 - h, w, h)
    pg.add(18 + h, draw, gap=9, it=it)

def blank_staff_png():
    return render(ly_line(dict(music="", key="c", time="4/4"), blank=True), "blank")

def build_unit(book, k, u):
    c = book.c; pg = Page(c, book); book.toc.append(("Unit %d" % (k + 1), u["title"], book.n))
    notes = u["notes"]; gap = 10; nw = (CW - gap * (len(notes) - 1)) / len(notes) if len(notes) >= 2 else (CW - gap * 2) / 3
    one = len(notes) == 1; bw1 = CW - nw - gap
    nh = max(122, sum(concept_h(bw1, b[2]) for b in u["boxes"]) + 8 * (len(u["boxes"]) - 1)) if one else 122
    def draw_notes(c, y):
        x = M
        for i, (ly, name, tip) in enumerate(notes):
            note_card(c, x, y, nw, nh, ly, name, tip, TINT); x += nw + gap
        if one:                                              # the room beside a single note card holds the idea boxes
            yy = y
            for kind, title, text in u["boxes"]: yy -= concept(c, x, yy, bw1, kind, title, text) + 8
    pg.add(nh, draw_notes, gap=10)
    boxes = [] if one else u["boxes"]
    if len(boxes) == 2:
        bw = (CW - gap) / 2; bh = max(concept_h(bw, b[2]) for b in boxes)
        def draw_boxes(c, y):
            for i, (kind, title, text) in enumerate(boxes): concept(c, M + i * (bw + gap), y, bw, kind, title, text)
        pg.add(bh, draw_boxes, gap=12)
    for it in u["lines"]:
        if it["type"] == "line": music_block(book, pg, it, PNGS[id(it)])
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
    first = next(it for it in u["lines"] if it["type"] == "line")
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
def to_tune(it, chapter):
    """One numbered line as a player tune: the written notes on screen, a click (or a drone under long tones), and the notes played back."""
    import gen_study as g
    bpb = int(it["time"][0]); wkey = it["key"].upper(); below = BELOW[ED]
    wk = g.parse_note(wkey); sp = PX.Abc(PX.keysig(wk, False))
    drone = it["title"].lower().startswith("long tone"); tune_like = bool(it.get("src"))
    bars = [b.split() for b in it["music"].split("|")]
    ev, abc, marks, chords, held, dur, last_root = [], [], [], [], None, "4", (wk.pc - below) % 12
    for bi, toks in enumerate(bars):
        sp.bar(); t, parts, mk, prev8, root = 0.0, [], "", None, None
        notes = []
        for tok in toks:
            if tok == "~": notes[-1][2] = True; continue
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
        abc.append(" ".join(parts)); marks.append(mk)
        if root is not None: last_root = root
        r = last_root if drone else (wk.pc - below) % 12
        chords.append([dict(sym=PCS[r], beats=bpb, root=r, degs=[0, 2, 4, 5, 7, 9, 11], scale="Ionian (major)")])
    T = it.get("tempo") or (60 if drone else (84 if bpb == 3 else 76) if tune_like else 66)   # the player opens at this tempo; the presets go up from it
    sec = dict(id="notes", title="Notes", tab="Notes", desc=(it.get("sub") or "").rstrip("."), rh=ev, lh=[], abc=dict(rh=abc, marks=marks))
    tune = dict(format="aam-tune/1", slug=slug_of(it), title="%d · %s" % (it["_no"], it["title"]), subtitle="Saxophone Beginner Booklet · " + chapter,
                instrument=ED, concert_key=PCS[(wk.pc - below) % 12], native=g.INSTRUMENTS[ED][1] % 12, style="drone" if drone else "click", keys="off",
                hide=["chords", "solo", "names"], hear=True, first_bar=1, chart_tempo=T, tempo_presets=[T, T + 20, T + 40], form=[], bars=chords, sections=[sec],
                notation=dict(key=wkey, staves="treble"), page=it["_page"])
    if bpb != 4: tune["meter"] = [bpb, 4]
    if it.get("src"): tune["source"] = it["src"]
    return tune

def publish(repo):
    pdf_id = "sax-beginner-" + ED; title = "Saxophone Beginner Booklet · " + {"alto": "Alto", "tenor": "Tenor"}[ED]
    ip = os.path.join(repo, "index.json"); idx = json.load(open(ip))
    h = hashlib.sha256(("aam:" + re.sub(r"[^A-Z0-9]", "", CODE.upper())).encode()).hexdigest()
    clash = [p["id"] for p in idx["pdfs"] if p.get("hash") == h and p["id"] != pdf_id]; assert not clash, "that code is already used by " + clash[0]
    contents, slugs = [], []
    groups = [("Unit %d · %s" % (k + 1, u["title"]), [it for it in u["lines"] if it["type"] == "line"]) for k, u in enumerate(UNITS)] + [("Finish · Four scales", SCALE_LINES)]
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
        c.drawImage(qr_img(slug_of(UNITS[0]["lines"][0])), qx, qy, qs, qs)
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
    p, ph = para_h("There are eight units. Each one adds one, two or three notes and one or two new ideas. Work through a unit in order, top to bottom, "
                   "and don't move on until its Checkpoint is ticked.", CW, ParagraphStyle("hb", parent=B.body, fontSize=10.5, leading=15.5)); p.drawOn(c, M, y - ph); y -= ph + 16
    bw = (CW - 10) / 2
    demo = [("note", "A note you haven't played before", "Shows the note on the staff and which keys to press. Its first appearances in the music are printed in amber."),
            ("rhythm", "A new note length or time signature", "Clap and count it before you play it."),
            ("key", "A new key signature", "Tells you which notes are sharp or flat for the whole piece."),
            ("word", "A new word", "The musical terms you need, in plain English.")]
    for i, (kind, t, tx) in enumerate(demo):
        hh = max(concept_h(bw, d[2]) for d in demo[(i // 2) * 2:(i // 2) * 2 + 2])
        concept(c, M + (i % 2) * (bw + 10), y, bw, kind, t, tx)
        if i % 2: y -= hh + 10
    y -= 10
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y - 12, "On every page"); y -= 26
    for badge, text in [("12", "<b>Numbered lines.</b> Play them in order. Tick the box at the end of a line when you can play it three times in a row without a mistake."),
                        ("LT", "<b>Long tones first.</b> Every unit and every practice session starts with them. They build your sound."),
                        ("CREATE", "<b>Your turn.</b> Write a few bars of your own on the empty staff, then play them."),
                        ("✓", "<b>Checkpoint.</b> Three things to be able to do before you start the next unit.")]:
        bwid = 44
        c.setFillColor(HexColor(SLATE if badge != "CREATE" else "#3E8E7E")); c.roundRect(M, y - 13, bwid, 15, 4, fill=1, stroke=0)
        c.setFillColor(white); c.setFont("DJ-B" if badge == "✓" else "Pop-B", 8); c.drawCentredString(M + bwid / 2, y - 9, badge)
        p, ph = para_h(text, CW - bwid - 12); p.drawOn(c, M + bwid + 12, y + 2 - ph); y -= max(ph, 15) + 9
    y -= 8
    y = B.tip_box(c, M, y, CW, "A good practice session (15 minutes)", ["<b>3 minutes:</b> long tones from the unit you are on.", "<b>5 minutes:</b> the next two or three numbered lines, slowly.",
                                                                           "<b>5 minutes:</b> a tune you are learning.", "<b>2 minutes:</b> a tune you already know, just for fun."]) - 22
    c.setFillColor(HexColor(SLATE)); c.setFont("Pop-B", 13); c.drawString(M, y, "My progress"); y -= 12
    cw = (CW - 16) / 2; rh = min(22, (y - 60) / 4)
    for i, (ku, title, pgn) in enumerate(book.toc):
        x = M + (i // 4) * (cw + 16); yy = y - (i % 4) * rh - 12
        c.setStrokeColor(HexColor(SLATE)); c.setLineWidth(0.9); c.setFillColor(white); c.roundRect(x, yy - 2, 10, 10, 2, fill=1, stroke=1)
        c.setFillColor(HexColor(AMBER)); c.setFont("Pop-B", 8.4); c.drawString(x + 18, yy, ku.upper())
        c.setFillColor(HexColor(SLATE)); c.setFont("Pop-M", 9.6); c.drawString(x + 56, yy, title)
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
        scales_page(book); chart_page(book); book.c.save()
        toc = [t for t in book.toc if t[0].startswith("Unit")]
    print(out, book.n - 1, "pages,", book.line_no, "numbered lines")
    if REPO: publish(REPO)
    for t, s in sources_text(): print("  %-34s %s" % (t, s))

if __name__ == "__main__":
    main()
