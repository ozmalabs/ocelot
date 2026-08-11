# MARSHMALLOW DISSOLUTION — results (block 240000)

Pre-registration: `MARSHMALLOW_DELAY_PREREG.md`, committed BEFORE any measurement
(commit 7fd9694e). Base sha **ecdcd8dbad**. Confirmatory measure:
`scripts/marshmallow_delay_measure.py` → `results/marshmallow_delay/results.json`
(RNG seeded once at 240000, N=60 agents/cohort, bootstrap 95% CI, 2000 reps).

**Headline: the substrate SEPARATES temperament from the reliability-prior — the
causally-clean dissolution the confounded human marshmallow test cannot run. Both
main effects on wait-time are present and CI-separated, and the confound is
exhibited in both directions. Every measured number matches the pre-registered
analytic grid exactly.**

This is a CAPABILITY demonstration (the substrate CAN dissolve the entangled
causes over one value economy), NOT an empirical claim about real children.

## The mechanism (named)

The wait/take choice is the graph rule **`mm_choose`** — an `Argmax` over two
candidate `Appraisal`s (wait, take) by `total_value` — decided entirely over the
**204000 `core_emotions` value economy** (`em_happiness = benefit − cost + mood`,
`em_total_value = happiness + fulfilment`). The wait candidate's valuation
(`mm_appraise_wait`) rides the **207000 time-cost `Drive`**: it reads
`Drive.weight` (= TEMPERAMENT) to scale the accrued per-tick time-cost
(`individual_cost = cost_per_tick · weight · elapsed`) and reads
`DelayDecision.reliability_prior` (the belief) to scale the expected delayed
reward (`individual_benefit = prior · delayed / scale`). The adapter only sets
those two node attrs (data) and sweeps `elapsed`, reading `chosen_action` off the
graph. **No Python decision; no Rust; no reward/punishment shaping.**
`total_value(wait) = 2P − 2·weight·t` (even), `total_value(take) = 101` (odd) ⇒
the Argmax is tie-free at every tick.

## Factorial grid (deterministic single agent) — MATCHES PREREG EXACTLY

