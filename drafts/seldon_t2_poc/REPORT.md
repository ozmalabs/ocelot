# PoC: Agenthon 2026 Track T2 as a "Seldon manifold with a confidence dimension"

**Status:** empirical PoC / mechanism study. Synthetic data with a known
generating process. **Not** a benchmark submission and **not** evidence of
benchmark value. Read the verdict section literally.

**What this PoC set out to raise or lower confidence in:** whether the T2
forecasting task (probabilistic panel forecasts, CRPS-scored, as-of cutoff,
calibration gate, text-uplift over text-blind baselines) can be implemented as
OCELOT's proposed "reachable-set-plus-confidence" forecast object, and whether
each of the four load-bearing claims holds:

- (a) the object can be **emitted as a valid probabilistic forecast**,
- (b) it can be **scored by CRPS**,
- (c) it can be **calibrated**,
- (d) it can **extract text-driven uplift** over a text-blind baseline.

## The framing under test

A **Seldon manifold** (from `papers/formal/02_seldon_manifolds_theory_referenced.tex`)
is a time-indexed *reachable set* — the set of futures reachable from now over a
horizon `h`, at operative resolution `ρ` — of which a hurricane cone of
uncertainty is the everyday instance. The theory paper explicitly states that
**probability is an optional "epistemic overlay on the reachable family,"** not a
substrate primitive.

The OCELOT-native T2 framing operationalises that overlay as a **confidence
dimension**: a *stepped credence mass* assigned across the reachable integer
cells at each future time slice. Because OCELOT's frame/continuum invariant keeps
in-frame values **integer at operative resolution**
(`docs/features/dynamic-quantization.md`), the resulting predictive distribution
is *natively* a stepped / empirical CDF — and CRPS is exactly, closed-form
defined on that object. Calibration becomes a well-formedness property of the
confidence dimension. Text uplift = the text corpus shifts/sharpens the
confidence mass.

## What was built (all standalone Python + numpy; no substrate_rs)

| File | Role |
|---|---|
| `crps.py` | Closed-form CRPS for stepped `(value, mass)` distributions; independent energy-score cross-check. **The load-bearing correctness module.** |
| `test_crps.py` | 8-check correctness gate for CRPS (runs first; aborts the PoC on failure). |
| `data.py` | Regime-switching AR(1) **integer** panel + timestamped text corpus carrying genuine advance signal (lead-`k` regime-switch tokens, imperfect recall + spurious noise). |
| `forecasters.py` | `SeldonConfidenceForecaster` (reachable set via convolved one-step kernel + stepped confidence + optional text overlay) and two text-blind baselines (climatology, Gaussian-AR(1)). |
| `calibration.py` | Randomised-PIT calibration for discrete predictive CDFs. |
| `run_poc.py` | End-to-end runner: gate → panel → rolling-origin CRPS → calibration → text-uplift ablation → per-horizon breakdown. |
| `multiseed.py` | 10-seed robustness sweep. |

### How the forecaster maps to the theory

- **Codebook / quantisation**: one-step integer innovation kernel learned by
  pooling `Δ = x_{t+1} − x_t` over history up to the cutoff (the manifold's
  propagation operator).
- **Reachable set (manifold support at horizon h)**: convolve that kernel `h`
  times from the current integer cell → the set of reachable cells.
- **Confidence dimension**: the stepped mass produced by that convolution
  (empirical, *not* a Gaussian assumption).
- **Foveation / adaptive resolution**: negligible tail cells are dropped so the
  support concentrates where credence lives (theory §on adaptive resolution).
- **Text overlay**: an as-of token announcing an incoming regime shifts and
  sharpens the mass toward that regime's cell-band. **Strict as-of masking:**
  only tokens with `timestamp ≤ cutoff` (and recent enough to be pending) are
  used.

## Correctness gate (run first, every time)

```
[PASS] point mass at m vs y: CRPS == |m − y|         (all cases)
[PASS] stepped == energy-score identity               max abs diff 1.07e-14
[PASS] two-point {0,1}@0.5 vs y=0: CRPS == 0.25
[PASS] symmetry CRPS(+d) == CRPS(−d)
[PASS] concentrating mass at truth reduces CRPS
[PASS] stepped == brute-force numerical integral       max abs diff 5.14e-05
[PASS] uniform{−1,0,1} vs y=0: CRPS == 2/9
[PASS] empirical N(0,1) sample vs y=0 ≈ 0.2337
```

