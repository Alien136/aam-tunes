import os
import asyncio, subprocess, sys, time, json
from playwright.async_api import async_playwright
KEY = "() => document.querySelector('[data-r=p-key-k]').textContent"
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/ww/site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    out = {}
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
            ctx = await b.new_context(viewport={"width": 390, "height": 760}, has_touch=True, is_mobile=True, device_scale_factor=2)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            first = True
            for slug in sys.argv[2:]:
                await pg.goto("http://localhost:8765/index.html?t=sax-welcome-%s-%s%s" % (sys.argv[1], slug, "&c=" + CODE if first else "")); first = False
                await pg.wait_for_selector("#aam-play .score svg", timeout=15000); await pg.wait_for_timeout(1000)
                r = {"key": await pg.evaluate(KEY), "notes": await pg.evaluate("() => document.querySelectorAll('#aam-play .score svg .abcjs-note').length")}
                await pg.screenshot(path="/home/claude/ww/wb_%s.png" % slug)
                for _ in range(2):
                    bx = await pg.locator('[data-r="p-faster"]').bounding_box(); await pg.mouse.move(bx["x"]+10, bx["y"]+10); await pg.mouse.down(); await pg.wait_for_timeout(1800); await pg.mouse.up()
                await pg.tap('[data-r="p-play"]'); keys = []
                for i in range(16):
                    await pg.wait_for_timeout(500); k = await pg.evaluate(KEY)
                    if not keys or keys[-1] != k: keys.append(k)
                await pg.tap('[data-r="p-play"]'); await pg.wait_for_timeout(300); r["keys"] = keys; r["after"] = await pg.evaluate(KEY); out[slug] = r
            await pg.tap('[data-r="title"]'); await pg.wait_for_timeout(400); await pg.screenshot(path="/home/claude/ww/wb_toc.png")
            out["errs"] = errs; print(json.dumps(out, ensure_ascii=False)); await b.close()
    finally: srv.terminate()
CODE = os.environ["AAM_TEST_CODE"]                     # the booklet code for this edition, without the dash
asyncio.run(main())
