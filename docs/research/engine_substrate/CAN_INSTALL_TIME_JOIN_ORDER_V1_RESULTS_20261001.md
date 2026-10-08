# CAN install-time join-order policy v1 results

Date: 2026-10-01  
Status: complete; all 9 analyzer gates pass.

## Result

The panel ran 45 new fresh workers across the same 15 N×Q cells as productive closure v1. It loaded the CAN graph before importing the two target rules, so `Substrate::add_rule`'s cardinality-based ordering saw the measured data. An independent implementation of the source ordering algorithm predicted all 180 installed rule orders. Every arm passed the productive per-pair oracle and exact graph-growth bound, reached a terminal fixed point, reconciled candidate counters, and matched the corresponding graph-first arm from the locked earlier capture.

| N | Q | First clause, authored input | First clause, sparse input | Graph-first authored tests | Graph-first sparse-authored tests | Empty-graph sparse-first reference tests | Graph-first sparse / reference |
|---:|---:|---|---|---:|---:|---:|---:|
| 32 | 0 | coactivated_with | coactivated_with | 0 | 0 | 0 | — |
| 32 | 32 | has_concept | coactivated_with | 10,800 | 2,944 | 2,944 | 1.00× |
| 32 | 128 | has_concept | has_concept | 61,056 | 30,528 | 11,776 | 2.59× |
| 32 | 248 | has_concept | has_concept | 188,272 | 55,188 | 22,816 | 2.42× |
| 32 | 992 | has_concept | has_concept | 2,574,000 | 208,080 | 91,264 | 2.28× |
| 64 | 0 | coactivated_with | coactivated_with | 0 | 0 | 0 | — |
| 64 | 64 | has_concept | coactivated_with | 43,104 | 11,008 | 11,008 | 1.00× |
| 64 | 256 | has_concept | has_concept | 244,992 | 122,496 | 44,032 | 2.78× |
| 64 | 1,008 | has_concept | has_concept | 2,804,896 | 433,448 | 173,376 | 2.50× |
| 64 | 4,032 | has_concept | has_concept | 41,556,320 | 1,683,872 | 693,504 | 2.43× |
| 128 | 0 | coactivated_with | coactivated_with | 0 | 0 | 0 | — |
| 128 | 128 | has_concept | coactivated_with | 172,224 | 42,496 | 42,496 | 1.00× |
| 128 | 512 | has_concept | has_concept | 981,504 | 490,752 | 169,984 | 2.89× |
| 128 | 4,064 | has_concept | has_concept | 43,364,416 | 3,437,136 | 1,349,248 | 2.55× |
| 128 | 16,256 | has_concept | has_concept | 667,968,192 | 13,550,400 | 5,396,992 | 2.51× |

The source's cardinality heuristic follows the smaller `has_concept` edge set whenever Q>N. It therefore overrides sparse-first authorship in every tested Q>N cell. The closure v1 reference shows that coactivation-first is still cheaper at these densities: the graph-first sparse-authored arm performs 2.28–2.89× as many candidate tests as the explicit sparse-first order. At Q=N, tie behavior preserves each arm's starting clause; at Q=0, choosing the empty coactivation relation avoids the broad pair scan. The current heuristic uses first-edge cardinality as a selectivity proxy, while this rule family's cost depends strongly on the joined binding structure.

## Interpretation and limits

This is direct evidence that install-time visibility alone does not make the current ordering choice efficient for this pattern. It motivates measuring join cardinality/intermediate binding estimates or learning from runtime statistics before changing the production heuristic. The panel does not establish a better universal heuristic; a selector must be tested across other rule shapes, graph topologies, and densities, while retaining exact closure semantics. The rules-before-data reference represents the captured productive fixture construction path and should not be generalized to every application boot route. Wall times are instrumented and vary between captures; candidate tests and exact semantics are the primary comparison.

## Reproduction and artifacts

- Protocol: [preregistration](CAN_INSTALL_TIME_JOIN_ORDER_V1_PREREG_20261001.md)
- Runner: [capture script](../../../evaluation/substrate_capability/can_install_time_join_order_v1.py)
- Analyzer: [order oracle and gates](../../../scripts/analyze_can_install_time_join_order_v1.py)
- Lock: [source and prior-capture lock](../../../evaluation/substrate_capability/can_install_time_join_order_v1_lock_20261001.json)
- Raw data: [45 workers](../../../evaluation/reports/can_install_time_join_order_v1_workers_20261001.json)
- Summary: [analysis output](../../../evaluation/reports/can_install_time_join_order_v1_analysis_20261001.json)

Run `python3 evaluation/substrate_capability/can_install_time_join_order_v1.py` to verify all locked inputs, execute the panel, and run the analyzer.
