# Ownership-order census v1 preregistration

**Question.** How often does the full seed-booted substrate contain names for which `implication_harvester._owning_mt_map()` has multiple possible owning microtheories, making its first-edge choice sensitive to edge ordering?

## Method

Construct the ordinary full seed graph with `WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)` followed by `load_all_seeds(adapter)`. Count `has_concept` and `has_rule` edges. Group by `(edge type, target node ID)` to count graph-level multiple ownership, and separately by `(edge type, target node name)` to count helper-level name collisions across distinct source node IDs. Report loaded/failed seed counts, graph size, ownership edge count, number of named groups, ambiguous groups, duplicate same-owner rows, and a deterministic sample of ambiguous groups with source Microtheory names/IDs. Capture a combined SHA-256 digest of all seed JSON sources and hashes for the loader, adapter, helper, and native extension before/after the census.

## Interpretation limits

This is a descriptive census of the current authored seed corpus, not a distribution over natural tasks. Name collisions may represent intentional homonyms, duplicated concepts, or distinct concepts that the helper conflates; this count alone does not adjudicate them. Failed seed loads are reported and bound the coverage claim. The audit establishes exposure to ordering dependence, not that a receipt changed a downstream task result.

The first exploratory full boot preceded this preregistration and motivated the question. Its output is excluded from the frozen result; run the locked script after this protocol is recorded.
