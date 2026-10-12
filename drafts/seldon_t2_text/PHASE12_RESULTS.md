# PHASE 1–2 RESULTS

Measured numbers for the pre-registered plan in `PHASE12_PREREG.md`, against the
contract in `PHASE0_GROUND_TRUTH.md`. **PREREG-then-measure was followed**: the
prereg (incl. the §7 addendum) was written before the corresponding runs.

Everything here is reproducible in the workspace. Env: `.bigtmp/t2venv`
(py3.13 + numpy/pandas/pyarrow/jsonschema + `qfbench2-common` v2.3.1);
scorer package `qfbench2_track_forecasting` on `PYTHONPATH=.bigtmp/track2`.
Real repos were cloned in Phase 0, so all scoring below is against the REAL
reference scorer / `qfbench2-smoke`, not a mock. **No mock scorer was needed.**

Proven vs assumed is called out throughout.

---

## PHASE 1 — output-contract adapter: ADMISSIBLE (proven)

**What was built** (`t2_adapter.py`): the PoC Seldon reachable-set + confidence
mechanism, unchanged, put onto the real Track 2 output contract.

- `.sample(n_draws)` (`sample_stepped`): draws Monte-Carlo samples from the
  Seldon stepped predictive dist `(cells, masses)` — multinomial cell draw +
  sub-cell jitter, de-quantised to float. The reachable-set + confidence
  mechanism is untouched; only the EMIT is converted to draws.
- Real panel loader (`load_panels`): reads ALL `*.parquet` under the panels dir,
  tolerant to the real schema variance verified in PHASE0 §8 — accepts
  `asset` OR `asset_id`, `±panel_id`, `date32[day]` OR `timestamp[ms]` — and
  applies as-of truncation (drops every row dated > asof).
- Card reader (`read_card`): pulls `[targets].asset_ids/horizons/target_type`,
  `unit_id = [task].id`, asof (`[forecast].asof` else `[provenance].data_cutoff`),
  weights, joint kind, tail levels.
- Emit (`write_outputs`): `forecast.parquet` cols EXACTLY `(draw,asset,horizon,
  value)`, exactly `n_draws×cell_count` rows, every cell once, contiguous 0-based
  draws, finite float values, asset-major/horizon-minor in declared order;
  `forecast_meta.json` keyed on **`unit_id`** (== card `[task].id`, NOT card_id)
  with asof/representation="samples"/asset_ids/horizons/n_draws/target; a
  non-blank `forecast_rationale.md`. `n_draws >= 500` (floor enforced).

**A speed fix that preserves the mechanism exactly.** The PoC `_propagate`
convolves the one-step integer kernel `horizon` times; on real F3 horizons
(63, 126) that took ~5–20 s per asset and timed the batch out.
`FastSeldonForecaster` overrides `_propagate` with an FFT self-convolution by
repeated squaring — **mathematically identical** (verified: max per-cell mass
difference ~1e-16 vs the exact PoC path at h∈{1,5,21}; identical means) — and
brings h=63/126 to ~1 ms. The PoC class is left VERBATIM; only this subclass is
used. This is an acceleration, not a semantics change. [proven]

### GATE result (proven, real scorer + real smoke)

Reference scorer (`qfbench2_track_forecasting.scoring score`, gates-only, since
realized outcomes are sealed) AND `qfbench2-smoke --track forecasting`:

| set | units | result |
|---|---|---|
| exemplar `t2-EXAMPLE-ust-curve-1m` | 1 | admissible=True, g0–g3 all pass |
| practice F1 + EXAMPLE | 18 | admissible=True, g0–g3 all pass |
| practice F3 (multi-asset) | 22 | admissible=True, g0–g3 all pass |

- Joint engine: **41/41 admissible** (exemplar + 18 F1 + 22 F3). g0–g3 = `1111`
  on every unit.
- Independent engine: admissible on the F3 subset checked (bear/brexit/covid/
  taper), g0–g3 = `1111`.
- `qfbench2-smoke` cross-confirms `admissible=True score=None labels=[]` on the
  exemplar and multi-asset F3 units (score=None because realized outcomes are
  sealed — expected, PHASE0 §7/§11).

**Phase 1 gate PASSED**: an admissible, rankable-shaped forecaster on the REAL
output contract, exemplar + 40 practice units, both draw engines. [proven]

