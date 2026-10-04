"""Samples & Scale unit (Grade 7 on-level: MA.7.DP.1.3 predictions from a random sample,
MA.7.GR.1.5 scale factors and scale drawings; M7 lessons 5.01–5.10).

Writes units/samples_and_scale.json:
    python3 units/src/samples_and_scale.py

How an answer is made, so that question, answer and worked step cannot drift apart:
  * every quantity in a question is a variable, and the question's wording is built from it;
  * every answer is COMPUTED from those variables with exact fractions, and the printed answer and
    every number in the worked step are formatted from the computed value, never typed;
  * every computed value is then compared with a value worked by hand (`expect`) — a second
    derivation, so a slip in the set-up here does not pass silently;
  * a prediction must come out a whole number (nobody predicts 96.4 students), a plan's rectangle
    is drawn from the same numbers its labels print (figs.py `check=`);
  * no two questions in the unit share an answer.
Nothing is written if any of that fails.

The review day this game is played on comes before the unit test, and the test carries two
transfer items whose surfaces must not be rehearsed (HOUSE STYLE ruling 18): a sample fraction
given as a decimal, and a model at a scale of 1 : N whose real length must be changed to
centimeters first. No sample fraction here is a decimal, and no question is about a model.
"""
import json, re, sys
from fractions import Fraction as F
from pathlib import Path
from figs import Fig, shoelace

problems = []


def expect(label, actual, by_hand):
    ok = F(actual) == F(str(by_hand))
    print(('ok  ' if ok else 'BAD ') + f'{label}: computed {actual}, by hand {by_hand}')
    if not ok: problems.append(label)


def whole(label, v):
    if F(v).denominator != 1: problems.append(f'{label}: {v} is not a whole number')
    return int(v)


def n(v):
    """A whole number or a terminating decimal, with LaTeX thousands: 2{,}800, 2.5."""
    v = F(v)
    for places in range(0, 5):
        if (v * 10 ** places).denominator == 1:
            return f'{float(v):,.{places}f}'.replace(',', '{,}')
    raise ValueError(f'{v} does not terminate')


def frac(v):
    v = F(v)
    return rf"\frac{{{v.numerator}}}{{{v.denominator}}}"


def Q(q, a, work, fig=None):
    d = {"q": q, "a": a, "work": work}
    if fig is not None: d["fig"] = fig.svg()
    return d


def plan(w, h, wl, hl):
    """A rectangle w by h (plan units), its sides labelled; the labels are held to the drawing."""
    pts = [(0, 0), (w, 0), (w, h), (0, h)]
    f = Fig(max_h=200).poly(pts)
    for i in range(4): f.right_angle(pts[i], pts[i - 1], pts[(i + 1) % 4])
    f.edge(pts[0], pts[1], wl, check=w).edge(pts[3], pts[0], hl, check=h)
    return f, shoelace(pts)


# =====================================================================================
# 1. SAMPLE OR POPULATION?  (5.01)
# =====================================================================================
def c1():
    out = []
    pop, samp = 900, 60
    expect('C1-100', samp, 60)
    out.append(Q(rf"A school has ${pop}$ students. The principal asks ${samp}$ of them about lunch. How many students are in the sample?",
                 rf"${samp}$ students",
                 rf"The sample is the group that was actually asked: ${samp}$. The population is all ${pop}$."))

    pop, samp = 5000, 200
    expect('C1-200', pop, 5000)
    out.append(Q(rf"A factory makes ${n(pop)}$ phones in a day. An inspector tests ${samp}$ of them. How many phones are in the population?",
                 rf"${n(pop)}$ phones",
                 rf"The population is the whole group the inspector wants to know about: all ${n(pop)}$. The ${samp}$ tested are the sample."))

    samp, part = 40, 10; v = F(part, samp)
    expect('C1-300', v, '1/4')
    out.append(Q(rf"In a random sample of ${samp}$ students, ${part}$ walk to school. What fraction of the sample walks? Write it in lowest terms.",
                 rf"${frac(v)}$",
                 rf"Part of the sample over the whole sample: $\frac{{{part}}}{{{samp}}} = {frac(v)}$."))

    pop, samp = 800, 30
    out.append(Q(rf"A librarian wants to know the favorite kind of book of all ${pop}$ students. Which plan gives a random sample?" "\n"
                 rf"Plan A: ask the ${samp}$ students in the book club." "\n"
                 rf"Plan B: draw ${samp}$ student numbers from all ${pop}$.",
                 "Plan B",
                 rf"In Plan B every one of the ${pop}$ students has the same chance of being drawn. The book club is not like the whole school."))

    samp, pct = 80, 30; v = F(pct, 100) * samp
    expect('C1-500', v, 24)
    out.append(Q(rf"In a random sample of ${samp}$ students, ${pct}\%$ chose soccer. How many students in the sample chose soccer?",
                 rf"${whole('C1-500', v)}$ students",
                 rf"${pct}\%$ of the sample: $0.{pct} \cdot {samp} = {n(v)}$."))
    return out


