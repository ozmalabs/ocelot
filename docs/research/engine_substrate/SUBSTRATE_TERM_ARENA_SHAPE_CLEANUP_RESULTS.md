# TermArena cleanup for JSON shape APIs

## Finding and repair

An exploratory pre-fix call on the built extension ran batches of 1, 10, 100, and 1,000 `shape_of_term` calls over the same one-node literal. The 1,111 total calls grew `term_arena_len()` from 0 to 1,111. The API parsed fresh JSON Terms into the persistent arena each time, and its TermIdx-keyed cache could not reuse an entry across those fresh IDs. Source review also found that `add_shape_node_for_term` retained its input Terms even though its durable output is a graph Shape node.

Both APIs now parse into a temporary arena suffix, compute the structural Shape without adding one-shot TermIdx cache entries, and truncate the suffix on success or partial parse failure. Internal callers holding stable TermIdx values still use the Substrate's TermIdx cache. Shape nodes created by `add_shape_node_for_term` remain graph-resident as intended.

## Confirmatory engineering verification

The post-change runner performed three in-process replicates at 10, 100, and 1,000 repeated calls. All returned Shapes matched. Each size left arena delta zero. In each replicate, 100 malformed partial Terms per API were rejected and left arena length unchanged. Creating 1,000 Shape graph nodes retained exactly 1,000 graph nodes and zero TermArena nodes. Median total time was 0.038 ms for 10 calls, 0.335 ms for 100, and 3.627 ms for 1,000. These are diagnostic timings without an old/new paired performance design; they verify neither cache speedup nor broader API latency.

The release extension was rebuilt from the current Rust source. Its SHA-256 is recorded in the lock and raw report. `cargo check -p substrate-rs`, `scripts/engine_build.sh`, and `domains/engine_provenance.py` succeeded. The build script printed its pytest command but did not run that test; no ordinary test suite was run.

## Reproduction and limits

- Runner: [`substrate_term_arena_shape_cleanup_probe.py`](../../../scripts/substrate_term_arena_shape_cleanup_probe.py)
- Lock: [`term_arena_shape_cleanup_lock_20260925.json`](../../../evaluation/substrate_capability/term_arena_shape_cleanup_lock_20260925.json)
- Raw report: [`substrate_term_arena_shape_cleanup_20260925.json`](../../../evaluation/reports/substrate_term_arena_shape_cleanup_20260925.json)
- Ownership audit: [`SUBSTRATE_TERM_ARENA_OWNERSHIP_AUDIT.md`](SUBSTRATE_TERM_ARENA_OWNERSHIP_AUDIT.md)

This closes one observed JSON convenience-path retention defect. It does not bound arena allocation capacity/RSS, audit every JSON parser or caller that can truncate, measure long-run synthesis reuse, or solve reclamation of Terms referenced by rules, grammar productions, concepts, and caches. The public JSON `shape_of_term` path now recomputes the small structural summary on each call instead of pretending fresh TermIdx values are reusable cache keys. A content-keyed bounded cache would require separate design and measurement.
