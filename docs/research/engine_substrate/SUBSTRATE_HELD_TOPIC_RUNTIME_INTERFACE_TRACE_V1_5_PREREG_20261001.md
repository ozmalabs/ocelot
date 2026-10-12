# Held-topic runtime interface trace v1.5 preregistration (2026-10-01)

## Objective

The v1.4 capture's 36 legacy `term_index_query` events originate in `SdCacheKey::typed_fingerprints`, not `NodesWhere`. They denote hashing a type's full node population and attributes for ShapeDecode cache invalidation. Rename this event to `term_typed_population_query` and emit one `term_typed_population_candidate` event for every node visited, keyed by rule UID and type. Preserve the v1.4 detailed snapshot for `NodesWhere` queries, which were not observed in v1.4.

## Gates

Rebuild the optimized native extension and repeat the locked seven-turn, three-worker capture. Require current source hashes, distinct fresh workers, seven turns each, zero dropped events, mapped rule IDs, exact trace/interface aggregates, and identical structural/runtime signatures. Classify typed-population query and candidate events as covered by `reads_any` because they hash every attribute on nodes of each queried type. Report query counts and visited-node units by rule and type. Keep explicit `NodesWhere` indexed/fallback query counts and candidate/result cardinalities separate; do not imply B-tree internal work from result size. No old event kind should remain unexplained.

## Limits

Typed-population candidate units count node visits, not hashed bytes or CPU instructions. Attribute values are hashed but per-attribute hashing cost is not weighted. The route remains one workload; this audit does not establish locality prevalence or partition safety.
