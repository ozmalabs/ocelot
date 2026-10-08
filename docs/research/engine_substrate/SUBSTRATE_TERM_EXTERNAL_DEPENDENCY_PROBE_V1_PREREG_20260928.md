# Term external-dependency probe v1 preregistration

Date: 2026-09-28

## Question

What graph-access declarations and native trace events accompany a rule whose effect evaluates `ReadFile` or `UseTool`, and how many times does the engine invoke a tool callback during one fixed-point settle?

This probe measures the engine boundary only. It does not test path containment, tool authorization, operating-system isolation, or general host-effect safety.

## Locked design

Use a synthetic one-match graph and one rule that writes the evaluated Term result to a matched node. Run each cell in a fresh Python process, with three processes total. Each worker records source/build hashes, rule access sets, progress, final graph, callback/fire counts, trace rows, and dropped events.

Cells:

1. Existing file with content `alpha`, then the same fixture with content `beta`, both with tracing enabled.
2. Missing file with tracing enabled.
3. Registered `probe` handler returning a fixed string, tracing enabled and disabled.
4. Missing `probe` handler, tracing enabled.

The tool callback increments a process-local counter and returns a fixed value; it does not access the substrate or perform I/O. All filesystem paths are newly created inside a temporary directory. The native handler registry is cleared between tool cells.

## Preregistered checks

- All workers use the same locked sources/native binary and finish without trace drops.
- File-content cells write their exact content to graph state; the two results differ although their graph fixtures and static rule access declarations match. The static rule set has only the trigger-edge dependency and `reads_any=false`; runtime traces contain no file-read event. The missing-file cell produces the evaluator's `None` result.
- The successful tool rule has `reads_any=true`. Fixed-return callbacks fire twice per settle in this one-rule fixture, while graph state settles after one progressing application. The trace contains two `term_tool_dispatch` events per settle; disabled tracing changes neither callback count nor result and emits no events.
- The missing-handler cell records dispatch attempts but zero successful native handler fires and writes the evaluator's `Int(0)` fallback.
- Report callback invocations, native fire-counter deltas, dispatch event counts, and graph outcomes separately; do not treat them as interchangeable measures.

The exact two-call expectation follows the current evaluator/fixpoint path established in an exploratory pilot; this probe freezes that behavior for confirmation. A mismatch is reported as a failed gate, not normalized away.

## Claim boundary

Positive results show that graph access sets and the selected trace do not account for filesystem contents or handler-internal effects. They do not establish frequency in natural workloads, containment, safe authority, complete tracing, or a general callback-call bound. `ProgCallExtern` is excluded from dynamic host cells because source audit found that the current Program IR path calls an in-engine Rust oracle whitelist.

## Artifacts

Runner: `scripts/substrate_term_external_dependency_probe_v1.py`  
Independent analyzer: `scripts/analyze_term_external_dependency_probe_v1.py`  
Lock: `evaluation/substrate_capability/term_external_dependency_probe_v1_lock_20260928.json`  
Raw capture: `evaluation/reports/term_external_dependency_probe_v1_20260928.json`
