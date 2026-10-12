# Cross-family adequacy-gated adoption boundary v2 — preregistration

## Question

Does the narrow authenticated `_teach_shape` graph-delta contract replicate across three independently specified code-write tasks with distinct input arities and Term structures?

## Design

Run three fresh workers for each of parity, clamp, and square (nine workers total). Reuse the existing source-hashed independent code-write oracle and fixtures. In each worker, construct a candidate-bound one-probe request on a fresh input, create a signed false label and a signed truthful label from the independent oracle, then submit the false receipt followed by the truthful receipt through `teach_write_shape_from_example_authenticated`. Instrument `_teach_shape` to capture complete canonical graph state immediately before and after adoption. Evaluate the accepted Term against the task's held-out set using both the native engine and the independent oracle.

## Gates

Require the full 3×3 task/repetition grid in unique fresh PIDs and stable source/native/seed/oracle hashes. Independently recompute the correct/false labels, receipts and signatures. False evidence must be rejected without entering `_teach_shape` or changing the code-write shape inventory/epoch. Truthful evidence must be accepted, add exactly one code-write `ShapeSignature` and one pending `ShapeObservation`, update only the Agent adoption metadata, remove no nodes/edges, and add no edges. All native held-out predictions must match the independent oracle. Keep per-task adoption-boundary timing descriptive; this is not a full-conversation latency study.

## Limits

Three authored task families, one host, one deterministic provider key, and three repetitions per task. This tests transfer of the transaction invariant across these fixtures. It does not establish natural task coverage, label truth from authentication, autonomous candidate generation, or all-caller graph-mutation safety.

## Reproduction

```sh
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2.py --lock
.venv/bin/python evaluation/substrate_capability/substrate_adequacy_adoption_boundary_v2.py
.venv/bin/python evaluation/substrate_capability/analyze_substrate_adequacy_adoption_boundary_v2.py
```
