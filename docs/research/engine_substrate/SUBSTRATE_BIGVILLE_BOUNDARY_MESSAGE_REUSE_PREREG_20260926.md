# Bigville exact boundary-message reuse preregistration

## Question

For the controlled cross-resident Bigville CAN models, can exact component messages conditioned only on each component's adjacent boundary variables preserve global MAP while avoiding repeated interior enumeration across all `d^k` global boundary assignments?

## Design

Reuse the source-locked authored workload and topology design in [the cross-boundary preregistration](SUBSTRATE_BIGVILLE_CROSS_BOUNDARY_MAP_PREREG_20260926.md): cast prefixes N=10/25, three matching/topic patterns, k=0/2/4/6, and three fresh workers. Extract the whole CAN graph and discover the boundary/interior structure from graph edges, not resident labels.

For each interior component C, form its interface I(C), the boundary variables incident to any pairwise factor touching C. For each assignment to I(C), enumerate C's states and store the minimum component-local energy including its unary terms, internal factors, and C-to-boundary factors. Then enumerate all global boundary assignments and minimize the sum of boundary unary/boundary-only factors and the cached component messages. Each factor is charged once. Compare with current global min-fill/junction-tree MAP and score all returned states independently against the full extracted model.

Record `d^k` global boundary combinations and message-construction assignments `Σ_C d^(|I(C)|+|C|)`, alongside the direct-oracle work `d^k Σ_C d^|C|`. Time graph extraction, global solver, message construction plus boundary minimization separately. Preserve component interfaces, message-table sizes, exact counts, width, energies, and all source/build fingerprints.

## Gates and limits

Require three fresh worker PIDs, stable source/build locks, complete N×k replication, exact extracted factor coverage, valid interfaces, independently reconstructed assignment counts, complete domain-valid output states, and energy agreement to 1e-7 against global JT and independent whole-model scoring. This tests an offline Python exact algorithm on controlled authored/synthetic cross-links. It does not measure native frame scheduling, learned separators, natural boundary distributions, or engine end-to-end savings. The k≤6 envelope is deliberately bounded and is not evidence for wide interfaces.
