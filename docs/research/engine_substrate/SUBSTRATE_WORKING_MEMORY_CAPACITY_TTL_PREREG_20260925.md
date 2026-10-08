# Preregistration: working-memory capacity, replacement, and expiry

**Question.** Do the graph-authored working-memory gates enforce the configured slot limit, refuse same-task overflow, replace only a lower-priority foreign-task slot when full, and expire slots at the configured epoch boundary unless maintained?

**Workload.** Each scenario runs in a fresh process with `episodic_working_memory_core`. The policy's `maximum_slots` is set to 2 for capacity and replacement scenarios. The capacity scenario admits three sequential inputs with the same task key at epochs 1, 2, and 3. The replacement scenario admits two `chat` inputs at priorities 0.1 and 0.9, then a `project` input at priority 0.8. The TTL scenarios admit one item at epoch 1 (default TTL 8); the maintained arm runs a maintain gate at epoch 8. Both then advance the memory clock to epoch 8 and next to the expected expiry epoch (9 unmaintained, 16 maintained).

**Scoring.** Capacity pass: exactly two active slots, first two inputs accepted, third refused with `capacity_limit`, with no content loss. Replacement pass: exactly two active slots; the low-priority foreign-task slot is reused by the project item, high-priority chat content remains, and replacement metadata increments. TTL pass: active at epoch 8; unmaintained slot expires at epoch 9 and releases its content; maintained slot has expiry 16, stays active at epoch 9, and expires/releases content at epoch 16. Gate result, slot status, task key, content edge, and expiry are recorded.

**Measures.** Rule-tick time per gate/clock, progress count, node/slot counts, final graph outcomes, boot time, and process RSS. Timing is descriptive, with no performance threshold.

**Claim boundary.** This measures the authored four-slot working-memory mechanism under a reduced two-slot synthetic configuration. It does not measure long-term episodic forgetting, natural task relevance, memory utility, learned retention policies, concurrent gate races, or scale. The scenarios are source-derived and specified before execution; existing source tests are not rerun as part of this measurement.
