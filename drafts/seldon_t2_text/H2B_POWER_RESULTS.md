# H2b POWER — RESULTS

Answers `H2B_POWER_PREREG.md` (the contract; nothing above its MEASUREMENT GATE
was edited once numbers existed). Powers the ONE explicitly-unresolved question
of the induced-belief arc — H2b (`grounding_weighted` vs `flat_0.1σ`, both
correctly directed) came back **MIXED / near-tie at 8 realized seeds** and the
results doc itself flagged it under the standing rule *"POWER THE GATE BEFORE
THE ENDGAME — deltas within ~3× the per-episode step are not results."* This
rung powers that gate to **64 seeds** and resolves it.

**RAW_UNRANKABLE.** Every number is on `make_realized_text_aware` — the
direction-aware PROXY, sympathetic to the arm's own decode by construction. It
is NOT the sealed organizer outcome. These are relative, direction-sensitive
calibration instruments.

**Instrument REUSED verbatim.** `measure_h2b_power.py` reuses
`measure_h2_directed`'s `build_units` / `decode_units` / `cell_shift_grid` /
`apply_band_shift_percell`, `make_realized_text_aware`, the REAL scorer
`crps.crps_composite`, and the Phase-5 PIT machinery. The ONLY additions are
(1) 64 seeds instead of 8, and (2) collecting the PAIRED per-seed delta
`d_i = composite_gw(seed_i) − composite_flat(seed_i)` — both arms scored on the
SAME realized draw per seed, so `d_i` is a paired sample and its across-seed
spread is the noise floor. No new metric; no hand-fitting.

---

## The powered grid (22 F3 units, seeds 0–63, n_draws=1000, signed proxy)

Paired `gw − flat` composite delta, mean ± 95% CI (`mean ± 1.96·SE`,
`SE = std(d)/√64`). Positive delta = flat has the LOWER (better) composite.

| p_signal | e | gw comp | flat comp | Δcomp (gw−flat) | 95% CI | verdict |
|---|---|---:|---:|---:|---|---|
| 0.3 | 0.5 | 1.74951 | 1.74920 | +0.000305 | [+0.000014, +0.000596] | **flat<gw** |
| 0.3 | 1.0 | 1.82600 | 1.82522 | +0.000776 | [+0.000436, +0.001117] | **flat<gw** |
| 0.5 | 0.5 | 1.74337 | 1.74282 | +0.000544 | [+0.000260, +0.000827] | **flat<gw** |
| 0.5 | 1.0 | 1.82841 | 1.82710 | +0.001315 | [+0.000987, +0.001642] | **flat<gw** |
| 0.7 | 0.5 | 1.75126 | 1.75021 | +0.001053 | [+0.000777, +0.001328] | **flat<gw** |
| 0.7 | 1.0 | 1.84637 | 1.84408 | +0.002291 | [+0.002000, +0.002582] | **flat<gw** |

**Every 95% CI is entirely above 0.** Flat has the lower composite in 6/6
signalled cells, CI-separated.

### Tail delta (gw − flat), same 64 seeds (negative = gw better tail)

| p_signal | e | Δtail | 95% CI | verdict |
|---|---|---:|---|---|
| 0.3 | 0.5 | +0.000013 | [−0.000627, +0.000653] | TIE |
| 0.3 | 1.0 | +0.000044 | [−0.000579, +0.000667] | TIE |
| 0.5 | 0.5 | −0.000070 | [−0.000725, +0.000586] | TIE |
| 0.5 | 1.0 | +0.000141 | [−0.000552, +0.000833] | TIE |
| 0.7 | 0.5 | +0.000379 | [−0.000339, +0.001097] | TIE |
| 0.7 | 1.0 | +0.000803 | [−0.000035, +0.001640] | TIE |

**Every tail CI straddles 0** — the tail is a genuine tie under power.

---

