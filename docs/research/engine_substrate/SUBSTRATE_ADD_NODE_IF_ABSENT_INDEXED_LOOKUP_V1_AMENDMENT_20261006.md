# Indexed `AddNodeIfAbsent` lookup v1 amendment

Date: 2026-10-06

The preregistration is preserved unchanged because its digest is part of the source lock. The implementation treats a declared index with no bucket for a requested value as an exact empty candidate set; only an undeclared index triggers the reference-scan fallback. This distinction enables indexed misses without changing semantics. See the [locked results](SUBSTRATE_ADD_NODE_IF_ABSENT_INDEXED_LOOKUP_V1_RESULTS_20261006.md).

The captured semantic controls cover first-witness behavior after deletion and NodeID reuse, indexed-attribute mutation, subset matching, case-varied values, and empty-attribute fallback. Heterogeneous values, retyping, and all duplicate-request combinations in the preregistration remain open. The live-route timing comparison is confounded because full-seed boot already creates `Concept.name`; the separate source-matched presence probe establishes this directly. No live-route speed effect is claimed.
