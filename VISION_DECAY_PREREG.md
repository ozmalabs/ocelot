# VISION — THE EDGE-ANCHORED DECAYING GRADIENT (PRE-REGISTRATION)

*Written and COMMITTED before any implementation and before any measurement
(PROTOCOL §3). Branch `gamma-substrate/decaying-gradient`, worktree
`.claude/worktrees/agent-ad92e5a814bb8c342`. Base `main` HEAD **`51f5ecf9`**.
Engine **`25fa11652e83`** (shared build, Rust source byte-identical to canonical —
`domains/engine_provenance.py` reads *"shared build … Rust source identical"*).
**Seed block 69000–69999**, verified free against the §PROTOCOL burned-seed ledger.
This rung adds **NO Rust**.*

---

## 0. The question, and why it is a mechanism-level hypothesis and not a sweep

`VISION_PAINT_RESULTS.md` (merged `1759aec7`) ends on exactly one open question:

> *the escalation that makes the mechanism honest is the escalation that breaks
> Cornsweet. Either the percept is read at a LOWER order than the residual
> reaches … or the order-2 code must not be EXTRAPOLATED beyond the cells it was
> fitted to. Both are mechanism-level hypotheses and neither may be tried as a
> parameter search on this pre-registration (§3.6); each needs its own.*

This is the second of those two, and this file is its own pre-registration.

`VISION_PRIOR_ART_MAP.md` §1.2/§1.3/§1.4/§1.5b says three published camps
converge on one answer — **the raw gradient must not be used as-is**: Retinex
*thresholds* the slow component away (Land & McCann 1971, stage 2); Arend &
Goldstein 1987 *segment* it, because thresholded derivatives have non-zero curl
so far-field integration is structurally ill-posed; Cohen-Duwek & Spitzer 2019
*weight* it by a multi-scale dominance function, and state our failure as a
design requirement — *"without modification, unmodified gradients would
reconstruct the original image during diffusion."* And Blakeslee & McCourt 2013
measured induced brightness **declining with distance from the inducing edge**,
concluding *"a homogeneous filling-in mechanism cannot explain the induced
structure"* — which rules out BOTH of our existing arms (flat fill is
homogeneous; the extrapolated plane is not decaying).

**THE HYPOTHESIS (mechanism-level, two-sided).** The order-2 code's excursion is
**anchored at the boundary that sourced it and decays with distance from it**,
so the code interpolates between the fitted plane *at* the edge and the order-1
constant *far from* it. Predicted consequence: Cornsweet survives escalation with
the correct sign AND the Blakeslee–McCourt decline-with-distance signature
appears. Predicted cost, stated in advance: **the same suppression must
under-render a REAL gradient that lies inside a bounded compartment**, because
the mechanism has no way to tell a genuine bounded ramp from a Cornsweet
shoulder — they are the same signal.

**The two-sided form.** If the decay is derivable and the sign comes out
inverted anyway, or if the pinned residual arm regresses, the finding is that
perception-matching and residual-honesty are in **structural** tension rather
than separated by a parameter — which is the more valuable outcome and will be
reported as the headline.

---

## 1. THE MECHANISM — an extension of `seeds/vision_paint.json`, not a parallel one

Four changes, all inside the existing seed. `pt_delta` / `pt_block` / `pt_seed` /
`pt_flood` / `pt_hub` / `pt_fit1` / `pt_fit2` / `pt_resid` / `pt_escalate` /
`pt_verdict` are **untouched in behaviour**.

1. **`pt_anchor`** (per cell) — `panchor := 1` iff the cell touches a BLOCKED
   link: `pblk_e` or `pblk_s` on itself, or `pblk_e` on its west neighbour, or
   `pblk_s` on its north neighbour. A blocked link is a strict-|Δ| maximum, i.e.
   a luminance edge. **The field's outer border is NOT an anchor** — it carries
   no |Δ| (`pd_has_*` = 0), so it can never be a strict maximum. "Edge-anchored"
   therefore means anchored at a luminance discontinuity, nothing else.

