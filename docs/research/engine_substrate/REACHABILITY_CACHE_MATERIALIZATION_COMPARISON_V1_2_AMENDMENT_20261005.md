# Reachability cache/materialization comparison v1.2 amendment

V1.1's independent analysis exposed that the runner still recorded expected reader matches as N×R, although the `query_source` relation targets vertex 0 and the matcher enforces injective bindings. The `x=vertex0, q=vertex0` self-binding is correctly omitted, so the expected count is (N−1)×R. This is a runner expectation defect; the v1.1 raw capture and failed analysis are preserved.

V1.2 changes only this expected reader-match count. It retains the three arms, graph generators, timings, repetitions, order schedule, semantic checks, and analyzer checks. A fresh runner/analyzer/protocol fingerprint and new capture ensure the corrected artifact is independently auditable. No timing outcomes from v1 or v1.1 are used to alter the design.

Reproduction: run `python3 evaluation/substrate_capability/reachability_cache_materialization_comparison_v1_2.py --lock`, run it without arguments, then run `python3 evaluation/substrate_capability/analyze_reachability_cache_materialization_comparison_v1_2.py`.
