import asyncio, subprocess, sys, time, json
from playwright.async_api import async_playwright
SLUG, CODE = sys.argv[1], sys.argv[2]
ST = """() => { const q = s => document.querySelector('[data-r="'+s+'"]'); const s = document.querySelector('#aam-play .score svg');
  return { key: q('p-key-k').textContent + ' / ' + q('p-key-i').textContent, cells: [...document.querySelectorAll('#aam-play .cell')].slice(0, 8).map(c => [...c.querySelectorAll('.c > b')].map(b => b.textContent).join(' ')).join(' | '),
    bridge: [...document.querySelectorAll('#aam-play .cell')].slice(16, 20).map(c => [...c.querySelectorAll('.c > b')].map(b => b.textContent).join(' ')).join(' | '),
    score: s ? [...s.querySelectorAll('.ch-t')].slice(0, 6).map(e => e.textContent).join(' ') : null, tight: document.querySelectorAll('.cell.tight').length, note: q('k-note').textContent }; }"""
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/ww/site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
            ctx = await b.new_context(viewport={"width": 390, "height": 760}, has_touch=True, is_mobile=True, device_scale_factor=2)
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(f"http://localhost:8765/index.html?t={SLUG}&c={CODE}"); await pg.wait_for_selector("#aam-play .cell"); await pg.wait_for_timeout(800)
            out = {"start": await pg.evaluate(ST)}
            await pg.tap('[data-r="p-key"]'); await pg.wait_for_timeout(300); await pg.screenshot(path=f"/home/claude/ww/k_{SLUG}_dlg.png")
            for inst in ("0", "2", "9"):
                await pg.tap(f'[data-r="k-insts"] [data-inst="{inst}"]'); await pg.wait_for_timeout(300); out["inst" + inst] = await pg.evaluate(ST)
            await pg.tap('[data-r="k-insts"] [data-inst="0"]'); await pg.tap('[data-r="k-keys"] [data-pc="7"]'); await pg.wait_for_timeout(300); out["keyG_concert"] = await pg.evaluate(ST)
            await pg.screenshot(path=f"/home/claude/ww/k_{SLUG}_dlg2.png")
            await pg.tap('[data-r="k-close"]'); await pg.tap('[data-view="arpeggios"]'); await pg.wait_for_timeout(1000); out["arp_G"] = await pg.evaluate(ST); await pg.screenshot(path=f"/home/claude/ww/k_{SLUG}_arpG.png")
            await pg.tap('[data-r="p-key"]'); await pg.tap('[data-r="k-insts"] [data-inst="9"]'); await pg.tap('[data-r="k-close"]'); await pg.wait_for_timeout(1000); out["arp_G_alto"] = await pg.evaluate(ST); await pg.screenshot(path=f"/home/claude/ww/k_{SLUG}_arpGalto.png")
            await pg.tap('[data-r="p-play"]')
            for i in range(14):
                await pg.wait_for_timeout(330)
                if i in (1, 5): await pg.screenshot(path=f"/home/claude/ww/k_{SLUG}_cnt{i}.png")
            cnt = await pg.evaluate("""() => { const c = document.querySelector('[data-r=cnt]'); return { hidden: c.hidden, on: c.querySelectorAll('i.on').length }; }""")
            await pg.wait_for_timeout(3500); cnt2 = await pg.evaluate("""() => document.querySelector('[data-r=cnt]').hidden""")
            await pg.tap('[data-r="p-play"]'); out["count_mid"] = cnt; out["count_after"] = cnt2; out["errs"] = errs
            print(json.dumps(out, indent=1, ensure_ascii=False)); await b.close()
    finally: srv.terminate()
asyncio.run(main())