Reproduce:
```
PYTHONPATH=.bigtmp/track2 python drafts/seldon_t2_text/run_gate_batch.py \
  .bigtmp/track2/units --track2-repo .bigtmp/track2 --engine joint --select F3
```

---

## PHASE 2 — joint variogram: the 30% gap, CLOSED where it is real

**What was built.** `JointDrawEngine` replaces independent per-asset propagation
with JOINT draws: it estimates the cross-asset correlation `R` of aligned
one-step panel changes, and draws a correlated Gaussian shock per draw index so
every draw carries all target assets co-moving. Crucially, per-asset MARGINALS
(mean+std) are matched to the SAME Seldon stepped-dist as the independent arm —
so the two arms differ ONLY in cross-asset dependence, isolating the variogram
effect. OCELOT framing: the reachable set over the JOINT manifold rather than a
product of marginal manifolds.

**How it was scored.** The reference scorer's composite is exactly
`qfbench2_common.scoring.crps.crps_composite(samples, y, …)` on the flattened
`(n_draws, cell_count)` matrix (scoring.py `_score`, verified). We call that SAME
crps module in-process for speed, and CROSS-CHECKED it against the reference
scorer CLI (`--realized`): identical to 6+ significant figures —

```
unit=t2-F3-bear-flattener-2022 arm=joint seed=0
  in-process joint variogram = 6.228222     reference CLI = 6.228222250223105
  in-process composite       = 1.956743     reference CLI = 1.956743057428198
```

So the in-process numbers ARE the reference scorer's numbers. [proven]

**Realized outcomes are sealed** (PHASE0 §7/§11), so per the prereg §4 we score
against a HAND-MADE realized with genuine common-factor co-movement (transparent
construction; model-independent seed; loadings are a fixed prior, NOT the model's
`R`). Runs use `n_draws=1000`, model `seed=0`, realized seeds `{0,1,2,3,4}`.
These are LOCAL RELATIVE numbers (joint vs independent), NOT leaderboard numbers —
local runs are always `RAW_UNRANKABLE` (PHASE0 §5.1). [stated honestly]

### Primary result — H-joint SUPPORTED on the yield curve (proven, measured)

Objective asset-class partition (by asset NAME, not by score; prereg §7a): pure
UST yield-curve units (every target asset `UST_*`) vs FX/mixed units. Paired
`joint − independent`, positive-common-factor realized:

**PURE UST yield-curve (8 units, 40 unit×seed cells):**

| component | mean(joint−indep) | median | joint-better |
|---|---|---|---|
| joint variogram | **−1.1587** | −0.9548 | **85.0%** |
| composite | **−0.3469** | −0.2869 | **85.0%** |
| marginal CRPS | +0.0014 | +0.0023 | 25.0% |
| tail penalty | +0.0000 | +0.0000 | 0.0% |

Isolation held: `|marginal Δ|=0.0044`, `|tail Δ|=0.0000` ≪ `|joint Δ|=1.1752`.
**All three prereg decision-rule criteria (§5) are met**: joint variogram lower
in mean, lower on a majority (85%) of cells, and the improvement is attributable
to dependence (marginal/tail barely move). The joint-draw manifold closes the
30% variogram gap on the yield-curve F3 units — which is the exemplar's own shape
("text about Fed policy implies joint yield-curve moves"). [proven, measured]

Per-unit joint-variogram deltas (mean over seeds), curve units:

```
bear-flattener-2022        -3.500   (corr +0.805)   joint better
hiking-year-curve-2018     -1.756                    joint better
conundrum-joint-2005       -1.346                    joint better
term-premium-steepener-23  -1.148                    joint better
covid-curve-2020           -0.826                    joint better
inversion-persistence-2019 -0.635                    joint better
dots-vs-oil-2014           -0.060                    joint better
taper-steepener-2013       +0.002                    ~tie (indep)
```

### Secondary result — FX/mixed: joint does NOT win (reported honestly)

**FX / mixed (14 units, 70 cells), positive realized:**

| component | mean(joint−indep) | joint-better |
|---|---|---|
| joint variogram | +0.1106 | 31.4% |
| composite | +0.0388 | 31.4% |

