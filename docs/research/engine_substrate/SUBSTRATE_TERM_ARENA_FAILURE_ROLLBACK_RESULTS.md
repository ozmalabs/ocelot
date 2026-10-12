# TermArena failure-path rollback audit results

## Scope and result

The suffix rollback audit identified malformed-input paths that could append child Terms before returning an error. Rollback is now applied to scratch parsing and setup in `evaluate`, `relax_to_fixpoint`, and `search`; to partial reflected-Term reads in `term_subgraph_json`; and to failed `define_concept` parsing. The previously fixed shape and Term-subgraph creation APIs also restore the arena after malformed partial parses.

The locked engineering verification ran three in-process replicates with 100 attempts per case. All 2,100 attempted operations raised the expected input error, and every case preserved `term_arena_len()` exactly. Cases cover: malformed `evaluate` parse; `evaluate` environment conversion after a successful parse; malformed `relax_to_fixpoint` parse; a valid first `search` Term followed by malformed second Term; malformed concept definition; malformed `add_term_subgraph`; and `term_subgraph_json` failing after reading one valid child from a deliberately incomplete reflected graph.

This specifically verifies logical TermArena length on these seven API failure paths. It does not measure allocator capacity/RSS or claim a general transactional contract over every substrate loading API. Durable rule parsing/import needs a separate rule-store transaction design.

## Reproduction

- Runner: [`substrate_term_arena_failure_rollback_probe.py`](../../../scripts/substrate_term_arena_failure_rollback_probe.py)
- Lock: [`term_arena_failure_rollback_lock_20260925.json`](../../../evaluation/substrate_capability/term_arena_failure_rollback_lock_20260925.json)
- Raw report: [`substrate_term_arena_failure_rollback_20260925.json`](../../../evaluation/reports/substrate_term_arena_failure_rollback_20260925.json)
- Ownership context: [`SUBSTRATE_TERM_ARENA_OWNERSHIP_AUDIT.md`](SUBSTRATE_TERM_ARENA_OWNERSHIP_AUDIT.md)

The lock binds the source, native extension, runner, inputs, and repetition count. This is post-change engineering verification, not a preregistered performance study. Native provenance was checked against the rebuilt extension; the build script's printed pytest command was not executed.
