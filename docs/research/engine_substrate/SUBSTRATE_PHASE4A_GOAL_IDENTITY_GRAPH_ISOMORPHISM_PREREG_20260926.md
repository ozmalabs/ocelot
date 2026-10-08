# Phase 4A Goal identity graph-isomorphism scale check

**Question:** does the N=2 finding that full and scoped Phase 4A outputs are the same typed graph up to generated node IDs hold at every captured N=2/4/8 replicate?

Reuse the locked producer-integrated `worker()` in `substrate_phase4a_produced_goal_identity_v1.py`, capture the full `graph_to_dict()` result from each full/scoped worker, and run three fresh-process pairs per size (18 workers). Do not change the materializer, seed, task inputs, schedules, or closure caps. Preserve each worker's semantic projection and fixed-point/provenance gates. Compare graphs by node descriptors (`type` plus sorted attributes), then pair nodes within equal descriptor classes in ID order and compare complete typed edge multisets after the mapping. Report ambiguous descriptor classes. Require node descriptor multiset equality, total node mapping, typed edge equality, equal normalized task projections, and unique PIDs for every pair. Raw digests may differ.

This mapping check is a bounded diagnostic; it does not prove a unique canonical labeling or graph isomorphism for arbitrary graphs. Should any descriptor class pairing fail, preserve the counterexample and investigate with a stronger graph-isomorphism algorithm before asserting non-isomorphism. No production code or semantic rules are modified.
