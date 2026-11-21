# Change log

What changed for students, by version. The nightly builder adds lines under **Unreleased**; `tools/release.py --version X.Y`
moves that block under the new version when Alex says "ship".

- **Added**: something a student or Alex can now do.
- **Fixed**: something that was wrong and is now right.
- **Prevented**: something a check or the guard stopped before it reached a student. Say which check, and what would have broken.

## Unreleased

### Added
- Flute lines (the new Flute Beginner Booklet) show the flute fingering chart in the tuner and in Learn mode, the same diagram as the printed booklets, from low C to high G. A right note in the wrong octave says "Same fingers: change the speed of your air."
- The booklet's PDF button is now first in the contents list ("Download the booklet (PDF)"), above the search box. A link that ends in `&pdf=1` opens the player with that list open and the button marked, for the "download the booklet" link in the Starter Pack emails. Analytics records whether a download came from the link or the list.
- Tunes written at concert pitch (the free demo tunes) show an instrument under the title, and tapping it lets the reader choose theirs: piano, flute, clarinet, tenor or alto saxophone. The page is rewritten for it, the choice is remembered, and the tuner and Learn mode follow it (Learn accepts the right note in any octave).
- The public demo on the lessons page uses the same instrument button, with trumpet added, in place of its small "I play" menu. The page changes at once, without reloading the tune, and Analytics records which instrument was chosen.

### Fixed
- Opened from the home screen, the play bar sat too close to the bottom edge of the phone and was partly cut off. It now keeps clear of the edge.
- Beginner Booklet and Starter Pack, page 28 (alto and tenor): the green SCALE label on line 116, "C major arpeggio, two octaves", was printed over the line's tick box. The generator now sets a heading that is too long for its space slightly smaller, so it stops short of the box. Fixed in the generator; the PDFs students download still show the old page until the booklets are republished.

### Prevented
- Booklet generator (`cell` in `tools/build_beginner.py`): it now refuses to build when a line's title and label cannot fit beside the tick box even at the smaller size. A clarinet, flute or piano book built from the same generator cannot print a label over a tick box.

## v1.2 · 2026-11-20

### Added
- Free Saxophone Starter Pack (alto and tenor): the Beginner Booklet under its own code, with a last page inviting the free first lesson. It opens the same play-along lines as the Beginner Booklet and has its own PDF download.
- Install on phone: the player page carries a home-screen icon, a name and the full-screen flag, and Practice settings has "Add to your home screen" with the steps for the phone in hand. (Working with no signal needs one file uploaded to the website; not done yet.)
- (Test copy only, not offered to students yet) four more band styles waiting for Alex's ear: Slow Swing, Samba, Afro-Cuban, Shuffle Blues.
- Learn mode on piano pages, one hand at a time: tap Learn, choose Right hand or Left hand, and it follows that staff. A hand with a few chords is fine (any note of the chord counts); a hand that is all chords is not offered.

### Changed
- Metronome: the "Play it: with the music / metronome only" choice is now "Band: with the band / metronome only", and it is hidden on pages that have no band (pieces and exercises), where it did nothing.

### Fixed

### Prevented

## v1.1 · 2026-11-20

### Added
- Band styles: a picker beside the instrument's name (and in Practice settings) changes the band while it plays. Five styles to start: Medium Swing, Two-Feel, Up-Tempo Swing, Bossa Nova, Straight Ballad. The choice is remembered per tune.
- "Apply changes": while the band is playing, a new number of repeats, a new key or a new instrument reading waits (the choice is outlined) until "Apply changes" above the Play button is tapped. Stopping applies it. Tempo, style, the mix and the metronome stay instant.

### Fixed
- During a page turn the cloud could show as a plain blue shape, or the notes turned blue with no cloud. The copy of the next page no longer carries a cloud or a second copy of its blur.
- "How many times through" is now "Number of repeats".

### Prevented

## v1.0.2 · 2026-11-20

### Added
- Piano pages: the left hand has its own blue cloud during playback, so each hand shows where it is. Single-line instruments keep one cloud.

### Fixed
- During playback the bar no longer has a second, larger blue wash behind the note's cloud (it showed most during a page turn). A bar with nothing written in it still gets the faint wash, so the place is never lost.

## v1.0.1 · 2026-11-20

### Added
- Under the title, an instrument icon and name (piano, saxophone, clarinet or flute) replace the line of small text, so a student sees at once they have the right edition.

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
