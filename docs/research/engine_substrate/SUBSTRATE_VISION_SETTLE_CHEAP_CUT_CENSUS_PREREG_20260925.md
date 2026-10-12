# Vision settling dependency-cut source census — preregistration

**Evidence type:** deterministic static source census, not runtime measurement. The question is whether the authored `vision_settle` rule's declared state reads permit small dependency cuts when a sheet is divided into spatial frames.

## Method and frozen interpretation

Parse `seeds/vision_settle.json` and require `st_settle` to match `r -has_sunit-> u`, be batched, and write `u.act_next`; require its expression to contain both a local `Neighbours(u, sunit_neighbour)` fold reading neighbor `act` and a global `NodesOfType(SUnit)` fold reading `act`. Require `st_commit` to be batched and copy `u.act_next` to `u.act`. Under this source-defined equation, each `SUnit` output depends on every `SUnit` input via the global mean. Thus the primal dependency graph is complete, exact treewidth is N−1, and a partition into equal frames of k units has N−k external state variables at each frame, N(N−k) ordered cross-frame dependency pairs, and cross-frame share 1−k/N of the global input incidences. These are symbolic consequences, not observed runtime counts.

Report all divisible cases for N in {16, 64, 256, 1024} and frame sizes k in {4, 16, 64}. Also inspect `run_rules_scoped`/`mt_owned_nodes` to establish whether the current native scoped runner accepts arbitrary SUnit frames.

## Claim boundary

This can refute cheap-cut locality for this specific authored rule as written. It cannot establish that all vision workloads are dense, measure execution cost, or show that other rules/substrates share this global read. It does not test how `NodesOfType(SUnit)` behaves when multiple sheets coexist at runtime; that is a separate semantic/runtime probe.
