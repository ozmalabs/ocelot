# Thoughtexperiment touched-object parity v1.1 results

## Finding

All 18 current-source workers complete and pass the corrected independent
analysis's 19 checks. Candidate selection, primary isolation, branch and
monolithic-oracle parity, active-rule preservation, stale-return refusal, and
closure quiescence hold at 10,511/100,511/200,511 nodes under both copy
backends. Every selected residual is node-change-only, changing one or two
nodes; no candidate residual in this panel adds, removes, or changes edges.
Reconstructing the complete touched node state from its before-image plus
journal patch matches the returned primary in all 18 workers.

| Nodes | Backend | Exact branch/primary audit | Touched preimage + projection | Median per-worker full/touched ratio |
|---:|---|---:|---:|---:|
| 10,511 | Full-copy | 136.0 ms | 0.095 ms | 1,512× |
| 10,511 | Shared pages | 128.4 ms | 0.091 ms | 1,256× |
| 100,511 | Full-copy | 1.326 s | 0.106 ms | 12,936× |
| 100,511 | Shared pages | 1.335 s | 0.101 ms | 13,220× |
| 200,511 | Full-copy | 2.633 s | 0.125 ms | 21,480× |
| 200,511 | Shared pages | 2.637 s | 0.113 ms | 23,904× |

The exact comparison comprises two full graph exports and two canonical
digests: selected branch and returned primary. The touched check reads and
reconstructs one or two complete changed nodes. Its measured time stays near
0.09–0.13 ms over this size range; exact comparison cost increases from about
0.13 s to 2.64 s. Medians use three workers per cell on one host.

## Guarantee boundary

All six preregistered scratch controls pass the touched projection after
changing an unrelated noise node outside the journal, while exact whole-graph
digest comparison detects the divergence. Therefore, touched-object parity is
a cheap check that the adopted primary matches the journal's reported changes
on those objects. It is not a substitute for exact graph parity when
untracked, unjournaled, or unrelated mutations are possible. It also does not
validate edge changes; the validator fails closed on any residual containing
adds/removes or edge changes. Any production use would need a separately
established guarantee that every relevant mutation is covered by the journal
and an explicit policy for when a global audit remains required.

The first v1 attempt is retained but all 18 workers failed because audit
instrumentation tried to deep-copy a native `NodeID`. The v1.1 runner copies
only the node type and JSON attribute payload and completes the full schedule.
The v1.1 analyzer initially assumed exactly one changed node; retained rows
show one or two, so a post-capture analyzer correction checks its count against
the raw selected residual. No worker was removed or rerun for that correction.

## Reproduction artifacts

- [Protocol](THOUGHTEXPERIMENT_TOUCHED_OBJECT_PARITY_V1_PREREG_20261004.md)
- [v1.1 amendment](THOUGHTEXPERIMENT_TOUCHED_OBJECT_PARITY_V1_1_AMENDMENT_20261004.md)
- [Analysis correction](THOUGHTEXPERIMENT_TOUCHED_OBJECT_PARITY_ANALYSIS_AMENDMENT_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_touched_object_parity_v1_1.py)
- [Original v1.1 analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_touched_object_parity_v1_1.py)
- [Corrected independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_touched_object_parity_v1_1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_touched_object_parity_v1_1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_touched_object_parity_v1_1_20261004.json)
- [Corrected analysis](../../../evaluation/reports/thoughtexperiment_touched_object_parity_v1_1_1_analysis_20261004.json)
- [Failed v1 capture](../../../evaluation/reports/thoughtexperiment_touched_object_parity_v1_20261004.json), retained and excluded from performance conclusions