## H2b-POWER — verdict: **flat-wins on composite (CI-separated 6/6); tail is a genuine tie**

Per the pre-declared criterion (gw-wins iff CI < 0 in a majority; flat-wins iff
CI > 0 in a majority; genuine-tie iff CI straddles 0 in a majority):

- **Composite: FLAT-WINS.** The `gw − flat` composite delta is CI-separated
  ABOVE 0 in **6/6** signalled cells. `flat_0.1σ` is decisively composite-better
  than `grounding_weighted`, everywhere on the swept grid.
- **Tail: GENUINE-TIE.** The tail delta CI straddles 0 in **6/6** cells.
  Grounding-weighting is NOT tail-better under power.

### The 8-seed MIXED verdict was underpowered noise (the headline)

The 8-seed run reported gw winning BOTH criteria in 2/6 cells (`p0.3_e0.5`,
`p0.5_e0.5`), with composite deltas of −0.000457 and −0.000176 (gw better).
**Under power those two cells FLIP sign and CI-separate the other way:**

| cell | 8-seed Δcomp | 64-seed Δcomp | 64-seed 95% CI |
|---|---:|---:|---|
| p0.3_e0.5 | **−0.000457** (gw better) | **+0.000305** | [+0.000014, +0.000596] |
| p0.5_e0.5 | **−0.000176** (gw better) | **+0.000544** | [+0.000260, +0.000827] |
| p0.7_e0.5 | +0.000101 | +0.001053 | [+0.000777, +0.001328] |
| p0.3_e1.0 | +0.000168 | +0.000776 | [+0.000436, +0.001117] |
| p0.5_e1.0 | +0.001101 | +0.001315 | [+0.000987, +0.001642] |
| p0.7_e1.0 | +0.001576 | +0.002291 | [+0.002000, +0.002582] |

The two "gw wins" cells at 8 seeds were sampling noise: at 64 seeds every cell
lands firmly on flat, and the two flipped cells are now CI-separated *above* 0.
This is exactly what "deltas within ~3× the per-episode step are not results"
predicted — the 8-seed near-tie could not see the true sign, and the true sign
is uniformly flat-better on composite.

### The e-crossover dissolves under power

The 8-seed run read a crossover — "gw favoured on tail at e=0.5, flat favoured
on composite at e=1.0." Under power:

- On **composite**, flat wins at BOTH e=0.5 (mean Δ +0.000634) and e=1.0 (mean
  Δ +0.001461) — no crossover; the effect is monotone in e (flat's advantage
  GROWS with effect size), not a sign change.
- On **tail**, both e are a TIE (all CIs straddle 0) — the 8-seed "gw better on
  tail at e=0.5" does not survive power.

So there is no effect-size interaction that reverses the verdict: the
magnitude-policy ordering is flat ≥ gw on composite across the whole grid, and
tie on tail. The interaction the 8-seed run saw was noise.

### Why flat wins (mechanism, consistent with H2's reading)

Both arms are correctly directed; the only difference is magnitude.
`grounding_weight = 0.333` (hops=3) attenuates the gw shift to 0.033σ, a third
of flat's 0.1σ. When the realized signal is real and correctly typed (the
proxy's construction), the FULL flat shift moves further toward the gold outcome
and extracts more composite; the attenuated gw shift UNDER-SHOOTS. Crucially,
`grounding_weight` encodes *the typer's confidence*, not *the effect size* — so
the stronger the effect (higher e) or the more frequent the signal (higher
p_signal), the more gw under-shoots, which is exactly the monotone-in-p-and-e
growth of flat's advantage in the table. This is the H2_RESOLUTION mechanism
claim, now CI-confirmed under power rather than asserted from a near-tie.

---

## What this resolves (localised conclusion)

