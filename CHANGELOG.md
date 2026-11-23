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

## v1.5 · 2026-11-23

### Added
- F Blues (alto) rebuilt with a Sample Solo (5 pages); the player's Solo tab now holds it. Same link and code.
- The blank **Solo** tab is gone from every tune, in the live player too (17 tunes carried it). A tune gets a Solo tab back when it is rebuilt with a written Sample Solo; Fly Me to the Moon is the first.
- Chord & scale studies get a **Sample Solo**: a written chorus with the guide tones (3rd and 7th) in blue on beats 1 and 4, arpeggio notes between them in the first half and scale notes in the second. It replaces the blank "Your Chorus" page in the PDF and is the study's Solo tab in the player. First study: Fly Me to the Moon (piano).
- Beta (test copy only): the blank "Your solo" page is gone from the player; the Sample Solo's guide tones show in blue.
- Seven more band styles, approved by Alex on 22 Nov: Slow Swing, Samba, Afro-Cuban, Shuffle Blues, Soul Jazz, Jazz Waltz and Ballad in 3. They are in the style picker for everyone from the next release; Going Home plays with the band in 3.
- Beta (test copy only, and hidden in a released player until Alex has tried it): **My music, first step.** In My tunes, "Add my own music" takes a MusicXML file (.musicxml, or compressed .mxl) from the device and turns a one-line melody into a tune: the notes on the staff, Play with the click at any tempo, Hear it, Learn. Reads treble clef in 2/4, 3/4 and 4/4: key signature, accidentals, dotted notes, ties, triplets, sixteenth notes, a pick-up bar, and the transposition for saxophones, clarinet, trumpet and flute. The tune is kept on that device only; nothing is uploaded, and Analytics is told "my-music", never the tune's name. A file it cannot read whole (a piano score on two staves, two voices, 6/8, a bar that does not add up) is refused with the reason. "Remove this tune from this device" takes it off again. Not yet: piano (both hands), chord symbols with the band, repeats, MIDI files, the share file a teacher can send.
- Blues Études Vol. 1 and Vol. 2 are in the player's library: 8 études each, for alto sax, tenor sax and flute (48 tunes), written for each instrument as the PDF prints them, with the band, and locked by a code per edition (nobody has the codes yet). Made by the new `tools/publish_etudes.py`, which the product bots now use for every étude volume.
- Beta (test copy only): Learn mode follows lines with long runs of triplets or sixteenth notes. Before, a bar of triplets drifted by a hair and Learn was not offered on 20 of the 48 études.
- Beta (test copy only): **less on the screen.** A line printed in a booklet no longer shows the key button or "Through the keys" (it is played in the key on the page). The repeats button has left the play bar: the number of repeats is in the settings, with the one-line hint about tapping and looping bars. **My tunes** is a small icon. The "How it works" list is replaced by one button, **Show me around**, which replays the tour.
- Beta (test copy only): the three speeds in the tempo popup carry their musical term, worked out from the number (for example Andante · 76, Moderato · 96, Allegro · 116). Under 60 Largo, 60 Adagio, 72 Andante, 92 Moderato, 112 Allegro, 140 Vivace, 168 Presto.
- Beta (test copy only): every line now plays **twice** by default (it was once). The repeats button still changes it.
- Beta (test copy only): the **Tuner** has moved off the play bar into the settings, since it is used once or twice in a practice session.
- Beta (test copy only): a cleaner Learn bar. It starts with one short line and one button, Fingering. The Learn button reads Stop while Learn is on. Skip note appears only for a note that will not go (three wrong tries, twenty seconds on it, or nothing heard). Start again and Next line appear when the line is finished. Level (Forgiving or Strict) has moved into the settings.
- Beta (test copy only): **Learn starts in one tap.** No microphone check first: the player works out the room's level and how sharp or flat the student sits while they play, and keeps it. If it hears no clear note for twelve seconds it says so and offers a **Check microphone** button, which runs the full two-step check. The Tuner still has the full check.
- Beta (test copy only): the Tuner and "hear the notes" have moved to the play bar as icons: a gauge with a needle beside the metronome, and a speaker that is blue when on and struck through when off (the speaker then moved to the foot of the music, on the right). Learn stays above the music, on the right beside Next.
- Beta (test copy only): a **Next** button beside Hear it, Learn and Tuner on every booklet line: one tap goes to the next line of the booklet.
- Beta (test copy only): the tour is now six notes in practice order: the instrument the booklet is written for (and how to get another), Learn, Play, tempo, Next, the title.

