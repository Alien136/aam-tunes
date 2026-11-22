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

## 2026-11-20 · Band styles (beta, not released)
- `BAND` in the player is the table of styles: `sw` (how late an off-beat eighth is, in ticks), `drums` (one grid per bar, cycled:
  `[sound, beat, loudness, classic-kit dB, chance]`), `bass` (a rule: `walk`, `two`, `bossa`), `comp` and `half` (comping rhythms for
  a chord that lasts a bar / half a bar), `kit` (extra drum sounds). `bandParts(S)` writes the bass and chords; one generic block in
  `scheduleMusic()` plays any table style. Medium Swing (`swing`) and Straight Ballad (`ballad`, the old "straight" feel) keep their
  own hand-tuned code and are only gated by name. Every style is scheduled up front and gated on the variable `band`, so the
  style can change while the band plays.
- A tune can name its style with `"band": "<id>"`; the older `"feel": "straight"` still means the ballad. The student's choice is
  kept in localStorage `aam-band` per tune (`aam-feel` is read once for old choices).
- The swing of the written "Hear it" line follows the style playing (`SW`).
- Picker: `st-pill` (`data-r="style-btn"`) beside the instrument name, the `feel` chip in Practice settings ("Style: ..."), dialog
  `stdlg`. Only for band tunes (`style` absent or "swing"). Analytics event `aam_style` (style).
- Sounds: the closed hi-hat `hhc` (already in sounds/v2) is now loaded for band tunes. Styles that need an electric bass, a pop
  kit, percussion or an electric piano need a new sound set (`sounds/v3`). The band is still 4/4 only.
- Check group `style` in `tools/check_features.js`: every style sounds, its name fits on a phone, the choice is remembered,
  exercises have no picker.
- NOT judged by ear: nobody has listened to Two-Feel, Up-Tempo or Bossa yet. Alex listens in beta before a release.

## 2026-11-20 · v1.0.2: one cloud per hand on piano pages, no wash on the bar
- Playback: the bar's own blue wash (`.hl.is-now`) is drawn only when `.score` has the class `bar-wash`, which `playCloud` sets
  when the bar has no note or rest in either staff. Otherwise the note's cloud is the only marker.
- Piano pages (`TUNE.instrument` contains "piano"): `beats()` also reads the lower staff (`.abcjs-v1`) into `bars2`, and
  `playCloud` keeps a second cloud (`.lr-line.lr-line2`, element `playEl2`) on the left hand's note. A duet's second part gets none.
- Released as a "ship now" fix while the test copy held the unreleased band styles: `tools/release.py --from <file> --version
  1.0.2 --notes <file>` checks and releases a copy of the last released player plus the fix (kept in git-ignored `tools/out/hotfix/`),
  and leaves the Unreleased block of the change log alone. The same fix is in the test copy.
- `tools/check_features.js` skips the `style` group for a copy of the player that has no styles.

## 2026-11-20 · v1.1: band styles released; "Apply changes"; page-turn cloud fix
- Alex listened to the five styles in beta and said ship. v1.1 is the test copy as it stood (styles + everything in v1.0.2).
- `stage(name, fn, btn)`: while `state.playing`, a change is kept in `staged` and its button gets the class `pend` (dashed
  outline); the pill `[data-r="apply"]` above Play runs them (`applyStaged`). `stop()` also applies them. Staged today: number of
  repeats (`reps`), key (`key`), instrument reading (`inst`). Instant by design: tempo, style, mix, metronome, the band's on/off
  chips, Hear it. Not staged yet (Alex to decide): tapping a bar or a loop, through-the-keys, the speed-up ramp, count-in.
- Page-turn copy (`showOver`): the cloned SVG is stripped of `.lr-line`, of `lr-now`/`lr-ok`/`lr-miss`, and of the `<defs>` holding
  `#lr-soft`. Two filters with one id made iPhone Safari draw the real cloud unblurred or not at all; the stale copy showed blue
  notes with no cloud. Not reproducible in Chromium, so the check asserts the copy is clean rather than how it looks.
- Check group `apply` in `tools/check_features.js`.

## 2026-11-20 · Beta: four more styles; the metronome's band switch
- New `BAND` entries: `slow` (Slow Swing), `samba`, `afro` (Afro-Cuban: cascara on the ride bell, 2-3 clave on the rim), `shuffle`
  (Shuffle Blues). New bass rules in `bandParts`: `tumbao` (the "and" of 2 and beat 4, the 4 anticipating the next chord) and
  `boogie` (root, third, fifth, sixth). The ride bell `bell` is now loaded for band tunes. New group "Blues".
- These four were written from general knowledge of the styles and NOT checked against recordings or method books, and nobody has
  heard them. They are in beta for Alex's ear; BUILDER.md's rule (name two sources) applies to every style after these.
- Metronome dialog: `m-only` ("With the band / Metronome only") and its heading are hidden when the page has no band
  (`STYLE !== "swing"`).

