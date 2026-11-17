#!/usr/bin/env python3
"""Find the largest staff and text sizes that keep a study at its target page count.

Usage: python3 fit_study.py spec.json
Target: 4 pages for tunes over 16 bars (one section per page), 2 pages otherwise.
Binary-searches, in order: music staff size (Sections 1, 3, 4), body text size, then the Section 2 page
text size (its staff scales with it). Writes them back into the spec as staff_size, text_size, s2_text_size.
"""
import json, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_study import build

STAFF = [x / 2 for x in range(28, 47)]      # 14 .. 23
TEXT = [x / 2 for x in range(18, 31)]       # 9 .. 15 pt


def pages(spec, work):
    ly = os.path.join(work, "fit.ly")
    open(ly, "w").write(build(spec))
    subprocess.run(["lilypond", "-s", "-o", os.path.join(work, "fit"), ly], check=True)
    data = open(os.path.join(work, "fit.pdf"), "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def largest(spec, key, values, target, work):
    """Largest value in sorted `values` for which the study still fits on `target` pages."""
    lo, hi, best = 0, len(values) - 1, values[0]
    while lo <= hi:
        mid = (lo + hi) // 2
        spec[key] = values[mid]
        if pages(spec, work) <= target:
            best, lo = values[mid], mid + 1
        else:
            hi = mid - 1
    spec[key] = best
    return best


def main(path):
    spec = json.load(open(path))
    target = spec.get("target_pages") or (4 if len(spec["bars"]) > 16 else 2)
    work = tempfile.mkdtemp(prefix="fit_")
    spec.pop("s2_staff_size", None)  # Section 2 staff is derived from s2_text_size
    spec["text_size"], spec["s2_text_size"] = TEXT[0], TEXT[0]
    staff = largest(spec, "staff_size", STAFF, target, work)
    text = largest(spec, "text_size", TEXT, target, work)
    s2_text = largest(spec, "s2_text_size", TEXT, target, work)
    json.dump(spec, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"target {target} pages -> staff {staff}, text {text}pt, section-2 text {s2_text}pt")


if __name__ == "__main__":
    main(sys.argv[1])
