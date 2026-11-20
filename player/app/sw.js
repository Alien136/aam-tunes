/* Alex Attard Music play-along: offline file. NOT active until it is uploaded to the website as  https://alexattardmusic.com/aam-sw.js
   (one upload; see BUILDER.md / STATUS.md). The player registers it for the /play/ page only.

   What it does: keeps a copy of the play page, the player, the tunes a student has opened and the band's sounds, so the player
   opens and plays with no signal. It answers ONLY the requests listed below; everything else on the website passes through untouched.
   Bump VERSION to make every phone fetch fresh copies. */
const VERSION = "aam-1", PAGE = VERSION + "-page", DATA = VERSION + "-data", SOUNDS = "aam-sounds-v2";
const REPO = /^https:\/\/(raw\.githubusercontent\.com\/Alien136\/aam-tunes\/|cdn\.jsdelivr\.net\/gh\/Alien136\/aam-tunes@)/;
const LIBS = /^https:\/\/(cdn\.jsdelivr\.net\/npm\/(tone|abcjs)@|fonts\.googleapis\.com\/|fonts\.gstatic\.com\/)/;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.startsWith("aam-") && ![PAGE, DATA, SOUNDS].includes(k)) await caches.delete(k);
  await self.clients.claim();
})()));

const put = async (name, req, res) => { if (res && (res.ok || res.type === "opaque")) { const c = await caches.open(name); await c.put(req, res.clone()); } return res; };
const fresh = async (name, req) => {                       // the network first (so updates arrive), the saved copy when there is no signal
  try { return await put(name, req, await fetch(req)); }
  catch (e) { const hit = await caches.match(req, { ignoreSearch: name === PAGE }); if (hit) return hit; throw e; }
};
const saved = async (name, req) => (await caches.match(req)) || put(name, req, await fetch(req));   // sounds and libraries never change under one address

self.addEventListener("fetch", e => {
  const r = e.request, u = r.url;
  if (r.method !== "GET") return;
  if (r.mode === "navigate") { if (new URL(u).pathname.replace(/\/$/, "") === "/play") e.respondWith(fresh(PAGE, r)); return; }
  if (REPO.test(u)) { e.respondWith(/\/sounds\//.test(u) ? saved(SOUNDS, r) : fresh(DATA, r)); return; }
  if (LIBS.test(u)) { e.respondWith(saved(DATA, r)); return; }
});
