#!/usr/bin/env node
/* Feature check, run by tools/release.py after the page-by-page check. It proves the things a student relies on still work:

     tuner            names the right note (as the instrument reads it) and how flat it is
     Learn mode       every note turns green for clean playing, for a weak noisy microphone, for tenor low notes and in a shifted key;
                      a wrong note is named; a concert pitch sung against a transposing part is refused
     playback         the blue cloud moves from note to note in time
     contents list    search by number and by name, chapter chips, Enter opens the first match
     PDF download     the newest booklet PDF arrives and really is a PDF
     play bar         Play is in the exact middle and nothing overlaps, at four screen sizes; the phone tempo wheel sets the tempo;
                      the instrument icon and name sit under the title
     demo             a concert-pitch tune shows an instrument, the reader can change it, and Learn follows it in any octave
     install          the home-screen icon, manifest and full-screen flag are on the page; Practice settings explains how to add it
     level            Learn mode's two levels: the microphone check picks Strict for a steady note and Forgiving for a wavering one; Strict
                      asks for a note in tune, Forgiving lets it pass; the student's own choice is remembered; a piano page has no levels
     piano            Learn mode on a piano page: asks which hand, follows that hand to the end, green notes on its staff
     apply            repeats, key and instrument changes wait for "Apply changes" while the band plays; the page-turn copy has no cloud
     style            the style picker lists the band styles, each one sounds, the choice is remembered, exercises have none

   The microphone is a sound file: saxophone-like tones are generated here and fed to the browser as a fake microphone.

   Usage:  AAM_CODE=<master code> node tools/check_features.js [--file player/aam-player.html] [--only tuner|mic|flute|learn|level|cloud|contents|pdf|bar|style|apply|piano|install|demo|cards]
   Needs:  playwright, plus the tone and abcjs packages (tools/node_modules or $AAM_NODE_MODULES). Nothing is fetched from the internet. */
