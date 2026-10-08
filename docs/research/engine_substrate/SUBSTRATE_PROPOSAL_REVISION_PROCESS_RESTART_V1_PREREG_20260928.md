# Proposal revision recovery across process restart v1

## Question

Does the substrate's graph/grammar/rule persistence round-trip preserve a partially completed proposal revision well enough for a fresh process to resume it and commit an oracle-correct result?

## Protocol

Three workers each run producer and resume as separate Python processes for N=2/16/64 and cutpoints after 0/1/2/3 max/count/decision stages. The producer completes revision 0, lowers the winner's score, creates revision 1, runs the requested prefix of stages, then serializes graph, grammar, exported rules, node IDs, and cut metadata to a JSON checkpoint. It flushes and `fsync`s the file before exiting. The resume process constructs a fresh Substrate, restores graph via `graph_from_dict`, replays grammar productions with `add_production_no_mirror`, imports rules with `import_rules`, verifies graph/grammar/rule parity, then resumes missing stages and commit based on revision stamps. A guarded consumer must not consume revision 1 before commit and must consume the final label afterward.

## Gates

Producer and resume PIDs must differ. The checkpoint must exist and its byte length/hash must match the manifest. Restored graph, grammar, and exported rule store must exactly match the producer snapshot before resume. Every closure reaches fixed point. No pre-commit consumption is present. Resume executes exactly missing stages and commits only with all stamps current. Final output matches an independent score oracle; one revision event remains. Integer work counts replicate across workers after timing fields are excluded.

## Limits

This tests a JSON checkpoint round-trip between local processes, not machine power-loss durability, fsync guarantees on every filesystem, concurrent writers, schema migration, torn writes, or in-closure partial-effect atomicity. The producer exits cleanly after saving; this injects a process boundary at closure cutpoints rather than killing the process during a native closure. Checkpoint serialization/deserialization costs and bytes are reported separately from native rule work.
