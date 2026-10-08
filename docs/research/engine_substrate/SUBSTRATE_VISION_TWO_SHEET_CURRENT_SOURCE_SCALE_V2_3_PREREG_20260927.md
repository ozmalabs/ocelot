# Two-sheet current-source vision scale sweep v2.3 preregistration

## Question
How do closure CPU time and memory scale from 8 to 512 SUnits when the settlement fold is global versus Retina-root-scoped, and how much do the native work counters perturb these measurements?

## Design
Use the current `vision_settle` rule on two disjoint square SUnit sheets with side lengths 2, 4, 8, and 16. Cross three fixed RNG seeds (4101, 7301, 10703), global versus benchmark-only root-scoped fold, and B-sheet initial activation 0 versus 1. For each of the 48 semantic cells, run a fresh uninstrumented worker and a fresh worker with `scale_audit` and per-rule counters enabled: 96 isolated processes total. Measure `run_rules(CAP=10,000)` wall time and process CPU time, progress count, graph size, RSS before/after fixture build and closure, and process peak RSS.

The scoped arm rewrites only the two global `NodesOfType(SUnit)` fold sources to `Neighbours(r, has_sunit)`. Generate afferent values deterministically from `PCG64(seed+31*n)`. Compare every arm with an independent equation oracle and require exact output/progress parity between audit-off/on workers. Check global cross-root response to B activation and scoped independence. Audit-enabled counters must equal per-rule sums and the closed-form global/scoped `NodesOfType` counts.

## Integrity and analysis
Lock this protocol and runner, `vision_settle.json`, relevant Python/native sources and binary, build manifest, Python/platform, and engine provenance before spawning any worker. Each worker verifies the lock and writes an independent result file. Require 96 unique cells, exact root membership, no budget exits, equation residual at most 1e-12, semantic parity, counter conservation, and source stability. Report medians/ranges over seeds and B states by size, scope, and audit mode. Memory is process peak RSS including fixture construction; it is a per-cell bound, not a component allocation.

## Claim boundary
This is a controlled one-rule vision factor with two roots, not a natural workload or a production scheduler. It tests scaling and instrumentation overhead for this factor only. The largest case has 512 SUnits total; it cannot justify extrapolation to 10⁷–10⁸ nodes or arbitrary rule interactions.
