# The nightly builder: runbook

A scheduled task runs this every night with nobody watching. It starts on a fresh machine with no memory of earlier nights, so
everything it needs to know is here, in `STATUS.md`, and in the Build Desk doc. Read this file first, every run.

The Build Desk (a Claude Doc; its link and ids are in the scheduled task's instructions) is where Alex follows the work:
Needs Alex · Ideas inbox · Roadmap · Library · Nightly log · Releases. The master code is given to the run in its instructions and is
passed to tools only as the environment variable `AAM_CODE`. It is never written in this repository, in a commit message or in a log.

## What "live" and "beta" mean

| | File | Who sees it | Who writes it |
|---|---|---|---|
| Live player | `release/player.html` | students, at alexattardmusic.com/play | only `tools/release.py`, only after Alex says "ship" |
| Beta player | `player/aam-player.html` | Alex, at alexattardmusic.com/play/?player=test | the builder |
| Tunes and booklets | `index.json`, `tunes/` | both players | generators in `tools/`; a new booklet is locked by its own code |
| Booklet PDFs | branch `pdf` (encrypted) | the player's download button | `tools/publish_pdf.py` |

So a player change is invisible to students until a release. A new booklet is data on `main`, but nobody can open it without its
code, and its code goes only into the Build Desk Library table until Alex releases the booklet to students.

## Every run, in this order

1. `bash tools/setup.sh` must print `SETUP: READY`. If it does not, write what is missing in the Nightly log and stop.
2. Read `STATUS.md` (the tail first), this file, `CHANGELOG.md` (the Unreleased block), then the Build Desk.
3. Pick ONE job with the rules below. Say which rule picked it in the log.
4. Do it. Time-box the build to about 40 minutes of work; if the job is bigger, do a complete, checked part and write the exact next
   step in the Roadmap row's "Next step" cell.
5. Check it (see "Checks"). Red means: fix it, or undo it with `git checkout -- .` and `git clean -fd`, and log what happened.
6. `python3 tools/guard.py` must print `GUARD: safe to push`. Never push without it. Never pass `--release` or `--tools`.
7. Commit (message: what changed for a student, then the two attribution lines the session gives) and `git push origin HEAD:main`.
   If the push is refused because main moved: `git pull --rebase origin main`, run the guard again, push again. Never force-push main.
8. Write the night up: `CHANGELOG.md` Unreleased (Added / Fixed / Prevented), one dated section appended to `STATUS.md` when a
   tool, a format or a rule changed, the Roadmap row, the Library table when a booklet moved, one new top row in the Nightly log.
   (Steps 7 and 8 can be one commit: write the files first, then guard, commit, push, then the doc.)
9. Final reply (it becomes Alex's phone notification), three lines at most:
   `Built: <what, in plain words>` / `Look: <beta link, or the Library row>` / `Needs you: <one thing, or nothing>`.

## Picking tonight's job

1. **Alex's fixes.** A line starting with FIX in the Ideas inbox, or a note he left under a Needs Alex item. Before fixing a bug that
   reached him, add a check to `tools/check_features.js` that fails on it; then fix it; then the check passes. Log it as Fixed, and
   say which check now guards it.
2. **A failing check** on `main` as you found it.
3. **By night** (use the date in Europe/Malta): Sunday, Monday, Wednesday, Friday = the top Booklet row that is In progress, else
   the top Queued one. Tuesday, Thursday = the same for Player rows. Saturday = the brand and style pass.
4. **Finish before starting.** Never have more than one Booklet row and one Player row In progress.
5. **Do not pile up unreviewed work.** If two booklets sit at Ready for Alex, start no new booklet: work a Player row or the style
   pass instead. If a Player row has sat unreviewed in beta through two release reviews, say so in Needs Alex and move on.
6. **New ideas.** Each night, move every new Ideas inbox line into the Roadmap as a Queued row, placed after the rows already In
   progress and before anything it obviously unblocks; delete the inbox line; mention it in the log. Ideas for PDF packs (Blues
   Études and similar) belong to the CPO: add them to the "Not on this list" note instead and tell Alex to put them on the AAM Board.
   An idea that needs a decision only Alex can make (price, a new product line, anything public) becomes a Needs Alex line, not work.
7. **Nothing to do?** Run the brand and style pass. Never invent a product.

Rows marked Hold, Approved, Released or Ready for Alex are never picked. A row Alex marked Approved is released by the Sunday review,
not by the builder.

## A booklet in six nights

Load the skill that owns the booklet first (`beginner-booklet`, `starter-book`, `graded-repertoire`) and follow it; where the skill
and the repository's generator differ, the repository wins. One stage a night. A stage is done only when its pages have been
rendered (`pdftoppm -r 70 -png`) and looked at one by one.

1. **Plan.** Written range, first notes and the order new notes arrive, the nine units and their tune lists, what differs from the
   saxophone book (clef, transposition, register break, fingering system). Check the order of notes against at least two published
   method books or syllabuses you actually opened; link them. Tunes: public domain only (US published 1930 or earlier; EU/Malta
   composer died before 1956), each with its source recorded in `src`. Write the plan into the Build Desk under the Roadmap as
   `### Plan: <booklet>`. No code yet.
2. **Fingering chart** (piano: keyboard and hand-position diagrams). Draw the instrument's key diagram and every fingering in the
   booklet's range. Check every fingering against two published charts you opened. Add a Needs Alex line: "Check the <instrument>
   fingering chart", with the page. An unverified fingering is never shown to a student.
3. **Units 1 to 3.** Copy the generator pattern (`tools/build_beginner.py`), do not fork the layout: instrument differences go in
   data (range, clef, transposition, chart), so one fix reaches every instrument's book.
4. **Units 4 to 6.**
5. **Units 7 to 9**, cover, contents, glossary. Every unit starts at the top of a page; no large empty space; fill with staff paper.
6. **Into the player.** Make the booklet's code (three letters, a dash, four random digits; unused prefix), write it ONLY in the
   Library table. Publish with `--publish` and `AAM_CODE` set: every numbered line becomes a tune, the PDF goes to the `pdf` branch.
   Run the full release check. Score the book out of 10 against the saxophone book and the skill's checklist; below 8, fix first.
   Then set the row to Ready for Alex, add the Library row (status Draft, with its Open link), and a Needs Alex line to play it through.

A second booklet for the same instrument reuses that instrument's chart, cover drawing and range data.

## A player job

- Edit `player/aam-player.html` only. Never `release/`. Keep markup, styles and script in the one file.
- Every new behavior gets a check in `tools/check_features.js` in the same commit.
- Nothing from the microphone is recorded or sent anywhere. The sounds credit stays. US spelling. No new outside script or font.
- Then run the full check (below). Tell Alex exactly where to tap in beta to see it.

## The brand and style pass (Saturdays)

Render every booklet's PDF from its generator. Compare with the brand rules: slate #2F3E4E, amber #D4922A, tint #FBF1E1, muted
#6B7785, rule #D9DEE3; Poppins headings, DejaVu Sans body; footer "Alex Attard Music" and the page number only; the same header,
tip-box and unit-opener system in every book; no page with a large empty band; no text touching or overlapping music. Fix ONE
inconsistency at its source (the shared code, not one book), rebuild every edition it touches, and keep every code and QR link the
same. If a rebuilt PDF changes what a student sees, republish it with a new edition date. Log before and after.

## Checks

- Changed the player, `index.json` or anything in `tunes/`: `node tools/check_release.js` then `node tools/check_features.js`
  (about 8 minutes together; run in the background and wait). Both must pass. Do NOT run `tools/release.py`.
- Changed a generator: rebuild every edition it makes and look at every page.
- Always: `python3 tools/guard.py`.
- Each time a check or the guard stops something, that is a result, not a failure: write one line under Prevented in
  `CHANGELOG.md` and in the Nightly log's Prevented cell (which check, what a student would have seen).

## Never

- Never run `tools/release.py`, write to `release/`, or change `tools/guard.py` or `tools/release.py`.
- Never change or reuse a code, a booklet id or a tune slug that exists. A renamed line keeps its old slug. Never delete a tune.
- Never write a code (master or booklet) in the repository, a commit message, `STATUS.md` or `CHANGELOG.md`.
- Never commit a PDF or `.bin` to `main`.
- Never publish music that is not public domain, or a melody from memory without checking it against a source you opened.
  If it cannot be checked, leave it out and say so.
- Never use a photo from the web in a book.
- Never send, reply to or forward email, post anywhere, buy or sign up for anything, or contact anyone.
- Never touch the website, the AAM Board, the AAM Playbook, the Student Progress Log, or a student's name.
- Never force-push `main`. Never rewrite history.
- More than one job a night: no.

## The Sunday release review

A second scheduled task. It writes; it does not ship.

1. Setup and reading as above. Run both checks and the guard on `main` as it stands.
2. Every Sunday: add a "Week of <date>" line to the Nightly log summing up the week: jobs done, what is in beta and not live, what
   was prevented, what is waiting on Alex.
3. If the newest version in `CHANGELOG.md` is 13 or more days old AND Unreleased has at least one Added or Fixed line AND the checks
   are green: propose the next version (v1.1, v1.2 ...). The proposal, in the final reply and at the top of the Releases section:
   what is in it (Added / Fixed / Prevented, in plain words), what was NOT verified by a machine (real instrument, real iPhone), and
   a test list Alex can do in 10 minutes on the beta link, step by step.
4. Alex replies "ship" in that chat. Only then: `AAM_CODE=... python3 tools/release.py --version <X.Y>`, `python3 tools/guard.py
   --release`, commit, push, add the Releases row in the Build Desk, set shipped Roadmap rows to Released and Draft Library rows he
   approved to Released. Anything else he replies is a list of fixes: put them in the Ideas inbox as FIX lines.
5. **Retro, every release** (this is how the loop gets better): for each Fixed line, is there a check that would catch it next time?
   For each thing Alex corrected by hand, is the rule written in this file or in the skill that builds that product? Add the missing
   check or rule. Skill changes are proposed to Alex with a skill card in that chat; rules for the builder go under Lessons below.

## Lessons

Newest first. One line each: what went wrong or was nearly wrong, and the rule that now prevents it. The builder adds a line when a
night taught something; the release retro prunes lines that have become checks.

- 2026-11-20 · Start of the loop. Earlier lessons live in `STATUS.md` and the project doc "Player review and next 10 steps".
