#!/usr/bin/env python3
"""Build the player's sound sets from free libraries (see CREDITS in each manifest).

  python3 build_sounds.py                      v2 (piano, upright bass, jazz kit). Sources cloned under /home/claude/sfzinstruments.
  python3 build_sounds.py v3 <Growlybass dir>  v3 (so far: the electric bass). The folder is the unzipped Growlybass release
                                               (address and licence in sounds/v3-sources.md).

Output: out/<set>/*.mp3 + manifest.json, relative to where it is run; copy the folder to sounds/<set>/. sounds/v2 is never rebuilt
in place: a changed set gets a new folder."""
import subprocess, os, json, sys
V3 = len(sys.argv) > 1 and sys.argv[1] == "v3"
SRC = "/home/claude/sfzinstruments"; OUT = "out/v3" if V3 else "out/v2"; os.makedirs(OUT, exist_ok=True)
NOTE = {"C": 0, "D#": 3, "F#": 6, "A": 9}
def run(args): subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + args, check=True)
def enc(inputs, out, dur, fade, ch, br, mix=None, thr=-55, gain=0):
    """inputs: list of files (mixed with weights in dB via `mix`), trimmed to the first sound, cut to `dur` with a fade-out."""
    a = []
    for f in inputs: a += ["-i", f]
    w = mix or [0] * len(inputs)
    pre = "".join(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,volume={w[i]}dB[a{i}];" for i in range(len(inputs)))
    mixf = "".join(f"[a{i}]" for i in range(len(inputs))) + f"amix=inputs={len(inputs)}:normalize=0[m];"
    post = (f"[m]silenceremove=start_periods=1:start_threshold={thr}dB:start_silence=0.002:detection=peak,"
            f"atrim=0:{dur},afade=t=out:st={dur - fade}:d={fade},volume={gain}dB" + (",pan=mono|c0=0.5*c0+0.5*c1" if ch == 1 else "") + "[o]")
    run(a + ["-filter_complex", pre + mixf + post, "-map", "[o]", "-ac", str(ch), "-c:a", "libmp3lame", "-b:a", br, os.path.join(OUT, out)])
def sounding_midi(f):
    """The pitch a sample actually sounds at (autocorrelation, 0.3 s in): file names differ by library, so every note is measured."""
    import numpy as np, math
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "22050", "-f", "f32le", "-"], capture_output=True, check=True).stdout, dtype=np.float32)
    seg = x[6615:6615 + 16384]; seg = seg - seg.mean(); ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
    lo, hi = 22050 // 700, 22050 // 25; k = lo + int(np.argmax(ac[lo:hi])); best = ac[k]
    for d in (2, 3, 4):                                    # the shortest period that is nearly as strong: not an octave below
        kk = k // d
        if kk > lo:
            j = kk - 3 + int(np.argmax(ac[kk - 3:kk + 4]))
            if ac[j] > 0.9 * best: k = j
    return 69 + 12 * math.log2(22050 / k / 440)
if V3:
    # ---- electric bass: Karoryfer Growlybass (Squier Jazz Bass, recorded direct, CC0 1.0). Its files are named an octave above the
    # sound (a2 is the open A string, 55 Hz = MIDI 33); db2 is the E string tuned down to C#. Layers p / f / ff of pp p f ff, takes 1 and 2
    # of 4, the sustained notes only (no staccato, release or scrape samples). 3.5 s where the upright has 3.0: it rings longer.
    G = sys.argv[2]; EN = {"c": 0, "db": 1, "eb": 3, "e": 4, "gb": 6, "a": 9}
    man = {"version": 3, "ebass": {"notes": [], "layers": 3, "rr": 2}}
    for nm, octv in [("db", 2), ("e", 2), ("gb", 2), ("a", 2), ("c", 3), ("eb", 3), ("gb", 3), ("a", 3), ("c", 4), ("eb", 4), ("gb", 4), ("a", 4), ("c", 5), ("eb", 5)]:
        midi = 12 * octv + EN[nm]                          # (octave + 1) * 12 for the name, minus the octave the names sit above the sound
        got = sounding_midi(f"{G}/sustain/{nm}{octv}_f_rr1.wav")
        if abs(got - midi) > 0.4: sys.exit(f"{nm}{octv} sounds at MIDI {got:.2f}, not {midi}: the note table is wrong, nothing written")
        man["ebass"]["notes"].append(midi)
        for li, v in enumerate(["p", "f", "ff"], 1):
            for rr in (1, 2):
                enc([f"{G}/sustain/{nm}{octv}_{v}_rr{rr}.wav"], f"e-{midi}-{li}-{rr}.mp3", 3.5, 0.7, 1, "64k", thr=-50, gain=2)
    man["credits"] = [{"what": "Electric bass", "name": "Growlybass", "by": "Karoryfer Samples", "licence": "CC0 1.0", "url": "https://github.com/sfzinstruments/karoryfer.growlybass",
                       "changes": "three of four layers, two of four takes, trimmed, MP3"}]
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
    print(len(os.listdir(OUT)), "files"); sys.exit()
