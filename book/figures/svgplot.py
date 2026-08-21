"""Minimal dependency-free SVG plotting for the book's figures.

Why this exists: there is no matplotlib in this tree, and adding a plotting
dependency to draw twenty figures is a worse trade than 250 lines of stdlib.
Output is vector SVG (right for print), theme-aware (readable on a dark screen
without a second render), and every figure is a committed generator plus its
committed output -- FIGURES.md's rule.

Coordinates: user data space -> pixel space via Axes. Y grows upward in data
space and downward in pixels; Axes handles the flip.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

# One palette, defined once. Names are roles, not colours, so a figure never
# hard-codes "blue" for a meaning.
INK = "var(--ink)"
MUTED = "var(--muted)"
RULE = "var(--rule)"
ARM_A = "var(--arm-a)"
ARM_B = "var(--arm-b)"
ACCENT = "var(--accent)"
NULLC = "var(--null)"

_STYLE = """
:root{--ink:#16181d;--muted:#5b6270;--rule:#c8cdd6;--arm-a:#1f6f8b;
--arm-b:#b4531f;--accent:#2f7d4f;--null:#8a8f99;--bg:transparent}
@media (prefers-color-scheme:dark){:root{--ink:#e6e8ec;--muted:#9aa1ae;
--rule:#3a4049;--arm-a:#5fb6d4;--arm-b:#e08a52;--accent:#6fc08d;--null:#767c86}}
text{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
fill:var(--ink)}
.lbl{font-size:12px}.tick{font-size:11px;fill:var(--muted)}
.ttl{font-size:15px;font-weight:600}.sub{font-size:12px;fill:var(--muted)}
.cap{font-size:11px;fill:var(--muted)}
.note{font-size:11.5px;fill:var(--muted)}
.val{font-size:11.5px;font-weight:600}
"""


class Fig:
    def __init__(self, width: int, height: int):
        self.w, self.h = width, height
        self.parts: list[str] = []

    # --- primitives -----------------------------------------------------
    def line(self, x1, y1, x2, y2, stroke=RULE, width=1.0, dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="{cap}"{d}/>')

    def rect(self, x, y, w, h, fill=ARM_A, opacity=1.0, rx=1.5, stroke="none"):
        self.parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(w,0):.2f}" '
            f'height="{max(h,0):.2f}" rx="{rx}" fill="{fill}" '
            f'fill-opacity="{opacity}" stroke="{stroke}"/>')

    def circle(self, cx, cy, r, fill=INK, opacity=1.0, stroke="none", sw=1.0):
        self.parts.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{fill}" '
            f'fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, cls="lbl", anchor="start", fill=None, rotate=None):
        f = f' fill="{fill}"' if fill else ""
        t = f' transform="rotate({rotate} {x:.2f} {y:.2f})"' if rotate else ""
        self.parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" class="{cls}" '
            f'text-anchor="{anchor}"{f}{t}>{escape(str(s))}</text>')

    def path(self, d, stroke=INK, width=1.4, fill="none", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-linejoin="round"{da}/>')

    # --- composites -----------------------------------------------------
    def title(self, x, y, main, sub=None):
        self.text(x, y, main, cls="ttl")
        if sub:
            self.text(x, y + 16, sub, cls="sub")

    def caption(self, x, y, lines):
        for i, ln in enumerate(lines):
            self.text(x, y + i * 14, ln, cls="cap")

    def save(self, path):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'role="img"><style>{_STYLE}</style>')
        with open(path, "w") as fh:
            fh.write(head + "\n" + "\n".join(self.parts) + "\n</svg>\n")
        return path


@dataclass
class Axes:
    """A rectangular plot area mapping data space to pixels."""
    fig: Fig
    x0: float
    y0: float
    w: float
    h: float
    xlim: tuple = (0.0, 1.0)
    ylim: tuple = (0.0, 1.0)
    categorical: list = field(default_factory=list)

    def px(self, v):
        lo, hi = self.xlim
        return self.x0 + (v - lo) / (hi - lo) * self.w

    def py(self, v):
        lo, hi = self.ylim
        return self.y0 + self.h - (v - lo) / (hi - lo) * self.h

    def frame(self, left=True, bottom=True):
        if bottom:
            self.fig.line(self.x0, self.y0 + self.h, self.x0 + self.w,
                          self.y0 + self.h, RULE, 1.0)
        if left:
            self.fig.line(self.x0, self.y0, self.x0, self.y0 + self.h, RULE, 1.0)

    def xticks(self, vals, fmt=lambda v: f"{v:g}", label=None):
        for v in vals:
            x = self.px(v)
            self.fig.line(x, self.y0 + self.h, x, self.y0 + self.h + 4, RULE, 1.0)
            self.fig.text(x, self.y0 + self.h + 17, fmt(v), cls="tick",
                          anchor="middle")
        if label:
            self.fig.text(self.x0 + self.w / 2, self.y0 + self.h + 36, label,
                          cls="lbl", anchor="middle")

    def yticks(self, vals, fmt=lambda v: f"{v:g}", label=None, grid=False):
        for v in vals:
            y = self.py(v)
            self.fig.line(self.x0 - 4, y, self.x0, y, RULE, 1.0)
            self.fig.text(self.x0 - 8, y + 4, fmt(v), cls="tick", anchor="end")
            if grid:
                self.fig.line(self.x0, y, self.x0 + self.w, y, RULE, 0.6,
                              dash="2 4")
        if label:
            self.fig.text(self.x0 - 44, self.y0 + self.h / 2, label, cls="lbl",
                          anchor="middle", rotate=-90)

    # interval + point, the shape most of these figures need
    def interval_h(self, y, lo, hi, mean, colour=ARM_A, r=4.0, capsize=5):
        xl, xh, xm = self.px(lo), self.px(hi), self.px(mean)
        self.fig.line(xl, y, xh, y, colour, 2.0)
        self.fig.line(xl, y - capsize, xl, y + capsize, colour, 1.6)
        self.fig.line(xh, y - capsize, xh, y + capsize, colour, 1.6)
        self.fig.circle(xm, y, r, fill=colour)

    def interval_v(self, x, lo, hi, mean, colour=ARM_A, r=4.0, capsize=5):
        yl, yh, ym = self.py(lo), self.py(hi), self.py(mean)
        self.fig.line(x, yl, x, yh, colour, 2.0)
        self.fig.line(x - capsize, yl, x + capsize, yl, colour, 1.6)
        self.fig.line(x - capsize, yh, x + capsize, yh, colour, 1.6)
        self.fig.circle(x, ym, r, fill=colour)


def nice_ticks(lo, hi, n=5):
    """Round tick values covering [lo, hi]."""
    import math
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            step = m * mag
            break
    start = math.floor(lo / step) * step
    out, v = [], start
    while v <= hi + step * 0.5:
        out.append(round(v, 10))
        v += step
    return out
