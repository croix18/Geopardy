"""To-scale SVG figures for Boards Up units.

Every figure is described in real units (y up). Shapes are scaled to fit a fixed-height canvas so label text is the
same size on every figure. Labels that state a length can pass `check=` and the build fails if the drawn segment
is not actually that long, so a figure can never disagree with its own labels."""
import math

FS = 30            # label font size, in viewBox px
CW = 0.50          # average glyph width (em) for the condensed label face
CANVAS_H = 400     # every figure's viewBox is this tall
PAD = 16


def _sub(a, b): return (a[0] - b[0], a[1] - b[1])
def _add(a, b): return (a[0] + b[0], a[1] + b[1])
def _mul(a, k): return (a[0] * k, a[1] * k)
def _len(a): return math.hypot(a[0], a[1])
def _unit(a):
    L = _len(a)
    return (a[0] / L, a[1] / L)
def dist(p, q): return _len(_sub(p, q))


def shoelace(pts):
    s = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


class Fig:
    def __init__(self, max_w=560, max_h=250):
        self.max_w, self.max_h = max_w, max_h
        self.polys, self.ops, self.checks = [], [], []
        self._geom = []

    # ---------- geometry (unit coordinates) ----------
    def poly(self, pts, cls='fs'):
        self.polys.append((list(pts), cls)); self._geom += list(pts); return self

    def dash(self, p, q):
        self.ops.append(('dash', p, q)); self._geom += [p, q]; return self

    def right_angle(self, v, a, b, size=17):
        self.ops.append(('ra', v, a, b, size)); return self

    def ticks(self, p, q, n=1):
        self.ops.append(('tick', p, q, n)); return self

    def centroid(self):
        pts = self.polys[0][0]
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    # ---------- labels ----------
    def edge(self, p, q, text, away=None, toward=None, d=12, check=None, cls=''):
        """Label the segment p-q. Sits on the side away from `away` (default: the first polygon's centroid),
        or on the side of `toward` if given."""
        if check is not None:
            self.checks.append((text, dist(p, q), check))
        self.ops.append(('edge', p, q, text, away, toward, d, cls)); return self

    def dim(self, p, q, text, away=None, off=30, d=8, check=None):
        """Dimension line parallel to p-q, pushed `off` px to the side away from `away`, with end ticks."""
        if check is not None:
            self.checks.append((text, dist(p, q), check))
        self.ops.append(('dim', p, q, text, away, off, d)); return self

    def text(self, p, text, dx=0, dy=0, cls=''):
        self.ops.append(('text', p, text, dx, dy, cls)); return self

    # ---------- render ----------
    def svg(self):
        for text, actual, stated in self.checks:
            assert abs(actual - stated) < 0.02, f'label "{text}" says {stated} but the segment is {actual:.3f}'
        xs = [p[0] for p in self._geom]; ys = [p[1] for p in self._geom]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        s = min(self.max_w / (maxx - minx), self.max_h / (maxy - miny))
        P = lambda u: ((u[0] - minx) * s, (maxy - u[1]) * s)
        cen = P(self.centroid())
        out, box = [], []           # box: px points for the bounding box

        def see(x, y): box.append((x, y))

        def put_text(cx, cy, text, cls=''):
            tw = len(text) * FS * CW
            see(cx - tw / 2, cy - FS * 0.55); see(cx + tw / 2, cy + FS * 0.55)
            c = f' class="{cls}"' if cls else ''
            t = text.replace('&', '&amp;').replace('<', '&lt;')
            out_text.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central"{c}>{t}</text>')

        def side_normal(a, b, away, toward):
            """unit normal of a-b (px), pointing away from `away` / toward `toward`"""
            t = _unit(_sub(b, a)); n = (-t[1], t[0])
            mid = _mul(_add(a, b), 0.5)
            ref = P(toward) if toward is not None else (P(away) if away is not None else cen)
            sign = 1 if (ref[0] - mid[0]) * n[0] + (ref[1] - mid[1]) * n[1] > 0 else -1
            if toward is None: sign = -sign
            return (n[0] * sign, n[1] * sign), t, mid

        out_text = []
        for pts, cls in self.polys:
            pp = [P(p) for p in pts]
            for x, y in pp: see(x, y)
            out.append(f'<polygon class="{cls}" points="' + ' '.join(f'{x:.1f},{y:.1f}' for x, y in pp) + '"/>')
        for op in self.ops:
            k = op[0]
            if k == 'dash':
                a, b = P(op[1]), P(op[2]); see(*a); see(*b)
                out.append(f'<line class="fd" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
            elif k == 'ra':
                v, a, b, size = P(op[1]), P(op[2]), P(op[3]), op[4]
                u1, u2 = _unit(_sub(a, v)), _unit(_sub(b, v))
                assert abs(u1[0] * u2[0] + u1[1] * u2[1]) < 1e-3, 'right-angle mark on a corner that is not 90 degrees'
                p1 = _add(v, _mul(u1, size)); p3 = _add(v, _mul(u2, size)); p2 = _add(p1, _mul(u2, size))
                out.append(f'<polyline class="fm" points="{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}"/>')
            elif k == 'tick':
                a, b, n = P(op[1]), P(op[2]), op[3]
                t = _unit(_sub(b, a)); nn = (-t[1], t[0]); mid = _mul(_add(a, b), 0.5)
                for i in range(n):
                    c = _add(mid, _mul(t, (i - (n - 1) / 2) * 8))
                    p1, p2 = _add(c, _mul(nn, 9)), _add(c, _mul(nn, -9))
                    out.append(f'<line class="fm" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}"/>')
            elif k == 'edge':
                _, p, q, text, away, toward, d, cls = op
                n, t, mid = side_normal(P(p), P(q), away, toward)
                tw = len(text) * FS * CW
                r = d + abs(n[0]) * tw / 2 + abs(n[1]) * FS * 0.5
                put_text(mid[0] + n[0] * r, mid[1] + n[1] * r, text, cls)
            elif k == 'dim':
                _, p, q, text, away, off, d = op
                a, b = P(p), P(q)
                n, t, mid = side_normal(a, b, away, None)
                a2, b2 = _add(a, _mul(n, off)), _add(b, _mul(n, off))
                see(*a2); see(*b2)
                out.append(f'<line class="fm" x1="{a2[0]:.1f}" y1="{a2[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}"/>')
                for e in (a2, b2):
                    e1, e2 = _add(e, _mul(n, 9)), _add(e, _mul(n, -9))
                    out.append(f'<line class="fm" x1="{e1[0]:.1f}" y1="{e1[1]:.1f}" x2="{e2[0]:.1f}" y2="{e2[1]:.1f}"/>')
                tw = len(text) * FS * CW
                r = off + d + abs(n[0]) * tw / 2 + abs(n[1]) * FS * 0.5
                put_text(mid[0] + n[0] * r, mid[1] + n[1] * r, text)
            elif k == 'text':
                _, p, text, dx, dy, cls = op
                c = P(p); put_text(c[0] + dx, c[1] + dy, text, cls)
        bx0, bx1 = min(b[0] for b in box) - PAD, max(b[0] for b in box) + PAD
        by0, by1 = min(b[1] for b in box) - PAD, max(b[1] for b in box) + PAD
        h = by1 - by0
        assert h <= CANVAS_H + 0.5, f'figure content is {h:.0f}px tall; canvas is {CANVAS_H}'
        y0 = (by0 + by1) / 2 - CANVAS_H / 2
        vb = f'{bx0:.0f} {y0:.0f} {bx1 - bx0:.0f} {CANVAS_H}'
        return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img">' + ''.join(out) + ''.join(out_text) + '</svg>'