2. **`pt_dist`** (per cell, to the `run_rules` fixpoint) — `pdist` := 0 if
   `panchor`, else `Min(cap, 1 + MinOver(reachable neighbours, pdist))` where
   `reachable` is the SAME unblocked-link relation `pt_flood` already uses, so
   the distance is **geodesic WITHIN the region** and never crosses a boundary.
   `cap = prows·pcols` (the field's own cell count — a bound no in-region
   geodesic can reach, present only so the iteration provably terminates for an
   unanchored region). Least-fixed-point from 0, monotone non-decreasing,
   bounded ⇒ terminates. Same shape as `pt_flood`.

3. **`pt_decay`** (per hub) — `panch_n := Count(region cells with panchor)` and
   **`plam := Σ pdist / pnall` over the region's cells** — the region's own MEAN
   GEODESIC DEPTH from its own boundary. This is the decay length λ. See §2.

4. **`pt_paint`** (modified, one multiplicative factor) —

   ```
   w(c) = 1                       if pdecay is OFF, or panch_n == 0
        = plam / (plam + pdist(c)) otherwise
   painted = mean + w(c)·[slope_r·(row − cen_r) + slope_c·(col − cen_c)]
   ```

   `w(0) = 1` (at the edge the code IS the fitted plane), `w` strictly
   decreasing, `w → 0` far away (the code relaxes to the order-1 constant).

**`PaintParams` gains `pdecay: 0.0` — OFF BY DEFAULT (§9).** With `pdecay = 0`,
`w ≡ 1` and every rule reduces to its committed form, so
`results/paint_measure.json` must reproduce **byte-identically**. That is a gated
assertion, not a hope. `domains/paint_world.py`, `scripts/paint_measure.py` and
`tests/test_paint_migrated.py` are **NOT EDITED AT ALL** (the paint gate reads
the live adapter source and asserts its only `set_attr` write is `paint`); the
new flag is written by a new adapter, `domains/decay_world.py`.

**Two structural invariants, asserted in advance:**

- **The decay touches ONLY the order-2 rendering, NEVER the escalation
  decision.** `korder` steps 1→2 on the residual of the order-1 (flat) code, in
  which no plane term appears. So "k falls out" is untouched by construction and
  `pt_escalate` remains the sole writer of `korder`.
- **No boundary ⇒ no anchor ⇒ no decay.** A region with `panch_n == 0` gets
  `w ≡ 1` and is painted exactly as before. This is Arend & Goldstein's field
  segmentation made graded: *the order-2 code's domain of validity is its own
  compartment, measured from its own boundary.*

---

## 2. THE DECAY LENGTH — it FALLS OUT (§13), and here is the derivation

**λ = the region's own mean geodesic depth from its own boundary**,
`plam = Σ_v pdist(v) / pnall`.

- It is **geometry only**. No tuning, no threshold, no imported constant, no
  reference to any target output. It is the *same kind of object* the seed
  already computes — `pt_fit1`'s `pcen_r`/`pcen_c` are the first moment of the
  region in the row/column coordinate; `plam` is the first moment of the region
  in the **distance-to-its-own-boundary** coordinate.
