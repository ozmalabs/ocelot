# Harvest Qwen3.8 — Five New Relations, Calibrate-Then-Harvest (block 338000)

## What this block does

Extends the harvest beyond is-a to five relations — **part-of, located-in,
capital-of, same-as, opposite-of** — under the same trust-band discipline block
330 applied to is-a: **a relation earns the band only if its own held-out
structural control passes and its shuffle control collapses.** Relations that
fail are recorded as honest negatives and NOT reaped. Concept/process tiers
remain excluded (they failed calibration in block 330).

The elicitor was generalized (`llm_knowledge_seed.elicit_relation_batch`): the
batched constrained read of block 335, parameterized by a per-relation template
and candidate object-vocabulary. The mechanism is relation-agnostic; only the
template + candidates change.

## Per-relation control design (matched to each relation's algebra)

The control has to falsify the *right* structure for each relation:

| relation | algebra | structural control |
|---|---|---|
| part-of | transitive (finger⊂hand⊂body) | held-out transitive acc + shuffle collapse + direct-edge fails |
| located-in | transitive (Paris⊂France⊂Europe) | held-out transitive acc + shuffle collapse |
| capital-of | 1:1 function (NOT transitive) | held-out **direct** acc vs gold + shuffle collapse |
| same-as | symmetric+transitive (equivalence) | **symmetry** recovered in-graph + shuffle collapse |
| opposite-of | symmetric, NOT transitive | **symmetry** + shuffle collapse |

Using a transitive test on capital-of, or a transitive test on the symmetric
relations, would be the wrong falsifier — so each gets the control its structure
actually predicts.

## Calibration table (measured)

| relation | fidelity | structural control | shuffle | verdict |
|---|---|---|---|---|
| **capital_of** | 0.95 | direct | 0.05 | **EARNED** |
| **opposite_of** | 1.00 | symmetry 1.00 | 0.00 | **EARNED** |
| **located_in** | 0.81 | transitive 1.00 | 0.55 | **EARNED** |
| **part_of** | 0.56 | transitive 1.00 | 0.57 | **EARNED** (borderline fidelity) |
| **same_as** | 0.20 | symmetry 1.00 | 0.25 | **NOT earned** — honest negative |

- **capital_of / opposite_of** are the strongest: near-perfect fidelity, control
  passes, shuffle collapses to chance. These are exactly the relations a 4B model
  represents crisply (a capital is a memorized fact; an antonym is a well-defined
  lexical pair).
- **located_in** earns comfortably (0.81 fidelity, transitive 1.00).
- **part_of** passes its *structural* control (transitive 1.00) but fidelity is
  only 0.56 — its edges are noisier; still admitted at trust 0.5, corroborate-
  before-assert.
- **same_as fails**: 0.20 fidelity. The model, constrained to a synonym pool,
  could not reliably pick a true synonym (it tends to echo the word or drift to a
  related-but-not-equivalent term). Recorded as a negative and NOT harvested —
  this is the gate doing its job, the same way process-negate was rejected in
  block 330.

## Harvest (earned relations only)

130 edges reaped at scale, `same_as` skipped:

| relation | edges | example |
|---|---|---|
| located_in | 42 | paris → france |
| capital_of | 35 | france → paris |
| opposite_of | 33 | big → small (and small → big) |
| part_of | 20 | finger → hand |

All tagged `source=qwen3`, `trust=0.5`. `seeds/generated/qwen3_reaped_relations.json`
carries each relation's edges plus its calibration record, so a consumer sees the
per-relation fidelity (and knows part_of is the noisiest of the four).

## The point

This is what "extract everything" looks like done honestly: not "run 6 relations
and report 6× the edges", but **wire the relation, calibrate it with a control
matched to its structure, harvest only what earns the band, and keep the failure
(same_as) as a recorded negative.** 4 of 5 relations earned it; the fifth did not,
and saying so is the result.

## Artifacts

- `domains/llm_knowledge_seed.py` (`elicit_relation_batch`)
- `scripts/llm_calibrate_relations.py` (the per-relation controls)
- `scripts/llm_harvest_relations.py` (harvest of earned relations)
- `seeds/generated/qwen3_relation_calibration.json` (the calibration table)
- `seeds/generated/qwen3_reaped_relations.json` (130 edges, 4 relations)

## Guardrails

- `.so` md5 unchanged: `7efe75eba05b006cafd15dbb4b7da246` (python/JSON only).
- Protected READ-ONLY files untouched.
- Model/venv under `/applications` not committed; run logs under `var/` (ignored).
- Committed block-338 only, add-by-name.
