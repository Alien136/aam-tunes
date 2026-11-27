# Sounds

`v2/` is the band the player uses: a recorded grand piano, upright bass and jazz drum kit, each note in several
loudness layers and alternate takes. `manifest.json` lists what is in the folder. The player loads these files
directly from this repository (see `SOUND_SOURCES` in `player/aam-player.html`); nothing needs uploading to the website.
Rebuilt with `tools/build_sounds.py`. A new set goes in a new folder (`v3/`), so old links keep working.

`v3/` holds sounds that only some band styles will use. So far: an electric bass (27 Nov 2026), 14 notes from low C# to the E flat
above middle C, three loudness layers, two takes each, files `e-<note>-<layer>-<take>.mp3`. The player fetches this folder only when
a style asks for the electric bass; no style does yet, so students never download it. In the test copy, adding `&bass=electric`
to a tune's link plays any band style with it. Built with `python3 tools/build_sounds.py v3 <unzipped Growlybass folder>`.

## Credits

| | Library | By | Licence |
|---|---|---|---|
| Piano | [Salamander Grand Piano V3](https://archive.org/details/SalamanderGrandPianoV3) | Alexander Holm | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) — trimmed, three of the sixteen layers, converted to MP3 |
| Bass | [Meatbass](https://github.com/sfzinstruments/karoryfer.meatbass) (pizzicato) | Karoryfer Samples, played by Drogomir Smolken | CC0 1.0 |
| Drums | [Virtuosity Drums](https://github.com/sfzinstruments/virtuosity_drums) | Versilian Studios / Virtuosity Musical Instruments, played by Austin McMahon | CC0 1.0 |
| Electric bass (`v3/`) | [Growlybass](https://github.com/sfzinstruments/karoryfer.growlybass) (sustained notes) | Karoryfer Samples | CC0 1.0 — three of four layers, two of four takes, trimmed, converted to MP3 |

The piano's licence requires credit wherever it is used: the player shows it at the bottom of Practice settings.
