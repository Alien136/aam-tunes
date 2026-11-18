#!/usr/bin/env node
/* Pre-release check: opens EVERY tune, on every tab, at phone / half-window / laptop / wide sizes, through the real loader,
   and fails if any music is clipped, lines collide, the page overflows sideways or a script error appears.

   Usage:  AAM_CODE=<master code> node tools/check_release.js [--file player/aam-player.html] [--only slug-part] [--loader]
   Needs:  playwright, plus the tone and abcjs packages (looked for in tools/node_modules, then $AAM_NODE_MODULES).
   Nothing is fetched from the internet: the CDN and repository addresses are answered from this folder. */
const fs = require("fs"), path = require("path");
const { chromium, devices } = require("playwright");
const ROOT = path.resolve(__dirname, ".."), arg = (k, d) => { const i = process.argv.indexOf(k); return i < 0 ? d : process.argv[i + 1]; };
const FILE = path.resolve(ROOT, arg("--file", "player/aam-player.html")), ONLY = arg("--only", ""), CODE = process.env.AAM_CODE;
const NM = [path.join(__dirname, "node_modules"), process.env.AAM_NODE_MODULES || ""].find(d => d && fs.existsSync(path.join(d, "tone")));
if (!CODE) { console.error("Set AAM_CODE to the master code."); process.exit(2); }
if (!NM) { console.error("tone / abcjs not found: run `npm install` in tools/ or set AAM_NODE_MODULES."); process.exit(2); }
const TYPES = { ".json": "application/json", ".mp3": "audio/mpeg", ".html": "text/plain; charset=utf-8", ".js": "application/javascript" };
const SIZES = [["phone", { ...devices["iPhone 13"] }], ["half", { viewport: { width: 942, height: 900 } }],
               ["laptop", { viewport: { width: 1366, height: 680 } }], ["wide", { viewport: { width: 1900, height: 900 } }]];

