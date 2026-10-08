# Shape-decoding native rule-patch comparison v4 — preregistration

**Question:** Does replacing a candidate rule by name inside the native branch remove enough Python serialization and GIL-held work to improve concurrent shared-page thoughtexperiments?

**Intervention:** Add `replace_active_rule_by_name` to the PyO3 substrate API. It finds the active named rule directly in the native rule store, removes it, optionally parses and installs its replacement, and returns whether a target was found. The Python rehearsal gains an opt-in `_native_rule_patch` route; the existing export/scan/remove/add path remains the control. Each operation is confined to an already detached experiment branch. Compare both patch routes in a 2×2×2 design: scoped full-copy/shared graph pages × sequential/concurrent fanout 8 × 3 fresh processes per cell, using the same 100k-node `dedup_identity_fix` task and phase/thread-CPU measurements (24 total processes).

**Gates:** All cells must retain exact positive candidate application and convergence; signatures must match across patch methods, backends, and modes; primary graph/rule revision must remain fixed; all phase and CPU values nonnegative; 24 unique processes; source/native binary lock and build freshness pass.

**Decision:** The main target is a reproducible reduction in concurrent shared-page wave time and an increase in CPU/wall overlap, without semantic differences. Any improvement is workload-specific. Three repeats, one candidate family, and one host do not establish broad throughput or scaling.