## 2026-11-20 · Beta: Learn mode on piano pages, one hand at a time
- `learnSeq(hand)`: on a piano page (`IS_PIANO`) it builds the sequence for `rh` (staff `.abcjs-v0`, `beatMap.notes`) or `lh`
  (`.abcjs-v1`, `beatMap.notes2`). A chord becomes its lowest note in the sequence, with all its notes in `seq.alts[index]`;
  `learnHear` accepts whichever is nearest to the pitch heard (the listener hears one pitch at a time). A hand is offered when every
  sounding note found a written note and at most a quarter of its onsets are chords. `learn.hand` holds the hand; `learnEls()`
  follows it. Dialog `hdlg` asks which hand when both are possible (`learnStart(hand)`).
- Graded Repertoire Level 1: both hands of every piece qualify, except pieces written in two voices per hand if any fail the
  note match. Lead-sheet piano pages: right hand only (the left hand is all guide-tone chords).
- Checked with generated, sustained tones (check group `piano`). NOT checked with a real piano, whose notes die away: the
  repeated-note rule and the level threshold may need tuning once Alex tries it.

## 2026-11-20 · Starter Pack edition; install on phone (beta)
- `tools/build_beginner.py <alto|tenor> --starter --code XXX-0000 --publish <repo>` builds the free Starter Pack: the same book,
  "FREE STARTER PACK" on the cover, a last page (`invite_page`) with a QR code to the booking form (`BOOKING`), file
  `Sax_Starter_Pack_<Ed>.pdf`. In the player it is a second shelf (`sax-starter-<ed>`) over the Beginner Booklet's own tunes: no
  tune file is written twice, so publish the Beginner Booklet first, and after any change to the booklet rebuild BOTH (same codes).
  The Starter Pack codes are in the Build Desk Library, not here.
- The four Starter Pack emails are drafts in the Claude Doc "Starter Pack emails". MailerLite (free plan) is the email tool; the
  account exists; the domain is not connected yet (needs Alex at a computer).
- Install on phone, in the library part of the player (after `urlFor`): removes the website's own apple-touch-icon and manifest
  links and adds ours from `player/app/` (`icon-180/192/512.png`, `manifest.json`, `manifest-beta.json` for the test copy), plus
  `apple-mobile-web-app-capable`, the home-screen name "Attard Music" and a theme colour. `install-btn` in Practice settings opens
  `idlg` with steps for iPhone, or Android's own install box (`beforeinstallprompt`). Before showing the steps it rewrites the
  address to `?t=<tune>&c=<code>` so the icon opens that tune unlocked (a home-screen app on iPhone keeps its own storage).
  Hidden when already running from the home screen and in the public demo. Analytics event `aam_install`.
- Offline: `player/app/sw.js` is written but NOT in use. It must be uploaded to the website as `/aam-sw.js` (the test copy
  registers it with scope `/play/`; a 404 does nothing). It answers only the play page, this repository's files and the Tone,
  abcjs and font files. Untested on real phones: try it in beta first, then let the released player register it.
- Not checkable here: how iPhone Safari treats the icon and full-screen flag when they are added by script. Alex tests on his phone.
- `pdfOf(slug)` now prefers a booklet the student has unlocked when two booklets share a tune. Without it a Starter Pack reader is
  shown the Beginner Booklet's shelf and cannot download the PDF: the released player (v1.1) does NOT have this yet, so release the
  test copy before the Starter Pack is given to anyone. The PDF check opens a shared shelf as a student who unlocked that booklet.

## 2026-11-20 · v1.2
- Alex said ship. Released: the Starter Pack shelf fix (`pdfOf`), Learn mode on piano pages, install on phone (icon, full
  screen, steps), the metronome's band switch. The four styles nobody has heard (`slow`, `samba`, `afro`, `shuffle`) carry
  `beta: true` in `BAND` and are listed by the picker only in the test copy; remove the flag per style when Alex approves it.
- The free lesson is 30 minutes (Alex, 20 Nov), as printed on the Starter Pack's last page and in email 4.

## 2026-11-20 · Beta: the play bar from the home screen
- Alex added the test player to his iPhone's home screen: icon and full screen work. The play bar was cut off at the bottom.
- The install block now appends `viewport-fit=cover` to the page's viewport meta (so `env(safe-area-inset-*)` is real) and, when
  running from the home screen, adds the class `is-app` to `#aam-play`: `.is-app .pbar` and `.is-app.is-open` keep at least 26 px
  under the Play button whatever the phone reports. Not yet confirmed on his phone.

## 2026-11-20 · Beta: an instrument picker on concert-pitch tunes
- A tune with no `instrument` (the seven demo tunes) and keys not "off" gets a pill under the title (`inst-btn`) and the dialog
  `pdlg` ("I play": piano, flute, clarinet, tenor, alto). Choosing sets `keyState.inst` (0, 2 or 9, the same reading the Key dialog
  sets), saves it per tune in `aam-keys`, and remembers the instrument in localStorage `aam-play-as` so the next concert tune opens
  written for it. `showInst()` keeps the pill in step and is called from `keyLabels`. While the band plays the change waits for
  "Apply changes" like any other reading change. Analytics event `aam_instrument`.
