# Live self-identity reply-release integration v3 preregistration (2026-09-26)

## Question and changes under evaluation

V2 established one identity-bound Goal, but an additional readback found that the action faculty's released surface was not the surface selected by `chat_transcript`; an earlier graph-authored candidate remained outbound. A controlled reflective-faculty failure also allowed that candidate to surface without a production receipt.

The adapter now records the graph rule's reply candidate on its owning Goal. On successful self-report, the action reply's production receipt is linked to the Goal and the exact outbound Message; that Message becomes the selected action surface and retains the prior candidate text for audit. On a self-report faculty failure, the candidate is marked suppressed and the explicit error surface is returned.

## Fixed panel and controls

Use full seed boot and run three fresh worker processes. In each, send in order:

1. `describe who you are` — table/meta question, no action Goal.
2. `describe yourself` — one resolved identity Goal; transcript, returned surface, and receipt surface must match; receipt commits the Goal and outbound Message.
3. `who are you` — direct meta question, no action Goal.
4. `tell me about yourself` — same success gates as item 2.
5. `summarise the report` — external-object negative; no self-report Goal.
6. Inject a reflective faculty exception for another `describe yourself` turn. The Goal must be blocked by selection→execution→action_failure; the surface must be the canonical explicit error; the transcript must show that same error; the graph candidate must be suppressed and absent from outbound messages; no released receipt may claim the candidate or failed action surface.

## Gates and provenance

Require three distinct PIDs, stable full-source fingerprints including the native artifact, repeated route/ownership signatures, exactly one event-bound report_self Goal per successful self-report, receipt-linked exact output, unchanged question/meta routing, external-object rejection, and the injected-failure behavior above. Lock source files and seeds, runner, native extension, build manifest, protocol, and commit. Timings are descriptive; no language coverage or tractability claim is made.

Any mismatch, duplicate Goal, unreceipted outbound success surface, surfaced failed candidate, or source drift fails the run. Preserve the failure capture and amend before changing gates.