# =====================================================================================
# 2. PROBABILITY FROM DATA  (5.02)
# =====================================================================================
def c2():
    out = []
    hits, trials = 12, 40; v = F(hits, trials)
    expect('C2-100', v, '3/10')
    out.append(Q(rf"A spinner landed on red ${hits}$ times in ${trials}$ spins. What fraction of the spins were red? Write it in lowest terms.",
                 rf"${frac(v)}$", rf"Reds over all spins: $\frac{{{hits}}}{{{trials}}} = {frac(v)}$."))

    hits, trials, future = 10, 50, 300; f = F(hits, trials); v = f * future
    expect('C2-200 fraction', f, '1/5'); expect('C2-200', v, 60)
    out.append(Q(rf"A number cube was rolled ${trials}$ times and showed a 4 on ${hits}$ of the rolls. It will be rolled ${future}$ more times. Use these results to predict the number of 4s.",
                 rf"About ${whole('C2-200', v)}$",
                 rf"The trial says $\frac{{{hits}}}{{{trials}}} = {frac(f)}$ of the rolls. Then ${frac(f)} \cdot {future} = {n(v)}$."))

    hits, trials, future = 27, 60, 400; f = F(hits, trials); v = f * future
    expect('C2-300 fraction', f, '9/20'); expect('C2-300', v, 180)
    out.append(Q(rf"A coin landed heads ${hits}$ times in ${trials}$ flips. Use these results to predict the number of heads in ${future}$ more flips.",
                 rf"About ${whole('C2-300', v)}$",
                 rf"Use what happened, not what should happen: $\frac{{{hits}}}{{{trials}}} = {frac(f)}$. Then ${frac(f)} \cdot {future} = {n(v)}$."))

    pct, future = 35, 600; v = F(pct, 100) * future
    expect('C2-400', v, 210)
    out.append(Q(rf"In a trial, ${pct}\%$ of the seeds sprouted. Tomorrow ${future}$ seeds will be planted. Use the trial to predict the number that sprout.",
                 rf"About ${whole('C2-400', v)}$ seeds",
                 rf"${pct}\%$ of ${future}$: $0.{pct} \cdot {future} = {n(v)}$."))

    blue, draws, future = 28, 80, 200; notblue = draws - blue; f = F(notblue, draws); v = f * future
    expect('C2-500 not blue', notblue, 52); expect('C2-500 fraction', f, '13/20'); expect('C2-500', v, 130)
    out.append(Q(rf"A marble is drawn from a bag and put back, ${draws}$ times. ${blue}$ of the draws were blue. Use these results to predict how many of the next ${future}$ draws will NOT be blue.",
                 rf"About ${whole('C2-500', v)}$",
                 rf"Not blue: ${draws} - {blue} = {notblue}$ of the ${draws}$ draws, and $\frac{{{notblue}}}{{{draws}}} = {frac(f)}$. Then ${frac(f)} \cdot {future} = {n(v)}$."))
    return out


# =====================================================================================
# 3. PREDICT THE POPULATION  (5.03, 5.04)
# =====================================================================================
def c3():
    out = []
    part, samp, pop = 8, 50, 600; f = F(part, samp); v = f * pop
    expect('C3-100 fraction', f, '4/25'); expect('C3-100', v, 96)
    out.append(Q(rf"In a random sample of ${samp}$ students, ${part}$ ride a bike to school. The school has ${pop}$ students. Predict how many ride a bike.",
                 rf"About ${whole('C3-100', v)}$ students",
                 rf"The sample fraction times the population: $\frac{{{part}}}{{{samp}}} \cdot {pop} = {n(v)}$."))

    part, samp, pop = 6, 200, 3000; f = F(part, samp); v = f * pop
    expect('C3-200 fraction', f, '3/100'); expect('C3-200', v, 90)
    out.append(Q(rf"In a random sample of ${samp}$ light bulbs, ${part}$ are faulty. A shipment holds ${n(pop)}$ bulbs. Predict the number of faulty bulbs in the shipment.",
                 rf"About ${whole('C3-200', v)}$ bulbs",
                 rf"$\frac{{{part}}}{{{samp}}} = {frac(f)}$ of the sample is faulty. Then ${frac(f)} \cdot {n(pop)} = {n(v)}$."))

    samp, pct, pop = 250, 40, 7000; v = F(pct, 100) * pop
    expect('C3-300', v, 2800)
    out.append(Q(rf"In a random sample of ${samp}$ voters, ${pct}\%$ say yes. The town has ${n(pop)}$ voters. Predict how many of them would say yes.",
                 rf"About ${n(whole('C3-300', v))}$ voters",
                 rf"The percent goes with the population, not with the ${samp}$: $0.{pct} \cdot {n(pop)} = {n(v)}$."))

    part, pct = 14, 20; v = F(part) / F(pct, 100)
    expect('C3-400', v, 70)
    out.append(Q(rf"${part}$ students in a club are seventh graders. That is ${pct}\%$ of the club. How many students are in the club?",
                 rf"${whole('C3-400', v)}$ students",
                 rf"This time the whole group is missing: ${pct}\%$ of the club is ${part}$, so the club is ${part} \div 0.{pct} = {n(v)}$."))

    tagged, caught, found = 30, 120, 9; f = F(found, caught); v = F(tagged) / f
    expect('C3-500 fraction', f, '3/40'); expect('C3-500', v, 400)
    out.append(Q(rf"A ranger tags ${tagged}$ turtles and lets them go. Later she catches ${caught}$ turtles at random, and ${found}$ of them are tagged. Estimate the number of turtles in the pond.",
                 rf"About ${whole('C3-500', v)}$ turtles",
                 rf"$\frac{{{found}}}{{{caught}}} = {frac(f)}$ of the second catch is tagged, so the ${tagged}$ tagged turtles are about ${frac(f)}$ of the pond: ${tagged} \div {frac(f)} = {n(v)}$."))
    return out


