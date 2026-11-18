#!/usr/bin/env python3
"""Turn a two-staff piano MIDI file (as LilyPond writes from a public-domain source score) into a repertoire source file:
one ABC string per bar for each hand, in the piece's key. The result is the starting point for an Alex Attard Music edition;
fingering, phrasing and dynamics are then added by hand in the ABC.

  python3 tools/import_ly_midi.py in.midi out.json --key F --meter 3/4 --title "Minuet in F" --composer "W. A. Mozart" ...
"""
import argparse, json, mido
G = 12                                   # grid: twelfths of a beat (sixteenths = 3, triplet eighths = 4, eighths = 6)
NEXT = {}
LET = "CDEFGAB"; NAT = [0, 2, 4, 5, 7, 9, 11]
SHARPS, FLATS = "FCGDAEB", "BEADGCF"
KEYS = {"C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "F": -1, "Bb": -2, "Eb": -3, "Ab": -4,
        "Am": 0, "Em": 1, "Bm": 2, "Dm": -1, "Gm": -2, "Cm": -3, "Fm": -4}

def keysig(key):
    n = KEYS[key]
    return {l: 1 for l in SHARPS[:n]} if n > 0 else {l: -1 for l in FLATS[:-n]} if n < 0 else {}

def read(path):
    mid = mido.MidiFile(path); tpq = mid.ticks_per_beat; hands = []
    for tr in mid.tracks:
        t, on, notes = 0, {}, []
        for m in tr:
            t += m.time
            if m.type == "note_on" and m.velocity > 0: on.setdefault(m.note, []).append(t)
            elif m.type in ("note_off", "note_on") and on.get(m.note):
                s = on[m.note].pop(0); notes.append((round(s * G / tpq), m.note, max(1, round((t - s) * G / tpq))))
        if notes: hands.append(sorted(notes))
    return hands

def spell(midi, ks, tonic, minor=False, rises=False):
    """Letter, accidental and octave for a pitch: in the key if it can be; otherwise the usual chromatic spelling for the key
    (major keys: raised 1st, 4th and 5th degrees as sharps, lowered 3rd and 7th as flats)."""
    pc = midi % 12
    for i, l in enumerate(LET):
        v = NAT[i] + ks.get(l, 0)
        if v % 12 == pc: return l, ks.get(l, 0), (midi - v) // 12 - 1
    if rises: want = 1                           # a chromatic note that steps up a half step is written as a sharp
    elif minor: want = {1: -1, 4: 1, 6: 1, 9: 1, 11: 1}[(pc - tonic) % 12]     # counted from the minor tonic: raised 3rd, 4th, 6th, 7th
    else: want = {1: 1, 3: -1, 6: 1, 8: 1, 10: -1}[(pc - tonic) % 12]
    for acc in (0, want, -want):                 # a natural that cancels the key signature comes first (B natural in F major)
        for i, l in enumerate(LET):
            if (NAT[i] + acc) % 12 == pc: return l, acc, (midi - NAT[i] - acc) // 12 - 1

def abc_note(l, a, octv, state, ks):
    name = (l, octv); cur = state.get(name, ks.get(l, 0)); acc = ""
    if a != cur: acc = {1: "^", -1: "_", 0: "="}[a]; state[name] = a
    s = l if octv <= 4 else l.lower()
    s += "," * max(0, 4 - octv) + "'" * max(0, octv - 5)
    return acc + s

def dur(d):                                   # d in twelfths of a beat; ABC unit is the eighth (6)
    if d % 6 == 0: n = d // 6; return "" if n == 1 else str(n)
    if d % 3 == 0: return {3: "/2", 9: "3/2", 15: "5/2", 21: "7/2"}[d]
    raise ValueError("odd duration %d" % d)

