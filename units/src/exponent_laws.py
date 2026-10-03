"""Laws of Exponents unit (Grade 7 Accelerated: MA.7.NSO.1.1, MA.8.NSO.1.3, MA.8.AR.1.1).

Writes units/exponent_laws.json. Every answer is checked with sympy before the file is written:
    python3 units/src/exponent_laws.py
"""
import json, sys
from pathlib import Path
from sympy import symbols, simplify, Rational, Eq, solve, sympify

x, y, a, b, c, d, n = symbols('x y a b c d n', nonzero=True)

SINGLE = "Write as a single power.\n"
SIMP = "Simplify.\n"
POS = "Simplify. Use positive exponents only.\n"
EVAL = "Evaluate.\n"
FIND = "Find the value of $n$.\n"

def Q(q, ans, work, check):
    return {"q": q, "a": ans, "work": work, "_check": check}

cats = [
 ("Product of Powers", [
  Q(SINGLE + r"$$5^{3} \cdot 5^{4}$$", r"$5^{7}$",
    r"Same base, so add the exponents: $3 + 4 = 7$.",
    (5**3 * 5**4, 5**7)),
  Q(SINGLE + r"$$2^{5} \cdot 2 \cdot 2^{3}$$", r"$2^{9}$",
    r"A plain $2$ is $2^{1}$. Add all three exponents: $5 + 1 + 3 = 9$.",
    (2**5 * 2 * 2**3, 2**9)),
  Q(SIMP + r"$$(3x^{4})(5x^{6})$$", r"$15x^{10}$",
    r"Multiply the coefficients: $3 \cdot 5 = 15$. Add the exponents: $4 + 6 = 10$.",
    ((3*x**4)*(5*x**6), 15*x**10)),
  Q(SIMP + r"$$(-2a^{3}b)(4a^{5}b^{6})$$", r"$-8a^{8}b^{7}$",
    r"Coefficients: $-2 \cdot 4 = -8$. For $a$: $3 + 5 = 8$. For $b$: $1 + 6 = 7$.",
    ((-2*a**3*b)*(4*a**5*b**6), -8*a**8*b**7)),
  Q(POS + r"$$(2x^{-5}y^{3})(-7x^{2}y^{4})$$", r"$-\dfrac{14y^{7}}{x^{3}}$",
    r"Coefficients: $2 \cdot (-7) = -14$. For $x$: $-5 + 2 = -3$, so $x^{3}$ goes in the denominator. For $y$: $3 + 4 = 7$.",
    ((2*x**-5*y**3)*(-7*x**2*y**4), -14*y**7/x**3)),
 ]),
 ("Quotient of Powers", [
  Q(SINGLE + r"$$\dfrac{9^{8}}{9^{5}}$$", r"$9^{3}$",
    r"Same base, so subtract the exponents: $8 - 5 = 3$.",
    (Rational(9**8, 9**5), 9**3)),
  Q(EVAL + r"$$\dfrac{3^{9}}{3^{5}}$$", r"$81$",
    r"Subtract the exponents: $9 - 5 = 4$. Then $3^{4} = 81$.",
    (Rational(3**9, 3**5), 81)),
  Q(SIMP + r"$$\dfrac{12x^{9}}{4x^{3}}$$", r"$3x^{6}$",
    r"Divide the coefficients: $12 \div 4 = 3$. Subtract the exponents: $9 - 3 = 6$.",
    ((12*x**9)/(4*x**3), 3*x**6)),
  Q(SIMP + r"$$\dfrac{18a^{7}b^{4}}{-6a^{2}b^{4}}$$", r"$-3a^{5}$",
    r"Coefficients: $18 \div (-6) = -3$. For $a$: $7 - 2 = 5$. For $b$: $4 - 4 = 0$, and $b^{0} = 1$.",
    ((18*a**7*b**4)/(-6*a**2*b**4), -3*a**5)),
  Q(POS + r"$$\dfrac{8x^{3}y^{-2}}{20x^{7}y^{-6}}$$", r"$\dfrac{2y^{4}}{5x^{4}}$",
    r"Coefficients: $\frac{8}{20} = \frac{2}{5}$. For $x$: $3 - 7 = -4$, so $x^{4}$ goes in the denominator. For $y$: $-2 - (-6) = 4$.",
    ((8*x**3*y**-2)/(20*x**7*y**-6), 2*y**4/(5*x**4))),
 ]),
 ("Raise It to a Power", [
  Q(SINGLE + r"$$(7^{2})^{5}$$", r"$7^{10}$",
    r"Power of a power, so multiply the exponents: $2 \cdot 5 = 10$.",
    ((7**2)**5, 7**10)),
  Q(SIMP + r"$$(5x)^{3}$$", r"$125x^{3}$",
    r"The exponent goes to every factor: $5^{3} \cdot x^{3} = 125x^{3}$.",
    ((5*x)**3, 125*x**3)),
  Q(SIMP + r"$$(2x^{4})^{3}$$", r"$8x^{12}$",
    r"The coefficient gets the power too: $2^{3} = 8$. For $x$: $4 \cdot 3 = 12$.",
    ((2*x**4)**3, 8*x**12)),
  Q(SIMP + r"$$\left(\dfrac{2x^{3}}{y^{2}}\right)^{4}$$", r"$\dfrac{16x^{12}}{y^{8}}$",
    r"Top and bottom both get the $4$: $2^{4} = 16$, then $3 \cdot 4 = 12$ and $2 \cdot 4 = 8$.",
    (((2*x**3)/(y**2))**4, 16*x**12/y**8)),
  Q(POS + r"$$(3x^{-2}y)^{-2}$$", r"$\dfrac{x^{4}}{9y^{2}}$",
    r"Every factor gets the $-2$: $3^{-2} = \frac{1}{9}$. For $x$: $(-2)(-2) = 4$. For $y$: $1 \cdot (-2) = -2$, so $y^{2}$ goes in the denominator.",
    ((3*x**-2*y)**-2, x**4/(9*y**2))),
 ]),
 ("Zero & Negative", [
  Q(EVAL + r"$$14^{0}$$", r"$1$",
    r"Any nonzero base raised to the zero power equals $1$.",
    (sympify(14)**0, 1)),
  Q(EVAL + r"$$5^{-2}$$", r"$\dfrac{1}{25}$",
    r"A negative exponent means take the reciprocal: $5^{-2} = \frac{1}{5^{2}} = \frac{1}{25}$. Also correct: $0.04$.",
    (Rational(5)**-2, Rational(1, 25))),
  Q("Rewrite with a positive exponent.\n" + r"$$4x^{-3}$$", r"$\dfrac{4}{x^{3}}$",
    r"Only $x$ has the exponent $-3$, so only $x^{3}$ moves to the denominator. The $4$ stays on top.",
    (4*x**-3, 4/x**3)),
  Q(EVAL + r"$$\left(\dfrac{2}{3}\right)^{-3}$$", r"$\dfrac{27}{8}$",
    r"Flip the fraction, then cube it: $\left(\frac{3}{2}\right)^{3} = \frac{27}{8}$. Also correct: $3\frac{3}{8}$.",
    (Rational(2, 3)**-3, Rational(27, 8))),
  Q(POS + r"$$\dfrac{5a^{-3}b^{0}}{c^{-2}d^{4}}$$", r"$\dfrac{5c^{2}}{a^{3}d^{4}}$",
    r"$b^{0} = 1$. $a^{-3}$ moves down and $c^{-2}$ moves up. The $5$ and $d^{4}$ stay where they are.",
    ((5*a**-3*b**0)/(c**-2*d**4), 5*c**2/(a**3*d**4))),
 ]),
 ("Find the Exponent", [
  Q(FIND + r"$$5^{3} \cdot 5^{n} = 5^{9}$$", r"$n = 6$",
    r"Multiplying adds exponents: $3 + n = 9$.",
    ("solve", Eq(3 + n, 9), 6)),
  Q(FIND + r"$$\dfrac{7^{n}}{7^{4}} = 7^{6}$$", r"$n = 10$",
    r"Dividing subtracts exponents: $n - 4 = 6$.",
    ("solve", Eq(n - 4, 6), 10)),
  Q(FIND + r"$$(x^{n})^{3} = x^{15}$$", r"$n = 5$",
    r"Power of a power multiplies exponents: $3n = 15$.",
    ("solve", Eq(3*n, 15), 5)),
  Q(FIND + r"$$6^{n} \cdot 6^{-9} = 6^{-2}$$", r"$n = 7$",
    r"Add the exponents: $n + (-9) = -2$, so $n = 7$.",
    ("solve", Eq(n + (-9), -2), 7)),
  Q(FIND + r"$$\dfrac{(a^{n})^{3}}{a^{-2}} = a^{14}$$", r"$n = 4$",
    r"Multiply, then subtract: $3n - (-2) = 14$. So $3n + 2 = 14$ and $3n = 12$.",
    ("solve", Eq(3*n - (-2), 14), 4)),
 ]),
]

