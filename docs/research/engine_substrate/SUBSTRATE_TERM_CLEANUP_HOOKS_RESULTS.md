# Reflected Term cleanup hook results

**Status:** ownership-aware cleanup dispatches every deletion event, including when an earlier callback raises; the first error is still reported to the caller.

## Findings

A pre-locked probe exercised successful cleanup, an externally owned leaf, and a raising callback followed by an observer. On success, callback `(node_id, former_type)` records exactly matched the native removal order (4/4). With a shared leaf, the three removed nodes each generated one callback and the protected leaf generated none. Both success arms passed.

The first run against the initial binding exposed a dispatch defect: a raising hook caused later deleted-node notifications to be skipped even though all nodes had already been deleted. The binding was changed at two levels: `fire_hook` now attempts every callback for an event while retaining the first exception, and `remove_term_subgraph` attempts every removed-node event before returning the first exception. The confirmatory run shows the raising callback and a later observer each received all four deletion notifications; all Term nodes were deleted and `RuntimeError('hook_probe_failure')` was surfaced after dispatch. The post-fix probe passed.

This is a callback-delivery result for one small Term tree. It does not establish hook reentrancy safety, behavior for callbacks that mutate the substrate, concurrent mutation safety, arena reclamation, or workload-level callback cost.

## Provenance

The post-fix native extension was built with `scripts/engine_build.sh`; `cargo check --lib` passed. The registered hook probe, native ownership probe, and P4 cleanup recheck all passed against the same rebuilt extension. No ordinary pytest suite was run.

Preregistration: [protocol](SUBSTRATE_TERM_CLEANUP_HOOKS_PREREG_20260925.md). Runner: [hook probe](../../../scripts/substrate_term_cleanup_hooks_probe.py). Lock: [content lock](../../../evaluation/substrate_capability/term_cleanup_hooks_lock_20260925.json). Raw record: [hook results](../../../evaluation/reports/substrate_term_cleanup_hooks_20260925.json). The ownership/P4 reruns are recorded in [ownership raw](../../../evaluation/reports/substrate_term_subgraph_native_cleanup_20260925.json) and [P4 raw](../../../evaluation/reports/substrate_p4_term_cleanup_recheck_20260925.json).
