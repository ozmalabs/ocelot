# Native query-eligibility join-order comparison v2 preregistration

## Question

Does binding the relation vote and its example before checking episode probe membership reduce eligibility closure cost while preserving exactly the same eligible set and selected query as the v1.3 match order?

## Design

Compare two native rule match orders on paired deterministic graphs at 512, 1,024, 2,048, 4,096, and 8,192 probe examples, with five seeds at each size. `probe_first` retains the v1.3 order: episode selected-family, episode has-probe-example, family has-vote, vote-to-example. `vote_first` uses: episode selected-family, family has-vote, vote-to-example, episode has-probe-example. The where condition, effects, node attributes, prediction distribution, rank distribution, and selector are identical. Each arm runs in a fresh process with its paired seed.

Measure graph build, eligibility closure, and selector closure separately. Require exact eligible-set digest and selected ordinal/rank parity with the independent host oracle, and require pairwise parity between arms. Report per-size medians/p90 and paired ratios. Do not infer an asymptotic class from these points.

## Gates and limits

Require 50 source-locked successful workers, five paired seeds per size, stable source fingerprints, exact host and cross-arm output parity, and finite timings. This is a graph-level synthetic join-order experiment derived from one authored route. It establishes an optimization candidate only; any change must next pass the full v1.3 task workload and broader task families. It does not establish natural-task prevalence, end-to-end application speedup, or frame locality.

## Reproduction

Create the immutable panels and source lock with `python3 evaluation/substrate_capability/native_query_eligibility_scale_v2.py --lock`, run with `--run`, and analyze with `python3 evaluation/substrate_capability/analyze_native_query_eligibility_scale_v2.py`.

