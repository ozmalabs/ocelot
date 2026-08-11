# MOOD AS MOMENTUM — R1c: the DECISIVE, POWERED confirmation of R1b's near-miss (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`9c5172d697`**
(`9c5172d697d031ac613a36e5bc98b7edfb373723` — carries mood_r1 + mood_r1b).
Design spec: `MOOD_MOMENTUM_SCOPING.md` (Part C, R1) + `MOOD_R1B_RESULTS.md`
(the near-miss null this rung powers). This rung adds **NO Rust** —
`runners/dsl/src` diff EMPTY. It adds **NO new seed and NO new mood mechanism**:
it REUSES `domains/mood_r1b_world.py`, `domains/mood_r1_world.py`,
`seeds/mood_r1.json` (the `Mood` node + `mood_momentum`/`mood_bias` rules) and
`seeds/mood_r1_task.json` (the fast delta-rule appraisal + accept/decline
choice) VERBATIM. **The ONLY change from R1b is the SAMPLE SIZE.** Engine: this
worktree builds its OWN engine from committed source (`scripts/engine_build.sh`);
`provenance_stamp` verdict **`own`** (`_native.abi3.so` md5
**`10f65be659e0d9a9290aff39f7f5b92a`**, a real tree-build file, not a symlink).
The CANONICAL shared-tree engine md5 **`e75bc65021b6be0740abeee63662e21b`** is
recorded here and must be UNCHANGED at end — this rung never writes through to
it. Seed block **238000–238999**.*

Seed-claim check (verbatim, run before any number):

