"""Second pass over a built file: other screen sizes and edge cases.

    python3 tools/playtest_sizes.py games/Boards_Up_Area_of_Polygons.html [screenshot_dir]

Checks that a saved game from a different unit is not offered for resume, the huddle and boards-up phases,
a windowed panel browser (1920x940), a laptop (1366x768), a 5:4 screen, and a phone in portrait.
Needs a unit with at least four categories. Fails on any overlap, clipped category name or page error."""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

FILE = 'file://' + os.path.abspath(sys.argv[1])
SHOTS = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', os.path.splitext(os.path.basename(sys.argv[1]))[0])
os.makedirs(SHOTS, exist_ok=True)

OVERLAP_JS = """() => {
  const out = [], vw = innerWidth, vh = innerHeight;
  const t = document.querySelector('.qtext'), b = document.querySelector('.qbody');
  if (t && b) {
    const tr = t.getBoundingClientRect(), br = b.getBoundingClientRect();
    if (tr.left < -1 || tr.right > vw + 1) out.push('text off screen horizontally');
    if (tr.top < br.top - 1 || tr.bottom > br.bottom + 1) out.push('text outside its area');
    const s = document.querySelector('.side');
    if (s) { const sr = s.getBoundingClientRect(); if (!(tr.right <= sr.left + 1 || tr.bottom <= sr.top + 1 || sr.bottom <= tr.top + 1)) out.push('text overlaps clock panel'); if (sr.bottom > vh + 1) out.push('clock panel off screen'); }
  }
  const f = document.querySelector('.qfoot'); if (f && f.getBoundingClientRect().bottom > vh + 1) out.push('buttons off screen');
  if (document.documentElement.scrollWidth > vw + 1) out.push('page scrolls sideways');
  const sc = document.querySelector('.scores'); const bd = document.querySelector('.board');
  if (sc && bd) { const last = [...bd.querySelectorAll('.tile')].pop().getBoundingClientRect(); if (last.bottom > sc.getBoundingClientRect().top + 1) out.push('board runs under score strip'); }
  return out;
}"""

