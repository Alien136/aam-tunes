#!/usr/bin/env python3
"""Build the player's v2 sound set from free libraries (see CREDITS in the manifest).
Sources are cloned under /home/claude/sfzinstruments. Output: out/v2/*.mp3 + manifest.json"""
import subprocess, os, json, sys
SRC = "/home/claude/sfzinstruments"; OUT = "out/v2"; os.makedirs(OUT, exist_ok=True)
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