const fs = require("fs"), path = require("path"), os = require("os");
const { chromium, devices } = require("playwright");
const { wire, ROOT, CODE, ONLY } = require("./wire.js");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "aam-ear-")), SR = 48000;
const URL_OF = slug => "https://alexattardmusic.com/play/?t=" + slug + "&c=" + encodeURIComponent(CODE);
const tune = slug => JSON.parse(fs.readFileSync(path.join(ROOT, "tunes", slug + ".json"), "utf8"));
const index = JSON.parse(fs.readFileSync(path.join(ROOT, "index.json"), "utf8"));
const problems = [], ok = [];
const FILE_OF = path.resolve(ROOT, process.argv.includes("--file") ? process.argv[process.argv.indexOf("--file") + 1] : "player/aam-player.html");
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

  if (want("flute")) await withMic(wav("flute", [sil(2.4), tone(69, 7), sil(1)]), {}, async page => {      // a flute booklet line: the flute's own fingering chart, read at concert pitch
    await page.goto(URL_OF("flute-beginner-hot-cross-buns")); await page.waitForTimeout(1500);
    expect(/Flute/.test(await page.evaluate(() => (document.querySelector(".who") || document.querySelector('[data-r="who"]') || document.body).textContent)), "flute: the page says it is a flute tune");
    await page.click('[data-r="tuner-btn"]'); await page.waitForTimeout(6500);
    const note = await txt(page, "t-note"), fg = await page.evaluate(() => ({ on: document.querySelectorAll('[data-r="t-fing"] .fg-k.on').length, all: document.querySelectorAll('[data-r="t-fing"] .fg-k').length }));
    expect(note === "A", "flute: a piano A reads as A (got " + note + ")");
    expect(fg.all === 12 && fg.on === 4, "flute: the tuner shows the flute fingering for A: thumb, two fingers and the right pinky (" + JSON.stringify(fg) + ")");
  });

  if (want("mic")) {
    await withMic(wav("dead", [sil(9)], 0), {}, async page => {      // a microphone that is on but sends pure silence (an iPad whose sound engine never woke up)
      await page.addInitScript(() => { window.__ev = []; window.gtag = function (a, n) { if (a === "event") window.__ev.push(n); }; });
      await page.goto(URL_OF(HCB)); await page.waitForTimeout(1500); await page.click('[data-r="tuner-btn"]'); await page.waitForTimeout(4500);
      const msg = await txt(page, "t-msg");
      expect(/no sound is reaching the player/.test(msg) && !/Step 2|ready/.test(msg), "microphone check: a silent microphone is reported and never passes as a quiet room (\"" + msg.slice(0, 50) + "\")");
      const ev = await page.evaluate(() => window.__ev);
      expect(ev.includes("aam_mic_silent"), "microphone check: Analytics hears about a silent microphone");
    });
    await withMic(wav("handover", played(hcb, 0.55, 0.12)), {}, async page => {      // the first-time check hands the SAME live microphone to Learn mode: no second start
      await page.addInitScript(() => { const g = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices); window.__gum = 0; navigator.mediaDevices.getUserMedia = c => { window.__gum++; return g(c); }; });
      await page.addInitScript(() => { try { localStorage.setItem("aam-ear", JSON.stringify({ floor: 0.01, off: 0, at: 1 })); } catch (e) {} });
      await page.goto(URL_OF(HCB)); await page.waitForTimeout(1500);
      await page.click('[data-r="tuner-btn"]'); await page.waitForTimeout(900); await page.click('[data-r="t-close"]'); await page.waitForTimeout(150);
      await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(1200);
      const st = await page.evaluate(() => ({ gum: window.__gum, bar: !document.querySelector('[data-r="learn-bar"]').hidden }));
      expect(st.gum === 1 && st.bar, "microphone: going from the tuner straight into Learn mode keeps one live microphone (" + JSON.stringify(st) + ")");
    });
  }

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
    const shares = index.pdfs.some(q => q.id !== p.id && index.pdfs.indexOf(q) < index.pdfs.indexOf(p) && q.tunes.includes(p.tunes[0]));   // a second shelf over another booklet's tunes (the Starter Pack)
    const ctx0 = await b.newContext({ acceptDownloads: true, viewport: { width: 1280, height: 800 } }); await wire(ctx0);
    if (shares) await ctx0.addInitScript(id => { try { if (!localStorage.getItem("aam-library")) localStorage.setItem("aam-library", JSON.stringify({ pdfs: [id] })); } catch (e) {} }, p.id);   // a student who unlocked THIS booklet
    const page = await ctx0.newPage(); page.on("pageerror", e => expect(false, "script error: " + e.message)); await page.goto(URL_OF(p.tunes[0])); await page.waitForTimeout(1700);
    await page.click('[data-r="title"]'); await page.waitForTimeout(300);
    const [dl] = await Promise.all([page.waitForEvent("download", { timeout: 25000 }).catch(() => null), page.click("[data-dl]")]);
    let good = false; if (dl) { const f = path.join(TMP, p.id + ".pdf"); await dl.saveAs(f); const fd = fs.openSync(f, "r"), head = Buffer.alloc(5); fs.readSync(fd, head, 0, 5, 0); fs.closeSync(fd); good = head.toString() === "%PDF-" && fs.statSync(f).size === p.file.size; }
    expect(good, "PDF download: " + p.id + " arrives, opens with the code and is the size the catalog says" + (dl ? "" : " (nothing arrived: " + (await page.evaluate(() => (document.querySelector(".toc-dl-msg") || {}).textContent)) + ")"));
    await page.context().close();
  }

  if (want("pdf")) {                                      // the "download the booklet" link in an email: ...&pdf=1 opens the list with the PDF button first
    const ctx0 = await b.newContext({ acceptDownloads: true, ...devices["iPhone 13"] }); await wire(ctx0);
    const page = await ctx0.newPage(); page.on("pageerror", e => expect(false, "script error: " + e.message));
    await page.goto(URL_OF("sax-beginner-alto-count-then-play") + "&pdf=1"); await page.waitForTimeout(2500);
    const st = await page.evaluate(() => { const toc = document.querySelector('[data-r="toc"]'), box = document.querySelector(".toc-dl"), list = document.querySelector('[data-r="toc-list"]'), btn = document.querySelector("[data-dl]");
      const r = btn && btn.getBoundingClientRect(); return { open: toc && !toc.hidden, hi: !!box && box.classList.contains("hi"), above: !!r && (list.offsetParent === null ? !document.querySelector('[data-r="toc-q"]').offsetParent : r.bottom <= list.getBoundingClientRect().top + 1), seen: !!r && r.top >= 0 && r.bottom <= innerHeight, label: btn && btn.textContent, url: location.search }; });
    expect(st.open && st.hi, "PDF link: &pdf=1 opens the contents with the download button marked");
    expect(st.above && st.seen && /Download the booklet \(PDF\)/.test(st.label || ""), "PDF link: the download card shows the button and no list or search, on a phone screen");
    expect(!/pdf=|c=/.test(st.url), "PDF link: the code and the pdf flag leave the address bar");
    const [dl] = await Promise.all([page.waitForEvent("download", { timeout: 25000 }).catch(() => null), page.click("[data-dl]")]);
    expect(!!dl, "PDF link: the button downloads the booklet");
    await page.waitForTimeout(400);
    expect(await page.evaluate(() => document.querySelector(".toc-next").classList.contains("go")), "PDF link: after the download, \"Now play along\" becomes the main button");
    await page.click(".toc-next"); await page.waitForTimeout(400);
    const t1 = await page.evaluate(() => { const t = document.querySelector("#aam-play .tour"), on = document.querySelector("#aam-play .tour-on"), r = t && t.getBoundingClientRect(); return { toc: document.querySelector('[data-r="toc"]').hidden, tour: !!t, on: on && on.dataset.r, fits: !!r && r.left >= 0 && r.right <= innerWidth && r.top >= 0 && r.bottom <= innerHeight, text: t && t.textContent }; });
    expect(t1.toc && t1.tour && t1.on === "inst-name" && t1.fits && /written for alto saxophone/.test(t1.text) && /Reply to the email/.test(t1.text), "tour: leaving the download card starts the tour at the instrument, naming it, on the screen (" + JSON.stringify(t1).slice(0, 160) + ")");
    const order = ["inst-name"]; for (let k = 0; k < 5; k++) { await page.click('#aam-play .tour [data-tour="next"]'); await page.waitForTimeout(150); order.push(await page.evaluate(() => (document.querySelector("#aam-play .tour-on") || { dataset: {} }).dataset.r)); }
    expect(order.join(" ") === "inst-name learn-btn p-play p-bpm next-line title", "tour: the notes come in practice order: instrument, Learn, Play, tempo, Next, the title (" + order.join(", ") + ")");
    let stepsSeen = 6; for (let k = 0; k < 6 && await page.$("#aam-play .tour"); k++) { await page.click('#aam-play .tour [data-tour="next"]'); await page.waitForTimeout(150); if (await page.$("#aam-play .tour")) stepsSeen++; }
    expect(stepsSeen >= 6 && !(await page.$("#aam-play .tour")) && !(await page.$("#aam-play .tour-on")), "tour: " + stepsSeen + " steps, then it is gone and nothing stays marked");
    const nx = await page.evaluate(() => { const b = document.querySelector('#aam-play [data-r="next-line"]'), r = b.getBoundingClientRect(); return { seen: !b.hidden && r.width > 0 && r.right <= innerWidth && r.top >= 0, t: document.querySelector('#aam-play [data-r="title"]').textContent }; });
    await page.click('#aam-play [data-r="next-line"]'); await page.waitForTimeout(2500);
    const t2 = await page.textContent('#aam-play [data-r="title"]');
    expect(nx.seen && /^1 /.test(nx.t) && /^2 /.test(t2), "next: the Next button beside Learn and Tuner opens the next line of the booklet (" + nx.t.trim() + " -> " + t2.trim() + ")");
    await page.click('[data-r="title"]'); await page.waitForTimeout(300);
    expect(await page.evaluate(() => !document.querySelector(".toc-dl").classList.contains("hi") && !document.querySelector(".toc-card").classList.contains("pdf-only") && !!document.querySelector('[data-r="toc-list"]').offsetParent), "PDF link: opening the list from the title is the ordinary list");
    await page.click('[data-r="toc-close"]'); await page.reload(); await page.waitForTimeout(2500);
    expect(!(await page.$("#aam-play .tour")), "tour: it shows once for a device, and never by itself on a teacher's device");
    await page.goto(URL_OF("sax-beginner-alto-count-then-play") + "&tour=1"); await page.waitForTimeout(3600);
    expect(!!(await page.$("#aam-play .tour")), "tour: &tour=1 shows it again");
    await page.click('#aam-play .tour [data-tour="skip"]'); expect(!(await page.$("#aam-play .tour")), "tour: Skip closes it");
    await page.click('[data-r="p-play"]'); await page.waitForTimeout(600); await page.click('[data-r="p-play"]');
    if (process.env.AAM_STARTER) {                           // a real newcomer: a Starter Pack code and nothing else (the code is given on the command line, never stored)
      const c2 = await b.newContext({ ...devices["iPhone 13"] }); await wire(c2); const p2 = await c2.newPage();
      await p2.goto("https://alexattardmusic.com/play/?t=sax-beginner-alto-count-then-play&c=" + encodeURIComponent(process.env.AAM_STARTER)); await p2.waitForTimeout(4200);
      expect(!!(await p2.$("#aam-play .tour")), "tour: a newcomer with a Starter Pack code sees it without asking"); await c2.close();
    }
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
      const who = await page.evaluate(() => { const e = document.querySelector('[data-r="subtitle"]'), i = e.querySelector(".inst-ic svg"), h = document.querySelector('[data-r="title"]').getBoundingClientRect(), b = e.getBoundingClientRect();
        return { kind: e.getAttribute("data-inst"), name: e.textContent.trim(), icon: !!i && i.getBoundingClientRect().width >= 16, inside: b.right <= innerWidth + 1 && b.top >= h.bottom - 4 }; });
      expect(who.kind === "sax" && who.name === "Alto saxophone" && who.icon && who.inside, "under the title on a " + name + ": the saxophone icon and \"Alto saxophone\", nothing else, not cut off");
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
  const HAS_STYLES = fs.readFileSync(path.resolve(ROOT, process.argv.includes("--file") ? process.argv[process.argv.indexOf("--file") + 1] : "player/aam-player.html"), "utf8").includes('data-r="stdlg"');
  if (want("style") && !HAS_STYLES) console.log("  (style checks skipped: this copy of the player has no band styles)");
  if (want("style") && HAS_STYLES) {                        // band styles: the picker, each style sounds, the choice is remembered, exercises have none
    const TEN = fs.readdirSync(path.join(ROOT, "tunes")).map(f => f.replace(/\.json$/, "")).find(sl => { const t = tune(sl); return t.instrument === "tenor" && (!t.style || t.style === "swing"); });
    const ctx = await b.newContext({ ...devices["iPhone 13"] }); await wire(ctx); const page = await ctx.newPage(); page.on("pageerror", e => expect(false, "script error: " + e.message));
    await page.addInitScript(() => { window.__starts = 0; const o = AudioBufferSourceNode.prototype.start; AudioBufferSourceNode.prototype.start = function () { window.__starts++; return o.apply(this, arguments); }; });
    await page.goto(URL_OF(TEN)); await page.waitForTimeout(2200);
    const ids = await (async () => { await page.click('[data-r="style-btn"]'); const x = await page.$$eval('[data-r="st-list"] button', bs => bs.map(e => e.dataset.id)); await page.click('[data-r="st-close"]'); return x; })();
    expect(ids.length >= 5 && ids[0] === "swing", "style picker: lists the styles, Medium Swing first (" + ids.length + ")");
    await page.click('[data-r="p-play"]'); await page.waitForTimeout(7000);
    for (const id of ids) {
      await page.click('[data-r="style-btn"]'); await page.click('[data-r="st-list"] button[data-id="' + id + '"]'); await page.click('[data-r="st-close"]');
      const a0 = await page.evaluate(() => window.__starts); await page.waitForTimeout(3500); const n = await page.evaluate(() => window.__starts) - a0;
      const fit = await page.evaluate(() => { const p = document.querySelector('[data-r="style-btn"]').getBoundingClientRect(), all = [...document.querySelectorAll("#aam-play .head button, #aam-play .head a")].filter(e => e.offsetParent && !e.closest('[data-r="subtitle"]')).map(e => e.getBoundingClientRect());
        return p.right <= innerWidth && !all.some(r => p.right > r.left + 1 && p.left < r.right - 1 && p.bottom > r.top + 1 && p.top < r.bottom - 1); });
      expect(n >= 12, "style " + id + ": the band plays (" + n + " sounds in 3.5 s)");
      expect(fit, "style " + id + ": its name fits beside the instrument on a phone");
    }
    await page.click('[data-r="p-play"]');
    await page.click('[data-r="style-btn"]'); await page.click('[data-r="st-list"] button[data-id="bossa"]'); await page.click('[data-r="st-close"]');
    await page.reload(); await page.waitForTimeout(2200);
    expect((await page.textContent('[data-r="style-btn"]')) === "Bossa Nova", "style: the choice is remembered for the tune");
    await page.goto(URL_OF(HCB)); await page.waitForTimeout(1800);
    expect(!(await page.$('[data-r="style-btn"]')), "style: an exercise with a click has no style picker");
    expect(!ids.some(id => /^waltz/.test(id)), "style: a tune in 4/4 is not offered a waltz");
    const WALTZ = "going-home-alto-arpeggios", html = await page.content();
    const TESTCOPY = /var PLAYER_VERSION = "test copy"/.test(html), isBeta = id => new RegExp("\\b" + id + ":\\s*\\{ name: \"[^\"]+\", beta: true").test(html);
    if (html.includes('soul:')) {                             // "band_new": a tune moves to a new style only where that style is released (beta styles: the test copy)
      await page.goto(URL_OF("cold-duck-time-alto")); await page.waitForTimeout(2200);
      const want = TESTCOPY || !isBeta("soul") ? "Soul Jazz" : "Bossa Nova", got = await page.textContent('[data-r="style-btn"]');
      expect(got === want, "soul style: Cold Duck Time opens with " + want + " (" + got + ")");
    }
    if (html.includes('waltzb:') && !TESTCOPY && isBeta("waltzb")) {
      await page.goto(URL_OF(WALTZ)); await page.waitForTimeout(2200);
      expect(!(await page.$('[data-r="style-btn"]')), "3/4 band: students keep the click on Going Home until the waltz styles are released");
    }
    if (html.includes('waltzb:') && (TESTCOPY || !isBeta("waltzb"))) {      // the band in 3/4: a tune that older players show with a click
      await page.goto(URL_OF(WALTZ)); await page.waitForTimeout(2200);
      expect(/Ballad in 3/.test(await page.textContent('[data-r="style-btn"]')), "3/4 band: Going Home opens with the Ballad in 3 style");
      await page.click('[data-r="style-btn"]'); const w = await page.$$eval('[data-r="st-list"] button', bs => bs.map(e => e.dataset.id)); await page.click('[data-r="st-close"]');
      expect(w.length >= 1 && w.every(id => /^waltz/.test(id)), "3/4 band: a tune in 3/4 is offered only the styles in three (" + w.join(", ") + ")");
      await page.click('[data-r="p-play"]'); await page.waitForTimeout(6000);
      for (const id of w) {
        await page.click('[data-r="style-btn"]'); await page.click('[data-r="st-list"] button[data-id="' + id + '"]'); await page.click('[data-r="st-close"]');
        const a0 = await page.evaluate(() => window.__starts); await page.waitForTimeout(3500); const n = await page.evaluate(() => window.__starts) - a0;
        expect(n >= 8, "3/4 band: style " + id + " plays (" + n + " sounds in 3.5 s)");
      }
      await page.click('[data-r="p-play"]');
    }
    await ctx.close();
  }
  if (want("cards") && fs.existsSync(path.join(ROOT, "theory", "cards.html")) && /var PLAYER_VERSION = "test copy"/.test(fs.readFileSync(FILE_OF, "utf8"))) {
    // theory flash cards: the play page steps aside for them; every kind of card draws, answers are counted, a round ends with a score
    const ctx = await b.newContext({ ...devices["iPhone 13"] }); await wire(ctx); const page = await ctx.newPage();
    page.on("pageerror", e => { if (!/not a fault/.test(e.message)) expect(false, "flash cards: script error: " + e.message); });
    await page.goto("https://alexattardmusic.com/theory/?beta"); await page.waitForTimeout(2500);
    expect(!!(await page.$("#aam-cards")) && !(await page.$("#aam-play")), "theory page: /theory/?beta opens the test copy of the cards, with no code screen and no player");
    const fits = await page.evaluate(() => { const q = document.querySelector('#aam-cards [data-c="start"]').getBoundingClientRect(); return q.bottom <= innerHeight && q.top > 0; });
    expect(fits, "flash cards: the whole setup, Start button included, fits a phone screen without scrolling");
    const pick = (g, id) => page.click('#aam-cards [data-c="' + g + '"] button[data-id="' + id + '"]');
    const NEED = { 1: 2, 2: 3, 3: 4, 4: 4 };
    for (const [inst, mode, clef, level] of [["piano", "name", "both", 1], ["piano", "key", "bass", 2], ["piano", "staff", "treble", 3], ["alto", "fing", "", 4], ["tenor", "staff", "", 2], ["flute", "fing", "", 3], ["flute", "name", "", 4], ["other", "name", "bass", 4]]) {
      await pick("inst", inst); await pick("mode", mode); if (clef) await pick("clef", clef); await pick("level", level); await pick("round", "calm"); await page.click('#aam-cards [data-c="start"]'); await page.waitForTimeout(250);
      let ok = true, why = "";
      for (let k = 0; k < 6 && ok; k++) {
        const st = await page.evaluate(() => { const r = document.getElementById("aam-cards"), o = [...r.querySelectorAll(".opt")]; return { n: o.length, pic: !!r.querySelector('[data-c="show"] svg'), faces: o.every(e => e.querySelector("svg") || e.textContent.trim()), fit: o.every(e => { const q = e.getBoundingClientRect(); return q.left >= 0 && q.right <= innerWidth + 1; }), same: new Set(o.map(e => e.innerHTML)).size }; });
        if (st.n !== NEED[level] || !st.pic || !st.faces || !st.fit || st.same !== st.n) { ok = false; why = JSON.stringify(st); }
        await page.click("#aam-cards .opt >> nth=" + (k % st.n)); await page.waitForTimeout(1250);
      }
      expect(ok, "flash cards " + inst + " / " + mode + " / level " + level + ": a picture, " + NEED[level] + " different answers, all on the screen " + why);
      await page.click('#aam-cards [data-c="quit"]'); await page.click('#aam-cards [data-c="change"]');
    }
    await page.goto("https://alexattardmusic.com/theory/?beta"); await page.waitForTimeout(2500);
    if (!fs.existsSync(path.join(ROOT, "release", "cards.html"))) {
      const p2 = await ctx.newPage(); await p2.goto("https://alexattardmusic.com/theory/"); await p2.waitForTimeout(1500);
      expect(/coming soon/i.test(await p2.textContent("body")) && !(await p2.$("#aam-cards")), "theory page: before a release, visitors see \"coming soon\" and not the test copy"); await p2.close();
    }
    await pick("inst", "piano"); await pick("mode", "name"); await pick("clef", "treble"); await pick("level", 1); await pick("round", "calm"); await page.click('#aam-cards [data-c="start"]');
    let right = 0;
    for (let k = 0; k < 20; k++) {                            // a whole round, answered by reading the note off the staff the way a student would
      await page.waitForFunction(() => !document.querySelector("#aam-cards .opt.right") && document.querySelectorAll("#aam-cards .opt").length === 2);
      await page.click("#aam-cards .opt >> nth=" + (k < 15 ? 0 : 1)); const hit = await page.evaluate(() => /Yes/.test(document.querySelector('#aam-cards [data-c="said"]').textContent)); if (hit) right++;
    }
    await page.waitForSelector('#aam-cards [data-c="done"]:not([hidden])', { timeout: 4000 }).catch(() => {});
    const end = await page.evaluate(() => ({ shown: !document.querySelector('#aam-cards [data-c="done"]').hidden, score: +document.querySelector('#aam-cards [data-c="score"]').textContent, mem: JSON.parse(localStorage.getItem("aam-cards") || "{}") }));
    expect(end.shown && end.score === right, "flash cards: 20 cards end the round and the score is the number answered right (" + end.score + " shown, " + right + " counted)");
    expect(end.mem.best && end.mem.best["piano|name|treble|1|calm"] >= right && (right === 20 || Object.keys(end.mem.miss || {}).length > 0), "flash cards: the best score and the missed notes are remembered on the device");
    await ctx.close();
  }
  const HAS_LEVELS = fs.readFileSync(FILE_OF, "utf8").includes('data-r="learn-lvl"');
  if (want("level") && !HAS_LEVELS) console.log("  (level checks skipped: this copy of the player has no Learn mode levels)");
  if (want("level") && HAS_LEVELS) {                        // Learn mode's two levels
    const waver = (midi, secs, wide) => { const n = Math.round(SR * secs), x = new Float32Array(n), H = [1, .9, .7, .5, .35, .25, .15]; let ph = 0;      // a beginner's long note: the pitch drifts up and down
      for (let i = 0; i < n; i++) { const t = i / SR, f = 440 * Math.pow(2, (midi - 69) / 12 + wide * Math.sin(2 * Math.PI * 1.5 * t) / 1200); ph += 2 * Math.PI * f / SR; let v = 0; for (let k = 0; k < H.length; k++) v += H[k] * Math.sin((k + 1) * ph); x[i] = 0.25 * v / 3 * Math.min(1, t / 0.03) * Math.min(1, (secs - t) / 0.04); } return x; };
    for (const [name, sound, lvl] of [["steady", tone(60, 7), "strict"], ["wavering", waver(60, 7, 28), "easy"]])
      await withMic(wav("lvl-" + name, [sil(2.4), sound, sil(1)]), {}, async page => {      // the first-time microphone check chooses the level
        await page.goto(URL_OF(HCB)); await page.waitForTimeout(1500); await page.click('[data-r="tuner-btn"]'); await page.waitForTimeout(6500);
        const c = await page.evaluate(() => JSON.parse(localStorage.getItem("aam-ear") || "{}")), msg = await txt(page, "t-msg");
        expect(/ready/.test(msg) && c.lvl === lvl, "levels: a " + name + " long note in the microphone check sets Learn mode to " + (lvl === "strict" ? "Strict" : "Forgiving") + " (got " + c.lvl + ", spread " + c.spread + " cents)");
        if (lvl === "strict") expect(/Strict/.test(msg), "levels: the check tells the student that Learn mode starts on Strict");
      });
    const cal = lvl => page => page.addInitScript(lvl => { try { if (!localStorage.getItem("aam-ear")) localStorage.setItem("aam-ear", JSON.stringify({ floor: 0.01, off: 0, at: 1, lvl: lvl })); } catch (e) {} }, lvl);
    const flat = [sil(1.5)]; hcb.forEach((m, i) => { if (i === 1) flat.push(tone(m, 1.6, { cents: -40 }), sil(0.15)); flat.push(tone(m, 0.7), sil(0.12)); }); flat.push(sil(3));     // the second note is played 40 cents flat first, then in tune
    const run = async (page, ms) => { const said = [], t0 = Date.now(); while (Date.now() - t0 < ms) { await page.waitForTimeout(150); const m = await txt(page, "learn-msg"); if (said[said.length - 1] !== m) said.push(m); if (/every note/.test(m)) break; } return said; };
    await withMic(wav("lvl-flat", flat), {}, async page => {
      await cal("strict")(page); await page.goto(URL_OF(HCB)); await page.waitForTimeout(1600); await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(250);
      expect((await txt(page, "learn-lvl")) === "Level: Strict" && await page.evaluate(() => !document.querySelector('[data-r="learn-lvl"]').hidden), "levels: the Learn bar shows the level the check chose (Strict)");
      const said = await run(page, 20000);
      expect(said.some(m => /^Right note, but flat/.test(m)), "levels, Strict: a note 40 cents flat is not accepted, and the player says it is flat (" + said.slice(0, 4).join(" / ").slice(0, 120) + ")");
      expect(!said.some(m => WRONG.test(m)), "levels, Strict: an out-of-tune note is never called a wrong note");
      expect(/every note/.test(said[said.length - 1] || ""), "levels, Strict: once the note is in tune the line carries on to the end");
      expect(await page.evaluate(() => document.querySelector('[data-r="learn-lvl"]').hidden), "levels: the level button goes away when the line is finished");
    });
    await withMic(wav("lvl-flat2", flat), {}, async page => {
      await cal("easy")(page); await page.goto(URL_OF(HCB)); await page.waitForTimeout(1600); await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(250);
      expect((await txt(page, "learn-lvl")) === "Level: Forgiving", "levels: after a wavering check the Learn bar shows Forgiving");
      const said = await run(page, 20000);
      expect(!said.some(m => /^Right note, but/.test(m)) && /every note/.test(said[said.length - 1] || ""), "levels, Forgiving: the same playing, 40 cents flat, is accepted without a remark (as before levels existed)");
    });
    await withMic(wav("lvl-pick", [sil(20)]), { ...devices["iPhone 13"] }, async page => {      // the student's own choice, on a phone
      await page.addInitScript(() => { window.__ev = []; window.gtag = function (a, n, p) { if (a === "event") window.__ev.push(n + ":" + (p && p.how || "")); }; });
      await cal("strict")(page); await page.goto(URL_OF(HCB)); await page.waitForTimeout(1800); await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(400);
      await page.click('[data-r="learn-lvl"]'); await page.waitForTimeout(200);
      const a = await page.evaluate(() => { const bar = document.querySelector('[data-r="learn-bar"]'), r = bar.getBoundingClientRect(), bs = [].slice.call(bar.querySelectorAll("button")).filter(b => !b.hidden).map(b => b.getBoundingClientRect());
        return { label: document.querySelector('[data-r="learn-lvl"]').textContent, msg: document.querySelector('[data-r="learn-msg"]').textContent, kept: localStorage.getItem("aam-lvl"), fits: bs.every(b => b.left >= r.left - 0.5 && b.right <= r.right + 0.5 && b.width > 40) && r.right <= innerWidth + 0.5, ev: window.__ev }; });
      expect(a.label === "Level: Forgiving" && a.kept === "easy", "levels: tapping the level button changes Strict to Forgiving and keeps the choice on the device (" + a.label + ", " + a.kept + ")");
      expect(/^Forgiving: /.test(a.msg) && /Next: \S+\./.test(a.msg), "levels: the change is explained in a sentence and the next note is still named (\"" + a.msg.slice(0, 60) + "\")");
      expect(a.fits, "levels: every button of the Learn bar fits inside the bar on a phone");
      expect(a.ev.includes("aam_learn_level:easy"), "levels: Analytics hears which level a student chose");
      await page.reload(); await page.waitForTimeout(1800); await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(400);
      expect((await txt(page, "learn-lvl")) === "Level: Forgiving", "levels: the student's choice wins over the microphone check the next time");
    });
    await withMic(wav("lvl-piano", [sil(12)]), {}, async page => {      // a piano cannot play out of tune and its notes die away: no levels there
      await page.addInitScript(() => { try { localStorage.setItem("aam-lvl", "strict"); } catch (e) {} });
      await cal("strict")(page); await page.goto(URL_OF("gr1-mozart-theme-k265")); await page.waitForTimeout(1800); await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(300);
      await page.click('[data-r="h-hands"] button[data-hand="rh"]'); await page.waitForTimeout(500);
      const p = await page.evaluate(() => ({ bar: !document.querySelector('[data-r="learn-bar"]').hidden, lvl: document.querySelector('[data-r="learn-lvl"]').hidden }));
      expect(p.bar && p.lvl, "levels: a piano page has no level button (" + JSON.stringify(p) + ")");
    });
  }
  if (want("piano")) {                                      // Learn mode on a piano page: one hand at a time, chosen in a small dialog
    const handSeq = (slug, h) => { const at = {}; tune(slug).sections[0][h].forEach(e => { const k = Math.round(e[0] * 48); at[k] = Math.min(at[k] == null ? 999 : at[k], e[1]); }); return Object.keys(at).map(Number).sort((x, y) => x - y).map(k => at[k]); };
    for (const [slug, h, name] of [["gr1-beethoven-ode-to-joy", "lh", "left"], ["gr1-mozart-theme-k265", "rh", "right"]]) {
      const seq = handSeq(slug, h);
      await withMic(wav("piano-" + h, played(seq, 0.5, 0.16)), { ...devices["iPhone 13"] }, async page => {
        await calibrated(page); await page.goto(URL_OF(slug)); await page.waitForTimeout(1800);
        await page.click('[data-r="learn-btn"]'); await page.waitForTimeout(300);
        const asked = await page.evaluate(() => !document.querySelector('[data-r="hdlg"]').hidden);
        expect(asked, "piano Learn: it asks which hand (" + slug + ")");
        await page.click('[data-r="h-hands"] button[data-hand="' + h + '"]');
        const said = [], t0 = Date.now(); while (Date.now() - t0 < seq.length * 800 + 9000) { await page.waitForTimeout(200); const m = await txt(page, "learn-msg"); if (said[said.length - 1] !== m) said.push(m); if (/every note/.test(m)) break; }
        const where = await page.evaluate(h => { const l = document.querySelector(".score .lr-ok"); return l ? (/abcjs-v1/.test(l.getAttribute("class")) ? "lh" : "rh") : "none"; }, h);
        expect(new RegExp("^" + (h === "lh" ? "Left" : "Right") + " hand\\.").test(said[0] || ""), "piano Learn: it says which hand it is listening to (" + (said[0] || "").slice(0, 40) + ")");
        expect(/every note/.test(said[said.length - 1] || ""), "piano Learn, " + name + " hand: every note of the hand is followed to the end (" + seq.length + " notes; last: " + (said[said.length - 1] || "").slice(0, 50) + ")");
        expect(where === h, "piano Learn, " + name + " hand: the green notes are on that hand's staff");
        expect(said.filter(m => WRONG.test(m)).length === 0, "piano Learn, " + name + " hand: no false wrong-note message (" + said.filter(m => WRONG.test(m)).slice(0, 2).join(" / ") + ")");
      });
    }
    const page = await open({ ...devices["iPhone 13"] }, "winter-wonderland-piano");
    await page.addInitScript(() => { try { localStorage.setItem("aam-ear", JSON.stringify({ floor: 0.01, off: 0, at: 1 })); } catch (e) {} });
    await page.click('[data-r="views"] button:nth-child(3)'); await page.waitForTimeout(600);
    const lead = await page.evaluate(() => { const b = document.querySelector('[data-r="learn-btn"]'); return !b.hidden; });
    expect(lead, "piano lead sheet: Learn is offered for the right hand's line (the left hand is all chords)");
    await page.context().close();
  }
  if (want("demo")) {                                       // a concert-pitch tune (the free demo tunes): pick your instrument, and Learn follows it in any octave
    const DJ = "demo-jingle-bells", mel = tune(DJ).sections.find(x => x.id === "melody"), at = {};
    mel.rh.forEach(e => { at[Math.round(e[0] * 48)] = e[1]; }); const seq = Object.keys(at).map(Number).sort((x, y) => x - y).map(k => at[k] - 12);   // an alto plays it an octave under the tune file
    await withMic(wav("demo-alto", played(seq, 0.5, 0.16)), { ...devices["iPhone 13"] }, async page => {
      await calibrated(page); await page.goto(URL_OF(DJ)); await page.waitForTimeout(1800);
      const before = await page.evaluate(() => ({ name: document.querySelector('[data-r="inst-name"]').textContent, kind: document.querySelector('[data-r="subtitle"]').getAttribute("data-inst") }));
      expect(before.name === "Piano" && before.kind === "piano", "demo tune: it opens with an instrument under the title (" + before.name + ")");
      await page.click('[data-r="inst-btn"]'); await page.waitForTimeout(250);
      const n = await page.evaluate(() => document.querySelectorAll('[data-r="p-insts"] button').length);
      await page.click('[data-r="p-insts"] button[data-as="alto"]'); await page.waitForTimeout(900);
      const after = await page.evaluate(() => ({ name: document.querySelector('[data-r="inst-name"]').textContent, key: document.querySelector('[data-r="p-key-k"]').textContent, learn: !document.querySelector('[data-r="learn-btn"]').hidden,
        fit: (() => { const p = document.querySelector('[data-r="inst-btn"]').getBoundingClientRect(), l = document.querySelector('[data-r="lib-btn"]').getBoundingClientRect(); return p.right <= l.left || p.top >= l.bottom; })() }));
      expect(n === 6 && after.name === "Alto saxophone" && after.key === "D" && after.fit, "demo tune: choosing alto saxophone rewrites the page for it (key " + after.key + ") and the name fits");
      expect(after.learn, "demo tune as alto: Learn is still offered");
      await page.click('[data-r="learn-btn"]'); const said = [], t0 = Date.now(); while (Date.now() - t0 < seq.length * 800 + 9000) { await page.waitForTimeout(200); const m = await txt(page, "learn-msg"); if (said[said.length - 1] !== m) said.push(m); if (/every note/.test(m)) break; }
      expect(/F♯|F#/.test(said[0] || ""), "demo tune as alto: Learn names the first note as the alto reads it (" + (said[0] || "").slice(0, 60) + ")");
      expect(/every note/.test(said[said.length - 1] || "") && said.filter(m => WRONG.test(m)).length === 0, "demo tune as alto: the melody played an octave lower is followed to the end, with no wrong-note message (" + (said[said.length - 1] || "").slice(0, 40) + ")");
      await page.reload(); await page.waitForTimeout(1800);
      expect((await txt(page, "inst-name")) === "Alto saxophone", "demo tune: the instrument is remembered");
    });
  }
  if (want("demo")) {                                       // the public demo card on the lessons page: the same instrument button, in its bar, and Analytics hears the choice
    const ctxD = await b.newContext({ ...devices["iPhone 13"] }); await wire(ctxD);
    await ctxD.addInitScript(() => { window.__ev = []; window.gtag = function (a, n, p) { if (a === "event") window.__ev.push(n + (p && p.instrument ? ":" + p.instrument + ":" + (p.where || "") : "")); }; });
    const page = await ctxD.newPage(); page.on("pageerror", e => expect(false, "script error: " + e.message));
    await page.goto("https://alexattardmusic.com/lessons/?player=test"); await page.click("#aam-demo .poster"); await page.waitForSelector("#aam-demo iframe"); await page.waitForTimeout(3500);
    const f = page.frames().find(x => x !== page.mainFrame());
    const inBar = await f.evaluate(() => { const p = document.querySelector('[data-r="inst-btn"]'); return !!p && !!p.closest(".demo-bar") && p.getBoundingClientRect().width > 40 && !document.querySelector(".demo-inst select") && !document.querySelector('[data-r="gate"]:not([hidden])'); });
    expect(inBar, "demo card: the instrument button sits in the demo's bar, and the tune opened");
    await f.click('[data-r="inst-btn"]'); await page.waitForTimeout(300); await f.click('[data-r="p-insts"] button[data-as="clarinet"]'); await page.waitForTimeout(900);
    const got = await f.evaluate(() => ({ name: document.querySelector('[data-r="inst-name"]').textContent, key: document.querySelector('[data-r="p-key-k"]').textContent, ev: window.__ev }));
    expect(got.name === "Clarinet" && got.key === "G", "demo card: choosing clarinet rewrites the page for a B♭ instrument (key " + got.key + ")");
    expect(got.ev.includes("aam_instrument:clarinet:demo"), "demo card: Analytics hears which instrument was chosen, and that it was in the demo (" + got.ev.filter(x => /instrument/.test(x)).join(", ") + ")");
    await f.click(".demo-chips button:nth-child(2)"); await page.waitForTimeout(2500);
    const f2 = page.frames().find(x => x !== page.mainFrame());
    expect((await f2.textContent('[data-r="inst-name"]')) === "Clarinet", "demo card: the next tune opens written for the same instrument");
    await ctxD.close();
  }
  if (want("cloud")) {                                      // a piano page: one cloud per hand, and no wash on the bar; a one-line page: one cloud
    const page = await open({ ...devices["iPhone 13"] }, "winter-wonderland-piano");
    const count = () => page.evaluate(() => ({ rh: document.querySelectorAll(".score .lr-line:not(.lr-line2)").length, lh: document.querySelectorAll(".score .lr-line2").length,
      wash: [...document.querySelectorAll(".score .hl.is-now")].some(e => { const c = getComputedStyle(e); return c.fill !== "rgba(0, 0, 0, 0)" && c.fill !== "transparent" && c.fill !== "none"; }) }));
    await page.click('[data-r="views"] button:nth-child(3)'); await page.waitForTimeout(500); await page.click('[data-r="p-play"]'); await page.waitForTimeout(8500);
    let c = await count(); expect(c.rh === 1 && c.lh === 1, "piano page: a cloud on the right hand's note and one on the left hand's (" + c.rh + ", " + c.lh + ")");
    expect(!c.wash, "playback: the bar itself is not washed when a note carries the cloud");
    await page.click('[data-r="p-play"]'); await page.waitForTimeout(400);
    await page.click('[data-r="views"] button:nth-child(2)'); await page.waitForTimeout(500); await page.click('[data-r="p-play"]'); await page.waitForTimeout(8500);
    c = await count(); expect(c.rh === 0 && c.lh === 1, "piano page with an empty right hand: the left hand still has its cloud");
    await page.context().close();
    const one = await open({ ...devices["iPhone 13"] }, "sax-beginner-alto-cuckoo-duet");
    await one.click('[data-r="p-play"]'); await one.waitForTimeout(9000);
    const d = await one.evaluate(() => document.querySelectorAll(".score .lr-line").length); expect(d === 1, "a saxophone duet: one cloud, on the top part only (" + d + ")");
    await one.context().close();
  }
  if (want("apply")) {                                      // changes made while the band plays wait for "Apply changes"; the page-turn copy carries no cloud
    const page = await open({ ...devices["iPhone 13"] }, "f-blues-piano");
    const pill = () => page.evaluate(() => { const b = document.querySelector('[data-r="apply"]'); return b.hidden ? "" : b.textContent; });
    expect((await page.evaluate(() => document.querySelector('[data-r="p-reps"]').getAttribute("aria-label"))) === "Number of repeats", "repeats: the button is called \"Number of repeats\"");
    await page.click('[data-r="p-reps"]'); await page.click('[data-r="p-reps-pop"] button[data-n="3"]'); await page.waitForTimeout(200);
    expect((await pill()) === "" && (await txt(page, "p-reps")) === "3×", "stopped: a new number of repeats applies at once, with no prompt");
    await page.click('[data-r="views"] button:nth-child(3)'); await page.waitForTimeout(500);
    await page.click('[data-r="p-play"]'); await page.waitForTimeout(6000);
    await page.click('[data-r="p-reps"]'); await page.click('[data-r="p-reps-pop"] button[data-n="5"]'); await page.waitForTimeout(300);
    expect((await pill()) === "Apply changes" && /\/3$/.test(await txt(page, "p-reps")), "playing: a new number of repeats waits, and \"Apply changes\" appears (" + (await txt(page, "p-reps")) + ")");
    const fit = await page.evaluate(() => { const a = document.querySelector('[data-r="apply"]').getBoundingClientRect(), pl = document.querySelector('[data-r="p-play"]').getBoundingClientRect(); return Math.abs(a.left + a.width / 2 - pl.left - pl.width / 2) <= 2 && a.bottom <= pl.top && a.left >= 0 && a.right <= innerWidth; });
    expect(fit, "\"Apply changes\" sits just above the Play button");
    const keyBefore = await txt(page, "p-key-k");
    await page.click('[data-r="p-key"]'); await page.click('[data-r="k-keys"] button:not([aria-pressed="true"])'); await page.click('[data-r="k-close"]'); await page.waitForTimeout(300);
    expect((await pill()) === "Apply 2 changes" && (await txt(page, "p-key-k")) === keyBefore, "playing: a key change waits too, and the page does not move");
    await page.waitForTimeout(9000);                          // far enough down the page for the page-turn copy to appear
    const over = await page.evaluate(() => { const o = document.querySelector(".score-over"); return o ? [o.querySelectorAll(".lr-line").length, o.querySelectorAll(".lr-now").length, o.querySelectorAll("#lr-soft").length, document.querySelectorAll(".score .lr-line").length].join() : "none"; });
    expect(over === "none" || /^0,0,0,/.test(over), "page turn: the copy of the next page carries no cloud, no blue note and no second filter (" + over + ")");
    await page.click('[data-r="apply"]'); await page.waitForTimeout(700);
    expect((await pill()) === "" && /\/5$/.test(await txt(page, "p-reps")) && (await txt(page, "p-key-k")) !== keyBefore, "Apply changes: the repeats and the key change together, and the prompt goes away");
    await page.click('[data-r="p-reps"]'); await page.click('[data-r="p-reps-pop"] button[data-n="2"]'); await page.waitForTimeout(200);
    await page.click('[data-r="p-play"]'); await page.waitForTimeout(500);
    expect((await pill()) === "" && (await txt(page, "p-reps")) === "2×", "stopping applies what was waiting");
    await page.context().close();
  }
  if (want("install")) {                                    // install on the phone: icon, manifest, full-screen flag, and the how-to in Practice settings
    const page = await open({ ...devices["iPhone 13"] }, HCB);
    const head = await page.evaluate(() => ({ icon: (document.head.querySelector('link[rel="apple-touch-icon"]') || {}).href || "", icons: document.head.querySelectorAll('link[rel="apple-touch-icon"]').length,
      man: (document.head.querySelector('link[rel="manifest"]') || {}).href || "", cap: (document.head.querySelector('meta[name="apple-mobile-web-app-capable"]') || {}).content || "", name: (document.head.querySelector('meta[name="apple-mobile-web-app-title"]') || {}).content || "" }));
    const app = path.join(ROOT, "player", "app"), file = u => path.join(app, u.split("/player/app/")[1] || "missing");
    expect(head.icons === 1 && /\/player\/app\/icon-180\.png$/.test(head.icon) && fs.existsSync(file(head.icon)), "install: the page carries one home-screen icon, and the file exists");
    let man = null; try { man = JSON.parse(fs.readFileSync(file(head.man), "utf8")); } catch (e) {}
    expect(man && man.display === "standalone" && /^https:\/\/alexattardmusic\.com\/play\//.test(man.start_url) && man.icons.every(i => fs.existsSync(file(i.src))), "install: the manifest opens the play page full screen and its icons exist");
    expect(head.cap === "yes" && head.name.length > 0 && head.name.length <= 12, "install: full-screen flag and a home-screen name that fits under an icon (" + head.name + ")");
    await page.click('[data-r="p-gear"]'); await page.waitForTimeout(400);
    await page.click('[data-r="install-btn"]'); await page.waitForTimeout(300);
    const dlg = await page.evaluate(() => ({ open: !document.querySelector('[data-r="idlg"]').hidden, steps: document.querySelector('[data-r="i-steps"]').textContent, url: location.search }));
    expect(dlg.open && /Share/.test(dlg.steps) && /Add to Home Screen/.test(dlg.steps), "install: on an iPhone the steps say Share, then Add to Home Screen");
    expect(/[?&]t=sax-beginner-alto-hot-cross-buns/.test(dlg.url) && /[?&]c=\w+/.test(dlg.url), "install: the address now names this tune and its code, so the icon opens it unlocked");
    await page.context().close();
    const ctxA = await b.newContext({ ...devices["iPhone 13"] }); await wire(ctxA);                       // the same page opened from the home screen
    await ctxA.addInitScript(() => { const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode: standalone/.test(q) ? { matches: true, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} } : mm(q); });
    const pa = await ctxA.newPage(); await pa.goto(URL_OF(HCB)); await pa.waitForTimeout(1800);
    const appv = await pa.evaluate(() => { const bar = document.querySelector('[data-r="pbar"]'), pl = document.querySelector('[data-r="p-play"]').getBoundingClientRect(), sc = document.querySelector(".score").getBoundingClientRect();
      return { gap: Math.round(innerHeight - pl.bottom), fit: /viewport-fit=cover/.test((document.querySelector('meta[name="viewport"]') || {}).content || "") || !document.querySelector('meta[name="viewport"]'), clear: sc.bottom <= bar.getBoundingClientRect().top + 1, btn: document.querySelector('[data-r="install-btn"]').hidden }; });
    expect(appv.gap >= 24 && appv.clear, "from the home screen: the play bar keeps clear of the bottom edge and the music stops above it (" + appv.gap + " px under Play)");
    expect(appv.btn, "from the home screen: the \"Add to your home screen\" button is not shown again");
    await ctxA.close();
    const sw = fs.readFileSync(path.join(app, "sw.js"), "utf8");
    expect(/r\.mode === "navigate"/.test(sw) && /"\/play"/.test(sw) && !/respondWith\(fetch\(r\)\)/.test(sw), "install: the offline file only answers the play page and the player's own files");
  }
  if (want("bar")) {                                        // a piano page shows the piano
    const page = await open({ viewport: { width: 390, height: 844 } }, "winter-wonderland-piano");
    const who = await page.evaluate(() => { const e = document.querySelector('[data-r="subtitle"]'); return e.getAttribute("data-inst") + "|" + e.querySelector('[data-r="inst-name"]').textContent.trim(); });
    expect(who === "piano|Piano", "under the title of a piano tune: the piano icon and \"Piano\"");
    await page.context().close();
  }
  await b.close();
  fs.rmSync(TMP, { recursive: true, force: true });
  console.log(ok.length + " feature checks passed" + (problems.length ? ", " + problems.length + " FAILED" : "") + " in " + Math.round((Date.now() - t0) / 1000) + "s");
  if (problems.length) process.exit(1); else console.log("All clear.");
})().catch(e => { console.error(e); process.exit(1); });
