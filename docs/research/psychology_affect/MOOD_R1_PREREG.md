# MOOD AS MOMENTUM — R1: the AUTOCORRELATION ADAPTIVE GATE (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Isolated worktree off `main` HEAD **`7ee7b7f5e9`**. Design spec:
`MOOD_MOMENTUM_SCOPING.md` (Part C, R1). This rung adds **NO Rust** — `term.rs`
diff EMPTY, whole `runners/dsl/src` diff EMPTY. Engine: this worktree builds its
OWN engine from committed source (`scripts/engine_build.sh`); `provenance_stamp`
verdict **`own`** (`_native.abi3.so` md5 **`10f65be659e0d9a9290aff39f7f5b92a`**,
a real tree-build file, not a symlink). The CANONICAL shared-tree engine md5
**`e75bc65021b6be0740abeee63662e21b`** is recorded here and must be UNCHANGED at
end — this rung never writes through to it. Seed block **236000–236999**.*

Seed-claim check (verbatim, run before any number):

```
SEED CLAIM 236000-236999: CLEAN -- no collision DETECTED.
  Scope: 957 files with seed sinks; 660 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## 0. What this is — the FIRST rung of the mood line

Mood = a slow leaky EMA of the SIGNED reward-prediction-error (the "momentum" of
value; Eldar, Rutledge, Dolan & Niv, *TICS* 2016, PMC4703769). It biases
appraisal of new outcomes. **R1's single falsifiable claim: mood-momentum PAYS
OFF only when environmental returns are AUTOCORRELATED — in an i.i.d. world it
must NOT help.** That, and only that, separates mood-as-momentum from
mood-as-noise. This rung builds the momentum layer + its appraisal feedback,
default-OFF, and measures the adaptive gate behind a control that CAN fail (the
i.i.d. world). The set-point layer, the mood-congruent bias (R2), the disorder
sweep (R3) and the two-layer double-dissociation (R4) are NOT in scope here.

**FRAMING (standing project rule):** the FUNCTIONAL momentum estimator (a leaky
integral of signed surprise that biases learning), NOT a claim to felt mood.

## 1. THE PRE-REGISTERED RPE CHOICE (the scoping doc's §7 explicit requirement)

The scoping doc names three candidates for the RPE the Mood integrates and
requires it be PINNED before R1: `Drive.value_progress` vs a signed
Δ`ModulatorState.valence` vs the raw order-0 residual. **This rung PINS the
RAW ORDER-0 SIGNED RESIDUAL:**

> **`Mood.momentum` integrates `rpe_t = (r_t − v_t)`** — the signed prediction
> error of the value estimate `v_t` against the delivered reward `r_t`, taken
> BEFORE the value update. Magnitude-preserving; sign = the direction of
> surprise.

**Why this one, decided before any number:**

- It IS the paper's `(r_t − v^s_t)` (Box 1 / Box 2) EXACTLY — the quantity whose
  leaky integral the paper's `m_{t+1} = m_t + η'·((r_t − v^s_t) − m_t)`
  accumulates. Faithful by construction.
- It is the substrate's OWN currency: the order-0 residual `sd_residual` already
  computes everywhere (`|caught − held|`), here taken WITH a sign. Mood adds no
  new signal — it is a second, slow reader of the residual the substrate already
  forms.
- It is MAGNITUDE-preserving. A signed Δ`ModulatorState.valence` is a −1/0/+1
  SIGN (see `mod_valence`), so it discards the size of the surprise and cannot be
  a leaky *integral that tracks the size of a trend* — rejected.
- `Drive.value_progress` is a downstream, already-summarised per-drive
  reinforcer that requires the full drive/appraisal stack to be live; using it
  would couple R1's momentum measurement to the entire modulator dynamics and
  confound the clean autocorrelation test — rejected for R1 (it is the natural
  hook when mood is later wired to the full drive core, a named future rung).

## 2. WHAT WILL BE BUILT (all-new, additive, default-OFF, NO Rust, NO new Term)

Every update is a graph RULE over EXISTING Terms
(`Plus / Minus / Times / Div / IfThenElse / Gt / Gte / Lt / And / Eq / Attr`,
all in `term.rs` today). Python is a mechanical world adapter only.

