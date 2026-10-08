# MetaShape downstream label source audit (2026-09-26)

## Decision

The repository does not currently provide an independently labeled, real-world
corpus for evaluating `categorise_by_shape` as a MetaShape filing decision.
The 20-item utility benchmark remains the strongest direct consumer result, but
its oracle is synthetic and its own report correctly limits the claim. Do not
promote its accuracy estimate to natural teaching data or general task utility.

## Sources inspected

| Source | Labels present | Why it cannot serve as independent MetaShape gold |
|---|---|---|
| `META_SHAPE_FIRST_CLASS_PREREG.md` / results | Authored shape observations, expected minted structures, and controls | These are designed to test the same learner and recognition ladder; using them as semantic filing labels would evaluate against the mechanism's own task specification. |
| `SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY` v1.1/v1.2 | Locked family/abstain oracle over 20 schema items | Valid for the stated synthetic schema task, but not naturally collected or human-judged examples. |
| `tests/test_mechanism_transfer_migrated.py` | Expected mechanism and MetaShape for two authored goals | Tests retrieval/transfer mechanisms, not independent filing judgments or a representative teaching distribution. |
| `tests/test_ground_categories.py` and category-oriented fixtures | Explicit `category` attributes and expected category hubs | The target taxonomy is domain-authored category, not MetaShape; the classifier also consumes string attributes, so the category field itself can leak the answer. |
| `tests/test_grammar_teacher.py` and `domains/teach.py` call sites | Teacher payloads and explicit categories | Teacher source answers and caller-provided filing labels are not blinded MetaShape judgments; several paths bypass the consumer under evaluation. |

Search scope was repository docs/research, tests, and `domains/` call sites for
`categorise_by_shape`, category labels, and teacher filing. This is a code/data
inventory, not proof that no external or unindexed dataset exists.

## Filing-consumer call-site census

A Python AST scan of executable `.py` files under `domains/`, `substrate/`, and
`worlds/` found 36 syntactic calls to `teach()`: 31 pass `category=` directly;
one more (`domains/code_write_growth.py`) constructs a kwargs dictionary with
`category="code_write_constructions"` before calling; four omit a visible
category and are inside the epistemic, class-baseline, and legal-hedging codebook
seed helpers. Repository search found those four helpers invoked only by tests,
not by another in-repository production caller. The scan found no explicit
`categorise=` argument. Several direct `category=` arguments are forwarded
variables, so their values may be `None` and syntax alone cannot show whether
they bypass the shape classifier.

Therefore the exact production footprint is not demonstrated: `teach()` always
records a `ShapeObservation`; a non-None explicit category skips the
`categorise_by_shape` filing decision, while `None` falls through to it. The
direct utility benchmark tests a real callable, but the census does not establish
how often the default-category branch runs in production. The next integration
gate should trace runtime values and branch outcomes at actual `teach()` call
sites before prioritizing category utility as a live capability. This source
census is syntactic and does not prove runtime frequency.

## Consequence for measurement

The next valid natural-data evaluation needs independently judged examples with
at least: original item type and attributes; intended MetaShape or an explicit
“none of the current shapes” label; source/provenance; and a split by source or
task so near-duplicates cannot cross train/test. The prediction input must mask
the gold-label field and any direct aliases. Judges should see the item and the
held MetaShape descriptions, not the classifier output. Preserve disagreements
and abstentions rather than adjudicating them into forced labels.

Until such data is available, continue measuring substrate mechanisms with
synthetic, source-locked fixtures and report each result as conditional. Useful
next general-capability gates can still use independently specified task outputs
(for example held-out transform predictions, exact graph-state parity, or
action outcomes); those measure their own task families and must not be treated
as substitutes for semantic MetaShape labels.

## Evidence and next work

- [MetaShape categorisation utility results](SUBSTRATE_METASHAPE_CATEGORISATION_UTILITY_RESULTS_20260926.md)
- [MetaShape first-class results](META_SHAPE_FIRST_CLASS_RESULTS.md)
- [Mechanism transfer fixture](../../../tests/test_mechanism_transfer_migrated.py)
- [Ground-category fixture](../../../tests/test_ground_categories.py)
- [Teacher filing path](../../../domains/teach.py)

Next work: keep the MetaShape natural-utility claim open; prioritize a capability
matrix across independent task families and choose the next experiment from
existing held-out task oracles, with acquisition cost and negative controls
reported alongside success.