- Listening on these tunes: `EAR_SHIFT` follows `keyState.inst` (names as the reader reads them); `ANY_OCT()` makes Learn accept
  the right pitch in any octave, because a tenor or alto sounds the line an octave away from the tune file. The listening range
  stays wide (`EAR_FIXED` is 0). No fingering diagrams on these tunes (`IS_SAX` goes by the tune's own instrument).
- Check group `demo`.

## 2026-11-21 · Beta: the instrument button in the public demo
- The demo card (`demoChrome`) no longer builds a `<select>`. Its bar has an empty `.demo-inst` slot and the pill built with the
  page text (`inst-btn`) is moved into it by whichever of the two runs second; `showInst` reaches the pill through the variable
  `pill`, never through the subtitle element. The older choice in localStorage `aam-demo-inst` is read once into `aam-play-as`.
- Trumpet added to the list and to the header icons (`ICON.trumpet`).
- Analytics: `aam_instrument` carries `instrument` (piano, flute, clarinet, trumpet, tenor, alto) and `where` ("demo" or
  "player"). To see the split in reports, `instrument` and `where` must be registered as custom dimensions.
- See the demo's test copy at the lessons page address with `?player=test` added.

## 2026-11-20 (US) · Google Analytics: custom dimensions and a weekly emailed report
- Done in Alex's Analytics property (alexattardmusic.com) through the browser pane, with him signed in: nine event-scoped custom
  dimensions (Who=who, Tune=tune_title, Instrument=instrument, Where=where, Style=style, View=view, How=how, Booklet=pdf,
  Player version=player_version). They apply to events from now on.
- A scheduled email of the Events report (last 28 days, CSV, weekly, 12 months) goes to Alex's own Gmail as "AAM player events
  (weekly for Claude)". The Sunday review reads it (BUILDER.md, step 2a). First one is due Saturday 21 November.
- First reading, 23 Oct to 19 Nov 2026: 291 users and 723 page views on the site; aam_open 21 and aam_practice 10, each from 4
  users (not yet split by student or teacher); demo started 3 times, demo booking button 1; trial_booked 5; form_submit 8.

## 2026-11-21 · Saturday style pass: headings stop short of the tick box
- Rendered from the generators and looked at page by page: Beginner Booklet alto (37 pages), Starter Pack alto (38), Welcome
  Booklet alto (27), Graded Repertoire Level 1 (20); tenor editions compared with alto page by page.
- Fixed at the source: `cell()` in `tools/build_beginner.py` measured a heading only to decide where the subtitle goes, never
  against the tick box. In a half-width cell "C major arpeggio, two octaves" + SCALE ran 7 pt into the box (line 116, page 28).
  `cell()` now works out `ts`, the title size that leaves 4 pt before the box (10.6 pt normally, never under 9 pt), and stops the
  build with a message if 9 pt is still too wide. Only page 28 changed, in all four editions (pixel comparison of every page).
- NOT republished: the four PDFs on the `pdf` branch are the released ones and still show the old page 28. Republishing a
  released booklet is waiting for Alex's answer in the Build Desk (the runbook says republish; the nightly task says nothing may
  reach students). When he says yes: rebuild both Beginner Booklets, then both Starter Packs, with `--publish` and the same codes.
- Seen and left for later Saturdays (one fix a night), most visible first:
  1. Welcome Booklet, Blues pages 23 and 24 (`gen_study.py`): body lines set too tight, so wrapped lines touch the next line
     ("dominant chord.", "climbs to the root."); page 24 has no page header.
  2. Footers differ: Welcome = "Alex Attard Music" + page (the brand rule); Beginner adds the book title and "Edition 4 ·
     November 2026"; Graded Repertoire = "Alex Attard Graded Repertoire · Level 1 · Baroque & Classical" in muted grey with a
     slate page number. Needs one shared footer; the edition line may be wanted, so ask before removing it.
  3. Beginner Booklet pages 30 to 33 (finale, piano score, four scales, rhythm gym) end with a third of the page empty.
  4. Welcome Booklet music pages: the title sits closer to its kicker, and the amber rule lower, than on the text pages.
  5. Beginner cover: the signature "Alex" sits on or just under the bottom edge of the welcome box.
  6. Glossary: "Whole, half and quarter notes" wraps its "Unit 1" tag onto a line of its own.

## 2026-11-21 · Flute Beginner Booklet, first edition (built in one session at Alex's request)
- Alex asked for it "asap", so the six-night plan was done in one sitting. Nothing in it has been played or checked by a flute
  teacher yet: see "Needs Alex" below.
