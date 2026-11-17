import asyncio, subprocess, sys, time, json
from playwright.async_api import async_playwright
ST = """() => { const q = s => document.querySelector('[data-r="'+s+'"]'); const s = document.querySelector('#aam-play .score svg');
  return { title: q('title').textContent, toc: q('title').classList.contains('has-toc'), tabs: [...document.querySelectorAll('#aam-play [data-view]')].map(b => b.querySelector('.sm').textContent),
    key: q('p-key-k').textContent, reps: q('p-reps').textContent, chips: [...document.querySelectorAll('#aam-play .sheet-body .chip, #aam-play [data-r=row-band] .chip')].filter(c => !c.hidden).map(c => c.textContent.trim()).join(' | '),
    chords: s ? [...s.querySelectorAll('.ch-t')].map(e => e.textContent).join(' ') : null, notes: s ? s.querySelectorAll('.abcjs-note').length : 0, scoreHidden: q('score').hidden }; }"""
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/ww/site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    out = {}
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
            ctx = await b.new_context(viewport={"width": 390, "height": 760}, has_touch=True, is_mobile=True, device_scale_factor=2)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto("http://localhost:8765/index.html?t=demo-long-tones&c=DEMO1"); await pg.wait_for_selector("#aam-play .score svg", timeout=15000); await pg.wait_for_timeout(900)
            out["long"] = await pg.evaluate(ST); await pg.screenshot(path="/home/claude/ww/b_long.png")
            await pg.tap('[data-r="title"]'); await pg.wait_for_timeout(300); await pg.screenshot(path="/home/claude/ww/b_toc.png")
            out["toc"] = await pg.evaluate("() => [...document.querySelectorAll('[data-r=toc-list] .lib-pdf, [data-r=toc-list] .lib-tune b')].map(e => e.textContent)")
            await pg.tap('[data-r="toc-close"]'); await pg.tap('[data-r="p-play"]'); await pg.wait_for_timeout(9000)
            out["long_playing"] = await pg.evaluate("() => ({where: document.querySelector('[data-r=p-reps]').textContent, now: !!document.querySelector('#aam-play .score .hl.is-now')})"); await pg.tap('[data-r="p-play"]')
            await pg.tap('[data-r="title"]'); await pg.tap('[data-r="toc-list"] [data-go]:not([disabled])'); await pg.wait_for_selector("#aam-play .score svg"); await pg.wait_for_timeout(1200)
            out["scale"] = await pg.evaluate(ST); await pg.screenshot(path="/home/claude/ww/b_scale.png")
            for _ in range(3):
                bx = await pg.locator('[data-r="p-faster"]').bounding_box(); await pg.mouse.move(bx["x"]+10, bx["y"]+10); await pg.mouse.down(); await pg.wait_for_timeout(1500); await pg.mouse.up()
            await pg.tap('[data-r="p-play"]'); keys = []
            for i in range(26):
                await pg.wait_for_timeout(500); k = await pg.evaluate("() => document.querySelector('[data-r=p-key-k]').textContent + ' ' + document.querySelector('[data-r=p-reps]').textContent + ' ' + ([...document.querySelectorAll('#aam-play .score .ch-t')][0]||{}).textContent")
                if not keys or keys[-1] != k: keys.append(k)
                if i == 12: await pg.screenshot(path="/home/claude/ww/b_scale_play.png")
            await pg.tap('[data-r="p-play"]'); await pg.wait_for_timeout(400); out["scale_keys"] = keys; out["scale_after_stop"] = await pg.evaluate("() => document.querySelector('[data-r=p-key-k]').textContent")
            await pg.goto("http://localhost:8765/index.html?tune=demo-251-lick"); await pg.wait_for_selector("#aam-play .cell"); await pg.wait_for_timeout(900)
            out["lick"] = await pg.evaluate(ST); await pg.tap('[data-view="notes"]'); await pg.wait_for_timeout(800); await pg.screenshot(path="/home/claude/ww/b_lick.png")
            await pg.tap('[data-r="lib-btn"]'); await pg.wait_for_timeout(300); out["mytunes"] = await pg.evaluate("() => [...document.querySelectorAll('[data-r=lib-list] .lib-pdf, [data-r=lib-list] .lib-tune b')].map(e => e.textContent)")
            out["errs"] = errs; print(json.dumps(out, indent=1, ensure_ascii=False)); await b.close()
    finally: srv.terminate()
asyncio.run(main())