`wait_time` (ticks held out before the graph's Argmax flips to take):

| reliability-prior P | temperament w=2 | w=4 | w=8 |
|---|---|---|---|
| 60  | 5  | 3  | 2 |
| 80  | 15 | 8  | 4 |
| 100 | 25 | 13 | 7 |

`matches_prereg = True`. Both main effects monotone: across a row (prior fixed)
rising temperament shortens wait; down a column (temperament fixed) rising prior
lengthens wait.

## G-dissolution (HEADLINE) — PASS

N=60 agents/cohort, bootstrap 95% CI.

- **Pure temperament effect** (reliability-prior distribution held FIXED):
  patient cohort (`w∈{2,3}`) mean wait **12.05 [10.40, 13.67]** vs impatient
  cohort (`w∈{7,8}`) **4.13 [3.68, 4.58]** — **CI-separated**. (Predicted ≈11.8
  vs ≈4.0.)
  - Null control (temperament held CONSTANT): CIs **overlap** [10.15,13.15] vs
    [10.73,13.83] — the effect comes from the factor, not the machinery. ✓
- **Pure prior effect** (temperament distribution held FIXED): low-prior cohort
  (`P∈{58,60,62}`) mean wait **2.92 [2.60, 3.27]** vs high-prior
  (`P∈{96,98,100}`) **13.23 [11.63, 14.97]** — **CI-separated**. (Predicted ≈3.0
  vs ≈13.5.)
  - Null control (prior held CONSTANT): CIs **overlap** [2.60,3.10] vs
    [2.73,3.40]. ✓

Both effects present and separable → **the two entangled causes are individually
identified**, which the human test (temperament and prior confounded) cannot do.

## G-rational-impatience (reproduces Kidd 2013) — PASS

Same PATIENT temperament (`w=2`) in both arms; only the reliability-prior differs.
Unreliable-environment prior (`P∈{58,60,62}`) mean wait **5.12 [4.90, 5.32]** vs
reliable prior (`P∈{96,98,100}`) **23.82 [23.60, 24.03]** — CI-separated;
deterministic anchor 5 (P=60) vs 25 (P=100). A patient agent waits SHORT under a
low prior: **impatience as the RATIONAL output of a correct belief, cleanly
attributed to the PRIOR, not a temperament deficit.** Failable control (high prior
same temperament waits long) holds.

## G-confound-exhibited (the dissolution's teeth) — PASS

- **Same temperament, different prior → DIFFERENT wait-time**: `w=4`,
  `P∈{60,80,100}` → wait **[3, 8, 13]** (strictly increasing). A naive marshmallow
  score reads these as three different "self-control" levels though patience is
  IDENTICAL — wait-time is **not identifiable** for temperament.
- **Different temperament, compensating prior → SAME wait-time**: `(w=2,P=60)`,
  `(w=4,P=68)`, `(w=8,P=85)` → wait **[5, 5, 5]** though temperament differs 4×. A
  naive marshmallow score reads them as IDENTICAL "self-control".

## G-glass-box — PASS

`temperament` (Drive.weight), `reliability_prior`, `elapsed`, `chosen_action`, and
both candidate `total_value`s are read straight from the graph (e.g. agent (w=2,
P=60) at elapsed 3: wait_total_value=108, take_total_value=101, chosen_action=1 =
wait). Every decision is a named rule (`mm_appraise_wait`, `mm_appraise_take`,
`mm_choose`, core_emotions `em_*`). Adapter source-audit clean: zero
`graph_rewrite.run`/`gr.run`/`_match`/`_apply`/`make_rule`; zero shaping tokens
(`reward_signal`/`punish`/`reinforce`/`backprop`/`gradient`).

## G-discipline — PASS

Canonical `_native.abi3.so` md5 **e75bc65021b6be0740abeee63662e21b** — UNCHANGED
(the current base's canonical; NO Rust, `runners/dsl` diff empty). Seed
integer-native (no non-integer `Lit`s), `self_load_only:true`, `depends_on:[]`,
and ABSENT from `load_all_seeds` (existing tree byte-identical with it absent).
Own engine `own`; `source_match=own`.

**Oracle (BEFORE == AFTER, `data/` symlinked):**
- `per_area_settlement_regression.sh`: **306 passed / 0 failed** before and after —
  fail-set identical (empty); ZERO new reds.
- `rung7_vision_bench.sh`: (recorded in the return report) before == after.

## Honest residuals & claim separation

- **Capability vs empirical.** This is a synthetic MECHANISM demonstration: the
  substrate CAN hold temperament fixed and sweep the prior (and vice versa),
  identifying each cause. It is NOT a developmental-psychology validation and says
  nothing about real children's wait-times.
- **Prior-art posture is LOW-CONFIDENCE.** Per `PRIOR_ART_SOCIAL_EXPERIMENTS.md`
  Rung 4, the temperament-vs-reliability SEPARATION is a targeted NONE-FOUND
  absence (thin area, targeted searches). We do NOT claim "nobody has done this."
  The discounting behaviour (RL) and the reliability insight (Kidd 2013) are prior
  art; the contribution is the glass-box separation on this substrate.
- **The model is deterministic** (integer arithmetic, zero mechanism noise). The
  reported CIs come from JITTERED cohorts (a temperament/prior "family" per
  level), not from mechanism stochasticity — the CI-separation reflects that the
  effect sizes dominate the cohort spread, exactly as an identification claim
  should. Individual-agent wait-times are exact and reproduce the analytic grid.
- **Linear time-cost, not the MicroPsi decay channel.** Temperament is the
  `Drive.weight` on the 207000 time-cost Drive node, and the per-tick cost is a
  linear accrual (`cost_per_tick · weight · elapsed`), computed by the marshmallow
  rule. We do NOT load the full `drives.json` decay machinery (Ashr half-life);
  the reuse is of the Drive node + weight semantics + the core_emotions value
  economy, which is what the value formula requires.
