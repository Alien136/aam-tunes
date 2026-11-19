#!/usr/bin/env python3
"""Release the player: run the page-by-page check and the feature check on the test copy (player/aam-player.html) and, only if it is all clear,
stamp a version and copy it to release/player.html, which is what the website loads.

  AAM_CODE=<master code> python3 tools/release.py          then: git add -A && git commit && git push

The website's loader shows the release within about five minutes of the push. ?player=test on the page loads the test copy."""
import os, subprocess, sys, datetime, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
r = subprocess.run(["node", os.path.join(ROOT, "tools", "check_release.js")], cwd=ROOT)
if r.returncode != 0:
    sys.exit("NOT released: the check found problems (above).")
r = subprocess.run(["node", os.path.join(ROOT, "tools", "check_features.js")], cwd=ROOT)      # tuner, Learn mode, cloud, contents search, PDF download, play bar
if r.returncode != 0:
    sys.exit("NOT released: a feature check failed (above).")
src = open(os.path.join(ROOT, "player", "aam-player.html"), encoding="utf-8").read()
n = len(re.findall(r'var PLAYER_VERSION = "test copy";', src))
assert n == 1, "PLAYER_VERSION line not found"
short = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
ver = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M") + " UTC" + (" (after " + short + ")" if short else "")
out = src.replace('var PLAYER_VERSION = "test copy";', 'var PLAYER_VERSION = "%s";' % ver)
os.makedirs(os.path.join(ROOT, "release"), exist_ok=True)
open(os.path.join(ROOT, "release", "player.html"), "w", encoding="utf-8").write(out)
demo = open(os.path.join(ROOT, "player", "demo.html"), encoding="utf-8").read()                 # the public demo card goes out with it
open(os.path.join(ROOT, "release", "demo.html"), "w", encoding="utf-8").write(demo)
print("Released:", ver, "-> release/player.html and release/demo.html  (commit and push to make it live)")