```
SEED CLAIM 238000-238999: CLEAN -- no collision DETECTED.
  Scope: 959 files with seed sinks; 667 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 0. What this is — POWER, NOT TUNING

R1b (block 237000, `MOOD_R1B_RESULTS.md`) got a **near-miss null** on the strict
absolute-net-benefit bar: on the fair persistent-regime world the WITH−WITHOUT
cumulative-reward gap was **+0.622, boot95 [−0.050, +1.277]** — POSITIVE and
adaptive in direction, but the lower CI bound sat a WHISKER (0.05) below 0, so
`regime_ci_above_0 = False`. The matched-marginal i.i.d. control was clearly
**−1.903 [−2.661, −1.142]** (mood HURTS where returns carry no persistence — a
valid failable control), and the two worlds were CI-separated FROM EACH OTHER.
The fair design flipped the SIGN of the effect exactly as mood-as-momentum
predicts; it only missed CI-separation FROM ZERO, by a whisker.

R1b's own residual (measured, not speculated) named WHY it fell short: the
per-episode gap has high variance because the benefit is concentrated in the ~10
short post-switch transients per 200-trial episode, while the ~90%
within-regime steady state contributes near-zero signed momentum but non-zero
choice noise. **That is an under-powered bar, not a moved effect.** The fix is
therefore NOT to change the world, the learning rates, the gain, or the metric —
it is to shrink the standard error of the mean gap by **increasing the sample
size**. That is what R1c does, and the ONLY thing it does.

**FRAMING (standing project rule):** the FUNCTIONAL momentum estimator (a leaky
integral of signed surprise that biases learning), NOT a claim to felt mood.

## 1. THE ONE CHANGE — sample size K, 200 → 750 (variance reduction, nothing else)

| parameter | R1b value | R1c value | changed? |
|---|---|---|---|
| regime `μ` (levels ±μ) | 1.0 | 1.0 | **no** |
| regime `σ` (within-regime noise) | 0.5 | 0.5 | **no** |
| `p_switch` (per-step switch prob; dwell ~20) | 0.05 | 0.05 | **no** |
| fast value `lr` (the lagging condition) | 0.1 | 0.1 | **no** |
| `momentum_lr` (η′, EMA rate) | 0.3 | 0.3 | **no** |
| `gain` (f_t) | 1.0 | 1.0 | **no** |
| `accept_thresh` | 0.0 | 0.0 | **no** |
| RPE | raw (r−v) | raw (r−v) | **no** |
| `N` (trials/episode) | 200 | **200** | **no** |
| `B` (bootstrap resamples) | 10000 | 10000 | **no** |
| **`K` (episodes)** | **200** | **750** | **YES — the only change** |

**Why K = 750 and not more.** The variance-reduction lever is more independent
episodes: the standard error of the mean per-episode gap falls as `1/√K`. K =
750 is **3.75×** R1b's 200, so the SE shrinks by **√3.75 = 1.936×**. K is capped
here by the SEED BUDGET, not by choice: every RNG seed must stay inside the
claimed block **238000–238999** (1000 integers), and R1c keeps the per-episode
`episode(seed)` construction from R1b VERBATIM (one independent
`default_rng(seed)` per episode — NOT re-pooled into one master stream), so K is
bounded by the in-block integers left after the unchanged sanity bands. The
layout (all seeds strictly inside 238000–238999, none touching the sibling's
239000 block):

| band | seed integers | count | purpose |
|---|---|---|---|
| G-adaptive episodes | 238000 … 238749 | **750** | the headline (`episode(238000+i)`, i=0…749) |
| G-momentum streams | 238750 … 238849 | 100 | mechanism sanity (k2=100, unchanged) |
| diagnostic MSE | 238850 … 238949 | 100 | LABELED NON-GATE (k=100, unchanged) |
| bootstrap resamples | 238950 … 238955 | 6 | percentile bootstrap seeds |

The relocation of the sanity/bootstrap seed bands (vs R1b's 237000-relative
offsets) is FORCED by keeping all seeds in-block at the larger K; it does NOT
change any estimator — `episode()`, `run_arm()`, `boot_ci()`, `t_ci()`, and the
seeds are reused verbatim. **No world parameter, no learning rate, no gain, no
metric, and N are touched.**

## 2. THE PRE-COMMIT TO STOP (decisive/final)

This is the FINAL test of the absolute net-benefit bar. **Run ONCE at K = 750.**
Whatever comes out is reported and the arc STOPS — no sweep, no re-tune, no R1d,
no second K. The two exhaustive outcomes:

- **(a) powered regime gap CI clears 0** (boot95 lower bound > 0) AND i.i.d. NOT
  CI-above-0 → the adaptive net-benefit gate is **CONFIRMED**. Banked.
- **(b) still misses** (regime lower bound ≤ 0) → mood-momentum is directionally
  real but **NOT net-beneficial** at this config → that is the FINAL honest
  verdict. Banked.

Both are complete results. There is no third move.

## 3. PREDICTION (committed before any number)

If R1b's point estimate reflects a TRUE positive effect of ≈ **+0.62** reward
units, then at K = 750 the SE falls to ≈ 0.18 (R1b's per-episode gap SD ≈ 4.84,
from its t-CI half-width 0.6705 = 1.96·SE·, SE₂₀₀ = 0.342 ⇒ SD = 0.342·√200 =
4.84; SE₇₅₀ = 4.84/√750 = 0.177), giving a projected 95% CI of roughly
**[+0.28, +0.97]** — lower bound **clearing 0 with ~+0.28 of margin** ⇒ headline
PASS. The i.i.d. control (R1b −1.90) is projected to stay clearly CI-below-0.

**The genuine risk that keeps this a real test:** the +0.62 point estimate is
itself a 200-episode sample statistic. If the TRUE effect is smaller than ≈
+0.35, the powered lower bound may still touch or cross 0 and the headline is a
FINAL null (outcome b). K = 750 does not manufacture a pass; it only removes the
under-power excuse either way. **This prediction is the gate's direction, not a
guarantee.**

## 4. WHAT WILL BE BUILT (all-new, additive, default-OFF, NO Rust, NO new Term, NO new seed)

The agent side and the world are UNCHANGED — the SAME two seeds and the SAME two
world adapters R1/R1b built and gated are reused verbatim. R1c adds ONLY:

1. **`scripts/mood_r1c_measure.py`** — the powered runner. It imports the R1b
   world adapter (`domains/mood_r1b_world.py`: `regime_stream`, `iid_permute`,
   `run_arm`, `run_arm_trace`, `lag1_autocorr`) and the R1b measurement helpers
   (`episode`, `boot_ci`, `t_ci`, `g_glass_box`, `g_discipline` from
   `scripts/mood_r1b_measure.py`) VERBATIM, and re-runs the SAME estimator at
   **K = 750** with the in-block seed layout of §1. No agent decision, no Rust,
   no Term, no new seed.
2. **`tests/test_mood_r1c_migrated.py`** — PINS the R1c result (whatever it is)
   so it cannot silently flip later, exactly as R1/R1b's tests pinned theirs.

## 5. THE GATES

**G-adaptive-regime-powered (HEADLINE, falsifiable).** Same strict bar as R1b,
now at the powered N: over K = 750 paired episodes the regime gap
`Δ_regime = cum_reward(WITH) − cum_reward(WITHOUT)` has its 95% bootstrap CI
**entirely above 0** (`regime_ci_above_0 = True`) AND the matched-marginal
i.i.d. gap is **NOT CI-above-0** (`iid_ci_above_0 = False`). `headline_pass =
(regime_ci_above_0 and not iid_ci_above_0)`. Reported with both bootstrap and
normal-approx t-CIs, plus the exact marginal-match (max per-episode mean/var
diff < 1e-9) and the regime/i.i.d. lag-1 autocorrelations.

**G-momentum (mechanism sanity, falsifiable).** Unchanged from R1b at lr=0.1:
`Mood.momentum` rises on a sustained GOOD run and falls on a sustained BAD run
(good−bad separation CI-above-0), and the **shuffled-stream control kills it**
(separation CI contains 0).

**G-glass-box.** `Mood` is a readable node (`momentum`, `gain`, `enabled`);
`bias` is a readable `MoodTask` attr; every update is a named rule
(`mood_momentum`, `mood_bias`, `mt_decide`, `mt_accrue`, `mt_rpe`, `mt_learn`);
source audit clean — the reused adapters run NO Python rule engine (no `gr.run`
/ `graph_rewrite` / `make_rule` / `gr._match` / `gr._apply`) and take no
`if`/`else` over a mood value.

**G-discipline.**
  - default-OFF byte-identity: with no `MoodTask`/`Mood` node created, loading
    the two reused seeds is byte-identical to not loading them.
  - both reused seeds are `self_load_only`; R1c adds NO new seed.
  - **NO Rust:** `runners/dsl/src` diff EMPTY; no new Term.
  - engine provenance `own` (md5 `10f65be659e0d9a9290aff39f7f5b92a`); canonical
    shared engine md5 `e75bc65021b6be0740abeee63662e21b` UNCHANGED at end.
  - `source_match = own`.
  - `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (count).
  - `bash scripts/per_area_settlement_regression.sh`: the SET of failing node
    ids BEFORE == AFTER (never a count). ZERO new reds from R1c's additive files.

