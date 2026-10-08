# Conversation route failure diagnostics v1.1 preregistration

Date: 2026-10-04

This version repeats the v1 two-worker route diagnostic with explicit hashes
for dynamically imported production dependencies. The v1 lock audit showed
that `BASE.inputs()` did not include `scripts/arc_self_report.py`, even though
the scene path imports it at runtime. V1.1 directly locks
`domains/conversation_action.py`, `domains/reflective_faculty.py`,
`substrate/world_adapter.py`, `scripts/arc_self_report.py`,
`domains/language_world.py`, `domains/language_production.py`, and
`scripts/language_test.py`, in addition to the base runtime source closure,
runner, analyzer, and protocol hashes. The capture method and diagnostic
interpretation follow v1 unchanged.

The question remains where scene-description processing fails between faculty
build, authored rule firing, Goal-to-request binding, and fallback; and which
native repair disposition preempts concern authoring. Wrappers are no-op and
must preserve return values. Two fresh full-seed workers replay one fixed
five-prompt order. The result is limited to this fixture and does not establish
intent validity or prevalence.