- **How it is built.** No fork. `python3 tools/build_beginner.py flute [--starter] --code XXX-0000 --publish <repo>`. The flute
  reads the same written notes as the saxophone in the same range, so the curriculum is the saxophone book's, line for line (nine
  units, 128 numbered lines, same sources). What differs is data in `tools/beginner_flute.py`: the key diagram (`KEYS`,
  `draw_keys`, `key_map`), the fingerings low C to upper C sharp (`FINGERINGS`, B flat with the thumb as an extra card), the
  two-page chart (`fingering_pages`), the cover drawing (`draw_flute`), the Getting started page (`START`, `CARE`) and the words
  about fingers and air (`NOTE_TIPS`, `BOXES`, `SUBS`, `CHECKS`). `patch(UNITS)` swaps them in and refuses to build if a
  saxophone word is left ("octave key", "reed", "strap", "mouthpiece", "jaw", "bite"...).
- **Note order** is the saxophone book's: B A G; C and D; F E low D; F sharp; upper E F sharp G; B flat and upper F; low C;
  C sharp; upper A B C. Checked against two flute sources that start B, A, G and then C: The Instrumentalist, "First Lessons
  for the Beginning Flutist, part 2" (Oct 2015), and the 8notes Beginner Flute Method. B flat is taught as B plus the right index
  finger; the thumb lever is on the chart only.
- **The saxophone book did not change**: built before and after, every page compared pixel for pixel, text identical.
- **In the player:** shelves `flute-beginner` (Flute Beginner Booklet) and `flute-starter` (Free Flute Starter Pack, a second
  shelf over the same tunes, with the invitation page). 128 tunes `flute-beginner-<line>`, `instrument: "flute"`, concert pitch.
  Both PDFs are on the `pdf` branch. Codes: only in `tools/out/beginner_codes.json` (git-ignored), the Build Desk Library and the
  project doc "Flute Beginner Booklet - status and codes".
- **Player (beta, not released):** the tuner and Learn mode draw the flute fingering (`FLUTE_KEYS`, `FLUTE_BOX`, `FLUTE_FING`,
  written by `tools/export_fingerings.py`; `FG` picks the chart; `HAS_FING`). In the live player a flute line plays, shows the
  cloud and Learn mode names the notes, but no fingering diagram appears until the next release.
- Checks: every flute line at four screen sizes in the test copy and in the live copy (512 views each); new `flute` group in
  `tools/check_features.js`; the PDF download with each code.
- **Needs Alex:** (1) check every fingering on pages 35 and 36 and on the note cards; (2) read the Getting started page and the
  FLUTE SKILL boxes as a flute teacher; (3) is low C in Unit 7 too early for a flute beginner (it needs the footjoint keys)?
  (4) play it through. Same open items as the saxophone book: duet part B and the finale's piano part are unplayed.
- Not done: a flute Welcome Booklet (the last page says "your next book"); a MailerLite form and emails for the flute Starter Pack.

## 2026-11-21 · Flute Welcome Booklet, first edition (same session, at Alex's request)
- Alex: "similar to the sax book but altered slightly to fit an intermediate flute student... start on low C and go up to high G."
- **How it is built.** No fork: `python3 tools/build_book.py flute` -> `tools/out/Flute_Welcome_Booklet.pdf` (27 pages, the same
  page numbers as the saxophone book). `FLUTE` and `LOW` (60 = low C; saxophone 58) at the top of `build_book.py`; the flute's
  long-tone and chromatic lists are `LT_DOWN`, `LT_UP`, `CHR_UP`, `CHR_DOWN`. Chromatic order starts on C. Long tones: middle B
  down to low C, then up to high G (five cells to a line). Chromatic scale: low C to high G and back. Scales, thirds, fours and
  arpeggios: one octave and a bit from each root between low C and B (C has no note below it, so it ends on the root, as B flat
  does on saxophone). Arpeggio pages are one staff size smaller than the saxophone's to keep twelve keys on a page. Licks are
  the same four; the blues is in F (concert pitch).
- **Chart:** `welcome_chart()` in `tools/beginner_flute.py`: low C to high G on three pages, B flat with both fingerings; the
  third octave is `HIGH` (high D to high G). `export_fingerings.py` now sends all 32 notes to the player.
- **In the player:** shelf `flute-welcome`, 21 exercises `flute-welcome-<name>` published by `tools/book_player.py flute <code>
  <repo>`. Exercises that go through the keys are stored in written F with `start_key` -5 (the player moves a pattern -5 to +6
  half steps, so F covers C to B); both key orders begin on C. PDF on the `pdf` branch. Code in `tools/out/beginner_codes.json`,
  the Build Desk Library and the project doc.
- **The saxophone Welcome Booklet did not change** (alto built before and after, every page compared pixel for pixel), and no
  saxophone tune file was rewritten.
- Known: in the player, the C major and C minor loops show the note below the root (low B), which only a flute with a B foot
  has; the printed page ends on the root. The saxophone booklet has the same quirk on B flat (low A).
- Scales are one octave and a bit, as in the saxophone book. Two-octave scales to high G are not in this edition.
- **Needs Alex:** check the third-octave fingerings (page 27) and say whether an intermediate flute student should have
  two-octave scales in this book.

## 2026-11-21 · Three alto studies for a student preparing ABRSM Grade 3 Jazz
- Cold Duck Time (`cold-duck-time-alto`), Mercy, Mercy, Mercy (`mercy-mercy-mercy-alto`) and Autumn Leaves
  (`autumn-leaves-alto`): chord and scale studies with licks, each its own PDF, code and tune. Codes in
  `tools/out/beginner_codes.json` and the project doc "ABRSM Grade 3 Jazz studies - codes".