1. **`seeds/mood_r1_task.json`** — the task/appraisal core, loaded for BOTH arms.
   A `MoodTask` node (hung off an `EmotionHub` by `has_mood_task`) carrying the
   fast value estimate and the choice. Rules, one pass per trial (guarded
   `input_epoch > epoch`, closed by setting `epoch = input_epoch` — the same
   once-per-tick idiom `sd_*` uses):
   - `mt_decide` (order 0): `decision = (v > accept_thresh) ? 1 : 0` — accept the
     offer iff the current value estimate predicts positive return.
   - `mt_accrue` (order 1): `reward_got = decision·r`; `cum_reward += reward_got`.
   - `mt_rpe` (order 2): `raw_rpe = r − v` — the pinned signed order-0 residual,
     stored before any update.
   - `mt_learn` (order 4): `v += lr·(raw_rpe + bias)` — the fast delta-rule
     appraisal (a lagging EMA of reward). `bias` is a `MoodTask` attr defaulting
     to **0**; absent the mood layer the update is a plain delta rule.
   - `mt_close` (order 5): `epoch = input_epoch`.

2. **`seeds/mood_r1.json`** — the MOMENTUM LAYER (the mood). A `Mood` node hung
   off the SAME `EmotionHub` by `has_mood`, joined to the `MoodTask` through the
   hub. **A readable node**: `enabled`, `momentum`, `gain`, `momentum_lr`. Rules,
   every one guarded on `Mood.enabled == 1`:
   - `mood_momentum` (order 4): the leaky EMA of the signed RPE —
     `momentum += momentum_lr·(raw_rpe − momentum)` = `(1−momentum_lr)·momentum
     + momentum_lr·raw_rpe`. This is **structurally `sd_blend`** (the Kalman
     held-vs-new blend `held + α·(new − held)`) with the blend coefficient `α =
     momentum_lr`; the `(1−α)` factor IS the leak — the extensional, per-tick
     form of the `staleness_decay` scale2 half-life decay toward zero. Same
     atoms, no new Term. It integrates the RAW `raw_rpe` (an honest trend
     tracker; feeding the self-inflated perceived RPE back into momentum is the
     R3 runaway, deliberately NOT done here).
   - `mood_bias` (order 3): `bias = gain·momentum` — Eldar/Niv's `f_t·m_t`
     feedback, written onto the `MoodTask` so `mt_learn` adds it to the perceived
     RPE before the reinforcer forms. Uses the momentum carried from the previous
     trial (order 3 precedes this trial's `mood_momentum` at order 4), a
     one-step-ahead anticipation.

**Momentum = order-1 "velocity of value" (the reuse NAMED):** the leaky-EMA
update is the extensional per-tick form of the first finite difference of the
value stream — the eye's order-1 motion inference (`TimeInfer` / `diff_pyramid`)
pointed at reward instead of pixels. No new Term; the leaky integrator IS the
order-1 form (scoping §B3).

**Default-OFF discipline.** Every `mood_r1.json` rule guards on
`Mood.enabled`. WITHOUT arm = the SAME graph with `Mood.enabled = 0` (so `bias`
stays 0 and `mt_learn` is a plain delta rule — the otherwise-identical agent).
Separately, with NO `MoodTask`/`Mood` node created, loading the two seeds is
byte-identical to not loading them (the opt-in nodes are created only by the
measure adapter).

## 3. THE WORLD (mechanical adapter — `domains/mood_r1_world.py`)

A one-offer-per-trial accept/decline world. Each trial the adapter delivers a
scalar reward `r_t`, bumps `input_epoch`, calls `run_rules()`, and reads
`decision` / `cum_reward`. NO conditional over graph state; every decision is a
rule.

- **Autocorrelated world:** a zero-mean AR(1) return stream
  `r_t = φ·r_{t−1} + ε_t`, `ε_t ~ N(0, σ_ε²)` with `σ_ε = σ_r·√(1−φ²)` so the
  marginal std is `σ_r`. Returns drift with momentum — the paper's adaptive
  regime.
- **i.i.d. control:** the SAME per-episode stream, RANDOMLY PERMUTED. A
  permutation preserves the multiset exactly ⇒ **identical marginal mean and
  variance**; only the autocorrelation is destroyed. This is the cleanest
  possible matched control — the two worlds differ in autocorrelation and
  NOTHING else.

**Pinned parameters (primary configuration, fixed before measurement):**
`φ = 0.9`, `σ_r = 1.0`, `accept_thresh = 0`, value `lr = 0.3`,
`momentum_lr = 0.3`, `gain = 1.0`, `N = 200` trials/episode, `K = 200`
independent episodes. RNG seeds drawn from block base `236100` (one integer per
episode, `236100 … 236299`, all inside 236000–236999). WITH and WITHOUT run on
the SAME per-episode stream (paired); the auto and iid worlds share the same
generated multiset per episode.

## 4. THE GATES (measured by `scripts/mood_r1_measure.py`; pinned by
`tests/test_mood_r1_migrated.py`)

