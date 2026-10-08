# Production retinal join-order panel v1.1 results

Date: 2026-10-01  
Protocol amendment: [v1.1 analyzer correction](PHOTON_RETINAL_JOIN_ORDER_V1_1_AMENDMENT_20261001.md)  
Original preregistration: [v1 protocol](PHOTON_RETINAL_JOIN_ORDER_V1_PREREG_20261001.md)  
Runner: [source-locked exhaustive panel](../../../evaluation/substrate_capability/photon_retinal_join_order_v1_1.py)  
Analyzer: [independent gates](../../../scripts/analyze_photon_retinal_join_order_v1_1.py)  
Capture: [nine-worker raw data](../../../evaluation/reports/photon_retinal_join_order_v1_1_workers_20261001.json)  
Analysis: [gates and order rankings](../../../evaluation/reports/photon_retinal_join_order_v1_1_analysis_20261001.json)  
Input lock: [source/native lock](../../../evaluation/substrate_capability/photon_retinal_join_order_v1_1_lock_20261001.json)

## Result

The corrected source/native-locked replay passes **13/13 gates** across nine fresh processes. Each worker evaluates the ordinary cardinality-based install order and all 120 permutations of the production five-clause `photon_column_synthesizes_retinal_percept` rule. Real epoch guards and productive percept effects remain active. In every permutation, only the designated last-column percept advances from epoch 0 to 1; its four computed attributes match the oracle; the other 11 percepts stay unchanged; closure reaches fixed point; and canonical final graph facts agree. Default and measured-best instrumented/plain executions also agree.

| Support profile | Default installed order | Default candidates | Exhaustive best order | Best candidates | Reduction vs default | Range across all 120 orders |
|---|---|---:|---|---:|---:|---:|
| uniform | has_percept → rod → s → m → l | 54 | has_percept → rod → l → m → s | 54 | 0% | 54–1,104 |
| correlated | has_percept → rod → s → m → l | 364 | has_percept → rod → l → m → s | 364 | 0% | 364–5,088 |
| rotated | has_percept → rod → s → m → l | 88 | has_percept → l → m → s → rod | 57 | 35.2% | 57–1,656 |

In all profiles, each sensor relation has the same global cardinality: 24 edges for uniform supports and 30 for correlated/rotated supports. Correlated and rotated profiles also use the same per-relation 1–4 multiplicity histogram; only how those multiplicities align across columns changes. The default order is therefore identical for correlated and rotated profiles, but in the rotated case it uses 1.54× the minimum candidate work. The measured best is computed by exhaustive enumeration over 120 orders; it is an offline oracle, not an online selector.

The initial v1 run completed its nine workers but hit an analyzer aggregation `TypeError` before producing a gate report. Its raw capture is preserved as diagnostic evidence. V1.1 fixes the aggregation expression, uses distinct output paths and a refreshed lock, and reruns the unchanged panel.

## Interpretation and limits

This is an independent production rule family from the CAN Hebbian pattern. It shows that ordinary global edge-type counts can be insufficient: two supports with the same global cardinalities and per-relation histograms can have different best orders because the relation supports align differently by column. On this rotated fixture the default order misses the exact minimum by 35.2%, while exhaustive search finds the optimum. The large worst-order ranges also show that clause order can matter even when semantics and outcomes stay fixed.

This remains a small constructed retinal graph, not a natural image or real-time end-to-end workload. One production rule and three hand-built support profiles do not support a universal optimizer or natural-task tractability claim. Next build a selector that estimates prefix work from maintained graph indexes, then measure its ranking regret and runtime/memory overhead on held-out rule fixtures, including CAN and this retinal rule.
