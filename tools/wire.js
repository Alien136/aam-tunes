/* Shared by the release checks: answers every network request from this folder, so nothing is fetched from the internet.
   The website pages, the repository (main branch and the "pdf" branch that holds the booklet PDFs) and the CDN packages are all stood in for. */
const fs = require("fs"), path = require("path");
const ROOT = path.resolve(__dirname, ".."), arg = (k, d) => { const i = process.argv.indexOf(k); return i < 0 ? d : process.argv[i + 1]; };
const FILE = path.resolve(ROOT, arg("--file", "player/aam-player.html")), ONLY = arg("--only", ""), CODE = process.env.AAM_CODE;
const NM = [path.join(__dirname, "node_modules"), process.env.AAM_NODE_MODULES || ""].find(d => d && fs.existsSync(path.join(d, "tone")));
if (!CODE) { console.error("Set AAM_CODE to the master code."); process.exit(2); }
if (!NM) { console.error("tone / abcjs not found: run `npm install` in tools/ or set AAM_NODE_MODULES."); process.exit(2); }
const TYPES = { ".json": "application/json", ".mp3": "audio/mpeg", ".html": "text/plain; charset=utf-8", ".js": "application/javascript" };
async function wire(ctx) {
  await ctx.route("**/*", route => {
    const u = new URL(route.request().url());
    const file = f => fs.existsSync(f) ? route.fulfill({ body: fs.readFileSync(f), contentType: TYPES[path.extname(f)] || "application/octet-stream", headers: { "access-control-allow-origin": "*" } }) : route.abort();
    if (u.hostname === "alexattardmusic.com" && u.pathname.startsWith("/lessons"))                      // a stand-in lessons page holding the demo card
      return route.fulfill({ contentType: "text/html", body: "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><body style='margin:0'><div style='padding:24px 12px'>" + fs.readFileSync(path.join(ROOT, "player/demo-loader.html"), "utf8") + "</div>" });
    if (u.hostname === "alexattardmusic.com" && u.pathname.startsWith("/theory"))                       // the theory page: its own loader
      return route.fulfill({ contentType: "text/html", body: "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><body style='margin:0'>" + fs.readFileSync(path.join(ROOT, "theory/loader.html"), "utf8") });
    if (u.hostname === "alexattardmusic.com" && u.pathname.startsWith("/play"))
      return route.fulfill({ contentType: "text/html", body: "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><body style='margin:0'>" + fs.readFileSync(path.join(ROOT, "player/loader.html"), "utf8") });
    if (u.hostname === "raw.githubusercontent.com") {
      const rel = u.pathname.replace(/^\/[^/]+\/[^/]+\/[^/]+\//, "");
      if (u.pathname.split("/")[3] === "pdf") {                                         // booklet PDFs live on their own branch
        const staged = path.join(ROOT, "tools", "out", "pdf-branch", rel);
        if (fs.existsSync(staged)) return file(staged);
        try { return route.fulfill({ body: require("child_process").execFileSync("git", ["show", "origin/pdf:" + rel], { cwd: ROOT, maxBuffer: 1 << 28 }), contentType: "application/octet-stream", headers: { "access-control-allow-origin": "*" } }); }
        catch (e) { return route.abort(); }
      }
      if (rel === "release/cards.html" && !fs.existsSync(path.join(ROOT, rel))) return route.fulfill({ status: 404, body: "", headers: { "access-control-allow-origin": "*" } });
      if (rel === "release/demo.html") return file(path.join(ROOT, "player/demo.html"));
      return file(rel === "release/player.html" ? FILE : path.join(ROOT, rel));       // the candidates stand in for the released copies
    }
    if (u.hostname === "cdn.jsdelivr.net" && u.pathname.startsWith("/npm/")) return file(path.join(NM, u.pathname.replace(/^\/npm\/([^@/]+)@[^/]+/, "$1")));
    return route.abort();
  });
}
module.exports = { wire, ROOT, FILE, ONLY, CODE, NM, arg };