final = Q(POS + r"$$\dfrac{(2x^{3}y^{-2})^{3}}{4x^{-1}y^{2}}$$", r"$\dfrac{2x^{10}}{y^{8}}$",
          r"Power first: $(2x^{3}y^{-2})^{3} = 8x^{9}y^{-6}$. Then divide: $8 \div 4 = 2$. For $x$: $9 - (-1) = 10$. For $y$: $-6 - 2 = -8$, so $y^{8}$ goes in the denominator.",
          (((2*x**3*y**-2)**3)/(4*x**-1*y**2), 2*x**10/y**8))

# ---- verify ----
bad = 0
def verify(label, q):
    global bad
    ck = q.pop("_check")
    if ck[0] == "solve":
        sol = solve(ck[1], n)
        ok = sol == [ck[2]]
        # also confirm the stated n satisfies the ORIGINAL exponent equation numerically
    else:
        ok = simplify(ck[0] - ck[1]) == 0
    print(("ok  " if ok else "BAD ") + label, "->", q["a"])
    if not ok: bad += 1

tiers = [100, 200, 300, 400, 500]
for name, qs in cats:
    assert len(qs) == len(tiers)
    for t, q in zip(tiers, qs):
        verify(f"{name} {t}", q)
verify("Final", final)

# independent numeric check of the Find-the-Exponent equations with the stated n
import math
checks = [
    (5**3 * 5**6, 5**9), (7**10 / 7**4, 7**6), ((2.0**5)**3, 2.0**15),
    (6.0**7 * 6.0**-9, 6.0**-2), ((2.0**4)**3 / 2.0**-2, 2.0**14),
]
for i, (l, r) in enumerate(checks):
    ok = math.isclose(l, r, rel_tol=1e-12)
    print(("ok  " if ok else "BAD ") + f"numeric find-n #{i+1}")
    if not ok: bad += 1

unit = {
    "title": "Laws of Exponents",
    "course": "Grade 7 Accelerated Math",
    "tiers": tiers,
    "tierNotes": ["Warm-up", "One twist", "Variables", "Multi-step", "Challenge"],
    "categories": [{"name": name, "questions": qs} for name, qs in cats],
    "final": {"category": "Every Law at Once", "solo": 90, **final},
}
if bad: sys.exit("not written: an answer failed its check")
out = Path(__file__).resolve().parent.parent / "exponent_laws.json"
out.write_text(json.dumps(unit, indent=1, ensure_ascii=True) + "\n")
print("problems:", bad, "| questions:", sum(len(c["questions"]) for c in unit["categories"]) + 1)
