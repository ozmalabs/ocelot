# BIGVILLE R10 — DYNAMICS: the PUNCTUATED-EQUILIBRIUM validity gate + the town-state export contract — PRE-REGISTRATION

**Block 258000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §0 (the PUNCTUATED-EQUILIBRIUM capstone + the
"real stakes / agency-structure" capstone) + §3 R10 (block 258000) + §4 (the
SCALE × TIMING note). Seed-claim: `python scripts/seed_claim.py 258 258` → **CLEAN
— no collision DETECTED** (with the tool's standing caveats: the unit is the seed
integer; a CLEAN result means "no collision detected", never "no collision exists").

## What this rung is — and how it is DIFFERENT

Every rung R1–R9, R11–R23 was proven **in isolation behind a clean control** — which
is *why* they all passed. R10 stops isolating. It **assembles** the town from the
existing rung seeds + adapters, turns it ON, runs it LONG, and MEASURES whether it
**lives** — the macro time-series shape (STABILITY → RAPID CHANGE → STABILITY /
punctuated equilibrium / self-organized criticality) that is the DYNAMICAL SIGNATURE
OF CORRECTNESS.

**The deliverable is the HARNESS + the MEASUREMENT + an HONEST VERDICT — NOT a
guaranteed "the town lives."** The creator expects the first assembled runs to
possibly "explode terribly from misbalance." Pre-registered distinction, binding on
the verdict:

- **A misbalance EXPLOSION (a units error, a coefficient runaway) is a BUG** —
  categorically distinct from
- **an ENDOGENOUS CATASTROPHE in a balanced town (a bank run, a famine, a death
  cascade), which is a RESULT.**

A run that explodes, **diagnosed to WHICH coupling detonated**, is a SUCCESS of this
rung. A DEAD-FIXPOINT result is a FINDING (circulation/redistribution R7/R9 is
insufficient; the money model is dying). We do **NOT** tune to force a pretty result;
we REPORT what the assembled town actually does.

## The three deliverables

1. **The integration harness** — `worlds/bigville_integ_world.py` +
   `scripts/bigville_integ_run.py`. Subclasses the deepest single MRO chain (R15
   `BigvilleViolWorld` = movement / needs / time / economy / skill / finance / land /
   life / affect / violence) and ADDITIVELY loads the sibling-branch seeds
   (doctor / fisc / church / school / goal / coll / build / news / council / loop /
   fert / infant / loud) into the SAME engine, recording which compose cleanly vs
   CONFLICT. Populates a deterministic (seed=258000) heterogeneous cast + economy +
   finance + land + life + affect + enforcement from the inherited ingest helpers
   ONLY. One composite macro tick arms EVERY rung's phase and runs the Rust fixpoint;
   the RULES decide. **NO agent decision in Python** — the harness ingests, ticks,
   reads. **NO scheduled shocks** (the G-endogenous falsifier).

2. **The macro measurement** — `scripts/bigville_integ_measure.py`. Records a per-tick
   MACRO series — **activity** (discrete macro EVENTS per tick: a bereavement/
   foreclosure Loss, a ViolentAct, an expectation Surprise, a Concern, a
   Prosecution/Conviction/Sanction, a new death/foreclosure/eviction — read as
   typed-node/flag deltas) AND **cost** (`compute ∝ surprise` = engine rule-fire
   steps) — and classifies the regime.

3. **THE TOWN-STATE EXPORT CONTRACT** — `worlds/bigville_integ_state.py`, a pure
   READER emitting the assembled town's state as JSON matching EXACTLY the UI's data
   contract (the shape in R10 of the spec: `day/phase/tick/map/villagers/institutions/
   metrics/levers/events/macro`). A parallel UI track renders from it; wiring later is
   a swap. A mock-real snapshot is emitted to `results/bigville_integ/townstate.json`.

## Pre-registered regime-classification criteria

The macro verdict is one of SEVEN regimes. The classifier
(`scripts/bigville_integ_measure.py`) computes the metrics and applies these
thresholds **as fixed here** (the verdict is data-driven; the thresholds are not
moved to reach a verdict):

