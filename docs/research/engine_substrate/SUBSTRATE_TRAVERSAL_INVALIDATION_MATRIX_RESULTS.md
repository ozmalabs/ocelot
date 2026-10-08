# Traversal-term invalidation matrix

**Status:** exploratory native runtime matrix; one insertion case per term family.

## Method

Each case uses two rules and a stable `trigger` binding. The reader computes a value from a graph-traversal term and writes it to the target's `observed_value`; the writer inserts a typed `causal` edge. The run checks both the reader's final value against an independently computed answer from `graph_to_dict()` and a separate terminal no-work probe. The matrix executes against the same rebuilt native extension used by the closure controls.

## Results

| Read term | Derived term-edge resource | `reads_any` | Reader value | Direct graph oracle | Settled |
|---|---|---:|---:|---:|---|
| `Edges` typed | `edge:causal` | false | 1 | 1 | Yes |
| `Neighbours` typed | `edge:causal` | false | 1 | 1 | Yes |
| `InNeighbours` typed | `edge:causal` | false | 1 | 1 | Yes |
| `ReachableFrom` typed | `edge:causal` | false | 1 | 1 | Yes |
| `MapNeighbours` typed | `edge:causal` | false | 1 | 1 | Yes |
| `Edges` any-type | none; conservative wildcard | true | 2 | 2 | Yes |
| `Sum(Edges, EdgeAttr)` | `edge:causal` plus conservative wildcard | true | 1 | 1 | Yes |

All seven cases made three progressing rule steps and then passed the terminal probe with zero progress. The any-type edge query and edge-attribute read correctly use `reads_any`; typed traversal terms carry the `edge:causal` dependency. Raw output, source hashes, and the native extension hash are in [`substrate_traversal_invalidation_matrix_20260924.json`](../../../evaluation/reports/substrate_traversal_invalidation_matrix_20260924.json); reproduce with [`substrate_traversal_invalidation_matrix.py`](../../../scripts/substrate_traversal_invalidation_matrix.py).

## Limits and next gate

This validates output refresh after one typed edge insertion per term family in the default runner. It does not cover deletion for every term, dynamic or indirect term access beyond these examples, external graph mutation, parallel scheduling, or representative task workloads. Continue with mutation and cursor-mode coverage, then measure task-level behavior and update cost. These results do not prove complete runtime access tracing or frame factorisation.
