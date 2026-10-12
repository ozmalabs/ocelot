# Productive CAN join-order validation v2 results

Date: 2026-10-01  
Protocol: [preregistration](CAN_PRODUCTIVE_JOIN_ORDER_V2_PREREG_20261001.md)  
Runner: [source-locked panel](../../../evaluation/substrate_capability/can_productive_join_order_v2.py)  
Analyzer: [independent gates](../../../scripts/analyze_can_productive_join_order_v2.py)  
Capture: [45-worker raw data](../../../evaluation/reports/can_productive_join_order_v2_workers_20261001.json)  
Analysis: [summary and per-cell medians](../../../evaluation/reports/can_productive_join_order_v2_analysis_20261001.json)  
Input lock: [source/native lock](../../../evaluation/substrate_capability/can_productive_join_order_v2_lock_20261001.json)

## Result

All **10/10 gates pass** across 45 fresh worker processes: 15 N×Q cells with three replicates each. The panel compares the ordinary install-time heuristic (the original authored rule list installs as `has_concept(a), has_concept(b), coactivation_of(coact,b), coactivated_with(a,coact)` on an empty graph), sparse-first, and the exact minimum-work sequence found by exhaustive prefix enumeration: `has_concept(a), coactivated_with(a,coact), coactivation_of(coact,b), has_concept(b)`.

The exact sequence could not be expressed by merely permuting authored clauses: the default tie path removes selected edges from the remaining vector by swapping with its last item. The panel therefore uses the new opt-in `add_rule_preserving_match_order` path for the measured-best arm. Default installation still uses the existing automatic reorder unchanged. The opt-in API is limited to explicit ordering control; this result does not evaluate a production selector that discovers the best order.

All three arms use the real production CAN mint/reweight rules, including their original `where` guards and effects. Every seeded coactivation pair reached the expected evidence state and causal link; node/edge bounds held; each run terminated below the step cap and the extra closure probe made no progress. Canonical graph facts matched among all three orders. Audited and uninstrumented runs matched, and per-rule candidate counts reconciled with global counters. Source and native-extension fingerprints remained stable throughout.

| N | Q | Default install | Sparse-first | Measured best | Best reduction vs default | Best reduction vs sparse |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 0 | 2,112 | 0 | 64 | 97.0% | — |
| 32 | 32 | 10,800 | 2,944 | 2,896 | 73.2% | 1.6% |
| 32 | 128 | 61,056 | 11,776 | 11,200 | 81.7% | 4.9% |
| 32 | 248 | 188,272 | 22,816 | 21,580 | 88.5% | 5.4% |
| 32 | 992 | 2,574,000 | 91,264 | 85,936 | 96.7% | 5.8% |
| 64 | 0 | 8,320 | 0 | 128 | 98.5% | — |
| 64 | 64 | 43,104 | 11,008 | 10,912 | 74.7% | 0.9% |
| 64 | 256 | 244,992 | 44,032 | 42,880 | 82.5% | 2.6% |
| 64 | 1,008 | 2,804,896 | 173,376 | 168,088 | 94.0% | 3.1% |
| 64 | 4,032 | 41,556,320 | 693,504 | 671,584 | 98.4% | 3.2% |
| 128 | 0 | 33,024 | 0 | 256 | 99.2% | — |
| 128 | 128 | 172,224 | 42,496 | 42,304 | 75.4% | 0.5% |
| 128 | 512 | 981,504 | 169,984 | 167,680 | 82.9% | 1.4% |
| 128 | 4,064 | 43,364,416 | 1,349,248 | 1,327,408 | 96.9% | 1.6% |
| 128 | 16,256 | 667,968,192 | 5,396,992 | 5,308,096 | 99.2% | 1.6% |

Candidate work is the stable effect. At the largest cell, audited closure medians were 40.58 s default, 1.71 s sparse-first, and 1.57 s measured-best; wall time is noisier and instrumentation-heavy. Across the population cells, best-order median candidate work is consistently lower than sparse-first when Q>0, but the incremental reduction is modest compared with the major gain from moving coactivation relations earlier. For Q=0, sparse-first immediately proves no match and performs zero candidates; the measured-best sequence also prunes early but still scans the initial concept-membership clause.

## Interpretation and limits

This confirms that the offline minimum-work sequence preserves the productive semantics of this CAN rule family under its actual guards and effects. It refines the earlier read-only result: after a selective population clause binds the concept, joining the two coactivation relations before checking the second population membership reduces the remaining prefix work. The large structural gain comes from avoiding the default's early Cartesian pairing of concept memberships; the measured-best sequence improves further over sparse-first by a small amount.

This is not evidence for an online or general join-order optimizer. The best sequence was identified by exhaustive comparison on the bounded four-clause pattern, then supplied explicitly. The data use a synthetic cyclic pair ledger, fixed concept states, and half of pairs pre-seeded for reweighting, on one host and finite sizes. Natural CAN workloads, alternate rule families, selector overhead, memory behavior, and scaling beyond N=128 remain unmeasured. The order-preserving API provides an experimental control, not a claim that new orders should become the default.

## Next measurement

Use the exact-order control on at least one independent productive rule family and an alternate topology. Then prototype a prefix-cost selector behind the existing default behavior and measure selector-statistics overhead, order quality, semantic parity, and productive closure work on held-out patterns. Keep the current heuristic as the control arm.