def bars_for(notes, key, bpb, nbars):
    minor = key.endswith("m"); tonic = (7 * KEYS[key] + (9 if minor else 0)) % 12
    ks = keysig(key); tonic = (tonic, minor); L = bpb * G; out = []
    groups = {}                                # onset -> [pitches], shortest length wins (one rhythm per hand)
    for s, p, d in notes: groups.setdefault(s, []).append((p, d))
    onsets = sorted(groups)
    seq = []
    for i, s in enumerate(onsets):
        nxt = onsets[i + 1] if i + 1 < len(onsets) else None
        d = min(d for _, d in groups[s])
        if nxt is not None: d = min(d, nxt - s)
        if d in (5, 11, 17, 23): d += 1        # a note LilyPond's MIDI shortened slightly
        seq.append((s, sorted(p for p, _ in groups[s]), d))
    global NEXT; NEXT = {seq[i][0]: seq[i + 1][1] for i in range(len(seq) - 1)}   # onset -> the pitches that follow
    pos = 0; items = []                        # (start, pitches or None, length), rests filled in, split at barlines with ties
    for s, ps, d in seq:
        if s > pos: items.append((pos, None, s - pos, False))
        while d > 0:
            room = L - s % L; take = min(d, room)
            items.append((s, ps, take, d > take)); s += take; d -= take
        pos = s
    if pos % L: items.append((pos, None, L - pos % L, False))
    for b in range(nbars):
        state, parts, row = {}, [], [it for it in items if it[0] // L == b]
        if not row: out.append("z%d" % (bpb * 2)); continue
        i = 0
        while i < len(row):
            s, ps, d, tie = row[i]
            trip = [r for r in row[i:i + 3]]
            if d == 4 and len(trip) == 3 and all(r[2] == 4 for r in trip) and s % G == 0:   # a triplet of eighths on the beat
                parts.append((s, "(3" + "".join(tok(r, state, ks, tonic, "") for r in trip))); i += 3; continue
            if ps is None and d not in (3, 6, 9, 12, 18, 24, 36, 48):   # a rest of an odd length: split on the beat
                first = G - s % G if s % G else min(d, G)
                row[i:i + 1] = [(s, None, first, False), (s + first, None, d - first, False)]; continue
            parts.append((s, tok(row[i], state, ks, tonic, dur(d)))); i += 1
        txt = ""                               # notes inside one beat are beamed together; a space starts each new beat
        for j, (st, part) in enumerate(parts):
            txt += (" " if j and st // G != parts[j - 1][0] // G else "") + part
        out.append(txt)
    return out

def tok(r, state, ks, tonic, dtxt):
    s, ps, d, tie = r
    if ps is None: return "z" + dtxt
    names = [abc_note(*spell(p, ks, tonic[0], tonic[1], (p + 1) in NEXT.get(s, [])), state, ks) for p in ps]
    return ("[" + "".join(names) + "]" if len(names) > 1 else names[0]) + dtxt + ("-" if tie else "")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("midi"); ap.add_argument("out")
    for a in ("key", "meter", "title", "composer", "slug", "source", "note"): ap.add_argument("--" + a, default="")
    ap.add_argument("--tempo", type=int, default=100)
    ap.add_argument("--pickup", type=float, default=0, help="beats of pick-up before bar 1; the piece then opens with a bar of rests ending in the pick-up")
    a = ap.parse_args(); bpb = int(a.meter.split("/")[0])
    hands = read(a.midi); assert len(hands) == 2, "expected two staves, found %d" % len(hands)
    if a.pickup: sh = round((bpb - a.pickup) * G); hands = [[(s + sh, p, d) for s, p, d in h] for h in hands]
    end = max(s + d for h in hands for s, _, d in h); nbars = -(-end // (bpb * G))
    piece = {"slug": a.slug, "title": a.title, "composer": a.composer, "key": a.key, "meter": a.meter, "tempo": a.tempo, "source": a.source, "note": a.note,
             "rh": bars_for(hands[0], a.key, bpb, nbars), "lh": bars_for(hands[1], a.key, bpb, nbars)}
    json.dump(piece, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(a.title, nbars, "bars"); [print("%2d  %-34s | %s" % (i + 1, r, l)) for i, (r, l) in enumerate(zip(piece["rh"], piece["lh"]))]
