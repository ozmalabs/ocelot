# Live self-report lifecycle identity v1.5 amendment

## Reason

The describe-scene v1.1 integration changed shared `domains/reflective_faculty.py` rule-authoring code and `domains/conversation_action.py`. The earlier self-report v1.4 capture remains valid against its own lock, but no longer fingerprints the current tree. This amendment re-runs the unchanged self-report route protocol and five controls against the new shared-source state.

## Gates

Retain the original three fresh full-seed workers, two same-recipient self-report requests per worker, identity-linked selection/execution/result checks, terminal closure, and five controls (correct link, omitted link, swapped link, duplicate result, faculty failure). Require source hashes to match at worker start/end and post-run. Use new v1.5 artifact paths; preserve v1.4 as prior source-state evidence.

## Limits

This is a source-current regression confirmation of the existing held self-report route. It does not extend that route's semantic scope or establish concurrent execution, other action routes, external-effect authorization, workload prevalence, or scaling.
