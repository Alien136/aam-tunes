#!/usr/bin/env node
/* Feature check, run by tools/release.py after the page-by-page check. It proves the things a student relies on still work:

     tuner            names the right note (as the instrument reads it) and how flat it is
     Learn mode       every note turns green for clean playing, for a weak noisy microphone, for tenor low notes and in a shifted key;
                      a wrong note is named; a concert pitch sung against a transposing part is refused
     playback         the blue cloud moves from note to note in time
     contents list    search by number and by name, chapter chips, Enter opens the first match
     PDF download     the newest booklet PDF arrives and really is a PDF
     play bar         Play is in the exact middle and nothing overlaps, at four screen sizes; the phone tempo wheel sets the tempo

   The microphone is a sound file: saxophone-like tones are generated here and fed to the browser as a fake microphone.

   Usage:  AAM_CODE=<master code> node tools/check_features.js [--file player/aam-player.html] [--only tuner|learn|cloud|contents|pdf|bar]
   Needs:  playwright, plus the tone and abcjs packages (tools/node_modules or $AAM_NODE_MODULES). Nothing is fetched from the internet. */
const fs = require("fs"), path = require("path"), os = require("os");
const { chromium, devices } = require("playwright");
const { wire, ROOT, CODE, ONLY } = require("./wire.js");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "aam-ear-")), SR = 48000;
const URL_OF = slug => "https://alexattardmusic.com/play/?t=" + slug + "&c=" + encodeURIComponent(CODE);
const tune = slug => JSON.parse(fs.readFileSync(path.join(ROOT, "tunes", slug + ".json"), "utf8"));
const index = JSON.parse(fs.readFileSync(path.join(ROOT, "index.json"), "utf8"));
const problems = [], ok = [];
const expect = (cond, what) => { (cond ? ok : problems).push(what); if (!cond) console.log("  FAIL: " + what); };

// ---- sound: a reed-like tone (strong overtones, a little vibrato), silence, hiss
function tone(midi, secs, o) {
  o = o || {}; const f = 440 * Math.pow(2, (midi - 69) / 12 + (o.cents || 0) / 1200), n = Math.round(SR * secs), x = new Float32Array(n), H = [1, .9, .7, .5, .35, .25, .15];
  for (let i = 0; i < n; i++) {
    const t = i / SR, ph = 2 * Math.PI * f * t + 0.02 * Math.sin(2 * Math.PI * 5 * t), env = Math.min(1, t / 0.03) * Math.min(1, (secs - t) / 0.04);
    let v = 0; for (let k = 0; k < H.length; k++) v += H[k] * Math.sin((k + 1) * ph);
    x[i] = (o.amp || 0.25) * v / 3 * env;
  }
  return x;
}
const sil = secs => new Float32Array(Math.round(SR * secs));
function wav(name, parts, noise) {
  const n = parts.reduce((a, p) => a + p.length, 0), buf = Buffer.alloc(44 + 2 * n); let o = 44, seed = 7;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647 - 0.5; };
  buf.write("RIFF", 0); buf.writeUInt32LE(36 + 2 * n, 4); buf.write("WAVEfmt ", 8); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(1, 22);
  buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(2 * SR, 28); buf.writeUInt16LE(2, 32); buf.writeUInt16LE(16, 34); buf.write("data", 36); buf.writeUInt32LE(2 * n, 40);
  for (const p of parts) for (let i = 0; i < p.length; i++) { const v = Math.max(-1, Math.min(1, p[i] + (noise == null ? 0.002 : noise) * 3.4 * rnd())); buf.writeInt16LE(Math.round(v * 32767), o); o += 2; }
  const f = path.join(TMP, name + ".wav"); fs.writeFileSync(f, buf); return f;
}
const played = (seq, len, gap, o) => [sil(1.5)].concat(...seq.map(m => [tone(m, len, o), sil(gap)]), [sil(3)]);

