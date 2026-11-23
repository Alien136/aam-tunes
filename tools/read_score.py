"""Read a printed score (a PDF scan) into notes, bar by bar, with two score-reading engines, and say where they disagree.

Usage: python3 tools/read_score.py score.pdf --pages 152-157 --out tools/out/scores/pas-de-deux [--skip-engines]

Why two engines (Alex, 22 Nov 2026: "take complex scores and recreate them for the app"). Reading exact pitches off a
dense scan by eye is where Claude makes mistakes; score-reading engines count staff lines by geometry and are good at
pitches, but each is weak somewhere else. Tested on Tchaikovsky's own piano version of the Nutcracker Pas de deux:
  Audiveris (Java, https://github.com/Audiveris/audiveris)  right bar count, clean voices and chords; misses tuplets.
  homr (Python, pip install homr)                            very good pitches in running passages; rhythm and voices jumbled.
A bar that both read the same way can be trusted; a bar where they differ is shown to a person with the scan beside it.
Neither engine's rhythm is trusted: note lengths are read by Claude from the bar's picture and checked by arithmetic.

What it writes into --out:
  pages.pdf          the pages asked for
  audiveris.mxl      Audiveris's reading (MusicXML), and audiveris.omr (its project, which holds where every bar is)
  homr/p-N.musicxml  homr's reading, one file per page
  bars/b-NNN.png     a picture of every bar, cut from the scan
  report.json        per bar: the notes each engine read on each staff, how far they agree, and flags
  review.html        the same as a page: picture, both readings, agreement. Open it in a browser.

Engines: set AAM_AUDIVERIS to the Audiveris launcher (default /opt/audiveris/bin/Audiveris; the .deb from its GitHub
releases can be unpacked with `dpkg -x` and run from there, it brings its own Java). homr is found on the PATH.
Either may be missing: the report then holds one reading and every bar is flagged "one engine only".
Needs: pypdf, pillow, music21, poppler (pdftoppm). Nothing here is committed: scores and readings stay in tools/out/.
"""
import argparse, html, json, os, re, shutil, subprocess, sys, zipfile
from collections import Counter
from fractions import Fraction as F


def run(cmd, log, timeout):
    with open(log, "w") as f:
        try:
            return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            f.write("\nTIMED OUT after %d s\n" % timeout); return 124


def staff_notes(measure):
    """A bar of one staff -> (note names in reading order, [length of each voice in quarter notes])."""
    names, lens = [], []
    voices = list(measure.voices) or [measure]
    for v in voices:
        t = F(0)
        for e in v.notesAndRests:
            if e.duration.isGrace: continue
            t += F(e.duration.quarterLength)
        lens.append(float(t))
    for e in sorted(measure.recurse().notes, key=lambda x: (float(x.getOffsetInHierarchy(measure)), -max(p.midi for p in x.pitches))):
        names += [p.nameWithOctave for p in sorted(e.pitches, key=lambda p: p.midi)]
    return names, lens


def parse(path):
    import music21 as m21, warnings
    warnings.simplefilter("ignore")
    s = m21.converter.parse(path)
    out = []
    parts = list(s.parts)
    n = max(len(p.getElementsByClass("Measure")) for p in parts) if parts else 0
    for i in range(n):
        bar = []
        for p in parts[:2]:
            ms = p.getElementsByClass("Measure")
            bar.append(staff_notes(ms[i]) if i < len(ms) else ([], []))
        out.append(bar)
    return out


def agreement(a, b):
    ca, cb = Counter(a), Counter(b)
    union = sum((ca | cb).values())
    return 1.0 if not union else sum((ca & cb).values()) / union


