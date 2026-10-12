# TermArena rollback edge-case results

**Status:** all three amended, preregistered edge cases pass against the current native build.

A malformed Cat Term with a valid first child and unknown second variant raises ValueError while leaving both TermArena length and the graph fingerprint unchanged in direct add_term_subgraph. Loading the same malformed stimulus as a seed reflex skips that entry and leaves arena and graph state unchanged. Loading a valid four-node Cat stimulus creates one Reflex node and a durable stimulus_term subgraph whose canonical JSON matches the source Term, while TermArena length remains zero.

The initial v1 probe had a result-adapter assertion error: it expected summary key reflexes_added where the seed loader returns reflexes. The raw failed artifact and original lock are preserved. Amendment v1.1 changes that expected field only; all three cases pass on the amended run.

This does not establish all parser errors, multi-entry partial manifest behavior, reflex persistence/reload, concurrent loading, or broad memory behavior.

Protocols: [v1 protocol](SUBSTRATE_TERM_ARENA_ROLLBACK_EDGECASES_PREREG_20260925.md), [v1.1 amendment](SUBSTRATE_TERM_ARENA_ROLLBACK_EDGECASES_V1_1_AMENDMENT_20260925.md). Runner: [edge-case probe](../../../scripts/substrate_term_arena_rollback_edgecases.py). Locks: [failed v1](../../../evaluation/substrate_capability/term_arena_rollback_edgecases_lock_20260925.json), [amended v1.1](../../../evaluation/substrate_capability/term_arena_rollback_edgecases_v1_1_lock_20260925.json). Raw records: [failed v1](../../../evaluation/reports/substrate_term_arena_rollback_edgecases_20260925.json), [passing v1.1](../../../evaluation/reports/substrate_term_arena_rollback_edgecases_v1_1_20260925.json).
