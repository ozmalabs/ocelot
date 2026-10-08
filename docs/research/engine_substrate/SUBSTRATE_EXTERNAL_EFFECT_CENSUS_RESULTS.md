# External-effect source census — 2026-09-25

## Question and method

How many explicit Python process/network call sites and tool-registration calls appear in the runtime-owned source surfaces, and where are explicit P0-A guard calls placed?

[`scripts/substrate_external_effect_census.py`](../../../scripts/substrate_external_effect_census.py) parses Python ASTs under `domains/`, `substrate/`, `runners/dsl/python/`, and `scripts/jabberwock_daemon.py`. It does not import application modules or invoke handlers, subprocesses, or network requests. Calls are normalized through direct import aliases, then classified as process, network, explicit `deny_direct_io` guard, or tool-registration candidates. The raw report hashes all 832 scanned files: [`evaluation/reports/substrate_external_effect_census_20260925.json`](../../../evaluation/reports/substrate_external_effect_census_20260925.json).

## Result

The scan parsed all 832 files without syntax errors and found:

| Syntactic call-site class | Count |
|---|---:|
| Process launch/control calls | 37 |
| Network API calls/construction sites | 19 |
| Explicit `deny_direct_io` calls | 6 |
| Tool-registration call candidates | 14 |

The network sites include HTTP(S) URL access, `requests` clients, HTTP connection construction, and sockets. Process sites include ToolBox shell execution, typed tool subprocesses, audio/video conversion, language services, experiments, builds, and training. They are source call sites, not counts of enabled tools or reachable effects.

Two process call sites share the same enclosing function as an explicit guard call: `domains/experiment_dispatch.py::_spawn` and `domains/voice_world.py::capture_utterances_from_mic`. In `domains/fetch_dispatch.py`, the guard is in `_materialize_http_get`, but the fallback `urllib.request.urlopen` is in the separate `_plain_http_get`; source inspection therefore does not support treating that guard as coverage for the fallback request. Even same-function overlap does not prove control-flow dominance, activation, or coverage of alternate routes. The remaining sites include both agent-facing and infrastructure/domain operations; no agent-reachability classification was attempted.

The P0-A `ROUTE_INVENTORY` has eight named high-level routes, while this scan found six literal guard call sites. These counts have different units and are not a coverage percentage: multiple routes can share guards, and one route can contain multiple effect calls. The fetch fallback demonstrates why call-site counts are insufficient: guard placement around materialization does not necessarily intercept the network operation itself. A runtime registry snapshot and route-by-route interception test are still required.

## Limits and next experiment

The AST scan can miss reflection, dynamically supplied callables, aliases it cannot resolve, native effects, and I/O hidden in dependencies. It can also find code paths that are never imported or enabled. It does not scan filesystem mutations, credential use, database clients, GPU/device interfaces, or all external protocols. It is therefore a reproducible source baseline, not dynamic reachability, authorization, containment, or receipt evidence.

Next, freeze an evaluator-owned runtime build, enumerate actual registered handlers and adapter routes without calling them, then invoke denial/interception probes under the activated P0-A context. Record per-route attempted/blocked/executed counts and receipt linkage. Do not run capability-efficacy or planning trials until that route coverage and the existing custody prerequisites pass.