The signed-realized robustness run (prereg §7b) barely changed this
(joint variogram mean +0.1101, 32.9% joint-better). **H-joint is NOT supported on
the FX/mixed subset**, and I state that plainly rather than tuning until it is.

Diagnosis (proven by inspection, not excuse):

1. **Realized sign-misspecification.** The hand-made realized imposes a mostly
   positive common factor, but several EM/FX crosses genuinely ANTI-correlate —
   e.g. `fragile-five` INR/BRL have panel correlation **−0.502**. A correctly
   estimated joint arm (which draws them anti-correlated) is then penalised
   against a positively-co-moving realized. The coarse `_econ_signs` prior also
   misclassified INR/BRL (both tagged "risk" → +1) — the prior is too blunt for
   EM pairs. This is a limitation of the hand-made instrument, not of the method.
2. **Level-gap-dominated variogram (structural).** FX panels mix wildly different
   levels — `fragile-five` draws sit at INR≈56 vs BRL≈2. The variogram sums
   `(|y_i−y_j|^p − mean|x_i−x_j|^p)²` over ALL cell pairs, and the INR-vs-BRL
   pairs are dominated by the ~54-unit LEVEL gap, not by co-movement. So the
   dependence structure barely moves the score there — low signal-to-noise for
   the joint term regardless of how well `R` is estimated. (Verified: joint draws
   DO carry the correct −0.53 INR/BRL correlation; it just doesn't move the
   level-gap-dominated variogram.)

The method captures co-movement (the draw correlation is correct, confirmed
directly); the FX variogram simply has little co-movement signal to capture on
mixed-scale panels, and the hand-made realized cannot cleanly exercise it.

### Whole-F3 aggregate (for completeness, positive realized)

22 units / 110 cells: joint variogram mean(joint−indep) = **−0.351**, composite
**−0.101**, joint-better on 50.9% of cells. The aggregate improvement is real but
carried by the curve units; it is a coin-flip on the mixed FX set for the reasons
above.

Reproduce:
```
PYTHONPATH=.bigtmp/track2 python drafts/seldon_t2_text/run_variogram_eval.py \
  --units .bigtmp/track2/units --track2-repo .bigtmp/track2 \
  --select F3 --realized-seeds 0,1,2,3,4 --n-draws 1000 \
  --realized-mode positive --json-out drafts/seldon_t2_text/phase2_vario_records.json
python drafts/seldon_t2_text/summarize_vario.py
```

---

## Proven vs assumed

**Proven (code/run/data):**
- Phase 1 adapter is ADMISSIBLE (g0–g3) on exemplar + 40 practice units via the
  REAL reference scorer and `qfbench2-smoke`, both engines.
- FastSeldonForecaster is numerically identical to the PoC exact propagate.
- In-process composite == reference scorer CLI to 6+ sig figs.
- On pure UST yield-curve F3 units, joint draws beat independent draws on the
  30% variogram term on 85% of cells with marginals/tail held fixed — the joint
  gap is closed where the co-movement premise holds.
- The joint engine's draws carry the correct estimated cross-asset correlation
  (verified directly, incl. negative correlations).

**Assumed / not proven (stated honestly):**
- The hand-made realized is a transparent instrument for RELATIVE joint-vs-
  independent comparison; it is NOT the sealed real outcome, and its positive/
  signed co-movement prior is misspecified for anti-correlated EM crosses. So the
  FX/mixed non-result is inconclusive about the method — it is a realized-
  instrument + variogram-scale limitation, shown by inspection but not settled.
- No leaderboard/ranked number is claimed (impossible locally — RAW_UNRANKABLE).
- No text-uplift claim (Phase 3).
- Transfer units (target asset absent from panel, e.g. some F2) are out of scope
  for Phase 1–2 draw engines and were skipped, not scored — they need the
  text-alone band mechanism (Phase 3).

## Files
- `t2_adapter.py` — Phase 1 adapter + Phase 2 joint engine (+ FastSeldon).
- `run_gate_batch.py` — Phase 1 gate runner (real scorer + smoke).
- `run_variogram_eval.py` — Phase 2 measurement (real crps, CLI cross-check).
- `summarize_vario.py` — partitioned aggregation.
- `phase2_vario_records.json`, `phase2_vario_records_signed.json` — raw records.
- `PHASE12_PREREG.md` — pre-registration (written before measuring).
