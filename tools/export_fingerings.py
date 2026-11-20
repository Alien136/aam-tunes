#!/usr/bin/env python3
"""Copy the saxophone fingering chart from tools/build_book.py into the player, so the diagram a student sees on screen is the
same one printed in the booklets.

  python3 tools/export_fingerings.py        rewrites the block between FINGERINGS:BEGIN and FINGERINGS:END in player/aam-player.html

Run it whenever KEYS or FINGERINGS change in build_book.py, then run the release check."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.argv = sys.argv[:1] + ["alto"]
import build_book as B
keys = [[k, shape, x, y, a, b, 1 if main else 0] for k, shape, x, y, a, b, main in B.KEYS]
notes = {}
for i, (ly, name, pressed, line) in enumerate(B.FINGERINGS): notes[58 + i] = [sorted(pressed), line]        # written pitch: low B flat = 58 ... high F = 89
assert len(notes) == 32 and B.FINGERINGS[0][0] == "bes" and B.FINGERINGS[-1][0] == "f'''"
block = "/* FINGERINGS:BEGIN (written by tools/export_fingerings.py from tools/build_book.py: do not edit by hand) */\nvar SAX_KEYS = %s;\nvar SAX_BOX = %s;\nvar SAX_FING = %s;\n/* FINGERINGS:END */" % (
    json.dumps(keys, separators=(",", ":")), json.dumps([B.KX_MIN, B.KX_MAX, B.KY_MIN, B.KY_MAX]), json.dumps(notes, ensure_ascii=False, separators=(",", ":")))
p = os.path.join(os.path.dirname(HERE), "player", "aam-player.html"); s = open(p, encoding="utf-8").read()
new, n = re.subn(r"/\* FINGERINGS:BEGIN.*?FINGERINGS:END \*/", lambda m: block, s, flags=re.S)
assert n == 1, "markers not found in the player"
open(p, "w", encoding="utf-8").write(new); print("fingerings written:", len(notes), "notes,", len(keys), "keys")