**BEFORE bench baselines (environment only, recorded at prereg time, NOT an
experimental result).** This is a **data-less worktree** — `data/` is not
symlinked, so the oracles read fewer than a data-symlinked tree; the discipline
is BEFORE == AFTER in THIS environment.
  - `rung7_vision_bench.sh` BEFORE = **214 passed, 10 skipped** (data-less; 214
    without `data/`, would be 224 with).
  - `per_area_settlement_regression.sh` BEFORE = **23 failed, 278 passed, 5
    skipped** — the pre-existing data-less elaboration / topic-route /
    gap-awareness / cortices-tick / composer_driver-parity reds (the composer
    parity test fails with a data-less `FileNotFoundError`, not a logic
    regression). The exact 23-node-id set is saved to
    `results/mood_r1c_perarea_before.txt` and must be identical AFTER.

## 6. HONEST RISK, named before measurement

- **R1c may STILL be a null (outcome b).** K = 750 shrinks the SE by 1.936×; if
  the true effect is materially below R1b's +0.62 point estimate, the powered
  lower bound can still sit at or below 0. That would be the FINAL verdict:
  mood-momentum is directionally adaptive but not net-beneficial at this config.
  Reported straight, no re-tune.
- **K is seed-budget-capped at 750, not the 8× the scoping mused.** The block is
  1000 integers and the per-episode independent-seed construction is kept
  verbatim, so the maximum in-block K after the unchanged sanity bands is ~790.
  750 is the pinned choice. 3.75× is enough to move R1b's −0.05 lower bound to a
  projected ≈ +0.28 under R1b's point estimate — decisive if the effect is real,
  and honestly still failable if it is not.
- **No parameter was tuned.** The world, the learning rates, the gain, the
  accept threshold, the RPE choice, N, and the metric are all carried from R1b
  UNCHANGED. Only K changed. One config, run once.

## 7. Prior art (situate honestly)

- Eldar, Rutledge, Dolan & Niv 2016, *TICS* 20(1):15–24 — mood as momentum (RPE
  integral + additive perceptual feedback). The backbone. Architecture theirs;
  our contribution is the glass-box, gated, shared-atom, default-OFF
  instantiation and the failable-control measurement on a fair
  persistent-regime world, now powered.

Deterministic given the pinned seeds; no wall-clock claim. Prereg committed ALONE
before any code.
