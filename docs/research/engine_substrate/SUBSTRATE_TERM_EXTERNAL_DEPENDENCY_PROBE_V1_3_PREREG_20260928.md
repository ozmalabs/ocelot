# Term external-dependency replay/order probe v1.3 preregistration

Date: 2026-09-28

## Question

When two rules share a stateful `UseTool` predicate that returns true only on its first invocation, does rule insertion order determine which effect commits? After settling, does resetting only the callback's external state cause a second `run_rules` call to re-evaluate the predicate?

## Frozen design

Run two schedules in each of three fresh processes: rule order `[rule_a, rule_b]`, then `[rule_b, rule_a]` in a fresh substrate. Both rules match the same single trigger edge, call the same registered handler in `where`, and write their own marker. The handler logs calls and returns `true` only on its first call, then `false`. After the first settle, clear only the handler's local call log, leave the graph unchanged, clear trace rows, and call `run_rules` again.

Record per-run progress, callback results, callback/native-fire counts, trace events by RuleUID, static read sets, and full graph state. Run three fresh processes under a source/native lock. The runner must refuse to overwrite an existing raw capture; reproductions must choose a new output path.

## Pilot-frozen expectations

The exploratory pilot observed these outcomes, now frozen for confirmatory replication:

- First settle: exactly three callback calls in order `[true, false, false]`; the first inserted rule calls twice, the second calls once; progress is 1; only the first rule's marker is written.
- Reverse insertion order: the other rule wins, with the same three-call schedule.
- Both rules have `reads_any=true` and finite `edge:trigger` access.
- After clearing the handler's local state but changing no graph data, the second settle returns progress 0, invokes no callbacks, emits no new trace events, and preserves the graph exactly.
- Callback invocations equal successful native fire-count deltas and dispatch trace counts; no trace events are dropped.
- All outcomes replicate exactly in three fresh processes.

Any deviation fails the gate and is retained. The pilot-derived schedule is explicitly fixture-specific; this panel does not infer global scheduler order or a general memoization contract.

## Claim boundary

This is a synthetic two-rule example of order-sensitive stateful predicates and graph-only settle invalidation. It does not establish natural frequency, justify stateful predicates, test true host actions, or generalize to all rule engines and scheduler modes. The result will inform a design decision about callback purity/declared effects and external invalidation; no engine semantics change is authorized by this measurement alone.

## Artifacts

Runner: `scripts/substrate_term_external_dependency_probe_v1_3.py`  
Independent analyzer: `scripts/analyze_term_external_dependency_probe_v1_3.py`  
Lock: `evaluation/substrate_capability/term_external_dependency_probe_v1_3_lock_20260928.json`  
Raw capture: `evaluation/reports/term_external_dependency_probe_v1_3_20260928.json`