CRPS is verified before any comparison number is trusted. The point-mass case
confirms CRPS reduces to absolute error (MAE); the energy-score identity and the
brute-force integral are two independent implementations agreeing with the
closed form.

## Results (seed 0: 60 entities, T=320, H=5, 6 rolling cutoffs → 1800 forecasts/method)

### Mean CRPS by method (lower is better)

| method | mean CRPS | vs climatology |
|---|---|---|
| climatology (text-blind baseline A) | 2.2034 | 0.0% |
| Gaussian-AR(1) (text-blind baseline B) | 1.1052 | −49.8% |
| **Seldon, text-blind** | 1.1257 | −48.9% |
| **Seldon, text-informed** | **1.0492** | **−52.4%** |

### Calibration (randomised PIT, KS deviation from uniform; lower = better)

- **Seldon text-blind: KS = 0.0357** — histogram is visibly flat. **Calibrated
  out of the box.**
- Seldon text-informed: KS = 0.0579 — slightly *worse*; the crude blend
  over-sharpens toward the announced band. See gaps.

### Text-uplift ablation (paired, same forecaster, text on vs off)

- text-blind CRPS: 1.1257
- text-informed CRPS: 1.0492
- **mean reduction: 0.0764 = 6.8% of text-blind CRPS**
- **95% paired bootstrap CI: [0.0409, 0.1138] = [3.6%, 10.1%]** — excludes 0.
- **Verdict: UPLIFT.**

### Where the uplift lives (by horizon)

| horizon | blind | text | reduction |
|---|---|---|---|
| h=1 | 0.7449 | 0.8148 | **−0.0699 (text HURTS)** |
| h=2 | 1.0073 | 0.9971 | +0.0102 |
| h=3 | 1.1747 | 1.0671 | +0.1077 |
| h=4 | 1.2718 | 1.1135 | +0.1583 |
| h=5 | 1.4297 | 1.2538 | +0.1759 |

This pattern is a *feature, not noise*: tokens are emitted `lead = 3` steps
before a switch, so they carry the most information about slices 3–5 ahead and
essentially none about the very next step (where the switch has not happened
yet). At h=1 the text overlay slightly over-anticipates and hurts. An honest
mechanism should behave exactly like this, and it does.

### Robustness across 10 seeds

- **Text uplift: mean 5.71%, sd 2.04%, range 2.8%–9.0%, positive in 10/10 seeds.**
- **Seldon-text-blind vs Gaussian-AR: mean −0.40%, sd 2.56%** — straddles zero.

## What worked

1. **(a) Valid forecast object — YES.** The manifold-with-confidence emits a
   well-formed stepped predictive distribution per (entity, horizon) with
   integer support and normalised mass. No special-casing needed.
2. **(b) CRPS-scorable — YES, cleanly.** The stepped/integer form is the *exact*
   domain of closed-form CRPS. This is the strongest part of the framing: the
   frame/continuum invariant and CRPS fit together with no impedance mismatch.
3. **(c) Calibratable — YES, and calibrated out of the box (text-blind).** The
   empirical convolution kernel produces honest confidence bands (KS 0.036)
   without any post-hoc recalibration.
4. **(d) Text uplift — YES on this controlled setup.** Conditioning the
   confidence dimension on strictly as-of-masked text reduced CRPS by ~6% (95%
   CI [3.6%, 10.1%]), robust across seeds, with a horizon profile that matches
   the known information structure of the text.

## What did NOT work / honest nulls

1. **The reachable-set framing itself buys ~nothing over a plain AR baseline
   (text-blind).** Seldon-text-blind vs Gaussian-AR(1): mean −0.40% across
   seeds, indistinguishable from zero. On a genuinely AR(1) process this is
   *expected* — the correctly-specified Gaussian AR(1) is near-optimal, so the
   empirical-convolution manifold can only match it. **The value in this PoC
   comes from the text conditioning, not from the reachable-set representation
   per se.** State that plainly.