- It is **relative, not absolute** (§13's "ratios transfer, absolutes do not"):
  the code depends only on the dimensionless `pdist/plam`. Rescale the lattice
  and λ rescales with it.
- **The degenerate cases are self-consistent and need no special code.**
  λ = 0 ⟺ `pdist ≡ 0` ⟺ every cell in the region is on its boundary; then
  `Div(0, 0) = 0` (the engine's documented behaviour, already load-bearing in
  `pt_fit2`) and the order-2 term vanishes — a region that is all boundary has
  no room for a gradient. `panch_n = 0` ⟹ `w ≡ 1` — no edge, no anchoring.

**AND THE DERIVATION HAS A CLOSED FORM THAT IS ITSELF A FALLEN-OUT NUMBER.**
For a region anchored on ONE side, `pdist` is uniform on `0 … d_max`, so
λ = d_max/2 **exactly**, and the weight at the far edge is

> **w(d_max) = (d_max/2) / (d_max/2 + d_max) = 1/3, INDEPENDENT OF REGION WIDTH.**

The far-field excursion of the plane is cut to **exactly one third**. Nothing was
chosen to make that 1/3; it is what a uniform depth distribution gives. It is
also the rung's sharpest quantitative prediction, because it makes the inversion
criterion explicit and width-free:

| code | far-field painted value | inverts iff |
|---|---|---|
| order-1 flat | `m` | never |
| order-2 plane (committed) | `m − s·h` | `s·h > (m − 100)` |
| order-2 decaying (this rung) | `m − s·h/3` | `s·h > 3(m − 100)` |

(`m` = region mean, `s` = fitted slope, `h` = half-width = the far cell's
deviation from the centroid.) **The decay buys exactly a factor of 3 of
headroom, derived rather than fitted.** Whether the Cornsweet stimulus family
sits inside that headroom is a fact about the stimulus, not about the mechanism,
and it is measured in ARM 1 and bounded in ARM B.

**WHAT IS *NOT* DERIVED, DECLARED HERE AND NOT LATER (§13.1).** The FORM of the
falloff is a **choice**, constrained but not derived. The constraints are
w(0) = 1, strictly decreasing, w(∞) = 0, one scale parameter, expressible in the
existing DSL without new Rust. The rational falloff `λ/(λ+d)` is the simplest
function meeting all five (an exponential would need a new `Exp` Term). **A
different admissible form would give different magnitudes.** So: the decay
LENGTH fell out; the decay SHAPE went in as architecture, and the
decline-with-distance signature of ARM 2 is therefore **FORCED by the
construction** — §13.1's third category. ARM 2 is reported for what it is (see
§4) and is NOT claimed as an emergent prediction.

**NOTHING IS IMPORTED FROM COHEN-DUWEK & SPITZER.** Their mechanism (weight the
gradient before filling in) is the idea being tested; their multi-scale Gabor
dominance function and its parameters are NOT used. No constant of theirs
appears in this rung.

---

## 3. THE GATE — a THREE-WAY CONJUNCTION, on the SINGLE-EDGE geometry only

All three, or the rung FAILS. Each outcome's meaning is fixed here, in advance.

### ARM 1 — Cornsweet appears with the CORRECT sign at the escalated order

- **Stimulus:** `scripts/paint_measure.py::stim_cornsweet`, unchanged — two
  physically identical flat far-fields (both 100.0) joined by one cusp.
- **Statistic:** `difference = ppaint_lum(3,0) − ppaint_lum(3,19)` at the
  converged state, with `pdecay = 1`. Also recorded: `hub.korder` on both sides
  (must be 2.0 — the verdict is read at the order the residual REACHES, never at
  an intermediate one; reading k=1 would be §5 surgery).
- **PASS:** `difference > 0` **and** both `korder == 2.0`.
- **Baseline pinned for contrast:** `pdecay = 0` gives **−1.818** (committed).
- **A NULL/FAIL means:** suppressing the far-field extrapolation is not
  sufficient to restore the illusion, i.e. the inversion is not (only) an
  extrapolation artifact and the paint rung's second hypothesis is refuted too.

### ARM 2 — induced brightness DECLINES with distance from the edge

- **The induction** `I(c) = ppaint_lum(c) − plum(c)`, measured **only on the
  PHYSICALLY UNIFORM far fields** (left cols 0–5 and right cols 14–19, all
  exactly 100.0) — the analogue of Blakeslee & McCourt's uniform test field.
- **The distance is the STIMULUS's, not the mechanism's** (§1 / the
  instrument-discipline rule: *a diagnostic must not be computed by the component
  it checks*). `dist(c) = 9 − c` on the left and `c − 10` on the right, from the
  cusp between columns 9 and 10. `pdist` is NOT used in this measurement.
- **Statistic:** `|I|` as a function of `dist`, on each side separately.
- **PASS:** `|I|` is **strictly decreasing** in `dist` on BOTH sides (6 points
  each), and `I` does not change sign within a far field.
