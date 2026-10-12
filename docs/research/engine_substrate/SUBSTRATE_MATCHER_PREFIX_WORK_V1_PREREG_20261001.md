# Matcher prefix-work panel v1 preregistration

Date: 2026-10-01

## Question

How does candidate work at each match-clause prefix vary across independent path, star, and cycle rule shapes and graph topologies, and do the native per-clause audit counters agree with an independent join enumerator?

## Design

Use three four-edge Concept patterns (`causal_influence` path, four-edge star, and directed four-cycle), three directed graph topologies (path, center-out star, and ring), N={16,32}, and two clause-list orders (authored and reversed). Run three fresh-process replicates per cell: 3 patterns × 3 graph shapes × 2 N × 2 orders × 3 repeats = 108 workers. Graph edges are deterministic and all use one relation type so edge-cardinality ties expose the matcher’s connected-edge/tie behavior. Each worker creates graph facts first, imports one effect-free rule with `match_type=Concept`, captures the installed order, and runs full match enumeration under native scale audit.

Record the candidate tests at each installed zero-based clause position via `scale_audit_match_clause_snapshot()`, along with global candidate totals, candidate-pair work, leaf visits, variable collisions, graph counts, and elapsed time. Independently simulate the matcher’s bound-source/bound-target candidate enumeration from the generated adjacency lists, including the engine’s leaf-time injective-binding rejection. Require exact equality between simulated and observed per-position candidate counts.

## Gates

- Exactly 108 unique worker cells and PIDs; stable lock over protocol, runner, analyzer, seed, native extension, and relevant matcher/audit sources.
- The independent greedy ordering replay matches the actual installed four-clause sequence.
- Independent prefix candidate counts match native audit counters exactly at every position.
- Per-position sums equal global `cand_tested`; graph state/digest stays unchanged and repeated closure is stable.
- Candidate enumeration completes below the configured rule-step bound; zero effects/progress are expected.

## Limits

These are four-clause synthetic patterns with one relation type and small deterministic path/star/ring graphs. They isolate prefix candidate work and topology sensitivity, not natural rule libraries, mixed-relation selectivity, productive closure, full system cost, or general asymptotic behavior. The panel validates a candidate-work model; it does not prove that a practical selector can estimate its costs cheaply on arbitrary graphs.
