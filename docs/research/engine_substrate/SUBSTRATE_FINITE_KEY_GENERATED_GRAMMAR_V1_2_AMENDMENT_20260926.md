# Finite-key generated grammar v1.2 amendment

The first 25-case v1 capture passed 24 cases and exposed a mismatch in the independent reference interpreter for `minted_endpoint_recursion`. Source review of `runners/dsl/src/rewrite.rs::extend_each` shows that the runtime deliberately requires distinct bound variables to map to distinct nodes. The v1 reference interpreter omitted this injective-binding condition and therefore expected a self-loop binding that the runtime correctly refuses. The initial tentative engine-defect diagnosis was incorrect; the v1 raw capture is retained as evidence of the oracle mismatch.

V1.2 fixes the reference interpreter to enforce injective bindings before rule effects. No runtime behavior or semantic criteria change. The amended runner rebuilds against the unchanged runtime source and reruns the same 15 accepted / 10 rejected cases. Every accepted program must reach the same terminal graph as the corrected interpreter, report `fixed_point`, and stay within the finite-fact progress bound; every registered negative case must be refused by the checker.

The amended panel remains a finite representative grammar sample, not exhaustive parser equivalence or a general termination theorem.
