# Declared scope-anchor matcher v2.0.1 results

Date: 2026-10-03  
Protocol: [v2.0 preregistration and amendments](SUBSTRATE_CONVERSATION_TASK_SCOPE_DECLARED_ANCHOR_V2_PREREG_20261003.md)  
Runner: [conversation_task_scope_anchor_pilot_v2_0.py](../../../evaluation/substrate_capability/conversation_task_scope_anchor_pilot_v2_0.py)  
Analyzer: [independent analysis script](../../../evaluation/substrate_capability/analyze_conversation_task_scope_anchor_pilot_v2_0.py)  
Source lock: [v2.0.1 lock](../../../evaluation/substrate_capability/conversation_task_scope_anchor_pilot_v2_0_1_lock_20261003.json)  
Capture: [v2.0.1 capture](../../../evaluation/reports/conversation_task_scope_anchor_pilot_v2_0_1_20261003.json)  
Analysis: [v2.0.1 analysis](../../../evaluation/reports/conversation_task_scope_anchor_pilot_v2_0_1_analysis_20261003.json)

## Result

The independent analyzer passes all validity and semantic gates across 54 paired cases and 738 checkpoints. All 54 anchor-arm final states match the full-fallback arm; checkpoint graphs, goal lifecycle states, and trace-on/off states match exactly. Nine fresh worker processes cover three scope sweep orders, three replicates, four aligned workloads, and cross-frame plus orphan-owner controls. The declared-anchor path is exercised on every aligned case. Unsafe ownership controls trigger proof-guard rejections, and the access trace is nonempty with no dropped rows.

The performance hypothesis fails. The fallback and declared-anchor arms each enumerate 81,228 Candidate pairs and evaluate 313,842 Terms. Both therefore perform 4.02× the monolithic Candidate work and 5.34× its Term work on this partitioned panel; measured work reduction is zero for both counters. The anchor fast path has 18,378 match attempts, with 19,854 proof rejections followed by full fallback. These counters show correct conservative routing, but no aggregate work advantage. Wall-clock values are secondary diagnostics and do not override the failed work-reduction gate.

The result is a semantic and guard-validation result, not an optimization success. It establishes that the metadata path can run with exact state parity on these authored task graphs and that the runtime rejects the tested unsafe ownership arrangements. It does not establish a general proof for arbitrary rules, natural-task prevalence, lower latency, asymptotic factorization, or general tractability. The earlier v2.0 capture remains preserved as a failed implementation attempt: it passed parity but rejected the anchor path on aligned cases. The v2.0.1 source correction now handles the owned Microtheory root and anchor-adjacent Event roles under explicit runtime checks.

## Correction — fallback arm was not isolated

After this report was written, source inspection showed that the runner patched `substrate.seed_loader.manifest_for` but `substrate.boot_core` retained a module-level import of the original function. The arm labelled `partition_fallback` therefore also loaded anchor metadata. Reclassify the reported parity and guard observations as evidence for the anchor-enabled path, and withdraw the claimed anchor-versus-fallback comparison and conclusion that their work counts tied. The v2.0.2 semantic-edge accounting remains a valid account of work in those two anchor-enabled arms but is not evidence about generic fallback. A corrected, explicitly isolated comparison passes in [v2.1.1 selectivity results](SUBSTRATE_CONVERSATION_TASK_SCOPE_SELECTIVITY_V2_1_RESULTS_20261003.md).

## Next work

Do not adopt this anchor matcher as a performance improvement. First attribute Candidate and Term work by actual match clause, edge candidate source, and scope invocation, and compare that instrumentation with the anchor-first reorder. If the current counters are already invariant to clause ordering for this rule shape, change the matcher to avoid repeated full candidate expansion rather than merely reorder it. Keep the passing parity/guard panel as a regression gate, and require a new source-locked confirmatory capture with both Candidate and Term reductions before claiming optimization. Continue broader capability work independently: this one authored workload cannot validate the cheap-cut prevalence hypothesis or the general learning regime.
