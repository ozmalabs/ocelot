# Program IR candidate-snapshot transfer v1 preregistration

## Question

Does the substrate's ordinary Rung 3 program-synthesis route acquire an executable Program/IR inside an isolated candidate snapshot, and does that representation remain executable with identical held-out behavior in eager-copy and shared-graph-page CoW child branches?

This is an independent object-level family from GenMint: scalar integer program synthesis using the default numeric grammar. It tests graph-resident Program/IR lifecycle and exact execution, not natural-task capability, formal P3-E1, substrate meta-learning, or adoption.

## Fixed tasks, controls, and schedule

Use two clamp tasks with exact oracle `min(max(x, low), high)`:

| Task | Bounds | Six training pairs | Six held-out inputs |
|---|---:|---|---|
| `clamp_0_5` | `[0,5]` | `(-2,0),(0,0),(1,1),(4,4),(5,5),(7,5)` | `-6,-4,-1,2,6,9` |
| `clamp_neg2_4` | `[-2,4]` | `(-5,-2),(-2,-2),(-1,-1),(1,1),(4,4),(7,4)` | `-8,-3,0,2,6,9` |

Run five fresh worker processes per task (10 total), in a fixed randomized task/replicate order. In each worker, boot one empty base snapshot and record its canonical digest. Create three independent branches:

1. **Candidate:** shared-graph-page fork; ingest the task and run the standard `ensure_program_synthesis → ingest_spec → pump` route. Retain the acquired graph-resident Program and its IR root in an immutable candidate snapshot. Evaluate all held-outs from child branches made by eager full copy and shared-graph-page CoW, without mutating the candidate snapshot.
2. **Frozen:** eager-copy branch from the pre-training base, with no examples or synthesis; report that no executable candidate is available (score 0/6 coverage, not a wrong numeric prediction).
3. **Exposure without consolidation:** shared-graph-page branch receives the same task request and examples through `ingest_spec`, but does not run `pump`; evaluate and report whether an executable Program exists. It must not be silently promoted to the candidate arm.

For every available candidate, evaluate its stored IR using native `ProgEval` on the six held-out inputs, including values outside the training range. Recompute the exact clamp target independently. Any accepted Program that traps, lacks one IR root, or returns a wrong result is an accepted false generalization for that input.

## Measures and gates

Record synthesis status/rung, Program/IR counts, exact oracle output on each held-out, acquisition and branch costs, rule-closure/pump wall and CPU time, peak RSS, graph/grammar/rule digests, and source/extension hashes. Report acquisition rate separately from exact conditional transfer and exact coverage over all 10 workers. Report frozen/exposure capability availability without converting absence into numeric prediction errors.

Integrity gates: exact task/input/order reconstruction, 10 unique worker PIDs, current source/native lock, no worker errors, pre-training primary unchanged after candidate work, candidate snapshot unchanged by either evaluation child, no executable Program in frozen or exposure-only controls, exactly one candidate Program/IR root for each accepted candidate, and exact eager/shared parity on status, traps, outputs, and graph-resident candidate identity. The independent analyzer recomputes every oracle label and all semantic summaries from raw rows.

No adoption occurs. This panel can establish bounded executable-structure acquisition and isolated transfer on the two registered clamp tasks only. CoW timings are descriptive unless a separate performance protocol is preregistered.

## Reproduction

Preserve the source/native lock before capture, then run the worker-panel runner and the separate analyzer. Record the exact commands and all artifacts in the results document.
