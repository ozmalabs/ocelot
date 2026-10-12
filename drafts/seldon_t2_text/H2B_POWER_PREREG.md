# PREREG — powering H2b (grounding-weighted vs flat) above the 8-seed noise floor

**Committed BEFORE any powered number.** PREREG-then-measure + CLAUDE.md. This
resolves the ONE explicitly-unresolved question the induced-belief arc left:
H2b (`H2_RESOLUTION_RESULTS.md`) came back **MIXED / near-tie** at 8 realized
seeds — `grounding_weighted` won BOTH criteria in 2/6 cells, flat in the rest,
per-cell deltas ~1e-4 to 1.5e-3. The results doc itself flagged this under the
standing CLAUDE.md rule: *"POWER THE GATE BEFORE THE ENDGAME — deltas within
~3× the per-episode step are not results"* and called H2b a directional
structure, not a CI-separated win. This rung powers exactly that gate.

## What is (and is NOT) under test

- **NOT re-opened:** H2a (gw beats no_shift under signal — CONFIRMED 6/6) and
  H2c (graceful under no signal — CONFIRMED). Those are robust and stand.
- **Under test:** H2b only — `grounding_weighted` vs `flat_0.1sigma`, BOTH
  correctly directed (identical direction; the ONLY difference is the magnitude
  policy: flat 0.1σ vs 0.1σ × grounding_weight). The 8-seed run could not
  separate them. Does more power separate them, or is it a genuine tie?

## The instrument (UNCHANGED — power only, no new metric)

Reuse `measure_h2_directed.py` / `make_realized_text_aware` / the REAL scorer
`crps.crps_composite` / the Phase-5 PIT-KS machinery VERBATIM. The ONLY change
is (a) many more realized seeds and (b) collecting the PAIRED per-seed
`gw − flat` composite and tail deltas so a confidence interval is computable.
The per-seed pairing is legitimate: both arms are scored on the SAME realized
draw for a given seed (same `make_realized_text_aware` output), so their
difference is a paired sample and its across-seed spread is the noise floor.
`make_realized_text_aware` is deterministic per seed; all three RNGs
(proxy `1e6+seed`, selection `2e6+seed`, PIT `7e3+seed`) are seed-derived and
independent, so seeds are independent replicates that cleanly average down.

## Power protocol (fixed before measuring)

- Realized seeds: **0…63** (64 seeds), an 8× increase over the original 8.
  Report the 8-seed vs 64-seed means side by side so the power gain is visible.
- Sweep the SAME grid the original used: `p_signal ∈ {0.3,0.5,0.7}`,
  `e ∈ {0.5,1.0}` (the signalled cells; `p_signal=0` is the H2c floor, reported
  but not part of the H2b verdict). `n_draws=1000`, `flat_shift=0.1σ`,
  `realized_mode=signed`, `--select t2-F3`.
- Per signalled cell, compute the paired per-seed delta `d_i = composite_gw(seed_i)
  − composite_flat(seed_i)` across the 64 seeds, and report mean(d), the
  standard error `SE = std(d)/√64`, and the 95% interval `mean(d) ± 1.96·SE`.
  Likewise for tail.

## Hypothesis (falsifiable, pre-declared)

- **H2b-POWER:** with 64 seeds, is the `gw − flat` composite delta
  CI-SEPARATED from 0 in a consistent direction across the signalled grid?
  - **gw-wins** iff the 95% CI for `mean(d_composite)` is entirely < 0 in a
    MAJORITY of signalled cells AND tail is within the pre-declared 5% tol.
  - **flat-wins** iff the 95% CI is entirely > 0 in a majority of signalled
    cells.
  - **genuine-tie** iff the 95% CI straddles 0 in a majority of cells (the
    near-tie survives power — the two magnitude policies are statistically
    indistinguishable on composite at this proxy structure). THIS IS A VALID,
    PRE-COMMITTED FINDING, not a failure: it would confirm the original
    MIXED verdict was the real answer, now with the power to say so.
  - Report the e=0.5 vs e=1.0 split separately: the 8-seed run saw
    gw-favoured-on-tail at e=0.5 and flat-favoured-on-composite at e=1.0. Does
    that crossover survive power (a real effect-size interaction) or dissolve
    into one verdict?

## What a null / tie means (pre-committed)

- **genuine-tie under power** → the pre-committed H2b flat-wins-branch guidance
  from `H2_RESOLUTION` still applies operationally: *ship a flat shift at the
  typer's precision for composite; keep `grounding_weight` for the H3/H2c
  guard (attenuate-to-0 on ungrounded).* The tie means grounding-weighting is
  not a composite lever OR a composite liability — it is calibration/guard
  machinery, confirmed under power. Localises remaining composite headroom to
  the shift MAGNITUDE/SHAPE (grounding_weight attenuates by confidence, not
  effect size), not to grading-vs-flat.
- **crossover survives** → e is a real interaction; the operational rule
  becomes effect-size-aware (grade at modest effect, flat at strong), reported
  as a measured interaction not a tuned one.

## Discipline

