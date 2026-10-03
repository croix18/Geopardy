"""Area of Polygons unit (Grade 7 on-level: MA.7.GR.1.1 / 1.2, plus rectangle and triangle review).

Writes units/area_of_polygons.json. Every area is recomputed from the drawn coordinates, and every labelled
length is checked against the drawn segment (see figs.py), so questions, figures and answers cannot drift apart:
    python3 units/src/area_of_polygons.py
"""
import json, math, sys
from pathlib import Path
from figs import Fig, shoelace

SQ = lambda n, u: rf"${n}\ \text{{{u}}}^2$"
problems = []

def expect(label, actual, stated):
    ok = abs(actual - stated) < 1e-6
    print(('ok  ' if ok else 'BAD ') + f'{label}: {actual:g} vs {stated:g}')
    if not ok: problems.append(label)

def corners(f, pts, idx=None):
    n = len(pts)
    for i in (range(n) if idx is None else idx):
        f.right_angle(pts[i], pts[(i - 1) % n], pts[(i + 1) % n])

def height(f, top, foot, toward_pt, label, check=None, cls=''):
    f.dash(top, foot)
    f.edge(top, foot, label, toward=toward_pt, check=check, cls=cls)

def Q(q, a, work, fig, afig=None):
    d = {"q": q, "a": a, "work": work, "fig": fig.svg()}
    if afig is not None: d["afig"] = afig.svg()
    return d

# =====================================================================================
# 1. RECTANGLES & TRIANGLES
# =====================================================================================
def c1():
    out = []
    # 100 rectangle 9 x 6
    pts = [(0, 0), (9, 0), (9, 6), (0, 6)]
    f = Fig().poly(pts); corners(f, pts)
    f.edge(pts[0], pts[1], '9 cm', check=9).edge(pts[3], pts[0], '6 cm', check=6)
    expect('C1-100', shoelace(pts), 54)
    out.append(Q("Find the area of the rectangle.", SQ(54, 'cm'), r"$A = \ell w = 9 \cdot 6 = 54$.", f))

    # 200 triangle 13-14-15, height 12
    A, B, C, F = (0, 0), (14, 0), (5, 12), (5, 0)
    f = Fig().poly([A, B, C])
    height(f, C, F, B, '12 ft', check=12); f.right_angle(F, C, B)
    f.edge(A, B, '14 ft', check=14).edge(A, C, '13 ft', check=13).edge(B, C, '15 ft', check=15)
    expect('C1-200', shoelace([A, B, C]), 84); expect('C1-200 formula', 0.5 * 14 * 12, 84)
    out.append(Q("Find the area of the triangle.", SQ(84, 'ft'),
                 r"Use the base and the height, not the slanted sides: $\frac{1}{2} \cdot 14 \cdot 12 = 84$.", f))

    # 300 right triangle, legs 7.5 and 4, drawn resting on its longest side
    x = (7.5**2 - 4**2 + 8.5**2) / (2 * 8.5); y = math.sqrt(7.5**2 - x**2)
    A, B, C = (0, 0), (8.5, 0), (x, y)
    f = Fig().poly([A, B, C]); f.right_angle(C, A, B)
    f.edge(A, B, '8.5 m', check=8.5).edge(A, C, '7.5 m', check=7.5).edge(B, C, '4 m', check=4)
    expect('C1-300', shoelace([A, B, C]), 15); expect('C1-300 formula', 0.5 * 7.5 * 4, 15)
    out.append(Q("Find the area of the right triangle.", SQ(15, 'm'),
                 r"The two sides that meet at the right angle are the base and height: $\frac{1}{2} \cdot 7.5 \cdot 4 = 15$.", f))

    # 400 compare a rectangle and a triangle
    R = [(0, 0), (8, 0), (8, 5), (0, 5)]
    x0 = 12.5
    T = [(x0, 0), (x0 + 12, 0), (x0 + 5, 7)]; foot = (x0 + 5, 0); tc = (x0 + 5.67, 2.33)
    f = Fig(max_w=760, max_h=230).poly(R).poly(T); corners(f, R)
    f.edge(R[0], R[1], '8 in', check=8).edge(R[3], R[0], '5 in', check=5)
    f.dash(T[2], foot); f.right_angle(foot, T[2], T[1])
    f.edge(T[2], foot, '7 in', toward=T[1], check=7)
    f.edge(T[0], T[1], '12 in', away=tc, check=12)
    f.text((4, 5), 'FLAG A', dy=-30).text(T[2], 'FLAG B', dy=-30)
    expect('C1-400 rect', shoelace(R), 40); expect('C1-400 tri', shoelace(T), 42); expect('C1-400 diff', shoelace(T) - shoelace(R), 2)
    out.append(Q("Flag A is a rectangle. Flag B is a triangle. Which flag has the greater area, and by how much?",
                 r"Flag B, by $2\ \text{in}^2$",
                 r"Flag A: $8 \cdot 5 = 40$. Flag B: $\frac{1}{2} \cdot 12 \cdot 7 = 42$. Then $42 - 40 = 2$.", f))

    # 500 obtuse triangle, height outside
    A, B, C, F = (0, 0), (5, 0), (11, 8), (11, 0)
    f = Fig().poly([A, B, C]); f.dash(B, F).dash(C, F); f.right_angle(F, B, C)
    f.edge(A, B, '5 cm', check=5).edge(B, F, '6 cm', check=6).edge(C, F, '8 cm', check=8)
    f.edge(B, C, '10 cm', toward=F, check=10)
    expect('C1-500', shoelace([A, B, C]), 20); expect('C1-500 formula', 0.5 * 5 * 8, 20)
    out.append(Q("Find the area of the shaded triangle.", SQ(20, 'cm'),
                 r"The base is only the 5 cm side. The height is 8 cm, measured outside the triangle: $\frac{1}{2} \cdot 5 \cdot 8 = 20$.", f))
    return out