async function wire(ctx) {
  await ctx.route("**/*", route => {
    const u = new URL(route.request().url());
    const file = f => fs.existsSync(f) ? route.fulfill({ body: fs.readFileSync(f), contentType: TYPES[path.extname(f)] || "application/octet-stream", headers: { "access-control-allow-origin": "*" } }) : route.abort();
    if (u.hostname === "alexattardmusic.com" && u.pathname.startsWith("/play"))
      return route.fulfill({ contentType: "text/html", body: "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><body style='margin:0'>" + fs.readFileSync(path.join(ROOT, "player/loader.html"), "utf8") });
    if (u.hostname === "raw.githubusercontent.com") {
      const rel = u.pathname.replace(/^\/[^/]+\/[^/]+\/[^/]+\//, "");
      return file(rel === "release/player.html" ? FILE : path.join(ROOT, rel));       // the candidate stands in for the released copy
    }
    if (u.hostname === "cdn.jsdelivr.net" && u.pathname.startsWith("/npm/")) return file(path.join(NM, u.pathname.replace(/^\/npm\/([^@/]+)@[^/]+/, "$1")));
    return route.abort();
  });
}

// run inside the page: what is wrong with the music as drawn right now?
function inspect() {
  const out = [], root = document.getElementById("aam-play");
  if (document.documentElement.scrollWidth > window.innerWidth + 1) out.push("page is wider than the screen");
  const bar = root.querySelector(".pbar"); if (bar) { const r = bar.getBoundingClientRect(); if (r.bottom > window.innerHeight + 1 || r.right > window.innerWidth + 1) out.push("play bar runs off the screen"); }
  const score = root.querySelector('[data-r="score"]'); if (!score || score.hidden) return out;
  const svg = score.querySelector("svg"); if (!svg) { out.push("no music drawn"); return out; }
  const sr = score.getBoundingClientRect(), mask = root.querySelector(".score-mask"), mr = mask && !mask.hidden ? mask.getBoundingClientRect() : null;
  const visBot = mr && mr.height > 1 ? mr.top : sr.bottom, lines = [];
  for (let l = 0; svg.querySelectorAll(".abcjs-staff.abcjs-l" + l).length; l++) {
    const st = [...svg.querySelectorAll(".abcjs-staff.abcjs-l" + l)].map(e => e.getBoundingClientRect());
    let top = 1e9, bot = -1e9; svg.querySelectorAll(".abcjs-l" + l).forEach(e => { const r = e.getBoundingClientRect(); if (!r.height && !r.width) return; top = Math.min(top, r.top); bot = Math.max(bot, r.bottom); });
    lines.push({ staffTop: Math.min(...st.map(r => r.top)), staffBot: Math.max(...st.map(r => r.bottom)), top, bot });
  }
  svg.querySelectorAll(".ch-t").forEach(t => {                       // each chord name belongs to the first staff below it
    const r = t.getBoundingClientRect(), mid = (r.top + r.bottom) / 2, ln = lines.find(x => x.staffTop > mid - 2);
    if (ln) { ln.top = Math.min(ln.top, r.top + r.height * 0.2); ln.names = true; }       // the top fifth of a text box is empty space above the letters
  });
  lines.forEach((ln, l) => {
    const nx = lines[l + 1];
    if (nx && ln.bot > nx.top + 1.5) out.push("line " + (l + 1) + " runs into line " + (l + 2) + " by " + Math.round(ln.bot - nx.top) + "px");
    if (ln.staffTop >= visBot - 1) { if (ln.top < visBot - 1.5) out.push("line " + (l + 1) + " is hidden but its top shows at the bottom (" + Math.round(visBot - ln.top) + "px)"); return; }
    if (ln.staffBot > visBot + 1) { out.push("line " + (l + 1) + " is cut through the staff"); return; }
    if (ln.bot > visBot + 1.5) out.push("line " + (l + 1) + ": low notes or beams clipped by " + Math.round(ln.bot - visBot) + "px");
    if (l === 0 && ln.top < sr.top - 1.5) out.push("line 1 is clipped at the top");
  });
  if (!lines.length) out.push("no staves found");
  return out;
}

(async () => {
  const slugs = fs.readdirSync(path.join(ROOT, "tunes")).filter(f => f.endsWith(".json")).map(f => f.slice(0, -5)).filter(s => s.includes(ONLY));
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] }), problems = [], t0 = Date.now(); let states = 0;
  for (const [size, opts] of SIZES) {
    const ctx = await browser.newContext(opts); await wire(ctx);
    const queue = slugs.slice();
    await Promise.all([0, 1, 2, 3].map(async () => {
      const page = await ctx.newPage(); let errs = [];
      page.on("pageerror", e => errs.push(e.message));
      while (queue.length) {
        const slug = queue.shift(); errs = [];
        const note = (view, what) => problems.push(`${size.padEnd(6)} ${slug} [${view}] ${what}`);
        try {
          await page.goto("https://alexattardmusic.com/play/?t=" + slug + "&c=" + encodeURIComponent(CODE));
          await page.waitForSelector("#aam-play.is-open", { timeout: 15000 });
          await page.waitForFunction(() => document.querySelector("#aam-play [data-view]") || document.querySelector('#aam-play [data-r="score"] svg'), null, { timeout: 15000 });
          await page.waitForTimeout(350);
          const views = await page.$$eval("#aam-play [data-view]", els => els.filter(e => e.offsetParent).map(e => e.dataset.view));
          for (const v of views.length ? views : [null]) {                // an exercise with one view has no tabs
            if (v) { await page.click(`#aam-play [data-view="${v}"]`); await page.waitForTimeout(260); }
            states++; (await page.evaluate(inspect)).forEach(w => note(v || "music", w));
          }
          errs.forEach(e => note("-", "script error: " + e));
        } catch (e) { note("-", "did not open: " + String(e.message).split("\n")[0]); }
      }
      await page.close();
    }));
    await ctx.close();
  }
  // does the band actually start? one tune of each kind: load the sounds, count in, reach bar 1, no errors
  if (!ONLY) {
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 680 } }); await wire(ctx);
    const kinds = {}; slugs.forEach(sl => { const t = JSON.parse(fs.readFileSync(path.join(ROOT, "tunes", sl + ".json"), "utf8")); const k = t.style || "swing"; if (!kinds[k]) kinds[k] = sl; });
    for (const [kind, slug] of Object.entries(kinds)) {
      const page = await ctx.newPage(), errs = []; page.on("pageerror", e => errs.push(e.message));
      try {
        await page.goto("https://alexattardmusic.com/play/?t=" + slug + "&c=" + encodeURIComponent(CODE));
        await page.waitForSelector("#aam-play.is-open", { timeout: 15000 }); await page.waitForTimeout(500);
        await page.keyboard.press("Space");
        await page.waitForFunction(() => /Bar/.test(document.querySelector('#aam-play [data-r="p-where"]').textContent), null, { timeout: 40000 });
        if (await page.$eval('#aam-play [data-r="snd-credit"]', e => e.hidden)) problems.push(`play   ${slug} (${kind}) fell back to the classic sounds`);
      } catch (e) { problems.push(`play   ${slug} (${kind}) did not start playing: ${String(e.message).split("\n")[0]}`); }
      errs.forEach(e => problems.push(`play   ${slug} (${kind}) script error: ${e}`));
      states++; await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  console.log(`${slugs.length} tunes x ${SIZES.length} screen sizes, ${states} views checked in ${Math.round((Date.now() - t0) / 1000)}s`);
  if (problems.length) { console.log(problems.length + " PROBLEMS:\n" + problems.sort().join("\n")); process.exit(1); }
  console.log("All clear.");
})();
