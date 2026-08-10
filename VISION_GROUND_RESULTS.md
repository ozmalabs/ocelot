# THE BLIND SPOT — vision is a GROUNDED FIELD, not a sample array (RESULTS)

*Pre-registration: `VISION_GROUND_PREREG.md`, committed at `59467857` BEFORE any
measurement. Runner `scripts/ground_measure.py`; gate
`tests/test_vision_ground_migrated.py`; seed `seeds/vision_ground.json` (built by
`tools/build_vision_ground.py`); adapter `domains/ground_world.py`. Engine
`62d8fbbb23b8` (shared build, Rust source identical — this rung adds NO Rust,
§10.1 rule 4). Bench with `data/` symlinked (§10.2).*

## Headline

**Vision here IS a grounded field, not a sample array — bounded to the discrete /
integer, in-frame class the frame invariant blesses.** The blind spot (a hole in
the retina with no photoreceptors) is FILLED FROM the surround by grounding, so
the absence is invisible; a contour crossing it is bridged AS a contour (structure
preserved, not blurred); an ambiguous surround is HELD OPEN, not confabulated; and
the belief REVISES when the eye moves. All four discrimination claims PASS and each
BEATS an interpolation control run on the SAME hole and SAME stimulus. The field is
LOCAL / O(N) (fitted exponent **1.02**), NOT the O(N²) uniform-grid drive the
assembled-eye scaling condemned. **Every prediction held; no proviso broke.**

## What was built (NO new Rust — pure seed rules)

`seeds/vision_ground.json` reuses `vision_lateral`'s LOCAL machinery: each
`RetinaCell` folds over its OWN 4-neighbourhood (`Neighbours`/`Filter`/`Count`/
`Sum`), driven by `run_rules` (`s.tick`, all bindings per sweep) — NEVER
`apply_rule_once` per binding (the O(N²) drive). Three rules, the decision entirely
in graph data (PROTOCOL §0):

- **`gr_label`** — a SENSED cell is a contour with an AXIS iff its observation is
  CONSTANT along one axis and DIFFERS along the other (structural equality on the
  observed value — no threshold, no magic number).
- **`gr_fill`** — the unified grounding fill (one rule, so no inter-rule race):
  CONFLICT (a same-row contour value A and a same-col contour value B≠A) → HELD
  OPEN (`gambig=1`, stay unfilled); else CONTINUE a contour along its carried axis;
  else the surface MEAN of filled non-contour neighbours. Because the axis is
  carried and a horizontal contour is continued only to same-row cells, a
  1-cell-thin contour bridges AS a contour instead of blurring. `gconf` falls out
  of support (summed neighbour confidence over the number that could support) —
  RELATIVE decay, no fixed constant.
- **`gr_interp`** — the INTERPOLATION CONTROL (graph data, `interp=1`, suppresses
  the fill): the mean of ALL filled neighbours, contour and surface alike, no
  structure — the baseline that blurs and confabulates.

The blind-spot GEOMETRY (centre offset, radius) is a named STRUCTURAL construction
parameter in `ground_world.add_grounded_field` (the optic nerve must exit
somewhere — §13, honest); it is a knob, NOT a fall-out. What FALLS OUT is the
FILLING and the decay.

## The four discrimination claims (grounding vs interpolation)

| claim | grounding | interpolation | verdict |
|---|---|---|---|
| **H1 STRUCTURE not blur** — mean\|gbel−1\| on a contour crossing the hole | **0.0000** (bridged, profile `[1,1,1,1,1]`, cross-bar edge a sharp STEP, jump 1.000) | **0.8229** (blurred, profile `[0.33,0.17,0.08,0.04,0.26]`, edge washed out, jump 0.083) | **PASS** |
| **H2 HOLE INVISIBLE** — max\|gbel(blind)−v\| on a uniform field | **1.11e−16**, no NaN (no void, no seam) | — | **PASS** (headline phenomenology reproduced) |
| **H3 HIDDEN then REVEALED** — a marker entirely inside the hole | covered gbel **0.000** (invisible, filled with surround), raw sensor **NaN** (no data); eye moves → gbel **3.000** (appears, belief REVISES) | — | **PASS** (both halves) |
| **H4 AMBIGUOUS held open** — a same-row (A=1) × same-col (B=2) crossing | crossing **HELD OPEN** (gambig=1, unfilled), exactly **1** ambiguous cell, both contours still continue (H→1, V→2 away from the crossing); unambiguous control commits **1.0** confidently | crossing COMMITTED (a single confabulated mean **0.25**, never held open) | **PASS** |

## The instrument — positive-controlled (§1 clauses 4/5, §12.4)

