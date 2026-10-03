"""Render the printed recording sheet and answer key of a built file to PDF.

    python3 tools/printtest.py games/Geopardy_Area_of_Polygons.html [output_prefix]

Writes <prefix>_printkey.pdf and <prefix>_printsheet.pdf (default: out/<game>/print_...). Look at them:
this script only fails on page errors, it cannot judge the pages."""
import asyncio, os, sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for f, tag in [(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', os.path.splitext(os.path.basename(sys.argv[1]))[0]), 'print'))]:
            os.makedirs(os.path.dirname(os.path.abspath(tag)), exist_ok=True)
            page = await (await b.new_context(viewport={'width':1280,'height':800})).new_page()
            errs = []
            page.on('pageerror', lambda e: errs.append(str(e)))
            await page.add_init_script("window.print = () => { window.__printed = (window.__printed || 0) + 1; }")
            await page.goto('file://' + os.path.abspath(f)); await page.wait_for_timeout(300)
            await page.emulate_media(media='print')
            for act in ['printkey', 'printsheet']:
                await page.evaluate("window.__printed = 0")
                await page.evaluate(f"document.querySelector('[data-act=\"{act}\"]').click()")
                await page.wait_for_function("window.__printed === 1", timeout=5000)
                await page.pdf(path=f'{tag}_{act}.pdf', format='Letter', prefer_css_page_size=True)
            print(tag, 'errors', errs)
            if errs: sys.exit(1)
        await b.close()
asyncio.run(main())