- **Baseline pinned for contrast:** the committed plane gives a NON-monotone
  profile that crosses zero (|I| = 1.212, 0.788, 0.364, 0.061, 0.485, 0.909 at
  dist 4…9 on the left) — it declines, overshoots through the null, and comes
  back up inverted. A flat fill gives a CONSTANT |I|. The arm therefore
  discriminates all three codes.
- **HONESTY CLAUSE, registered here and not after the fact:** the DIRECTION of
  this arm is forced by the construction (§13.1). What it can still fail on, and
  what it is therefore actually testing, is (a) **strictness and monotonicity of
  the TOTAL induction**, which is `(m − 100) + s·dev(c)·w(d(c))` — a product of
  two varying terms whose deviation factor CHANGES SIGN inside the left far
  field, so non-monotonicity is a live outcome; and (b) **no sign change**,
  which fails for the committed plane. It is not evidence that a decaying code
  decays.

### ARM 3 — THE RESIDUAL ARM MUST STILL PASS

- **What "must still pass" means, fixed in advance:** the paint rung's OWN
  pinned arm, R1–R4, re-measured with `pdecay = 1` (`scripts/paint_measure.py`'s
  `arm_R` logic, re-run through the decay adapter at seed 69600), plus the
  floors F1 (n=100, seeds 69000–69099) and F2 (n=100, seeds 69100–69199).
- **PASS requires ALL of:**
  - R1 uniform: 1 region, `korder` 1, not refuted, mean residual 0.000;
  - R2 linear ramp: 1 region, `korder` 2, not refuted, mean residual 0.000, and
    `pslope_c_plum` recovered **exactly 3.0**;
  - R3 texture: `korder` 2, refuted, refuted-area fraction > 0.9, mean residual
    ≥ pquant/2, region count < 10;
  - R4 contrast: texture mean residual > uniform mean residual, texture refuted
    and uniform not;
  - F1: **0/100** fields invent appearance from none, `max|ppaint_app| = 0.0`;
  - F2: fraction of fields with a refuted region > 0.9.
- **A REGRESSION HERE IS THE FINDING and will be reported as the headline, not
  traded away.**
- **Registered expectation, with its reason:** R1/R2 are expected byte-identical
  because neither stimulus produces a single blocked link, so `panch_n = 0` and
  `w ≡ 1`. That is not luck; it is the "no edge, no anchor" invariant. R3's paint
  DOES change (a texture has anchors) and its residual is expected to rise
  slightly, which strengthens rather than threatens the arm.

### ARM 3b — R5, THE COST PROBE (new; NOT part of the pinned arm)

Because R1/R2's pass is structural, arm 3 as pinned cannot see the cost the
hypothesis predicts. So a **new, declared-in-advance** probe: **a real linear
ramp INSIDE a bounded compartment.** Profile `[20]×4 + [50,53,…,71] + [120]×4`
(16 columns, 8 rows) — two steps that ARE strict-|Δ| maxima, so the ramp region
has anchors on BOTH sides.

- **Statistics:** the middle region's `pslope_c_plum` (the FIT), its
  `presid_mean` and `prefuted` (the RENDERING), with `pdecay` 0 and 1.
- **This is diagnostic, not a pass/fail arm** — it was never in the paint rung's
  arm, and inventing a new pass condition for it in either direction after the
  fact would be surgery. Its outcome is reported first-class regardless of
  direction.
- **Registered prediction:** the FIT is unchanged (`pslope_c_plum = 3.0`
  exactly — the decay never touches `pt_fit2`) while the RENDERING is damped, so
  `presid_mean` goes 0.000 → non-zero and the region becomes REFUTED where it was
  not. **If that is what happens, the honest statement is: the mechanism cannot
  distinguish a genuine bounded ramp from a Cornsweet shoulder, because they are
  the same signal — and the suppression that fixes one necessarily breaks the
  other.** That is the structural-tension result, arrived at from the other side.

---

## 4. THE TWO GEOMETRIES — measured SEPARATELY, and only one is gated

Cavanagh & Anstis (2018) report that under **cumulative** diamond geometry the
human percept is *"a global lightness shift opposite in direction to the actual
luminance gradients"* — so inversion is not automatically proof of a bug
(`VISION_PRIOR_ART_MAP.md` §1.5c).

