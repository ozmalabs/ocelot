# Budget-cut proposal revision process restart v1

## Question

Does a fresh process recover a guarded proposal pipeline after `run_rules_report(max_steps=1)` returns mid-sequence, and does persistence leave an unguarded false commit incorrect?

## Protocol

Three workers run N=2/64 with three arms: reverse-order guarded, reverse-order unguarded, and normal-order guarded. The producer settles revision 0, lowers its winner's score, creates revision 1 with max/count/decision/commit stages all present, then runs one `max_steps=1` closure. It checkpoints graph, grammar, exported rules, IDs, closure report/counters, and target state to an fsync'ed JSON file and exits. A fresh process restores graph/grammar/rules, checks exact graph/grammar and semantic rule parity (canonicalized match-clause order and derived content hash), then settles with a large budget. A consumer copies output only when all stage stamps, resolved revision, and event revision agree; it stamps the consumed revision.

## Gates

Producer/resume PIDs must differ; checkpoint byte length/hash and graph/grammar/rule restoration must verify. Guarded reverse order must retain the prior resolved/consumed revision after the budget cut and recover to the oracle winner after restart. Normal guarded order is a correct positive control. Reverse unguarded order is an expected false-commit control: it must persist the wrong selection and remain wrong after restart/full settle. Integer counts replicate across workers ignoring timing. Checkpoint files are retained.

## Limits

This uses one JSON checkpoint path and clean process exits after the budget-limited closure; no OS kill inside native code or power-loss guarantee is claimed. Only one graph family, mutation, rule order pair, and two sizes are tested. Readiness guards are authored policy, not engine-enforced structure.