**G-adaptive (HEADLINE, falsifiable).** Per episode, the paired gap
`Δ = cum_reward(WITH) − cum_reward(WITHOUT)`. Over the `K` episodes:
  - **AUTOCORRELATED world:** `mean(Δ_auto) > 0` with its 95% CI **entirely above
    0** (CI-separated from 0). Prediction (direction + separation are the gate):
    `mean(Δ_auto) > 0`, 95% CI lower bound `> 0`; predicted relative gap
    `mean(Δ_auto) / mean(cum_WITHOUT_auto)` in a positive band **≈ +5% … +40%**
    (band wide because the reward scale is arbitrary pre-measurement; the GATE is
    lower-CI > 0, NOT hitting the band).
  - **THE CONTROL THAT CAN FAIL — i.i.d. world:** `mean(Δ_iid)` 95% CI
    **CONTAINS 0** (or is negative) — mood must NOT help where returns carry no
    momentum. Predicted: `|mean(Δ_iid)|` small, CI overlapping 0, and NOT
    CI-above-0.
  - **CI-separation is the result, not above-baseline.** The headline holds iff
    `Δ_auto` is CI-above-0 AND `Δ_iid` is NOT CI-above-0. If BOTH are above 0, or
    `Δ_auto` is null, the headline is FALSE and the straight null is reported
    (the honest risk in §7 is named up front).
  - CIs: 95%, from B = 10000-resample bootstrap of the per-episode paired gaps
    (percentile), reported alongside a normal-approx t-CI.

**G-momentum-is-signed-RPE-EMA (falsifiable).** The readable `Mood.momentum`
value IS the leaky signed-RPE average:
  - fed a sustained GOOD run (a stream of positive `raw_rpe`), `momentum` rises
    monotonically toward the input level; fed a sustained BAD run (negative),
    it falls — it tracks the SIGN/trend of the injected stream.
  - **failable control — shuffled stream:** the SAME values permuted (no trend,
    mean ≈ 0) drive `momentum` to stay near 0; the correlation between the
    momentum trajectory and the running reward trend is HIGH on the trended
    stream and is KILLED (≈ 0 / CI-overlapping) on the shuffle. If the shuffle
    still "tracks", momentum is not a trend estimator and the claim fails.

**G-glass-box.** `Mood` is a node; `momentum`, `gain`, `enabled` are readable
attrs; `bias` on `MoodTask` is readable; the `mood_momentum` / `mood_bias`
updates are named rules; every reported episode reconstructs from graph data.
Source audit: the adapter runs NO Python rule engine (no `gr.run` /
`graph_rewrite` / `make_rule` / `gr._match` / `gr._apply`); no `if`/`else`
decides a mood value.

