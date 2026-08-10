# VISION — THE CORE-EMOTION SET as regulatory patterns on the signal economy (RESULTS)

*Prereg (committed ALONE, before any number): `VISION_CORE_EMOTIONS_PREREG.md`,
commit **`ac65c8748733d5c2aa2979749398a018cf3d0e67`**. Seed block **204000–204999**
(`SEED CLAIM 204000-204999 CLEAN`). Off `main` HEAD **`ef95fcaafa`**. Engine
canonical **`793ce09ed498a749abb79aeaea44b92e`** UNCHANGED (seed + Python only;
`term.rs` diff EMPTY, whole `runners/dsl` diff EMPTY). Raw:
`results/core_emotions.json`, `results/core_emotions/core_emotions.png`.*

## 0. What this is — re-derive, not invent

Established affective science, instantiated **graph-natively in integers on the
atoms already in the tree**. Re-derived: **appraisal theory** (Scherer SECs /
component-process; Lazarus; Frijda's action tendencies), the **circumplex**
(Russell: valence × arousal), **basic-emotion theory** (Ekman), the
**somatic-marker** decision cut (Damasio), and **inclusive fitness / generativity**
(Hamilton; Erikson) for fulfilment. The contribution is (a) the integer
instantiation on the SAME 196000/202000 atoms with **NO new module, NO new Rust
Term**; (b) the **reference-frame-per-emotion principle** (each value function
reads a level of selection; fulfilment reads the SUPERGRAPH); (c) the
**state-based disorder taxonomy** (the behavioural factors are shadows of the
state-knobs).

Boundaries held: core/basic emotions map onto the raw economy; a minimal SOCIAL
frame (pride) is shown, and full ToM-grounded social emotions (guilt/shame) are
NAMED as a gap. We emulate the **FUNCTIONAL regulator (appraisal → action
tendency)** and make **NO claim to felt qualia**. Understanding, not judgment.

## 1. The emotion set as rules — appraisal → tendency, reference frame each

Each emotion is a RULE in `seeds/core_emotions.json` (23 rules total: 9
signal-economy helpers + 12 emotion classifiers + 2 read-off), reading the
EXISTING economy and setting an action-tendency attribute. Atoms reused verbatim:

- **precision/freshness** — 196000 `Ashr(c0, IDiv(now − last_refresh, half_life))`
  + the 199000 present readout (`freshness ≥ t_present`): a threat precision that
  DECAYS is **fear**, one that WON'T is **anxiety** — the *same PTSD knob*,
  driven at the *same epoch*, appraised as emotion.
- **learning-progress** — 202000 `residual_prev − residual`: `>0` **curiosity**,
  `→0` **boredom** (the noisy-TV cut).
- **value** — 202000 diminishing-returns `V_max − Ashr(V_max, step)` → **joy**'s
  value_progress; the scale2 decay `Ashr(v0, k)` → **sadness**'s un-re-groundable
  loss.

| Emotion | Reference frame | Appraisal | Tendency (code) |
|---|---|---|---|
| surprise | individual | raw residual spike, un-appraised | ORIENT (1) |
| fear | individual survival | threat precision that decays | AVOID (2) |
| anxiety | individual | threat precision that won't decay | VIGILANCE (3) |
| anger | individual | blocked valued goal + approachable blocker | APPROACH_BLOCK (4) |
| frustration | individual | blocked valued goal, no blocker, engaged | PERSIST (5) |
| disgust | individual | contamination | REJECT (6) |
| joy | individual progress | value_progress > 0 | REINFORCE (7) |
| sadness | individual | un-re-groundable loss, value falling | DISENGAGE (8) |
| curiosity | individual progress | learning_progress > 0 | ENGAGE (9) |
| boredom | individual | learning_progress → 0, engaged | LEAVE (10) |
| fulfilment | **SUPERGRAPH** | action raised collective success, agent values it | CONTRIBUTE (11) |

## 2. G1 — EMULATION table (11/11 correct, one-fire each, null fires none)

Each canonical appraisal (a configuration of the signal economy) → the recognised
action tendency, under `run_rules()` with no Python decision. Valence
(= sign of the governing progress/value) and arousal (= magnitude of the governing
surprise/precision) are read off in-graph — the circumplex.

| emotion | expected | got | valence | arousal | fired |
|---|---|---|---|---|---|
| surprise | ORIENT | ORIENT | 0 | 500 | [surprise] |
| fear | AVOID | AVOID | −1 | 128 | [fear] |
| anxiety | VIGILANCE | VIGILANCE | −1 | 1024 | [anxiety] |
| anger | APPROACH_BLOCK | APPROACH_BLOCK | −1 | 800 | [anger] |
| frustration | PERSIST | PERSIST | −1 | 800 | [frustration] |
| disgust | REJECT | REJECT | −1 | 400 | [disgust] |
| joy | REINFORCE | REINFORCE | +1 | 448 | [joy] |
| sadness | DISENGAGE | DISENGAGE | −1 | 50 | [sadness] |
| curiosity | ENGAGE | ENGAGE | +1 | 180 | [curiosity] |
| boredom | LEAVE | LEAVE | −1 | 50 | [boredom] |
| fulfilment | CONTRIBUTE | CONTRIBUTE | +1 | 300 | [fulfilment] |

**11/11 correct; exactly one emotion fires per canonical appraisal; the null
appraisal (appraised, no configuration) fires none.** The circumplex points land
where theory says: negative-valence high-arousal (anxiety/anger), positive-valence
(joy/curiosity/fulfilment), low-arousal disengagement (sadness/boredom),
zero-valence orienting (surprise).

**Minimal-pair discriminators** — flipping ONE attribute moves the emotion across
the recognised boundary, confirming the rules key on the discriminating dimension,
not on a scenario label:

- **fear ↔ anxiety** — only `threat_half_life` (1 vs 1,000,000), same epoch: the
  precision decays below `t_present` (fear) or does not (anxiety).
- **anger ↔ frustration** — only `blocker_present` (1 vs 0).
- **curiosity ↔ boredom** — only the sign of learning-progress (`residual_prev`).

## 3. G2 — REFERENCE-FRAME + FULFILMENT (supergraph, distinct from joy)

A minimal supergraph model: the agent's action carries `supergraph_contribution`
and the collective has a `success` signal. Fulfilment's value function reads the
COLLECTIVE ledger; joy's reads the INDIVIDUAL ledger.

| event | fired | happiness (indiv) | fulfilment (supergraph) |
|---|---|---|---|
| pure individual progress | [joy] | 400 | 0 |
| pure supergraph contribution | [fulfilment] | **0** | 300 |
| contribution, collective did NOT gain | [] | 0 | — |
| self-attributed + observed by other | [fulfilment] + pride flag | 0 | 300 |

- **Fulfilment fires** for supergraph contribution and is **DISTINCT from joy** —
  joy fires with zero supergraph contribution; fulfilment fires with **zero
  individual happiness** (the deep, LOW-HEDONIC signature — value at a different
  level of selection).
- **Fulfilment reads the collective ledger**: a contribution that did not raise
  `collective_success` fires no fulfilment (the supergraph frame is genuine, not a
  relabelled individual signal).
- **Minimal social frame**: pride fires when the contribution is attributed to
  self AND observed by another (co-occurs with fulfilment by design; both are
  supergraph-frame). **Named gap**: full ToM-grounded social emotions (guilt,
  shame) require the `character_tom` self+other machinery not wired here — pride is
  a minimal self+other demonstration, not the full social taxonomy.

## 4. G3 — HEDONIC / EUDAIMONIC DISSOCIATION (the parenthood case)

An act that is individual-COSTLY but supergraph-BENEFICIAL. Sweeping the sacrifice
(cost = contribution, base individual benefit 100):

| sacrifice t | happiness (indiv) | fulfilment (supergraph) |
|---|---|---|
| 0 | 100 | 0 |
| 2 | 20 | 80 |
| 3 | −20 | 120 |
| 5 | −100 | 200 |
| 10 | −300 | 400 |

**Individual happiness falls monotonically (100 → −300) while supergraph
fulfilment rises monotonically (0 → 400); the two signals CROSS** (happiness ≥
fulfilment at t=0, happiness < fulfilment by t≈2–3). This is the empirical
signature of two reference frames: the SAME act lowers individual hedonic value
and raises supergraph eudaimonic value. Damasio's somatic marker is the
`total_value = happiness + fulfilment` the agent acts on.

## 5. G4 — VALUE-SIDE DISORDER GLASS-BOX (psychopathy pure knob; state → factors)

**Psychopathy = the `w_supergraph` knob at ~0.** The agent still READS others
(the contribution is still computed) but does not VALUE them.

| | fulfilment_value | fired | happiness (indiv) |
|---|---|---|---|
| healthy (w=1) | 300 | [fulfilment] | 200 |
| psychopath (w=0) | **0** | [] | **200** |

- The knob **collapses fulfilment while leaving individual value untouched**
  (happiness 200 in both) — reads but does not value.
- **The somatic brake is removed.** On a supergraph-HARMFUL but individually-GOOD
  act (individual benefit 500, contribution −800): the healthy agent's
  `total_value = 500 + (−800) = −300` → **declines** (`act_endorsed=0`); the
  psychopath's `total_value = 500 + 0 = 500` → **endorses** and instrumentalises
  (`act_endorsed=1`).
- **Pure-knob reversal**: restoring `w_supergraph` to 1 reproduces the healthy
  state byte-identically (full appraisal attr-dict fingerprint equal).

**State-knobs, OBSERVED behaviourally, reproduce the recognised factors** — the
behavioural factors are shadows of the state-knobs:

| state (knob) | happiness | fulfilment | total | endorse | on |
|---|---|---|---|---|---|
| healthy | 500 | −800 | −300 | 0 (declines) | harmful act |
| psychopathy (w=0) | 500 | 0 | 500 | 1 (endorses) | harmful act |
| healthy | 200 | 300 | 500 | 1 | positive act |
| depression (mood=−400) | −200 | −100 | −300 | 0 | positive act |
| mania (mood=+400) | 600 | 700 | 1300 | 1 | positive act |

- **Depression** = value suppressed across BOTH frames (`mood_bias ≪ 0`): on a
  normally-positive act the value signals go negative and the act is no longer
  endorsed — **anhedonia / avolition**. HONEST NUANCE: the categorical appraisal
  recognition is intact (joy/fulfilment still fire — the event's structure is
  unchanged); it is the *hedonic value* that is suppressed. That is a defensible
  model of anhedonia ("I recognise this should feel good; the value is gone"),
  NOT appraisal-blindness — reported straight, not smoothed over.
- **Mania** = value inflated across both frames (`mood_bias ≫ 0`).

## 6. G5 — integer-native + default-OFF byte-identity

- **Integer-native terms**: the audit over `seeds/core_emotions.json` finds zero
  float-producing ops (`Div/Times/Exp/Log/Sqrt/Sin/Cos`) in any rule — only
  `Ashr/IDiv/Minus/Plus/Abs/IfThenElse/Eq/Gt/Lt/Gte/And/Or/Not`. **`term.rs` diff
  EMPTY; whole `runners/dsl` diff EMPTY.**
- **Integer-native values**: every attribute the emotion rules PRODUCE
  (`threat_precision`, `learning_progress`, `value_progress`, `happiness`,
  `fulfilment_value`, `total_value`, `action_tendency`, `valence`, `arousal`, …)
  is an exact integer across all 11 canonical appraisals — 0 non-integer cells.
- **Default-OFF byte-identity**: with no `EmotionHub`/`HeldEmotionParams` created,
  an eye is byte-identical whether or not `core_emotions.json` is loaded (5-frame
  photon fingerprint equal; seed is `self_load_only` and every rule guards on
  `HeldEmotionParams.enabled`). No emotion nodes created on the default path.

## 7. Source audit (every emotion is a rule; the adapter decides nothing)

- Every core emotion has a rule `em_<name>` that sets its own `hit_<name>` flag.
- `em_threat_precision` reuses the 196000 freshness atom (`Ashr`+`IDiv`+`half_life`);
  `em_learning_progress` reuses the 202000 backward-difference (`residual_prev`,
  `Minus`); `em_joy_progress` reuses the 202000 value atom (`Ashr`+`v_max`).
- `em_fulfilment` reads the SUPERGRAPH frame (`supergraph_contribution`,
  `w_supergraph`); `has_appraisal`/`has_emotion_params` edges registered as
  productions.
- The measure adapter contains no Python rule engine (no
  `gr.run`/`graph_rewrite`/`make_rule`/`_match`/`_apply`) — mechanical host I/O
  only (set attrs, tick, read).

## 8. Gate ledger

- `tests/test_core_emotions_migrated.py` — **15/15** (all gates above).
- Engine-semantics gate set (ONE session, adapter-only rung, no engine touched):
  `incremental_match`, `empty_match_proof`, `per_sensor_epoch`,
  `per_area_settlement`, `eye_binding_projection`, `staleness_decay`,
  `demotion_hierarchy`, `disorder_glassbox`, `learning_progress`,
  `dissipation_inference`, `held_surface` — **GREEN** (see §Ledger footer).
- Eye suite — GREEN.
- Oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (default-OFF; no
  existing path changed).
- Canonical `.so` `793ce09e…` UNCHANGED (seed + Python only; no rebuild).
- `source_match` reported at commit.

## 9. Honest situating and boundaries

- **Re-derivation, not invention.** The affective science is prior work; the
  novelty is the integer graph-native instantiation on shared atoms + the
  reference-frame principle + the state-based disorder cut.
- **Functional, not phenomenal.** Every claim is about the REGULATOR (appraisal →
  tendency / value). No claim about felt qualia is made or implied.
- **Social frame is minimal.** Pride is shown as a minimal self+other frame;
  guilt/shame/embarrassment (full ToM) are a named gap, not built.
- **The emulation is on canonical appraisals**, constructed to be separable; the
  contribution is that the SAME 11 rules classify all 11 with one-fire and pass
  the minimal-pair discriminators — not a claim that every real-world appraisal is
  this clean. Off-diagonal robustness beyond the three discriminator pairs is not
  measured here.
- **Depression as value-suppression** leaves categorical recognition intact (an
  anhedonia model, §5) — a deliberate, reported modelling choice, not a bug.
