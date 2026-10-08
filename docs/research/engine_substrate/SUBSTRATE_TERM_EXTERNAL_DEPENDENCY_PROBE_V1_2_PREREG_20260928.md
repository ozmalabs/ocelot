# Term external-dependency probe v1.2 preregistration

Date: 2026-09-28

## Question

How often does a `UseTool` callback execute when used in rule predicates, nested short-circuit Terms, and multiple rules, including when callback results depend on callback-local state?

This is a source-locked mechanism probe extending v1/v1.1. The callback only records its arguments and returns booleans; it performs no filesystem access, substrate reentry, or other host action.

## Frozen panel

Each fresh worker runs these five synthetic rule cells on one `x --trigger--> y` graph:

1. Direct predicate: `UseTool` always returns `true`; one rule sets one marker.
2. Short-circuit before callback: `And(false, UseTool)`; callback should not run.
3. Short-circuit after callback: `And(UseTool, false)`; callback runs but the rule does not fire.
4. Multiple rules: two independent rules each use direct `UseTool(true)` and set distinct markers.
5. Stateful predicate: `UseTool` returns `true` on its first invocation and `false` on its second; one marker effect records whether the first result led to an application.

Run three fresh processes, tracing enabled, with identical source/native lock. Capture per-call arguments and returns, successful native fire delta, dispatch trace counts by RuleUID, static access sets, progress, final graph, and worker stdout/stderr hashes.

## Confirmatory expectations and gates

These exact counts and states were observed during an exploratory pilot and are frozen here for confirmation:

| Cell | Callback returns | Callback calls / dispatches | Progress | Marker |
|---|---|---:|---:|---|
| Direct predicate | `true, true` | 2 | 1 | written |
| False before callback | none | 0 | 0 | absent |
| False after callback | `true` | 1 | 0 | absent |
| Two direct predicate rules | two `true` per rule | 4 total (2 per RuleUID) | 2 | both written |
| Stateful direct predicate | `true, false` | 2 | 1 | written |

For all cells, callback invocations must equal native successful-fire delta and traced dispatch counts; there must be no dropped events. Every rule reports `reads_any=true`. All three workers must reproduce cell outcomes exactly. Any mismatch fails the gate and is retained.

## Claim boundary

This establishes only the specified callback and Term evaluation behavior. It does not establish safe semantics for real side effects, arbitrary callback behavior, other matcher/scheduler paths, or natural callback prevalence. In particular, first-true/then-false behavior is an explicit stateful predicate example, not a recommended use pattern. Counts are not a general complexity bound.

## Artifacts

Runner: `scripts/substrate_term_external_dependency_probe_v1_2.py`  
Independent analyzer: `scripts/analyze_term_external_dependency_probe_v1_2.py`  
Lock: `evaluation/substrate_capability/term_external_dependency_probe_v1_2_lock_20260928.json`  
Raw capture: `evaluation/reports/term_external_dependency_probe_v1_2_20260928.json`
