# Productive CAN topology sensitivity v1.1 results

Date: 2026-10-01  
Protocol amendment: [v1.1 schedule correction](CAN_PRODUCTIVE_JOIN_TOPOLOGY_V1_1_AMENDMENT_20261001.md)  
Original protocol: [v1 preregistration](CAN_PRODUCTIVE_JOIN_TOPOLOGY_V1_PREREG_20261001.md)  
Runner: [source-locked panel](../../../evaluation/substrate_capability/can_productive_join_topology_v1_1.py)  
Analyzer: [independent gates](../../../scripts/analyze_can_productive_join_topology_v1_1.py)  
Capture: [54-worker raw data](../../../evaluation/reports/can_productive_join_topology_v1_1_workers_20261001.json)  
Analysis: [summary and per-cell medians](../../../evaluation/reports/can_productive_join_topology_v1_1_analysis_20261001.json)  
Input lock: [source/native lock](../../../evaluation/substrate_capability/can_productive_join_topology_v1_1_lock_20261001.json)

## Result

The corrected 54-worker replay passes **12/12 gates**. It covers three pair layouts × two sizes × three population levels × three fresh-process replicates. The first v1 run used the same 54-cell design but its preregistration and analyzer mistakenly said 36. Its source, productive outcomes, parity, ordering, and counter checks passed; the two worker-count checks failed. That raw capture and failed analysis are retained under the v1 filenames as pilot evidence. V1.1 changes only the schedule count, uses distinct artifact names, refreshes the source lock, and reruns the full panel.

| Layout | N | Q | Default install | Sparse-first | Measured best | Best reduction vs default | Best reduction vs sparse |
|---|---:|---:|---:|---:|---:|---:|---:|
| cyclic | 32 | 32 | 10,800 | 2,944 | 2,896 | 73.2% | 1.6% |
| cyclic | 32 | 128 | 61,056 | 11,776 | 11,200 | 81.7% | 4.9% |
| cyclic | 32 | 248 | 188,272 | 22,816 | 21,580 | 88.5% | 5.4% |
| cyclic | 64 | 64 | 43,104 | 11,008 | 10,912 | 74.7% | 0.9% |
| cyclic | 64 | 256 | 244,992 | 44,032 | 42,880 | 82.5% | 2.6% |
| cyclic | 64 | 1,008 | 2,804,896 | 173,376 | 168,088 | 94.0% | 3.1% |
| hub | 32 | 32 | 10,560 | 2,944 | 2,896 | 72.6% | 1.6% |
| hub | 32 | 128 | 60,248 | 11,776 | 11,200 | 81.4% | 4.9% |
| hub | 32 | 248 | 187,623 | 22,816 | 21,580 | 88.5% | 5.4% |
| hub | 64 | 64 | 42,112 | 11,008 | 10,912 | 74.1% | 0.9% |
| hub | 64 | 256 | 241,336 | 44,032 | 42,880 | 82.2% | 2.6% |
| hub | 64 | 1,008 | 2,802,255 | 173,376 | 168,088 | 94.0% | 3.1% |
| clustered | 32 | 32 | 10,741 | 2,944 | 2,896 | 73.0% | 1.6% |
| clustered | 32 | 128 | 61,007 | 11,776 | 11,200 | 81.6% | 4.9% |
| clustered | 32 | 248 | 188,316 | 22,816 | 21,580 | 88.5% | 5.4% |
| clustered | 64 | 64 | 42,933 | 11,008 | 10,912 | 74.6% | 0.9% |
| clustered | 64 | 256 | 244,656 | 44,032 | 42,880 | 82.5% | 2.6% |
| clustered | 64 | 1,008 | 2,805,043 | 173,376 | 168,088 | 94.0% | 3.1% |

All order arms use identical pair inputs within a cell. The pair-sequence hashes differ across the three layouts in each matched N/Q/repetition cell. Real CAN `where` clauses and effects run in every arm; per-pair causal/evidence results satisfy the oracle; each arm reaches a terminal fixed point; canonical graph outcomes agree across matcher orders; instrumented and plain outcomes agree; and per-rule candidate counters sum to global counts.

## Interpretation

The benefit is stable across these constructed topologies. Sparse-first and measured-best work is nearly invariant to layout at matched N/Q, while default-order work shifts modestly with topology. Measured-best beats sparse-first by 0.9–5.4% for this subset of Q>0 cells, and cuts work by 72.6–94.0% against default installation. The major reduction comes from avoiding the early concept-pair product; the exact best sequence contributes a smaller additional gain.

This increases confidence that the order result is not an artifact of one cyclic pair ledger. It remains evidence about one CAN rule family and three deterministic synthetic pair layouts. It does not show natural topology frequencies, a learned or automatic order selector, another production rule family, or general average-case tractability. Further work should test an independent productive family, then measure the selector on held-out patterns and include its estimation overhead.
