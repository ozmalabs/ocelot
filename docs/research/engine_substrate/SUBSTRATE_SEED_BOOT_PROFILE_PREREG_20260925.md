# Seed boot stage profile preregistration

Date: 2026-09-25  
Status: exploratory stage attribution

## Question and design

Profile the full `load_all_seeds` path on the immutable V1.7 baseline snapshot to locate the costs behind the 24–29 second unprofiled boot interval measured in the cold/warm ProblemShape parity probe. Run four fresh processes in fixed order cold, warm, warm, cold; cold removes the seed-index cache immediately before boot, while warm builds and hashes it before launch. Every seed file must match the frozen corpus lock.

Use Python `cProfile` for `load_all_seeds`, reporting call count, self time, and cumulative time for index lookup/build, source digest, topological ordering, JSON loading, and native `load_seed_manifest`, plus the top cumulative functions. Record full graph, grammar, rule store, rule access, rule order, load report, and cache hashes. Require exact boot-state equality across all four processes and unchanged warm-cache bytes.

## Claim boundary

Profiler timings include measurement overhead and are stage-attribution evidence only. They are not production latency or cache speedup estimates. This is one corpus and four runs; any optimization proposal requires unprofiled replicated before/after runs with the same full-state parity checks.
