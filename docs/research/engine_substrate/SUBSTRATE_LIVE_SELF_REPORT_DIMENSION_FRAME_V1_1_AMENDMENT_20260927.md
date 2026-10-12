# Live self-report task-dimension frame scale v1.1 amendment

Date: 2026-09-27

The v1 protocol recorded aggregate trace counts but did not retain concrete graph node IDs, so it could not compare its harness-declared frame nodes with the engine's selected access sites. Before the confirmatory v1.1 capture, extend the same worker schedule and source lock to retain every aggregated access-trace event whose node or peer is one of the frame nodes or shared Agent root. Record rule UID, access kind, node, resource, peer, count, and frame role for touched nodes. Record total event counts touching frame nodes and root, and reconcile both totals against the retained filtered rows.

This extension is descriptive and adds no minimum expected frame hit rate. A zero-touch result is valid evidence of a mismatch between the operational frame and the selected trace surface. It does not prove the engine never reads the frame: access tracing documents selected instrumentation sites and has specialized-operation blind spots. The output oracle, workload sizes, replicate count, paired arms, and prior gates are unchanged. The rerun uses a fresh lock that includes this amendment and the finalized analyzer.
