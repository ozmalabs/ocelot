# Thoughtexperiment graph-authored correction ranking v1 — results

**Result:** 14/14 preregistered gates pass.

The first harness invocation exposed an implementation mistake in the worker loop: it ran 18 episodes instead of the preregistered six and failed the episode-count gate. The runner was corrected without changing the protocol, then rerun with exactly three workers and six episodes. Only the corrected replay below is treated as the confirmatory capture.

## Outcome

3 fresh workers completed 6 episodes, with each worker running both arms on fresh substrates. The graph-authored composers produced the correction gate and rank Program. Both arms passed the correct-ready gate, identified `sd_mint_quantum`, adopted `dedup_identity_fix`, and passed every held-out continuation oracle. The third wave used new observation signatures; direct graph inspection found no pending held-out observations, exactly one induced axis per signature, and a zero-progress native closure at the fixed point.

| Arm | Candidate attempts | Median attempts | Median correction time | Held-out oracle |
|---|---:|---:|---:|---:|
| `default_order` | [1, 1, 1] | 1 | 831.105 ms | 3/3 |
| `graph_cost_rank` | [2, 2, 2] | 2 | 1113.933 ms | 3/3 |


The graph ranker orders candidates by structural cost and tries the zero-cost `swap_term_leaf:signature->residual` first; it fails to converge, then `dedup_identity_fix` succeeds at a JSON-size-difference score of 868. The default order tries the successful repair first. Both routes reach the same held-out outcome, while ranking performs more candidate rehearsals. This task therefore does not show a utility advantage for the rank policy; on this fixture its edit-size prior increases search work. Structural edit size is not a substitute for predicted task utility. Every worker ran `default_order` before `graph_cost_rank`, so timing differences are descriptive and may include arm-order/cache effects; candidate attempts and held-out task outcomes are the stronger comparisons.

## Interpretation and limits

The result establishes that the active adapter can execute the graph-authored rank Program and carry a selected correction into later task inputs on this authored observation family. It also reveals that cost-only ranking does not reduce work here. The policy is authored once and does not learn from the returned experience record. Three workers and one task family do not estimate general correction quality, natural-task frequency, or scale. A future delegated-boundary evaluation should make the rank policy consume accumulated outcome/residual/cost experience and compare it on fresh correction families against default, random, and frozen controls.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_GRAPH_AUTHORED_CORRECTION_RANK_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_graph_authored_correction_rank_v1_raw_20261001.json)