**G-discipline.**
  - default-OFF byte-identity: with no `MoodTask`/`Mood` node created, loading the
    two seeds is byte-identical to not loading them (fingerprint equal; no mood
    nodes created on the default path).
  - `self_load_only: true` on both new seeds; both are all-new files.
  - **NO Rust:** `runners/dsl/src` diff EMPTY; no new Term; the momentum update
    uses only atoms `sd_blend` already uses.
  - engine provenance `own` (this worktree's build,
    md5 `10f65be659e0d9a9290aff39f7f5b92a`); canonical shared engine md5
    `e75bc65021b6be0740abeee63662e21b` UNCHANGED at end (§10).
  - `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (count).
  - `bash scripts/per_area_settlement_regression.sh`: the SET of failing node ids
    BEFORE == AFTER (never a count). KNOWN possible pre-existing red:
    `test_composer_driver_migrated::test_ground_concern_dispatch_parity` (a
    brittle test being fixed in parallel by the supervisor) — this rung adds ZERO
    NEW reds beyond whatever is red BEFORE.
  - `§10 source_match = own`.

*(BEFORE bench baselines recorded here at prereg time, environment only, not an
experimental result. This is a **data-less worktree** — `data/` is not
symlinked, so rung7 reads 214 not the 224 a data-symlinked tree reads; the
discipline is BEFORE == AFTER in THIS environment.)*

- **rung7 BEFORE** = `214 passed, 10 skipped` (0 failed).
- **per-area BEFORE** = `24 failed, 277 passed, 5 skipped` — the failing-node-id
  SET (recorded, compared as a SET never a count):
  ```
  test_composer_driver_migrated.py::test_ground_concern_dispatch_parity   (the known brittle test, fixed in parallel by supervisor — NOT this rung's)
  test_composer_driver_migrated.py::test_question_driver_parity
  test_cortices_tick.py::test_crow_report_byte_identical_via_tick
  test_cortices_tick.py::test_nested_lion_mouse_reciprocity_via_tick
  test_cortices_tick.py::test_ticked_reading_matches_run_reading_flow_report
  test_elaboration_migrated.py::test_detail_request_minted_and_chain_ingested
  test_elaboration_migrated.py::test_expand_synonym_also_serves
  test_elaboration_migrated.py::test_more_without_detail_falls_through_to_summary
  test_elaboration_migrated.py::test_plain_anaphora_uses_summary_not_serve
  test_elaboration_migrated.py::test_progressive_disclosure_serves_next_chunk_each_time
  test_gap_awareness_migrated.py::test_gaps_are_deduped_by_content
  test_gap_awareness_migrated.py::test_implicit_gap_is_filed_once
  test_gap_awareness_migrated.py::test_implicit_unresolved_topic_files_a_gap
  test_gap_awareness_migrated.py::test_resolved_topic_files_no_gap
  test_gap_awareness_migrated.py::test_unaccounted_self_faculty_files_a_clean_self_gap
  test_topic_route_selfheal_migrated.py::test_external_topic_still_routes_with_possessive_guard
  test_topic_route_selfheal_migrated.py::test_infer_3d_from_2d_image_graph_capability_reply
  test_topic_route_selfheal_migrated.py::test_navigate_3d_spaces_graph_capability_reply
  test_topic_route_selfheal_migrated.py::test_polar_capability_conditional_clause_not_topic_routed
  test_topic_route_selfheal_migrated.py::test_polar_capability_question_honest_reply
  test_topic_route_selfheal_migrated.py::test_polar_capability_with_object_still_routes_topic
  test_topic_route_selfheal_migrated.py::test_reflexive_topic_question_routes_to_topic_not_self
  test_topic_route_selfheal_migrated.py::test_self_heals_knowledge_gap_via_teacher
  test_topic_route_selfheal_migrated.py::test_what_is_x_made_of_routes_to_topic_not_know_tail
  ```
  (pre-existing data-less / live-daemon-reconcile reds; this rung must add ZERO
  NEW node ids to this set.)

## 5. HONEST RISK, named before measurement

The headline effect may SHRINK or vanish if the fast delta-rule value estimate
`v` (the fast appraisal, the `ModulatorState` analogue) already anticipates the
correlated drift well enough that momentum buys little. If the i.i.d. control
ALSO shows a CI-above-0 gain, or the autocorrelated gap is null, THAT IS THE
RESULT — reported straight. A real null beats a dressed-up positive. The whole
point of R1 is the failable i.i.d. control; the swing/gain is only a result once
it is measured behind it.

## 6. Prior art (situate honestly)

- Eldar, Rutledge, Dolan & Niv 2016, *TICS* 20(1):15–24 — mood as momentum (RPE
  integral + additive perceptual feedback). The R1 backbone. Architecture theirs;
  our contribution is the glass-box, gated, shared-atom, default-OFF
  instantiation and the failable-control measurement.

Deterministic given the pinned seeds; no wall-clock claim. Prereg committed ALONE
before any code.
</content>
</invoke>
