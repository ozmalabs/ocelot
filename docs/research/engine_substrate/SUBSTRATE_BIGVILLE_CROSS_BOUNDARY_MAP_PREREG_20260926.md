# Bigville cross-boundary exact MAP preregistration

## Question

When controlled pairwise CAN factors connect otherwise independent authored Bigville resident networks, does conditioning on the explicit boundary variables preserve the global exact MAP, and how do assignment work and timing change with boundary dimension?

## Workload and design

Build one aggregate CAN model from the deterministic Bigville cast using the authored five-Concept resident builder and common scenario evidence. Use N=10 and 25 residents, 3-state domains, and boundary dimensions k∈{0,2,4,6}. Add k/2 deterministic cross-resident pairwise edges, with distinct endpoints chosen from the first six residents under three preregistered matchings (one pattern per fresh worker); use fixed topic and weight assignments per pattern. The controlled edges are reciprocal in the substrate graph and represent one undirected factor each.

The boundary set B is the exact set of endpoint Concepts of the added cross-resident factors. For matching patterns 0, 1, and 2, respectively, use endpoint topic pairs `(trust_mayor,claim_credible)`, `(trust_mayor,world_safe)`, and `(claim_credible,debtor_trustworthy)`, with added weights `0.25`, `-0.25`, and `0.5` in matching order. Remove B from the extracted pairwise graph and discover connected interior components by BFS. For each assignment in D^B, independently enumerate each interior component's assignments while holding B fixed, include all unary, interior, boundary-interior, and boundary-only factors exactly once, select the best conditional state, and minimize over boundary assignments. Compare this result against current min-fill plus global junction-tree MAP. Score both with a separate whole-model energy implementation. Record `d^k` boundary assignments, `d^k Σ_C d^|C|` interior assignments, component sizes, width, extraction cost, global-solver cost, and conditional-solver cost.

## Replication and provenance

Three fresh workers cover the complete N×k design, with one deterministic cross-edge matching pattern per worker. Lock the protocol, runner, cast, Bigville builder, exact-inference and width modules, Rust graph/PyO3 sources, native extension/build manifest, and commit at worker start/end. Require extracted factors equal the resident-network union plus exactly the added factors; |B|=k; no pairwise factor joins distinct interior components after removing B; exact conditional/global energy agreement; complete domain-valid states; and independently reconstructed assignment counts. Preserve all failures.

## Claim boundary

This tests bounded nonzero separators on a controlled augmentation of deterministic authored simulation data. The cross-resident factors are experimental perturbations, not naturally observed task links. It does not establish that the substrate discovers boundary variables, that native frames exchange messages, or that natural workload boundary dimensions stay small. The three topology patterns provide limited sensitivity, not a population distribution.
