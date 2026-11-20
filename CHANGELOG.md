# Change log

What changed for students, by version. The nightly builder adds lines under **Unreleased**; `tools/release.py --version X.Y`
moves that block under the new version when Alex says "ship".

- **Added**: something a student or Alex can now do.
- **Fixed**: something that was wrong and is now right.
- **Prevented**: something a check or the guard stopped before it reached a student. Say which check, and what would have broken.

## Unreleased

### Added

### Fixed

### Prevented

## v1.0 · 2026-11-20

Baseline: the first numbered version. Everything built up to 20 November 2026.

### Added
- Play-along player: band, click and drone styles, real notation, page turns, tempo wheel, key and instrument switch.
- Tuner with a microphone check. Learn mode: listens, marks each right note, names a wrong one, shows the fingering (saxophone).
- The blue cloud follows playback on every tune with notation.
- Booklet contents with search by number or name. The newest PDF of every booklet downloads from the player.
- Saxophone Beginner Booklet edition 4 (alto, tenor), Saxophone Welcome Booklet (alto, tenor), Graded Repertoire Level 1.
- Analytics events for practice, the tuner, Learn mode, fingering, PDF downloads and search.

### Prevented
- Desktop layout clipping reached students once (17 November): since then every tune is opened at four screen sizes before a release.
- Booklet PDFs growing the repository's history: they now live on a branch that keeps no history.
- A booklet code written in the public repository: codes are kept out, and `tools/guard.py` now refuses a push that contains one.