- **Grounding-weighting is NOT a composite lever, and NOT a tail lever, over a
  flat correctly-directed shift** — CI-separated on composite (flat better),
  tie on tail. The pre-committed H2b flat-wins-branch guidance from
  `H2_RESOLUTION_RESULTS.md` is now the CONFIRMED operational rule, not a
  near-tie best-guess:

  > *Ship a flat shift at the typer's precision for composite; keep
  > `grounding_weight` ONLY for the H3/H2c guard (attenuate-to-0 on ungrounded).*

  Grounding-weighting's proven value is structural safety (H3 shift-ratio → 0 on
  GroundingGap; H2c graceful-under-no-signal), NOT calibration or composite.
- **The remaining composite headroom is the shift MAGNITUDE/SHAPE, not
  grading-vs-flat.** gw under-shoots because it scales by confidence, not effect
  size; a shift that scaled by *estimated effect* (not just grounding
  confidence) is the named next lever — and it is orthogonal to the
  grade-vs-flat question this rung closes.
- **Standing rule vindicated.** The 8-seed MIXED verdict was underpowered; two
  of its cells had the wrong sign. Powering to 64 seeds flipped them and
  CI-separated the whole grid. "Power the gate before the endgame" earned its
  place again.

---

## Proven-vs-assumed ledger

**PROVEN (measured, this run):**
- At 64 seeds, `gw − flat` composite delta is CI-separated above 0 (flat better)
  in 6/6 signalled cells; tail delta straddles 0 (tie) in 6/6. `flat-wins` on
  composite, `genuine-tie` on tail.
- The two 8-seed cells where gw appeared to win (p0.3_e0.5, p0.5_e0.5) flip sign
  and CI-separate the other way under power — the 8-seed MIXED was noise.
- Flat's composite advantage is monotone in both p_signal and e (the
  under-shoot mechanism), CI-separated at every grid point.
- The instrument is reused verbatim; the only additions are 64 seeds and the
  paired-delta CI. H2a (gw beats no_shift) and H2c (graceful) are NOT re-opened
  and stand.

**ASSUMED / RAW_UNRANKABLE:**
- All numbers are on the direction-aware PROXY, whose gold direction IS the
  arm's own decode — sympathetic by construction. It establishes the RELATIVE
  magnitude-policy ordering under the swept `p_signal`/`e` structure; it does
  NOT establish any absolute board score or that this ordering holds against the
  sealed organizer outcome.
- The composite deltas are small in absolute terms (~3e-4 to 2e-3 on a ~1.8
  composite); they are CI-SEPARATED at 64 seeds (SE ~1.5e-4), which is the claim
  — not that the magnitude is large. The operational takeaway (ship flat, keep
  gw for the guard) follows from the SIGN being resolved, not from the size.

## Reproduce

```
PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
  .bigtmp/t2venv/bin/python \
  drafts/seldon_t2_text/induced_belief/measure_h2b_power.py \
  --units .bigtmp/track2/units --select t2-F3 \
  --realized-seeds 0-63 --n-draws 1000 \
  --p-signals 0.3,0.5,0.7 --effects 0.5,1.0 \
  --json-out drafts/seldon_t2_text/induced_belief/h2b_power_results.json
```

Artifacts: `measure_h2b_power.py` (reuses `measure_h2_directed` verbatim),
`induced_belief/h2b_power_results.json` (full grid + paired CIs). The 8-seed
`measure_h2_directed.py` and its `h2_directed_results.json` are left INTACT as
the record of the underpowered near-tie.



---

# ITEM 2 — RESULTS: sweeping the grounding-weight RANGE (is the near-tie a pinned-gw artifact?)

Answers the item-2 ADDENDUM in `H2B_POWER_PREREG.md` (committed above its own
MEASUREMENT GATE (item 2); nothing there edited once these numbers existed). The
seed-power rung above resolved the FIXED-gw question, but the arm's decoded
`grounding_weight` is a **constant 0.3333** in this harness (verified: all 12
signalled units, hops=3, marginal saturated → `min(1,|m|)·(1/3)=0.333`, zero
cross-unit variance). This rung asks whether the flat-win is an artifact of that
pin by making the gw magnitude a SWEPT quantity spanning a real range.

