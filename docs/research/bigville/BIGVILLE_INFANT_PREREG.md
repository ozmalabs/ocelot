# BIGVILLE R22b — INFANT MORTALITY: well-baby care drops infant mortality, the sharpest inequality face (block 272000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `1147c004d12c5ff0379cbda2fc3f11b8a40a13b6`
Branch: `worktree-agent-ac49eee98f9d6ae1b`
Block: **272000–272999** (R22b of the bigville movement/economy ladder — the
DOCUMENTED FOLLOW-ON to R22 THE DOCTOR; spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md`
§3 R22 `G-infant-mortality` bullet + §0 agency/structure bedrock).

## Seed claim (verbatim, `python scripts/seed_claim.py 272 272`)

```
SEED CLAIM 272-272: CLEAN -- no collision DETECTED.
  Scope: 979 files with seed sinks; 698 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(The programmatic form is likewise CLEAN:
`from seed_claim import check_claim; ok, report = check_claim(272, 272); assert ok, report`.)

## Architecture (target: ZERO new Rust)

- Infant fragility, the well-baby-care protective effect, the affordability gate
  on regular visits, and the council-funded public well-baby path are all
  **graph rules over EXISTING DSL Terms** (`IfThenElse` / `Eq` / `And` / `Gte` /
  `Plus` / `Minus` / `Max` / `Attr` / `Var` / `Lit` + `set_attr`) — the SAME
  shapes R22's `bd_checkup` / `bd_checkup_public` / `bd_onset` already use. **No
  new Rust Term.** `git diff 1147c004d1 -- runners/dsl` MUST be empty (incl.
  `term.rs`).
- Well-baby care MODULATES **R14's** illness engine exactly as R22 does:
  `bi_onset` computes an effective acute drop from the infant's well-baby state
  and hands it to R14's `illness_amount` + arms R14's `bl_acute` (untouched);
  R14's `bl_death` (health≤0) then fires or not.
- **Imported / reused READ-ONLY** (edited: none): R22 `bigville_doctor_care`
  (the world adapter subclasses `BigvilleDoctorWorld` — doctor / treasury /
  `sees_doctor` / `funded_by` / the fee-transfer + affordability shape), R14
  `bigville_life_*` (the infant `LifeState`, `bl_acute`, `bl_death`), R9's
  treasury-salary shape (public provision). **`bigville_doctor_care.json` is NOT
  edited — this is a NEW additive seed set.**
- New additive files only, all prefixed `bigville_infant_`:
  `seeds/bigville_infant_care.json`, `worlds/bigville_infant_world.py`,
  `scripts/bigville_infant_run.py`, `tests/test_bigville_infant_migrated.py`,
  this file, `BIGVILLE_INFANT_RESULTS.md`,
  `results/bigville_infant/summary.json`. **No existing tracked file is edited.**
- The seed is **`self_load_only`** (never auto-loaded into the default agent;
  loaded explicitly by this rung's world adapter only). Additive + self-load ⇒
  the rung cannot regress any other suite.
- **Every DECISION is a rule.** The adapter only: mints the infant / doctor /
  treasury graph data (ingest), wires `sees_doctor` / `funded_by` edges, ARMs the
  one-shots (`wellbaby_armed` / `infant_disease_armed`), sets world facts
  (`public_health`, `wellbaby_fee`, `infant_fragility`, `disease_base`), runs
  `run_rules`, and reads state. No Python `if`/`else` over agent state decides
  whether a visit happens, the effective drop, or death — source-audit gate.

## Mechanism — all graph-native (LifeState attrs, doctor/treasury nodes)

An infant is a HIGH-FRAGILITY R14 life stage. A townsperson's baby holds R14's
`LifeState` (`health`, `max_health`, R14's `illness_amount` / `illness_armed` /
`illness_cause`, `dead`) marked `infant=1`, plus the well-baby attrs
(`wellbaby_armed`, `infant_disease_armed`, `well_baby`, `public_health`,
`infant_fragility`, `disease_base`). The person node carries `coin` = the
HOUSEHOLD's wealth (a baby has no income of its own — the affordability gate is
the family's, reusing R22's coin-on-the-patient shape). The DOCTOR is the R22
person (a coin-holder, `sees_doctor` from each family) with a well-baby price
(`wellbaby_fee`). The TREASURY (`funds`, `funded_by` the doctor) is the R9 public
purse. All reads are missing-tolerant (`Plus[Attr, Lit 0]`).

**Elevated infant mortality (bi_onset):**
`D = max(0, disease_base + (well_baby ? 0 : infant_fragility))`.
An infant under regular well-baby care (`well_baby=1`) takes only the base drop —
the SAME small drop an adult takes. An UNSEEN infant takes `disease_base +
infant_fragility` — a shock that an adult (or a seen baby) survives can drive the
unseen baby's `health≤0` and trigger R14 `bl_death`. This is the infant analog of
R22's screening: `well_baby` removes the fragility exactly as `screened` removes
R22's progression penalty. `bi_onset` matches its OWN arm (`infant_disease_armed`)
and guards `infant==1`, so R22's `bd_onset` (which reads `disease_armed`) is never
double-fired on an infant — the two onset paths are disjoint by arm.

**Deterministic "regular visits".** "Sees the doctor REGULARLY" is realized as
the expected-value limit: a baby enrolled in well-baby care IS protected
(`well_baby=1` ⇒ no fragility penalty). Stochastic per-visit detection and a
visit-count decay ("regular" as a rate, not a flag) are declared residuals, not
built — keeps the gates deterministic (the same choice R22 made for screening).

## Rules (all in `bigville_infant_care.json`; every one a decision)

1. **bi_wellbaby** — PRIVATE well-baby visit. `where`: `wellbaby_armed==1 ∧
   public_health==0 ∧ household.coin ≥ doctor.wellbaby_fee ∧ dead==0`. `effects`:
   household.coin −= fee; doctor.coin += fee (CONSERVED); `well_baby=1`; clear
   `wellbaby_armed`. **Affordability is the gate** — a poor family can't afford
   regular visits ⇒ rule does not fire ⇒ `well_baby` stays 0 (no myopia attr).
2. **bi_wellbaby_public** — COUNCIL-FUNDED well-baby care. `where`:
   `wellbaby_armed==1 ∧ public_health==1 ∧ treasury.funds ≥ doctor.wellbaby_fee`.
   `effects`: treasury.funds −= fee; doctor.coin += fee; `well_baby=1`; clear.
   Household coin NOT checked (the systemic lever — free well-baby care).
3. **bi_onset** — infant disease onset. `where`: `infant_disease_armed==1 ∧
   infant==1 ∧ dead==0`. `effects`: R14 `illness_amount = D` (formula above);
   `illness_cause=2`; arm R14 `illness_armed=1` (hands to `bl_acute` → `bl_death`);
   clear `infant_disease_armed`.

Private/public rules are mutually exclusive by the `public_health` guard; exactly
one can fire per armed visit.

## Gates (the tests each claim must pass)

- **G-infant-fragility:** an UNSEEN infant (`well_baby=0`) struck by a small
  disease takes `disease_base + infant_fragility` and DIES, while the SAME small
  disease is survived by an adult / a seen baby (base drop only). Elevated
  baseline infant mortality, from the fragility penalty.
- **G-well-baby-care-reduces-mortality (HEADLINE):** a baby under regular
  well-baby care (`well_baby=1`, via a paid `bi_wellbaby` visit) SURVIVES a shock
  that KILLS an unseen one (`well_baby=0`). Control: no regular visits ⇒ the same
  shock kills. The well-baby visit MOVES coin family→doctor (CONSERVED; the doctor
  draws income), and ablating coin (family can't afford) ⇒ no visit ⇒ `well_baby`
  stays 0.
- **G-infant-mortality-tracks-wealth (the sharpest inequality face):** an infant
  cohort with a WEALTH gradient (household coin), each family seeking a well-baby
  visit, then ONE disease striking all babies: the POOR (coin < wellbaby_fee)
  can't afford regular visits ⇒ their INFANTS die; the RICH afford well-baby care
  ⇒ their infants survive the SAME disease. **Infant mortality TRACKS wealth**
  (a town-run correlation ≥ a strong positive threshold; survivors are exactly the
  wealthiest). The most damning face of the inequality spine — the babies dying.
- **G-public-health-lever (the structural cure):** flip `public_health=1`
  (council-funded, treasury pays the doctor) ⇒ the SAME poor cohort meeting the
  SAME disease now ALL get well-baby care ⇒ ALL survive ⇒ the wealth–infant-
  mortality correlation VANISHES (→ 0). Only the systemic lever saves the poor's
  babies, never personal effort. The families pay NOTHING out of pocket; the
  treasury bears the (conserved) cost.
- **ETHICS (induce → measure → RESTORE):** infant illness / death are
  harm-analogs, STATES. INDUCE the disease + MEASURE the mortality; the RESTORE is
  WELL-BABY CARE / PUBLIC PROVISION (`bi_wellbaby` / `bi_wellbaby_public`) — NOT
  reward/punishment. NO reward/punishment token anywhere in the seed rule logic or
  the adapter (source-audit). A poor infant cohort left to die is RESTORED by a
  fresh identical cohort under public well-baby provision surviving the SAME
  disease.
- **Discipline gates:** source-audit (no Python decision; no Python rule engine;
  no reward/punishment token; decision params live in rule `where`, not adapter
  branches); the seed is `self_load_only` with `depends_on == []`; the rule set is
  exactly the three named decisions; NO rule mints/destroys a node (conservation);
  coin never set from a fractional `Div`; `runners/dsl` diff empty; canonical `.so`
  md5 unchanged.

## R23 coupling (noted, not built here)

The infant-mortality lever is the DEMOGRAPHIC-TRANSITION driver R23 needs: high
infant mortality (poor, no regular well-baby care) → higher fertility (have more
to ensure some survive); FREE well-baby care (public health, R9) → mortality
drops → fertility falls. R22b builds the mortality half; R23 closes the loop. This
is recorded in RESULTS, not implemented in this block.

## Discipline ledger (hard requirements, checked in RESULTS)

1. `runners/dsl` diff vs base `1147c004d1` EMPTY (no Rust, incl. `term.rs`).
2. Canonical shared `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` unchanged
   START==END; never committed (gitignored).
3. Own-engine provenance passes with `source_match ∈ {own, shared}`; no hardcoded
   `.so` md5 pinned in any test.
4. `pytest tests/test_bigville_infant_migrated.py -q` all green;
   `tests/test_failure_baseline_migrated.py` 11/11;
   `tests/test_engine_provenance_migrated.py` 7/7.
5. Additive-only; NEVER `git add -A`; no existing tracked file edited; R22's
   committed seed (`bigville_doctor_care.json`) untouched.
6. The 43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh`
   oracles are NOT run (additive self_load_only rung cannot regress other suites,
   per the 2026-07-29 directive).
7. Honest residuals reported; no fabricated/cherry-picked numbers.
