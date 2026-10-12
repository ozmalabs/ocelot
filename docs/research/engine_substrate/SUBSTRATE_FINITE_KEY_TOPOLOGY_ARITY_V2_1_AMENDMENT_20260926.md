# Finite-key topology/arity v2.1 analysis amendment

Date: 2026-09-26

## Scope

This is an analysis-only correction to the source-locked v2 capture. It does not change the runner, raw observations, engine, or locked measurement inputs, and no measurement cases were rerun.

The initial independent analyzer compared tuple-valued node labels against the capture's list-valued graph projection. That representation mismatch falsely rejected otherwise identical projected graphs. The initial analysis file is retained as `mint_termination_topology_arity_v2_analysis_20260926.json`. The corrected, separately versioned analyzer converts oracle edge endpoints to the capture's normalized list representation and independently checks all plain and audit arms against the exact oracle.

## Corrected result

The v2.1 analyzer passes all nine checks: balanced design (171 cells), exact terminal graph/status/bound oracle, recorded candidate counters, finite costs, randomized arm order, stable lock, successful current-engine manifest, captured-log hash, and native binary hash. Its SHA-256 is included in `mint_termination_topology_arity_v2_1_analysis_20260926.json`.

This correction changes only the analyzer's representation comparison. The raw v2 measurement capture and its provenance remain unchanged. See [v2.1 results](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_1_RESULTS_20260926.md), [protocol](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_PROTOCOL_20260926.md), and [analysis](../../../evaluation/reports/mint_termination_topology_arity_v2_1_analysis_20260926.json).
