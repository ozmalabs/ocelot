# BIGVILLE R23 — FERTILITY: the quantity–quality decision; does "poorer → more children" EMERGE? (block 271000) — RESULTS

Base SHA (merge-base, origin/main): `1147c004d12c5ff0379cbda2fc3f11b8a40a13b6`
Branch: `worktree-agent-a3dc0c22481f97daf`
Prereg: `BIGVILLE_FERT_PREREG.md` (separate commit, ahead of this build).
Gates: `tests/test_bigville_fert_migrated.py` — **13/13 green**.

## What was built

FERTILITY as a graph **DECISION**, never a rule keyed on wealth. Three staged
one-shot rules (`seeds/bigville_fert_decide.json`, `self_load_only`, ZERO new Rust,
composing only existing DSL Terms):

1. **`bf_oldage`** — `oldage_motive = safety_net==1 ? 0 : oldage_value` (the R9
   old-age-security insurance motive).
2. **`bf_quantity_quality`** — the Becker decision:
   `decision_value = base_target + child_labour_benefit + oldage_motive − school_cost − opp_cost`;
   `desired_surviving = max(floor, decision_value)`.
3. **`bf_mortality_replace`** — the demographic-transition engine (ties R22):
   `survival = max(eps, 1 − mortality)`; `fertility = desired_surviving / survival`.

`fertility` is a desired-births RATE; birth stays the honest R14 ingest boundary
but is now GATED by the decision (`beget()` mints `floor(fertility)` children).
`BigvilleFertWorld` subclasses `BigvilleDoctorWorld` (⊃ `BigvilleLifeWorld`), so
R14 + R22 come in by import; R18/R9 relationships enter the town measurement as
world facts the harness delivers. **No `bf_*` rule reads coin/wealth/class.**

## Glass-box findings

### G-fertility-is-a-decision — HELD (FORWARD)
`decision_value` = benefit − cost exactly (4 vs 2 for a matched low/high-cost pair);
a higher-cost family reaches a lower `fertility`. `beget()` mints 4 vs 1 children —
birth flows FROM the decision, not a fixed ingest. **Source-audit
(`test_no_rule_keys_fertility_on_wealth`): NO rule reads coin/wealth/class/rich/
poor/income/money.** The gradient comes THROUGH the mechanisms.

### G-quantity-quality (Becker) — HELD (FORWARD)
Cheap children (child labour, no school) → desired_surviving 4; expensive children
(school + the mother's opp cost) → desired_surviving 1. **Ablate the school cost →
desired_surviving rises 0 → 2** (the tradeoff shifts toward quantity).

### G-child-mortality-drives-fertility (ties R22) — HELD (FORWARD)
Same desired_surviving (2), mortality 0.5 → fertility 4; mortality 0 → fertility 2.
**Ablate mortality (public health, R22's lever) → fertility falls 4 → 2** (= the
demographic transition, from mechanism).

### G-old-age-security (insurance motive) — HELD (FORWARD)
No safety net → `oldage_motive` 2 → fertility 4; add a safety net (R9) →
`oldage_motive` 0 → fertility 2. **The R9 lever lowers fertility.**

### G-does-"poorer→more-children"-EMERGE — HEADLINE, EMERGED, **FORWARD** mode
Town of n=40, wealth from a lognormal gradient, wealth entering ONLY through the
four mechanism inputs (`scripts/bigville_fert_run.py`, `results/bigville_fert/summary.json`),
12 seed-replays (default_rng(271000+k)):

| measurement | value (mean ± 95% CI over 12 replays) |
|---|---|
| **corr(wealth, fertility)** | **−0.917 ± 0.020** |
| poor mean fertility (coin < R18 school fee) | 7.62 ± 0.04 |
| rich mean fertility (coin ≥ R9 pension wealth) | 0.83 ± 0.05 |
| gradient emerged (poorer → more) | **TRUE** |

**"Poorer → more children" EMERGED** — a strong negative wealth→fertility gradient,
**FORWARD mode: no target fitted.** The mechanism directions (mortality replacement,
Becker quantity–quality, old-age insurance) are theory-derived and locked
a-priori; the wealth gradient is an emergent COMPOSITION, never keyed on wealth in
any rule. This is convergent validity with the demographic transition / Becker
(a third quantitative law reproduced from mechanism).

**Structural levers bend the gradient (agency/structure counterfactuals):**

| lever (applied to EVERY family) | poor mean | rich mean | corr |
|---|---|---|---|
| baseline | 7.56 | 0.98 | −0.955 |
| free public health (mortality → low) | **5.54** | — | −0.947 |
| free schooling (school cost → 0) | — | **2.12** | −0.981 |
| universal safety net (R9) | **5.41** | — | −0.892 |

Public health drops the poor's mortality-replacement births; free schooling shifts
the rich toward quantity; a safety net removes the poor's old-age motive — each a
systemic lever moving what no individual family's choice can.

## Honest residuals

- **Magnitude is INDICATIVE, not a benchmark.** Small N (40) and a synthetic town;
  the gradient is reported with a CI over seed-replays, never a sharp decimal. The
  **poor mean fertility (~7.6) is STEEPER than empirical TFR (~5–6)** — an honest
  residual of the a-priori mechanism magnitudes (base_target 3.0 + child labour 1.0
  + old-age 1.5, all replacement-inflated at high mortality). The magnitudes were
  locked on per-mechanism principle, NOT fit to a TFR target; the SIGN (poorer →
  more) is what the gate asserts and is robust across replays and levers.
- **The wealth→mechanism coupling is REDUCED-FORM**, not a full multi-year
  simulation: the run harness maps each family's wealth to the four mechanism inputs
  through each rung's affordability gate (R22 well-baby fee, R18 school fee, R9
  pension wealth), with health access and the educated mother's opportunity cost as
  smooth functions of wealth (education is continuous and the strongest real
  predictor) and the three affordability gates discrete. This is a documented
  world model in the MEASUREMENT harness — it is NOT a fertility rule and NOT in the
  world adapter; the fertility rules never see wealth. Mechanism-proven at the unit
  level (9 unit gates); the town number is a forward convergent-validity
  measurement, not a benchmark.
- **Literature situated:** real-world, women's EDUCATION > income is the strongest
  predictor (captured here as the mother's opportunity cost, the top-weighted cost);
  confounds not modelled — reverse causality, contraception access, cultural norms.

## Discipline ledger

- `tests/test_bigville_fert_migrated.py` — **13/13 green**.
- `tests/test_failure_baseline_migrated.py` — **11/11**.
- `tests/test_engine_provenance_migrated.py` — **7/7**, `source_match = own`.
- `git diff 1147c004d1 -- runners/dsl` — **EMPTY** (no Rust; `term.rs` untouched).
- canonical `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` — **UNCHANGED** start==end
  (never committed).
- Additive-only, one prefix `bigville_fert_`; seed `self_load_only`; no existing
  tracked file edited; adapter decision-free; **no rule keys fertility on wealth**.
- The 43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` oracles
  were **NOT run** (additive `self_load_only` rung cannot regress other suites, per
  the 2026-07-29 directive).
