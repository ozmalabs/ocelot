# BIGVILLE R22 — THE DOCTOR: preventive care + treatment, health as a MONEY-GATED market good (block 270000) — RESULTS

Base SHA (merge-base, origin/main): `59653fd443fb0e0894b5ea59a51bb39402260f4e`
Branch: `worktree-agent-a68f8a06716b529c3`
Prereg: `BIGVILLE_DOCTOR_PREREG.md` (committed ahead of any number).

Health is now a money-gated market good. The doctor MODULATES R14's illness
engine (nothing in `bigville_life_*` was edited). Six graph rules over EXISTING
DSL Terms; ZERO new Rust. Every claim is gated in
`tests/test_bigville_doctor_migrated.py` (**16/16 green**).

## Gate results

- **G-doctor-is-paid (fee-for-service market health).** A checkup / treatment
  MOVES coin patient→doctor, CONSERVED (Σcoin unchanged); the doctor DRAWS INCOME
  (`test_doctor_is_paid_conserved_transfer`, `test_checkup_is_paid_conserved`,
  `test_conserved_transfer_no_node_minting_in_practice`). **Ablate coin**
  (`test_ablate_coin_no_care`): a patient with `coin < fee` gets NO care — the
  rule does not fire, coin unchanged, `screened`/`treated` stay 0. This is the
  marshmallow dissolution: under-investment in care is AFFORDABILITY, not myopia —
  there is no myopia attr; the affordability `where`-gate is the whole mechanism.
- **G-preventive-detection (screening).** A SCREENED patient (paid checkup before
  onset) suffers a SMALLER acute drop (20 of 100) than an UNSCREENED one struck by
  the SAME disease (50 of 100 — base + progression);
  `test_preventive_detection_smaller_drop`.
- **G-treatment-reduces-severity/length.** A TREATED patient suffers a smaller
  acute drop (25 vs 40; `test_treatment_reduces_severity`) AND recovers to full in
  FEWER ticks (`test_treatment_faster_recovery_length`: doctor_care 40/tick vs
  natural_care 5/tick). Ablate treatment → the full R14 trajectory
  (`test_ablate_treatment_full_trajectory`).
- **G-treatment-prevents-death (extreme cases).** A severe disease (base 50,
  health 40) KILLS the untreated (drop 50 ≥ 40 → R14 `bl_death`, cause=2) and is
  SURVIVED by the treated (drop 50−40=10 < 40); `test_treatment_prevents_death`.
- **G-health-inequality (HEADLINE).** `test_health_inequality_tracks_wealth`: a
  wealth gradient `[0,5,10,20,29,30,50,100]` meets ONE severe disease — the 5 poor
  (coin < 30) DIE, the 3 rich (coin ≥ 30) SURVIVE the SAME illness. Survival is
  monotone in wealth; every survivor could afford the fee. Health inequality
  TRACKS wealth inequality — the poor die of a TREATABLE illness.
  - **THE STRUCTURAL LEVER** (`test_public_health_dissolves_the_gradient`): flip
    council-funded PUBLIC HEALTH on (the treasury pays the doctor, R9 shape) → the
    SAME cohort meets the SAME disease and ALL survive; the poor pay nothing
    out-of-pocket; the treasury bears the full (conserved) cost. Only the systemic
    lever saves the poor — never personal effort.
- **ETHICS (induce → measure → RESTORE, NO reward/punishment).** Illness is
  induced + measured, then RESTORED by TREATMENT + recovery to full
  (`test_ethics_illness_is_restored_by_treatment`), and at the structural scale a
  poor cohort left to die is RESTORED by PUBLIC PROVISION
  (`test_ethics_public_provision_restores_the_poor_cohort`). No reward / punishment
  token anywhere in the seed rule logic or the adapter (`test_no_reward_punishment_in_seed`,
  source-audit) — illness / death are STATES, and the RESTORE is care / provision.

## Town-scale measurement (`scripts/bigville_doctor_run.py`, seed 270000)

A town of **n=40** with a seeded lognormal wealth gradient (32 below the fee, 8
at/above), one severe disease for all, `results/bigville_doctor/summary.json`:

| regime | survivors | dead | poor survival | rich survival | corr(wealth, survival) | corr(afford, survival) |
|---|---|---|---|---|---|---|
| **PRIVATE** (fee-for-service) | 8 | 32 | 0.00 | 1.00 | 0.755 | **1.000** |
| **PUBLIC** (council-funded) | 40 | 0 | 1.00 | 1.00 | **0.000** | — |

Private health: survival is EXACTLY affordability (`corr_afford_survival = 1.0`) —
the poor die of a treatable illness, having done nothing wrong. Public health: the
wealth–survival gradient VANISHES (`corr → 0`, all survive). This is the
healthcare instance of the agency/structure bedrock, and a convergent-validity
target (`[[ozma_bigville_reproduces_quantitative_laws]]`) — reproduces the real
wealth-health gradient and the single lever that bends it.

## Discipline ledger (all satisfied)

- `runners/dsl` diff vs base `59653fd443` is **EMPTY** (0 bytes; no Rust, incl.
  `term.rs`).
- Canonical shared `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` UNCHANGED
  START==END; never committed. The worktree copy placed for import is the SAME
  bytes (md5 `fd82…`, gitignored).
- Engine provenance passes (`test_engine_provenance_migrated` 7/7);
  `source_match = own` (∈ {own, shared}); no `.so` md5 pinned in any test.
- `tests/test_bigville_doctor_migrated.py` **16/16**;
  `tests/test_failure_baseline_migrated.py` **11/11**;
  `tests/test_engine_provenance_migrated.py` **7/7**.
- Additive-only, one prefix `bigville_doctor_`; the seed is `self_load_only`
  (`depends_on == []`); NO existing tracked file edited; R14/R7/R9 imported
  read-only.
- Source-audit: no Python decision, no Python rule engine, no reward/punishment
  token; the six named rules are exactly the decision set; no rule mints/destroys
  a node (conservation); coin/funds never set from a fractional `Div`.
- The ~43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh`
  oracles were NOT run — an additive `self_load_only` rung cannot regress another
  suite (per the 2026-07-29 directive).

## Honest residuals

- **Deterministic screening.** "Raises the *probability* of catching a disease
  early" is realized as its expected-value limit: a screened patient IS caught
  early (`screened=1` ⇒ no progression). Stochastic detection was NOT built (keeps
  gates deterministic; the spec tree prefers deterministic mechanism). A future
  rung could sample detection with a screening-raised probability.
- **Death-prevention = drop reduction.** Treatment prevents death by reducing the
  onset drop below `health` (deterministic; no death/heal race). It does not model
  a post-collapse rescue (a treated patient at `health≤0` is not resurrected — no
  rule un-dies a node, by design / conservation).
- **Treatment engaged before onset (drop arm).** The severity/death arm requires
  `treated=1` at onset (you present with acute symptoms; the doctor caps how bad
  the episode gets). The LENGTH arm (`bd_recover`) reads `treated` at recovery
  time, so post-onset treatment still speeds recovery — but only the recovery arm,
  not the drop arm, is available after onset.
- **Public checkup uses a large treasury.** The town run funds the treasury
  generously; a scarce public purse (treasury funds < Σ fees) would ration care —
  a real fiscal-tradeoff lever (ties R9) left for a later rung.
- **Small-N / LLN caveat** applies to the town numbers (n=40); the mechanism is
  deterministic and the per-gate unit tests pin the exact arithmetic, but the
  town survival counts are one seed's draw of the wealth vector.
