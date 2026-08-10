# TIME = the inferred parameter of the transition generator

The temporal rung's design note (companion to `COMPOSITION_DESIGN.md` /
`DYADIC_DEPTH_DESIGN.md`). One line: **time is not in a frame — it is the
exponent of the generator BETWEEN frames.**

## The frame/continuum invariant, applied to time

A single tick's graph state is the present: an integer lattice, no stored `t`.
Time is not a coordinate (in-frame is integer; a `t` coordinate would be a
category error). A pattern moving over ticks is a SEQUENCE of frames; that
sequence is an ORBIT under a transition generator `G` with
`frame(t+1) = G(frame(t))`; the exponent `k` indexing `G⁰,G¹,G²…` IS the time
axis. `G` lives in `Hom(frame,frame)` — the map between frames — exactly where
this tree puts every non-in-frame structure (rotation angle, scale ratio, the
verdict metrics). So time and space become the SAME KIND of thing: inferred
latent dimensions indexing discovered generators.

## Two motion classes, one operation

`TimeInfer` (`shape_decode::eval_time_infer`) is `GenInfer` one level up: it
asks whether ONE `G` carries EVERY consecutive presented pair, inferring `G`
from the first pair and VERIFYING by exact equality across the rest.

- **LINEAR transitions** (rotate/scale/shear per tick) were ALREADY in-class:
  the transition is a non-trivial integer 2×2 map, identifiable from ONE pair
  by `GenInfer`'s enumerate-and-test, and the sd loop already mints a
  `LatentDimension` whose coordinate is the exponent `k`. Zero new decode code.
- **TRANSLATION** needed the affine extension, and it is the subtle case:
  - a pure translation is RUNG-1 (a uniform per-frame shift), so the normal
    ladder recognizes it WITHOUT a generator — no exponent, no dimension;
  - worse, translation is GROUP-CLOSED: any two frames of a constant-velocity
    orbit are mutual translates PAIRWISE, so "is this pair explainable?" is
    VACUOUSLY yes for any ordering. Pairwise-explainability CANNOT discriminate
    ordered from shuffled for translation.
  - The discriminator is therefore CONSTANT VELOCITY across the WHOLE orbit —
    an orbit-level property, not a per-frame one. `TimeInfer` reads the offset
    `δ` from the first pair and requires `frame(i)+δ == frame(i+1)` for EVERY
    `i`; a shuffle breaks constancy, an acceleration breaks constancy.
  - `apply_translate_once` (`{kind:"translate", offset}`) is the one new
    dispatch arm: `v -> v + offset`, NO wrap (unlike `modular`), NO
    origin-normalization (unlike every linear step — a translation is ABOUT
    position). Its `k`-th power is `+k·δ`, so a minted translate generator's
    exponent is a displacement quantum along `latent:time`, uniform with the
    linear generators.

## The floor and the arrow

A shuffled sequence is not an orbit (no single `G` carries every PRESENTED
pair) ⇒ unexplained ⇒ enumeration (the honest MDL floor). A monotone reversal
IS a genuine orbit under `G⁻¹` (time's arrow reversed) — reported as such, not
a floor failure. The floor is HARDER to spuriously satisfy at LONGER windows
(more pairs must agree on one `G`), so it is gated at the longest window
(§1.1's dead-arm disease, time-domain form).

## Boundedness (honest scope)

Time is inferred for the motion class {integer-linear transition ∪ constant
integer-velocity translation} — the same integer/in-frame boundary the
gen-mint rung proved for space. Real-angle rotation (cross-frame, non-integer)
and acceleration (non-constant transition) are OUT — refused to enumeration,
not hallucinated.
