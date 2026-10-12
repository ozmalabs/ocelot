# Live conversation capability panel v1 preregistration (2026-09-27)

## Question

On current full-seed `WorldAdapter` boots, which distinct conversation capabilities complete their observable task contracts, and how do their cold boot/request CPU, wall time, memory, rule growth, route choice, and Goal/reply evidence compare?

## Task conditions

Two fresh processes per condition, with no prior conversation turn in the worker:

1. **Scene description:** attach the standard grey/yellow/blue scene; `describe what you see` as a statement. Require exact expected description and resolved request-bound `describe_scene` Goal.
2. **Held self-knowledge answer:** `How are you organised?` as a question. Require a non-question reply containing `organis`, following the existing repository behavior contract.
3. **Self-report action:** `report your organisation` as a statement. Require nonempty substantive reply and a resolved request-bound `report_self` Goal through selection/execution/action-result.
4. **Unknown-word clarification:** `quorplezap the door` as a statement. Require a reply quoting `quorplezap`, ending in a question, plus a graph-linked agent Message responding to the inbound, marked as an expected response and carrying clarification speech-act evidence.
5. **Concern authoring:** `Compare where the two letters differ and judge the trial on that region.` Require a nonempty reply from the `concern_authored` route, no honest goal-only dead-end response, and zero self-teacher calls.

Run ten unique full-seed processes in the fixed schedule encoded by the runner. Lock the complete runtime closure/native build before and after each worker. Record full-seed boot and task wall/CPU, RSS/high-water, native rule delta, selected action route when the action bridge is used, inbound interpretation/communication route, Goals/events, reply commitment, outbound Messages, and teacher-call count. No rule access trace or graph-wide dump is enabled.

## Gates and reporting

- Ten unique processes, two per condition, identical source locks and no worker lock drift; full seed boot reports its loaded and failed manifest counts.
- Evaluate each condition only against its own task contract. A condition failure remains a failure; do not make pooled success rates from missing or invalid workers.
- Preserve per-worker evidence and report per-condition results, wall/CPU ranges, rule deltas, boot costs, and peak RSS. Do not compare one-turn cold worker timings with cached multi-turn timings as if paired.

## Scope limits

This is a selected prompt panel based on existing repository behavior contracts, not an independent benchmark suite, population sample, human evaluation, or measure of capability breadth. It does not establish natural prevalence, external-world accuracy, rule necessity, frame locality, or scaling. Its purpose is current-source route and measurement integration across distinct live conversation tasks.
