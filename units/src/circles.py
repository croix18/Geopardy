"""Circles unit (Grade 7 on-level: MA.7.GR.1.3 circumference, MA.7.GR.1.4 area; M7 lessons 4.05–4.10).

Writes units/circles.json:
    python3 units/src/circles.py

How an answer is made, so that question, figure, answer and worked step cannot drift apart:
  * every length is a variable; the figure's label is built from it and passed as `check=`, so the
    build fails if the drawn segment is not that long (figs.py);
  * every answer is COMPUTED from those variables with exact fractions (pi is 314/100 wherever the
    question says "Use 3.14", and stays a symbol where it says "in terms of pi") and the printed
    answer and every number in the worked step are formatted from the computed value, never typed;
  * every computed value is then compared with a value worked by hand (`expect`) — a second
    derivation, so a slip in the formula here does not pass silently;
  * shaded sectors are compared with the angle the figure actually draws;
  * no two questions in the unit share an answer.
Nothing is written if any of that fails.

The review day this game is played on comes before the unit test, and the test carries two
transfer items whose surfaces must not be rehearsed (HOUSE STYLE ruling 18): a bicycle wheel's
distance, and a walkway found by subtracting one area from another. Neither surface, and no
area-by-subtraction, appears here.
"""
import json, sys
from fractions import Fraction as F
from pathlib import Path
from figs import Fig, sector_area

PI = F(314, 100)
USE = r" Use $3.14$ for $\pi$."
problems = []


def expect(label, actual, by_hand):
    ok = F(actual) == F(str(by_hand))
    print(('ok  ' if ok else 'BAD ') + f'{label}: computed {fmt(actual)}, by hand {by_hand}')
    if not ok: problems.append(label)


def fmt(v):
    """An exact decimal string for a Fraction that terminates: 31.4, 706.5, 1,256 (LaTeX thousands)."""
    v = F(v)
    for places in range(0, 7):
        if (v * 10 ** places).denominator == 1:
            s = f'{float(v):,.{places}f}'
            return s.replace(',', '{,}')
    raise ValueError(f'{v} does not terminate within six places')


def U(v, unit):  return rf"${fmt(v)}\ \text{{{unit}}}$"
def SQ(v, unit): return rf"${fmt(v)}\ \text{{{unit}}}^2$"


def Q(q, a, work, fig=None):
    d = {"q": q, "a": a, "work": work}
    if fig is not None: d["fig"] = fig.svg()
    return d


# ---------------------------------------------------------------- figures
O = (0, 0)

def with_radius(r, label, cls=''):
    f = Fig().circle(O, r).seg(O, (r, 0)).dot(O)
    f.edge(O, (r, 0), label, toward=(r / 2, r), check=None if cls else r, cls=cls)
    return f

def with_diameter(d, label, cls=''):
    r = d / 2
    f = Fig().circle(O, r).seg((-r, 0), (r, 0)).dot(O)
    f.edge((-r, 0), (r, 0), label, toward=(0, r), check=None if cls else d, cls=cls)
    return f

def around(f, r, text):
    """The circumference written over the top of the circle."""
    return f.text((0, r), text, dy=-30)


# =====================================================================================
# 1. RADIUS & DIAMETER  (4.05)
# =====================================================================================
def c1():
    out = []
    r = 7; d = 2 * r
    expect('C1-100', d, 14)
    out.append(Q("Find the diameter of the circle.", U(d, 'cm'),
                 rf"The diameter is two radii: $2 \cdot {r} = {fmt(d)}$.", with_radius(r, f'{r} cm')))

    d = 9; r = F(d, 2)
    expect('C1-200', r, 4.5)
    out.append(Q("Find the radius of the circle.", U(r, 'in'),
                 rf"The radius is half the diameter: ${d} \div 2 = {fmt(r)}$.", with_diameter(d, f'{d} in')))

    C, d = F('31.4'), 10
    ratio = C / d
    expect('C1-300', ratio, 3.14)
    out.append(Q(rf"A lid measures ${fmt(C)}$ cm around and ${d}$ cm across. What is the distance around divided by the distance across?",
                 rf"${fmt(ratio)}$",
                 rf"${fmt(C)} \div {d} = {fmt(ratio)}$. For every circle, circumference $\div$ diameter is $\pi$, about $3.14$.",
                 around(with_diameter(d, f'{d} cm'), d / 2, f'{fmt(C)} cm around')))

    d = 34; r = F(d, 2)
    expect('C1-400', r, 17)
    f = Fig().circle(O, d / 2).seg((-d / 2, 0), (d / 2, 0)).dot(O)
    f.edge((-d / 2, 0), (d / 2, 0), f'{d} m', toward=(0, -d / 2), check=d)
    f.edge(O, (d / 2, 0), '?', toward=(d / 4, d / 2), cls='fu')
    out.append(Q(rf"A segment through the center of the circle is ${d}$ m long. How far is it from the center to the circle?",
                 U(r, 'm'), rf"A segment through the center is a diameter. Center to circle is a radius: ${d} \div 2 = {fmt(r)}$.", f))

    side = 18; r = F(side, 2)
    expect('C1-500', r, 9)
    h = side / 2
    sq = [(-h, -h), (h, -h), (h, h), (-h, h)]
    f = Fig().poly(sq, cls='fm').circle(O, h).dot(O)
    f.edge(sq[0], sq[1], f'{side} cm', away=O, check=side)
    out.append(Q(rf"The largest possible circle is cut from a square card ${side}$ cm on a side. What is the radius of the circle?",
                 U(r, 'cm'),
                 rf"The circle is as wide as the card, so its diameter is ${side}$. The radius is half: ${side} \div 2 = {fmt(r)}$.", f))
    return out


