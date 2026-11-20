#!/usr/bin/env python3
"""Safety guard: run before every push. It compares the working copy with origin/main and refuses the push when a change
would hurt something a student already has, or would leak a code.

  python3 tools/guard.py              the nightly builder (the live player and the release tools may not change)
  python3 tools/guard.py --release    a release run with Alex (release/ may change)
  python3 tools/guard.py --tools      a session with Alex that changes guard.py or release.py on purpose

Exit code 0 = safe to push. Anything else: do not push; fix or undo, and log it under "Prevented" in CHANGELOG.md.

What it refuses
  1. release/ changed (only tools/release.py writes it, and only in a release run).
  2. tools/guard.py or tools/release.py changed (the builder may add checks, never loosen the gate).
  3. A PDF or .bin file on main (booklets live encrypted on the `pdf` branch).
  4. index.json: the master fingerprint changed; a booklet disappeared or its code fingerprint changed; a tune left a booklet;
     a tune lost its file; a listed tune has no file; the file does not parse.
  5. A tune file that existed was deleted, or no longer parses.
  6. A real code written into the repository (any word whose fingerprint matches the master or a booklet).
  7. The test player lost its root element, its version line or the sounds credit; a sound file was deleted.
"""
import hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE, TOOLS = "--release" in sys.argv, "--tools" in sys.argv
BASE = "origin/main"
problems = []


def git(*a, check=True):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit("guard: git %s failed: %s" % (" ".join(a), r.stderr.strip()))
    return r.stdout


def bad(msg):
    problems.append(msg)


git("fetch", "-q", "origin", "main")
changed = [l.split("\t") for l in git("diff", "--name-status", "--no-renames", BASE).splitlines() if l.strip()]
untracked = [l for l in git("ls-files", "--others", "--exclude-standard").splitlines() if l.strip()]
names = [(st, p) for st, p in changed] + [("A", p) for p in untracked]

# 1, 2, 3
for st, p in names:
    if p.startswith("release/") and not RELEASE:
        bad("release/ changed (%s): only a release run writes the live player" % p)
    if p in ("tools/guard.py", "tools/release.py") and not TOOLS:
        bad("%s changed: the gate is changed only in a session with Alex (--tools)" % p)
    if st != "D" and re.search(r"\.(pdf|bin)$", p, re.I):
        bad("%s: no PDF or .bin on main (use tools/publish_pdf.py, which puts it on the pdf branch)" % p)

# 4
try:
    new = json.load(open(os.path.join(ROOT, "index.json"), encoding="utf-8"))
except Exception as e:
    new = None
    bad("index.json does not parse: %s" % e)
old = json.loads(git("show", BASE + ":index.json"))


def tunes_of(p):
    t = list(p.get("tunes") or [])
    for ch in p.get("contents") or p.get("chapters") or []:
        if isinstance(ch, dict):
            t += [x for x in ch.get("tunes", []) if isinstance(x, str)]
    return set(t)


if new:
    if new.get("master") != old.get("master"):
        bad("index.json: the master fingerprint changed")
    npdf = {p["id"]: p for p in new.get("pdfs", [])}
    for p in old.get("pdfs", []):
        q = npdf.get(p["id"])
        if not q:
            bad("index.json: booklet '%s' disappeared" % p["id"]); continue
        if q.get("hash") != p.get("hash") or bool(q.get("free")) != bool(p.get("free")):
            bad("index.json: the code of '%s' changed (students hold it)" % p["id"])
        gone = tunes_of(p) - tunes_of(q)
        if gone:
            bad("index.json: %d tune(s) left '%s' (QR links would break): %s" % (len(gone), p["id"], ", ".join(sorted(gone)[:5])))
    nt, ot = new.get("tunes", {}), old.get("tunes", {})
    lost = set(ot) - set(nt)
    if lost:
        bad("index.json: %d tune(s) removed from the list: %s" % (len(lost), ", ".join(sorted(lost)[:5])))
    for slug in nt:
        if not os.path.exists(os.path.join(ROOT, "tunes", slug + ".json")):
            bad("index.json lists '%s' but tunes/%s.json is missing" % (slug, slug))
    for p in new.get("pdfs", []):
        for slug in tunes_of(p):
            if slug not in nt:
                bad("booklet '%s' lists '%s', which is not in the tune list" % (p["id"], slug))

# 5
for st, p in names:
    if p.startswith("tunes/") and p.endswith(".json"):
        if st == "D":
            bad("%s was deleted: a published tune is never removed" % p)
        else:
            try:
                json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
            except Exception as e:
                bad("%s does not parse: %s" % (p, e))

# 6
prints = {old.get("master")} | {p.get("hash") for p in old.get("pdfs", [])}
if new:
    prints |= {new.get("master")} | {p.get("hash") for p in new.get("pdfs", [])}
prints.discard(None)
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]{3,29}")


def scan(where, text):
    seen = set()
    for w in WORD.findall(text):
        n = re.sub(r"[^A-Za-z0-9]", "", w).upper()
        if len(n) < 5 or n in seen:
            continue
        seen.add(n)
        if hashlib.sha256(("aam:" + n).encode()).hexdigest() in prints:
            bad("%s contains a real code (%s...): codes are never written in this repository" % (where, w[:2]))
            return


added = "\n".join(l[1:] for l in git("diff", "--no-renames", "-U0", BASE).splitlines() if l.startswith("+") and not l.startswith("+++"))
scan("a changed file", added)
for p in untracked:
    fp = os.path.join(ROOT, p)
    if os.path.getsize(fp) < 5_000_000:
        try:
            scan(p, open(fp, encoding="utf-8").read())
        except UnicodeDecodeError:
            pass
env = os.environ.get("AAM_CODE", "")
if env and (env in added):
    bad("a changed file contains the master code")

# 7
src = open(os.path.join(ROOT, "player", "aam-player.html"), encoding="utf-8").read()
if 'id="aam-play"' not in src:
    bad("player/aam-player.html lost its root element")
if len(re.findall(r'var PLAYER_VERSION = "test copy";', src)) != 1:
    bad("player/aam-player.html: the PLAYER_VERSION line must appear exactly once and read \"test copy\"")
if 'data-r="snd-credit"' not in src or "man.credits" not in src:
    bad("player/aam-player.html no longer shows the sounds credit (the piano's licence requires it)")
for st, p in names:
    if p.startswith("sounds/") and st == "D":
        bad("%s was deleted: the live player loads it" % p)

if problems:
    print("GUARD: NOT safe to push (%d problem%s)" % (len(problems), "" if len(problems) == 1 else "s"))
    for m in problems:
        print("  - " + m)
    sys.exit(1)
print("GUARD: safe to push (%d changed file%s checked against %s)" % (len(names), "" if len(names) == 1 else "s", BASE))
