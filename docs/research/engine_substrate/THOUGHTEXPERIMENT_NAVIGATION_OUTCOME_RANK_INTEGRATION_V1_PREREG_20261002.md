# Navigation outcome-ranker integration v1 — preregistration

**Date:** 2026-10-02  
**Question:** Can the production graph-resident correction ranker consume candidate outcomes from disjoint navigation training cases and improve first-candidate utility on held-out directions?

## Design

This is a one-family integration probe, not the confirmatory four-family ranker panel. Three fresh workers each compose the graph-authored self-correction rank Program, fault `hop_descend_gradient` by flipping its comparison, and obtain candidates from the unchanged `_default_candidates` generator. Training cases are Up and Left; held-out cases are Down and Right. The train/evaluation split is fixed before capture. All candidate edits are scored by the independent native navigation behavior oracle, which is outside `rank_candidates`.

Each worker compares three policies on the same candidate set and held-out states:

1. unchanged candidate-generator order;
2. the graph-authored rank Program with zero outcome history;
3. the same graph-authored Program with typed `CorrectionOutcome` records produced from the candidate executions on the two training directions.

For every policy, record the complete emitted candidate order before evaluating candidates on held-out states. Candidate attempts stop at the first candidate passing both held-out states. Record first-candidate utility, held-out successes, attempts, per-candidate training outcomes, rank traces, and ordering time. Every candidate is also scored on both held-out cases after the primary stopping rule to preserve the full utility table; these oracle results are not returned to the ranker.

## Integrity and limits

Lock the runner, this protocol, referenced navigation runner/protocol, ranker implementation, candidate generator, composer seed, navigation seed, relevant Python/native source fingerprints, and loaded native binary before capture. Require three workers, exact source-lock parity, successful composition of the actual `self_correct_rank_*` Program, and disjoint training/held-out state identifiers. Preserve all outcomes, including failed candidates.

The candidate set is host-enumerated and the outcome rows are transferred by the evaluation harness. This measures outcome use by an existing graph-authored rank Program on one controlled family. It cannot establish autonomous experience collection, broad cross-family transfer, autonomous candidate generation, or general self-improvement. Even a positive held-out result is only a prerequisite for the four-family utility panel.