- **Built from the standard changes, not from the ABRSM book** (Alex did not have the pages to hand): Cold Duck Time in concert
  F (12 bars: F7 Bb7 x4, Dbmaj7, Ebmaj7, F7, F7), Mercy in concert B flat (20 bars; the plain B flat and E flat chords in bars 9
  and 11 are written as 6 chords, F7sus as F7), Autumn Leaves in concert G minor. The ABRSM arrangements may be in other keys
  with shorter solo sections: rebuild from the book's pages when Alex sends them. "Going Home" (arr. Pete Churchill) is not
  built: the chart is needed.
- `gen_study.py`: new spec key `licks_title` (default "ii-V-I Licks") for tunes with no ii-V-I; these two use "Soul Licks" with
  `voice_leading: false`.
- The two soul tunes carry `"band": "bossa"` in their tune files so the band plays even eighth notes. The player has no soul or
  funk style yet: a good next band style.
- Recordings: only one recording of Cold Duck Time itself could be verified (Swiss Movement); its other four are alto players
  in the same style, and the page says so.

## 2026-11-21 · Going Home (Mark Lockheart, arr. Pete Churchill): alto study of the 8-bar solo section, in 3/4
- Built from a photo of the ABRSM Grade 3 alto part. `tools/study_going_home.py [--code XXX-0000 --publish <repo>]`: a
  hand-written study, because `gen_study.py` is 4/4 only. Written key B flat (concert D flat), chord symbols as the part
  prints them. Arpeggios (two lines), scale choices, scale chorus, three licks, a two-time lick chorus, a blank chorus.
- Player: shelf `going-home-alto`, four 3/4 exercises (`-arpeggios`, `-arpeggios-7`, `-scales`, `-licks`), click only: the
  band cannot play 3/4 yet and the student has the book's backing track.
- The earlier note stands: the other three Grade 3 studies were built from standard changes and still need checking against
  the book.

## 2026-11-21 · Beta: the microphone on iPad (a student's check "passed" but Learn mode heard nothing)
- Report from Alex: a student on an iPad tapped through the microphone check, then the player could not hear her saxophone.
- Not reproduced on a device (no iPad here). Found by reading the code and confirmed with two new checks that FAIL on v1.2:
  1. `ear.start()` made the AudioContext inside the getUserMedia promise, after the tap had ended. iPad and iPhone Safari can
     leave such a context suspended; `resume()` outside a tap does not wake it. A suspended context reads as exact zeros.
  2. Step 1 of the check ("stay quiet") accepted exact zeros as a quiet room, so a dead microphone passed step 1.
  3. The first-time check closed the microphone and Learn mode opened a second one (second getUserMedia, second context).
  4. The analyser was not connected to the destination; Safari may not process a chain that does not reach the speakers.
- Fix (test copy): the context is created and resumed synchronously in `start()`; analyser -> gain 0 -> destination;
  `off()` waits 500 ms before stopping so the check hands the live microphone to Learn mode; `tick()` marks `r.dead` after
  1.5 s of a non-running context or exact zeros, arms a one-time `pointerdown` that calls `resume()`, and sends
  `aam_mic_silent` (how = the context state). The tuner and Learn mode show `MIC_SILENT`. Older Safari without
  `getFloatTimeDomainData` falls back to the byte version.
- New check group `mic` in `tools/check_features.js`. Still unverified on a real iPad: ask the student to try the beta link.

## 2026-11-21 · v1.3
- Alex said "ship". Released after the full check (489 tunes x 4 sizes, 117 feature checks): the iPad microphone fix, the
  booklet PDF button first in the list and the `&pdf=1` link, flute fingerings in the tuner and Learn mode, the instrument
  picker on concert-pitch tunes and in the demo, the play bar from the home screen. The four `beta: true` band styles stay in
  the test copy only. The iPad fix is still unconfirmed on a real device: it is on the Needs Alex list.
- Decided by Alex the same day: the Flute Welcome Booklet gets two-octave scales (welcome books are intermediate books). The
  ABRSM pages for the other three studies are tabled (he does not have the books). MailerLite waits for a computer.

## 2026-11-21 · Flute Welcome Booklet, edition 2: two-octave scales
- Alex: "the welcome book for flute should get two octave scales: welcome books are intermediate books".
- Two new pages after the harmonic minor scales (pages 11 and 12; the book is now 29 pages): Two-Octave Major Scales and
  Two-Octave Harmonic Minor Scales, chromatic order. `pat_two_oct` in `build_book.py`: two octaves up and back where the key
  fits under high G (C to G); from A flat to B the scale climbs to the highest note of the key below high G and returns to
  the root. `HIGH` = 91 on flute. Only the flute edition prints them (`if FLUTE` in `main`).
