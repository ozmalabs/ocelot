# MOOD R1c — the DECISIVE, POWERED confirmation of R1b's near-miss — RESULTS (block 238000)

*Measured on the pre-registered design (`MOOD_R1C_PREREG.md`), single pinned
config, ONE run, no post-hoc change to the headline or any parameter. Isolated
worktree off `main` **`9c5172d697`** (`9c5172d697d031ac613a36e5bc98b7edfb373723`).
The ONLY change from R1b is the sample size **K (200 → 750)**; the world
(`domains/mood_r1b_world.py`), the two seeds (`seeds/mood_r1.json` +
`seeds/mood_r1_task.json`), the learning rates, the gain, the accept threshold,
the RPE choice, N=200, and the metric are all reused VERBATIM (the estimator —
`episode`/`boot_ci`/`run_arm` — is imported byte-identically from
`scripts/mood_r1b_measure.py`). Own engine build (`provenance_stamp` = **own**,
`_native.abi3.so` md5 `10f65be659e0d9a9290aff39f7f5b92a`); canonical shared
engine md5 `e75bc65021b6be0740abeee63662e21b` UNCHANGED. NO Rust —
`runners/dsl/src` diff EMPTY. Measured by `scripts/mood_r1c_measure.py`; pinned
by `tests/test_mood_r1c_migrated.py` (12 passed).*

## BOTTOM LINE — the pre-registered headline PASSES. The adaptive net-benefit gate is CONFIRMED.

**At the powered N (K = 750), the persistent-regime WITH−WITHOUT cumulative-reward
gap is +0.564 with 95% bootstrap CI [+0.266, +0.855] — the CI now CLEARS 0. The
matched-marginal i.i.d. control is −2.029 [−2.391, −1.660] (mood HURTS where
returns carry no persistence — NOT CI-above-0). `headline_pass = True`.
Mood-momentum is net-beneficial exactly where environmental returns persist, and
harmful where they don't. R1b's near-miss was under-power, not a moved effect —
powering the bar confirmed it.**

| world (K=750 episodes, N=200 trials, fast lr=0.1) | WITH−WITHOUT cumulative-reward gap | 95% bootstrap CI | t-CI | verdict |
|---|---|---|---|---|
| **persistent regime** (2-state, dwell~20, switch p=0.05; lag-1 autocorr 0.691) | **+0.564** | **[+0.266, +0.855]** | [+0.272, +0.856] | mean POSITIVE; **CI CLEARS 0** → regime_ci_above_0 = **True** |
| **i.i.d.** (same multiset permuted; lag-1 −0.004) | **−2.029** | [−2.391, −1.660] | [−2.392, −1.665] | CI **below 0** — mood HURTS (valid failable control; NOT CI-above-0) |

The two worlds share an EXACTLY matched marginal (max per-episode mean/var diff
`2.2e-16 / 4.4e-16` — a permutation of the same stream), so persistence is the
ONLY difference. Baseline WITHOUT-mood cumulative reward: regime 59.6, i.i.d.
16.0. The regime gap is +0.95% of baseline.

**The prediction held.** The pre-registration committed (before any number): if
R1b's +0.62 point estimate reflects a true effect, at K = 750 the SE falls to
≈ 0.18 and the CI clears 0 with a projected ≈ [+0.28, +0.97]. Measured:
[+0.266, +0.855] — the lower bound moved from R1b's −0.05 to +0.27, a decisive
+0.27 of margin, right where predicted. The point estimate came in at +0.564
(vs R1b's +0.622, well within R1b's own CI), and the 3.75× larger sample (SE
shrink √3.75 = 1.936×) was enough to separate it from 0.

## The full arc, in one line each

- **R1 (236000, AR(1), lr=0.3):** honest null — BOTH worlds negative
  (mood-as-noise). Two confounds diagnosed (fast layer already tracked; AR(1)
  mean-reverts and punishes momentum).
- **R1b (237000, fair regime world, lr=0.1):** near-miss null — regime **+0.622
  [−0.050, +1.277]** (flipped POSITIVE, adaptive in direction), i.i.d. −1.903
  (mood hurts), the two CI-separated from each other, but the regime lower bound
  a whisker below 0 → strict bar missed by 0.05. Diagnosis: under-powered (the
  benefit is concentrated in ~10 short post-switch transients/episode).
- **R1c (238000, SAME config, K 200→750):** **PASS** — regime **+0.564 [+0.266,
  +0.855]**, i.i.d. −2.029 [−2.391, −1.660]. The bar is cleared. Net benefit
  established.

## What ALSO held — the mechanism, the control, and the discipline (all gated green)

**G-momentum — the momentum signal is a correct leaky signed-RPE tracker (at the
pinned lr=0.1).** `Mood.momentum` rises in a good run (+0.496) and falls in a bad
run (−0.995); the trended good−bad separation is +1.491, 95% CI [+1.470, +1.513]
(CI-above-0), and the **shuffled-stream control kills it**: separation +0.032,
95% CI [−0.045, +0.108] (contains 0). The momentum IS the leaky EMA of the signed
RPE `(r − v)` — R1's pinned RPE choice, kept verbatim.

