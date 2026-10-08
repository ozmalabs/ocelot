# Full Substrate memory large-scale extension v1 — preregistration

**Date:** 2026-10-01  
**Question:** How does full-process RSS/PSS change when a complete Substrate forks a branch at 100k and 200k unrelated graph nodes across eager, shared-record, and shared-graph-page backends?

## Design

Extend the existing fresh-process `thoughtexperiment_full_substrate_pss_v1.py` panel at sizes 100,000 and 200,000 unrelated nodes, using three measured repeats per backend/size and no warmups. Each fixture boots the normal core substrate, retains its rules and candidate/observation state, and adds a linked noise graph. The worker measures Linux `smaps_rollup` at baseline, after branch creation, after one branch-local node insertion, and after branch drop plus garbage collection. Backend order is randomized within each iteration. Before execution, save a source/native build lock; retain the exact raw worker and aggregate records.

## Gates

- Six size/backend cells, three fresh-process observations each, with current source/native build provenance.
- Every branch adds exactly one isolated node; the parent graph/rule revision and counts remain unchanged.
- Report median RSS/PSS, private/shared clean/dirty deltas at fork, write, and post-drop; preserve outliers and negative deltas.
- Keep full-process startup and loaded runtime state inside the memory measure and separate them from fork deltas.

## Interpretation limits

This is one synthetic substrate family and one host. The noise graph and normal loaded runtime are present, but candidate prediction, inference, and rule closure are not executed. `smaps_rollup` gives current residency, not peak memory; allocator and kernel page retention affect drop measurements. It is not a workload-wide memory law or an independent-host result.
