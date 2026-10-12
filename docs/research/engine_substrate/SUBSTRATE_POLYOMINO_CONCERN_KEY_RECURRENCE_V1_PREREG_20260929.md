# Polyomino concern-key recurrence and collision v1 preregistration

**Date:** 2026-09-29. **Question:** when several structurally different uncovered cell signatures have the same predicate-derived `capability_keys`, does the graph-native mint loop suppress later distinct structures as duplicates? How does that compare with replaying the same structure twice?

## Rationale

`reflective_faculty.induce_concern` derives an Observation key from the sorted predicate heads in its signature. `sd_mint_quantum` admits a mint only when no induced `CapabilityAxis` already has matching `capability_keys`; `sd_dedup_existing` marks a blocked residual `recognized_duplicate`. The previous negative-control audit created one axis per distinct shape in a fresh graph, so it did not exercise recurrence or collisions in a shared graph. This experiment uses the public `induce_concern` path in one graph per sequence.

## Frozen cases

Use five held-out six-cell shapes `H06_A` through `H06_E` and create each control by appending the same deterministic extra adjacent cell as v1: one row below the maximum row, in the minimum occupied column on that bottom row. Every target contains seven `cell` relations, so the normal predicate-derived key must be identical across all five controls. An independent coordinate-set check must confirm that all five targets are distinct and that same-shape repeats are exactly equal.

Run 15 fresh-graph sequences, each with exactly two sequential `induce_concern` calls and no Python codebook growth between calls:

- Five exact-repeat controls: `H06_A→H06_A`, `H06_B→H06_B`, `H06_C→H06_C`, `H06_D→H06_D`, `H06_E→H06_E`.
- Ten ordered distinct-shape cases: both directions for adjacent pairs in the frozen ring `A-B-C-D-E-A`.

For each sequence, add only its first shape as the held `ShapeSignature`, then present the two seven-cell targets. Record each call's derived capability key, terminal Observation status, mint/dedup/transform edges, before/after axis count and IDs, codebook epoch, native settlement steps, and elapsed wall/CPU time. Each sequence starts from a fresh boot. No trial is excluded based on outcome.

## Outcomes and gates

1. All 15 sequences execute two observations and reach a terminal status.
2. Each target has seven `cell` predicates; all five derived keys are equal.
3. Same-shape control targets are equal; each ordered distinct-shape pair has unequal exact signatures.
4. Report first-call and second-call status, axis deltas, and order effects separately for repeat and distinct-shape sequences. Do not interpret `recognized_duplicate` as semantic equivalence without an independent exact-signature check.
5. Preserve all raw graph-level outcomes and worker costs. A passing integrity gate does not establish that predicate-only keys are a desirable identity for all applications.

## Lock and execution

Lock the protocol, runner, current native source/binary/build record, engine/adapter sources, seed manifest, and fixed case definitions. Require identical pre- and post-run locks. Run with:

```sh
python3 evaluation/substrate_capability/polyomino_concern_key_recurrence_v1.py --lock
python3 evaluation/substrate_capability/polyomino_concern_key_recurrence_v1.py
python3 evaluation/substrate_capability/analyze_polyomino_concern_key_recurrence_v1.py
```

The result is limited to repeated and same-predicate-count six-cell polyomino observations on this graph-native concern path. It does not establish collision prevalence in natural tasks or general memory economics.