**The i.i.d. control is a VALID failable control.** It behaves as designed: mood
does NOT help where returns carry no persistence — it HURTS (CI entirely below
0). Had it helped in i.i.d. too, the regime effect would be noise/optimism; it
did not. The regime CI [+0.266, +0.855] is CI-separated ABOVE the i.i.d. CI
[−2.391, −1.660].

**G-glass-box.** `Mood` is a readable node (`momentum`, `gain`, `enabled`);
`bias` is a readable `MoodTask` attr; every update is a named rule
(`mood_momentum`, `mood_bias`, `mt_decide`, `mt_accrue`, `mt_rpe`, `mt_learn`);
source audit clean — the reused adapters run no Python rule engine and take no
`if`/`else` over a mood value.

**G-discipline.** NO new Rust Term — the momentum EMA uses only atoms `sd_blend`
already uses (`new_terms = []`); `runners/dsl/src` diff EMPTY; NO new seed (both
seeds reused verbatim). Default-OFF byte-identical (no `MoodTask`/`Mood` node on
the default path; 5-frame photon fingerprint equal with/without the two seeds
loaded). Engine provenance **own** (`source_match = own`).

## LABELED NON-GATE diagnostic (NOT a pre-registered gate) — value-prediction MSE

Reported for interpretation only, never as R1c's result. Does momentum improve
the raw value-prediction MSE (mean `raw_rpe²`)?

| world | MSE improvement (without−with, >0 = mood helps) | 95% boot CI |
|---|---|---|
| regime | **−0.008** | [−0.019, +0.002] |
| i.i.d. | **−0.055** | [−0.059, −0.051] |

Momentum slightly WORSENS the raw prediction MSE (more so in i.i.d.; the regime
CI now touches 0), yet HELPS the cumulative-REWARD choice metric in the regime
world (+0.56, CI-above-0). Same reconciliation as R1b: the accept/decline choice
cares about getting the SIGN of `v` right FASTER at a regime switch, not about
minimising per-trial squared error — momentum accelerates the post-switch
sign-crossing (adaptive where switches persist) at the cost of a little extra
within-regime overshoot (which MSE penalises but the thresholded choice largely
ignores). This is why the pre-registered metric is cumulative reward, not MSE.

## Discipline ledger

- Prereg committed ALONE before any number (`MOOD_R1C_PREREG.md`, commit
  `ab9e61b10d`); seed-claim `238000–238999` CLEAN.
- Own engine built from committed source; provenance **own**
  (`10f65be659e0d9a9290aff39f7f5b92a`). Canonical shared engine
  `e75bc65021b6be0740abeee63662e21b` UNCHANGED end-to-end (never written
  through; `engine_build.sh` uses `cp --remove-destination`).
- `runners/dsl/src` diff EMPTY (no Rust, no Term). NO new seed (R1/R1b seeds
  reused). `new_terms = []`.
- Additive new files only (`mood_r1c_*` / `MOOD_R1C*`); explicit `git add` of
  each path; no existing tracked file touched; never `git add -A`.
- Oracle `scripts/rung7_vision_bench.sh` BEFORE == AFTER = **214 passed, 10
  skipped** (data-less worktree — `data/` not symlinked; would be 224 with).
  `scripts/per_area_settlement_regression.sh` failing node-id SET BEFORE ==
  AFTER (23 pre-existing data-less reds — cortices-tick / composer_driver-parity
  `FileNotFoundError` / gap-awareness / elaboration / topic-route; the exact set
  in `results/mood_r1c_perarea_before.txt`, `diff` empty). ZERO new reds from
  R1c's additive files.
- `tests/test_mood_r1c_migrated.py` 12 passed — it PINS the PASS (regime gap
  CI-above-0, `headline_pass` True) so it can never silently regress to a null
  without a fresh, honest measurement.

## Honest notes

- **The pre-commit to stop was honored.** The powered config (K = 750) was run
  ONCE. No lr/gain/world sweep, no second K, no re-tune. This is the FINAL
  verdict on the absolute-net-benefit bar, and it is a PASS.
- **K = 750, not the 8× the scoping mused.** K is seed-budget-capped: every RNG
  seed stays inside the claimed block 238000–238999 and R1c keeps R1b's
  per-episode independent-seed construction verbatim, so the max in-block K after
  the unchanged sanity bands is ~790. 750 (3.75×) shrank the SE by 1.936× —
  enough to clear the bar with +0.27 of margin. A single, honest, sufficient
  increase; not tuned to win (the direction and size were predicted, and the
  test was genuinely failable if the true effect had been < ~+0.35).
- **What is now established across R1→R1b→R1c:** on a fair persistent-regime
  world with a lagging fast layer, a leaky signed-RPE momentum bias is (a)
  directionally adaptive (helps where returns persist, hurts where they don't —
  CI-separated), and (b) **net-beneficial** on the cumulative-reward choice
  metric (regime CI-above-0 at powered N). The i.i.d. failable control did its
  job at every stage. The effect is small in absolute terms (+0.95% of baseline)
  but real and correctly signed — the paper's mechanism (Eldar/Rutledge/Dolan/Niv
  2016), instantiated glass-box, gated, shared-atom, default-OFF, and now powered.