man = {"version": 2, "piano": {"notes": [], "layers": 3}, "bass": {"notes": [], "layers": 3, "rr": 2}, "drums": {}}
# ---- piano: Salamander Grand Piano V3 (Yamaha C5), layers 4 / 8 / 12 of 16
for octv in range(1, 8):
    for nm in ["C", "D#", "F#", "A"]:
        midi = 12 * (octv + 1) + NOTE[nm]
        if midi < 33 or midi > 96: continue
        man["piano"]["notes"].append(midi)
        dur = 7.0 if midi < 60 else 6.0 if midi < 80 else 4.0
        for li, v in enumerate([4, 8, 12], 1):
            enc([f"{SRC}/SalamanderGrandPiano/Samples/{nm}{octv}v{v}.flac"], f"p-{midi}-{li}.mp3", dur, 1.2, 2, "96k", thr=-60)
# ---- bass: Karoryfer Meatbass pizzicato (1958 Otto Rubner double bass)
BN = {"c": 0, "eb": 3, "gb": 6, "a": 9}
for octv in range(1, 5):
    for nm in ["c", "eb", "gb", "a"]:
        midi = 12 * (octv + 1) + BN[nm]
        if midi > 60: continue
        man["bass"]["notes"].append(midi)
        for li, v in enumerate([2, 3, 4], 1):
            for rr in (1, 2):
                enc([f"{SRC}/karoryfer.meatbass/Samples/pizz/{nm}{octv}_vl{v}_rr{rr}.wav"], f"b-{midi}-{li}-{rr}.mp3", 3.0, 0.6, 1, "64k", thr=-50)
# ---- drums: Virtuosity Drums (jazz kit, sticks): overheads + room mics, kick mic added on the kick
D = f"{SRC}/virtuosity_drums/Samples"
def drum(name, folder, stem, layers, rrs, dur, fade, kick=False, vlfmt="_vl{v}_rr{r}", gain=0):
    man["drums"][name] = {"layers": len(layers), "rr": len(rrs)}
    for li, v in enumerate(layers, 1):
        for ri, r in enumerate(rrs, 1):
            suf = vlfmt.format(v=v, r=r)
            ins = [f"{D}/oh/{folder}/oh_{stem}{suf}.flac", f"{D}/room/{folder}/room_{stem}{suf}.flac"]; mix = [0, -5]
            if kick: ins.append(f"{D}/kickmic/{folder}/kickmic_{stem}{suf}.flac"); mix.append(0)
            enc(ins, f"d-{name}-{li}-{ri}.mp3", dur, fade, 2, "96k", mix=mix, thr=-58, gain=gain)
drum("ride", "ride", "ride_ride", [1, 2, 3], [1, 2, 3], 4.0, 1.5, gain=10)
drum("bell", "ride", "ride_bell", [2], [1, 2], 3.5, 1.5, gain=10)
drum("hh", "hh", "hh_pedal", [1, 2], [1, 2, 3], 1.2, 0.3, gain=10)
drum("hhc", "hh", "hh_closed", [2], [1, 2], 0.8, 0.2, gain=10)
drum("kick", "kick", "kick_snoff", [1, 2], [1, 2], 1.0, 0.3, kick=True, gain=16)
drum("crash", "crash", "crash_crash", [2], [1], 5.0, 2.0, gain=10)
drum("stick", "snare", "snare_crossstick", [4, 7, 10, 13], [1], 0.9, 0.3, vlfmt="_vl{v}", gain=4)
drum("snare", "snare", "snare_center", [3, 5, 7], [1], 1.2, 0.4, vlfmt="_vl{v}", gain=10)
man["credits"] = [
  {"what": "Piano", "name": "Salamander Grand Piano V3", "by": "Alexander Holm", "licence": "CC BY 3.0", "url": "https://archive.org/details/SalamanderGrandPianoV3", "changes": "trimmed, three of sixteen layers, MP3"},
  {"what": "Bass", "name": "Meatbass", "by": "Karoryfer Samples (Drogomir Smolken)", "licence": "CC0 1.0", "url": "https://github.com/sfzinstruments/karoryfer.meatbass"},
  {"what": "Drums", "name": "Virtuosity Drums", "by": "Versilian Studios / Virtuosity Musical Instruments (Austin McMahon, drums)", "licence": "CC0 1.0", "url": "https://github.com/sfzinstruments/virtuosity_drums"}]
json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print(len(os.listdir(OUT)), "files")
