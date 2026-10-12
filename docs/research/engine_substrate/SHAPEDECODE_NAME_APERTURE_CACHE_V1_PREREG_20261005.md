# ShapeDecode name-aperture cache v1 — preregistration

**Question:** Does an EvalCtx-local parsed-codebook cache remove repeated full-population scans from the candidate-at-a-time ShapeDecode route without changing outputs?

## Design

The implementation stores a fully validated codebook once per immutable `EvalCtx`, plus an insertion-order vector index by `Part.name.to_lowercase()`. Every subsequent singleton/multi-name aperture selects matching parts by folded-name positions, merges positions in original order, and deduplicates indices. The graph is immutably borrowed for the entire EvalCtx lifetime, so the cache cannot outlive the graph view. A fresh-process switch selects the original scan path or the cache path against the identical current source and fixture.

Use the v1 cross-frame identity workload and 16 target parts plus 0/16/48/112 distractors (effective populations 33/49/81/145, including 17 boot parts). Run five fresh-process replicates per population, scan/cache mode, and traced/untraced condition (80 workers total). Paired arms use identical per-replicate target tiles, candidate insertion order, and graph construction. Shuffle the locked case schedule with seed 20261005.

## Measurements and gates

Require source/build lock stability, unique process per case, exact graph-produced winner/readback parity, identical coarse closure work, traced/untraced parity, and zero dropped trace events. Report ShapeDecode calls, codebook population visits, parts parsed, cache hits/misses, candidate work, untraced closure wall/CPU distributions, and RSS. Compare scan-arm trace counts with the v1 baseline to confirm the switch retains the existing path. Do not claim an end-to-end speedup unless paired untraced timing improves after construction and cache costs are included.

The optimization is local to one immutable term evaluation and does not create graph state or persist across mutations. This panel does not establish natural-task prevalence, standalone query-index lifecycle, or general tractability. Case-folding, exact duplicate overwrite, mixed-case duplicate inclusion, `Str`/`Surface(Text)`, empty/absent scopes, malformed out-of-scope records, and output ordering remain semantic controls for the implementation audit; any discrepancy blocks promotion even if the cross-frame fixture passes.

## Amendment v1.1 — analyzer input correction

The first 80-worker capture completed, but its independent analyzer pointed at the raw baseline capture instead of the baseline analysis summary and stopped before producing an analysis. The first lock and capture are retained as attempt 1. This amendment corrects only the baseline-analysis input path; the workload, implementation, cases, and acceptance criteria are unchanged. A new source lock and full 80-worker capture are required because the analyzer is part of the locked source closure.
