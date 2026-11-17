import asyncio, subprocess, sys, time, json
from playwright.async_api import async_playwright
async def run(b, stall, nostore):
    ctx = await b.new_context(viewport={"width": 390, "height": 760}, has_touch=True, is_mobile=True)
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    if stall:
        async def hang(route): await asyncio.sleep(60)
        await pg.route("**/raw.githubusercontent.com/**", hang); await pg.route("**/cdn.jsdelivr.net/**", hang)
    if nostore: await pg.add_init_script("Object.defineProperty(window, 'localStorage', { get: function () { throw new Error('blocked'); } });")
    await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(700)
    await pg.fill('[data-r="pw"]', "ww-2193"); await pg.tap('[data-r="gate-form"] button'); await pg.wait_for_timeout(2500)
    r = await pg.evaluate("""() => { const q = s => document.querySelector('[data-r="'+s+'"]'); return { url: location.search, gate: q('gate').hidden, err: q('err').textContent, title: q('title').textContent, cells: document.querySelectorAll('#aam-play .cell').length }; }""")
    # switch tune through My tunes (a page reload)
    r2 = None
    if r["gate"]:
        await pg.tap('[data-r="lib-btn"]'); await pg.fill('[data-r="add-code"]', "WA-5627"); await pg.tap('[data-r="add-form"] button'); await pg.wait_for_timeout(3000)
        r2 = await pg.evaluate("""() => { const q = s => document.querySelector('[data-r="'+s+'"]'); return { url: location.search, gate: q('gate').hidden, sub: q('subtitle').textContent.slice(0, 24), err: q('err').textContent }; }""")
    await ctx.close(); return {"stall": stall, "nostore": nostore, "typed": r, "then_alto": r2, "errs": errs}
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/ww/site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
            for stall, nostore in [(False, False), (True, False), (False, True), (True, True)]: print(json.dumps(await run(b, stall, nostore), ensure_ascii=False))
            await b.close()
    finally: srv.terminate()
asyncio.run(main())
