# THE BLIND SPOT — grounded field, not sample array (PRE-REGISTRATION)

*Written and committed BEFORE any measurement (PROTOCOL §3). Seeds 30000–30999,
declared here, ledgered. The block 12000–29999 is untouched.*

## The claim under test

**Vision is a GROUNDED FIELD, not a sample array.** The proof the creator named
is the blind spot: the retina has a hole (the optic disc — no photoreceptors) and
we do not perceive it. A uniform sample-grid HAS a hole where the sensor has one;
a grounded field FILLS the hole from the surround, so the absence is invisible and
a contour crossing it is perceived whole. Human phenomenology already ran this
experiment; the verdict is "grounded field". This rung builds that on the (G, Γ)
substrate and reproduces (or fails to reproduce) the verdict.

**The blind-spot GEOMETRY (its existence, size, offset) is a STRUCTURAL
CONSTRUCTION PARAMETER of the eye** — the optic nerve must exit somewhere; it is a
named design knob, NOT a dynamic fall-out (§13, honest). What must FALL OUT is the
FILLING, and the confidence DECAY must be RELATIVE to the surround's support, never
a chosen gap-size constant.

## The mechanism (built as SEED RULES, `seeds/vision_ground.json`; NO new Rust)

Each `RetinaCell` holds a grounded belief: `gbel` (value), `gconf` (0..1, 0 =
ungrounded), `gfilled` (0/1), `gcont`/`gcax` (on a contour, and its axis 1=runs
along the row / 2=runs along the column), `gambig` (held-open), `gsensed` (1 =
photoreceptor present, 0 = blind spot — no data ever). The grounding DECISION is
rules (PROTOCOL §0 / CLAUDE.md); the adapter only states observations and the
anatomy. The rules, gated on `GroundParams.ground > 0.5` (ships OFF, §9), reuse the
LOCAL `Neighbours`/`Filter`/`Count`/`Sum` machinery of `vision_lateral`'s `lat_pool`
(a cell folds over its OWN 4-neighbourhood — O(1) per cell, O(N) per sweep):

1. `gr_label` — a SENSED cell is labelled a contour (with an axis) iff its
   observation is CONSTANT along one axis and DIFFERS along the other (structural
   equality on the observed value — no threshold, no magic number).
2. `gr_ambig` — an unfilled blind cell with BOTH a same-row contour-H neighbour and
   a same-col contour-V neighbour of DIFFERENT value is HELD OPEN (`gambig=1`).
   Loaded BEFORE the fill rules, so a conflict always wins → refuse to confabulate.
3. `gr_fill_contour_h` / `gr_fill_contour_v` — an unfilled blind cell with a filled
   contour neighbour along its axis, and NO conflict, CONTINUES the contour (adopts
   its value + axis). This is what preserves a contour AS a contour: a horizontal
   contour propagates only to same-row cells, so it stays 1-cell thin instead of
   blurring.
4. `gr_fill_surface` — an unfilled blind cell with no contour continuation adopts
   the confidence-weighted MEAN of its filled SURFACE (non-contour) neighbours.
5. `gr_interp` (the INTERPOLATION control, `GroundParams.interp > 0.5`, suppresses
   1–4) — the naive baseline: adopt the mean of ALL filled neighbours, contour and
   surface alike, with no structure. This is graph DATA (an ablation), not a Python
   fork (§0).

`gconf` for a filled cell = the summed confidence of its SUPPORTING neighbours over
the number that could support (fraction) — so it FALLS OUT of surround support and
DECAYS where support is weak/sparse (the periphery), with NO fixed decay constant.

## The four DISCRIMINATION claims (grounding vs interpolation) — two-sided

Each is a comparison of the SAME hole + SAME stimulus under grounding vs
interpolation, on the SAME graph. Failure of grounding to beat interpolation is a
clean NEGATIVE about what the operation can express, reportable, not to be rescued
(§5/§7).

- **H1 — STRUCTURE SURVIVES (grounding), NOT BLUR (interpolation).** Statistic: on
  a contour (a value-1 bar on a 0 surround) crossing the blind spot, the mean
  `|gbel − 1|` over the blind cells ON the bar. Grounding PASS: ≤ 0.05 (bridged as a
  contour); interpolation: ≈ 0.5 (blurred to the surround mean). Two-sided: if
  grounding ALSO gives ≈0.5, grounding cannot preserve structure → NEGATIVE.
  Secondary: the cross-bar profile is a STEP under grounding (contour edge sharp)
  and a RAMP under interpolation.
- **H2 — HOLE INVISIBLE under a consistent fill.** Statistic: on a uniform field
  (all cells equal to `v`), max `|gbel(blind) − v|`. PASS: ≤ 1e−6 (no void, no
  seam). This is the headline reproduction of the phenomenology. Two-sided: a NaN /
  a residual void ⇒ the field does not fill ⇒ NEGATIVE.
- **H3 — HIDDEN-WHEN-COVERED + REVEALED-AND-REVISED-WHEN-THE-EYE-MOVES.** A unique
  marker (value 2) lies ENTIRELY inside the blind spot on a 0 surround. (a) COVERED:
  max `|gbel(marker cells) − 0|` ≤ 1e−6 — invisible, filled with the surround belief
  (the falsifiable, human-matching behaviour). (b) EYE MOVES (the scene shifts under
  the eye so the marker location becomes sensed): `gbel(marker cells)` REVISES from 0
  to 2 — it APPEARS. PASS requires BOTH. Two-sided: if the marker is visible while
  covered, the fill is not respecting "no data"; if it never appears after the move,
  the belief is not revisable.
