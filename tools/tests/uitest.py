import os
import asyncio, json, subprocess, sys, time
from playwright.async_api import async_playwright
H = int(sys.argv[1]) if len(sys.argv) > 1 else 760
JS_TOUCH = """
async ([sel, i0, i1]) => {
  const box = document.querySelector(sel);
  const pt = (i) => { if (sel.includes('form')) { const r = document.querySelectorAll('#aam-play .cell')[i].getBoundingClientRect(); return [r.left + r.width/2, r.top + r.height/2]; }
                      const r = document.querySelectorAll('#aam-play .score .hl')[i].getBoundingClientRect(); return [r.left + r.width/2, r.top + r.height/2]; };
  const mk = (x, y) => new Touch({identifier: 1, target: document.elementFromPoint(x, y) || box, clientX: x, clientY: y, pageX: x, pageY: y});
  const fire = (type, x, y) => { const t = mk(x, y); (document.elementFromPoint(x, y) || box).dispatchEvent(new TouchEvent(type, {bubbles: true, cancelable: true, touches: type === 'touchend' ? [] : [t], changedTouches: [t]})); };
  const [x0, y0] = pt(i0), [x1, y1] = pt(i1);
  fire('touchstart', x0, y0); await new Promise(r => setTimeout(r, 420));
  fire('touchmove', (x0+x1)/2, (y0+y1)/2); fire('touchmove', x1, y1); fire('touchend', x1, y1);
  await new Promise(r => setTimeout(r, 100));
}"""
STATE = """() => { const q = s => document.querySelector('[data-r="'+s+'"]'); return {
  inRange: [...document.querySelectorAll('#aam-play .cell.in-range')].map(c => +c.dataset.i), badge: document.querySelectorAll('#aam-play .loop-badge').length,
  svgBadge: document.querySelectorAll('#aam-play .loop-g').length, hlRange: document.querySelectorAll('#aam-play .score .hl.in-range').length,
  reps: q('p-reps').textContent, repsVis: getComputedStyle(q('p-reps')).display, pop: !q('p-reps-pop').hidden, hint: q('hint').textContent.slice(0, 60),
  modes: [...document.querySelectorAll('[data-mode]')].map(b => b.dataset.mode + ':' + b.getAttribute('aria-pressed')).join(' '), where: q('p-where').textContent }; }"""
async def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--directory", "/home/claude/ww/site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
            ctx = await b.new_context(viewport={"width": 390, "height": H}, has_touch=True, is_mobile=True, device_scale_factor=2)
            pg = await ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto("http://localhost:8765/index.html?t=winter-wonderland-piano&c=" + os.environ["AAM_TEST_CODE"] + ""); await pg.wait_for_selector("#aam-play .cell", timeout=15000); await pg.wait_for_timeout(1200)
            out = {"start": await pg.evaluate(STATE)}
            await pg.screenshot(path="/home/claude/ww/t1.png")
            await pg.tap('[data-r="p-reps"]'); await pg.wait_for_timeout(200); await pg.screenshot(path="/home/claude/ww/t2.png")
            await pg.tap('[data-r="p-reps-pop"] button[data-n="3"]'); await pg.wait_for_timeout(200); out["reps3"] = await pg.evaluate(STATE)
            await pg.evaluate(JS_TOUCH, ['[data-r="form"]', 4, 7]); out["held"] = await pg.evaluate(STATE)
            await pg.screenshot(path="/home/claude/ww/t3.png")
            await pg.tap('[data-view="arpeggios"]'); await pg.wait_for_timeout(1200); out["arp"] = await pg.evaluate(STATE); await pg.screenshot(path="/home/claude/ww/t4.png")
            await pg.evaluate("document.querySelector('#aam-play .loop-g').dispatchEvent(new MouseEvent('click', {bubbles: true}))"); await pg.wait_for_timeout(200); out["cleared"] = await pg.evaluate(STATE)
            await pg.evaluate(JS_TOUCH, ['[data-r="score"]', 2, 5]); out["heldScore"] = await pg.evaluate(STATE); await pg.screenshot(path="/home/claude/ww/t5.png")
            await pg.tap('[data-view="chords"]'); await pg.wait_for_timeout(500)
            await pg.tap('#aam-play .loop-badge'); await pg.wait_for_timeout(200); out["cleared2"] = await pg.evaluate(STATE)
            out["errs"] = errs; print(json.dumps(out, indent=1, ensure_ascii=False)); await b.close()
    finally:
        srv.terminate()
asyncio.run(main())
