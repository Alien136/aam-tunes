# Alex Attard Music play-along: where things stand (16 Nov 2026)

Everything needed to carry on from any conversation is in this repository and in the saved skills (`lead-sheet`, `starter-book`).

## What is live
- Player: `player/aam-player.html` is the block pasted into the Elementor HTML widget on alexattardmusic.com/play. The site has the latest version (start_key, http/https fix, booklets, key change, page turn).
- Library: `index.json` + `tunes/`. PDFs and codes:
  - G.I. piano, F Blues piano (earlier codes, see index.json ids `gi-piano`, `fblues-piano`)
  - Winter Wonderland piano WW-2193, Winter Wonderland alto WA-5627
  - F Blues alto FBA-9872 (4 pages: arpeggios, scales, patterns, licks)
  - Saxophone Welcome Booklet alto SWA-9426, tenor SWT-2764 (21 exercises each)
- Codes are stored as hashes: sha256("aam:" + CODE without dash, upper case).

- 17 Nov: the player uses the full-screen app layout on every screen (was phones only): wide screens get a centred 1180px column, full tab names, a tempo slider and bar/chord readout on the play bar, a centred settings card, a "← Website" link and space bar = play/stop. **Alex still has to paste this version into the Elementor Player widget.**

## Tools (`tools/`)
- `gen_study.py`, `fit_study.py`, `add_qr.py`, `publish_tune.py`: lead-sheet study PDF -> tune + QR. `example_blues_alto_spec.json` is the standard 4-page blues build.
- `build_book.py`, `book_player.py`, `publish_exercise.py`: Welcome Booklet PDF, its exercises and QR codes.
- `tests/`: headless-Chrome (Playwright) checks run against a local copy of the player; `player-with-inline-catalog.html` is the standalone test/artifact version of the player.

## Open items
1. Minor ii-V-i fix: blues bar 8 must be m7b5 -> 7b9 (alto F#m7b5 B7b9), bar 11 VI7b9. The skills have the rule; `gen_study.py` cannot print 7b9 yet. F Blues alto, both Welcome Booklets and their blues tunes still show the old bar 8 and need a rebuild.
2. /play page title still "Student Enrollment" (Yoast SEO title on the Play page).
3. InMotion hosting returned intermittent 502s on /play on 16 Nov (about 9:26 pm and 9:43 pm Pacific).
4. Access is per PDF code and per device; no per-student tracking. Student logins would be a separate build.
5. Not built: self-updating player loader, tempo ladder (60->120 then double), tenor/clarinet/flute lead-sheet editions untested, audio never checked by Claude, "Hear it" uses a piano sound for every instrument.
