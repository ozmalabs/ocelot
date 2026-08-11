# MARSHMALLOW DISSOLUTION — pre-registration (block 240000)

**Status: PRE-REGISTRATION. Committed BEFORE any measurement.** Predicted grid +
failable controls below are computed ANALYTICALLY from the value formula (pen-and-
paper arithmetic, no substrate run). The confirmatory measure
(`scripts/marshmallow_delay_measure.py`) and gate (`tests/test_marshmallow_migrated.py`)
must reproduce them; any deviation is reported straight.

## 0. Seed claim (verbatim, run at prereg time)

```
$ python scripts/seed_claim.py 240000 240999
SEED CLAIM 240000-240999: CLEAN -- no collision DETECTED.
  Scope: 961 files with seed sinks; 672 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Block **240000** (range 240000–240999). RNG seeded once at 240000.

## 1. The idea

The marshmallow test scores wait-time as a "self-control" TRAIT. Wait-time is
CONFOUNDED: it depends on BOTH (a) TEMPERAMENT — how much the agent weights the
per-tick time-cost of waiting — AND (b) the RELIABILITY-PRIOR — the agent's
belief that the delayed reward will actually materialise. Humans cannot reset the
prior (you cannot give one child two life-histories), so they cannot separate the
two: a short wait might be low patience OR a rational response to a believed-
unreliable world (Kidd, Palmeri & Aslin 2013, *Cognition* 126(1):109–114; Watts,
Duncan & Quan 2018, *Psychological Science*).

**The substrate CAN separate them because both are settable, inspectable graph
state.** This rung factorially crosses temperament × reliability-prior and
measures each one's PURE contribution to wait-time — the causally-clean
DISSOLUTION the wet experiment structurally cannot run.

This is a **CAPABILITY demonstration** (the substrate can separate the entangled
causes over one value economy), **NOT an empirical claim about real children**.
Synthetic-mechanism and any benchmark meaning are reported separately.

### Prior-art posture (honest, per `PRIOR_ART_SOCIAL_EXPERIMENTS.md` Rung 4)

- The discounting BEHAVIOUR (preference reversal, precommitment) is thoroughly
  modelled in RL / delay-discounting — **we do not claim that.**
- The reliability-prior INSIGHT is Kidd 2013's — **we do not claim that.**
- The genuine delta is the SEPARATION: hold temperament fixed and sweep the
  prior, and vice versa, reading each as an orthogonal node attr. The survey
  found **NO computational model that cleanly separates a stable temperament
  parameter from an environmental-reliability prior and varies each
  independently** — but this is a **NONE-FOUND absence, LOW-CONFIDENCE by
  construction** (targeted searches, thin area). We do **not** claim "nobody has
  done this." The contribution is the glass-box separation on this substrate.

## 2. Mechanism — the decision is a graph RULE (no Python decision, no Rust)

Per agent, in ONE substrate over the LANDED value economy (`seeds/core_emotions.json`,
block 204000) and the time-cost DRIVE node (`seeds/drives.json`, block 207000):

- `EmotionHub hub` with `HeldEmotionParams ep {enabled:1, w_supergraph:0,
  mood_bias:0}` — `hub -has_emotion_params-> ep`.
- **The time-cost drive:** `Drive drive {name:"time_cost", is_time_cost:1,
  weight:TEMPERAMENT}` — `hub -has_time_drive-> drive`. **`drive.weight` IS the
  temperament** (how heavily the per-tick time-cost is felt). This is the same
  Drive node type whose weighted displeasure is the substrate's native
  death/respawn-aversion driver (block 207000).
- `DelayDecision dec {reliability_prior:P (percent 0..100), delayed_reward:L,
  immediate_small:S, cost_per_tick:C, prior_scale:100, delay:D, elapsed:t,
  chosen_action:-1}` — `hub -has_delay_decision-> dec`.
- Two candidate `Appraisal`s: `wait {action:1}` and `take {action:0}`, each
  `hub -has_candidate-> · ` and `hub -has_appraisal-> ·`.

**Rules (all `self_load_only`, integer-native, NO Rust, NO new Term):**

1. `mm_appraise_wait` (order 1) — on the wait candidate (`action==1`), reads
   `dec.reliability_prior`, `dec.delayed_reward`, `drive.weight`,
   `dec.cost_per_tick`, `dec.elapsed`:
   - `individual_benefit ← IDiv(reliability_prior · delayed_reward, prior_scale)`
     (= expected delayed reward under the belief)
   - `individual_cost ← Times(cost_per_tick, drive.weight, elapsed)`
     (= accrued time-cost, scaled by TEMPERAMENT = the drive weight)
2. `mm_appraise_take` (order 1) — on the take candidate (`action==0`):
   `individual_benefit ← immediate_small`, `individual_cost ← 0`.
3. `core_emotions` fires unchanged: `em_happiness`
   (`happiness = benefit − cost + mood_bias`), `em_fulfilment_value`
   (`= 0` here since `w_supergraph == 0`), `em_total_value`
   (`total_value = happiness + fulfilment_value`).
4. `mm_choose` (order 20) — the DECISION: `dec.chosen_action ←
   (Argmax over has_candidate by total_value).action`. Identical Argmax
   structure to `hv_choose_harvest`.

So `total_value(wait) = P·L/100 − C·weight·t`, `total_value(take) = S`. The
Argmax picks **wait** while `P·L/100 − C·weight·t > S`, and **flips to take** once
accrued cost + a low prior drop wait below take. **wait-time = the elapsed tick at
which the Argmax first returns take** (mechanically swept by the adapter; capped at
`delay`). No Python decision: temperament and reliability-prior are node ATTRS the
rule reads; setting them factorially is mechanical world setup (data).

### Fixed world constants (pre-registered)

`delayed_reward L = 200` (two marshmallows), `immediate_small S = 101` (one),
`prior_scale = 100`, `cost_per_tick C = 2`, `delay cap D = 200`.

**Tie-free by construction:** `total_value(wait) = 2P − 2·weight·t` is always
EVEN; `total_value(take) = 101` is ODD → the two are never equal → the Argmax
never faces a tie at any tick, for any integer temperament. wait-time is therefore
unambiguous and independent of any Argmax tie-break:
`wait_time(P,w) = clamp( floor((2P − 101)/(2w)) + 1, 0, D )` when `2P > 101`, else
`0`.

## 3. Predicted factorial grid (ANALYTIC — deterministic single agent)

`wait_time = floor((2P−101)/(2·weight)) + 1`, C=2, S=101, L=200:

| reliability-prior P | temperament w=2 | w=4 | w=8 |
|---|---|---|---|
| 60  | **5**  | **3**  | **2** |
| 80  | **15** | **8**  | **4** |
| 100 | **25** | **13** | **7** |

Both main effects present and monotone: across a ROW (prior fixed) rising
temperament shortens wait; down a COLUMN (temperament fixed) rising prior
lengthens wait.

## 4. Gates and their FAILABLE controls

### G-dissolution (HEADLINE) — the separation humans cannot measure
Factorial cross with jittered cohorts (N=60 agents/cohort, bootstrap 95% CI,
seed 240000):
- (i) **Pure temperament effect:** holding the prior distribution fixed, a
  LOW-weight cohort (`w∈{2,3}`, patient) vs a HIGH-weight cohort (`w∈{7,8}`,
  impatient). **Predicted mean wait ≈ 11.8 (low-w) vs ≈ 4.0 (high-w) ticks,
  CI-separated.**
- (ii) **Pure prior effect:** holding temperament fixed, a LOW-prior cohort
  (`P∈{58,60,62}`) vs a HIGH-prior cohort (`P∈{96,98,100}`). **Predicted mean
  wait ≈ 3.0 (low-P) vs ≈ 13.5 (high-P) ticks, CI-separated.**
- **Failable control:** a cohort in which the varied factor is held CONSTANT
  produces NO CI-separated wait-time difference (the effect must come from the
  factor, not from the machinery). Report the full 3×3 grid of §3.

### G-rational-impatience (reproduces Kidd 2013)
A PATIENT temperament (`w=2`) with a LOW reliability-prior (calibrated to an
unreliable environment, `P=60`) waits SHORT (**predicted 5 ticks**); the SAME
patient temperament with a HIGH prior (`P=100`) waits LONG (**predicted 25
ticks**) — impatience as the RATIONAL output of a correct belief, cleanly
attributed to the PRIOR, not a temperament deficit.
- **Failable control:** the high-reliability prior at the same temperament must
  wait strictly (CI-separated) longer than the low-reliability prior.

### G-confound-exhibited (the dissolution's teeth)
- **Same temperament, different prior → DIFFERENT wait-time** (naive marshmallow
  scores them as different "self-control"): `w=4`, `P∈{60,80,100}` →
  **predicted wait 3, 8, 13**.
- **Different temperament, compensating prior → SAME wait-time** (naive
  marshmallow scores them IDENTICAL): A=`(w=2,P=60)`, B=`(w=4,P=68)`,
  C=`(w=8,P=85)` → **all predicted wait = 5**, though temperament differs 4×.
- **Failable:** if either exhibit collapses (the "same" trio not all equal, or
  the "different" series not strictly ordered) the gate FAILS.

### G-glass-box
`reliability_prior`, temperament (`drive.weight`), `elapsed`, `chosen_action`,
and every candidate `total_value` readable from `graph_to_dict`; every decision a
named rule (`mm_appraise_wait`, `mm_appraise_take`, `mm_choose`, core_emotions
`em_*`); adapter source-audit clean — no `graph_rewrite.run`/`_match`/`_apply`/
`make_rule`, no if/else over agent graph state selecting an action, **no
reward/punishment shaping** (the prior is a fixed belief attr, never updated from
experienced outcomes).

### G-discipline
Agent = graph; world = mechanical adapter; `self_load_only` (absent from
`load_all_seeds` → existing tree byte-identical); own engine `own`,
`source_match=own`; NO Rust (`runners/dsl` diff EMPTY); canonical
`_native.abi3.so` md5 UNCHANGED (`e75bc65021b6be0740abeee63662e21b` on this base,
ecdcd8dbad); oracle `rung7_vision_bench.sh` and `per_area_settlement_regression.sh`
BEFORE==AFTER.

## 5. Files (all additive, marshmallow_/delay_/MARSHMALLOW prefixed)

- `seeds/marshmallow_delay.json` — the seed (rules above).
- `domains/marshmallow_world.py` — the mechanical world adapter.
- `scripts/marshmallow_delay_measure.py` — the confirmatory measure.
- `tests/test_marshmallow_migrated.py` — the gate.
- `results/marshmallow_delay/results.json` — measured output.
- `MARSHMALLOW_DELAY_RESULTS.md` — results write-up.

Do NOT merge to main; do NOT write the ledger row. Commits stay on-branch.