- Player: 24 new exercises, one per key (`flute-welcome-2oct-major-c` ... `-minor-b`), because each key has its own length.
  `page_map()` in `book_player.py` has its own flute numbering; the other 20 exercises kept their slugs.
- The saxophone Welcome Booklet is unchanged (alto compared page by page).

## 2026-11-21 · Beta: Soul Jazz style; the band in 3/4 (Jazz Waltz, Ballad in 3)
- `BAND` has three new entries, all `beta: true`: `soul` (bass rule "soul": root, root on the and of 2, fifth, seventh below, a step into the
  next chord), `waltz` and `waltzb` (`m: 3`, bass rule "waltz"). Models, from knowledge and NOT yet judged by ear: Soul Jazz = Eddie Harris and
  Les McCann "Cold Duck Time", Cannonball Adderley "Mercy, Mercy, Mercy"; Jazz Waltz = Miles Davis "Someday My Prince Will Come", Bill Evans
  "Waltz for Debby". Alex listens in beta, then remove `beta` per style.
- `BPB` now follows `meter` for band tunes too (3 or 4; 2/4 stays exercises only). `m` on a style = its beats per bar; `bandFits(id)` keeps a
  style to tunes in its meter (picker, default, scheduler); `bandLive(id)` adds "not beta, or the test copy". The two hand-tuned styles
  (Medium Swing, Straight Ballad) are 4/4 only.
