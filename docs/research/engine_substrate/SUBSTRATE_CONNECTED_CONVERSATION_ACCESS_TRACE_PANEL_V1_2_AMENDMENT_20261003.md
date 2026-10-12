# Connected-conversation access-trace panel v1.2 amendment

Date: 2026-10-03

V1.1's instrumented capture and independent analyzer run successfully, but exact comparison with the 2026-09 baseline fails across all cases. The baseline was generated with earlier native/Rust and discourse-materializer sources; the current source lock confirms those identities have changed. Therefore the old graph is not a valid control for the effect of tracing. V1.1 and its failed parity analysis are retained as provenance.

V1.2 replaces historical-state parity as the tracing control with paired fresh executions on the same current sources: each case runs once with access tracing disabled and once enabled from a fresh world. It requires exact final and per-checkpoint graph digest parity between those arms, zero trace drops, nonempty rule-attributed trace events, and stable sources. The historical graph comparison is retained as descriptive drift evidence only. Worker CPU is added to parent CPU so resource totals include the subprocesses that execute the workloads. Task cases, workload family, structural measurements, and claim boundary remain unchanged.