- **G1 SINGLE-EDGE — GATED.** The three-way conjunction above. Here inversion IS
  wrong (§1.5b's diagnosis applies).
- **G2 CUMULATIVE — MEASURED AND REPORTED, NOT GATED.** A 1-D Cornsweet sawtooth:
  the unit `[100,100,100,100, 101,102,103,104, 96,97,98,99]` tiled 4× (48
  columns, 8 rows), so every plateau is physically 100 and every cusp has the
  same polarity. **Statistic:** `ppaint_lum` at the centre of each unit's
  physically-100 plateau (row 3, columns 13 / 25 / 37), asked whether they form a
  monotone staircase and in which direction.
- **They are NOT pooled**, and no G2 outcome moves the G1 verdict. G2 is not
  gated because our mechanism has no psychophysical comparator for it in this
  tree, and because the human result there is itself an inversion — a gate would
  mislead in both directions.
- **Registered prediction for G2, stated in advance:** our mechanism produces
  **NO cumulative effect at all** — not an inversion, an ABSENCE — because each
  cusp is a region boundary and regions do not communicate, so cusp steps cannot
  accumulate. Every interior unit is a translate of every other, so all three
  plateaus should paint identically. **If so, the finding is that the very field
  segmentation that fixes single-edge Cornsweet FORBIDS cumulative Cornsweet** —
  the same trade as R5, seen at a different scale. (This is a 1-D sawtooth, NOT
  Cavanagh & Anstis's 2-D diamond stimulus; declared as a bound.)

---

## 5. ARM B — BOUNDS (declared in advance; does NOT move the verdict, §8)

The paint rung's stated bound was *"ONE stimulus per illusion … I3's magnitude
should be expected to depend on cusp width"*. So: the SAME single-edge stimulus
at **three fixed flat-field widths — 3, 6 (the committed one) and 12** — with
`pdecay` 0 and 1. Reported as a scope statement only. Three points, fixed here,
no sweep, no re-runs (§3.6).

---

## 6. ARM V — VACUITY, RUN FIRST (§13.2)

Before any statistic above is believed: toggle `pdecay` 0 → 1 on the Cornsweet
stimulus and measure `D = max|on − off|` on every attribute this rung claims to
affect (`ppaint_lum`, `presid_lum`, `prefuted_cell`, `pdist`, `plam`, `panchor`,
`panch_n`). **`D == 0.0` exactly on the painted channel ⇒ the mechanism is
decorative; STOP and burn no seed.**

And its converse, ARM V2 — **§9 byte-identity**: with `pdecay = 0`,
`results/paint_measure.json` must reproduce **exactly**, key for key, and the
vision bench must stay **222 passed, exit 0**.

---

## 7. n, SEEDS, AND WHAT IS DETERMINISTIC

| arm | n | seeds |
|---|---|---|
| ARM 1, ARM 2, ARM 3b/R5, G2, ARM B, ARM V | 1 (deterministic stimuli, no RNG) | — |
| ARM 3 R1/R2/R3/R4 | 1 field each | **69600** (texture) |
| ARM 3 F1 noise floor | **100** | **69000–69099** |
| ARM 3 F2 texture floor | **100** | **69100–69199** |
| ARM 3b blind-spot (reported only) | 1 | **69500** |

n=100 on F1/F2 mirrors the paint rung's already-powered floors (100/100 and
0/100 there), which is the pilot that fixes it. **69200–69499, 69501–69599,
69601–69999 remain CLEAN.** Every other arm is a deterministic synthetic field
with no RNG, so it carries no CI and none will be quoted.

---

## 8. PREDICTIONS, STATED IN ADVANCE (§3.7), WITH NUMBERS

Computed by hand from the committed mechanism BEFORE writing any code. Being
wrong about these is the informative outcome.

| # | prediction | number |
|---|---|---|
| P1 | ARM 1 passes | `difference = +0.727` (from `2·[(m−100) − s·h/3]` = `2·[1.0 − 0.4242·4.5/3]`) |
| P2 | both hubs at `korder` 2.0 | escalation is untouched by the decay |
| P3 | λ for each Cornsweet far region | `plam = 4.5` exactly (uniform depth 0…9) |
| P4 | ARM 2 passes, both sides | left `\|I\|` = 1.1123, 0.8995, 0.7273, 0.5850, 0.4655, 0.3636 at dist 4…9 |
| P5 | ARM 3 passes; **R1/R2 byte-identical** to the committed run | R2 slope exactly 3.0, residual 0.000 |
| P6 | **R5 REGRESSES** — fit unchanged, rendering damped | slope 3.0 exactly; `presid_mean` 0.000 → ≈1.9; `prefuted` 0 → 1; λ = 1.5 |
| P7 | G2 shows **NO staircase** | the three plateaus paint IDENTICALLY (≈99.895) |
| P8 | ARM B: correct sign at all three widths, decreasing with width | +1.429 (w=3), +0.727 (w=6), +0.294 (w=12); baseline inverted at all three (−1.429, −1.818, −1.617) |
| P9 | ARM V: not decorative | `ppaint_lum` moves; `presid_lum` moves |

**The proviso most likely to break P1/P4:** λ = 4.5 sits below the inversion
threshold λ_crit ≈ 9.9 for this stimulus by a factor of ~2.2. If the anchor set
is not what §1 says — e.g. if the field border, or the *other* side of the cusp,
turns out to anchor the region — λ halves or the profile becomes two-sided and
every number above is wrong. **The anchor set is therefore measured and reported
explicitly, not assumed.**

**The proviso most likely to break P5:** if R2's ramp DOES produce a blocked link
anywhere (it must not — a ramp's |Δ| are all equal, so none is a strict maximum),
`w ≢ 1` and byte-identity fails. `panch_n` is reported for every R arm.

---

## 9. WHAT WOULD MAKE THIS RUNG A FAILURE, AND WHAT EACH FAILURE MEANS

| outcome | meaning, fixed in advance |
|---|---|
| ARM 1 fails (sign still negative) | far-field extrapolation was NOT the (only) cause; the paint rung's second hypothesis is refuted and the percept-order hypothesis is the only survivor |
| ARM 2 fails (non-monotone or sign-crossing) | the total induction is not a decaying profile even with a decaying code — the region-mean offset dominates, and "edge-anchored decay" does not deliver the Blakeslee–McCourt signature |
| ARM 3 regresses | perception-matching and residual-honesty are in STRUCTURAL tension, not separated by a parameter. **This is the more valuable finding and it will be the headline.** |
| all three pass but R5 (3b) regresses | the tension is real but LOCALISED: it costs exactly the bounded-gradient case, and the rung reports the price it paid rather than claiming a free lunch |
| ARM V fails | decorative mechanism; STOP, burn no seed, report |

**No sweep, no re-run, no second decay form.** If `λ/(λ+d)` fails, a different
falloff is a NEW mechanism-level hypothesis needing a NEW pre-registration
(§3.6) — not a parameter search on this one. **The decay will not be chosen to
produce the nicest illusion.**

---

## 10. DELIVERABLES AND PROVENANCE DISCIPLINE

- This file, committed BEFORE any implementation (§3).
- `tools/build_vision_paint.py` (extended) → `seeds/vision_paint.json` v1.1.0.
- `domains/decay_world.py` (new adapter — flag write + read-outs, no decisions).
- `scripts/decay_measure.py` (new runner) → `results/decay_measure.json` (pinned).
- `tests/test_decay_gradient_migrated.py` (new gate).
- `VISION_DECAY_RESULTS.md`.
- **NOT EDITED:** `domains/paint_world.py`, `scripts/paint_measure.py`,
  `tests/test_paint_migrated.py`, and every other rung's seed/adapter/default.
- Provenance pinned to a range with **BOTH endpoints fixed**, neither `HEAD`
  (§12.3); `tests/test_provenance_endpoint_guard_migrated.py` green.
- Vision bench `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0**,
  before and after, with `data/` symlinked (§10.2).
