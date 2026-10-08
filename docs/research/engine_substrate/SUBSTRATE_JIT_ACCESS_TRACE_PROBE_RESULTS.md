# JIT and adjacency access-trace probe

**Run date:** 2026-09-25  
**Evidence grade:** targeted native-site coverage probe  
**Status:** three paired fresh-substrate fixtures confirm JIT Attr, JIT TypeOf, and fused Count(Neighbours) trace events.

## Source gap and change

The first access trace observed interpreted `Attr` and `TypeOf` Terms, but the matcher can run where-clauses through `jit.rs` thunks that read `TypedGraph` directly. Fused `Count(Neighbours(...))` likewise calls `out_edges_slice` from native code. Interpreted adjacency Terms also returned graph structure without concrete edge-identity events. Those paths could therefore affect both access footprints and measured cheap-cut candidates while remaining invisible.

The native trace now records separate `jit_attr_read` and `jit_type_read` events, plus concrete `(src, edge_type, tgt)` `term_edge_read` events from the JIT neighbour-count thunk and the interpreted `Neighbours`, `InNeighbours`, `MapNeighbours`, and `ReachableFrom` paths. Event collection is guarded by the trace enable flag. The source change does not make the trace complete: the specialized paths in the [ten-case probe](SUBSTRATE_SPECIALIZED_TERM_ACCESS_TRACE_PROBE_RESULTS.md) are covered at selected sites, while other opaque graph-reading helpers and effect-value paths still need a source audit and targeted probes.

## Probe results

Three tiny paired probes each compile one JIT rule and compare tracing off/on: `Not(Attr(a,"flag"))`, `TypeOf(b) == "Probe"`, and `Count(Neighbours(a,"probe_edge")) > 0`. All pairs return the same progress/status, reach a fixed point, and have zero terminal progress. Disabled arms emit no events; enabled arms produce the expected event kind with no drops. The independent analyzer verifies the raw event-kind, parity, JIT activation, and source-hash invariants.

Raw capture: [`substrate_jit_access_trace_probe_v1_20260925.json`](../../../evaluation/reports/substrate_jit_access_trace_probe_v1_20260925.json). Independent analysis: [`analysis JSON`](../../../evaluation/reports/substrate_jit_access_trace_probe_v1_analysis_20260925.json). Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_jit_access_trace_probe_v1.py
python3 scripts/analyze_substrate_jit_access_trace_probe_v1.py
```

This is direct evidence for the three JIT instrumented site families only. The fixture is not a workload sample and provides no cost or general locality estimate. Next enumerate remaining direct graph reads in `term.rs` and delegated helpers, add tracing or targeted coverage for high-frequency paths, and keep uninstrumented paths explicit in frame-cut analyses.
