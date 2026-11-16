# aam-tunes

Tune files for the Alex Attard Music play-along player (alexattardmusic.com/play).

- `index.json` lists every PDF (title, unlock-code fingerprint, its tunes) and each tune's title.
- `tunes/<slug>.json` holds one tune (format `aam-tune/1`): chord changes, demo notes and notation. The player loads a tune only when a student opens it.

Adding a tune = adding one file to `tunes/` and one entry to `index.json`. Nothing on the website changes.