**RAW_UNRANKABLE.** Direction-aware PROXY (`make_realized_text_aware`),
sympathetic to the arm's decode by construction; NOT the sealed board.

**Instrument REUSED verbatim.** `measure_h2b_gwrange.py` reuses
`measure_h2_directed`'s `build_units` / `decode_units` (REAL arm decode;
**direction unchanged — still the arm's OWN decoded sign**) /
`apply_band_shift_percell`, `make_realized_text_aware`, the REAL scorer
`crps.crps_composite`, and the SAME 64-seed paired-delta CI protocol. The ONLY
override is the gw arm's MAGNITUDE: `flat × w` (GLOBAL-W) or `flat × w_unit`
(signal-TRACKING), instead of `flat × 0.333`. flat is the identical flat arm.

## Two built-in sanity checks (both PASS)

- **`w=1.0` ⇒ gw ≡ flat.** All six p/e cells give `d_comp` = **+0.000000**
  exactly (TIE). Definitional: at weight 1.0 the graded arm IS the flat arm.
- **`w=0.333` reproduces the seed-power gw−flat delta** to ~1e-6 (e.g.
  p0.5_e1.0: gwrange +0.001316 vs power +0.001315). The tiny residual is
  `flat×0.333` recomputed vs the power harness reading `arm.shift=0.333333`;
  the two harnesses agree — neither is fabricated.

## (A) GLOBAL-W sweep — `d_comp = composite(flat×w) − composite(flat)`, 64-seed 95% CI

Positive = flat has the LOWER (better) composite. `gw<flat` = graded CI-beats flat.

| w | p0.3_e0.5 | p0.3_e1.0 | p0.5_e0.5 | p0.5_e1.0 | p0.7_e0.5 | p0.7_e1.0 |
|---:|---|---|---|---|---|---|
| 0.200 | +0.000511 flat | +0.001070 flat | +0.000789 flat | +0.001802 flat | +0.001411 flat | +0.002965 flat |
| 0.333 | +0.000305 flat | +0.000777 flat | +0.000544 flat | +0.001316 flat | +0.001053 flat | +0.002293 flat |
| 0.400 | +0.000192 **TIE** | +0.000650 flat | +0.000430 flat | +0.001137 flat | +0.000876 flat | +0.001985 flat |
| 0.600 | −0.000077 **TIE** | +0.000229 flat | +0.000075 **TIE** | +0.000566 flat | +0.000380 flat | +0.001164 flat |
| 0.800 | **−0.000124 gw** | −0.000011 **TIE** | −0.000049 **TIE** | +0.000162 flat | +0.000112 flat | +0.000514 flat |
| 1.000 | +0.000000 **TIE** | +0.000000 **TIE** | +0.000000 **TIE** | +0.000000 **TIE** | +0.000000 **TIE** | +0.000000 **TIE** |

Per-w summary (mean `d_comp` across the 6 p/e cells; cell verdict counts):

| w | mean d_comp | gw<flat | flat<gw | TIE |
|---:|---:|:---:|:---:|:---:|
| 0.200 | +0.001425 | 0 | 6 | 0 |
| 0.333 | +0.001048 | 0 | 6 | 0 |
| 0.400 | +0.000878 | 0 | 5 | 1 |
| 0.600 | +0.000389 | 0 | 4 | 2 |
| 0.800 | +0.000101 | **1** | 3 | 2 |
| 1.000 | +0.000000 | 0 | 0 | 6 |

The curve is **monotone in w**: `mean d_comp` decreases smoothly from +0.00143
(w=0.2) to exactly 0 (w=1.0). Flat's advantage is largest when the grade
attenuates hardest, and vanishes precisely as the grade approaches 1.0 — where
the "graded" arm has become the flat arm. Across the ENTIRE range only **1 of 36
(w,p,e) cells** CI-separates gw below flat (w=0.8, p0.3, e0.5, by −0.000124), and
that single cell is bracketed by TIEs and does not carry a majority at any w.

