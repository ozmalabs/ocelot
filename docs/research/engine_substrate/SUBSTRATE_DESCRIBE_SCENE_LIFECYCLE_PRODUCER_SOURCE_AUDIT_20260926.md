# Describe-scene lifecycle producer source audit

## Scope

Static review of the attached-scene `describe_scene` route in `domains/conversation_action.py` and its rule-authored Goal producer in `domains/reflective_faculty.py`, reached through `scripts/arc_self_report.py`. This is a source audit, not a live-run result or a claim about unrelated routes.

## Findings

1. `act_on_instruction` selects `_act_describe_scene` for perception-cued self-report requests when a scene is attached, and can also fall back to that route for other self-report verbs with an attached scene.
2. `_act_describe_scene` invokes `world_receive` and native rule closure; those rules mint a `describe_scene` Goal and `produce_utterance` subgoals. The subgoals are produced per percept, so one inbound request may create multiple child Goals.
3. The host then searches the entire graph for nodes whose `kind` is `describe_scene`, takes `goals[-1]`, and binds only that Goal to the inbound Message. This is an order-dependent lookup, not an identity-bearing producer edge. It is ambiguous when multiple matching Goals exist or graph enumeration order changes.
4. This route does not call `_record_live_goal_event`; no source path in `_act_describe_scene` records Goal-bound `selection`, `execution`, `action_result`, or `action_failure` events. The self-report lifecycle integration does not cover it.
5. `attach_scene` independently invokes native rules for scene materialization and writes a receipt; that receipt describes scene ingestion and is not an action lifecycle receipt.

## Tractability and capability implications

The route has a plausible local unit (one inbound request, one scene, a parent Goal, and its child utterance Goals), but the current parent binding depends on a global scan and “last item” convention. Before measuring route latency or scaling, the owner relation must be made explicit and tested with overlapping requests. Child Goal ownership also needs a defined policy: whether lifecycle applies only to the parent action Goal, to each utterance subgoal, or to both with distinct lifecycle types.

## Next evidence gate

1. Add a preregistered live baseline with two independently identified inbound requests against an attached scene, capturing before/after Goal inventories and every origin/comprehends/lifecycle edge.
2. Test whether request A and request B bind to their own parent Goals when their rule-produced Goal sets overlap in time or are deliberately interleaved.
3. Specify the lifecycle owner and event vocabulary for parent versus child Goals before changing producer code.
4. Only then integrate the producer and repeat source-locked semantic controls, including a missing/ambiguous owner negative control.

The repeated-request probe confirmed the source-predicted failure: the second request reused the first scene-level parent Goal. The v1.1 bounded integration now passes three source-stable repetitions: it uses a request-scoped scene view, the actual inbound Message, an explicit rule-authored Goal-to-Message link, unique-new-Goal selection, parent-only lifecycle, and per-parent utterance subgoals. The initial failure is preserved ([baseline result](SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_RESULTS_20260926.md)); the integration is confirmed separately ([v1.1 results](SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_1_RESULTS_20260926.md)). Next validate negative owner behavior, then test overlapping/interleaved requests before generalizing beyond sequential operation.

No producer code change is included in this audit or the baseline probe. The current self-report route result remains bounded to its tested route.
