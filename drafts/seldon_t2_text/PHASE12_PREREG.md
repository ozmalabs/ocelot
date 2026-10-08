# PHASE 1–2 PRE-REGISTRATION

Written BEFORE any Phase-2 variogram numbers are measured. Records the hypothesis,
the exact metric, the two arms, the realized-outcome construction, and the
decision rule, so the results in `PHASE12_RESULTS.md` are a measurement against a
fixed prediction rather than a post-hoc story.

Built against the contract pinned in `PHASE0_GROUND_TRUTH.md`
(verified-from-code facts trusted; unverified facts treated cautiously).

---

## 0. What Phase 1 already established (gate, not hypothesis)

Phase 1 is a plumbing result, reported not hypothesised: the adapter
(`t2_adapter.py`) puts the PoC Seldon reachable-set + confidence mechanism onto
the REAL output contract and is ADMISSIBLE. Success criterion (pre-set): the
reference scorer (`qfbench2_track_forecasting.scoring score`) and `qfbench2-smoke`
both return `admissible=True` with g0–g3 all `pass` on the exemplar and ≥10
practice units, for the joint engine. This is a pass/fail plumbing gate; the
numbers reported are the gate booleans, not a metric to be optimised.

## 1. The Phase-2 hypothesis (the 30% the PoC fails)

**H-joint.** On multi-asset (F3-shaped, `cell_count ≥ 2` with ≥2 distinct assets)
units, replacing INDEPENDENT per-asset draws with JOINT draws that carry the
estimated cross-asset innovation correlation **reduces the joint variogram term**
of the composite, while leaving the marginal-CRPS and tail terms approximately
unchanged (because the two arms share identical per-asset marginals by
construction).

Directional prediction, fixed now:

- `joint_variogram(joint arm) < joint_variogram(independent arm)` on the F3 set,
  in the mean and on a majority of individual units.
- `|marginal(joint) − marginal(independent)|` and `|tail(joint) − tail(independent)|`
  are small relative to the variogram change (the arms differ only in dependence).
- Consequently the composite (0.5·marg + 0.3·joint + 0.2·tail) is lower for the
  joint arm on the F3 set.

**Null we could observe.** If the panel-estimated correlation is weak/noisy, or
the realized move has little genuine co-movement, the variogram term may not
improve (or the marginal-matching may leak into the other terms). We report
whichever way it comes out.

## 2. The metric — EXACTLY as coded (no reimplementation)

We score with the REAL reference scorer, not a private CRPS. From
`qfbench2_common/scoring/crps.py` (read line-by-line, cited in PHASE0):

