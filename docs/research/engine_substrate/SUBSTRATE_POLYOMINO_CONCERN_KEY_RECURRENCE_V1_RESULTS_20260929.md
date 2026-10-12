# Polyomino concern-key recurrence and collision v1 results

**Run:** 2026-09-29. **Status:** all locked-input and structural-integrity checks pass; 15 fresh-graph sequences, 30 total calls through `reflective_faculty.induce_concern`.

## Outcome

Every one of the 15 sequences has the same pattern: the first seven-cell observation is `minted` and adds one `CapabilityAxis`; the second is `recognized_duplicate` and adds no axis. This occurs in all five exact-repeat controls and all ten ordered distinct-shape cases. The exact-repeat control therefore verifies recurrence suppression. The distinct-shape cases reveal a key collision: all five seven-cell signatures contain seven `cell` predicates, and `induce_concern` derives the same key, `induced_cell_cell_cell_cell_cell_cell_cell`, from each. The five target shapes have distinct exact signatures and five distinct dihedral orbits, yet every second distinct target is classified as a duplicate of the first when they share a graph.

The rule-level outcome is clear: mint deduplication uses `capability_keys` equality without comparing the full residual geometry. `recognized_duplicate` is correct for exact recurrence but also suppresses these held-out geometrically distinct structures. This is evidence of a representational collision in the current concern identity on this shape family. Whether a predicate-multiset axis is intended to denote a broad concern class or an individual structural concept is a design question; under any caller that expects shape-specific acquisition, the behavior loses distinctions. The captured second-call readback resolves to the existing axis by key, while that axis retains the repeated predicate heads rather than the second target's coordinate structure.

| Sequence class | Sequences | First call | Second call | Axis delta |
|---|---:|---|---|---|
| Exact same shape repeated | 5 | `minted` | `recognized_duplicate` | 1 then 0 |
| Different shape, same seven-cell predicate key | 10 | `minted` | `recognized_duplicate` | 1 then 0 |

There was no order effect in the ten directed adjacent-pair comparisons: reversing each pair produces the same first-mint/second-duplicate pattern. The worker completed in 2.22 seconds wall time on this host. These timings cover only this tiny seed/graph workload and are descriptive.

## Boundaries and next gate

This is a deterministic five-shape diagnostic, not an estimate of collision prevalence over general task inputs. It measures the `induce_concern` native rule path with no codebook growth between calls. It does not test downstream use of the returned axis, changes to key design, noise distributions, or broad concept-learning quality. Next compare the current key against a structure-preserving key derived from canonicalized residual signatures. Hold fixed the same exact-repeat and cross-shape pairs; measure exact duplicate suppression, distinct-structure separation, key cost, axis count, downstream recognition, and persistence. Keep the current rule unchanged until that comparison is preregistered and its compatibility surface is mapped.

Artifacts: [preregistration](SUBSTRATE_POLYOMINO_CONCERN_KEY_RECURRENCE_V1_PREREG_20260929.md), [runner](../../../evaluation/substrate_capability/polyomino_concern_key_recurrence_v1.py), [analyzer](../../../evaluation/substrate_capability/analyze_polyomino_concern_key_recurrence_v1.py), [lock](../../../evaluation/substrate_capability/polyomino_concern_key_recurrence_v1_lock_20260929.json), [raw capture](../../../evaluation/reports/polyomino_concern_key_recurrence_v1/capture.json), [independent analysis](../../../evaluation/reports/polyomino_concern_key_recurrence_v1/analysis.json).
