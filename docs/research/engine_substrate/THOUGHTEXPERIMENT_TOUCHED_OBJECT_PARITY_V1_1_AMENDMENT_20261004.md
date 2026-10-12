# Touched-object parity v1.1 amendment

Date: 2026-10-04

The full v1 schedule was attempted and all 18 workers failed during audit
instrumentation setup. The Python `Substrate.node()` result includes a native
`NodeID`, which cannot be deep-copied; no touched comparison, falsifier, or
timing conclusion was produced. The failed capture and v1 lock remain retained.

Version 1.1 preserves the same workload, 18-cell schedule, audit method, and
gates. It stores only the node's type and a deep copy of its JSON attribute map,
excluding the non-copyable native ID wrapper. A fresh source lock binds the
amended runner, analyzer, amendment, lifecycle instrumenter, engine/build, and
the same node-scale baseline. The v1.1 run must still pass all original gates;
the v1 failures are not excluded from the project record.