- Three tune keys, all ignored by older players: `with_band: true` (a tune whose `style` is a click plays with the band once its `band` style
  is live: how a 3/4 tune stays safe in v1.3), `band_new` (use this style in place of `band` once it is live), and on a chord `bass`
  (pitch class of a slash chord's bass note) and `voice` (degree indexes for the piano, e.g. `[3,4,6,1]` for a sus chord).
- Going Home (4 exercises) republished with its real concert chords, `with_band` and `band: "waltzb"`; Cold Duck Time and Mercy, Mercy, Mercy
  have `band_new: "soul"`. In v1.3 all three behave exactly as before (checked with `check_release.js --file release/player.html`).
- Checks (`--only style`): 4/4 offers no waltz; Going Home opens with Ballad in 3, lists only styles in three, each sounds; Cold Duck Time
  opens with Soul Jazz in the test copy and Bossa Nova in a released copy while the style is beta. Soul Jazz sits after Straight Ballad in the
  picker on purpose: the ballad check counts sounds in a fixed window and is sensitive to where in the tune it lands.
- To release a style: delete its `beta: true`, then ship. Not done: `gen_study.py` still writes 4/4 only (Going Home is hand-written).

## 2026-11-21 · Theory arm: note flash cards (beta)
- Plan: project doc "Theory arm - game plan (2026-11-21)". One question engine (generators tagged by level and topic) feeds three things:
  flash cards (built), random practice exams and fixed workbooks (not started). Levels: Prep (age 7), 1 (8), 2 (9) ... 6; adult-looking early.
- `theory/cards.html` is the cards' TEST COPY: its own small app (`#aam-cards`), sharing only abcjs and the fingering data
  (`tools/export_fingerings.py` now writes its FINGERINGS block too). No code screen, no network use beyond abcjs and fonts.
- How it opens: the play page with `?app=cards`. The player's first lines (">>> OTHER APPS ON THIS PAGE") fetch the cards, put them in place
  of `#aam-play`, then `throw` to stop the player's own script (the message says it is not a fault). The test copy loads `theory/cards.html`;
  a released player loads `release/cards.html`, which does NOT exist yet, so students see "could not load" if they guess the address.
  To release the cards: have `tools/release.py` copy `theory/cards.html` to `release/cards.html` (stamp CARDS_VERSION), after Alex says ship.
  A page of its own (/theory, its own loader) is a computer job for later.
- Cards: `KIND` holds the four kinds (name, key, fing, staff); `same` says when two notes are the same answer for that kind, so wrong answers
  are always different pictures. `LEVELS` holds ranges and the number of answers. Memory: localStorage `aam-cards` (settings, best, miss).
- Email sign-up before use (Alex's idea, 21 Nov): not built; recommendation given was one free deck, email for the rest. Needs MailerLite.
- Checks: `--only cards` (8 instrument/card/level mixes draw and fit a phone; a 20-card round scores right; memory is kept).
- Next: key-signature, interval and chord-symbol generators; the syllabus table is in the project doc for Alex to mark up.
- 21 Nov, later: Alex wants theory on its own address, not the play page. `theory/loader.html` is the block to paste once into an Elementor
  HTML widget on a new /theory page: it loads `release/cards.html` (404 = "Theory practice is coming soon") or, with `?beta`, the test copy
  `theory/cards.html`. Steps are in the Computer session guide. Once /theory exists, remove the `?app=cards` hook from the player.

## 2026-11-22 · Beta: Learn mode levels, Forgiving and Strict (nightly builder)
- `LVL` in the player: `easy` (shown as "Forgiving": within 50 cents, 4 frames = 0.16 s, exactly the old behavior) and `strict` (within 30
  cents after the player's own offset, 8 frames = 0.32 s). `learnLvl()` decides: a piano page is always `easy`; else the student's own
  choice (localStorage `aam-lvl`); else `lvl` in the saved microphone check (`aam-ear`); else `easy`.
- The microphone check (tuner, step 2) now also saves `spread` (90th minus 10th percentile of the long note's cents) and `lvl`:
  `strict` when the spread is at most `LVL_STEADY` (20 cents) and the room was not noisy. A check saved before today has no `lvl`, so
  nobody's Learn mode changes until they tap "Check my microphone again" or the Level button.
- Strict, right note but 31 to 50 cents off: not counted, never a wrong note; after 18 frames (0.7 s) the bar says "Right note, but
  flat: bring it up a little." (or sharp). There is no automatic let-through: Skip note and the Level button are the ways on.
- Button `learn-lvl` in the Learn bar ("Level: Forgiving" / "Level: Strict"), hidden on piano pages and when the line is finished.
  Analytics: `aam_learn_level` (how = easy or strict); `level` and `out_of_tune` ride on the learn stop and done events.
- Check group `level` in `tools/check_features.js` (16 checks; skipped for a copy of the player without the button, like `style`).
- NOT judged with a real instrument: 20 cents (who gets Strict) and 30 cents (what Strict accepts) are first guesses. A real
  saxophone's long note may waver more than 20 cents and never be given Strict; Alex to try, then tune the two numbers.
- 22 Nov: Alex made the /theory page (loader pasted). The `?app=cards` shortcut is gone from the player. Cards setup redone as one row of
  equal buttons per choice so it fits a phone screen (check: Start is on screen without scrolling). Alex's decisions the same day: the
  Level 1 blues is the real 12-bar blues with a V-IV turnaround and no ii-V; theory material is piano-focused first; US terms only
  (quarter, half, whole note), no British terms. See project doc "Theory decisions (2026-11-22)".

## 2026-11-22 · Theory workbooks: the Prep book, first full draft
- `python3 tools/build_theory.py` writes `tools/out/Theory_Prep.pdf` (18 pages: cover, 8 units, review). Units 1-2 are in build_theory.py,
  Units 3-8 in theory_prep_units.py. Everything is drawn with ReportLab; clefs and the quarter rest are FreeSerif's music glyphs.
- Alex approved the look on the 4-page sample: Learn box then exercises, the website's blue (#428AD2) as the one accent, large type for Prep.
  `LEVEL_TYPE` in build_theory.py holds the type and staff size per level: Level 1 steps up quickly to a mature page.
- Piano first, US terms only. Finger numbers are NOT in Prep (asked twice, no answer: left out). Not yet read by Alex page by page.
- Not done: answer key, QR codes to the flash-card decks, publishing (it is a file only), Level 1.
- Same day, edition 2 after Alex read the draft ("text size is extreme; size it like the Beginner Booklets; fit more on a page; a better
  cover with a piano"): every page is drawn on a larger sheet and scaled by K = 0.76 (type 11 pt, staff spaces 12 pt). `Page` now FLOWS:
  blocks call `need(h)`, a section heading waits for its first block, `finish(filler, checks)` adds seeded "More practice" rows until the
  unit's last page is full and puts the checklist at its foot. New cover (keyboard with E G B lit, the same three notes on a staff) and a
  contents / how-to-use page. 19 pages. `LEVEL_K` holds the scale for later levels.
- Edition 2, second pass (Alex: "going in the right direction, fit maybe 20% more on each page"): K = 0.71 (type about 10.3 pt), tighter gaps
  between blocks, the checklist may dip into the foot margin sooner than go alone to a new page. 18 pages. He likes the new cover and design.

## 2026-11-22 · Beta: download card and first-visit tour (after Alex's own Starter Pack test)
- Alex signed up on /starter-pack with his own address: the confirmation email, Email 1 and both links work. Still to fix in MailerLite (in
  the Computer session guide): "Musoc" in the confirmation email's sender name, "newsletter" wording, raw links in Email 1, and Email 1 says
  the booklet "comes with a band" although all 128 Starter Pack lines are a click (119) or a drone (9): no line has the band.
- `&pdf=1`: `open(true)` adds `pdf-only` to `.toc-card` (no search, chips, list or foot). `.toc-next` ("Now play along") and the Done button
  both run `leave()`, which starts the tour. `.toc-all` turns the card back into the ordinary list.
- `tour(force)`: steps are found on the page as it is (phone bar or desktop controls), shown beside the control with an outline; no backdrop.
  Shown by itself only when the tune's booklet id contains "starter" and the device has no master code (`newcomer`), or after the download
  card; localStorage `aam-tour` makes it once per device. Analytics: `aam_tour {how: done|skip, step}`.
- Checks: `--only pdf` (22). `AAM_STARTER=<a Starter Pack code>` on the command line adds the real-newcomer check; the code is never stored.
- 22 Nov: **v1.4 released** (Alex: "ship both"): the download card and the first-visit tour are live. Still test-only: the seven beta band
  styles (each `beta: true`) and the theory cards (`release/cards.html` does not exist, so /theory says "coming soon").
- 22 Nov, after v1.4 (Alex's notes from his phone): **beta** has a `next-line` chip (made in `contents()`, appended to `.music-row`, hidden on
  a booklet's last line or a tune with no booklet) and the tour reordered to how a line should be practiced: instrument, Learn, Play,
  tempo, Next, title. A booklet's lines cannot change instrument (only concert-pitch demo tunes have `inst-btn`), so on a booklet the first
  note says to reply to the email for a different pack. Idea not built: let a newcomer switch between the alto, tenor and flute Starter
  Packs from the player; it needs the tenor and flute sign-ups (or their codes in the player, which the code rule forbids).
- 22 Nov (Alex at his computer): MailerLite double opt-in turned OFF for the Starter Pack Alto form (the confirmation email and page cannot
  be edited on the free plan), the form's own success message rewritten, Email 1 reduced to one linked sentence to the download card. He
  tested it: works. **Beta:** `tuner-btn` and `hear` are now `.p-ic` icon buttons in `.pbar` (same data-r, so nothing else changed); Learn
  and Next sit at the right of `.music-row`. The bar is sized for 360 px phones; the tempo slider is hidden between 621 and 1099 px.
- 22 Nov, **beta: one-tap Learn** (Alex: the long-note check is too much for a newcomer). `learnStart` no longer calls `openTuner`. In `ear`:
  with no saved check, `autoFloor` = 1.6 x the quietest tenth of the first 2.4 s (0.006 to 0.02). In `learnHear`: after four accepted notes
  the median deviation is saved as `{off, floor, at, auto: true, lvl: "easy"}` (so the next visit skips nothing and the Tuner opens ready);
  twelve seconds with no pitched sound shows "I can't hear a note yet" and `learn-check`, which clears the saved check and opens the full
  two-step one, then returns to Learn. Checks (`--only learn`): fresh device clean, fresh device weak and 25 cents flat, fresh silent room.
  NOT tried on a real instrument and phone yet: Alex to test with his saxophone.
- 22 Nov, **beta: a clean Learn bar** (Alex: too many buttons). `learn-stop` is always hidden (the `learn-btn` chip shows "Stop" through
  CSS while pressed); `learn-skip` is hidden at each new note and shown by three misses, an out-of-tune warning on Strict, twenty seconds
  on one note, or the can't-hear message; `learn-again` and the new `learn-next` (clicks the `next-line` chip) show when the line is done;
  `learn-lvl` moved to the Band chips row (settings sheet on phones), still shown only while Learn is on. The opening line no longer says
  what the note sounds as on a piano. Checks: `--only learn` (21). Not built: the two stars and the Unit 1 invitation (not yet approved).
- 22 Nov: the speaker (`hear`) moved again at Alex's request, from the play bar to `.key-row` at the foot of the music card, right-hand end,
  beside the line's description. The tuner stays on the bar beside the metronome.
- 22 Nov, three beta fixes from Alex's phone: (1) `TESTQ` keeps `&player=test` in `urlFor` and in the address after the code is removed:
  before, the FIRST move to another line loaded the released player, which is why "the changes disappeared" on Au Clair de la Lune (every
  change is app-wide, none is tied to one tune). (2) a ResizeObserver on `learn-bar` calls `drawScore()` when the bar's height changes
  (the music was cut off under the finished message on his iPhone; headless Chromium does not reproduce the cut, so the check
  "after a clean run on a phone" passes with or without the fix: only his phone proves it). (3) `learn-lvl` shows in the settings whenever
  the line has Learn, labelled "Learn level: ...", and can be set before starting.
- 22 Nov (later): `DEF_REPS = 2` (a tune's own `reps` still wins; "through the keys" still becomes 12). `tuner-btn` is now a chip in the
  Band row (the settings sheet); its click closes the sheet first. Checks reach it with `tunerOpen(page)`. Alex's wider aim, in his words:
  "extremely useful but without the clutter"; a review with further candidates (the key button on fixed-instrument lines, repeats, My
  tunes, the How it works text) was given in chat and is waiting for his choices. Tempo popup idea (Italian terms, a goal linked to the
  booklet) also discussed, not built.

- 22 Nov (evening), Alex said "go ahead" on the whole review. Built in beta: `FIXED_KEY` (`TUNE.keys === "off"` and the tune has an
  `instrument`: a printed booklet line) hides `p-key`, `key-btn` and `cycle`; `.pbar .p-reps` is never displayed (its text is still
  written, the checks read it) and `row-loop` (range, repeats) plus the `hint` line are shown in the settings sheet again;
  `lib-btn` is an icon with the label "My tunes"; the `tips` section holds one button, `tour-btn`, which closes the sheet and fires
  the document event `aam-tour` (the library answers with `tour(true)`); the tempo chips are labelled by `term(bpm)`. Checks: the
  second "bar" block and `setReps` in "apply". Still to do from that talk: goal tempos printed in the booklet and linked to the
  player (next booklet edition). While playing, the "1/2" pass count is no longer visible on a phone: say so if Alex misses it.
