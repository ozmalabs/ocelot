# Executable seed Argmax/Holds census v1 results — 2026-10-04

The source-locked scan covers 63 operator-bearing seed manifests from the locked JSON seed corpus. Among executable rules, it finds 327 `Argmax` term occurrences in 126 rules and 33 `Holds` occurrences in 10 rules. No executable rule contains both operators. The Holds-bearing seed families are `ballistics`, `projection`, and `shape_recognition`.

This is static authored-rule inventory evidence only: the census does not prove any rule fires or that a runtime cache becomes nonempty. It does show that a representative transfer panel should use separate Argmax-heavy and Holds-bearing rules or subsystems, rather than assuming a single authored rule exercises both families. `vision_growth` is an Argmax candidate; `ballistics` or `projection` is a Holds candidate. Runtime fixtures and exact cache/work replay remain the next gate.

Evidence: [preregistration](SUBSTRATE_CACHE_OPERATOR_SEED_CENSUS_V1_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/cache_operator_seed_census_v1.py), [source lock](../../../evaluation/substrate_capability/cache_operator_seed_census_v1_lock_20261004.json), and [capture](../../../evaluation/reports/cache_operator_seed_census_v1_20261004.json).