# =====================================================================================
# 2. CIRCUMFERENCE  (4.06)
# =====================================================================================
def c2():
    out = []
    d = 10; C = PI * d
    expect('C2-100', C, 31.4)
    out.append(Q("Find the circumference." + USE, U(C, 'cm'),
                 rf"$C = \pi d = 3.14 \cdot {d} = {fmt(C)}$.", with_diameter(d, f'{d} cm')))

    r = 4; C = 2 * PI * r
    expect('C2-200', C, 25.12)
    out.append(Q("Find the circumference." + USE, U(C, 'in'),
                 rf"The figure gives the radius: $C = 2\pi r = 2 \cdot 3.14 \cdot {r} = {fmt(C)}$.", with_radius(r, f'{r} in')))

    d = F('6.5'); C = PI * d
    expect('C2-300', C, 20.41)
    out.append(Q("Find the circumference." + USE, U(C, 'm'),
                 rf"$C = \pi d = 3.14 \cdot {fmt(d)} = {fmt(C)}$.", with_diameter(float(d), f'{fmt(d)} m')))

    r = 9; k = 2 * r                                   # C = k pi, exactly
    expect('C2-400 (coefficient of pi)', k, 18)
    out.append(Q(r"Find the exact circumference, in terms of $\pi$.", rf"${k}\pi\ \text{{ft}}$",
                 rf"$C = 2\pi r = 2 \cdot \pi \cdot {r} = {k}\pi$. Exact means $\pi$ stays in the answer.", with_radius(r, f'{r} ft')))

    d, laps = 50, 4; one = PI * d; total = one * laps
    expect('C2-500 one lap', one, 157); expect('C2-500', total, 628)
    out.append(Q(rf"A circular track is ${d}$ m across. How far is ${laps}$ laps around it?" + USE, U(total, 'm'),
                 rf"One lap is the circumference: $3.14 \cdot {d} = {fmt(one)}$. Then ${fmt(one)} \cdot {laps} = {fmt(total)}$.",
                 with_diameter(d, f'{d} m')))
    return out


