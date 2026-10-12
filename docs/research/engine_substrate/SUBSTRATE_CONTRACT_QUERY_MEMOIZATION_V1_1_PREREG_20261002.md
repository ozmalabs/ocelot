# Contract query evaluation memoization v1.1 — preregistration

V1 completed under a preregistered disabled/enabled comparison. It cut native evaluations by 2.0–2.6× but made end-to-end selector loops 2.5–2.8× slower; per-lookup JSON serialization erased the native savings. V1.1 preserves those results and compares the unchanged no-cache path, the JSON cache, and a new `TermEvaluationCache` that retains canonical Term/environment fingerprints across calls.

## Panel

Run two fresh workers per cache arm for H=32/N=500, H=128/N=28, and H=512/N=36 coded hypothesis sets. Require exact query/prediction/label/final-survivor parity among all three arms. Independently check native cache misses against one evaluation per pure Term/environment pair. A callback-backed `Holds` control must still execute four callbacks and store no values under both cache APIs, confirming that graph-dependent terms bypass memoization.

## Measures and limits

Report evaluator calls, full selector wall time, cache entries, logical serialized-key bytes, peak RSS, and paired speedup. Do not infer speed from fewer native calls; fingerprint preparation, dictionary lookups, deep copies, and memory all enter wall time. These are small finite pure-Term workloads. The caller must not mutate Terms/environments or change graph/evaluator semantics across the cache lifetime. No claim applies to graph-dependent terms, arbitrary side effects, or an integrated real-task query service.
