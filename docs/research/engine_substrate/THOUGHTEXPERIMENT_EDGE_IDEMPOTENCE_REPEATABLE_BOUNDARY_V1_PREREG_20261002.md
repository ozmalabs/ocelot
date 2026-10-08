# Generic edge-idempotence boundary on repeatable replies v1 — preregistration

**Question.** Does an edge-derived `Not Exists(source, edge_type)` proposal incorrectly suppress legitimate repeated outputs, and does the graph evidence selector abstain when multi-message outcomes show that mismatch?

## Task and candidates

Use the real seeded `reply_to_adjacency_pair` rule through `WorldAdapter(seeds=())` plus its ordinary intent/reply seed loading. Fault it by removing the per-message `Not Exists(m responds_to)` guard. A generic AST transform scans `add_edge` effects whose source is bound by the rule match. Since `agent.sent` targets a newly created reply (not a bound target), the transform can only propose a coarse `Not Exists(agent.sent)` guard. Include the general composer’s fixed `add_match_guard` as a second hypothesis. Do not call `_default_candidates` or provide a conversation-specific repair.

Each of four fresh workers evaluates both proposals on two training sequences of two inbound messages. The independent oracle requires one reply linked to each inbound. Feed only the resulting correct/incorrect labels and opaque proposal IDs to `select_candidate_from_graph_evidence` in an isolated snapshot. Freeze the decision before held-out evaluation. Held-out sequences contain three different response-expecting speech acts; score the source-rule positive control and the rejected coarse guard diagnostically, without adopting it.

## Gates and interpretation

- The unmodified source rule passes the per-message reply oracle in both training and held-out sequences.
- The generic transform emits exactly the coarse agent-level guard; the fixed composer proposal is distinct.
- Both fault-repair proposals fail the two-message training oracle; the graph selector abstains on all-wrong evidence.
- On held-out three-message sequences, the unmodified source still returns one reply per input; the generic coarse guard returns fewer than required and is recorded as a false suppression diagnostic.
- The source/native fingerprint, task inputs, candidate descriptors, source rule preservation, and branch evidence isolation are checked.

This measures a failure boundary for one authored conversation rule. It does not establish false-suppression rates across natural tasks or evaluate an automatically learned key. The new-node target is intentionally unbound, which is why the generic source/edge guard is too coarse; a reusable operator must represent edge identity or per-input scope, and must be selected against multi-input evidence.

Capture orders and training outcomes first, then held-out diagnostics, then run the independent analyzer.
