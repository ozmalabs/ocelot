# Shape-decoding Python/native attribution v3 — native rule-store summary preregistration

**Question:** Does avoiding full native-rule-store export during detached branch setup materially lower shared-page prediction and rehearsal cost?

Replace `_install_detached_rewrite_delta`'s `export_rules()`/Python scan with `experiment_rule_store_summary(remove_names)`, which returns the active rule count and removes requested names in native code. Native full-copy and shared-page forks already contain the rule store. Keep serialization snapshot behavior on its existing copy path. Repeat the 100k shape fixture, default native candidate patch, both scoped backends, sequential/concurrent fanout 8, and three fresh processes per backend/mode (12 total). Sequential cells use cProfile; concurrent cells remain unprofiled because the prior profiler arrangement was invalid.

Compare against profile v2: wall and CPU/wall, phase timings, isolated Python/native self CPU, JSON decode/export hot sites, exact task outcomes, primary graph/rule revision, source/binary lock, and 12 unique workers. Require task, parity, isolation, profile-total, phase-validity, and source-lock gates.

**Limits:** One fixture and host; a reduction does not establish broad scaling. Candidate-rule semantics are separately controlled by the v4 and rule-patch semantic captures. The compact summary method must preserve active count and removal behavior exactly.
