# Conversation partition API fit audit — 2026-10-03

## Finding

The existing `run_rules_scoped` path is not an implementation of task-frame partitioning for the connected-conversation workload. Its scope unit is a Microtheory (`scope_mt`), and `mt_owned_nodes` defines ownership as that Microtheory node plus one `has_concept` hop. A rule binding is retained when at least one bound node touches that owned set. The conversation workload instead has one `DiscourseState` per conversation, multiple goals and events labelled into task frames by the evaluation harness, and shared state accessed by all frames. Those labels are measurement metadata; they do not create separate Microtheory-owned regions.

The delta-reporting API also declares `frame_notifications_complete: false`; its documentation says deferred effect queues are surfaced rather than drained. Therefore a result from repeated per-frame calls cannot currently be interpreted as a settled partitioned fixpoint unless the experiment independently demonstrates queue quiescence and complete notifications. Applying the existing API to the single shared discourse Microtheory would scope the whole conversation, not partition it. Splitting or duplicating the shared state would change the workload semantics and cannot be treated as an equivalent optimization.

## Evidence

- [`Substrate::run_rules_scoped`](../../../runners/dsl/src/substrate.rs) passes one Microtheory ID to the scoped rewrite runner.
- [`mt_owned_nodes` and `run_rules_opts_scoped`](../../../runners/dsl/src/rewrite.rs) define ownership by `has_concept` adjacency and post-match binding touch; this is not arbitrary task-frame ownership or a boundary-factor interface.
- [`run_rules_scoped_delta_report`](../../../runners/dsl/src/substrate.rs) reports pending deferred effects and explicitly marks frame notifications incomplete.
- [`ensure_discourse_state`](../../../domains/discourse_state.py) creates/reuses one state node per conversation. `record_event` updates shared event index and topic/expectation fields and links events through a shared predecessor chain. The v1.3 access panel finds that most observed rule accesses touch task-owned events/goals and shared/unowned state.
- [Connected-conversation access trace results](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_3_RESULTS_20261003.md) show traced/untraced state parity but explicitly do not establish partition safety.

## Gate decision

The first [task-scope parity pilot](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_RESULTS_20261003.md) now shows that an experimental ownership encoding can use two seed-provided Microtheory roots, symmetric `has_concept` membership edges, and repeated global resweeps to match monolithic closure on one two-goal case. The edges require unchecked insertion and all scopes are rescanned; this is not ordinary validated ownership, learned partitioning, or an optimized interface scheduler. Keep this pilot as a narrow parity positive control. Next broaden exact parity to common-ground stress, 4/8-goal cases, dynamic owner updates, deletion/reuse, and adversarial cross-frame dependencies. Add read/matcher-work accounting and charge ownership annotation, boundary exchange, requeueing, scheduling, and memory. Keep a negative control where an omitted shared-state dependency must be detected or cause refusal. Require exact graph, goal, event-order, and lifecycle parity; quiescent deferred queues; and complete notification accounting before treating any partition as safe.

This is an API-fit result, not evidence that a new partition engine is impossible or that partitioning would be faster. It narrows the implementation seam and prevents the existing narrower Microtheory scope from being mistaken for a general factorization capability.

## Expanded pilot update — v1.2

The follow-up now creates task-specific Microtheory roots and reaches exact state parity on 2/4/8 concurrent goals and a four-frame common-ground stress case. It confirms that the ownership representation can scale past the two seed roots when native node insertion is used and task memberships are attached as unchecked annotations. At every checkpoint, the runner resweeps all scopes until global quiescence and verifies each scope reports no pending deferred work; the API's notification-completeness flag remains false. The selected cases still run the full-graph matcher once per scope call, and measured scoped cost grows with the number of calls. See [v1.2 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_2_RESULTS_20261003.md). Next work should make ownership edges ordinarily admissible or define a first-class ownership API, instrument actual matcher/read work, and add the explicit `term.rs` source lock and independent matrix validation before a confirmatory expansion.
