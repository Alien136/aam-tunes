# Sound set v3: sources and licences (step 1 of Roadmap row 3.6)

Written 26 Nov 2026 by the nightly builder. No sound file has been downloaded or added yet: this is the licence check that
comes first. "Opened" means the page was read on that date; "label only" means only the one-word licence label in the
SFZ Instruments index was read, and the library's own page or licence file must be opened before a single sample is used.

The player is part of a paid teaching business, so anything marked non-commercial (NC) is out. Share-alike (SA) libraries are
avoided: our trimmed MP3s are modified samples and would have to carry the same licence.

## Chosen, licence read

| For | Library | By | Licence, as the page words it | Opened | Notes |
|---|---|---|---|---|---|
| Electric bass | [Growlybass](https://sfzinstruments.github.io/basses/growlybass) | Karoryfer Samples | "CC0-1.0" | instrument page | "Squier Jazz bass." WAV, 44.1 kHz, 160 MB: `https://github.com/sfzinstruments/karoryfer.growlybass/releases/download/v1.002/Karoryfer.Growlybass.v1.002.zip`. Fingered or picked, layers and round robins: not stated on the page; read the README in the zip. |
| Percussion | [World and Rare Percussion](https://freepats.zenvoid.org/Percussion/world-and-rare-percussion.html) | FreePats (recordings by Xavimart, Gonzalo and Roberto; claves and conga from VCSL) | "Published under the terms of the Creative Commons CC0 1.0 public domain dedication." | project page | Has conga, bongos, claves, egg shaker, maracas, tambourine, hand clap, cajón, castanets, darbuka. Has NO cowbell, guiro, timbales, agogo or cabasa. WAV, 8 MB: `https://github.com/freepats/world-percussion/releases/download/2020-09-05/WorldPercussion-SFZ+WAV-20200905.7z` |

## Candidates, not settled

| For | Library | By | Licence | Opened | What is missing |
|---|---|---|---|---|---|
| Pop kit | [Naked Drums](https://sfzinstruments.github.io/drums/naked_drums) | Wilkinson Audio | "CC-BY-4.0" (credit required, like the piano) | instrument page | Yamaha Recording Custom kit, two snares, six toms, hi-hats, ride, crashes, splashes, chinas; 10 round robins, up to 5 layers; FLAC, 1.3 GB, repository `sfzinstruments/WilkinsonAudio.NakedDrums`. The exact credit wording is not on the page: read the repository's licence file. First choice for the pop kit. |
| Pop kit | [Muldjord Kit](https://sfzinstruments.github.io/drums/muldjord_kit) | DrumGizmo Team | "CC-BY-4.0" | instrument page | 347 MB, FLAC. The page lists no pieces. |
| Pop kit | Big Rusty Drums | Karoryfer Samples | CC0-1.0 | label only | 2.3 GB. "An oversized drum kit from 1980s Poland." Its own page could not be opened tonight. |
| Brushes (for Jazz Ballad) | Swirly Drums | Karoryfer Samples | CC0-1.0 | label only | 1.6 GB. "Punk/indie drums and unusual percussion played with brushes." Its own page could not be opened tonight, so whether it has a brush sweep is not known. |
| Electric piano | [Greg Sullivan E-Pianos](https://sfzinstruments.github.io/pianos/greg_sullivan_e-pianos) | Greg Sullivan | "CC-BY-3.0" (credit required) | instrument page | 21.5 MB, repository `sfzinstruments/GregSullivan.E-Pianos`. The page does not say which three instruments (Rhodes, Wurlitzer or other), the notes sampled or the layers. The only electric piano found so far whose licence allows a business to use it. |
| Cowbell and the missing Latin percussion | [Versilian Community Sample Library](https://github.com/sgossner/VCSL) | Versilian Studios LLC | README: "This collection is under a Creative Commons 0 license." | repository front page | 4 GB. The front page lists no instruments (folders Idiophones and Membranophones were not opened), so cowbell, guiro, timbales, agogo and cabasa are NOT confirmed. |
| Electric bass (spares) | Black And Blue Basses, Fashionbass, Swagbass, Pastabass | Karoryfer Samples | CC0-1.0 | label only | Only if Growlybass turns out wrong for the job. |

## Ruled out

| Library | Why |
|---|---|
| jRhodes3c (Jeff Learman) | "CC-BY-NC-SA-4.0": non-commercial. |
| jRhodes3d (Jeff Learman) | Samples "CC-BY-NC": non-commercial. |
| Rickenbacker 4001 (Project 16) | "CC-BY-NC-SA-3.0": non-commercial. |
| AVL Drumkits (Glen MacArthur) | "licensed CC-BY-SA 3.0": share-alike on modified samples. |
| Salamander Drumkit (Alexander Holm) | "CC BY-SA": share-alike on modified samples. It has a cowbell; do not take it from here. |
| Sam's Sonor | CC-BY-SA-4.0 (label). |
| SM Drums | Labelled "Public Domain" with no licence text, 2.2 GB on Google Drive: no licence to point to. |
| G1, L1 (TKDrums), Standard Bass (Unreal Instruments) | "Freemium" / "Custom": no free licence stated. |

## Next steps, in order

1. Electric bass first, alone: it is small, CC0 and settled. Download the Growlybass zip, read its README and licence file, add a
   `v3` block to `tools/build_sounds.py` on the pattern of the upright bass (every third note, three layers, two takes), write
   `sounds/v3/` with its own `manifest.json` and credits, and teach the player to load a second set only for a style that asks for
   it. `sounds/v2/` is never changed. Check that the workspace can reach the download address before anything else; if it cannot,
   say so in the Nightly log and stop.
2. Percussion from the FreePats pack (conga, bongos, claves, shaker, tambourine).
3. Open the Naked Drums repository's licence file, then the pop kit: kick, snare, closed and open hi-hat, crash, ride.
4. Electric piano: open the Greg Sullivan repository, find out what the three instruments are, then decide.
5. Cowbell, guiro, timbales: open the VCSL folders. Until they are found under CC0 or CC BY, Salsa waits or goes without them.
6. Every library with a CC BY licence gets a line in `sounds/README.md`, in the manifest's credits and in the player's credit
   at the foot of Practice settings, in the same commit that adds its first sample.