## (B) signal-TRACKING per-unit weights spanning [0.2, 1.0]

Per-unit `w` assigned by signal-strength rank (deterministic, not fit to any
outcome), so the grade genuinely VARIES across units (0.200 … 1.000) instead of
sitting at 0.333:

`d_comp = composite(gw_tracking) − composite(flat)`, 64-seed 95% CI:

| p_signal | e | Δcomp (gw−flat) | 95% CI | verdict |
|---|---|---:|---|---|
| 0.3 | 0.5 | +0.000106 | [−0.000176, +0.000389] | TIE |
| 0.3 | 1.0 | +0.000473 | [+0.000148, +0.000798] | flat<gw |
| 0.5 | 0.5 | +0.000298 | [+0.000018, +0.000579] | flat<gw |
| 0.5 | 1.0 | +0.000899 | [+0.000577, +0.001220] | flat<gw |
| 0.7 | 0.5 | +0.000672 | [+0.000411, +0.000932] | flat<gw |
| 0.7 | 1.0 | +0.001577 | [+0.001290, +0.001864] | flat<gw |

**flat wins 5/6, one TIE, gw wins 0/6.** A weight that TRACKS the signal across
a full [0.2,1.0] range does NOT beat flat either — it lands between the w=0.2 and
w=0.8 global rows, exactly as a per-unit average of that range should.

## item2-GW-RANGE — verdict: **flat-robust** (the near-tie is NOT a pinned-gw artifact)

Per the pre-declared criterion (gw-can-win iff some w/tracking gives CI<0 in a
MAJORITY of cells; flat-robust iff flat CI-wins-or-ties at every w):

- **No graded weight in [0.2, 1.0] CI-beats flat in a majority of cells.** At
  every w the majority verdict is flat-wins or (near w=1.0) tie. The single
  gw<flat cell (w=0.8) is isolated. The signal-tracking variant is flat-wins
  5/6. **flat-robust CONFIRMED.**
- **The grade can, at best, TIE flat — by BECOMING flat (w→1.0).** The `mean
  d_comp(w)` curve is monotone and asymptotes to 0 from above; it never crosses
  materially below 0. There is no interior optimum where grading beats flat.