// ---- browser helpers
async function withMic(file, opts, fn) {
  const b = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-file-for-fake-audio-capture=" + file] });
  try {
    const ctx = await b.newContext({ viewport: { width: 1280, height: 800 }, permissions: ["microphone"], acceptDownloads: true, ...opts }); await wire(ctx);
    const page = await ctx.newPage(); page.on("pageerror", e => expect(false, "script error: " + e.message));
    await fn(page);
  } finally { await b.close(); }
}
const calibrated = page => page.addInitScript(() => { try { localStorage.setItem("aam-ear", JSON.stringify({ floor: 0.01, off: 0, at: 1 })); } catch (e) {} });
const txt = (page, r) => page.evaluate(r => document.querySelector('[data-r="' + r + '"]').textContent, r);
async function learnRun(page, slug, ms) {                 // start Learn mode and collect what it says until it finishes
  await calibrated(page); await page.goto(URL_OF(slug)); await page.waitForTimeout(1600);
  await page.click('[data-r="learn-btn"]'); const said = [], t0 = Date.now(); let green = 0;
  while (Date.now() - t0 < ms) {
    await page.waitForTimeout(150); const m = await txt(page, "learn-msg"); green = await page.evaluate(() => document.querySelectorAll(".score .lr-ok").length);
    if (said[said.length - 1] !== m) said.push(m);
    if (/every note/.test(m)) break;
  }
  return { said, green, done: /every note/.test(said[said.length - 1] || "") };
}
const want = k => !ONLY || ONLY === k, WRONG = /^(You played \S+\. This note|Right note, wrong octave)/;