- RAW_UNRANKABLE stated on every number (direction-aware PROXY, sympathetic to
  the arm's decode by construction; NOT the sealed board).
- The instrument is REUSED verbatim; the only additions are more seeds + the
  paired-delta collection. No metric invented. No hand-fitting to a cell.
- No fabricated numbers; the tie is a finding; proven vs assumed explicit.

## Deliverables

- `H2B_POWER_RESULTS.md` — the 64-seed paired-delta CIs per signalled cell,
  the 8-vs-64-seed comparison, the H2b-POWER verdict (gw-wins / flat-wins /
  genuine-tie), the e-crossover check, and the proven-vs-assumed ledger.
- `induced_belief/measure_h2b_power.py` (a thin power harness that reuses
  `measure_h2_directed`'s cell machinery at seed granularity) +
  `induced_belief/h2b_power_results.json`.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.



---

# ADDENDUM — item 2: sweep the grounding-weight RANGE (does the near-tie survive if gw TRACKS the signal?)

**Committed BEFORE the item-2 numbers.** The seed-power rung above resolved the
fixed-gw question (flat-wins on composite, CI-separated 6/6; tail-tie). But it
used the arm's OWN decoded `grounding_weight`, which in THIS harness is a
CONSTANT **0.3333** for every one of the 12 signalled units:

```
grounding_weight = min(1.0, |marginal|) * hop_discount
hop_discount     = 1 / (1 + (hops - 1))     # every grounded read hits the
                                            # SensorAnchor at hops=3 -> 1/3
min(1.0, |marginal|) = 1.0                  # marginal saturates after CAN relax
=> grounding_weight = 0.3333, ZERO cross-unit variance
```

So the powered "grounding_weighted" arm was literally `flat * 0.333` — a fixed
3x attenuation, not a graded quantity that varies with signal. H2b's mechanism
claim ("gw attenuates by confidence, not effect size, so it under-shoots strong
signals") predicts the near-tie / flat-win is BECAUSE gw is pinned near-constant
and low. This addendum tests that mechanism directly, before looking at its
numbers.

## What is under test (item 2)

Whether the flat-vs-graded verdict is an artifact of `grounding_weight` being
pinned at 0.333, by making the gw MAGNITUDE a swept quantity that spans a real
range, and asking whether ANY point in that range — or a signal-TRACKING
weight — flips the composite verdict vs flat.

## Instrument (REUSED verbatim; only the gw MAGNITUDE is overridden)

`measure_h2b_gwrange.py` reuses `measure_h2_directed`'s `build_units`,
`decode_units` (the REAL arm decode — **direction is still the arm's OWN decoded
direction, unchanged**), `apply_band_shift_percell`, `make_realized_text_aware`,
the REAL scorer `crps.crps_composite`, and the same per-seed paired-delta CI
protocol as the seed-power rung (64 seeds, `d_i = comp_gw − comp_flat` on the
SAME realized draw). The ONLY change is the gw arm's magnitude policy:

- **GLOBAL-W:** gw arm = `flat × w` for a swept scalar `w`, over
  `{0.2, 0.333, 0.4, 0.6, 0.8, 1.0}`. Direction unchanged (arm's decoded sign).
  `w=0.333` MUST reproduce the seed-power gw−flat delta (a cross-check);
  `w=1.0` MUST give delta exactly 0 (gw≡flat) — two built-in sanity checks.
- **TRACKING:** per-signalled-unit `w` spanning `[0.2, 1.0]`, assigned by a
  signal-strength rank (the "stronger anchor → larger weight" design H2b names),
  deterministic per unit and NOT fit to any realized outcome. Tests whether a
  weight that TRACKS the signal (instead of being pinned) beats flat.

flat is the SAME unchanged flat arm in both. No new metric; no hand-fitting; the
whole `(w × p_signal × e)` grid is reported.

## Hypothesis (falsifiable, pre-declared)

- **item2-GW-RANGE:** across `w ∈ [0.2, 1.0]` and the signalled `p_signal/e`
  grid, is there ANY graded weight for which `gw − flat` composite CI-separates
  BELOW 0 (graded genuinely beats flat) in a majority of cells?
  - **gw-can-win** iff some `w` (or the tracking assignment) gives a CI < 0 in a
    majority of signalled cells — the near-tie WAS a pinned-gw artifact; a
    signal-tracking grade is a real composite lever.
  - **flat-robust** iff flat CI-wins or ties at every `w` (graded never
    CI-beats flat broadly) — the flat-vs-graded verdict is ROBUST to the
    grounding-weight range; the near-tie is not a pinned-gw artifact, grading is
    composite-dominated-by-or-equal-to flat regardless of the weight. THIS IS A
    VALID, PRE-COMMITTED FINDING (it would confirm the seed-power verdict is not
    an artifact of the specific 0.333 value).
  - Report `mean d_comp(w)` as a monotone-in-w curve; the `w=1.0`→0 and
    `w=0.333`→(power delta) checks must hold or the harness is wrong.

## What flat-robust means (pre-committed)

If graded never CI-beats flat across the whole range, the operational guidance
from the seed-power rung stands UNCONDITIONALLY on the grade-vs-flat axis: ship
flat for composite; keep `grounding_weight` only for the H3/H2c guard. It would
further mean the remaining composite headroom is NOT "grade harder / grade
differently within [0,1]" but a shift that scales by ESTIMATED EFFECT (a
quantity outside [0,1]×flat), which is orthogonal to this rung.

## Discipline

RAW_UNRANKABLE on every number (direction-aware PROXY, sympathetic to the arm's
decode by construction; NOT the sealed board). Instrument reused verbatim; only
the gw magnitude swept. No fabricated numbers; a flat-robust result is a
finding; the two sanity checks (`w=1.0`→0, `w=0.333`→power delta) are reported.

## Deliverables (item 2)

- item-2 section appended to `H2B_POWER_RESULTS.md` (the `(w × p_signal × e)`
  grid, the `mean d_comp(w)` curve, the tracking-variant grid, the two sanity
  checks, the item2-GW-RANGE verdict).
- `induced_belief/measure_h2b_gwrange.py` +
  `induced_belief/h2b_gwrange_results.json`.

---
MEASUREMENT GATE (item 2) — nothing above this line is edited once the item-2 numbers exist.
