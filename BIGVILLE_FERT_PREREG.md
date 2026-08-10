# BIGVILLE R23 — FERTILITY: the quantity–quality decision; does "poorer → more children" EMERGE? (block 271000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, the MODE of each measurement, and the anti-tuning
discipline the results must satisfy.

Base SHA (merge-base, origin/main): `1147c004d12c5ff0379cbda2fc3f11b8a40a13b6`
Branch: `worktree-agent-a3dc0c22481f97daf`
Block: **271000–271999** (R23 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R23 (block 271000, line ~1353) + §0
"THE 3.5% RULE / TWO VALID MODES / anti-tuning" discipline).

## Seed claim (verbatim, `python scripts/seed_claim.py 271 271`)

```
SEED CLAIM 271-271: CLEAN -- no collision DETECTED.
  Scope: 979 files with seed sinks; 698 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(`python scripts/seed_claim.py 271000 271999` — the range form — is likewise CLEAN.)

## The thesis — anti-tuning IS the point

"Do poorer people have more children?" is robustly YES across the demographic
transition, weaker/confounded within a society, and the strongest predictor is
**women's education**, not income per se. It is therefore a downstream SIGNATURE
of deeper mechanisms — child mortality, the cost of children, old-age security,
the mother's opportunity cost — NOT a primitive. **Keying a rule on wealth would
beg the question — the magic-number sin in demographic form.**

So FERTILITY is built as a graph DECISION (`decision_value` = child benefit vs
cost), driven by mechanism inputs, and the wealth→fertility gradient is
**MEASURED**, never asserted. **No rule keys fertility on wealth or class** — the
gradient, if any, must come THROUGH the mechanisms (source-audit gate).

## Architecture (target: ZERO new Rust)

- The fertility `decision_value`, the quantity–quality tradeoff, the child-mortality
  replacement, and the old-age-security motive are all **graph rules over EXISTING
  DSL Terms** (`IfThenElse` / `Eq` / `And` / `Gte` / `Gt` / `Plus` / `Minus` /
  `Times` / `Max` / `Min` / `Div` / `Attr` / `Var` / `Lit` + `set_attr`). **No new
  Rust Term.** `git diff 1147c004d1 -- runners/dsl` MUST be empty (incl. `term.rs`).
- The fertility decision UPGRADES **R14's** birth (currently an unconditional
  ingest event — no fertility decision) into an emergent `decision_value`. R14
  (`bigville_life_*` — birth/rearing), R22 (`bigville_doctor_*` — the child/health
  mortality driver), R18 (`bigville_school_*` — schooling cost + the mother's
  opportunity cost), R9 (`bigville_fisc_*` — old-age security / safety net) are
  imported/reused READ-ONLY. `BigvilleFertWorld` subclasses `BigvilleDoctorWorld`
  (⊃ `BigvilleLifeWorld`) so R14 + R22 come in by import; R18/R9 relationships
  enter the town measurement as world facts the adapter delivers.
- New additive files only, all prefixed `bigville_fert_`:
  `seeds/bigville_fert_decide.json`, `worlds/bigville_fert_world.py`,
  `scripts/bigville_fert_gen_seeds.py`, `scripts/bigville_fert_run.py`,
  `tests/test_bigville_fert_migrated.py`, this file,
  `BIGVILLE_FERT_RESULTS.md`, `results/bigville_fert/summary.json`.
  **No existing tracked file is edited.**
- The seed is **`self_load_only`** (never auto-loaded into the default agent;
  loaded explicitly by this rung's world adapter only). Additive + self-load ⇒
  the rung cannot regress any other suite. (Hence, per the 2026-07-29 directive,
  the 43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` oracles
  are NOT run.)

## The mechanism — a fertility DECISION, never keyed on wealth

Each fertile person/couple holds a `FertilityState` (edge `has_fertility`). Three
staged one-shot rules (armed → clear, guaranteed termination) compute the decision:

1. **`bf_oldage`** — the old-age-security (insurance) motive:
   `oldage_motive = IfThenElse(safety_net == 1, 0, oldage_value)`.
   No pension/safety-net → children as old-age insurance (motive ON); add a safety
   net (R9) → motive OFF. Arms stage 2.
