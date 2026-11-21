#!/usr/bin/env python3
"""Copy the saxophone fingering chart from tools/build_book.py into the player, so the diagram a student sees on screen is the
same one printed in the booklets.

  python3 tools/export_fingerings.py        rewrites the block between FINGERINGS:BEGIN and FINGERINGS:END in player/aam-player.html and theory/cards.html

Run it whenever KEYS or FINGERINGS change in build_book.py, then run the release check."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.argv = sys.argv[:1] + ["alto"]
import build_book as B
keys = [[k, shape, x, y, a, b, 1 if main else 0] for k, shape, x, y, a, b, main in B.KEYS]
notes = {}
for i, (ly, name, pressed, line) in enumerate(B.FINGERINGS): notes[58 + i] = [sorted(pressed), line]        # written pitch: low B flat = 58 ... high F = 89
assert len(notes) == 32 and B.FINGERINGS[0][0] == "bes" and B.FINGERINGS[-1][0] == "f'''"
import beginner_flute as FL                                        # the flute's chart: the same diagram as the Flute Beginner Booklet
fkeys = [[k, shape, x, y, a, b, 1 if main else 0] for k, shape, x, y, a, b, main in FL.KEYS]
fnotes = {}
for i, (ly, name, pressed, line) in enumerate(FL.FINGERINGS + FL.HIGH): fnotes[60 + i] = [sorted(pressed), line]     # written pitch: low C = 60 ... high G = 91
assert len(fnotes) == 32 and FL.FINGERINGS[0][0] == "c'" and FL.HIGH[-1][0] == "g" + "'" * 3
block = ("/* FINGERINGS:BEGIN (written by tools/export_fingerings.py from tools/build_book.py and tools/beginner_flute.py: do not edit by hand) */\nvar SAX_KEYS = %s;\nvar SAX_BOX = %s;\nvar SAX_FING = %s;\n"
         "var FLUTE_KEYS = %s;\nvar FLUTE_BOX = %s;\nvar FLUTE_FING = %s;\n/* FINGERINGS:END */") % (
    json.dumps(keys, separators=(",", ":")), json.dumps([B.KX_MIN, B.KX_MAX, B.KY_MIN, B.KY_MAX]), json.dumps(notes, ensure_ascii=False, separators=(",", ":")),
    json.dumps(fkeys, separators=(",", ":")), json.dumps([FL.KX_MIN, FL.KX_MAX, FL.KY_MIN, FL.KY_MAX]), json.dumps(fnotes, ensure_ascii=False, separators=(",", ":")))
for rel in (("player", "aam-player.html"), ("theory", "cards.html")):          # the player, and the theory flash cards (the same diagrams)
    p = os.path.join(os.path.dirname(HERE), *rel); s = open(p, encoding="utf-8").read()
    new, n = re.subn(r"/\* FINGERINGS:BEGIN.*?FINGERINGS:END \*/", lambda m: block, s, flags=re.S)
    assert n == 1, "markers not found in " + "/".join(rel)
    open(p, "w", encoding="utf-8").write(new)
print("fingerings written: saxophone", len(notes), "notes,", len(keys), "keys; flute", len(fnotes), "notes,", len(fkeys), "keys")