# =====================================================================================
# 3. WORKING BACKWARDS  (4.07)
# =====================================================================================
def c3():
    out = []
    C = F('15.7'); d = C / PI
    expect('C3-100', d, 5)
    out.append(Q(rf"The circumference of the circle is ${fmt(C)}$ cm. Find the diameter." + USE, U(d, 'cm'),
                 rf"$C = \pi d$, so $d = C \div \pi = {fmt(C)} \div 3.14 = {fmt(d)}$.",
                 around(with_diameter(float(d), '?', cls='fu'), float(d) / 2, f'C = {fmt(C)} cm')))

    C = F('62.8'); d = C / PI; r = d / 2
    expect('C3-200 d', d, 20); expect('C3-200', r, 10)
    out.append(Q(rf"The circumference of the circle is ${fmt(C)}$ in. Find the radius." + USE, U(r, 'in'),
                 rf"Diameter first: ${fmt(C)} \div 3.14 = {fmt(d)}$. The radius is half: ${fmt(d)} \div 2 = {fmt(r)}$.",
                 around(with_radius(float(r), '?', cls='fu'), float(r), f'C = {fmt(C)} in')))

    k = 26; d = k; r = F(d, 2)                         # C = 26 pi exactly, so d = 26
    expect('C3-300', r, 13)
    out.append(Q(rf"The circumference of the circle is exactly ${k}\pi$ m. Find the radius.", U(r, 'm'),
                 rf"$C = \pi d$, so the diameter is ${k}$. The radius is half: ${k} \div 2 = {fmt(r)}$.",
                 around(with_radius(float(r), '?', cls='fu'), float(r), f'C = {k}π m')))

    C = F('47.1'); d = C / PI; r = d / 2
    expect('C3-400 d', d, 15); expect('C3-400', r, 7.5)
    out.append(Q(rf"The circumference of the circle is ${fmt(C)}$ ft. Find the radius." + USE, U(r, 'ft'),
                 rf"Diameter first: ${fmt(C)} \div 3.14 = {fmt(d)}$. The radius is half: ${fmt(d)} \div 2 = {fmt(r)}$.",
                 around(with_radius(float(r), '?', cls='fu'), float(r), f'C = {fmt(C)} ft')))

    C = F('219.8'); d = C / PI
    expect('C3-500', d, 70)
    out.append(Q(rf"A rope ${fmt(C)}$ m long fits exactly once around the edge of a circular pond. How far is it straight across the pond, through the center?" + USE,
                 U(d, 'm'),
                 rf"The rope is the circumference, and straight across is the diameter: ${fmt(C)} \div 3.14 = {fmt(d)}$.",
                 around(with_diameter(float(d), '?', cls='fu'), float(d) / 2, f'rope: {fmt(C)} m')))
    return out


# =====================================================================================
# 4. AREA  (4.08, 4.09)
# =====================================================================================
def c4():
    out = []
    r = 2; A = PI * r * r
    expect('C4-100', A, 12.56)
    out.append(Q("Find the area of the circle." + USE, SQ(A, 'cm'),
                 rf"$A = \pi r^2 = 3.14 \cdot {r} \cdot {r} = {fmt(A)}$.", with_radius(r, f'{r} cm')))

    d = 8; r = F(d, 2); A = PI * r * r
    expect('C4-200 r', r, 4); expect('C4-200', A, 50.24)
    out.append(Q("Find the area of the circle." + USE, SQ(A, 'in'),
                 rf"The figure gives the diameter, so the radius is ${d} \div 2 = {fmt(r)}$. Then $3.14 \cdot {fmt(r)} \cdot {fmt(r)} = {fmt(A)}$.",
                 with_diameter(d, f'{d} in')))

    r = 6; k = r * r                                   # A = k pi, exactly
    expect('C4-300 (coefficient of pi)', k, 36)
    out.append(Q(r"Find the exact area of the circle, in terms of $\pi$.", rf"${k}\pi\ \text{{ft}}^2$",
                 rf"$A = \pi r^2 = \pi \cdot {r} \cdot {r} = {k}\pi$. Exact means $\pi$ stays in the answer.", with_radius(r, f'{r} ft')))

    d = 12; r = F(d, 2); whole = PI * r * r; A = whole / 2
    expect('C4-400 r', r, 6); expect('C4-400 whole', whole, 113.04); expect('C4-400', A, 56.52)
    expect('C4-400 figure is half a circle', F(sector_area(float(r), 0, 180)).limit_denominator(1000), r * r / 2)
    f = Fig().sector(O, float(r), 0, 180)
    f.edge((-float(r), 0), (float(r), 0), f'{d} cm', toward=(0, -float(r)), check=d)
    out.append(Q("Find the area of the half circle." + USE, SQ(A, 'cm'),
                 rf"The radius is ${d} \div 2 = {fmt(r)}$. A whole circle would be $3.14 \cdot {fmt(r)} \cdot {fmt(r)} = {fmt(whole)}$, and half of that is ${fmt(A)}$.", f))

    r = 10; whole = PI * r * r; A = whole * F(3, 4)
    expect('C4-500 whole', whole, 314); expect('C4-500', A, 235.5)
    expect('C4-500 figure is three quarters of a circle', F(sector_area(r, 0, 270)).limit_denominator(1000), F(3, 4) * r * r)
    f = Fig().circle(O, r, cls='fm').sector(O, r, 0, 270)
    f.right_angle(O, (r, 0), (0, -r))
    f.edge(O, (r, 0), f'{r} m', toward=(r / 2, -r), check=r)
    out.append(Q("One quarter of the circle is cut away. Find the shaded area." + USE, SQ(A, 'm'),
                 rf"The whole circle is $3.14 \cdot {r} \cdot {r} = {fmt(whole)}$. Three quarters are left: ${fmt(whole)} \div 4 \cdot 3 = {fmt(A)}$.", f))
    return out


