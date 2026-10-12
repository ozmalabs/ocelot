# Native query-eligibility scaling v3 preregistration

## Question

Does replacing neighbor enumeration with direct exact edge membership for fully bound match clauses improve eligibility scaling while preserving the v1 workload's eligible set and selected-node result?

## Design

Repeat the v1 graph-level population panel with the same five sizes (512, 1,024, 2,048, 4,096, 8,192), five replicates, and deterministic seeds. The only engine source change since the v1 baseline is in `rewrite::extend_each`: for a match clause whose source and target are both bound, use `TypedGraph::has_edge` to yield the singleton match or empty set. Measure graph build, eligibility closure, and `ArgminUnique` selection separately. Reconstruct expected positive IDs, eligible identity digest, and selected rank independently.

The v1 capture is the before-change baseline. Because builds and captures occur at different times, report paired-seed ratios descriptively and include each run's engine fingerprint, native artifact hash, timings, and memory. Do not characterize these as counterbalanced same-session timings or fit an asymptotic complexity class.

## Gates

Require 25 current-source workers, exact positive/eligible set parity, exact selected identity/rank parity, source stability, five replicates per size, and independent oracle replay. Report the relative v1/v3 eligibility and selector medians by size. A correctness pass with no cost reduction is not an optimization success. Follow any scale improvement with the full native adequacy/query task panel.

## Limits

This measures one synthetic graph-level rule workload and one generic matcher branch. It does not establish natural-task applicability, broad semantic equivalence for all matcher uses, or end-to-end speedup. General matcher correctness should receive dedicated review and broader existing differential coverage before release.

## Reproduction

Run `python3 evaluation/substrate_capability/native_query_eligibility_scale_v3.py --lock`, then `--run`, followed by `python3 evaluation/substrate_capability/analyze_native_query_eligibility_scale_v3.py`.

