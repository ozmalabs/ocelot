# Conversation route failure diagnostics v1.1 results

Two fresh, source-stable full-seed workers replayed the same five-prompt order.
The lock directly includes hashes for the dynamically imported
`scripts/arc_self_report.py`, language-world/production modules, task runner,
conversation action, reflective faculty, and world adapter, in addition to
the base source closure. All capture and independent analysis checks pass.

For scene description, `_ensure_describe` succeeds in both workers and
increases the native rule count by 22. `_act_describe_scene` is then entered but
returns `acted=false`, no reply, and the note “authored rule produced 0
request-owned parent Goals; expected exactly one.” `act_on_instruction` falls
through to `self_report`, mints a `report_self` Goal, and replies “I am
Jabberwock.” The failure is therefore after faculty construction and scene
dispatch, at request-owned Goal recognition/binding. The current data does not
establish why the authored Goal is not visible as request-owned to the host.

For concern authoring, no concern or generic action function runs. The native
interpretation is `kind=instruction`, `cognitive_disposition=repair`, with
`arbitration_basis=typed_unresolved_action_dependency`; `ask_back` then returns
“I don't know 'two' — what does it mean?” This may be correct because the
comparison target is not grounded. The existing concern-authoring contract
stimulus should be independently adjudicated before changing repair precedence.

The v1 capture lacked direct hashes for the dynamic `arc_self_report` import;
v1.1 closes that dependency gap for this diagnostic. These two workers diagnose
one fixed order only. Next inspect native installed-rule effects and Goal edge
creation for scene attribution, then adjudicate prompt validity and rerun the
counterbalanced panel with a complete dynamic source closure before using its
aggregate pass rate as a fully reproducible benchmark.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_CONVERSATION_ROUTE_FAILURE_DIAGNOSTICS_V1_1_PREREG_20261004.md)
- [V1 preregistration](SUBSTRATE_CONVERSATION_ROUTE_FAILURE_DIAGNOSTICS_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/conversation_route_failure_diagnostics_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/conversation_route_failure_diagnostics_v1_1_lock_20261004.json)
- [Capture](../../../evaluation/reports/conversation_route_failure_diagnostics_v1_1_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_conversation_route_failure_diagnostics_v1_1.py)
- [Independent analysis](../../../evaluation/reports/conversation_route_failure_diagnostics_v1_1_analysis_20261004.json)