2. **The text overlay mildly degrades calibration** (KS 0.036 → 0.058). The
   fixed-weight Gaussian blend toward the announced band over-sharpens. A real
   implementation would need to learn the overlay strength (and would face T2's
   calibration gate on exactly this).
3. **h=1 text uplift is negative.** Correct given `lead=3`, but a reminder that
   naive text conditioning can hurt short horizons.

## Honest verdict on viability

- **Does the framing produce a valid, CRPS-scorable, calibratable probabilistic
  forecast?** **Yes, on all three counts, and the CRPS/integer-frame fit is the
  cleanest structural result here.** This raises confidence that the *object* is
  sound.
- **Does the text-uplift mechanism demonstrably reduce CRPS where text truly
  carries signal?** **Yes — mechanism demonstrated on synthetic data**: ~6% CRPS
  reduction, CI excludes zero, 10/10 seeds, physically-sensible horizon profile
  and strict as-of masking. **This is a synthetic-proven mechanism, which is
  explicitly not benchmark value.**

### Residual risks / what the PoC did NOT prove

1. **Synthetic ≠ real.** Text signal here is clean, correctly timed, and
   entity-linked by construction. Real T2 text is noisy, must be *extracted*
   (NER/event detection), and its lead time is unknown. The uplift number does
   **not** transfer.
2. **The reachable-set representation earned no independent uplift.** On
   non-AR / regime-heavy / heavy-tailed real series it *might* beat a Gaussian
   AR — but this PoC gives no evidence for that, and on the AR process it
   matched, not beat.
3. **Text overlay calibration is unsolved.** The mechanism sharpens correctly on
   average but degrades PIT calibration; passing T2's calibration gate with text
   on will require a learned, calibrated overlay — untested here.
4. **No substrate_rs.** This is pure Python. The OCELOT substrate would
   contribute the codebook/dynamic-quantisation machinery and the run_rules
   fixpoint; nothing here demonstrates that the substrate *route* adds value
   over the direct numeric implementation. Honest note: for the numeric core
   (kernel convolution + CRPS) the substrate would **not** help; where it could
   help is the *text→graph→confidence* pathway (event extraction as graph
   mutations feeding the overlay), which this PoC stubbed out entirely.

### Updated viability judgment and CI on expected improvement

- **Object viability (a,b,c): raised to high confidence.** The stepped-CDF /
  CRPS / integer-frame alignment is real and needs no tricks.
- **Text-uplift *mechanism* viability (d): raised to moderate-high confidence**
  that the mechanism *functions*; **unchanged/low confidence** that it yields
  benchmark uplift on real T2 data.
- **Tightened CI on expected CRPS improvement over text-blind baselines:** on a
  controlled setup where text carries real, correctly-timed signal, **~3.6%–10%
  (95% CI, this synthetic setup)**. **For real T2** I would not carry this
  interval forward; the realistic expectation is a **substantial discount** —
  plausibly **0%–5%** with a real, non-trivial probability the effect is
  statistically null after honest text extraction and the calibration gate.
  Reasoning: the synthetic result isolates the *mechanism* under ideal signal;
  every real-world degradation (extraction error, timing uncertainty,
  attribution noise, calibration penalty) moves the number toward zero, and none
  moves it up.

**One-line prereg-style summary:** *The Seldon-manifold-with-confidence object is
a valid, CRPS-scorable, out-of-the-box-calibrated probabilistic forecast, and its
text-conditioning mechanism produces a real, robust CRPS reduction on synthetic
data where text carries signal — but the reachable-set framing earned no uplift
over a plain AR baseline text-blind, and none of this is evidence of benchmark
value on real T2.*

## Reproduce

```bash
# from repo root; requires only python3 + numpy (no scipy, no substrate_rs)
cd drafts/seldon_t2_poc

# 1. CRPS correctness gate (must pass before trusting anything)
python3 test_crps.py

# 2. full end-to-end PoC (prints the results table above)
python3 run_poc.py

# 3. 10-seed robustness sweep
python3 multiseed.py

# (optional) inspect the synthetic panel
python3 data.py
```

All runs are seeded and deterministic. Numbers in this report were produced by
the commands above on python 3.13 / numpy 2.5.2 (also confirmed reproducing
identically on the recorded run).