So the H2b near-tie was **not** an artifact of `grounding_weight` being pinned
low at 0.333. Raising the grade does not "unlock" a graded win — it merely walks
the graded arm toward the flat arm, which is the ceiling. Within the class
`flat × w, w ∈ [0,1]`, **flat (w=1) is the composite-optimal member**, and any
attenuation (w<1) strictly costs composite on this direction-aware proxy,
monotonically in how much it attenuates. This is the CI-backed, powered form of
the H2 mechanism reading ("gw under-shoots because it scales by confidence, not
effect size"): confidence-scaling can only shrink the correctly-directed shift,
and shrinking a correctly-directed shift can only lose composite here.

### Why this is the honest ceiling, and what it does NOT say

The proxy is direction-aware and the shift direction is correct, so a LARGER
correctly-directed shift moves further toward the gold outcome — hence w=1 (=
flat) dominates within [0,1]. This says grading DOWN from flat never helps on
composite. It does NOT say "shift harder than flat is better in general": the
`e=1.0` cells show flat's advantage GROWS with effect size, i.e. even the full
0.1σ flat shift is UNDER-shooting a strong realized effect. That is the named
next lever — a shift that scales by ESTIMATED EFFECT (a magnitude that can exceed
flat, outside the `[0,1]×flat` class this rung sweeps) — and it is orthogonal to
the grade-vs-flat question, which is now closed in BOTH the fixed-gw (seed-power)
and full-range (this rung) senses.

## Combined H2b verdict (seed-power + gw-range), CI-backed

Grounding-weighting is **CI-inseparable-from-or-worse-than flat on composite**,
and this is **robust to power (64 seeds) AND to the grounding-weight range
(0.2..1.0, global and signal-tracking)**:

- **Fixed gw (0.333), 64 seeds:** flat CI-wins on composite 6/6; tail tie 6/6.
- **gw range [0.2,1.0], 64 seeds:** flat CI-wins-or-ties at every w; graded
  CI-beats flat in only 1/36 cells; grade's best case is to TIE flat by
  converging to it (w→1). Signal-tracking grade: flat 5/6, tie 1/6.

**There is no direction (fixed value OR swept range OR signal-tracking) in which
grounding-weighting CI-separates ABOVE flat on composite.** It is a
CI-inseparable tie only in the degenerate limit where the grade becomes flat;
everywhere else flat is CI-better. Grounding-weighting's justified value is
therefore its **tail-calibration/guard role only** — the H3 shift-ratio→0 on
GroundingGap and the H2c graceful-under-no-signal attenuation — **not composite
lift**, exactly as the standing rule demanded be settled before the endgame.

## Proven-vs-assumed ledger (item 2)

**PROVEN (measured, this run):**
- The arm's decoded `grounding_weight` is a constant 0.3333 across all 12
  signalled F3 units (zero variance) — the item-2 premise holds in code.
- Over `w ∈ {0.2,0.333,0.4,0.6,0.8,1.0}`, `mean d_comp(w)` is monotone,
  +0.00143 → 0.0, CI-separated flat<gw at low w, TIE at w→1; only 1/36 cells
  CI-separate gw<flat. Signal-tracking grade over [0.2,1.0]: flat 5/6, tie 1/6.
- Sanity checks pass: `w=1.0` gives d_comp=0.000000 exactly (6/6);
  `w=0.333` reproduces the seed-power delta to ~1e-6.
- Verdict: **flat-robust** — the flat-vs-graded composite verdict does NOT
  depend on the specific 0.333 pin; flat (w=1) is composite-optimal within
  `flat×[0,1]`, and any attenuation strictly costs composite here.

**ASSUMED / RAW_UNRANKABLE:**
- All numbers are on the direction-aware PROXY whose gold direction IS the arm's
  own decode — sympathetic by construction. It establishes the RELATIVE ordering
  of magnitude policies within `flat×[0,1]`; it does NOT establish any absolute
  board score, nor that shifting HARDER than flat (outside this class, e.g.
  effect-scaled) would or would not help against the sealed organizer outcome.
- The deltas are small in absolute terms (~1e-4 to 3e-3 on a ~1.8 composite);
  the claim is the SIGN/CI-ordering (flat ≥ graded, monotone in attenuation),
  not the magnitude.

## Reproduce (item 2)

```
PYTHONPATH=runners/dsl/python:.bigtmp/track2 OZMA_SEED_PERSIST_DISABLED=1 \
  .bigtmp/t2venv/bin/python \
  drafts/seldon_t2_text/induced_belief/measure_h2b_gwrange.py \
  --units .bigtmp/track2/units --select t2-F3 \
  --realized-seeds 0-63 --n-draws 1000 \
  --p-signals 0.3,0.5,0.7 --effects 0.5,1.0 \
  --gw-values 0.2,0.333,0.4,0.6,0.8,1.0 --gw-range 0.2,1.0 \
  --json-out drafts/seldon_t2_text/induced_belief/h2b_gwrange_results.json
```

Artifacts: `measure_h2b_gwrange.py` (reuses `measure_h2_directed` verbatim;
overrides ONLY the gw magnitude), `induced_belief/h2b_gwrange_results.json`
(full `w × p × e` grid + tracking grid + both sanity checks). The seed-power
`measure_h2b_power.py` and its json are left INTACT.