# =====================================================================================
# 4. SCALE FACTOR  (5.05, 5.06, 5.07)
# =====================================================================================
def c4():
    out = []
    a, b = 4, 12; k = F(b, a)
    expect('C4-100', k, 3)
    out.append(Q(rf"A side that is ${a}$ cm long is ${b}$ cm long in the scaled copy. Find the scale factor.",
                 rf"${n(k)}$", rf"Copy over original: ${b} \div {a} = {n(k)}$."))

    per, k = 30, F('2.5'); v = per * k
    expect('C4-200', v, 75)
    out.append(Q(rf"A triangle has a perimeter of ${per}$ cm. It is redrawn with a scale factor of ${n(k)}$. Find the perimeter of the copy.",
                 rf"${n(v)}\ \text{{cm}}$", rf"Every side is multiplied by ${n(k)}$, so the perimeter is too: ${per} \cdot {n(k)} = {n(v)}$."))

    area, k = 15, 4; v = area * k * k
    expect('C4-300', v, 240)
    out.append(Q(rf"A rectangle has an area of ${area}\ \text{{cm}}^2$. It is redrawn with a scale factor of ${k}$. Find the area of the copy.",
                 rf"${n(v)}\ \text{{cm}}^2$",
                 rf"Length and width are both multiplied by ${k}$, so the area is multiplied by ${k} \cdot {k} = {k * k}$: ${area} \cdot {k * k} = {n(v)}$."))

    per, k = 48, F(1, 4); v = per * k
    expect('C4-400', v, 12)
    out.append(Q(rf"A shape has a perimeter of ${per}$ in. It is redrawn with a scale factor of ${frac(k)}$. Find the new perimeter.",
                 rf"${n(v)}\ \text{{in}}$", rf"A scale factor less than 1 shrinks it: ${per} \cdot {frac(k)} = {n(v)}$."))

    p0, p1, area = 12, 60, 8; k = F(p1, p0); v = area * k * k
    expect('C4-500 k', k, 5); expect('C4-500', v, 200)
    out.append(Q(rf"A figure's perimeter goes from ${p0}$ cm to ${p1}$ cm when it is scaled. Its original area is ${area}\ \text{{cm}}^2$. Find the area of the copy.",
                 rf"${n(v)}\ \text{{cm}}^2$",
                 rf"The scale factor is ${p1} \div {p0} = {n(k)}$. Area uses it twice: ${area} \cdot {n(k)} \cdot {n(k)} = {n(v)}$."))
    return out


