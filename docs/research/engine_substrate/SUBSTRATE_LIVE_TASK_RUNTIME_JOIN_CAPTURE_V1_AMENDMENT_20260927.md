# Live task runtime join-work capture v1 amendment

Recorded before locked capture, 2026-09-27.

## Exploratory pilot disclosure

A single current-source worker passed the serialized request schedule, goal identity/lifecycle, and expected B reply, but did not pass the inherited exact-reply oracle because request A returned a gap response instead of the registered `describe_scene` baseline. The runner's old reply gate requires both A and B replies to match that baseline. This is a current behavior difference from the 2026-09-26 capture, not an instrumentation change or a result to erase.

## Amended reporting rule

Keep the frozen two-request task, full active rule inventory, per-event native counters, one pre-action graph snapshot, and three fresh-process repeats unchanged. Preserve and report every original task gate separately. The capture is admitted as **runtime work/failure characterization** only if source/native provenance, threads/schedule, event order, goal identity/lifecycle, pattern-to-RuleIdx mapping, counter conservation, and graph-snapshot integrity pass. The old exact-reply gate remains mandatory for claiming semantic task parity; if it fails again, `task_semantic_gate_pass` is false and the result must explicitly report the actual A/B replies. Do not call the work capture a passing task evaluation or use it to claim successful capability.
