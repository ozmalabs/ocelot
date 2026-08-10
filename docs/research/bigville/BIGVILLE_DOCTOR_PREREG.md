# BIGVILLE R22 — THE DOCTOR: preventive care + treatment, health as a MONEY-GATED market good (block 270000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `59653fd443fb0e0894b5ea59a51bb39402260f4e`
Branch: `worktree-agent-a68f8a06716b529c3`
Block: **270000–270999** (R22 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R22 + §2.9 VIOLENCE/HEALTH + §0
agency/structure bedrock).

## Seed claim (verbatim, `python scripts/seed_claim.py 270000 270999`)

```
SEED CLAIM 270000-270999: CLEAN -- no collision DETECTED.
  Scope: 977 files with seed sinks; 694 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(`python scripts/seed_claim.py 270 270` — the single-integer form the supervisor
named — is likewise CLEAN.)

## Architecture (target: ZERO new Rust)

- The doctor's fee (a conserved coin transfer), the affordability gate, the
  screening/early-detection effect, the treatment severity/death modulation, and
  the council-funded public-health path are all **graph rules over EXISTING DSL
  Terms** (`IfThenElse` / `Eq` / `And` / `Gte` / `Gt` / `Plus` / `Minus` /
  `Times` / `Max` / `Min` / `Attr` / `Var` / `Lit` + `set_attr`). **No new Rust
  Term.** `git diff 59653fd443 -- runners/dsl` MUST be empty (incl. `term.rs`).
- The doctor MODULATES **R14's** illness engine: `bd_onset` computes an effective
  acute drop from the screened/treated state and hands it to R14's `illness_amount`
  + arms R14's `bl_acute` (untouched); R14's `bl_death` (health≤0) then fires or
  not. R14 (`bigville_life_*`), R7 (`bigville_fin_*` — coin), R9
  (`bigville_fisc_*` — the treasury-salary shape) are imported/reused READ-ONLY.
- New additive files only, all prefixed `bigville_doctor_`:
  `seeds/bigville_doctor_care.json`, `worlds/bigville_doctor_world.py`,
  `scripts/bigville_doctor_gen_seeds.py`, `scripts/bigville_doctor_run.py`,
  `tests/test_bigville_doctor_migrated.py`, this file,
  `BIGVILLE_DOCTOR_RESULTS.md`, `results/bigville_doctor/summary.json`.
  **No existing tracked file is edited.**
- The seed is **`self_load_only`** (never auto-loaded into the default agent;
  loaded explicitly by this rung's world adapter only). Additive + self-load ⇒
  the rung cannot regress any other suite.
- **Every DECISION is a rule.** The adapter only: mints the doctor / treasury /
  patient graph data (ingest), wires `sees_doctor` / `funded_by` edges, ARMs the
  one-shots (`checkup_armed` / `treat_armed` / `disease_armed` / `rec_armed`),
  sets world facts (`public_health`, fees, `disease_base`), runs `run_rules`, and
  reads state. No Python `if`/`else` over agent state decides whether care
  happens, the severity, recovery, or death — source-audit gate.

## Mechanism — all graph-native (LifeState attrs, doctor/treasury nodes)

Health is money-gated. A townsperson holds R14's `LifeState` (`health`,
`max_health`, R14's `illness_amount`/`illness_armed`/`illness_cause`, `dead`) plus
the doctor-interaction attrs (`checkup_armed`, `treat_armed`, `disease_armed`,
`rec_armed`, `screened`, `treated`, `public_health`, `disease_base`,
`detect_penalty`, `treat_relief`, `doctor_care`, `natural_care`). The DOCTOR is a
person (a coin-holder, `sees_doctor` from each patient) with a price list
(`checkup_fee`, `treat_fee`). The TREASURY (`funds`, `funded_by` the doctor) is
the R9 public purse. All reads are missing-tolerant (`Plus[Attr, Lit 0]`).

**Effective acute drop (bd_onset):**
`D = max(0, disease_base + (screened? 0 : detect_penalty) − (treated? treat_relief : 0))`.
Screening ⇒ caught early ⇒ no progression penalty. Treatment ⇒ relief ⇒ smaller
drop; if relief keeps `D < health`, the person survives what would otherwise kill
them (death-prevention = drop reduction, deterministic, no death/heal race).

**Deterministic screening.** "Raises the *probability* of catching a disease
early" is realized as the expected-value limit: a screened person IS caught early
(`screened=1` ⇒ no penalty). Stochastic detection is a declared residual, not
built (keeps gates deterministic; the spec tree prefers deterministic mechanism).

## Rules (all in `bigville_doctor_care.json`; every one a decision)

1. **bd_checkup** — PRIVATE preventive. `where`: `checkup_armed==1 ∧
   public_health==0 ∧ patient.coin ≥ doctor.checkup_fee ∧ patient.dead==0`.
   `effects`: patient.coin −= fee; doctor.coin += fee (CONSERVED); `screened=1`;
   clear `checkup_armed`. **Affordability is the gate** — can't afford ⇒ rule does
   not fire ⇒ `screened` stays 0 (the marshmallow dissolution: no myopia attr).
2. **bd_checkup_public** — COUNCIL-FUNDED preventive. `where`: `checkup_armed==1 ∧
   public_health==1 ∧ treasury.funds ≥ doctor.checkup_fee`. `effects`:
   treasury.funds −= fee; doctor.coin += fee; `screened=1`; clear. Patient coin
   NOT checked (the systemic lever).
3. **bd_treat** — PRIVATE curative. `where`: `treat_armed==1 ∧ public_health==0 ∧
   patient.coin ≥ doctor.treat_fee ∧ patient.dead==0`. `effects`: patient.coin −=
   fee; doctor.coin += fee (CONSERVED); `treated=1`; clear.
4. **bd_treat_public** — COUNCIL-FUNDED curative. `where`: `treat_armed==1 ∧
   public_health==1 ∧ treasury.funds ≥ doctor.treat_fee`. `effects`:
   treasury.funds −= fee; doctor.coin += fee; `treated=1`; clear. Patient coin NOT
   checked.
5. **bd_onset** — disease progression. `where`: `disease_armed==1 ∧
   patient.dead==0`. `effects`: R14 `illness_amount = D` (formula above);
   `illness_cause=2`; arm R14 `illness_armed=1` (hands to `bl_acute`); clear
   `disease_armed`.
6. **bd_recover** — recovery tick (severity/LENGTH arm). `where`: `rec_armed==1 ∧
   patient.dead==0`. `effects`: `health = min(max_health, health + (treated?
   doctor_care : natural_care))`; clear `rec_armed`. Treated ⇒ heals fast ⇒
   shorter illness; untreated ⇒ slow natural recovery (uses a SEPARATE armed flag,
   never R14's `heal_armed`, so no clash with `bl_recover`).

Private/public rules are mutually exclusive by `public_health` guard; exactly one
of each pair can fire.

## Gates (the tests each claim must pass)

- **G-doctor-is-paid:** a checkup/treatment MOVES coin patient→doctor, CONSERVED
  (Σcoin unchanged); the doctor's coin RISES (draws income). Ablate coin (patient
  can't afford) ⇒ rule does not fire ⇒ NO care, coin unchanged, `screened`/
  `treated` stay 0.
- **G-preventive-detection:** a SCREENED patient (checkup before onset) suffers a
  SMALLER acute drop than an UNSCREENED one struck by the SAME disease (early
  detection avoids the progression penalty). Control: no checkup ⇒ larger drop.
- **G-treatment-reduces-severity/length:** a TREATED patient suffers a SMALLER
  acute drop (severity) AND recovers to full health in FEWER `bd_recover` ticks
  (length) than an untreated one. Ablate treatment ⇒ full R14 trajectory.
- **G-treatment-prevents-death:** a SEVERE disease that drives an untreated
  patient to `health≤0` (DIES, R14 `bl_death`) is SURVIVED by a treated patient
  (drop reduced below health). Control (no treatment) ⇒ dies.
- **G-health-inequality (HEADLINE):** a population with a wealth gradient, one
  disease striking all: the POOR (coin < treat_fee) can't afford treatment ⇒ DIE;
  the RICH afford it ⇒ SURVIVE the SAME illness. Survival TRACKS wealth
  (money-gated health). **STRUCTURAL LEVER:** flip `public_health=1`
  (council-funded, treasury pays the doctor) ⇒ the poor are treated ⇒ the
  survival–wealth gradient VANISHES (only the systemic lever saves the poor, never
  personal effort).
- **ETHICS (induce → measure → RESTORE):** the disease INDUCES a health drop /
  death (harm-analogs, STATES); the RESTORE is TREATMENT / PUBLIC PROVISION
  (bd_treat / bd_treat_public / bd_recover) — NOT reward/punishment. NO
  reward/punishment token anywhere in the seed rule logic or the adapter
  (source-audit). A poor cohort left to die is RESTORED by turning on public
  health and re-running the SAME disease.
- **Discipline gates:** source-audit (no Python decision; no Python rule engine;
  no reward/punishment token; decision params live in rule `where`, not adapter
  branches); the seed is `self_load_only` with `depends_on == []`; the rule set is
  exactly the six named decisions; NO rule mints/destroys a node (conservation);
  coin never set from a fractional `Div`; `runners/dsl` diff empty; canonical `.so`
  md5 unchanged.

## Discipline ledger (hard requirements, checked in RESULTS)

1. `runners/dsl` diff vs base EMPTY (no Rust, incl. `term.rs`).
2. Canonical shared `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` unchanged
   START==END; never committed.
3. Own-engine provenance passes with `source_match ∈ {own, shared}`; no hardcoded
   `.so` md5 pinned in any test.
4. `pytest tests/test_bigville_doctor_migrated.py -q` all green;
   `tests/test_failure_baseline_migrated.py` 11/11;
   `tests/test_engine_provenance_migrated.py` 7/7.
5. Additive-only; NEVER `git add -A`; no existing tracked file edited.
6. The 43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh`
   oracles are NOT run (additive self_load_only rung cannot regress other suites,
   per the 2026-07-29 directive).
7. Honest residuals reported; no fabricated/cherry-picked numbers.
