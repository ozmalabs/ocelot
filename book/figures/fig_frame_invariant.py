#!/usr/bin/env python3
"""Figure FR-1 -- in-frame is integer; the continuum lives between frames.

Conceptual. The decision procedure the whole book runs on: for any number you
are about to write, ask whether it is IN a frame or BETWEEN frames. In-frame
coordinates are the integer lattice, because sampling is what grounding IS.
Every real-valued structure -- a rotation by a real angle, a scale ratio, pi,
Fourier, log, a comparison metric, a rendering -- lives in the MAP between
frames, never in an object's coordinates.

Source of truth: CLAUDE.md, "BASE-AS-DIMENSION + the frame/continuum
invariant"; shape_decode.rs::coord_ints (which refuses a Float slot, and is
correct to).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgplot as sp

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "frame_1_invariant.svg")


def lattice(f, x, y, w, h, n=6, col=sp.ARM_A):
    """A frame: an integer lattice, drawn as one."""
    f.rect(x, y, w, h, fill=col, opacity=0.06, rx=3)
    f.rect(x, y, w, h, fill="none", stroke=col, rx=3)
    dx, dy = w / (n + 1), h / (n + 1)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            f.circle(x + i * dx, y + j * dy, 1.9, fill=col, opacity=0.75)


def main():
    W, H = 780, 534
    f = sp.Fig(W, H)
    f.title(46, 34, "In-frame is integer. The continuum lives between frames.",
            "The test for every number in this book: is it IN a frame, or "
            "BETWEEN two?")

    lattice(f, 76, 92, 150, 150, col=sp.ARM_A)
    lattice(f, 554, 92, 150, 150, col=sp.ARM_B)
    f.text(151, 258, "a frame", cls="lbl", anchor="middle")
    f.text(151, 274, "coordinates are the lattice", cls="note",
           anchor="middle")
    f.text(629, 258, "another frame", cls="lbl", anchor="middle")
    f.text(629, 274, "also the lattice", cls="note", anchor="middle")

    # the map between them -- this is where the reals are
    f.path("M 236 148 C 320 108, 460 108, 544 148", stroke=sp.ACCENT,
           width=1.8)
    f.path("M 236 186 C 320 226, 460 226, 544 186", stroke=sp.ACCENT,
           width=1.8, dash="5 3")
    f.text(390, 100, "the map", cls="lbl", anchor="middle", fill=sp.ACCENT)
    f.text(390, 152, "Hom(frame, frame)", cls="val", anchor="middle",
           fill=sp.ACCENT)
    for i, ln in enumerate((
            "rotation by a real angle · a scale ratio · π",
            "Fourier · log · a comparison metric · a rendering")):
        f.text(390, 174 + i * 15, ln, cls="note", anchor="middle")
    f.text(390, 206, "REAL-VALUED, and correctly so", cls="note",
           anchor="middle", fill=sp.ACCENT)

    f.line(46, 300, 734, 300, sp.RULE, 0.8)

    f.text(46, 324, "Why in-frame MUST be integer", cls="lbl")
    for i, ln in enumerate((
            "Sampling is what grounding is. An observed frame is stepped by "
            "construction, so a float in an",
            "object's coordinates is a category error, not extra precision. "
            "The engine already enforces this:",
            "coord_ints returns None on a Float slot — a refusal that is "
            "load-bearing, not a gap to be filled.")):
        f.text(46, 344 + i * 15, ln, cls="note")

    f.text(46, 408, "Continuity is intensional only", cls="lbl")
    for i, ln in enumerate((
            "A continuous quantity is a rule you APPLY, never a datum you "
            "observe. A map may carry a real",
            "parameter intensionally; its observable is always the stepped "
            "rendering. You can apply π — but any",
            "given circle is stepped, and pinning a parameter finer than the "
            "steps support is encoding precision",
            "the observation cannot carry.")):
        f.text(46, 428 + i * 15, ln, cls="note")

    f.caption(46, 496, [
        "Conceptual figure — no data behind it. Source: CLAUDE.md "
        "§ BASE-AS-DIMENSION and shape_decode.rs::coord_ints.",
        "Generator: book/figures/fig_frame_invariant.py",
    ])
    f.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