async def main():
    errors, notes = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch()

        # --- A: a saved game from the old placeholder unit (4x4) must not be offered on this 5x5 unit
        ctx = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await ctx.new_page()
        page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        await page.goto(FILE)
        stale = {"screen": "board", "teams": [{"name": "A", "score": 300}, {"name": "B", "score": 100}], "played": [[True, True, False, False]] * 4, "picker": 0, "double": [1, 2], "cur": None, "lastSeat": 1, "endTime": None, "finalDone": False, "guardSnoozeUntil": 0, "count": 8}
        await page.evaluate("s => localStorage.setItem('reviewgame.v1', JSON.stringify(s))", stale)
        await page.reload(); await page.wait_for_timeout(400)
        notes.append(('stale 4x4 save offered?', await page.locator('[data-act="resume"]').count()))
        notes.append(('save key in use', await page.evaluate("Object.keys(localStorage)")))

        # --- B: end time set 45 minutes out -> what does the engine's own estimate say?
        from datetime import datetime, timedelta
        end = (datetime.now() + timedelta(minutes=45)).strftime('%H:%M')
        await page.fill('#endtime', end); await page.dispatch_event('#endtime', 'change'); await page.wait_for_timeout(200)
        notes.append(('estimate @45 min', (await page.inner_text('.est')).strip()))

        # --- C: huddle and boards-up phases on the widest question (Zero & Negative 300)
        await page.click('[data-act="start"]'); await page.wait_for_timeout(300)
        for r in range(3):
            await page.click('.tile.next[data-c="3"]')
            if await page.locator('.overlay .splash').count(): await page.click('.overlay')
            if r < 2:
                for a in ['solo', 'skipsolo', 'skiphuddle', 'reveal', 'award']: await page.click(f'[data-act="{a}"]')
        await page.click('[data-act="solo"]'); await page.click('[data-act="skipsolo"]'); await page.wait_for_timeout(2600)
        notes.append(('huddle phase', await page.evaluate(OVERLAP_JS))); await page.screenshot(path=f'{SHOTS}/huddle.png')
        await page.click('[data-act="skiphuddle"]'); await page.wait_for_timeout(300)
        notes.append(('boards phase', await page.evaluate(OVERLAP_JS))); await page.screenshot(path=f'{SHOTS}/boards.png')
        await page.click('[data-act="reveal"]'); await page.click('[data-act="award"]')
        await page.screenshot(path=f'{SHOTS}/board_midgame.png')
        notes.append(('board midgame', await page.evaluate(OVERLAP_JS)))

        # --- D: panel browser that is NOT full screen (tabs + address bar eat height), and an 8-team game
        for (w, h, tag) in [(1920, 940, 'windowed'), (1366, 768, 'laptop'), (1280, 1024, 'tall')]:
            await page.set_viewport_size({'width': w, 'height': h}); await page.wait_for_timeout(200)
            notes.append((f'board {tag} {w}x{h}', await page.evaluate(OVERLAP_JS)))
            await page.click('.tile.next[data-c="1"]')
            if await page.locator('.overlay .splash').count(): await page.click('.overlay')
            await page.click('[data-act="solo"]'); await page.wait_for_timeout(200)
            notes.append((f'timer {tag}', await page.evaluate(OVERLAP_JS)))
            for a in ['skipsolo', 'skiphuddle', 'reveal']: await page.click(f'[data-act="{a}"]')
            await page.wait_for_timeout(150)
            notes.append((f'answer {tag}', await page.evaluate(OVERLAP_JS)))
            if tag == 'windowed': await page.screenshot(path=f'{SHOTS}/answer_windowed.png')
            await page.click('[data-act="award"]')
        await ctx.close()

        # --- E: phone portrait (his preview device)
        ctx = await browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        page = await ctx.new_page()
        page.on('pageerror', lambda e: errors.append('PAGEERROR(phone) ' + str(e)))
        await page.goto(FILE); await page.wait_for_timeout(500)
        await page.screenshot(path=f'{SHOTS}/phone_setup.png')
        await page.tap('[data-act="start"]'); await page.wait_for_timeout(300)
        await page.screenshot(path=f'{SHOTS}/phone_board.png')
        notes.append(('phone board', await page.evaluate(OVERLAP_JS)))
        clip = await page.evaluate("() => [...document.querySelectorAll('.cat')].filter(c => c.scrollWidth > c.clientWidth + 1).map(c => c.textContent)")
        notes.append(('phone clipped category names', clip))
        # play column 2 (fractions) down to the 500
        for r in range(5):
            await page.tap('.tile.next[data-c="1"]')
            if await page.locator('.overlay .splash').count(): await page.tap('.overlay')
            await page.tap('[data-act="solo"]'); await page.wait_for_timeout(200)
            f1 = await page.evaluate(OVERLAP_JS)
            if r == 4: await page.screenshot(path=f'{SHOTS}/phone_timer.png')
            for a in ['skipsolo', 'skiphuddle', 'reveal']: await page.tap(f'[data-act="{a}"]')
            await page.wait_for_timeout(150)
            f2 = await page.evaluate(OVERLAP_JS)
            if r == 4: await page.screenshot(path=f'{SHOTS}/phone_answer.png')
            notes.append((f'phone q{r+1} timer/answer', f1, f2))
            await page.tap('[data-act="award"]')
        await ctx.close()

        # --- F: print: recording sheet and answer key as PDFs
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await ctx.new_page()
        await page.add_init_script("window.print = () => { window.__printed = (window.__printed || 0) + 1; }")
        await page.goto(FILE); await page.wait_for_timeout(400)
        await page.emulate_media(media='print')
        await page.click('[data-act="printsheet"]', force=True) if False else await page.evaluate("document.querySelector('[data-act=\"printsheet\"]').click()")
        await page.pdf(path=f'{SHOTS}/recording_sheet.pdf', format='Letter', prefer_css_page_size=True)
        await page.evaluate("document.querySelector('[data-act=\"printkey\"]').click()")
        await page.pdf(path=f'{SHOTS}/answer_key.pdf', format='Letter', prefer_css_page_size=True)
        notes.append(('print calls', await page.evaluate('window.__printed')))
        await browser.close()
    for n in notes: print(n)
    print('errors:', errors)
    info = ('save key in use', 'estimate @45 min', 'print calls')
    fails = [n for n in notes if n[0] not in info and any(x for x in n[1:])]
    if fails: print('FAILED:', fails)
    if fails or errors: sys.exit(1)

asyncio.run(main())