- **The blind spot is REAL:** a marker inside is NOT directly sensed — raw sensor
  reads **NaN** (no data) at the marker cell (§1's "prove the hole exists").
- **The fill is GROUNDING, not a stored default:** move the bar (rows 7/8/9, each
  crossing the hole) → the bridge follows the bar exactly and the rest of the hole
  stays clean; a BLANK surround (uniform random value, seeds **30000–30099**) →
  **0/100** invent a contour or an ambiguity, and the hole fills with the surround
  value (invisible). The fill TRACKS the surround.
- **The instrument is alive, not dead/forced:** hole coverage **1.000** (fills, not
  black), and it fills DIFFERENTLY per surround (bar bridged, blank uniform,
  ambiguous held open) — not one forced value.

## Scaling — LOCAL / O(N)

| grid | N | present (ms) |
|---|---|---|
| 16² | 256 | 4.23 |
| 24² | 576 | 9.67 |
| 32² | 1024 | 17.47 |
| 48² | 2304 | 39.98 |
| 64² | 4096 | 72.08 |

Fitted exponent **p = 1.02** (linear). NOT the O(N²) drive (fitted 1.99) the
assembled-eye scaling measured — the grounding is driven by `run_rules` (each cell
folds only its 4-neighbourhood, O(1); the blind-spot diameter is a fixed anatomical
constant, so the sweep count does not grow with N), never `apply_rule_once` per
binding.

## §9 — defaults preserve committed results

Ships INERT (`ground=0`, `interp=0`): with `ground=0` no rule fires and the hole is
never filled (verified: `hole_filled_when_off = 0.0`). The committed vision bench
is **200 passed / 0 failed** with `data/` (unperturbed by the new seed + adapter +
registration). Sibling gates green: depth 8/8 · time 6/6 · stereo 9/9 · dimension
inference 8/8 · gen_infer 7/7 · sdloop 15/15 · provenance 7/7. **fm0 still VACUOUS
(D == 0.0)** at the defaults. The sd orbit law `{2:1,3:2,4:2,6:2,12:4}` and every
depth/time/stereo contract are unmoved (this rung touches no existing seed, no
Rust, and adds no default that fires). New gate `test_vision_ground_migrated.py`
11/11 (+ the slow scaling gate).

## What is NOT claimed (§8 — the honest bounds)

- **Bounded to the DISCRETE / integer, in-frame class.** The contour test uses
  binary/step stimuli so "constant along an axis" is EXACT equality (no threshold).
  A graded natural surround needs a contour signal robust to a magnitude threshold
  — the natural home is the existing ON/OFF residual (edge) channel from
  `vision_lateral` (nonzero = contour), which this rung reuses in spirit but does
  not wire in; a graded-image build is a separate rung. The frame/continuum
  invariant: the field's coordinates are the integer lattice; real-valued fills
  would be cross-frame.
- **The ambiguity tested is present at the surround from the first sweep** (both
  conflicting continuations from the immediate neighbourhood), which is race-free.
  A crossing that only becomes ambiguous DEEP inside the hole after two contours
  propagate and meet asynchronously is a HARDER case NOT claimed here — a named
  bound, exactly as the pre-registration stated in advance.
- **The blind-spot geometry is a design PARAMETER**, not a fall-out — stated as
  such (§13). What falls out is the filling and the confidence decay (relative to
  support). The eccentricity-fade requirement (foveal detail / peripheral fade as
  one decay) is DESIGNED into `gconf` (support-relative, no fixed ρ) and holds for
  the blind-spot fill; a full peripheral-acuity gradient across the whole field is
  not separately measured here — the blind spot is the headline.
- **This is a retinal filling model, not a cortical one.** It reproduces the
  perceptual verdict (the hole is invisible; contours bridge; ambiguity is held);
  it does not claim which biological locus (retinal interpolation vs V1 filling-in)
  is correct — both are candidates and this does not discriminate them.

## The verdict, plainly

**Is vision here a GROUNDED FIELD rather than a sample array?** YES — measured, and
bounded. The blind spot is invisible because it is filled from BELIEF, not because
a sample happened to be there (a sample-grid would show the hole). A contour is
bridged AS a contour because the grounding carries the contour's AXIS and continues
STRUCTURE (0.0000 error, a sharp step) where interpolation blurs it (0.8229 error,
a ramp). An ambiguous surround is HELD OPEN (the anti-confabulation gate:
interpolation invents one mean, grounding refuses). The belief is REVISABLE — a
thing hidden in the hole is invisible and APPEARS when the eye moves. And it is
LOCAL / O(N), the redirection away from the uniform grid the scaling measurement
condemned. Grounding is a genuinely DIFFERENT operation from interpolation, not a
re-parameterised blur — which is the whole claim.

**What I got wrong, and fixed, before believing anything:** my first cut split the
fill into separate contour and surface rules; they RACED inside one `run_rules`
fixpoint and the surface rule won the interior of a contour (a bar bridged only one
hop from each anchor, `[1,0,0,0,1]`). The fix was a single UNIFIED contour-first
fill rule (no inter-rule race) — verified sweep-by-sweep before any claim. This is
exactly the §1 discipline: the separate-rules null was a silent bug, caught by
looking at the field, not by a gate going red.