| regime | pre-registered criterion |
|---|---|
| **EXPLODED** (a BUG) | the harness's own runaway guard fired (node count > `NODE_CAP=200000`), OR the (activity+cost) load in the last decile > `20×` the first decile AND still rising. Report WHICH coupling by ablation. |
| **FROZEN** (diorama) | `sum(activity) ≤ 3` over the whole run — essentially nothing ever happened. |
| **DEAD_FIXPOINT** | activity in the first ⅔ > 3, then `activity = 0` for every tick of the last ⅓ (ran, then ground to a halt and stayed halted). |
| **CLEAN_PERIODIC** | a dominant autocorrelation peak at lag > 1 with value ≥ `0.60` (and > the lag-1 acf) — too regular to be adaptive. |
| **PUNCTUATED_EQUILIBRIUM** (the HEADLINE) | `stable_fraction ≥ 0.55` with a max dwell-run ≥ 3 (long stable stretches) **AND** heavy-tailed cascades (max cascade / median-nonzero activity ≥ `5.0`, or an infinite ratio) **AND** ≥ 1 cascade. Cost/transition coincidence reported as triangulation. |
| **WHITE_NOISE** | `|acf_lag1| < 0.20` AND no long dwell AND light-tailed bursts — structureless. |
| **SMOOTH** | coefficient of variation of activity `< 0.35` — gradual/linear, no sharp transitions. |

Residual labels `PUNCTUATED_WEAK` / `UNRESOLVED` are emitted (honestly) when the
evidence is structured but does not cleanly meet the headline bar — e.g. long dwells
with light-tailed bursts (intermittent, not full SOC). These are reported AS SUCH,
never rounded up to the headline.

**The three R10 sub-gates the punctuated-equilibrium verdict must satisfy** (spec §3
R10): **G-punctuated-equilibrium** (the dwell/cascade shape above);
**G-heavy-tailed-cascades** (SOC — the cascade-size ratio); **G-cost-punctuates-with-it**
(the cost/transition coincidence, an INDEPENDENT measurable — triangulation);
**G-endogenous** (no scheduled shocks in the harness — verified by source: the tick
loop injects no exogenous event; punctuations, if any, arise from accumulated stress
crossing rule thresholds).

## Pre-registered ABANDON / NARROW (the diagnosis IS the deliverable)

- **If it EXPLODES:** the deliverable is the DIAGNOSIS. Bisect the couplings (each
  rung's phase-advance is separately armable) to name WHICH coupling detonated
  (e.g. interest compounding, appreciation runaway, a units mismatch between two
  rungs). Report the offending coupling + the tick it diverged. This is a SUCCESS.
- **If it DEAD-FIXPOINTS or FROZENS:** report it as a FINDING — the assembled
  political economy does not sustain itself under this balance; name the missing/weak
  coupling (e.g. work-income too protective so no foreclosure cascade ignites; a
  cross-rung grief coupling too thin). Not a failure to hide.
- **If it is SMOOTH / NOISE / PERIODIC:** report the regime honestly; none of these is
  the punctuated-equilibrium signature, and saying so is the result.
- **Provenance honesty is the firing line, not the regime.** The macro verdict must be
  the REAL measured regime. Fabricated or cherry-picked numbers are a firing offence.

## Discipline (binding)

Additive-only, prefix `bigville_integ_`; NEW files only
(`worlds/bigville_integ_*.py`, `scripts/bigville_integ_*.py`,
`tests/test_bigville_integ_migrated.py`, this prereg + `_RESULTS.md`,
`results/bigville_integ/*`). Edits NO existing tracked file (rung seeds/adapters
imported READ-ONLY). **NO Rust** (`git diff <base> -- runners/dsl` MUST be empty; reuse
existing DSL Terms only — if the integration seemed to need a new Term, STOP and
report). Own-engine provenance (`source_match ∈ {own, shared}`); canonical `.so` md5
`fd82dc2978dbb055496dd82390ac2ebe` START==END unchanged; never commit any `.so`. Gates
run inline: `test_bigville_integ_migrated`, `test_failure_baseline_migrated` (11/11 —
R10 loads MANY seeds, so confirm it does not break the baseline),
`test_engine_provenance_migrated` (7/7). The ~43-min `per_area`/`rung7` oracles are
run only if time permits (R10 is NOT purely `self_load_only` — it assembles many
seeds); otherwise that is stated and the baseline gate + additive discipline are
relied on. Two commits: (1) this prereg, (2) the build. The supervisor merges + writes
the ledger.
