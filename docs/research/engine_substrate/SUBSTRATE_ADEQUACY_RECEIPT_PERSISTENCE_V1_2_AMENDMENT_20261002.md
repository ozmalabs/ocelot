# Adequacy receipt persistence v1.2 performance measurement amendment

The v1.1 semantic panel identified full native rule serialization in
`information_commitment._ensure_loaded()` as the dominant durable-teach cost.
The native adapter already exposes exact-prefix rule export. The implementation
now uses that selective read, with full export retained as a compatibility
fallback when the method is unavailable.

The confirmatory writer will additionally time one full `export_rules()` and
one `export_rules_prefix("ic_gate_manifold_projection")` on the same fully
seeded substrate before teaching. Call order alternates by repetition to
reduce order bias. Since this gate seed is lazy-loaded in the fixture, both
pre-teach reads must agree that it is absent; the normal teach call must then
load it, which is checked with a post-teach prefix read. This diagnostic does
not change the persistence/replay pass criteria; it measures the work removed
and the unchanged end-to-end adoption path. An initial diagnostic capture had
an incorrect precondition (it expected the lazy gate before it was loaded) and
is preserved at [export-probe diagnostic](../../../evaluation/reports/substrate_adequacy_receipt_persistence_v1_export_probe_diagnostic_20261002.json).
The runner, this amendment, and `domains/information_commitment.py` are
included in the refreshed source lock. This remains a three-process, one-host
measurement, not a universal speedup estimate.
