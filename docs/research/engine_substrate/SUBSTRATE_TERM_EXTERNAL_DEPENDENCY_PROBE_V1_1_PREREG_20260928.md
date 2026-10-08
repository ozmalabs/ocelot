# Term external-dependency probe v1.1 preregistration

Date: 2026-09-28

## Question

How does successful `UseTool` callback work change with the number of matching bindings, and does placing the callback Term first or last among rule effects change invocation counts or final graph state?

This is a scale extension of v1's one-match result. It does not test callback authority, containment, natural frequency, or callback behavior that mutates the substrate.

## Locked panel

Run six cells per worker: match cardinality `M ∈ {1, 2, 4}` crossed with callback effect position `{first, last}`. Each synthetic graph has one source and M targets joined by the same `trigger` edge. One rule writes a fixed-return `UseTool` result and a separate literal marker to every matched target. Effect order changes between the two positions; the handler itself only appends a constant argument to a local list and returns a fixed string.

Use three fresh processes and a source/native lock. Enable native access tracing throughout each settle. Record callback invocations, native successful-fire counter delta, dispatch trace count, progress, final graph, declared `RuleKey` set, elapsed wall time, and worker streams. Do not infer work from graph progress alone.

## Gates

- Three fresh PIDs use identical locked inputs and reproduce exact final graphs and per-cell callback/fire/dispatch/progress counts.
- For every cell, callback invocations equal successful native fire-count delta and `term_tool_dispatch` trace count; there are no trace drops.
- The rule remains declared `reads_any=true` with `edge:trigger` in its finite read list.
- The graph has M matched targets, each with the fixed tool result and literal marker; progress is positive.
- Report the empirical callback count by M and effect position, both per settle and normalized per matched target. No linearity or position-invariance threshold is assumed.

Any worker disagreement, trace/callback mismatch, or state mismatch fails the gate and is preserved. The v1 observation of two calls at M=1 is not used to manufacture an expected scaling law; v1.1 estimates the curve under this frozen panel.

## Claim boundary

This authored one-rule family measures only `UseTool` in a rule effect with deterministic local callback behavior. It does not establish a general callback bound, behavior for matching predicates or nested calls, costs of real host work, or natural task prevalence. Elapsed times are descriptive at this scale and are not a performance claim.

## Artifacts

Runner: `scripts/substrate_term_external_dependency_probe_v1_1.py`  
Independent analyzer: `scripts/analyze_term_external_dependency_probe_v1_1.py`  
Lock: `evaluation/substrate_capability/term_external_dependency_probe_v1_1_lock_20260928.json`  
Raw capture: `evaluation/reports/term_external_dependency_probe_v1_1_20260928.json`
