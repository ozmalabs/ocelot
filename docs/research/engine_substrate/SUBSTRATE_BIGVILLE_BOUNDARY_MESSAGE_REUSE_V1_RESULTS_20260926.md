# Bigville exact boundary-message reuse results

## Result

The 24-case, three-worker replay passed all eight independent analysis gates. Across N=10/25, k=0/2/4/6, and three cross-resident matching/topic patterns, component-local boundary messages plus global boundary minimization matched global min-fill/junction-tree MAP in every case. Whole-model independent energy scoring agreed within 1e-7, states were complete and domain-valid, the explicit separator condition held, and assignment counts reconstructed from component sizes and interface sizes.

The direct conditional oracle repeated each interior enumeration for every global boundary assignment. Message reuse instead enumerated each interior only across its local interface assignments. At N=25,k=6, maximum component interface size was one; counted local work fell from 3,582,306 to 5,508 assignments (650.4× fewer). Median message-build plus global-boundary MAP time was 22.28 ms, versus 7.26 ms for global width-2 JT. At N=10,k=6, assignment work fell 496.6×, but message time was 10.45 ms versus 1.86 ms for global JT. At k=0, message reuse was also slower than global JT. Thus message reuse removes the catastrophic repeated-interior work but does not win on these small, already low-width graphs.

## Interpretation and limits

The experiment validates an exact algorithmic decomposition and the predicted work dependence on component interfaces. It demonstrates why global separator cardinality alone can be pessimistic for interior work: for k=6, every component interface had size at most one. However, the solver still enumerates all `d^k` global boundary assignments and is implemented as an offline Python diagnostic. The Bigville cross-links form a small controlled matching family; this is not a test of wide or dense boundary interaction graphs.

No native frame scheduler, runtime cut discovery policy, natural workload distribution, large-scale memory profile, or end-to-end engine benefit was measured. The next algorithmic question is whether variable elimination over the induced boundary factor graph replaces `d^k` enumeration with a cost governed by boundary treewidth, and whether that route beats monolithic JT after charging cut/message construction.

## Artifacts

- Protocol: [preregistration](SUBSTRATE_BIGVILLE_BOUNDARY_MESSAGE_REUSE_PREREG_20260926.md)
- Runner: [`substrate_bigville_boundary_message_reuse_v1.py`](../../../scripts/substrate_bigville_boundary_message_reuse_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_boundary_message_reuse_v1.py`](../../../scripts/analyze_substrate_bigville_boundary_message_reuse_v1.py)
- Source lock: [lock JSON](../../../evaluation/substrate_capability/bigville_boundary_message_reuse_v1_lock_20260926.json)
- Raw capture: [JSON report](../../../evaluation/reports/substrate_bigville_boundary_message_reuse_v1_20260926.json)
- Analysis: [analysis JSON](../../../evaluation/reports/substrate_bigville_boundary_message_reuse_v1_analysis_20260926.json)
