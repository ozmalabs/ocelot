# Conversation route failure diagnostics v1.2 preregistration

Date: 2026-10-04

Repeat v1.1 with the same two-worker, five-prompt order and explicit dynamic
source hashes. Extend the no-op wrappers to retain the active native export of
`comprehend_describe_directive_*` immediately after `_ensure_describe`, and to
record every newly created `Goal{kind:describe_scene}` across
`_act_describe_scene`, including its attributes, `describes` edges, and the
Message IDs on its `comprehends` edges. Keep reply values and direct call order.

This separates a missing installed-rule effect from a native rule that mints
the Goal but fails to bind it to the inbound Message. Compare the native export
to the locked `reflective_faculty.py` composer source and verify observations
across two workers. The measurement is diagnostic for the selected prompt and
does not change rule bodies or route results.
