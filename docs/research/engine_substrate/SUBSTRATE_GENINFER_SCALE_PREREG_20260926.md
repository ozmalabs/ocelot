# GenInfer 2-D exhaustive-search scaling preregistration

**Lock date:** 2026-09-26, before the scale capture  
**Target:** current-source `GenInfer` matrix enumeration in `shape_decode.rs`  
**Experiment type:** diagnostic algorithmic scaling, not a natural-task benchmark

## Question

How do measured direct `GenInfer` call times change as its own data-derived bound grows, when the same held shape and exact integer-linear transform family are retained? The evaluator enumerates every non-identity 2×2 integer matrix with entries in `[-B,B]`; the predicted candidate count is `(2B+1)^4 - 1`.

## Frozen fixture and schedule

- Held signature: four-cell L with coordinate slots 1 and 2, fixed predicate/value fields, and `dim_types = [pred, coord:r, coord:c, val]`.
- Targets: the held signature transformed by `[2s,s,s,s]` for `s ∈ {1,2,3}`. Expected bounds are `B ∈ {4,8,12}` and exact matrices `[2s,s,s,s]`.
- Schedule: one untimed `B=4` warm-up, then five measured repetitions per scale in ascending order within each repetition (`B=4,8,12`). No graph, code, or target changes between repeated calls within an instance.
- Timed operation: one `_native` `GenInfer` evaluation returning the matrix field. A separate untimed evaluation returns `checked` once per bound. Timing excludes process/import/graph-construction startup and the `checked`-field read.
- Scales are single-process, single-worker calls on one immutable substrate graph. Candidate count is a deterministic algorithmic work proxy; wall time is descriptive for this machine and process only.

## Locked checks and analysis

The runner must produce all 15 timed calls, the correct matrix on every call, and the exact count formula at each bound. The analyzer independently verifies the sample count, outcomes, source/native hashes, and count formula. It reports per-bound median/min/max latency, median candidate throughput, and B=8/B=4 and B=12/B=4 median ratios. It has no performance pass threshold: any timing shape is reportable and cannot fail semantic validity. There is no fitted asymptotic claim from three points.

## Claim boundary

This sweep can establish the realized candidate-count curve and local CPU time for one four-relation positive instance of the 2-D linear inducer. It cannot establish cost on other shapes, noisy or negative examples, higher dimensions (which are skipped), full closure cost, scaling beyond B=12, natural-task prevalence, memory, or general learning tractability. In particular, the `B^4` candidate count says nothing by itself about cost per candidate or workload distribution.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_scale_probe_v1.py
python3 scripts/analyze_substrate_geninfer_scale_probe_v1.py
```