def geometry(omr_path):
    """Where each bar is on its page, from the Audiveris project: [(page, x0, y0, x1, y1)] in pixels of BINARY.png."""
    bars, images = [], {}
    z = zipfile.ZipFile(omr_path)
    sheets = sorted({int(m.group(1)) for n in z.namelist() for m in [re.match(r"sheet#(\d+)/sheet#\d+\.xml", n)] if m})
    for k in sheets:
        x = z.read("sheet#%d/sheet#%d.xml" % (k, k)).decode("utf-8", "replace")
        images[k] = "sheet#%d/BINARY.png" % k
        for sysm in re.finditer(r"<system id=.*?</system>", x, re.S):
            sx = sysm.group(0)
            ys = [float(v) for v in re.findall(r'<point x="[\d.]+" y="([\d.]+)"', sx)]
            if not ys: continue
            y0, y1 = min(ys), max(ys); pad = (y1 - y0) * 0.38
            for st in re.finditer(r'<stack id="\d+" left="(\d+)" right="(\d+)"', sx):
                bars.append((k, int(st.group(1)) - 12, int(y0 - pad), int(st.group(2)) + 12, int(y1 + pad)))
    return bars, images, z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--pages", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--skip-engines", action="store_true", help="reuse the readings already in --out")
    A = ap.parse_args()
    a, b = [int(x) for x in A.pages.split("-")] if "-" in A.pages else (int(A.pages), int(A.pages))
    os.makedirs(os.path.join(A.out, "homr"), exist_ok=True); os.makedirs(os.path.join(A.out, "bars"), exist_ok=True)
    work = os.path.join(A.out, "pages.pdf")
    if not A.skip_engines:
        from pypdf import PdfReader, PdfWriter
        r = PdfReader(A.pdf); w = PdfWriter()
        for i in range(a - 1, b): w.add_page(r.pages[i])
        w.write(work)
        aud = os.environ.get("AAM_AUDIVERIS", "/opt/audiveris/bin/Audiveris")
        if os.path.exists(aud):
            tmp = os.path.join(A.out, "_aud"); os.makedirs(tmp, exist_ok=True)
            run([aud, "-batch", "-export", "-output", tmp, work], os.path.join(A.out, "audiveris.log"), 240 * (b - a + 1))
            for ext in ("mxl", "omr"):
                src = os.path.join(tmp, "pages." + ext)
                if os.path.exists(src): shutil.move(src, os.path.join(A.out, "audiveris." + ext))
            shutil.rmtree(tmp, ignore_errors=True)
        else: print("Audiveris not found at %s (set AAM_AUDIVERIS)" % aud)
        subprocess.run(["pdftoppm", "-r", "200", "-png", work, os.path.join(A.out, "homr", "p")], check=True)
        if shutil.which("homr"):
            for f in sorted(os.listdir(os.path.join(A.out, "homr"))):
                if f.endswith(".png") and "teaser" not in f:
                    run(["homr", os.path.join(A.out, "homr", f)], os.path.join(A.out, "homr", f + ".log"), 300)
        else: print("homr not found on the PATH (pip install homr)")

    A_bars = parse(os.path.join(A.out, "audiveris.mxl")) if os.path.exists(os.path.join(A.out, "audiveris.mxl")) else []
    geo, images, z = geometry(os.path.join(A.out, "audiveris.omr")) if os.path.exists(os.path.join(A.out, "audiveris.omr")) else ([], {}, None)
    per_page = Counter(g[0] for g in geo)
    H_pages = []
    for f in sorted((x for x in os.listdir(os.path.join(A.out, "homr")) if x.endswith(".musicxml")), key=lambda x: int(re.search(r"(\d+)", x).group(1))):
        H_pages.append(parse(os.path.join(A.out, "homr", f)))
    # line the two readings up page by page: only where both found the same number of bars on the page
    H_bars, page_of, mismatch = [], [], set()
    if A_bars and geo:
        k = 0
        for pg in sorted(per_page):
            n = per_page[pg]; hp = H_pages[pg - 1] if pg - 1 < len(H_pages) else []
            if len(hp) != n: mismatch.add(pg)
            for j in range(n):
                H_bars.append(hp[j] if len(hp) == n else None); page_of.append(pg); k += 1
    else:
        for pi, hp in enumerate(H_pages):
            for x in hp: H_bars.append(x); page_of.append(pi + 1)
    n = max(len(A_bars), len(H_bars))
    from PIL import Image
    pics = {k: Image.open(z.open(v)).convert("L") for k, v in images.items()} if z else {}
    report = []
    for i in range(n):
        ab = A_bars[i] if i < len(A_bars) else None
        hb = H_bars[i] if i < len(H_bars) else None
        row = dict(bar=i + 1, page=(page_of[i] + a - 1) if i < len(page_of) else None, staves=[], flags=[])
        agree = []
        for st in (0, 1):
            an, al = ab[st] if ab else ([], [])
            hn, hl = hb[st] if hb else ([], [])
            g = agreement(an, hn) if (ab and hb) else None
            if g is not None: agree.append(g)
            row["staves"].append(dict(audiveris=an, homr=hn, agreement=None if g is None else round(g, 2), audiveris_voice_beats=al))
        if not (ab and hb): row["flags"].append("one engine only" + (" (the engines counted a different number of bars on this page)" if row["page"] and (row["page"] - a + 1) in mismatch else ""))
        elif min(agree) < 0.9: row["flags"].append("the engines read different notes")
        if ab and any(v > 4.001 for st in ab for v in st[1]): row["flags"].append("a voice is longer than the bar")
        row["agreement"] = None if not agree else round(min(agree), 2)
        if i < len(geo):
            pg, x0, y0, x1, y1 = geo[i]
            name = "b-%03d.png" % (i + 1)
            pics[pg].crop((max(0, x0), max(0, y0), min(pics[pg].width, x1), min(pics[pg].height, y1))).save(os.path.join(A.out, "bars", name))
            row["picture"] = "bars/" + name
        report.append(row)
    json.dump(dict(source=os.path.basename(A.pdf), pages=[a, b], bars=report), open(os.path.join(A.out, "report.json"), "w"), ensure_ascii=False, indent=1)
    both = [r for r in report if r["agreement"] is not None]
    good = [r for r in both if r["agreement"] >= 0.9]
    esc = html.escape
    rows = []
    for r in report:
        cells = "".join("<td><b>%s</b><br><span class=a>A: %s</span><br><span class=h>H: %s</span><br><i>%s</i></td>" % (
            "Right hand" if k == 0 else "Left hand", esc(" ".join(s["audiveris"])) or "–", esc(" ".join(s["homr"])) or "–",
            "" if s["agreement"] is None else "agree %d%%" % round(s["agreement"] * 100)) for k, s in enumerate(r["staves"]))
        rows.append('<tr class="%s"><td class=n>%d<br><small>p. %s</small></td><td>%s</td>%s<td class=f>%s</td></tr>' % (
            "bad" if r["flags"] else "ok", r["bar"], r["page"], ('<img src="%s">' % r["picture"]) if r.get("picture") else "", cells, esc("; ".join(r["flags"])) or "✓"))
    open(os.path.join(A.out, "review.html"), "w", encoding="utf-8").write("""<!doctype html><meta charset=utf-8><title>Score reading: %s</title>
<style>body{font:14px/1.45 system-ui,sans-serif;margin:16px;color:#14171a}table{border-collapse:collapse;width:100%%}td{border-top:1px solid #d9dee3;padding:8px;vertical-align:top}
img{max-width:520px;width:100%%;background:#fff}.n{font-weight:700;font-size:18px;white-space:nowrap}.a{color:#0c5a8a}.h{color:#8a5a12}.bad{background:#fff6e5}.f{color:#a23b00;max-width:180px}
td{word-break:break-word;font-size:12.5px}h1{font-size:22px}</style>
<h1>%s, pages %d–%d</h1><p>%d bars. Both engines read %d of them; in %d the two readings match (90%% or more of the notes on both staves).
A = Audiveris, H = homr. Shaded rows need a person: compare the picture with the readings.</p><table>%s</table>""" % (
        esc(os.path.basename(A.pdf)), esc(os.path.basename(A.pdf)), a, b, n, len(both), len(good), "".join(rows)))
    print("%d bars; both engines on %d; matching readings on %d; flagged %d. Open %s" % (n, len(both), len(good), sum(1 for r in report if r["flags"]), os.path.join(A.out, "review.html")))
    if mismatch: print("pages where the engines counted different numbers of bars:", sorted(p + a - 1 for p in mismatch))


if __name__ == "__main__":
    main()
