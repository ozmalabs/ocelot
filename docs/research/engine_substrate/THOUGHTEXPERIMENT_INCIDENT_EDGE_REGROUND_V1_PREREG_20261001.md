# Thoughtexperiment incident-edge regrounding v1 — preregistration

**Date:** 2026-10-01  
**Question:** Does a native incident-edge accessor preserve exact incident-edge semantics while reducing before-image read cost as unrelated graph size grows?

## Design

Compare `Substrate.incident_edges(target)` with the reference operation `graph_to_dict()` followed by filtering all edges whose source or target is `target`. Use five fresh worker processes and five timed repeats per method/cell. Cells are (background node count, target degree): (0,4), (10,000,4), (50,000,4), and (50,000,32). Each background graph is a directed chain; target edges use unique labels and distinct peer nodes. Compare the complete returned `(src,type,tgt,attrs)` sets with an independently constructed expected list for both methods.

## Measures and gates

Record each worker's per-repeat wall times, graph node/edge counts, oracle parity, machine/runtime metadata, native binary hash, Rust source fingerprint, and SHA-256 for runner and implementation inputs. The capture passes only if all five PIDs are distinct and both methods match the independent incident-edge oracle in every cell. Report medians across worker medians; no asymptotic or natural-task claim follows from these four synthetic cells.

## Interpretation limits

This isolates the data-access cost of incident-edge before-image validation. It does not measure full `reground` latency, mixed commit latency, rule execution, CPU utilization, allocation attribution, or natural-task degree distributions. Graph construction is excluded from timed intervals. Python wrapper and serialization costs are included because both paths are exposed to the Python regrounder.
