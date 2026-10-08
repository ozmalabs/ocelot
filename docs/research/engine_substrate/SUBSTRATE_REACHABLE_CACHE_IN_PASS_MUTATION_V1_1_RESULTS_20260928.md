# ReachableFrom in-pass mutation probe v1.1 results

After the v1 counterexample, `attempt_one_rule` now clears graph-dependent evaluation state immediately after any progressing rule attempt. This ensures later rules in the same pass do not read a cache computed before that rule's graph effects.

The five-worker source-locked v1.1 replay passes every runner gate and all six independent analysis checks. Both cache modes derive the expected detection edge, return two progress steps, and produce byte-identical final graphs. The rule access sets retain the path edge as both the mutator's write and the later consumer's read. This verifies the repair on the falsifying workload only; it does not prove every internal mutation route or dynamic Term dependency correct.

The public mutation matrix was rerun against this engine and all ten cases still pass. The earlier quiet/audit profile was also rerun: at N=128, the quiet medians remain 12.34× faster for B=1 and 7.10× for B=4, with exact semantic and audit parity. See [v1.2 profile results](SUBSTRATE_BROWSER_PROFILE_REACHABLE_CACHE_V1_2_RESULTS_20260928.md).

Artifacts: [preregistration](SUBSTRATE_REACHABLE_CACHE_IN_PASS_MUTATION_V1_1_PREREG_20260928.md), [raw run](../../../evaluation/reports/substrate_reachable_cache_in_pass_mutation_v1_1_20260928.json), [independent analysis](../../../evaluation/reports/substrate_reachable_cache_in_pass_mutation_v1_1_analysis_20260928.json), [runner](../../../scripts/substrate_reachable_cache_in_pass_mutation_v1_1.py), [analyzer](../../../scripts/analyze_substrate_reachable_cache_in_pass_mutation_v1_1.py), [implementation](../../../runners/dsl/src/substrate.rs).
