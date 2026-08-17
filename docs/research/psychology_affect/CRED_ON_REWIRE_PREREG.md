# cred_on: rename the collision, wire the real trait — PREREG

## Context

The first opus design-review pass on the `AFFECT_COUPLING_SHAPE` follow-up
found a NAME COLLISION: `"cred_on"` is used as BOTH a hardcoded arming flag
(always `1.0`, on lightweight `Villager` nodes in
`worlds/bigville_drama_world.py`/`bigville_sim_world.py`, read by
`bd_villager_backs` in `seeds/bigville_drama_social.json`) AND a drawn,
continuous `_PARAM_SPEC` trait (mean 1.0, sd 0.2, clip lo=0.0 hi=None —
measured: 0/100 generated cast100 residents have `cred_on==1.0` exactly).
Different node types, so never a functional collision — but a real risk for
any future reader/rule that assumes the name means one specific thing.

Investigating the real trait's intended consumer: `seeds/bigville_can_beliefs.json`'s
own description ALREADY documents it — *"claim_credible... h seeded from
claim_weight, cred_on, w_supergraph"* — but `worlds/bigville_can_beliefs.py`'s
actual `identity_field` formula for `claim_credible` never read `cred_on` at
all. A real, named, DOCUMENTED consumer that was simply never wired.

## Design

1. **Rename the arming flag** to `cred_decide_on` — surgical, minimal-diff
   edits (not a JSON reformat) at every site: `bigville_drama_world.py`'s
   villager construction, `bigville_sim_world.py`'s reporter construction
   (confirmed to reuse the SAME `bd_villager_backs` rule — "the reporter is
   ANOTHER Villager node -> the SAME credibility rule"), and both copies of
   `bigville_drama_social.json`'s `bd_villager_backs` `where` clause +
   description text. Zero behavior change — same value (`1.0`), same rule
   logic, different key name on both write and read sides.
2. **Wire `cred_on` as a GAIN, not an AffectChannel** (per the original
   review's own recommendation — it doesn't fit affect_coupling's shape):
   `claim_credible`'s `identity_field` becomes
   `cred_on * ((claim_weight - 1.0) * 0.5 + (w_supergraph - 0.5))` —
   multiplicative on the whole existing credibility signal. At the
   population mean (`cred_on=1.0`), byte-identical to today's formula.
   `cred_on`'s own clip (`lo=0.0`, unbounded above) means it can only scale
   magnitude, never flip sign — a genuinely credible person's own view of
   their credibility carries more identity-weight; a zero-credibility
   person's contributes nothing. `p.get("cred_on", 1.0)` (not `p["cred_on"]`)
   so any caller not yet passing the trait keeps today's exact behavior.

## Predictions

1. Grep for `"cred_on"` as an exact key across the whole bigville repo,
   excluding the population-data seeds (`bigville_cast100.json`,
   `bigville_townspeople_*.json`) and the 3 already-legitimate real-trait
   sites (`_PARAM_SPEC`, `game.py`'s personality filter, its own test):
   ZERO remaining arming-flag references.
2. `claim_credible`'s `identity_field` at `cred_on=1.0` (population mean)
   is byte-identical to the pre-change formula; at `cred_on=1.5`/`cred_on=0.0`
   it scales/zeroes proportionally, measured directly (not asserted).
3. Every existing test referencing `bigville_can_beliefs.py`
   (`test_can_native_reimplementation.py`, `test_resident_trust.py`,
   `test_problem_shape_migrated.py`, `test_solver_dispatch_migrated.py`,
   `test_solver_nl_adapter.py`, `test_solve_gap_awareness_migrated.py`,
   `test_solver_can_adapter.py`) still passes.
4. `trust_mayor`'s own `identity_field` formula (a DIFFERENT concept,
   untouched) is unaffected.
5. Both `bigville_drama_social.json` diffs are surgical (a handful of
   lines), not a mass key-reorder — house discipline: don't reformat a
   hand-authored file for an unrelated rename.

## Does NOT claim

Does not claim `cred_on`'s multiplicative role is calibrated to anything
external. Does not touch `bd_villager_backs`'s own `cred_mary`/`cred_john`
formulas (a separate, unrelated computation on `Villager` nodes — this
rung only fixes the CAN network's `claim_credible` concept). Does not
address Phase C (remaining hygiene) or Phase D (Phase 4 self-consistency).
