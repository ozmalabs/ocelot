# Python source coverage audit v1.2

Date: 2026-09-28  
Status: stable-source static census; capability links are sparse and import reachability is approximate.

## Coverage

The capability map links 69/833 Python source files (8.3%) across `domains/`, `substrate/`, and `runners/dsl/python/`. Static imports from six runtime entrypoints reach 247/833; adding literal profile `importlib` loads reaches 248/833. `CONVERSATION_RUNTIME_MODULES` declares 65 module loads, with 65 distinct Python files. Exact dotted Python module strings occur in 0 of 742 eligible seed manifests (838 discovered). These are navigation and declared-load signals, not proof each module executed in a specific task.

| Source root | Files | Capability-linked | Static import-reachable | Declared runtime-reachable | Both linked and runtime-reachable |
|---|---:|---:|---:|---:|---:|
| `domains/` | 805 | 57 | 229 | 230 | 43 |
| `substrate/` | 18 | 11 | 16 | 16 | 9 |
| `runners/dsl/python/` | 10 | 1 | 2 | 2 | 0 |

The census found 0 Python parse errors and 0 malformed loader-selected seed manifests. The machine-readable per-file inventory, symbols, import edges, declared dynamic loads, exact seed module-name references, hashes, and capability-row links are [here](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_2_20260928.json).

## Interpretation

This audit shows the source-linked map is not yet a comprehensive Python inventory. Unlinked files are not thereby capabilities or dead code. The next mapping pass should classify modules into executable capability, shared substrate support, generated/experimental code, or excluded/legacy, then connect runtime-loaded modules and evaluated outcomes. Static or declared reachability does not establish execution on a workload.

Python sources, the exact top-level plus `seeds/generated/*.json` loader manifests, and the capability map are hashed before and after analysis; any concurrent change aborts output. Re-run with `python3 scripts/audit_substrate_python_source_coverage_v1_2.py`.
