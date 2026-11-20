#!/usr/bin/env python3
"""Release the player: run the page-by-page check and the feature check on the test copy (player/aam-player.html) and, only if it is all clear,
stamp a version and copy it to release/player.html, which is what the website loads.

  AAM_CODE=<master code> python3 tools/release.py [--version 1.1]     then: python3 tools/guard.py --release && git add -A && git commit && git push

Without --version it re-releases the current version number (VERSION). With it, VERSION is updated and the "Unreleased" block of CHANGELOG.md
moves under the new version. Only a session with Alex runs this, after he says "ship": the nightly builder never does (see BUILDER.md).

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
now = datetime.datetime.now(datetime.timezone.utc)
vfile, clog = os.path.join(ROOT, "VERSION"), os.path.join(ROOT, "CHANGELOG.md")
number = open(vfile).read().strip()
if "--version" in sys.argv:                                                                   # a new version: write VERSION and close the "Unreleased" block of the change log under it
    number = sys.argv[sys.argv.index("--version") + 1].lstrip("v")
    assert re.fullmatch(r"\d+\.\d+(\.\d+)?", number), "version must look like 1.1"
    open(vfile, "w").write(number + "\n")
    log = open(clog, encoding="utf-8").read()
    head = "## Unreleased\n"
    assert log.count(head) == 1, "CHANGELOG.md needs exactly one '## Unreleased' heading"
    fresh = head + "\n### Added\n\n### Fixed\n\n### Prevented\n\n"
    body = log.split(head, 1)[1].split("\n## ", 1)[0]
    log = log.replace(head + body, fresh + "## v%s · %s\n%s" % (number, now.strftime("%Y-%m-%d"), body if body.startswith("\n") else "\n" + body), 1)
    open(clog, "w", encoding="utf-8").write(log)
ver = "v" + number + " · " + now.strftime("%Y-%m-%d %H:%M") + " UTC" + (" (after " + short + ")" if short else "")
out = src.replace('var PLAYER_VERSION = "test copy";', 'var PLAYER_VERSION = "%s";' % ver)
os.makedirs(os.path.join(ROOT, "release"), exist_ok=True)
open(os.path.join(ROOT, "release", "player.html"), "w", encoding="utf-8").write(out)
demo = open(os.path.join(ROOT, "player", "demo.html"), encoding="utf-8").read()                 # the public demo card goes out with it
open(os.path.join(ROOT, "release", "demo.html"), "w", encoding="utf-8").write(demo)
print("Released:", ver, "-> release/player.html and release/demo.html  (commit and push to make it live)")
