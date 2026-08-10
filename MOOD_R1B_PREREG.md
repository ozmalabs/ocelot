# MOOD AS MOMENTUM — R1b: the AUTOCORRELATION ADAPTIVE GATE, RE-TESTED ON A FAIR (PERSISTENT-REGIME) WORLD (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`e742e94d99`**. Design spec:
`MOOD_MOMENTUM_SCOPING.md` (Part C, R1) + `MOOD_R1_RESULTS.md` (the null this
rung re-tests). This rung adds **NO Rust** — `runners/dsl/src` diff EMPTY. It
adds **NO new seed and NO new mood mechanism**: it REUSES `seeds/mood_r1.json`
(the `Mood` node + `mood_momentum`/`mood_bias` rules) and `seeds/mood_r1_task.json`
(the fast delta-rule appraisal + accept/decline choice) VERBATIM. Only the WORLD
(a persistent-regime reward process, replacing R1's mean-reverting AR(1)) and the
fast-layer learning rate (re-pinned SLOWER, so the fast layer genuinely lags)
differ. Engine: this worktree builds its OWN engine from committed source
(`scripts/engine_build.sh`); `provenance_stamp` verdict **`own`**
(`_native.abi3.so` md5 **`10f65be659e0d9a9290aff39f7f5b92a`**, a real tree-build file, not a symlink).
The CANONICAL shared-tree engine md5 **`e75bc65021b6be0740abeee63662e21b`** is
recorded here and must be UNCHANGED at end — this rung never writes through to
it. Seed block **237000–237999**.*

Seed-claim check (verbatim, run before any number):

```
SEED CLAIM 237000-237999: CLEAN -- no collision DETECTED.
  Scope: 958 files with seed sinks; 664 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 0. What this is — a FRESHLY PRE-REGISTERED CONFIRMATORY re-test

R1 (block 236000, `MOOD_R1_RESULTS.md`) was an **honest null**: at the pinned
config (fast `lr = 0.3`, `gain = 1.0`) mood-momentum did NOT earn reward in the
autocorrelated AR(1) world, and it HURT roughly equally in the i.i.d. control —
the mood-as-noise signature the i.i.d. control was built to detect. R1 DIAGNOSED
two confounds behind that null:

1. **The fast layer already tracked the signal.** At `lr = 0.3` the fast
   delta-rule value estimate already tracked the `φ = 0.9` AR(1) drift well
   enough that the slow momentum layer was redundant and only overshot (R1's
   honest-risk #4, which BIT).
2. **A stationary AR(1) MEAN-REVERTS.** A zero-mean AR(1) is always pulled back
   toward its mean, so momentum-style extrapolation is penalised at EVERY step,
   maximally at reversals. This is not the paper's "natural momentum"; it is a
   world that structurally punishes the mechanism.

R1's POST-HOC exploratory grid (labeled exploratory, NOT a result) suggested the
effect is REAL when the fast layer is slower (`lr = 0.1`, `gain = 1.0`: auto gap
`+1.28 [0.55, 2.00]` CI-above-0, i.i.d. gap `−1.81` CI-below-0). **R1b tests the
hypothesis that peek generated, on a FAIR design, as a proper CONFIRMATORY,
pre-registered rung — with a FRESH world (a persistent regime, not the AR(1) the
peek used) so the peek does not pre-determine the answer.**

**FRAMING (standing project rule):** the FUNCTIONAL momentum estimator (a leaky
integral of signed surprise that biases learning), NOT a claim to felt mood.

## 1. THE TWO PRINCIPLED DESIGN CHANGES (each REQUIRED by the theory, NOT chosen to win)

### Change 1 — a PERSISTENT-REGIME world, not a mean-reverting AR(1)

The paper's adaptive claim is that mood pays off when *recent good outcomes
PREDICT future good outcomes* — genuine environmental momentum. A stationary
AR(1) has positive lag-1 autocorrelation but ALSO mean-reverts, so it punishes
extrapolation. A **regime-switching** process has the persistence WITHOUT the
mean-reversion:

- A hidden regime `s ∈ {GOOD = +μ, BAD = −μ}` that PERSISTS: at each step it
  switches with probability `p_switch` (geometric dwell, mean `1/p_switch`
  steps), else holds.
- Within a regime the reward is stable + noisy: `r_t = s_t·μ + ε_t`,
  `ε_t ~ N(0, σ²)`.

Within a regime the level is STABLE (no pull back to a global mean); a run of
good outcomes genuinely predicts more good outcomes because you are probably
still in the GOOD regime. Momentum extrapolation is correct WITHIN a regime and
wrong only at the (occasional) switch — the exact structure the paper calls
adaptive. This is the FAIR world the R1 residuals named ("a random-walk /
drift-with-momentum return process … may be a fairer world … a named alternative
for R1b").

### Change 2 — a fast layer that genuinely LAGS (`lr = 0.1`)

Mood-as-momentum is ONLY expected to help when the fast layer CANNOT already
capture the correlation (R1 honest-risk #4). At `lr = 0.1` the fast delta-rule's
time constant (~10 trials) is comparable to the regime dwell (~20 trials), so
after a switch `v` lags the new regime level for many trials — a REAL job for
momentum to do (accelerate the catch-up). At `lr = 0.3` (R1's value) `v` would
catch up in ~1–2 trials and momentum would have nothing to add. **Pinning
`lr = 0.1` is not tuning-to-win — it is setting the CONDITION THE HYPOTHESIS IS
ABOUT, pinned before any number with its reason stated. It is the ONLY parameter
changed from R1's config besides the world itself.** (`momentum_lr`, `gain`,
`accept_thresh`, and the RPE choice are all carried over from R1 UNCHANGED — see
§2 — so R1b does not sweep the mood layer.)

## 2. THE PINNED RPE CHOICE — UNCHANGED FROM R1 (do NOT re-pin)

`Mood.momentum` integrates **`rpe_t = (r_t − v_t)`** — the RAW ORDER-0 SIGNED
RESIDUAL, taken BEFORE the value update. This is R1's pinned choice, kept
verbatim (it IS the paper's `(r_t − v^s_t)`; magnitude-preserving; the
substrate's own order-0 residual with a sign). NOT changed for R1b.

## 3. WHAT WILL BE BUILT (all-new, additive, default-OFF, NO Rust, NO new Term, NO new seed)

The agent side is UNCHANGED: the SAME two seeds R1 built and gated are reused
verbatim (`seeds/mood_r1_task.json` + `seeds/mood_r1.json`). Every update is
already a graph RULE over existing Terms; Python is a mechanical world adapter
only. R1b adds ONLY:

1. **`domains/mood_r1b_world.py`** — the mechanical persistent-regime reward
   process + its matched-marginal i.i.d. control, plus a thin runner that drives
   `MoodR1World` (reused from `domains/mood_r1_world.py`) at the pinned
   `lr = 0.1`. NO `if`/`else` over graph state; NO Python rule engine. The
   regime stream and its permutation are pure reward-sequence generation
   (mechanical world I/O); the WITH/WITHOUT arms are the SAME graph differing
   only in `Mood.enabled`.
2. **`scripts/mood_r1b_measure.py`** — generates the reward streams, ticks the
   world adapter, aggregates the gates. No agent decision, no Rust, no Term.
3. **`tests/test_mood_r1b_migrated.py`** — PINS the R1b result (whatever it is)
   so it cannot silently flip later, exactly as R1's test pinned its null.

## 4. THE WORLD (mechanical adapter — `domains/mood_r1b_world.py`)

A one-offer-per-trial accept/decline world (identical protocol to R1). Each trial
the adapter delivers a scalar reward `r_t`, bumps `input_epoch`, calls
`run_rules()`, and reads `decision` / `cum_reward`. Every decision is a rule.

- **Persistent-regime world (the adaptive regime):** the two-state regime process
  of §1 Change 1. Recent outcomes predict future outcomes via persistence,
  WITHOUT mean-reversion.
- **i.i.d. control:** the SAME per-episode regime stream, RANDOMLY PERMUTED. A
  permutation preserves the multiset EXACTLY ⇒ identical marginal mean and
  variance; only the persistence/autocorrelation is destroyed. The cleanest
  possible matched control (R1's exact control design, applied to the regime
  stream) — the two worlds differ in autocorrelation and NOTHING else.

**Pinned parameters (primary configuration, fixed before measurement):**

| parameter | value | why (pinned by principle, NOT to win) |
|---|---|---|
| regime `μ` (levels ±μ) | **1.0** | clean, non-trivial regime separation at `accept_thresh=0` |
| regime `σ` (within-regime noise) | **0.5** | SNR=2: regimes distinguishable but the decision is non-trivial |
| `p_switch` (per-step switch prob) | **0.05** | mean dwell 20 trials — long enough that within-regime is stable AND ~10 switches per 200-trial episode give many transients |
| fast value `lr` | **0.1** | THE LAGGING CONDITION (§1 Change 2): fast layer lags the regime so momentum has a real job. The only change from R1 besides the world |
| `momentum_lr` (η′, EMA rate) | **0.3** | REUSED from R1 unchanged |
| `gain` (f_t) | **1.0** | REUSED from R1 unchanged |
| `accept_thresh` | **0.0** | REUSED from R1 unchanged (accept iff v>0; symmetric ±μ process) |
| RPE | **raw (r−v)** | REUSED from R1 unchanged (§2) |
| `N` (trials/episode) | **200** | REUSED from R1 |
| `K` (episodes) | **200** | REUSED from R1 — POWER THE GATE (standing rule) |
| bootstrap `B` | **10000** | REUSED from R1 |

RNG seeds drawn from block base **237000**: one integer per episode
(`237100 … 237299`, all inside 237000–237999) for G-adaptive; `237300+` for
G-momentum; `237900+` for the bootstraps. WITH and WITHOUT run on the SAME
per-episode stream (paired); the regime and i.i.d. worlds share the same
generated multiset per episode.

## 5. THE GATES (measured by `scripts/mood_r1b_measure.py`; pinned by `tests/test_mood_r1b_migrated.py`)

**G-adaptive-regime (HEADLINE, falsifiable).** Per episode, the paired gap
`Δ = cum_reward(WITH) − cum_reward(WITHOUT)`. Over the `K` episodes:
  - **PERSISTENT-REGIME world:** `mean(Δ_regime) > 0` with its 95% bootstrap CI
    **entirely above 0** (CI-separated from 0). **PREDICTION (committed before any
    number; direction + separation are the gate):** `mean(Δ_regime) > 0`, 95% CI
    lower bound `> 0`; predicted relative gap
    `mean(Δ_regime) / |mean(cum_WITHOUT_regime)|` in a positive band
    **≈ +2% … +40%** (band wide because the reward scale is arbitrary
    pre-measurement; the GATE is lower-CI > 0, NOT hitting the band).
  - **THE CONTROL THAT CAN FAIL — i.i.d. world:** `mean(Δ_iid)` 95% CI
    **CONTAINS 0** (or is negative) — mood must NOT help where returns carry no
    persistence. **PREDICTION:** `|mean(Δ_iid)|` small or negative, CI
    overlapping 0 (or below 0), and NOT CI-above-0.
  - **CI-separation is the result, not above-baseline.** The headline holds iff
    `Δ_regime` is CI-above-0 AND `Δ_iid` is NOT CI-above-0. If BOTH are above 0,
    or `Δ_regime` is null, the headline is FALSE and the straight null is
    reported. **R1b CAN STILL COME OUT NULL — if it does, that is a STRONGER
    negative for mood-as-momentum in this substrate, and it is reported straight
    (§7).**
  - CIs: 95%, from B = 10000-resample bootstrap of the per-episode paired gaps
    (percentile), reported alongside a normal-approx t-CI.

**G-momentum (mechanism sanity, falsifiable).** The readable `Mood.momentum`
value IS the leaky signed-RPE average (unchanged mechanism from R1, re-checked at
`lr = 0.1`):
  - fed a sustained GOOD run (positive `raw_rpe`), `momentum` rises; fed a
    sustained BAD run, it falls — it tracks the SIGN/trend of the injected stream.
  - **failable control — shuffled stream:** the SAME values permuted (no trend)
    drive the good−bad `momentum` separation to ≈ 0 (CI contains 0). If the
    shuffle still "tracks", momentum is not a trend estimator and the claim fails.

**G-glass-box.** `Mood` is a node; `momentum`, `gain`, `enabled` are readable
attrs; `bias` on `MoodTask` is readable; the `mood_momentum` / `mood_bias`
updates are named rules; every reported episode reconstructs from graph data.
Source audit: the R1b adapter runs NO Python rule engine (no `gr.run` /
`graph_rewrite` / `make_rule` / `gr._match` / `gr._apply`); no `if`/`else`
decides a mood value.

**G-discipline.**
  - default-OFF byte-identity: with no `MoodTask`/`Mood` node created, loading the
    two (reused) seeds is byte-identical to not loading them.
  - both reused seeds are `self_load_only: true`; R1b adds NO new seed.
  - **NO Rust:** `runners/dsl/src` diff EMPTY; no new Term; the momentum update
    uses only atoms `sd_blend` already uses.
  - engine provenance `own` (this worktree's build, md5 `10f65be659e0d9a9290aff39f7f5b92a`); canonical
    shared engine md5 `e75bc65021b6be0740abeee63662e21b` UNCHANGED at end.
  - `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (count).
  - `bash scripts/per_area_settlement_regression.sh`: the SET of failing node ids
    BEFORE == AFTER (never a count). On this base (`e742e94d99`) the composer test
    is FIXED, so the per-area bench is expected 306 passed / 0 failed; this rung
    must add ZERO NEW reds.
  - `source_match = own`.

*(BEFORE bench baselines are recorded at prereg time, environment only, not an
experimental result. This is a **data-less worktree** — `data/` is not
symlinked, so rung7 reads fewer than a data-symlinked tree; the discipline is
BEFORE == AFTER in THIS environment. The exact BEFORE counts are recorded in
`MOOD_R1B_RESULTS.md` at measurement time.)*

## 6. HONEST RISK, named before measurement

- **R1b may come out NULL too.** Even with a persistent regime and a lagging
  fast layer, momentum's additive bias may over/under-shoot at switches enough to
  wipe the transient benefit, or the choice metric's noise near switches may
  swamp it. If the regime gap is null, or the i.i.d. control ALSO shows a
  CI-above-0 gain, THAT IS THE RESULT — reported straight, as a STRONGER negative.
- **The peek does not guarantee this.** The peek was on the AR(1) world; R1b's
  regime world is genuinely different (persistence without mean-reversion). A
  positive on AR(1)-lr0.1 does not entail a positive here; that is exactly why
  this is a confirmatory re-test on a fresh design, not a re-run.
- **`lr = 0.1` is a pinned choice with a stated reason, not a swept optimum.** It
  is the lagging condition the hypothesis is about. No other `lr` is measured;
  no `gain`/`momentum_lr` sweep is run. One config, run once.

## 7. Prior art (situate honestly)

- Eldar, Rutledge, Dolan & Niv 2016, *TICS* 20(1):15–24 — mood as momentum (RPE
  integral + additive perceptual feedback). The backbone. Architecture theirs;
  our contribution is the glass-box, gated, shared-atom, default-OFF
  instantiation and the failable-control measurement, now on a fair
  persistent-regime world.

Deterministic given the pinned seeds; no wall-clock claim. Prereg committed ALONE
before any code.
