# Rule-edge scope crosswalk v1 results (2026-10-03)

## Outcome

The post-hoc source/data reconciliation passes its integrity checks. In the
12-case conversation access-trace panel, the recorded graphs contain 90
direct cross-frame `follows_event` edges. The runtime traces record 6,240
weighted accesses from four `discourse_goal_*` rules, with 720 same-frame
endpoint accesses and 5,520 accesses between one frame-owned endpoint and
shared/unowned state. No direct different-owner access is observed, and none
of the 6,240 accesses reads `follows_event`.

That trace coverage is intentionally narrow: the panel's `base_world()` loads
only `conversation_discourse_state`. The four observed lifecycle rules match
`has_active_goal`, `originated_in`, `has_event`, and `for_goal`, and update
`transitioned_by`, `has_active_goal`, and `has_closed_goal` as appropriate.
Their traces are useful evidence for goal-local lifecycle work through shared
state, not evidence that cross-frame event dependencies are absent from the
wider substrate.

A source scan of the other relevant seeds finds three multi-edge rules that
do read `follows_event`:

| Rule | Seed | Match edges | Predecessor dependency |
|---|---|---:|---|
| `carry_scoped_action_target_across_topicless_event` | `communication_intent_arbitration` | 8 | Current event to prior event, with same speaker/addressee and prior scoped target |
| `ground_definite_correction_from_scoped_action_target` | `communication_intent_arbitration` | 9 | Current correction event to prior event and its grounded action target |
| `answer_from_immediately_preceding_reported_relation` | `communication_reported_content_recall` | 9 | Current question event to source event, followed through message and interpretation links |

None of these three appears in the 12-case dynamic trace panel. The first two
have event-index join hints, but none declares the `scope_anchor_var` /
`scope_anchor_type` metadata used by the scoped multi-edge optimization audit.
Their seed matches make the predecessor dependency explicit at the rule level;
the present crosswalk does not measure their runtime frequency or end-to-end
scope behavior.

## Interpretation

The typed census and this rule crosswalk together show why a projection-only
frame argument is incomplete. In the selected conversation graphs,
`follows_event` is the only direct disjoint-frame edge type. Existing traced
goal lifecycle rules access shared state without cross-reading another owned
goal. Separate available rules, however, explicitly bind an event to its
predecessor and traverse data from that earlier frame. A partition that drops
the predecessor event can therefore lose a valid rule binding even when the
local frame closure is otherwise exact.

The next runtime gate should load and execute these predecessor-dependent
rules in a paired monolithic/scoped harness. Include positive predecessor
continuity, wrong-speaker/addressee, intervening-topic/action, missing and
reordered predecessor, plus omitted-predecessor-scope controls. Verify exact
rule bindings, graph/effect parity, and fallback behavior; record both scoped
candidate work and predecessor-edge/index-join work. Until then, the prior
access trace supports only the four selected lifecycle rules.

## Reproduction and provenance

Run the reconciliation from the repository root:

```sh
python3 evaluation/substrate_capability/analyze_substrate_rule_edge_scope_crosswalk_v1.py
```

The output records SHA-256 digests of the raw trace, trace lock and analysis,
typed census capture and analysis, relevant rule seeds, and trace runner.
The trace panel's own source lock and independent analysis passed; the typed
interaction census independently reconstructed all 78 rows with zero errors.
See [crosswalk analysis](../../../evaluation/reports/substrate_rule_edge_scope_crosswalk_v1_analysis_20261003.json), [typed census results](SUBSTRATE_TYPED_FRAME_INTERACTION_CENSUS_V1_RESULTS_20261003.md), and [conversation access-trace results](SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_3_RESULTS_20261003.md).
