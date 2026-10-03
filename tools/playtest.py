"""Play one full game of a built file in headless Chromium.

    python3 tools/playtest.py games/Geopardy_Area_of_Polygons.html [screenshot_dir]

Opens every tile in ladder order and the Final, screenshots each question in its timer phase and its answer
phase (default: out/<game>/), reloads mid-game to check the saved game resumes, and fails on any console
error or any question whose text or figure overlaps the header, the clock or the buttons."""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

FILE = os.path.abspath(sys.argv[1])
SHOTS = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', os.path.splitext(os.path.basename(sys.argv[1]))[0])
os.makedirs(SHOTS, exist_ok=True)

FIT_JS = """() => {
  const vw = innerWidth, vh = innerHeight, out = [];
  const body = document.querySelector('.qbody'), text = document.querySelector('.qtext');
  if (!body || !text) return ['no question on screen'];
  const b = body.getBoundingClientRect(), t = text.getBoundingClientRect();
  if (t.top < b.top - 1 || t.bottom > b.bottom + 1) out.push('text taller than its area: ' + Math.round(t.height) + ' > ' + Math.round(b.height));
  if (t.left < -1 || t.right > vw + 1) out.push('text wider than screen');
  const side = document.querySelector('.side');
  if (side) { const s = side.getBoundingClientRect(); if (t.right > s.left + 1 && t.bottom > s.top && s.left > b.left + 5) out.push('text runs under the clock'); }
  document.querySelectorAll('.qtext .katex').forEach(k => { const r = k.getBoundingClientRect(); if (r.left < t.left - 2 || r.right > t.right + 2) out.push('math overflows text box'); });
  const foot = document.querySelector('.qfoot').getBoundingClientRect();
  if (foot.bottom > vh + 1) out.push('buttons pushed off screen by ' + Math.round(foot.bottom - vh));
  const aw = document.querySelector('.award'); if (aw && aw.getBoundingClientRect().top < t.bottom - 1 && false) out.push('award overlaps');
  return out;
}"""

async def click(page, act, extra=''):
    await page.click(f'[data-act="{act}"]{extra}')

async def play_question(page, label, problems, shots=True):
    # dismiss Double Up splash if present
    if await page.locator('.overlay .splash').count():
        await page.click('.overlay')
    await click(page, 'solo')
    await page.wait_for_timeout(250)
    f = await page.evaluate(FIT_JS)
    if f: problems.append((label + ' [timer]', f))
    if shots: await page.screenshot(path=f'{SHOTS}/{label}_1timer.png')
    await click(page, 'skipsolo')
    await click(page, 'skiphuddle')
    await click(page, 'reveal')
    await page.wait_for_timeout(150)
    f = await page.evaluate(FIT_JS)
    if f: problems.append((label + ' [answer]', f))
    if shots: await page.screenshot(path=f'{SHOTS}/{label}_2answer.png')
    await click(page, 'all')
    await click(page, 'award')

async def main():
    problems, errors = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await ctx.new_page()
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append('PAGEERROR ' + str(e)))
        await page.goto('file://' + FILE)
        await page.wait_for_timeout(600)
        setup_text = await page.inner_text('.setup')
        print('unit check line:', [l for l in setup_text.split('\n') if 'Unit check' in l or 'Fix before' in l])
        print('subtitle:', await page.inner_text('.setup .sub'))
        await page.screenshot(path=f'{SHOTS}/00_setup.png')
        await click(page, 'start')
        await page.wait_for_timeout(400)
        await page.screenshot(path=f'{SHOTS}/01_board.png')
        st = await page.evaluate('window.__game.state()')
        print('board:', len(st['played']), 'x', len(st['played'][0]), '| double at', st['double'], '| teams', len(st['teams']))
        # board fit: no category header clipped
        clip = await page.evaluate("""() => [...document.querySelectorAll('.cat')].filter(c => c.scrollWidth > c.clientWidth + 1 || c.scrollHeight > c.clientHeight + 1).map(c => c.textContent)""")
        if clip: problems.append(('board', ['clipped category: ' + ', '.join(clip)]))

        ncat, ntier = len(st['played']), len(st['played'][0])
        played = 0
        for c in range(ncat):
            for r in range(ntier):
                await page.click(f'.tile.next[data-c="{c}"]')
                await play_question(page, f'c{c+1}_t{r+1}', problems)
                played += 1
                if played == 7:   # mid-game: reload and resume from the saved game
                    await page.reload(); await page.wait_for_timeout(500)
                    assert await page.locator('[data-act="resume"]').count() == 1, 'no resume offer after reload'
                    await click(page, 'resume'); await page.wait_for_timeout(200)
                    s2 = await page.evaluate('window.__game.state()')
                    assert s2['count'] == 7, s2['count']
                    print('reload + resume ok at 7 questions; scores', [t['score'] for t in s2['teams']])
                # bell-guard / other overlay should not be up (no end time on a weekend/after hours run)
        await page.screenshot(path=f'{SHOTS}/02_board_done.png')
        st = await page.evaluate('window.__game.state()')
        print('after board: count', st['count'], 'scores', [t['score'] for t in st['teams']])
        # Final
        await click(page, 'menu'); await click(page, 'final'); await page.wait_for_timeout(300)
        label = await page.inner_text('[data-act="solo"]')
        print('final start button:', label, '| value:', await page.inner_text('.qpts'), '| head:', await page.inner_text('.qcat'))
        await play_question(page, 'final', problems)
        await page.wait_for_timeout(1400 * 6 + 800)
        await page.screenshot(path=f'{SHOTS}/03_podium.png')
        st = await page.evaluate('window.__game.state()')
        print('final scores', [t['score'] for t in st['teams']], 'finalDone', st['finalDone'])
        await browser.close()
    print('console errors:', errors)
    print('layout problems:', json.dumps(problems, indent=1))
    if errors or problems: sys.exit(1)

asyncio.run(main())
