# Thoughtexperiment incident-edge regrounding v1 — results

**Date:** 2026-10-01  
**Status:** source-locked access-path probe; all five workers and all oracle checks pass.

Five fresh workers compare `incident_edges(target)` with `graph_to_dict()` followed by a full edge scan. Each cell has five timed repeats. Both paths exactly match an independently built incident-edge oracle for every graph and degree treatment.

| Background nodes | Target degree | Edges | Local median | Full-scan median | Full/local |
|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 4 | 0.0102 ms | 0.0695 ms | 6.8× |
| 10,000 | 4 | 10,003 | 0.0565 ms | 133.1020 ms | 2,354× |
| 50,000 | 4 | 50,003 | 0.0640 ms | 709.9661 ms | 11,090× |
| 50,000 | 32 | 50,031 | 0.1059 ms | 708.0606 ms | 6,687× |

The result supports the expected access-path distinction: the native local read tracks target degree closely in these cells, while whole-graph serialization grows with total graph size. The 50k/degree-32 case is slower locally than degree 4, as expected for a larger aperture. Timings include Python wrapper conversion and, for the reference path, complete serialization; graph construction is excluded.

This is not a full `reground` benchmark or a natural-degree distribution. It uses a single target in a synthetic chain, five workers, and four size/degree cells; it does not isolate allocator/cache effects or prove an asymptotic bound. The data supports replacing the previous full serialization in deletion regrounding. Next measure complete reground latency across deletion-set sizes and graph topologies, then add randomized incident-edge parity and mixed-commit differential coverage.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_INCIDENT_EDGE_REGROUND_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_incident_edge_reground_v1.py)
- [Raw five-worker capture](../../../evaluation/reports/thoughtexperiment_incident_edge_reground_v1.json)