# =====================================================================================
# 2. PARALLELOGRAMS
# =====================================================================================
def pgram(base, h, off):
    return [(0, 0), (base, 0), (base + off, h), (off, h)]

def c2():
    out = []
    pts = pgram(8, 5, 2.5); cen = (5.25, 2.5)
    f = Fig().poly(pts); height(f, pts[3], (2.5, 0), cen, '5 cm', check=5); f.right_angle((2.5, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '8 cm', check=8)
    expect('C2-100', shoelace(pts), 40)
    out.append(Q("Find the area of the parallelogram.", SQ(40, 'cm'), r"$A = bh = 8 \cdot 5 = 40$.", f))

    off = math.sqrt(7**2 - 6**2); pts = pgram(12, 6, off)
    f = Fig().poly(pts); height(f, pts[3], (off, 0), (8, 3), '6 in', check=6); f.right_angle((off, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '12 in', check=12).edge(pts[1], pts[2], '7 in', check=7)
    expect('C2-200', shoelace(pts), 72)
    out.append(Q("Find the area of the parallelogram.", SQ(72, 'in'),
                 r"Use the height, not the slanted side: $A = bh = 12 \cdot 6 = 72$.", f))

    # 300 turned: the 4.5 m sides are vertical, the height runs across
    pts = [(0, 0), (0, 4.5), (6, 7), (6, 2.5)]
    f = Fig().poly(pts); f.dash((0, 3.5), (6, 3.5)); f.right_angle((0, 3.5), (6, 3.5), (0, 4.5))
    f.edge((0, 3.5), (6, 3.5), '6 m', toward=(3, 7), check=6)
    f.edge(pts[0], pts[1], '4.5 m', check=4.5).edge(pts[0], pts[3], '6.5 m', check=6.5)
    expect('C2-300', shoelace(pts), 27); expect('C2-300 formula', 4.5 * 6, 27)
    out.append(Q("Find the area of the parallelogram.", SQ(27, 'm'),
                 r"The base is the 4.5 m side. The height is the 6 m distance that meets it at a right angle: $4.5 \cdot 6 = 27$.", f))

    pts = pgram(6, 4, 2)
    f = Fig().poly(pts); height(f, pts[3], (2, 0), (4, 2), '4 in', check=4); f.right_angle((2, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '6 in', check=6)
    expect('C2-400 one tile', shoelace(pts), 24); expect('C2-400 total', shoelace(pts) * 20, 480)
    out.append(Q("A mosaic uses 20 tiles like this one. What is the total area of all 20 tiles?", SQ(480, 'in'),
                 r"One tile: $6 \cdot 4 = 24$. Twenty tiles: $24 \cdot 20 = 480$.", f))

    R = [(0, 0), (9, 0), (9, 8), (0, 8)]; x0 = 13
    Pg = [(x0, 0), (x0 + 12, 0), (x0 + 15, 6), (x0 + 3, 6)]; pc = (x0 + 7.5, 3)
    f = Fig(max_w=760, max_h=230).poly(R).poly(Pg); corners(f, R)
    f.edge(R[0], R[1], '9 cm', check=9).edge(R[3], R[0], '8 cm', check=8)
    f.dash(Pg[3], (x0 + 3, 0)); f.right_angle((x0 + 3, 0), Pg[3], Pg[1])
    f.edge(Pg[3], (x0 + 3, 0), '?', toward=pc, cls='fu')
    f.edge(Pg[0], Pg[1], '12 cm', away=pc, check=12)
    expect('C2-500 rect', shoelace(R), 72); expect('C2-500 pgram', shoelace(Pg), 72); expect('C2-500 h', 72 / 12, 6)
    out.append(Q("The rectangle and the parallelogram have the same area. What is the height of the parallelogram?",
                 r"$6\ \text{cm}$",
                 r"Rectangle: $9 \cdot 8 = 72$. The parallelogram also has area 72, so $12 \cdot h = 72$ and $h = 6$.", f))
    return out

# =====================================================================================
# 3. TRAPEZOIDS
# =====================================================================================
def trap(b1, b2, h, off):
    return [(0, 0), (b1, 0), (off + b2, h), (off, h)]

def c3():
    out = []
    pts = trap(10, 6, 4, 2)
    f = Fig().poly(pts); height(f, pts[3], (2, 0), (5, 2), '4 cm', check=4); f.right_angle((2, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '10 cm', check=10).edge(pts[2], pts[3], '6 cm', check=6)
    expect('C3-100', shoelace(pts), 32); expect('C3-100 formula', 0.5 * 4 * (6 + 10), 32)
    out.append(Q("Find the area of the trapezoid.", SQ(32, 'cm'),
                 r"Add the bases, multiply by the height, then take half: $\frac{1}{2} \cdot 4 \cdot (6 + 10) = 32$.", f))

    pts = trap(14, 8, 4, 3)
    f = Fig().poly(pts); height(f, pts[3], (3, 0), (7, 2), '4 in', check=4); f.right_angle((3, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '14 in', check=14).edge(pts[2], pts[3], '8 in', check=8)
    f.edge(pts[0], pts[3], '5 in', check=5).edge(pts[1], pts[2], '5 in', check=5)
    expect('C3-200', shoelace(pts), 44); expect('C3-200 formula', 0.5 * 4 * (8 + 14), 44)
    out.append(Q("Find the area of the trapezoid.", SQ(44, 'in'),
                 r"The 5 in sides are not needed: $\frac{1}{2} \cdot 4 \cdot (8 + 14) = 44$.", f))

    pts = [(0, 0), (6, 0), (6, 5.5), (0, 8.5)]
    f = Fig().poly(pts); corners(f, pts, [0, 1])
    f.edge(pts[3], pts[0], '8.5 m', check=8.5).edge(pts[1], pts[2], '5.5 m', check=5.5).edge(pts[0], pts[1], '6 m', check=6)
    expect('C3-300', shoelace(pts), 42); expect('C3-300 formula', 0.5 * 6 * (8.5 + 5.5), 42)
    out.append(Q("Find the area of the trapezoid.", SQ(42, 'm'),
                 r"The parallel sides are the bases, and 6 m is the height: $\frac{1}{2} \cdot 6 \cdot (8.5 + 5.5) = 42$.", f))

    pts = trap(14, 10, 5, 2)
    f = Fig().poly(pts); height(f, pts[3], (2, 0), (7, 2.5), '5 ft', check=5); f.right_angle((2, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '14 ft', check=14).edge(pts[2], pts[3], '10 ft', check=10)
    expect('C3-400 area', shoelace(pts), 60); expect('C3-400 bags', shoelace(pts) / 20, 3)
    out.append(Q(r"A garden bed is shaped like this trapezoid. One bag of mulch covers $20\ \text{ft}^2$. How many bags are needed to cover the bed?",
                 "3 bags", r"Area: $\frac{1}{2} \cdot 5 \cdot (10 + 14) = 60$. Bags: $60 \div 20 = 3$.", f))

    pts = trap(13, 7, 8, 3)
    f = Fig().poly(pts); f.dash(pts[3], (3, 0)); f.right_angle((3, 0), pts[3], pts[1])
    f.edge(pts[3], (3, 0), '?', toward=(6.5, 4), cls='fu')
    f.edge(pts[0], pts[1], '13 cm', check=13).edge(pts[2], pts[3], '7 cm', check=7)
    expect('C3-500 area', shoelace(pts), 80); expect('C3-500 h', 80 / (0.5 * (7 + 13)), 8)
    out.append(Q(r"The area of this trapezoid is $80\ \text{cm}^2$. What is its height?", r"$8\ \text{cm}$",
                 r"The bases add to 20, and half of 20 is 10. So $10 \cdot h = 80$ and $h = 8$.", f))
    return out

# =====================================================================================
# 4. RHOMBI
# =====================================================================================
def all_ticks(f, pts):
    for i in range(len(pts)): f.ticks(pts[i], pts[(i + 1) % len(pts)])

def diamond(d1, d2, l1, l2):
    a, b = d1 / 2, d2 / 2
    pts = [(-a, 0), (0, b), (a, 0), (0, -b)]
    f = Fig().poly(pts); all_ticks(f, pts)
    f.dash(pts[0], pts[2]).dash(pts[1], pts[3]); f.right_angle((0, 0), pts[2], pts[1], size=15)
    f.dim((-a, -b), (a, -b), l1, away=(0, 0), off=20, check=d1)
    f.dim((a, -b), (a, b), l2, away=(0, 0), off=20, check=d2)
    return f, pts

def c4():
    out = []
    off = math.sqrt(7**2 - 5**2); pts = pgram(7, 5, off)
    f = Fig().poly(pts); all_ticks(f, pts)
    height(f, pts[3], (off, 0), (7, 2.5), '5 cm', check=5); f.right_angle((off, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '7 cm', check=7, d=20)
    expect('C4-100', shoelace(pts), 35); expect('C4-100 side', math.dist(pts[1], pts[2]), 7)
    out.append(Q("Find the area of the rhombus.", SQ(35, 'cm'),
                 r"A rhombus is a parallelogram with four equal sides: $A = bh = 7 \cdot 5 = 35$.", f))

    pts = pgram(10, 8, 6)
    f = Fig().poly(pts); all_ticks(f, pts)
    height(f, pts[3], (6, 0), (9, 4), '8 in', check=8); f.right_angle((6, 0), pts[3], pts[1])
    f.edge(pts[0], pts[1], '10 in', check=10, d=20).edge(pts[1], pts[2], '10 in', check=10, d=20)
    expect('C4-200', shoelace(pts), 80)
    out.append(Q("Find the area of the rhombus.", SQ(80, 'in'),
                 r"Multiply the base by the height, not side by side: $10 \cdot 8 = 80$.", f))

    f, pts = diamond(8, 4.5, '8 m', '4.5 m')
    expect('C4-300', shoelace(pts), 18); expect('C4-300 formula', 0.5 * 8 * 4.5, 18); expect('C4-300 triangles', 2 * (0.5 * 4.5 * 4), 18)
    out.append(Q("Find the area of the rhombus.", SQ(18, 'm'),
                 r"Half the product of the diagonals: $\frac{1}{2} \cdot 8 \cdot 4.5 = 18$. Or split it into two triangles: each is $\frac{1}{2} \cdot 4.5 \cdot 4 = 9$.", f))

    f, pts = diamond(6, 5, '6 ft', '5 ft')
    expect('C4-400 area', shoelace(pts), 15); expect('C4-400 cost', shoelace(pts) * 4, 60)
    out.append(Q(r"A sign is shaped like this rhombus. Paint costs \$4 per square foot. How much does it cost to paint the front of the sign?",
                 r"\$60", r"Area: $\frac{1}{2} \cdot 6 \cdot 5 = 15$. Cost: $15 \cdot 4 = 60$.", f))

    off = math.sqrt(10**2 - 7**2); pts = pgram(10, 7, off)
    f = Fig().poly(pts); all_ticks(f, pts)
    height(f, pts[3], (off, 0), (12, 3.5), '7 cm', check=7); f.right_angle((off, 0), pts[3], pts[1])
    perim = sum(math.dist(pts[i], pts[(i + 1) % 4]) for i in range(4))
    expect('C4-500 perimeter', perim, 40); expect('C4-500', shoelace(pts), 70)
    out.append(Q("The perimeter of this rhombus is 40 cm. What is its area?", SQ(70, 'cm'),
                 r"All four sides are equal, so each side is $40 \div 4 = 10$. Then $A = bh = 10 \cdot 7 = 70$.", f))
    return out

# =====================================================================================
# 5. COMPOSITE FIGURES (rectangles and triangles)
# =====================================================================================
def c5():
    out = []
    # 100 L-shape, split shown
    pts = [(0, 0), (10, 0), (10, 4), (4, 4), (4, 9), (0, 9)]
    def fig(ans):
        f = Fig().poly(pts); f.dash((0, 4), (4, 4))
        f.edge(pts[0], pts[1], '10 m', check=10).edge(pts[1], pts[2], '4 m', check=4)
        f.edge(pts[4], pts[5], '4 m', check=4).edge(pts[3], pts[4], '5 m', toward=(10, 9), check=5)
        if ans: f.text((5, 2), '40', cls='fa').text((2, 6.5), '20', cls='fa')
        return f
    expect('C5-100', shoelace(pts), 60)
    out.append(Q("Find the area of the figure.", SQ(60, 'm'),
                 r"Two rectangles: $10 \cdot 4 = 40$ and $4 \cdot 5 = 20$. Then $40 + 20 = 60$.", fig(False), fig(True)))

    # 200 house, slanted roof edges are extra
    pts = [(0, 0), (8, 0), (8, 5), (4, 8), (0, 5)]
    def fig(ans):
        f = Fig().poly(pts); f.dash((0, 5), (8, 5)).dash((4, 8), (4, 5)); f.right_angle((4, 5), (4, 8), (8, 5), size=14)
        f.text((4, 5), '3 ft', dx=44, dy=-24)
        f.edge(pts[0], pts[1], '8 ft', check=8).edge(pts[1], pts[2], '5 ft', check=5)
        f.edge(pts[2], pts[3], '5 ft', check=5).edge(pts[3], pts[4], '5 ft', check=5)
        if ans: f.text((4, 2.5), '40', cls='fa').text((4, 5), '12', dx=-40, dy=-24, cls='fa')
        return f
    expect('C5-200', shoelace(pts), 52); expect('C5-200 roof height', 8 - 5, 3)
    out.append(Q("Find the area of the figure.", SQ(52, 'ft'),
                 r"Rectangle: $8 \cdot 5 = 40$. Triangle: $\frac{1}{2} \cdot 8 \cdot 3 = 12$. The 5 ft roof edges are not needed.", fig(False), fig(True)))

    # 300 L-shape with decimals, one side must be found by subtracting
    pts = [(0, 0), (9, 0), (9, 2.5), (4, 2.5), (4, 6.5), (0, 6.5)]
    def fig(ans):
        f = Fig().poly(pts)
        f.edge(pts[0], pts[1], '9 m', check=9).edge(pts[1], pts[2], '2.5 m', check=2.5)
        f.edge(pts[5], pts[0], '6.5 m', check=6.5).edge(pts[4], pts[5], '4 m', check=4)
        if ans:
            f.dash((0, 2.5), (4, 2.5)); f.text((4.5, 1.25), '22.5', cls='fa').text((2, 4.5), '16', cls='fa')
        return f
    expect('C5-300', shoelace(pts), 38.5); expect('C5-300 parts', 9 * 2.5 + 4 * (6.5 - 2.5), 38.5)
    out.append(Q("Find the area of the figure.", SQ('38.5', 'm'),
                 r"Bottom rectangle: $9 \cdot 2.5 = 22.5$. The top rectangle is $6.5 - 2.5 = 4$ tall, so $4 \cdot 4 = 16$. Then $22.5 + 16 = 38.5$.", fig(False), fig(True)))

    # 400 gable wall, then cans of paint
    pts = [(0, 0), (12, 0), (12, 8), (6, 12), (0, 8)]
    def fig(ans):
        f = Fig().poly(pts); f.dash((0, 8), (12, 8)).dash((6, 12), (6, 8)); f.right_angle((6, 8), (6, 12), (12, 8), size=13)
        f.text((6, 8), '4 ft', dx=44, dy=-22)
        f.edge(pts[0], pts[1], '12 ft', check=12).edge(pts[1], pts[2], '8 ft', check=8)
        if ans: f.text((6, 4), '96', cls='fa').text((6, 8), '24', dx=-40, dy=-22, cls='fa')
        return f
    expect('C5-400 area', shoelace(pts), 120); expect('C5-400 cans', shoelace(pts) / 40, 3)
    out.append(Q(r"A wall is shaped like this figure. One can of paint covers $40\ \text{ft}^2$. How many cans are needed to paint the wall?",
                 "3 cans", r"Rectangle: $12 \cdot 8 = 96$. Triangle: $\frac{1}{2} \cdot 12 \cdot 4 = 24$. Total: $120$. Cans: $120 \div 40 = 3$.", fig(False), fig(True)))

    # 500 rectangle with a triangle on each end; triangle height must be worked out
    pts = [(4, 0), (14, 0), (18, 3), (14, 6), (4, 6), (0, 3)]
    def fig(ans):
        f = Fig().poly(pts)
        f.edge(pts[3], pts[4], '10 cm', check=10)
        f.dim((0, 0), (18, 0), '18 cm', away=(9, 3), off=20, check=18)
        f.dim((0, 0), (0, 6), '6 cm', away=(9, 3), off=20, check=6)
        if ans:
            f.dash((4, 0), (4, 6)).dash((14, 0), (14, 6))
            f.text((9, 3), '60', cls='fa').text((2.7, 3), '12', cls='fa').text((15.3, 3), '12', cls='fa')
        return f
    expect('C5-500', shoelace(pts), 84); expect('C5-500 parts', 10 * 6 + 2 * (0.5 * 6 * ((18 - 10) / 2)), 84)
    out.append(Q("Find the area of the figure.", SQ(84, 'cm'),
                 r"Rectangle: $10 \cdot 6 = 60$. Each triangle is $(18 - 10) \div 2 = 4$ wide, so each is $\frac{1}{2} \cdot 6 \cdot 4 = 12$. Then $60 + 12 + 12 = 84$.", fig(False), fig(True)))
    return out

def final():
    pts = [(0, 0), (14, 0), (14, 4), (8, 10), (0, 10)]
    def fig(ans):
        f = Fig().poly(pts); corners(f, pts, [0, 1, 4])
        f.edge(pts[0], pts[1], '14 ft', check=14).edge(pts[1], pts[2], '4 ft', check=4)
        f.edge(pts[3], pts[4], '8 ft', check=8).edge(pts[4], pts[0], '10 ft', check=10)
        if ans:
            f.dash((8, 0), (8, 10)).dash((8, 4), (14, 4))
            f.text((4, 5), '80', cls='fa').text((11, 2), '24', cls='fa').text((10, 6), '18', cls='fa')
        return f
    expect('Final', shoelace(pts), 122); expect('Final parts', 8 * 10 + 6 * 4 + 0.5 * 6 * 6, 122)
    d = Q("Find the area of the figure.", SQ(122, 'ft'),
          r"Rectangle: $8 \cdot 10 = 80$. Rectangle: $6 \cdot 4 = 24$. Triangle: $\frac{1}{2} \cdot 6 \cdot 6 = 18$. Then $80 + 24 + 18 = 122$.", fig(False), fig(True))
    return {"category": "Put It All Together", "solo": 90, **d}

unit = {
    "title": "Area of Polygons",
    "course": "Grade 7 Math",
    "tiers": [100, 200, 300, 400, 500],
    "tierNotes": ["Warm-up", "Extra info", "Decimals", "Two steps", "Challenge"],
    "categories": [
        {"name": "Rectangles & Triangles", "questions": c1()},
        {"name": "Parallelograms", "questions": c2()},
        {"name": "Trapezoids", "questions": c3()},
        {"name": "Rhombi", "questions": c4()},
        {"name": "Composite Figures", "questions": c5()},
    ],
    "final": final(),
}
assert all(len(c["questions"]) == 5 for c in unit["categories"])
if problems: sys.exit("not written: a check failed")
out = Path(__file__).resolve().parent.parent / "area_of_polygons.json"
out.write_text(json.dumps(unit, indent=1, ensure_ascii=True) + "\n")
print('problems:', problems, '| questions:', sum(len(c["questions"]) for c in unit["categories"]) + 1,
      '| figures:', sum(1 for c in unit["categories"] for q in c["questions"] if q.get("fig")) + 1)
