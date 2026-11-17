# Sounds

`v2/` is the band the player uses: a recorded grand piano, upright bass and jazz drum kit, each note in several
loudness layers and alternate takes. `manifest.json` lists what is in the folder. The player loads these files
directly from this repository (see `SOUND_SOURCES` in `player/aam-player.html`); nothing needs uploading to the website.
Rebuilt with `tools/build_sounds.py`. A new set goes in a new folder (`v3/`), so old links keep working.

## Credits

| | Library | By | Licence |
|---|---|---|---|
| Piano | [Salamander Grand Piano V3](https://archive.org/details/SalamanderGrandPianoV3) | Alexander Holm | [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/) — trimmed, three of the sixteen layers, converted to MP3 |
| Bass | [Meatbass](https://github.com/sfzinstruments/karoryfer.meatbass) (pizzicato) | Karoryfer Samples, played by Drogomir Smolken | CC0 1.0 |
| Drums | [Virtuosity Drums](https://github.com/sfzinstruments/virtuosity_drums) | Versilian Studios / Virtuosity Musical Instruments, played by Austin McMahon | CC0 1.0 |

The piano's licence requires credit wherever it is used: the player shows it at the bottom of Practice settings.