# =====================================================================================
# 5. SCALE DRAWINGS  (5.08, 5.09, 5.10)
# =====================================================================================
def c5():
    out = []
    per, on_plan = 5, 9; v = per * on_plan
    expect('C5-100', v, 45)
    out.append(Q(rf"A plan uses the scale 1 in. : ${per}$ ft. A wall is ${on_plan}$ in. long on the plan. How long is the real wall?",
                 rf"${n(v)}\ \text{{ft}}$", rf"Each inch on the plan is ${per}$ ft: ${on_plan} \cdot {per} = {n(v)}$."))

    per, real = 20, 160; v = F(real, per)
    expect('C5-200', v, 8)
    out.append(Q(rf"A map uses the scale 1 cm : ${per}$ km. Two towns are really ${real}$ km apart. How far apart are they on the map?",
                 rf"${n(v)}\ \text{{cm}}$", rf"Going from real to map, divide: ${real} \div {per} = {n(v)}$."))

    m = 5; k = m * 100
    expect('C5-300', k, 500)
    out.append(Q(rf"A plan uses the scale 1 cm : ${m}$ m. What is the scale factor from the plan to the real thing?",
                 rf"${n(k)}$", rf"Put both in the same unit first: ${m}$ m is ${n(k)}$ cm. So 1 cm stands for ${n(k)}$ cm, and the scale factor is ${n(k)}$."))

    per, w, h = 4, 6, 5; W, H = w * per, h * per; v = W * H
    f, drawn = plan(w, h, f'{w} in', f'{h} in')
    expect('C5-400 sides', W, 24); expect('C5-400 sides', H, 20); expect('C5-400', v, 480)
    expect('C5-400 figure is the plan', F(drawn).limit_denominator(1000), w * h)
    out.append(Q(rf"A plan uses the scale 1 in. : ${per}$ ft. This room is ${w}$ in. by ${h}$ in. on the plan. Find the room's real area.",
                 rf"${n(v)}\ \text{{ft}}^2$",
                 rf"Scale each side first: ${w} \cdot {per} = {W}$ ft and ${h} \cdot {per} = {H}$ ft. Then ${W} \cdot {H} = {n(v)}$.", f))

    per, W, H = 6, 30, 18; w, h = F(W, per), F(H, per); v = w * h
    expect('C5-500 sides', w, 5); expect('C5-500 sides', h, 3); expect('C5-500', v, 15)
    out.append(Q(rf"A real garden is ${W}$ ft by ${H}$ ft. A plan of it uses the scale 1 in. : ${per}$ ft. Find the garden's area on the plan.",
                 rf"${n(v)}\ \text{{in}}^2$",
                 rf"Scale each side down first: ${W} \div {per} = {n(w)}$ in. and ${H} \div {per} = {n(h)}$ in. Then ${n(w)} \cdot {n(h)} = {n(v)}$."))
    return out


def final():
    per, w, h = 8, 10, 6; W, H = w * per, h * per; v = W * H
    f, drawn = plan(w, h, f'{w} in', f'{h} in')
    expect('Final sides', W, 80); expect('Final sides', H, 48); expect('Final', v, 3840)
    expect('Final by the area rule', w * h * per * per, 3840)
    expect('Final figure is the plan', F(drawn).limit_denominator(1000), w * h)
    q = Q(rf"A plan uses the scale 1 in. : ${per}$ ft. On the plan, this gym floor is ${w}$ in. by ${h}$ in. Find the real area of the gym floor.",
          rf"${n(v)}\ \text{{ft}}^2$",
          rf"Scale each side first: ${w} \cdot {per} = {W}$ ft and ${h} \cdot {per} = {H}$ ft. Then ${W} \cdot {H} = {n(v)}$. "
          rf"(Or: ${w * h}\ \text{{in}}^2$ on the plan, and each square inch is ${per} \cdot {per} = {per * per}\ \text{{ft}}^2$.)", f)
    return {"category": "Scale It Twice", "solo": 90, **q}


unit = {
    "title": "Samples & Scale",
    "course": "Grade 7 Math",
    "tiers": [100, 200, 300, 400, 500],
    "tierNotes": ["Warm-up", "One step", "Fractions and percents", "Two steps", "Challenge"],
    "categories": [
        {"name": "Sample or Population?", "questions": c1()},
        {"name": "Probability from Data", "questions": c2()},
        {"name": "Predict the Population", "questions": c3()},
        {"name": "Scale Factor", "questions": c4()},
        {"name": "Scale Drawings", "questions": c5()},
    ],
    "final": final(),
}
assert all(len(c["questions"]) == 5 for c in unit["categories"])
every = [q for c in unit["categories"] for q in c["questions"]] + [unit["final"]]
answers = [q["a"] for q in every]
shared = sorted({a for a in answers if answers.count(a) > 1})
if shared:
    problems.append(f'answers shared by two questions: {shared}')
for q in every:
    t = q["q"].lower()
    if 'model' in t or re.search(r'\b1 : \$?\d', t):
        problems.append(f'a transfer surface is rehearsed (a model at 1 : N): {q["q"][:50]}')
    if re.search(r'\b0\.\d+\$? of ', t):
        problems.append(f'a transfer surface is rehearsed (a decimal sample fraction): {q["q"][:50]}')
if problems: sys.exit(f"not written: {problems}")
out = Path(__file__).resolve().parent.parent / "samples_and_scale.json"
out.write_text(json.dumps(unit, indent=1, ensure_ascii=True) + "\n")
print('problems:', problems, '| questions:', len(answers), '| distinct answers:', len(set(answers)),
      '| figures:', sum(1 for q in every if q.get("fig")))
