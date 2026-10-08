# Python source coverage audit v1

Date: 2026-09-28  
Status: stable-source static census; capability links are sparse and import reachability is approximate.

## Coverage

The capability map links 32/833 Python source files (3.8%) across `domains/`, `substrate/`, and `runners/dsl/python/`. Static import traversal from five runtime entrypoints reaches 247/833 files (29.7%). These are separate measures: module linkage does not prove runtime execution, and import reachability misses dynamic dispatch.

| Source root | Files | Capability-linked | Import-reachable | Both |
|---|---:|---:|---:|---:|
| `domains/` | 805 | 20 | 229 | 6 |
| `substrate/` | 18 | 11 | 16 | 9 |
| `runners/dsl/python/` | 10 | 1 | 2 | 0 |

The census found 0 Python parse errors. The machine-readable per-file inventory, symbol names, import edges, hashes, and capability-row links are [here](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_20260928.json).

## Interpretation

This audit shows the source-linked map is not yet a comprehensive Python inventory. It leaves 801 source files without a capability-row link; that does not label them as capabilities or dead code. The next mapping pass should classify modules into executable capability, shared substrate support, generated/experimental code, or excluded/legacy, then connect runtime-loaded modules and evaluated outcomes. Dynamic dispatch and seed-defined rule execution require runtime evidence, not import-graph inference.

The input source hashes are re-read after AST analysis and must match exactly; a concurrent edit aborts output. Re-run with `python3 scripts/audit_substrate_python_source_coverage_v1.py`.
