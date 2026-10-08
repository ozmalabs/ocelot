# Daemon conversation → MetaShape bridge v1.1 amendment (2026-09-26)

The v1 capture installed `sys.setprofile` around each conversation turn to count Python calls to `domains.teach.teach`. It returned no teach calls and no measured MetaShape-route graph changes, but turn times were 10–17 seconds under a full graph and Python call tracing. These latencies are instrumentation-contaminated and are excluded from performance interpretation.

V1.1 repeats the same fresh full boot and the same four fixed utterances with the same seed-persistence guard, but removes call tracing. It records only graph deltas for `ShapeObservation`, `MetaShape`, `TaughtHint`, and `TeacherEvidence`, plus wall time. Since `teach()` mechanically calls `meta_shape.observe()` before persistence, the primary reachability outcome is whether a new `ShapeObservation` appears; no observation means the measured MetaShape learner input path was not reached. V1 results remain archived as diagnostic and are not silently replaced.

The utterances, boot profile, outcome interpretation, and scope remain as preregistered in [v1 protocol](SUBSTRATE_DAEMON_CONVERSATION_METASHAPE_BRIDGE_PREREG_20260926.md). V1.1 adds no new prompts or runtime behavior. Its source set is independently locked before execution.
