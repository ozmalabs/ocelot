# Native Term subgraph cleanup results

**Status:** native ownership-aware cleanup passes the focused ownership/error probe and the P4 integration recheck. Ordinary `remove_node` remains node-only.

## Native behavior

`Substrate.remove_term_subgraph(root)` traverses only `child.*` edges. It validates Term node types and cycle absence before mutation, protects each owned node with an incoming edge from outside the subgraph plus that node's Term descendants, then removes the remaining nodes deepest-first. It returns removed and protected IDs. The PyO3 binding fires the usual `node_deleted` hook for every removed node.

The native probe passes all eight preregistered cases: unshared tree, shared subtree, shared leaf, shared root, child cycle, non-Term child, non-Term root, and missing root. The unshared tree is fully reclaimed; external references survive, and deletion of the owner allows subsequent complete cleanup. Cycle/type/root errors leave the entire graph fingerprint unchanged.

## P4 integration and growth comparison

The P4 `contrast_reverse_string_01` route remained accepted with the same retrieved-exemplar construction. Both temporary-evaluation helpers (`prog_synthesis._eval_ir_on` and `prog_retrieval._eval_ir`) return the expected held-out output and leave the 2,700-node substrate at exactly 2,700 nodes. All seven task rows pass after the lifecycle exercise.

On this five-node IR, legacy root-only deletion retained four child nodes per cycle: +4/+40/+400 nodes and +316/+3,160/+31,600 compact graph JSON bytes after 1/10/100 cycles. The new native cleanup retained zero nodes and zero graph JSON bytes at all three points. The 100-cycle batch took 1.14 ms for root-only deletion and 2.32 ms for ownership-aware cleanup in this run. These tiny one-run times include the Python/native call boundary and should not be generalized as a performance comparison; they quantify a correctness/resource tradeoff for this selected Term.

The temporary cleanup callsites now use `remove_term_subgraph`: `domains/prog_synthesis.py`'s reflection round-trip roots and `_eval_ir_on`, plus `domains/prog_retrieval.py::_eval_ir`. The durable `ps_ir_reflected` root remains attached to the Goal and is not recursively removed.

## Provenance and limits

Native sources compiled with `cargo check --lib`, and `scripts/engine_build.sh` built/installed the edited extension and refreshed its content-based build record. The registered ownership probe and P4 recheck both passed. No ordinary pytest suite was run in this work session. The probe does not establish concurrent-mutation safety, TermArena memory compaction, maximum-size tree limits, or callbacks under registered `node_deleted` hooks. Shared-owner tests cover a fixed acyclic Term tree; broader ownership patterns still need evaluation.

Protocols: [native cleanup](SUBSTRATE_TERM_SUBGRAPH_NATIVE_CLEANUP_PREREG_20260925.md), [P4 integration recheck](SUBSTRATE_P4_TERM_CLEANUP_RECHECK_PREREG_20260925.md). Runners: [native ownership probe](../../../scripts/substrate_term_subgraph_native_cleanup.py), [P4 cleanup recheck](../../../scripts/substrate_p4_term_cleanup_recheck.py). Locks: [native probe](../../../evaluation/substrate_capability/term_subgraph_native_cleanup_lock_20260925.json), [P4 recheck](../../../evaluation/substrate_capability/p4_term_cleanup_recheck_lock_20260925.json). Raw data: [ownership cases](../../../evaluation/reports/substrate_term_subgraph_native_cleanup_20260925.json), [P4 comparison](../../../evaluation/reports/substrate_p4_term_cleanup_recheck_20260925.json).
