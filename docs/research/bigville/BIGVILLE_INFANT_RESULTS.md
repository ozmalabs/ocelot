# BIGVILLE R22b — INFANT MORTALITY: well-baby care drops infant mortality, the sharpest inequality face (block 272000) — RESULTS

Measured AFTER the pre-registration (`BIGVILLE_INFANT_PREREG.md`, committed
`53ea2758d1`). Every number below is the graph's outcome, read off the seed rules
(`bi_wellbaby` / `bi_wellbaby_public` / `bi_onset`) — no Python decision. The
measurement runner is `scripts/bigville_infant_run.py`; the dump is
`results/bigville_infant/summary.json`.

Base SHA (merge-base, origin/main): `1147c004d12c5ff0379cbda2fc3f11b8a40a13b6`
Branch: `worktree-agent-ac49eee98f9d6ae1b`
Engine: `ada5f2aefc25`, `source_match = own` (∈ {own, shared}).

## Headline findings (all graph-native)

### G-infant-fragility — an infant is a HIGH-FRAGILITY life stage
A small disease (`disease_base = 20`) strikes an unseen infant and an adult, both
at `health = 40`:
- **Unseen infant:** effective drop `= 20 + infant_fragility(40) = 60 ≥ 40` →
  `health → 0` → **DIES** (R14 `bl_death`, cause 2).
- **Adult (R22 `admit`, no fragility):** drop `= 20 < 40` → **survives**, `health =
  20`.

The SAME shock an adult shrugs off kills the unseen baby — elevated baseline infant
mortality, entirely from the `bi_onset` fragility penalty.

### G-well-baby-care-reduces-mortality (HEADLINE) — regular visits drop mortality
Two identical infants (`health = 40`, `fragility = 40`), same shock
(`disease_base = 20`). One gets a paid well-baby visit (`well_baby = 1`), one does
not:
- **Seen (well-baby care):** drop `= 20` only → **survives**, `health = 20`.
- **Unseen (control):** drop `= 20 + 40 = 60` → **DIES**.

The visit is fee-for-service: the family paid `10`, the doctor drew `10` income
(a CONSERVED transfer). A baby seen regularly survives a shock that kills an unseen
one — well-baby care drops infant mortality significantly.

### G-infant-mortality-tracks-wealth — the sharpest inequality face
An infant cohort with a wealth gradient (household coin
`[0, 5, 10, 20, 29, 30, 50, 100]`, `wellbaby_fee = 30`), each family seeking a
well-baby visit, then ONE disease (`disease_base = 20`) striking every baby:

| household coin | affords well-baby care? | infant outcome |
|---|---|---|
| 0, 5, 10, 20, 29 | no (coin < 30) | **DIES** |
| 30, 50, 100 | yes | survives |

- **5 of 8 infants die**; infant mortality **= 0.625**.
- Every survivor's family could afford the fee (`survivors_min_wealth = 30`).
- **Wealth–survival correlation = +0.755** — infant mortality TRACKS wealth.

The poor's babies die of a disease the rich's babies survive, the families having
done nothing wrong. This is the most damning point of the inequality spine — not
the poor merely sicker or landless or under-schooled, but their BABIES dying.

### G-public-health-lever — the structural cure dissolves it
Flip council-funded PUBLIC well-baby care on (`public_health = 1`, the treasury
pays the doctor). The SAME poor cohort meeting the SAME disease:
- **All 8 infants get well-baby care; infant mortality → 0.0.**
- **Wealth–survival correlation → 0.0** — the gradient VANISHES.
- Families paid NOTHING out of pocket (`out_of_pocket = [0,…,0]`); the treasury
  bore the full conserved cost (`treasury_paid = 240 = 8 × 30`).

Only the systemic lever saves the poor's babies — never personal effort. This is
the healthcare instance of the whole agency/structure thesis (§0), applied to its
darkest point.

## ETHICS (induce → measure → RESTORE)

Infant illness / death are harm-analogs, STATES. A poor cohort left to die
(mortality `= 1.0`, INDUCED + MEASURED) is RESTORED not by personal effort but by
PUBLIC PROVISION — a fresh identical poor cohort under public well-baby care
survives the SAME disease (mortality `= 0.0`). The RESTORE is well-baby care /
public provision, NOT reward/punishment. There is NO reward/punishment token in the
seed rule logic or the adapter (source-audit gate green).

## R23 coupling (noted, not built here)

R22b builds the mortality half of the demographic-transition engine R23 needs:
high infant mortality (poor, no regular well-baby care) → higher fertility (have
more to ensure some survive); FREE well-baby care (public health, R9) → mortality
drops → fertility falls. R23 will close the loop with an emergent fertility
decision. This block supplies the `bi_*` mortality lever it couples to; nothing
fertility-related is implemented here.

## Discipline ledger (all satisfied)

1. `git diff 1147c004d1 -- runners/dsl` — **EMPTY** (no Rust, incl. `term.rs`).
2. Canonical shared `.so` md5 `fd82dc2978dbb055496dd82390ac2ebe` — **unchanged
   START == END**; never committed (gitignored in the worktree).
3. Own-engine provenance — `source_match = own` (∈ {own, shared}); no `.so` md5
   pinned in any test.
4. Gates: `tests/test_bigville_infant_migrated.py` **12/12** green;
   `tests/test_failure_baseline_migrated.py` **11/11**;
   `tests/test_engine_provenance_migrated.py` **7/7**.
5. Additive-only; explicit-path adds only (never `git add -A`); no existing tracked
   file edited; R22's `bigville_doctor_care.json` untouched (its six rules intact —
   `test_r22_doctor_seed_untouched`). The infant onset uses a DISJOINT arm
   (`infant_disease_armed`) so R22's `bd_onset` is never double-fired.
6. The 43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` oracles
   were **NOT run** (an additive `self_load_only` rung cannot regress another suite,
   per the 2026-07-29 directive).

## Honest residuals

- **Deterministic well-baby flag.** "Sees the doctor REGULARLY" is realized as the
  expected-value limit: `well_baby = 1` ⇒ fully protected. Stochastic per-visit
  detection and a visit-COUNT decay ("regular" as a rate that lapses, not a latch)
  are declared residuals, not built — the same deterministic choice R22 made for
  screening. A one-off visit and a sustained regimen are indistinguishable in this
  model.
- **Household coin on the infant node.** A baby has no income; the affordability
  gate is the family's, modeled by carrying the household's `coin` on the infant
  person node (R22's coin-on-the-patient shape). There is no explicit parent→child
  `pays_for` edge — family poverty is a scalar on the baby, not a resolved kin
  transfer. A parent-pays wiring is deferred.
- **Preventive-only for infants.** R22b models the well-baby (preventive) arm.
  Curative infant treatment (an infant analog of `bd_treat`) is not wired to the
  fragility penalty; the headline "regular visits drop mortality" is the preventive
  claim, and that is what is built and measured.
- **`infant = 1` is an ingest flag, not a life-stage transition.** An infant is
  minted `infant = 1` at the birth boundary. Aging an infant out of the
  high-fragility stage (a `bl_come_of_age`-style transition that clears `infant`)
  is not modeled here — the block studies mortality WITHIN the infant stage.
- **No stochastic disease incidence.** Every baby is struck by the same
  deterministic disease to isolate the mortality gradient; a Poisson-like incidence
  model is out of scope (would add variance without changing the mechanism).
