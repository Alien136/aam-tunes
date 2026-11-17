import asyncio, json, subprocess, sys, time
from playwright.async_api import async_playwright
W, H, mobile = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3] == "m"
ST = """() => { const q = s => document.querySelector('[data-r="'+s+'"]'); const sc = q('score'); const o = document.querySelector('#aam-play .score-over');
  const now = document.querySelector('#aam-play .score > div .hl.is-now'); const hl=[...document.querySelectorAll('#aam-play .score > div .hl')];
  return { where: (q('p-where').textContent||q('now-where').textContent).slice(0,24), bar: now ? hl.indexOf(now) : -1, st: Math.round(sc.scrollTop), paging: sc.classList.contains('paging'), ovf: getComputedStyle(sc).overflowY,
    over: o ? Math.round(o.getBoundingClientRect().height) : 0, ch: sc.clientHeight }; }"""
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/ww/site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
            ctx = await b.new_context(viewport={"width": W, "height": H}, has_touch=mobile, is_mobile=mobile, device_scale_factor=2 if mobile else 1)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto("http://localhost:8765/index.html?t=winter-wonderland-piano&c=WW2193"); await pg.wait_for_selector("#aam-play .cell", timeout=15000); await pg.wait_for_timeout(800)
            await pg.click('[data-view="arpeggios"]'); await pg.wait_for_timeout(900)
            # fastest tempo so the test is quick
            for _ in range(40): await pg.click('[data-r="p-faster"]' if mobile else '[data-r="faster"]') if await pg.query_selector('[data-r="p-faster"]' if mobile else '[data-r="faster"]') else None
            await pg.click('[data-r="p-play"]' if mobile else '[data-r="play"]')
            log, shots, seen = [], 0, set()
            t0 = time.time()
            while time.time() - t0 < float(sys.argv[4]) :
                s = await pg.evaluate(ST); key = (s["bar"], s["over"] > 0, s["st"])
                if key not in seen:
                    seen.add(key); log.append(s)
                    if s["over"] > 0 and shots < 2: shots += 1; await pg.screenshot(path=f"/home/claude/ww/pt_{sys.argv[3]}{shots}.png")
                await pg.wait_for_timeout(120)
            await pg.click('[data-r="p-play"]' if mobile else '[data-r="play"]'); await pg.wait_for_timeout(300); log.append(await pg.evaluate(ST))
            print(json.dumps(log)); print("errs", errs); await b.close()
    finally: srv.terminate()
asyncio.run(main())
