# Varied-topology transport solver v1.1 amendment

Date: 2026-10-03

The v1 runner and lock preserve the original full-grid design. A direct single-worker diagnostic of its worker function was manually stopped at an operational 60-minute cutoff without a completed result or a partial capture. The worker emitted only one serialized result after all 320 cases, so the attempt provides no per-component timings and does not establish a solver runtime or complexity bound. The earlier full-panel launcher was also interrupted before capture; neither attempt is confirmatory.

V1.1 keeps the same 320 unique cases, graph/factor semantics, graph-only minimum-separator search, exact conditioning, junction-tree comparator, and three-worker target. It improves measurement observability and avoids reloading the same seed manifest for every case: each worker loads the seed once, then constructs each case as a separate microtheory in the same substrate. Cases have disjoint node sets and are read only by their own microtheory. The worker writes a flushed JSONL checkpoint after each case and progress messages after each hop/fan-in block. Seed initialization is timed separately and charged to both routes when calculating batch cost. The complete per-worker result is still source-locked and independently analyzed.
