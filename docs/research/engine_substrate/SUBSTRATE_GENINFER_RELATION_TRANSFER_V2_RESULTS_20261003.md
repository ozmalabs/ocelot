# GenInfer relation transfer v2 results (2026-10-03)

## Result

The preregistered three-family gate **passes**. In 30 fresh-core, source-locked
cases, all nine enabled clean cases acquired the exact target matrix during
training and applied the same graph-resident generator to the distinct
held-out signature (9/9). Per-family transfer was 3/3 for `[2,1,1,2]`,
`[2,-1,1,1]`, and `[1,1,1,2]`. The held-out signature was inserted only after
training closure and generator state had been captured.

All nine enabled corrupted-heldout cases used the training-acquired generator
and failed the exact target oracle, as required. Disabled controls acquired no
target generator (0/9); identity controls minted no identity generator (0/3).
The independent analyzer reports no gate errors. The measured median closure
time was 9.84 ms for training and 0.74 ms for held-out application; median
wall times were 9.93 ms and 0.83 ms respectively. These figures cover small
2-D fixtures on this host and do not establish a general scaling law.

## Scope of evidence

This is direct evidence that the existing bounded GenInfer path can induce
new integer 2×2 linear generators from observed relation signatures, store
them as graph data, and reuse them on separate inputs. It strengthens the
earlier one-map result with three task families and controls. The operator
family, seed path, representation, and integer search bound are authored in
advance; observations are synthetic; and this does not show the substrate
choosing its own learning goals, inventing an unbounded operator class, or
improving its own learner. It is a concrete substrate learning capability,
not general autonomous self-improvement.

## Artifacts and next gate

- [Preregistration](SUBSTRATE_GENINFER_RELATION_TRANSFER_V2_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_relation_transfer_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_relation_transfer_v2.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_geninfer_relation_transfer_v2_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_relation_transfer_v2_20261003.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_relation_transfer_v2_analysis_20261003.json)

The next tractability gate should vary input relation count, coordinate bound,
and generator-search volume under a fixed task family, reporting candidate
checks, closure time, peak memory, and exact transfer. It should also include
null transforms and relation-label/coordinate perturbations, so scaling and
false acceptance are measured together. Any broader capability claim still
requires tasks outside this authored geometric operator family.
