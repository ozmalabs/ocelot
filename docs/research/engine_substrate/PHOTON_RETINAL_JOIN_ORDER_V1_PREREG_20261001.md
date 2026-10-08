# Production retinal join-order panel v1 preregistration

Date: 2026-10-01

## Question

Does explicit prefix-order measurement improve productive matching for an independent five-clause production rule, and does the best sequence change when relation supports have different cross-column correlations despite identical global cardinalities?

## Rule and fixture

Use `photon_column_synthesizes_retinal_percept` from `seeds/photon_retina_per_sensor.json`, with its complete epoch guards and `set_attr_if_different` effects. Build 12 columns. Each column has a positive number of outgoing edges for each of `rod_receptor`, `l_receptor`, `m_receptor`, `s_receptor`, and one `has_retinal_percept`. Every receptor has epoch 1 and a type-constant activation; each column has `column_epoch=1`. The percept on the last column has epoch 0 and is the only expected productive match; all other percepts have epoch 1 and must be rejected by the production `Gt` guard. The active match writes four derived values and advances that percept to epoch 1, after which closure must stop.

Run three matched support profiles, each with three fresh-process replicates:

- `uniform`: two receptors of each type per column;
- `correlated`: each relation type has the same per-column multiplicity sequence, cycling 1,2,3,4;
- `rotated`: each relation has the same global cardinality histogram as `correlated`, but the 1–4 multiplicities rotate across columns by relation type.

For every worker, measure the normal cardinality-based installer order and all 120 permutations of the five match clauses using `add_rule_preserving_match_order`. Rebuild the same graph independently for each arm. Measure candidate tests, terminal progress, wall time, installed order, and canonical final graph digest. Repeat the default and measured minimum-work order without scale instrumentation. The analyzer independently verifies all 120 permutations, exact fixture invariants, the unique productive percept, guard negatives, semantic parity, source stability, and the minimum-work winner.

## Gates

- Nine unique workers cover three profiles × three replicates.
- Each worker measures exactly all 120 unique five-clause permutations and one automatic-order arm.
- Source/native fingerprints remain unchanged.
- Every arm has the same graph input and exact production rule body; only match sequence differs.
- Exactly the final-column percept changes; it reaches epoch 1, all guards hold, and a terminal probe makes no progress.
- All order arms produce the same canonical graph facts; instrumented/plain default and best results agree.
- The minimum-work order is reproducible across three replicates for each profile, or any variation is explicitly reported.

## Limits

This is a synthetic retinal rule fixture with controlled supports, not a natural image workload or a claim about production frame throughput. Exhaustively finding the best of 120 orders is an offline oracle; it is not the proposed online selector. It tests a second production rule family but remains one bounded pattern and three constructed support distributions.