### Fixed
- Beta only: the test copy now stays the test copy when you move to another line (Next, the contents list, My tunes). It used to drop back to the released player.
- Beta only: the music is laid out again whenever the Learn bar changes height, so the last line is no longer cut off when the finished message appears.
- Beta only: the Learn level (Forgiving or Strict) is in the settings whenever a line has Learn, not only while Learn is running.

### Prevented
- The feature check for the blue cloud went red on main on 23 Nov, after the blank Solo page was removed from every tune: one step of the check opened that page (the only page with an empty right hand). Nothing was wrong for a student. The nightly builder found it before pushing, and the step now checks the study's next page and that no blank Solo tab is shown.

## v1.4 · 2026-11-22

### Added
- Beta (test copy only): the "download the booklet" link (`&pdf=1`) now opens a small card with only the booklet's name, the download button and "Now play along", in place of the full contents list. "See every line in the booklet" opens the list.
- Beta (test copy only): a first-visit tour of four short notes (Play, tempo, Learn, the title) for someone who arrives with a free Starter Pack and no teacher's code. It shows once for a device, never blocks a tap, and can be skipped. `&tour=1` on a link shows it to anyone.
- Beta (test copy only): **note flash cards**, the first piece of the theory arm, at `/theory/?beta` (its own page). Free, no code screen. Pick an instrument, a card (name the note, find the piano key, find the saxophone or flute fingering, or find the note on the staff from a key or fingering), a clef and a level (2, 3 or 4 answers; ledger lines; sharps and flats). A 60-second sprint or 20 cards with no timer. Missed notes come back more often; scores stay on the device.
- Beta (test copy only, until Alex has listened): a **Soul Jazz** band style (even eighths, backbeat on 2 and 4, a bass riff) for tunes like Cold Duck Time and Mercy, Mercy, Mercy. Those two tunes open with it in the test copy; students keep Bossa Nova until it is released.
- Beta (test copy only): the band can play in 3/4. Two styles in three, **Jazz Waltz** (swung) and **Ballad in 3** (straight). A tune in 3/4 is offered only the styles in three, and a tune in 4/4 only the styles in four. Going Home's four exercises play with the band in the test copy; students keep the click until the styles are released.
- Beta (test copy only): **Learn mode has two levels, Forgiving and Strict.** Forgiving is Learn mode as it was: a clear note counts even when it is a little flat or sharp. Strict asks for the note in tune (within 30 cents) and held twice as long; a right note out of tune is never called wrong, the player says "Right note, but flat: bring it up a little." The first-time microphone check chooses: a steady long note in a quiet room starts on Strict, a wavering note or a noisy room on Forgiving. A "Level" button in the Learn bar changes it, and the choice is remembered on the device. Piano pages have no levels. Students who already did the microphone check stay on Forgiving until they change it or check the microphone again.

### Fixed

### Prevented

## v1.3 · 2026-11-21

### Added
- Flute lines (the new Flute Beginner Booklet) show the flute fingering chart in the tuner and in Learn mode, the same diagram as the printed booklets, from low C to high G. A right note in the wrong octave says "Same fingers: change the speed of your air."
- The booklet's PDF button is now first in the contents list ("Download the booklet (PDF)"), above the search box. A link that ends in `&pdf=1` opens the player with that list open and the button marked, for the "download the booklet" link in the Starter Pack emails. Analytics records whether a download came from the link or the list.
- Tunes written at concert pitch (the free demo tunes) show an instrument under the title, and tapping it lets the reader choose theirs: piano, flute, clarinet, tenor or alto saxophone. The page is rewritten for it, the choice is remembered, and the tuner and Learn mode follow it (Learn accepts the right note in any octave).
- The public demo on the lessons page uses the same instrument button, with trumpet added, in place of its small "I play" menu. The page changes at once, without reloading the tune, and Analytics records which instrument was chosen.

### Fixed
- On an iPad or iPhone the microphone check could "pass" while the player heard nothing: Safari can leave the sound engine asleep when it is started after the permission question instead of during the tap, and a sleeping engine delivers pure silence. The engine is now started inside the tap, the listening chain reaches the speakers at zero volume (Safari only runs a chain that does), and the first-time check hands the same live microphone to Learn mode instead of closing it and opening a second one.
- A microphone that is on but silent is no longer mistaken for a quiet room. The check stops and says so ("no sound is reaching the player"), the next tap anywhere wakes the engine, Learn mode shows the same message, and Analytics records it (`aam_mic_silent`).
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
