# Thoughtexperiment rule activation v1 preregistration

## Question

Can a candidate selected and held-out validated in the cross-family CoW
experiment be installed into a fresh task substrate with an atomic semantic
revision check, and does the installed rule preserve the measured repair?

## Design and gates

Use the locked candidate generators for recurrence and conversation, four
workers per family. The candidate is the previously unique training winner in
each family. In a fresh faulted context, capture the graph/rule revision,
replace the named target rule through
replace_active_rule_by_name_if_revision, then rerun the task. Require the
expected output and the successor rule active in the primary rule store.

For each family/worker, also attempt a stale revision after a graph mutation
and malformed rule JSON at a current revision. Both must fail without
changing the exported rule store. Hash all runner, analyzer, protocol, helper,
candidate, native Rust/Python API, task and build sources before capture and
require identical hashes afterward.

This gate evaluates rule-store activation after an externally specified
candidate has passed an external held-out oracle. It does not test autonomous
authorization, candidate/fault discovery, rollback after later task
regression, persistent multi-task utility, or concurrent semantic policy.