- **H4 — AMBIGUOUS SURROUND HELD OPEN, NOT CONFABULATED.** A blind cell whose
  surround offers a same-row contour-H continuation (value A) AND a same-col
  contour-V continuation (value B≠A) — two admissible fills. Grounding PASS:
  `gambig=1` and NO single confident committed value. Interpolation: commits a
  single invented mean `(A+B)/2` (`gambig=0`) — the confabulation. Two-sided: if
  grounding ALSO commits a single value, it cannot hold ambiguity → NEGATIVE. The
  UNAMBIGUOUS control (only the H continuation) must commit A confidently under
  grounding.

## Positive controls (the instrument — §1 clauses 4/5, §12.4)

- **The blind spot is REAL:** a unique marker placed inside it is confirmed NOT
  directly sensed — the marker cells have `gsensed=0` and NO `gobs` written (no
  data). If the raw sensor returns the marker, the "hole" is fake.
- **The fill is GROUNDING, not a stored default:** move the bar (row 5 vs row 8) →
  the fill moves with it (bridged on whichever row); a BLANK surround (all 0) → the
  fill invents NO contour (`gcont=0` everywhere, no marker); an AMBIGUOUS surround →
  held open. Reported as the WITNESS that the fill TRACKED the surround.
- **The instrument is not dead/forced:** a tick that fills NOTHING (blind cells stay
  `gfilled=0`) is un-grounded → FAIL; a tick that fills everything uniformly
  regardless of surround is confabulation → FAIL. Report `gfilled` coverage of the
  hole and the surround-tracking correlation.

## Scaling (part of the spec, PROTOCOL "LOCAL / O(N)")

The field must be LOCAL / O(N) — NOT the O(N²) uniform-grid drive the assembled-eye
scaling measurement condemned (global `RetinaCell` matching, one-binding-per
`apply_rule_once`). The grounding is driven by `run_rules` (`s.tick`, all bindings
per pass — the O(N) `wv_*`/`lat_*` path), NEVER `apply_rule_once` per binding, and
each rule folds only a cell's own 4-neighbourhood. Statistic: fit the wall-clock
grounding cost vs grid N (sweep 16²…64²) to `N^p`; PASS: p ≤ ~1.1. The blind-spot
diameter is a fixed anatomical constant, so the sweep count does not grow with N.

## Decision rules, seeds, n

- Every H is DETERMINISTIC (fixed stimuli, no RNG arm) — like SHAPE-SELFSEE, so no
  confirmatory seed is consumed by the arms themselves.
- The only randomness is the BLANK/NOISE positive-control (a random surround must
  invent no structure): seeds **30000–30099**, n=100 fixed in advance; PASS = 0/100
  mint a contour (`gcont` in the hole stays 0). Confirmatory block **30100–30999**
  reserved and unburned.
- §9: `seeds/vision_ground.json` ships `ground=0`, `interp=0` (INERT). Committed
  results reproduce byte-identically: sd orbit law {2:1,3:2,4:2,6:2,12:4} unmoved;
  fm0 VACUOUS; depth/time/stereo/dim gates green; vision bench 200/0 with `data/`.
- Exactly the listed tests. A further attempt needs a NEW pre-registration.

## PREDICTION (stated in advance, with provisos)

I predict **grounding PASSES all four and beats interpolation on H1 and H4**,
because the contour-continuation rule carries the contour's AXIS and only propagates
along it (structure), while the surface rule averages (the interpolation baseline),
so the two are genuinely different operations — not a re-parameterised blur.

- **Proviso on H1:** a 1-cell-thin contour through the EXACT centre of a symmetric
  hole is the adversarial case — a purely local rule sees a same-row agreement AND a
  same-col agreement at the crossing. I predict the AXIS-CARRYING propagation still
  bridges it (a horizontal contour never propagates to a different row, so it never
  competes off the bar), but if the fill instead reads ambiguous on the bar itself,
  that is the proviso breaking and it tells me the axis is not actually carried —
  a NEGATIVE I will report, not patch.
- **Proviso on H4:** the ambiguity must be present at the surround from the first
  sweep (both conflicting continuations from SENSED neighbours) to avoid an
  async-propagation race; a crossing that only becomes ambiguous deep inside the
  hole after both contours arrive is a HARDER case I do NOT claim (a named bound).
- **Proviso on H2/H3:** these should be near-trivial for any grounding that fills
  from the surround; if H2 leaves a seam, the surface rule is not reaching the hole
  interior (a coverage bug), and if H3's marker is visible while covered, the
  "no data" split is leaking — either is a NEGATIVE.
- **Proviso on decay:** `gconf` is claimed to fall out of support; if it needs a
  fixed multiplier to fade with eccentricity, that is a magic number and the
  eccentricity claim (requirement #1) is DOWNGRADED to "the blind-spot fill", which
  is the headline anyway.

**Either answer is a result (§7).** "The grounded field fills the blind spot
invisibly, preserves contours, holds ambiguity open, revises when the eye moves —
O(N)" proves grounded-not-sampled. "It can only interpolate" is a clean negative
about the operation's expressive limit. Four results were retracted this arc; every
rung here is believed only because it fails where it must.
