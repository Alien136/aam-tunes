# Alex Attard Music play-along: where things stand (18 Nov 2026)

Everything needed to carry on from any conversation is in this repository and in the saved skills (`lead-sheet`, `starter-book`).

## What is live
- Player: `player/aam-player.html` is the block pasted into the Elementor HTML widget on alexattardmusic.com/play. The site has the latest version (start_key, http/https fix, booklets, key change, page turn).
- Library: `index.json` + `tunes/`. PDFs and codes:
  - G.I. piano, F Blues piano (earlier codes, see index.json ids `gi-piano`, `fblues-piano`)
  - Winter Wonderland piano, Winter Wonderland alto
  - F Blues alto (4 pages: arpeggios, scales, patterns, licks)
  - Saxophone Welcome Booklet alto and tenor (21 exercises each)
  - Codes are never written in this repository: they are in the private project doc "Alex Attard Music knowledge base".
- Codes are stored as hashes: sha256("aam:" + CODE without dash, upper case).

- 17 Nov: the player uses the full-screen app layout on every screen (was phones only): wide screens get a centred 1180px column, full tab names, a tempo slider and bar/chord readout on the play bar, a centred settings card, a "← Website" link and space bar = play/stop. **Alex still has to paste this version into the Elementor Player widget.**

## How the player is released (since 18 Nov 2026)
- The Elementor HTML widget on /play holds only `player/loader.html` (pasted once). It loads `release/player.html` from this repository, keeps a saved copy for when GitHub can't be reached, and shows a "could not load" message otherwise.
- `player/aam-player.html` is the **test copy**: edit it, push, and try it on the live site with `?player=test` added to the address.
- To release: `AAM_CODE=<master code> python3 tools/release.py` (runs `tools/check_release.js`: every tune, every tab, phone / half window / laptop / wide, plus a play test of each kind of tune; refuses to release if anything is clipped, colliding, overflowing or erroring), then commit and push. Live within about five minutes. Never edit `release/player.html` by hand.
- The check needs `tone` and `abcjs` locally: `npm install` in `tools/`, or set `AAM_NODE_MODULES`. The master code is never written in this repository.
- Sounds: `sounds/v2/` (see `sounds/README.md`); Mix sliders and default levels are in the player.
- Usage counts (18 Nov): the player sends anonymous Google Analytics events when the site has gtag / Tag Manager: `aam_open` (tune opened) and `aam_practice` (one stretch of playing of 10 s or more: tune, view, seconds, tempo, tempo_start, looped, heard, key_shift, who = student/teacher, value = minutes, content_id = slug). Nothing is sent without Analytics on the page.
- Public demo (18 Nov): `tools/make_demo.py` writes seven free tunes (`tunes/demo-*.json`: Ode to Joy, When the Saints, Jingle Bells, Twinkle, Auld Lang Syne, a major scale, a four-bar blues riff; public-domain melodies written out, concert pitch) and the `demo` shelf in `index.json` (`"free": true`: opens with no code, on /play too). `player/demo-loader.html` is pasted once into an HTML widget on the lessons page (`data-cta` = booking address); it loads `release/demo.html` (test copy `player/demo.html`), a poster that on tap opens the player in a frame with `window.AAM_DEMO` set: tune buttons, an "I play" instrument choice, a Book-a-trial button and an end-of-tune panel. Tune options added for it: `open_on`, `reps`. Events: `aam_demo_start`, `aam_demo_tune`, `aam_demo_cta`; demo plays report `who: visitor`.
- Band feel (18 Nov): tunes play "swing" (default) or "straight" (even eighths, bass on 1 and 3, held chords, rim click on 2 and 4). A tune file sets `"feel": "straight"`; the player's "Band: swing / straight" button in Practice settings switches it per tune (remembered on the device). Demo: Jingle Bells opens first; Jingle Bells, Ode to Joy, Twinkle and Auld Lang Syne are straight.
- Graded Repertoire (18 Nov): "Alex Attard Graded Repertoire", 8 levels on the ABRSM scale, strands Baroque & Classical / Romantic & Early Modern / Études / Scales & Technique; plan in the claude.ai project ("Graded classical series plan"). Player support: `"style": "solo"` (the written piano part, both hands, no band; Right hand / Left hand buttons; never swung; plays from the start), `"meter": [2|3|4, 4]` for solo/click/drone tunes (count-in, click and notation follow it), per-note loudness (4th value of a note event; 90 = plain). Pipeline: `tools/import_ly_midi.py` (a public-domain source score compiled to MIDI by LilyPond -> `repertoire/src/<piece>.json`, one ABC string per bar per hand) then `tools/make_repertoire.py repertoire/books/<book>.json [--code XXX-0000]` (tunes + shelf in index.json; the ABC is the single source for notation and playback; fingering `!1!`, dynamics `!mf!`, staccato `.` are added there by hand). Level 1 Baroque & Classical is live with 7 pieces (Mozart Minuet K. 2; from the Anna Magdalena Notebook: March in E-flat Anh. 127 (the only 4/4 piece; cut time shown as 4/4), Minuets BWV Anh. 114, 115, 116, 121 and the Musette Anh. 126), every note checked by script against Mutopia Project public-domain typesets (ornaments omitted). The Mutopia Handel Aylesford pieces import badly (two voices per hand) and were left out; Burgmüller Op. 100, Czerny Op. 821 and Schumann Op. 68 are in Mutopia for the Études and Romantic strands (check each licence). Five more pieces bring Level 1 to 12. They were first written from memory (18 Nov, at Alex's request), then checked the same day against text sources and corrected: Mozart's theme "Ah, vous dirai-je, Maman" K. 265 (2/4; both hands checked against J. J. Olson's public-domain two-guitar typeset in Mutopia, `ftp/MozartWA/KV265/guitar-duo-complete`, which documents its only changes; second-hand source, so compare once with a piano score before printing), and four themes in our own two-part settings whose MELODIES were checked by script against the LilyPond notation in Wikipedia articles (read through the built-in browser: open the article, then `fetch('/w/index.php?title=...&action=raw')` and pull the `<score>` blocks): Haydn "Surprise" opening theme (2/4), Beethoven Ode to Joy (4/4, in G), Handel "See, the Conquering Hero Comes" (4/4, hymn-tune form, A-B-A, moved to G), Haydn Emperor's Hymn (4/4, starts on a half-bar pick-up written as rests). The left hands of those four are ours, so Alex judges them by ear. The memory drafts had real errors (K. 265 bar 7 and the left hand of bars 9-16; the Emperor's Hymn barring and two rhythms; a rhythm in the Handel), which is why nothing goes out unchecked. Not yet: real Level 1 literature in 4/4 to replace the arranged themes (no machine-readable public-domain source found yet; Mutopia's Clementi Op. 42 is CC BY-SA and was not used), 6/8 and cut time, pick-up bars as true anacruses, repeats, ornaments, the printable PDF, woodwind editions.

## Tools (`tools/`)
- `gen_study.py`, `fit_study.py`, `add_qr.py`, `publish_tune.py`: lead-sheet study PDF -> tune + QR. `example_blues_alto_spec.json` is the standard 4-page blues build.
- `build_book.py`, `book_player.py`, `publish_exercise.py`: Welcome Booklet PDF, its exercises and QR codes.
- `tests/`: headless-Chrome (Playwright) checks run against a local copy of the player; `player-with-inline-catalog.html` is the standalone test/artifact version of the player.

## Open items
1. Minor ii-V-i fix: blues bar 8 must be m7b5 -> 7b9 (alto F#m7b5 B7b9), bar 11 VI7b9. The skills have the rule; `gen_study.py` cannot print 7b9 yet. F Blues alto, both Welcome Booklets and their blues tunes still show the old bar 8 and need a rebuild.
2. /play page title still "Student Enrollment" (Yoast SEO title on the Play page).
3. InMotion hosting returned intermittent 502s on /play on 16 Nov (about 9:26 pm and 9:43 pm Pacific).
4. Access is per PDF code and per device; no per-student tracking. Student logins would be a separate build.
5. Not built: tempo ladder (60->120 then double), tenor/clarinet/flute lead-sheet editions untested, audio never checked by Claude, "Hear it" uses a piano sound for every instrument.

- Metronome (18 Nov): a pendulum button on the play bar, left of the key button (`p-met`; blue when on, grey when off) opens the Metronome card (`mdlg`): on/off, sound (Click / Wood block / Beep, all synthesized, no files), Stronger first beat, With the music / Metronome only, Volume. State `met` (localStorage "aam-met": on, accent, sound, vol; "only" is not remembered). It clicks on every beat while the player runs, count-in bars included (when it is on it replaces the side-stick count-in). "Metronome only" closes `musicGate` (a gain between the band's compressor and the limiter) so the page is silent music plus click. The metronome has its own output (`metOut` -> limiter -> speakers). On phones up to 430 px the key button shows the key letter only, to make room. Levels were set by meter, not by ear: Alex to judge.
- Metronome is the only click (18 Nov): the old "Click" chip, its Mix slider and its scheduled side-stick are gone from pieces and exercises (styles solo, click, drone). The metronome is ON by default on those and OFF by default on band tunes; each kind remembers its own on/off ("aam-met": `on1` without a band, `on` with the band).
- Graded Repertoire print edition (18 Nov): `python3 tools/make_repertoire_pdf.py repertoire/books/<book>.json --code XXX-0000 --out book.pdf` builds the PDF from the same per-bar ABC the player uses (LilyPond engraves; ReportLab draws cover, "How this book works", contents, piece headings with a QR per piece, sources page with the series map; pypdf merges). The code is a command-line argument and the PDF is NOT kept in this public repository. Series design lives at the top of that file: slate + one colour per strand (`STRANDS`), level medallion on the cover, Poppins headings. Book file fields: `level`, `strand`, `series`, `practice` (one practice note per piece; first drafts by Claude, Alex to rewrite), and per piece `print_source` (the wording printed on the Sources page; `source` stays the internal check record). Level 1 order is now easiest to hardest. First draft sent to Alex for a look; no fingering yet.
- Welcome Booklet fixes (18 Nov): fingering chart has a new key `fs` (chromatic F♯, the small key between E and D on the side-key side, labelled on the key map). Chromatic F♯ = F fingering + `fs` (was wrongly 1-2-3 + D key). Side B♭ = A fingering (two keys) + side B♭ (was one key). Blues pages and both booklet blues tunes: bar 8 is now the minor ii-V (alto F♯m7♭5 B7♭9, concert Am7b5 D7b9) and bar 11 ends on the 7♭9. `gen_study.py` knows the quality `7b9` (prints 7♭9, same arpeggio 1-3-5-7, Phrygian dominant scale). `publish_tune.py` no longer crashes on shelves without a hash (the free demo). `tools/out/` (holds the booklet codes) is ignored by git; `out/qr_<edition>.json` can be rebuilt from `book_player.page_map()` without republishing. Both PDFs rebuilt and sent to Alex. Still to do: a "how to read the chart" picture using a real photo of a saxophone (waiting for Alex's photo); the standalone F Blues alto study and tune still show the old bar 8.
- Saxophone Beginner Booklet, first draft (18 Nov): `python3 tools/build_beginner.py` writes `tools/out/Sax_Beginner_Booklet.pdf` (23 pages, 66 numbered lines, one edition for alto and tenor). The book BEFORE the Welcome Booklet (which is really intermediate). Modelled on how Accent on Achievement teaches, not on its content: eight units, each adds one to three notes with the Welcome Booklet's fingering diagram, long tones on the new notes, short drills, then tunes using only the notes so far; colour-coded idea boxes (amber new note, blue new rhythm, green key signature, red new word), new notes printed in amber where they first appear, a tick box on every line, a "Create" staff and a Checkpoint per unit. Note order: B A G; C D; low F E D; F sharp; upper E F sharp G; B flat and upper F; low C; C sharp. The whole curriculum is the `UNITS` list at the top of the script. Tunes are public domain; most were checked against the notation in Wikipedia (the `src` field on each line says which); Mary Had a Little Lamb, Jingle Bells, Old MacDonald and Yankee Doodle were written from memory and need Alex's check. "Getting started" text (assembly, posture, embouchure) is a first draft for Alex to rewrite. Not yet: play-along tunes in the player with a QR per unit, photos, a skill.
- Beginner Booklet in the player (18 Nov): `python3 tools/build_beginner.py alto --code XXX-0000 --publish /path/to/aam-tunes` (and `tenor`) builds the edition's PDF with a QR and code on the cover and a QR at the top of every unit, and writes one player tune per numbered line (66 per edition, slugs `sax-beginner-<edition>-<line title>`, so renumbering lines never breaks a QR) plus the shelf `sax-beginner-<edition>` in index.json with one chapter per unit. The codes are in the project doc "Saxophone Beginner Booklet - status and codes", not here. Lines titled "Long tone..." use the drone style on that note; the rest use the click style (the metronome). New tune option `"hear": true` makes the player start with "Hear it" on. 3/4 lines carry `meter`; pick-up bars are padded with rests in the player. The release check now covers 199 tunes and takes several minutes: run it in the background.
- Beginner Booklet is in a student's hands (18 Nov). Rules for every update: keep the same codes; a renamed line keeps its old slug (`slug="old title"` on the line); `--publish` never deletes a tune that left the book (it stays unlocked by the same code, just not listed in a chapter). The printed QR codes point at the cover line and each unit's first line.
- Beginner Booklet, second edition (18 Nov, after a look at how the leading band methods are built: Accent on Achievement, Standard of Excellence, Essential Elements, Sound Innovations, Tradition of Excellence, Measures of Success, Rubank; publisher descriptions only, no content used). Now 34 pages and 78 numbered lines. Added, all in `tools/build_beginner.py` as an "upgrades" block after `UNITS`: two more box colors (purple NEW SYMBOL for signs such as repeat, dynamics, slur, crescendo, fermata, accent; teal SAX SKILL for technique); a CLAP rhythm line on a one-line staff in most units and a six-level "Rhythm gym" page; a WRITE pencil exercise per unit (name the notes, write the counts, draw the bar lines); PLAY BY EAR prompts; a duet with parts A and B in units 1-4, 6 and 7 (part B is ours and stays inside the notes learned so far) and a round in unit 5; a scale and arpeggio in units 5-8 (SCALE label); a short "about this tune" line under many tunes; tempo words, dynamics and breath marks printed in the music; a finale, Holst's "Jupiter" theme (melody checked against the notation of "Thaxted" in Wikipedia, one rhythm simplified) with our own piano accompaniment, a piano score page in concert pitch per edition; a glossary. In the player: duets show two treble staves with "Part A" / "Part B" on-off buttons (`notation.lh_clef`, `hand_labels`), the finale plays the piano under the written sax part ("Saxophone" / "Piano" buttons); CLAP and WRITE lines are print only. Every earlier tune kept its link.
- Beginner Booklet back pages (18 Nov): the fingering chart is now the Welcome Booklet's complete chart, low B flat to high F on three pages (`full_chart` calls `build_book.fingering_pages` and appends it with this book's footer), so a fix to the chart in `build_book.py` reaches both books. 36 pages.

## 2026-11-19 · Beginner Booklet, third edition (denser layout, 31 more tunes)
- `tools/build_beginner.py`: staff size 21 → 18; bars per line chosen automatically (8 simple, 6 busier, 4 busiest; `bpl=` overrides);
  two short drills share a row (`plan_pairs`, `HALF_MM`); one long-tone line per unit; shorter note cards (`NOTE_H`);
  units flow on from one another (`Page.head` + `Page.flush`, keep-with-next for title + note cards + first idea row), a one-line
  running head on pages that start mid-unit; fixed gap `GAP` under every line (at most 8 pt extra per gap); duet staves line up with
  the other lines (labels A / B hang in the margin); spare room at the very end becomes staff paper (`manuscript`).
- `rep=N` on a line: the first N bars are repeated (repeat bar line in print, played twice in the player).
- 33 pages, 105 numbered lines (was 36 pages, 78 lines). 27 new tunes checked against Wikipedia notation (source in each tune's
  `src`, print with `--sources`) and 4 new exercises of ours (Stepping Stones, Sunrise, Echo Song, Morning Bells).
- Same codes, same unit QR links: merged long-tone lines keep the old slug (`slug=`); the five dropped long-tone tunes stay playable.
- `--fill` prints how full each page is.

## 2026-11-19 (later) · Beginner Booklet: every unit starts at the top of a page
- Alex's rule: the unit title, note cards and idea boxes always open a page. `build_unit` flushes its own `Page` again.
- To make each unit end on a full page: three G-major tunes moved from unit 5 to units 6, 7, 8 as review (`_move`), unit 2 lost its
  WRITE line, unit 4 gained two F sharp drills and an Aura Lee duet, unit 1 a play-by-ear prompt; what room is left at the end of a
  unit becomes one to four lines of staff paper (`manuscript`). Check with `--fill` after any content change.
- 33 pages, 108 numbered lines.

## 2026-11-19 (evening) · Beginner Booklet, fourth edition (nine units)
- Unit 9 "The top of the staff: A, B and C" (two-octave C major scale and arpeggio, six tunes); the book now reaches upper C.
- Units 3 and 5 gained step-by-step drills; `order_unit` sorts the tunes inside each unit easiest first by `hardness()` (range, biggest
  leap, length, eighth notes, dotted quarters); drills and written work stay put, a duet stays behind its tune, `review=True` tunes go last.
- 37 pages, 128 numbered lines. Same codes and unit QR links. Check `--fill` after any content change: every unit must start at the top
  of a page and end on a full one (staff paper takes up to four lines of slack).

## 2026-11-19 (night) · The newest PDF of every booklet, inside the player
- `tools/publish_pdf.py` encrypts a booklet PDF (AES-256-GCM, random key) to `pdf/<id>.bin` and stores the key in the booklet's
  `file` entry in index.json, wrapped once with a key made from the booklet code and once with one made from the master code
  (`sha256("aam-pdf:" + CODE)`). Needs `AAM_CODE`. Publishing again overwrites the file: only the newest edition exists.
- Player: the contents dialog (tap the title) shows "Download the latest PDF" with the edition and size. The file key is remembered
  when a code is entered or a QR code scanned (`lib.keys`); a student who unlocked before this feature is asked to scan once.
- `build_beginner.py --publish` calls it when `AAM_CODE` is set; `EDITION` is printed in the footer. For the Welcome Booklets and
  Graded Repertoire run `publish_pdf.py` after a rebuild. Any tool that rewrites a booklet's entry in index.json drops `file`:
  run `publish_pdf.py` again afterwards.
- Not real protection for paid material: the repository is public and the codes are short. Single-tune lead sheets have no
  contents dialog yet, so no download button.

## 2026-11-19 (late) · Tuner and Learn mode (listening through the microphone)
- Player: `ear` opens the microphone with echo cancellation, noise suppression and auto gain off, and measures pitch with McLeod's
  method (normalized autocorrelation, parabolic refinement, clarity score), searched only inside the instrument's range. No audio
  leaves the device.
- **Tuner** chip (every tune): written note name for the instrument, flat/sharp needle, steady-note timer. Its first run is a
  two-step microphone check (room noise, then one long note) saved in localStorage `aam-ear` {floor, off (cents), at}.
- **Learn the notes** chip (only where a section has `learn`): no band; the current note is blue, a note turns green when its pitch
  is held about 0.16 s (within 50 cents after the player's own offset); a repeated note needs a tongued break or a 1.1 s hold; a
  steady wrong note names what was played; Skip, Start again, Hear it (after two misses), Stop. Showing or hiding the bar calls
  `perShown = 0; drawScore()` so the page is laid out again.
- `build_beginner.py` writes `learn` (sounding MIDI per written note, -1 for a tied continuation) into every beginner tune. Other
  books do not have it yet.
- Tested with generated saxophone-like audio fed to Chromium as a fake microphone (`/home/claude/v2/mkwav.py`, `eartest.js`):
  clean, noisy and 25 cents flat with legato repeats, and tenor low notes all finish. NOT yet tested with a real saxophone or on a
  real iPhone (Safari may not allow the speech processing to be switched off).

## 2026-11-19 · Contents list: search, chapter chips, denser rows
- The contents dialog (tap the title) is a fixed-height card: search box and chapter chips at the top, a scrolling list, Previous /
  Next and the PDF download pinned at the bottom. It opens scrolled to the current line.
- Search (books with 12+ lines): digits match the start of the line number; words match the name or chapter, accents ignored;
  Enter opens the first match. Chips (3+ chapters) jump to a chapter and hide while searching.
- Rows show the number in its own column and drop the repeated chapter text; books without numbers have no number column.

## 2026-11-19 · Phone: tempo wheel; Learn mode: pink line
- Phones (up to 620 px wide): the plus and minus are gone from the play bar; the tempo number is a button that opens a wheel
  (`tpdlg`): every speed 40 to 240, scroll-snap, the middle one is chosen, with Slow / Medium / Goal chips from the tune's presets.
  Wider screens keep the slider and the plus and minus; the number opens the wheel there too.
- Learn mode: a pink vertical line (`.lr-line`, an SVG rect inside the music) sits on the current note and slides to the next one;
  the note itself is pink, finished notes green.
- "Too loud for the microphone" now needs a quarter of a second of distorted AND unreadable sound, and it clears itself.

## 2026-11-19 · Play in the middle; the Learn line fitted to the stem
- Play bar is a three-column grid: `.p-left` (bar/chord readout on screens 1100 px and wider, tempo, metronome), Play in the exact
  middle, `.p-right` (key, repeats, settings).
- Learn line: an SVG group `.lr-line` (rect + circle) on top of the music. It lies on the note's stem and runs a little past the
  staff, with a dot where the stem meets the head; a whole note gets the line and dot through the middle of the head.

## 2026-11-19 · Learn mode marker: a soft blue cloud (the pink line is gone)
- Alex did not like the pink line with a dot. `.lr-line` is now one blurred, translucent blue rounded rectangle (SVG filter
  `#lr-soft`) drawn under the music, sized to the whole note (head and stem), sliding to the next note. The note itself is dark blue.

## 2026-11-19 · Tempo wheel flipped: faster speeds are at the top (240 down to 40).

## 2026-11-19 · The blue cloud follows playback on every tune; Learn mode on every single-line tune
- Playback: `playCloud(k, beat)` (called from `frame()`) puts the cloud on the note or rest sounding now. `beats()` reads each
  top-part note's bar and beat from the drawn music (abcjs classes `abcjs-mm<bar>` and `abcjs-d<length>`), so it needs nothing from
  the tune files. The playing bar keeps a faint blue wash (`.hl.is-now`).
- Learn mode no longer needs `learn` in the tune file: `learnSeq()` matches each written note to the `rh` event at the same beat
  (-1 where there is none: a tie). It is offered when the section has a one-note-at-a-time `rh` part, no `lh`, the instrument is not
  piano, and the page shows the instrument's own reading (`keyState.inst === NATIVE`). A key change adds `keyState.key`, so
  through-the-keys exercises work in every key. A `learn` list in the file still wins (the beginner duets use it for part A).
- **Rule for every generator from now on:** a single-line part must be published as `sections[].rh` events with matching
  `abc.rh` (one written note per sounding note, ties written as ties). Then the Tuner, Learn mode and the cloud work with no
  extra step. Check after publishing: the tune shows the "Learn the notes" button on its notation tabs.

## 2026-11-19 · Checks in the repository; booklet PDFs on a branch with no history
- `tools/check_features.js` (run by `tools/release.py` after `check_release.js`): tuner, Learn mode (clean, weak noisy microphone,
  tenor low notes, a shifted key, a sung concert pitch), the playback cloud, contents search and chips, every booklet's PDF download,
  the play bar at four sizes and the phone tempo wheel. Its microphone is generated sound fed to Chromium as a fake microphone.
  `--only tuner|learn|cloud|contents|pdf|bar` runs one group. `tools/wire.js` is the shared stand-in for the network.
  `tools/package.json` lists the two packages the checks load (`npm install` in tools/, or set `AAM_NODE_MODULES`).
- Booklet PDFs are no longer in `main`. `tools/publish_pdf.py` encrypts the PDF and rebuilds the branch **`pdf`** as ONE commit
  (no history) holding the newest two files per booklet, force-pushes it, and writes `file: {branch: "pdf", path: "<id>-<time>.bin", ...}`
  into index.json. The player swaps `main` for the branch name in its two mirrors. A copy is staged in `tools/out/pdf-branch/` for
  the checks; in a fresh clone the checks read `origin/pdf` instead (fetch it with
  `git fetch origin +refs/heads/pdf:refs/remotes/origin/pdf`).
- Never commit a PDF or a `.bin` to `main`. The old `pdf/` folder's files remain in main's history (about 40 MB); removing them
  would mean rewriting history, which was not done.

## 2026-11-20 · Fingering on screen; Analytics for the listening features; accounts tabled
- `tools/export_fingerings.py` copies `KEYS` and `FINGERINGS` from `tools/build_book.py` into the player (the block between
  `FINGERINGS:BEGIN` and `FINGERINGS:END`: `SAX_KEYS`, `SAX_BOX`, `SAX_FING` keyed by written MIDI 58 to 89). Run it whenever the
  printed chart changes. `fingerSvg(written)` draws it; saxophones only (`IS_SAX`).
- Learn mode: a Fingering button (remembered in localStorage `aam-fing`) shows the diagram for the note to play; it also appears by
  itself after two misses on a note. Tuner: the diagram of the note being played sits beside the note name.
- Analytics events (through `AAM_TRACK.event`): `aam_tuner` (first_time), `aam_learn_start` (notes), `aam_learn_done` and
  `aam_learn_stop` (notes, reached, seconds, skipped, wrong_notes, value = minutes), `aam_fingering` (how: button / after misses),
  `aam_pdf_download` (pdf, edition), `aam_search` (pdf, kind: number / name, found).
- Real accounts for the player are tabled (project doc "Player accounts - tabled"). Usage is followed in Analytics for now.

## 2026-11-20 · Version numbers, the guard, and the nightly builder
- **Read `BUILDER.md` first if you are a scheduled run.** It is the runbook for the nightly builder and the Sunday release review:
  how a job is picked, the six nights of a booklet, the checks, the list of things never done, and the Lessons list.
- Versions: `VERSION` holds the number of the live player (1.0 = everything up to 20 November 2026). `CHANGELOG.md` has an
  Unreleased block (Added / Fixed / Prevented) that `tools/release.py --version X.Y` moves under the new version. The player's
  version line now reads "v1.0 · <date> UTC (after <commit>)".
- `tools/guard.py` runs before every push and refuses it when: `release/` changed outside a release run, the guard or release tool
  changed, a PDF or .bin is on main, a booklet or tune disappeared or a code fingerprint changed, a real code is written anywhere
  (it fingerprints every word of the change), or the test player lost its root, version line or sounds credit. `--release` for a
  release run, `--tools` for a session with Alex that changes the gate on purpose.
- `tools/setup.sh` prepares a fresh machine (LilyPond, Python packages, node packages, the pdf branch) and prints READY.
- Alex follows the work in the Build Desk doc (Claude Docs): Needs Alex, Ideas inbox, Roadmap, Library (every booklet, its code and
  its link), Nightly log, Releases. Beta = `?player=test` on the play page. Nothing goes live until he says "ship".

## 2026-11-20 · v1.0.1: instrument icon and name under the title
- The subtitle line under the title now shows a drawn icon and the instrument's name from `TUNE.instrument` (alto, tenor, soprano,
  bari -> saxophone icon; clarinet; flute; piano). An instrument with no icon (trumpet, concert, the demo) keeps the old subtitle
  text. The icons are original inline SVGs in the "page text" block of the player. `subtitle` in tune files is still used in the
  My tunes list, so generators keep writing it.
- Check: the play bar group of `tools/check_features.js` also checks the icon and name at four sizes and on a piano tune.
- "Ship now" and "Beta" requests from Alex: see BUILDER.md.