- **Joint variogram** (`variogram_score`, p = 0.5, unweighted d×d, d = cells):
  `VS = Σ_{i,j} ( |y_i − y_j|^p − mean_m |x_{m,i} − x_{m,j}|^p )²`.
  Lower is better. This term is **insensitive to marginal bias** and **sensitive
  to mis-specified cross-asset dependence** (the score's own docstring) — so it is
  the right instrument for H-joint.
- **Marginal CRPS** (`crps_marginal`, fair estimator, denom m(m−1)): mean over
  cells of the univariate CRPS. Weight 0.5.
- **Tail** (`tail_penalty`): `Σ_a |coverage_a − a|` over a∈{0.01,0.05,0.95,0.99}
  — PIT COVERAGE error, **not pinball** (PHASE0 §5.4 load-bearing correction).
  Weight 0.2.
- **Composite**: `0.5·marg + 0.3·joint + 0.2·tail`, multi-cell weights unchanged
  (no single-cell reweight because the F3 set is multi-cell). Lower wins.

All numbers are RAW / unranked (local runs are always `RAW_UNRANKABLE`, PHASE0
§5.1) — we can reproduce the raw components + gates, never the normalised
leaderboard number. That is exactly what we report.

## 3. The two arms (identical everything except dependence)

Both arms are produced by the SAME `t2_adapter.py` from the SAME as-of-truncated
panel and the SAME per-asset Seldon reachable-set + confidence stepped
distribution. The ONLY difference:

- **independent** (`IndependentDrawEngine`): each asset sampled independently
  from its own stepped dist — no cross-asset dependence in the draw matrix.
- **joint** (`JointDrawEngine`): per-asset marginals are matched to the SAME
  Seldon stepped-dist mean and std, but each draw index carries a correlated
  Gaussian shock whose correlation R is the empirical correlation of aligned
  one-step panel changes across the target assets. Co-movement preserved; every
  draw index has all target (asset,horizon) cells (also required by g3).

By matching marginals (mean+std) across the two arms, the marginal-CRPS and tail
terms are held approximately fixed, so any composite movement is attributable to
the joint term. This is a deliberate isolation design.

**Fixed seeds:** both arms use `seed=0`, `n_draws=1000` for the measurement runs
(≥500 plan floor; 1000 for tighter variogram estimation on multi-cell units).

## 4. The realized outcome (hand-made; the real one is sealed)

The real realized outcomes are sealed (`reference/realized.parquet` absent →
smoke score = None, PHASE0 §7/§11). For a LOCAL metric we need a realized joint
vector per unit. We construct it BY HAND and describe it fully so the comparison
is not rigged:

**Construction (fixed now, model-independent).** For each F3 unit, the realized
value of asset a at horizon h is:

    y[a,h] = last_obs[a] + beta[a] · (S_h) + idio[a,h]

where
- `last_obs[a]` = the asset's last as-of panel level (public, not sealed),
- `S_h` = a SINGLE common factor shock at horizon h (one scalar per horizon),
  drawn once from N(0, (k·h_scale)²) with a FIXED seed distinct from the model
  seeds — this is the systematic curve/cross move,
- `beta[a]` = a fixed per-asset loading on the common factor (1.0 for the first
  target asset, tapering for longer tenors / other crosses) — encodes that
  assets CO-MOVE, which is the F3 reality the variogram scores,
- `idio[a,h]` = small idiosyncratic noise N(0, (0.15·k·h_scale)²), fixed seed.

This realized process has GENUINE cross-asset co-movement (a dominant common
factor) but is generated by a mechanism that does NOT reuse the model's estimated
covariance R — it uses fixed betas on a common shock. So the joint arm is NOT
handed its own answer; it must have learned a co-movement structure from panel
history that happens to align with how the assets actually move together. If it
has not, the variogram will not improve.

The realized is written as `realized.parquet` with columns EXACTLY
`(asset, horizon, value)` (the scorer's `REALIZED_COLUMNS`, PHASE0 §11) and fed
to the reference scorer via `--realized`.

**Robustness:** we repeat the whole measurement over several common-factor seeds
(the realized-generation seed, NOT the model seed) and report the distribution,
so the result does not hinge on one lucky realized draw.

## 5. Decision rule (pre-set)

H-joint is SUPPORTED iff, aggregated over the F3 multi-asset units and over the
realized seeds:

1. mean `joint_variogram(joint) < mean joint_variogram(independent)`, AND
2. the joint arm has the lower variogram on a MAJORITY of (unit × seed) cells, AND
3. the marginal and tail terms move by less (in mean absolute change) than the
   variogram term does — i.e. the improvement is attributable to dependence.

If (1) holds but (3) fails (marginals drifted), we report the composite honestly
and flag that the isolation was imperfect. If (1) fails, H-joint is NOT supported
and we say so — no re-specification after seeing the numbers.

## 6. What we will NOT claim

- No leaderboard/ranked number (impossible locally — RAW_UNRANKABLE).
- No claim about text uplift (that is Phase 3).
- No claim the hand-made realized reproduces the sealed outcomes; it is a
  transparent instrument for the RELATIVE joint-vs-independent comparison only.
- If realized-based scoring cannot be run for a unit (e.g. transfer unit with an
  absent asset), we score gates only for it and say so.



---

## 7. ADDENDUM (pre-declared before the signed-realized run)

Sequencing note, for honesty: the PRIMARY test in §1–§5 — positive-common-factor
realized, all F3 multi-asset units — has been RUN once (records in
`phase2_vario_records.json`). Before running anything further I am declaring two
secondary analyses and their decision rules here, so they are not post-hoc:

**7a. Asset-class partition (objective, non-outcome split).** Partition the F3
multi-asset units into (i) PURE UST yield-curve units (every target asset is
`UST_*`) and (ii) FX/mixed units, by asset NAME only — a split fixed by the card,
independent of any score. The positive-common-factor realized of §4 assumes
POSITIVE co-movement, which is economically correct for a yield curve (a level
shock moves all tenors the same way) but WRONG for FX crosses that historically
move oppositely (safe-haven vs risk). Pre-declared expectation: H-joint holds
CLEANLY on the curve subset (that is where the realized's premise matches
reality); on the FX/mixed subset the positive realized is misspecified and joint
need not win.

**7b. Signed realized for FX (secondary robustness).** For the FX/mixed subset,
re-run with a realized whose common-factor loadings carry ECONOMIC SIGNS from a
fixed asset-class prior (`_econ_signs`: rates +; safe-haven JPY/CHF/USD −; risk
crosses +) — a prior set from asset class, NOT from the panel-estimated
correlation, so the joint arm is not handed its answer. Pre-declared prediction:
with a realized that co-moves as the assets truly do (signed), the joint arm
recovers an advantage on FX units too (joint variogram lower on a majority of
cells), demonstrating the method captures co-movement of EITHER sign, and that
the FX miss under the positive realized was a realized-misspecification, not a
method failure.

Decision rule for 7a/7b: same three criteria as §5, applied within each subset.
If 7b does NOT recover a joint advantage on FX, I report that the method's FX
co-movement capture is unconfirmed and say so plainly.
