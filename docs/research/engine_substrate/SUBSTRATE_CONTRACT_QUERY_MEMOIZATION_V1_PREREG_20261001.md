# Contract query evaluation memoization v1 — preregistration

## Question

Does retaining pure native Term evaluations across successive query rounds reduce the selector's measured work and latency without changing any queries or outcomes, and how much cache memory does it use?

## Intervention

The selector now has an opt-in `evaluation_cache`. It canonicalizes the exact Term and input environment, and memoizes only Terms composed from a conservative pure scalar allowlist. Graph-dependent/unknown Term types bypass the cache. Compare cache disabled/enabled on paired H=32/N=500, H=128/N=28, and H=512/N=36 coded hypothesis sets, two repetitions per arm/cell. A callback-backed graph-dependent control verifies that a disallowed `Holds` term is reevaluated and not inserted into the cache.

## Measures and gates

Lock active module/native/harness sources before capture. Require exact query, entropy, prediction, label, and final-survivor parity between arms. Independently derive the expected cache misses (one evaluation per pure hypothesis/environment pair), check the disallowed-term bypass count and empty cache, and report per-cell native calls, loop wall time, cache entries/serialized bytes, peak RSS, and speedup. Preserve outcomes including regressions: memoization may save native work yet lose wall time to key serialization or memory pressure.

## Scope

This measures a finite pure-Term version-space search only. The caller must keep evaluator semantics stable over cache lifetime. No caching claim applies to graph-dependent Terms, mutable external state, arbitrary side effects, or a different operator mix. Candidate generation and trusted labeling remain external.
