#!/usr/bin/env python3
"""Assemble a single-file Geopardy game from the engine parts and one unit.

    python3 tools/build.py                      # every unit in units/ (files starting with _ are skipped)
    python3 tools/build.py units/area_of_polygons.json
    python3 tools/build.py units/_placeholder.json -o /tmp/sample.html

The output is one self-contained HTML file in games/: no network requests, so it runs from a Drive
folder or a USB stick over file://. Everything in engine/ is included verbatim; the build adds nothing
of its own, which is why the same inputs always give the same bytes.
"""
import argparse, base64, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE, UNITS, GAMES = ROOT / 'engine', ROOT / 'units', ROOT / 'games'
SMALL_WORDS = {'of', 'and', 'the', 'a', 'an', 'to', 'in', 'on', 'for'}


def game_name(unit_path):
    """units/area_of_polygons.json -> Geopardy_Area_of_Polygons.html"""
    words = unit_path.stem.strip('_').split('_')
    return 'Geopardy_' + '_'.join(w if w in SMALL_WORDS and i else w.capitalize() for i, w in enumerate(words)) + '.html'


def check_unit(unit, where):
    """Shape checks only. The game re-checks that every string's math renders (setup screen: "Unit check")."""
    bad = []
    for key in ('title', 'tiers', 'categories', 'final'):
        if key not in unit: bad.append(f'missing "{key}"')
    if bad: sys.exit(f'{where}: ' + '; '.join(bad))
    n = len(unit['tiers'])
    if not 1 <= n <= 5: bad.append(f'{n} tiers (the solo timer table covers 1 to 5)')
    for c in unit['categories']:
        if len(c['questions']) != n: bad.append(f'{c["name"]}: {len(c["questions"])} questions, needs {n}')
        for q in c['questions']:
            if not q.get('q') or not q.get('a'): bad.append(f'{c["name"]}: a question is missing "q" or "a"')
    if not unit['final'].get('q') or not unit['final'].get('a'): bad.append('final: missing "q" or "a"')
    if bad: sys.exit(f'{where}: ' + '; '.join(bad))


def build(unit_path, out_path=None):
    unit = json.loads(unit_path.read_text(encoding='utf-8'))
    check_unit(unit, unit_path.name)
    unit_json = json.dumps(unit, ensure_ascii=True)
    assert '</script' not in unit_json.lower(), 'a unit string contains "</script"'

    html = (ENGINE / 'index.html').read_text(encoding='utf-8')
    def include(m): return (ENGINE / m.group(1)).read_text(encoding='utf-8')
    def audio(m): return base64.b64encode((ENGINE / m.group(1)).read_bytes()).decode('ascii')
    # one pass per marker kind, so text inside an included file is never treated as a marker
    parts = re.split(r'(\{\{(?:include|audio) [^}]+\}\}|\{\{unit\}\}|\{\{title\}\})', html)
    for i, p in enumerate(parts):
        m = re.fullmatch(r'\{\{include ([^}]+)\}\}', p)
        if m: parts[i] = include(m); continue
        m = re.fullmatch(r'\{\{audio ([^}]+)\}\}', p)
        if m: parts[i] = audio(m); continue
        if p == '{{unit}}': parts[i] = unit_json
        elif p == '{{title}}': parts[i] = 'Geopardy! ' + unit['title']
    out = ''.join(parts)

    out_path = Path(out_path) if out_path else GAMES / game_name(unit_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out, encoding='utf-8', newline='')
    shown = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
    print(f'{shown}  {len(out.encode("utf-8")) / 1e6:.2f} MB  '
          f'({len(unit["categories"])} x {len(unit["tiers"])} + final, "{unit["title"]}")')
    return out_path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('units', nargs='*', type=Path, help='unit JSON files (default: all in units/ not starting with _)')
    ap.add_argument('-o', '--out', help='output path (only with a single unit)')
    a = ap.parse_args()
    units = a.units or sorted(p for p in UNITS.glob('*.json') if not p.name.startswith('_'))
    if a.out and len(units) != 1: sys.exit('-o needs exactly one unit')
    for u in units: build(u.resolve(), a.out)