(async () => {
  const t0 = Date.now(), HCB = "sax-beginner-alto-hot-cross-buns", hcb = tune(HCB).sections[0].learn.filter(m => m >= 0);

  if (want("tuner")) await withMic(wav("tuner", [sil(2.4), tone(60, 7, { cents: -20 }), sil(1)]), {}, async page => {
    await page.goto(URL_OF(HCB)); await page.waitForTimeout(1500); await page.click('[data-r="tuner-btn"]'); await page.waitForTimeout(6500);
    const note = await txt(page, "t-note"), word = await txt(page, "t-word"), msg = await txt(page, "t-msg"), cents = +(/(\d+) cents/.exec(word) || [0, -1])[1];
    expect(note === "A", "tuner: a piano C reads as A on alto (got " + note + ")");
    expect(/^Flat/.test(word) && cents >= 15 && cents <= 25, "tuner: 20 cents flat is shown as flat by 15 to 25 (got \"" + word + "\")");
    expect(await page.evaluate(() => document.querySelectorAll('[data-r="t-fing"] .fg-k.on').length) === 2, "tuner: shows the fingering of the note being played (written A: two keys down)");
    expect(/ready/.test(msg), "tuner: the microphone check finishes (\"" + msg.slice(0, 40) + "\")");
  });

  if (want("learn")) {
    const withWrong = [sil(1.5)]; hcb.forEach((m, i) => { if (i === 1) withWrong.push(tone(63, 0.9), sil(0.15)); withWrong.push(tone(m, 0.55), sil(0.12)); }); withWrong.push(sil(3));
    await withMic(wav("clean", withWrong), {}, async page => {
      const r = await learnRun(page, HCB, 15000);
      expect(r.done, "Learn, clean playing: the line is finished");
      expect(r.said.some(m => /^You played C\. This note is A\./.test(m)), "Learn: a wrong note is named as the instrument reads it");
      expect(r.said.filter(m => WRONG.test(m)).length === 1, "Learn: no false wrong-note message (" + r.said.filter(m => WRONG.test(m)).join(" / ") + ")");
    });
    const held = [sil(1.5)]; for (let i = 0; i < hcb.length;) { let j = i; while (hcb[j + 1] === hcb[i]) j++; held.push(tone(hcb[i], 0.7 + 1.4 * (j - i), { cents: -25, amp: 0.06 }), sil(0.1)); i = j + 1; } held.push(sil(3));
    await withMic(wav("poor", held, 0.012), {}, async page => {
      const r = await learnRun(page, HCB, 20000);
      expect(r.done, "Learn, weak noisy microphone, 25 cents flat, repeated notes slurred: the line is finished");
      expect(!r.said.some(m => WRONG.test(m)), "Learn, weak microphone: no false wrong-note message");
    });
    const LOW = "sax-beginner-tenor-pinky-push-ups", low = tune(LOW).sections[0].learn.filter(m => m >= 0);
    await withMic(wav("low", played(low, 0.6, 0.12)), {}, async page => { const r = await learnRun(page, LOW, 14000); expect(r.done, "Learn, tenor low notes (down to written low C): the line is finished"); });
    const KEY = "sax-welcome-alto-arpeggios-4ths", kt = tune(KEY), ks = kt.sections[0].rh.slice().sort((a, b) => a[0] - b[0]).map(e => e[1] + (kt.start_key || 0));
    await withMic(wav("key", played(ks, 0.5, 0.12)), {}, async page => {
      const r = await learnRun(page, KEY, 18000);
      expect(r.done && r.green === ks.length, "Learn works on a Welcome Booklet exercise in a shifted key, with no note list in the file (" + r.green + " of " + ks.length + " green)");
    });
    const miss = [sil(1.5), tone(63, 0.9), sil(0.3), tone(64, 0.9), sil(0.3), tone(63, 0.9), sil(2.2)].concat(...hcb.map(m => [tone(m, 0.55), sil(0.12)]), [sil(3)]);
    await withMic(wav("miss", miss), {}, async page => {      // three wrong notes first: the fingering must appear by itself, and Analytics must hear about the session
      await page.addInitScript(() => { window.__ev = []; window.gtag = function (a, n) { if (a === "event") window.__ev.push(n); }; });
      await calibrated(page); await page.goto(URL_OF(HCB)); await page.waitForTimeout(1600); await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(5600);
      const f = await page.evaluate(() => { const b = document.querySelector('[data-r="learn-fing"]'); return { shown: !b.hidden, keys: b.querySelectorAll(".fg-k.on").length, cap: (b.querySelector("small") || {}).textContent }; });
      expect(f.shown && f.keys === 1 && /^B/.test(f.cap || ""), "Learn: after two misses the fingering for the note appears (written B: one key down) (" + JSON.stringify(f) + ")");
      await page.waitForTimeout(12000);
      const ev = await page.evaluate(() => window.__ev);
      expect(["aam_open", "aam_learn_start", "aam_fingering", "aam_learn_done"].every(n => ev.includes(n)), "Analytics hears about Learn mode: start, fingering shown, finished (" + ev.join(", ") + ")");
    });
    await withMic(wav("voice", [sil(1.5), tone(59, 1.6), sil(0.4), tone(62, 1.0), sil(3)]), {}, async page => {
      const r = await learnRun(page, HCB, 6000);
      expect(r.said.some(m => /^You played A♭/.test(m)) && r.green === 1, "Learn: a sung piano B is refused for alto's written B, a piano D is accepted");
    });
  }

  const b = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  const open = async (opts, slug) => { const ctx = await b.newContext({ acceptDownloads: true, ...opts }); await wire(ctx); const page = await ctx.newPage(); page.on("pageerror", e => expect(false, "script error: " + e.message)); await page.goto(URL_OF(slug)); await page.waitForTimeout(1700); return page; };

  if (want("cloud")) {
    const page = await open({ viewport: { width: 1280, height: 800 } }, "sax-beginner-alto-rain-rain-go-away"), seen = [];
    await page.click('[data-r="p-play"]'); const t1 = Date.now();
    while (Date.now() - t1 < 12000) {
      await page.waitForTimeout(110);
      const v = await page.evaluate(() => { const e = document.querySelector(".score .lr-now"), c = e && e.getAttribute("class"); return e ? /mm(\d+)/.exec(c)[1] + "." + /abcjs-n(\d+)/.exec(c)[1] + (document.querySelector(".score .lr-line") ? "" : "!") : ""; });
      if (v && seen[seen.length - 1] !== v) seen.push(v);
    }
    expect(seen.length >= 8 && !seen.some(v => /!/.test(v)), "playback: the blue cloud moves note by note (" + seen.length + " notes followed)");
    expect(seen.join() === seen.slice().sort((x, y) => x.split(".")[0] - y.split(".")[0] || x.split(".")[1] - y.split(".")[1]).join(), "playback: the cloud only moves forward");
    await page.click('[data-r="p-play"]'); await page.waitForTimeout(400);
    expect(await page.evaluate(() => !document.querySelector(".score .lr-line")), "playback: the cloud goes away when the music stops");
    await page.context().close();
  }

  if (want("contents")) {
    const page = await open({ viewport: { width: 1280, height: 800 } }, "sax-beginner-alto-away-in-a-manger");
    await page.click('[data-r="title"]'); await page.waitForTimeout(300);
    const rows = () => page.evaluate(() => [...document.querySelectorAll(".toc-row")].filter(r => !r.hidden).map(r => r.dataset.n + " " + r.querySelector("b").textContent));
    expect(await page.evaluate(() => { const l = document.querySelector('[data-r="toc-list"]'), c = l.querySelector('[aria-current]').getBoundingClientRect(), q = l.getBoundingClientRect(); return c.top >= q.top && c.bottom <= q.bottom; }), "contents: opens at the line being played");
    await page.fill('[data-r="toc-q"]', "45"); let r = await rows(); expect(r.length === 1 && /^45 /.test(r[0]), "contents: a number finds that line (" + r.join(", ") + ")");
    await page.fill('[data-r="toc-q"]', "claire"); r = await rows(); expect(r.length === 1 && /Claire/.test(r[0]), "contents: a name finds the tune, accents ignored");
    await page.fill('[data-r="toc-q"]', "zzz"); expect((await rows()).length === 0 && await page.evaluate(() => !document.querySelector(".toc-none").hidden), "contents: nothing found says so");
    await page.fill('[data-r="toc-q"]', ""); await page.click(".toc-chips button:nth-child(6)"); await page.waitForTimeout(200);
    expect(await page.evaluate(() => { const l = document.querySelector('[data-r="toc-list"]'), q = l.getBoundingClientRect(), r = [...l.querySelectorAll(".toc-row")].find(r => r.getBoundingClientRect().top >= q.top + 20); return r && r.dataset.g === "5"; }), "contents: a chapter chip jumps to that chapter");
    await page.fill('[data-r="toc-q"]', "hot cross"); await page.press('[data-r="toc-q"]', "Enter"); await page.waitForTimeout(1500);
    expect(/Hot Cross Buns/.test(await txt(page, "title")), "contents: Enter opens the first match");
    await page.context().close();
  }

  if (want("pdf")) for (const p of index.pdfs.filter(p => p.file)) {
    const page = await open({ viewport: { width: 1280, height: 800 } }, p.tunes[0]);
    await page.click('[data-r="title"]'); await page.waitForTimeout(300);
    const [dl] = await Promise.all([page.waitForEvent("download", { timeout: 25000 }).catch(() => null), page.click("[data-dl]")]);
    let good = false; if (dl) { const f = path.join(TMP, p.id + ".pdf"); await dl.saveAs(f); const fd = fs.openSync(f, "r"), head = Buffer.alloc(5); fs.readSync(fd, head, 0, 5, 0); fs.closeSync(fd); good = head.toString() === "%PDF-" && fs.statSync(f).size === p.file.size; }
    expect(good, "PDF download: " + p.id + " arrives, opens with the code and is the size the catalog says" + (dl ? "" : " (nothing arrived: " + (await page.evaluate(() => (document.querySelector(".toc-dl-msg") || {}).textContent)) + ")"));
    await page.context().close();
  }

  if (want("bar")) {
    for (const [name, opts, slug] of [["phone", { ...devices["iPhone 13"] }, HCB], ["small phone", { viewport: { width: 360, height: 700 } }, "sax-beginner-alto-rain-rain-go-away"],
                                      ["tablet", { viewport: { width: 820, height: 1100 } }, "sax-welcome-alto-long-tones-down"], ["laptop", { viewport: { width: 1280, height: 800 } }, HCB]]) {
      const page = await open(opts, slug);
      const r = await page.evaluate(() => {
        const bar = document.querySelector('[data-r="pbar"]').getBoundingClientRect(), pl = document.querySelector('[data-r="p-play"]').getBoundingClientRect();
        const kids = [...document.querySelectorAll('[data-r="pbar"] button, [data-r="pbar"] input')].filter(e => e.offsetParent).map(e => e.getBoundingClientRect());
        return { off: Math.round(pl.left + pl.width / 2 - bar.left - bar.width / 2), out: kids.some(k => k.right > bar.right + 1 || k.left < bar.left - 1),
                 lap: kids.some((a, i) => kids.some((q, j) => j > i && a.left < q.right - 1 && q.left < a.right - 1 && a.top < q.bottom - 1 && q.top < a.bottom - 1 && !(a.width > q.width * 3))) };
      });
      expect(Math.abs(r.off) <= 1 && !r.out && !r.lap, "play bar on a " + name + ": Play in the middle, nothing overlapping or cut off");
      if (name === "phone") {
        await page.click('[data-r="p-bpm"]'); await page.waitForTimeout(400);
        const before = +(await txt(page, "p-bpm")); await page.evaluate(() => { document.querySelector('[data-r="tp-list"]').scrollTop -= 44 * 6; }); await page.waitForTimeout(500);
        expect(+(await txt(page, "p-bpm")) === before + 6, "tempo wheel: scrolling toward the top makes it faster");
        const above = await page.evaluate(() => { const on = document.querySelector(".tp-list .on"); return +on.previousElementSibling.textContent > +on.textContent; });
        expect(above, "tempo wheel: faster speeds are above slower ones");
      }
      await page.context().close();
    }
  }
  await b.close();
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log(ok.length + " feature checks passed" + (problems.length ? ", " + problems.length + " FAILED" : "") + " in " + Math.round((Date.now() - t0) / 1000) + "s");
  if (problems.length) process.exit(1); else console.log("All clear.");
})().catch(e => { console.error(e); process.exit(1); });