# =====================================================================================
# 5. CIRCUMFERENCE OR AREA?  (4.10)
# =====================================================================================
def c5():
    out = []
    r = 3; A = PI * r * r
    expect('C5-100', A, 28.26)
    out.append(Q(rf"A circular rug has a radius of ${r}$ ft. How much floor does it cover?" + USE, SQ(A, 'ft'),
                 rf"Covering a surface is area: $3.14 \cdot {r} \cdot {r} = {fmt(A)}$."))

    d = 40; C = PI * d
    expect('C5-200', C, 125.6)
    out.append(Q(rf"Ribbon is glued around the edge of a circular mirror that is ${d}$ cm across. How long is the ribbon?" + USE, U(C, 'cm'),
                 rf"Around the edge is circumference: $3.14 \cdot {d} = {fmt(C)}$."))

    r = 5; A = PI * r * r
    expect('C5-300', A, 78.5)
    out.append(Q(rf"A sprinkler waters all the lawn within ${r}$ m of it. How much lawn does it water?" + USE, SQ(A, 'm'),
                 rf"The lawn it reaches is a circle with radius ${r}$, and how much lawn is area: $3.14 \cdot {r} \cdot {r} = {fmt(A)}$."))

    d, n = 20, 8; r = F(d, 2); whole = PI * r * r; A = whole / n
    expect('C5-400 whole', whole, 314); expect('C5-400', A, 39.25)
    out.append(Q(rf"A pizza ${d}$ in. across is cut into ${n}$ equal slices. What is the area of one slice?" + USE, SQ(A, 'in'),
                 rf"The radius is ${fmt(r)}$, so the whole pizza is $3.14 \cdot {fmt(r)} \cdot {fmt(r)} = {fmt(whole)}$. One slice: ${fmt(whole)} \div {n} = {fmt(A)}$."))

    d, rate = 10, 6; C = PI * d; cost = C * rate
    expect('C5-500 fence', C, 31.4); expect('C5-500', cost, 188.4)
    out.append(Q(rf"A circular garden is ${d}$ m across. Fencing to go around it costs \${rate} per meter. What does the fence cost?" + USE,
                 rf"\${float(cost):.2f}",
                 rf"A fence goes around, so find the circumference: $3.14 \cdot {d} = {fmt(C)}$ m. Then ${fmt(C)} \cdot {rate} = {float(cost):.2f}$."))
    return out


def final():
    C = F('94.2'); d = C / PI; r = d / 2; A = PI * r * r
    expect('Final d', d, 30); expect('Final r', r, 15); expect('Final', A, 706.5)
    q = Q(rf"The edge of a circular pond is ${fmt(C)}$ m long. Find the area of the pond's surface." + USE, SQ(A, 'm'),
          rf"Work back to the radius: ${fmt(C)} \div 3.14 = {fmt(d)}$ across, so $r = {fmt(r)}$. Then $A = 3.14 \cdot {fmt(r)} \cdot {fmt(r)} = {fmt(A)}$.")
    return {"category": "Around, Then Inside", "solo": 90, **q}


unit = {
    "title": "Circles",
    "course": "Grade 7 Math",
    "tiers": [100, 200, 300, 400, 500],
    "tierNotes": ["Warm-up", "Radius or diameter?", "Decimals and exact", "Two steps", "Challenge"],
    "categories": [
        {"name": "Radius & Diameter", "questions": c1()},
        {"name": "Circumference", "questions": c2()},
        {"name": "Working Backwards", "questions": c3()},
        {"name": "Area", "questions": c4()},
        {"name": "Circumference or Area?", "questions": c5()},
    ],
    "final": final(),
}
assert all(len(c["questions"]) == 5 for c in unit["categories"])
answers = [q["a"] for c in unit["categories"] for q in c["questions"]] + [unit["final"]["a"]]
shared = sorted({a for a in answers if answers.count(a) > 1})
if shared:
    problems.append(f'answers shared by two questions: {shared}')
banned = [w for w in ('wheel', 'walkway', 'bicycle', 'bike') for c in unit["categories"] for q in c["questions"] if w in q["q"].lower()]
if banned:
    problems.append(f'a transfer surface is rehearsed: {sorted(set(banned))}')
if problems: sys.exit(f"not written: {problems}")
out = Path(__file__).resolve().parent.parent / "circles.json"
out.write_text(json.dumps(unit, indent=1, ensure_ascii=True) + "\n")
print('problems:', problems, '| questions:', len(answers), '| distinct answers:', len(set(answers)),
      '| figures:', sum(1 for c in unit["categories"] for q in c["questions"] if q.get("fig")))
