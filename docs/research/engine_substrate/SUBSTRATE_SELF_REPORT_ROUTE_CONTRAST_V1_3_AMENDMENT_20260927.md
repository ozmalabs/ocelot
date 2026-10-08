# Self-report route contrast panel v1.3 amendment: canonical set attributes

Date: 2026-09-27

The v1.2 analyzer's exact graph gate flagged J because its digest preserved order inside serialized set-valued attributes. A source-locked three-worker follow-up captured the differing `Interlocutor.believed_concepts.__fset__` values: all workers contain the same five elements, but one serialization orders `communicative` and `generated` differently. Node IDs/types and typed edges otherwise match. Recursively sorting only tagged set/frozenset values yields an identical canonical full-graph digest across all three workers; routes, comprehension and replies also repeat.

This resolves the v1.2 J discrepancy as serialization-order variance, not graph-state variance. The original v1.2 raw digest and analysis are preserved. Do not rewrite the historical failed check; cite the follow-up canonical analysis when describing semantic graph repeatability. Future graph parity gates should canonicalize unordered containers before hashing.
