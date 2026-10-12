# Native thoughtexperiment rule-patch semantics v1 — preregistration

**Question:** Does native active-rule-by-name replacement preserve the legacy Python export/scan/remove/add behavior across common candidate shapes beyond the single positive candidate?

**Cases:** (1) replace `sd_mint_quantum` with the positive repair; (2) remove that rule; (3) target an absent rule; (4) patch an existing rule and absent rule together; (5) replace later-slot `sd_dedup_existing` with its exported definition; and (6) patch both existing rules in one candidate. Run both patch implementations against the same baseline and fixture, for scoped full-copy and shared graph pages, with three fresh processes per case/backend (36 worker processes). Each worker computes baseline once, runs legacy then native on discarded branches, and compares complete outcome signatures.

**Gates:** Every paired result signature matches exactly; active-target application/inertness agrees with the authored case; original primary graph/rule revision/counts/serialized rules remain identical; source/native binary lock and build freshness pass; 36 unique process IDs; all scenarios complete without exception.

**Limits:** One synthetic shape-decoding graph and rule vocabulary; no broad rule-dialect, malformed replacement, concurrent branch, or natural-task claim. This is a semantic promotion gate, not a performance test.
