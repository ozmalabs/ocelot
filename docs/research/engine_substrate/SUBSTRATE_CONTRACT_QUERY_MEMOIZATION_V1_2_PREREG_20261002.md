# Contract query evaluation memoization v1.2 — preregistration

V1's per-lookup JSON cache and v1.1's retained canonical fingerprints both reduced native Term calls but were slower than the uncached selector on measured workloads. V1.2 compares four routes under the same lock: no cache, JSON-per-lookup dictionary, retained content fingerprints, and a new identity-keyed cache for stable immutable objects.

## Panel and gates

Use paired fresh workers at H=32/N=500, H=128/N=28, and H=512/N=36, two repetitions per arm. Require identical query histories, predictions, oracle labels, and final finite-set survivors. Verify evaluator calls exactly: uncached calls follow selector refilter/rescore work; each memoized arm evaluates each pure hypothesis/environment pair once. Run the graph-dependent `Holds` callback under each cache route; it must execute four callbacks and store zero values.

Report native calls, end-to-end wall time, cache entries, logical serialized-key bytes, peak RSS, and paired speedups. Preserve all regressions. The identity cache is valid only while Term/input objects are immutable and the evaluator context remains fixed; it is restricted to the pure Term allowlist. This study does not justify caching graph-dependent Terms or mutable external state.
