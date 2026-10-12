# Direct `parse_rule_json_pub` rollback probe

**Question.** Does the public Rust rule-JSON parser wrapper restore both the TermArena suffix and interner suffix after a late parse failure, and does a valid parse still work afterward?

## Procedure

Compile and run `runners/dsl/examples/parse_rule_json_rollback_probe.rs` through Cargo. On one fresh `TermArena` and `Interner`, repeat the same malformed rule 25 times. The rule first parses a valid literal Term and interns its match/name strings, then fails on an unknown second Term node. After every error, require exact equality with the initial arena-node and interner-entry counts. Finally parse a valid control and require the rule name and allocated state to be available. The protocol, runner, example, crate manifest/lockfile, parser, JSON Term decoder, TermArena, and interner sources are hash-locked before the confirmatory run.

## Limits

This checks one late error shape and successful reuse in one process. It does not test every malformed rule path, concurrency, Python exception mapping, or codec manifest failure injection. The first unregistered `cargo run` was an exploratory smoke check; the locked runner records a separate confirmation. This is correctness evidence, not a performance or capability result.
