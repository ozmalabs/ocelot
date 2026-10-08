# Live self-identity single-Goal integration v2 preregistration (2026-09-26)

## Question and change

The v1 route probe found that the held `instruction_self_report_identity` rule creates a generic event-bound Goal, after which `conversation_action.act_on_instruction` created a second targeted Goal to record the selected reflective action. The adapter now adopts the unique `report_self` Goal already linked to the inbound Message, fills its action target fields, and records selection, execution, and result on that same identity.

This probe tests whether the integration removes the duplicate unresolved Goal while preserving route distinctions and refusing to interpret an external-object instruction as self-report.

## Fixed prompt panel

All prompts use `speech_act="instruction"`, speaker `alice`, full seed boot, and the fixed order below within each fresh worker:

1. `describe who you are` — held-table question/meta route; no action Goal expected.
2. `describe yourself` — self-report instruction; exactly one `report_self` Goal targeted to `self_identity`, resolved by selection→execution→action_result.
3. `who are you` — direct meta question; no action Goal expected.
4. `tell me about yourself` — self-report instruction; same one-Goal lifecycle expectation as item 2.
5. `summarise the report` — external-object instruction; it must not produce a self-report route or `report_self` Goal.

## Evidence and gates

Run three workers in distinct fresh processes. Lock the runner, all Python sources under `domains`, `substrate`, and the native Python facade, all seed JSON (including generated seeds), native extension, build manifest, and commit. Require stable start/end fingerprints; repeated route signatures; the expected question/action dispatch classes; exactly one event-bound self-identity Goal for each action phrasing; resolved status and correctly linked ordered lifecycle events; zero `report_self` Goals for the external-object control; and nonempty replies for all five prompts. Report per-turn elapsed time as descriptive only; this protocol makes no cost or language-coverage claim.

Any identity mismatch, duplicate Goal, wrong target, unexpected external-object self-report, or source drift fails the confirmatory gate. Preserve the failed raw capture and diagnose before amending this protocol.