2. **`bf_quantity_quality`** — the Becker decision (`decision_value` = benefit − cost):
   `decision_value = base_target + child_labour_benefit + oldage_motive − school_cost − opp_cost`;
   `desired_surviving = Max(floor, decision_value)`.
   Children CHEAP (no school cost, child labour useful) → high desired_surviving
   (quantity); children EXPENSIVE (schooling R18 + the mother's opportunity cost)
   → low desired_surviving (few, invested "quality"). Arms stage 3.
3. **`bf_mortality_replace`** — the demographic-transition engine (ties R22):
   `survival = Max(eps, 1 − mortality)`; `fertility = desired_surviving / survival`.
   High child mortality (poor, no R22 well-baby care) → more births to ensure some
   survive; ablate mortality (free public health, R22's lever) → `fertility` falls
   to `desired_surviving`.

**`fertility` is the decision_value read-off (a desired-births RATE).** Actual
birth remains the honest R14 ingest boundary, but now GATED/scaled by the graph's
decision: the adapter's `beget()` reads `fertility` and mints `floor(fertility)`
children (R14 `make_person`) — birth flows FROM the decision. **No wealth/coin/class
attr appears in any `bf_*` rule.**

## Gates (each an isolated unit test with a failing control) — with MODE

`tests/test_bigville_fert_migrated.py`:

**G-fertility-is-a-decision (FORWARD, unit):**
- `test_fertility_is_a_decision_value` — `decision_value` = benefit − cost exactly;
  a higher-cost person gets a lower `fertility` than an identical lower-cost one.
- `test_birth_flows_from_the_decision` — `beget()` mints more children for a
  high-decision_value person than a low one (birth is the decision, not fixed ingest).

**G-quantity-quality — Becker (FORWARD, unit):**
- `test_quantity_quality_tradeoff` — cheap children (no school, child labour) →
  MORE desired_surviving; expensive children (school + opp cost) → FEWER.
- `test_ablate_school_cost_shifts_to_quantity` — CONTROL: ablate the school cost →
  desired_surviving RISES (the tradeoff shifts toward quantity).

**G-child-mortality-drives-fertility — ties R22 (FORWARD, unit):**
- `test_high_mortality_raises_fertility` — same desired_surviving, higher mortality
  → higher `fertility` (replacement).
- `test_ablate_mortality_fertility_falls` — CONTROL: mortality → 0 (public health,
  R22's lever) → `fertility` falls to desired_surviving.

**G-old-age-security — insurance motive (FORWARD, unit):**
- `test_no_safety_net_raises_fertility` — no pension → oldage_motive ON → higher
  `fertility`.
- `test_safety_net_lowers_fertility` — CONTROL: add a safety net (R9) → oldage_motive
  OFF → lower `fertility`.

**G-does-"poorer→more-children"-EMERGE (HEADLINE — MEASURE-FIRST, FORWARD):**
- `test_poorer_more_children_gradient_emerges` — a town with a wealth gradient, where
  wealth enters ONLY through the four mechanism inputs (poor: high mortality [no R22
  doctor], no school cost [can't afford R18 → quantity], child labour, no safety net
  [no R9 savings]; rich: the reverse), and the fertility rules NEVER see wealth.
  MEASURE `corr(wealth, fertility)`. **FORWARD MODE — no target fitted.** The gate
  asserts only the SIGN emerges (poorer → more children, corr < 0) as convergent
  validity with the demographic transition / Becker; the magnitude is reported as
  indicative with a CI over seed-replays, never a sharp decimal.
- `test_structural_levers_bend_the_gradient` — town ablations: free public health
  (mortality→low for all), free schooling (school cost→0 for all), universal safety
  net (R9) each move overall fertility / flatten the gradient — the agency/structure
  counterfactuals.

**Discipline / source-audit:**
- `test_no_python_agent_decision_source_audit` — the adapter never COMPUTES the
  decision in Python (no `graph_rewrite`/`make_rule`/rule engine), and no
  `if <decision-attr>` branch; NO reward/punishment token.
- `test_no_rule_keys_fertility_on_wealth` — **THE anti-tuning source-audit:** no
  `bf_*` rule reads `coin` / `wealth` / `class` / `rich` / `poor` in match, where,
  or effects. The gradient comes THROUGH the mechanism inputs only.
- `test_seed_is_self_load_only_and_named` — the seed is `self_load_only`, declares no
  deps, its rule set is EXACTLY the three named fertility decisions, no rule
  mints/destroys a node, NO new Rust.

## Failing controls that actually fail (the gates above include)

- ablate school cost → desired_surviving RISES (else quantity–quality is fake);
- mortality → 0 → `fertility` FALLS (else the R22 tie is fake);
- safety net ON → `fertility` FALLS (else old-age-security is fake);
- the headline sign (corr < 0) must EMERGE — if it does not, that is a reported
  FINDING (a missing driver), not a silent pass.

## MODE declaration (the ONLY fabrication is misreporting this)

- **All unit gates: FORWARD** — the mechanism is pre-registered here; each gate
  reports the effect that falls out of the fixed arithmetic.
- **The headline town measurement: FORWARD** — sweep the wealth gradient, no target
  number fitted; report `corr(wealth, fertility)` and the poor/rich mean fertility
  AS THEY FALL OUT. Near the real "poorer → more children" direction emerging
  WITHOUT being tuned = convergent validity. The mechanism directions are
  theory-derived (replacement, Becker, insurance), NOT fit to reproduce a wealth
  gradient — the gradient is an emergent COMPOSITION.
- **Small-N / LLN caveat (§0):** the town is small; the gradient is reported as
  INDICATIVE with a CI over seed-replays, never a sharp decimal the town cannot
  support.

## Discipline ledger the results must satisfy

- `python -m pytest tests/test_bigville_fert_migrated.py -q` — all green.
- `python -m pytest tests/test_failure_baseline_migrated.py -q` — 11/11.
- `python -m pytest tests/test_engine_provenance_migrated.py -q` — 7/7,
  `source_match ∈ {own, shared}`.
- `git diff 1147c004d1 -- runners/dsl` — EMPTY (no Rust).
- canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED start==end
  (never committed).
- source-audit: seed `self_load_only`, adapter decision-free, AND no rule keys
  fertility on wealth.
- Two commits: (1) this prereg, (2) the build. Left on the branch; the supervisor
  merges.
