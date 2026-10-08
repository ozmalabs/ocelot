# P0-A denial-only runtime probe — 2026-09-25

## Question and protocol

Does the local P0-A activated compatibility guard block its named legacy routes and selected process/network/file API primitives before their original operation, and what handler registries are present in a clean process?

[`scripts/substrate_p0a_denial_probe.py`](../../../scripts/substrate_p0a_denial_probe.py) ran in a fresh Python process. It read the P0-A route inventory, inspected Python and native `UseTool` registry counts, and listed explicitly installable ToolBox capability names without constructing a ToolBox workspace. It booted `WorldAdapter` with default core seeds and shadow/deep reads disabled; it did not run rules, start the agent, install tools, or dispatch graph requests. On a separate substrate, it registered the explicit `domains.tool_use.register_real_tools` demo pack and mirrored its five Python callbacks into the native registry, recording resulting ToolSpecs and handler names without invoking them. The native fire counter was unchanged. Finally, it activated `evaluation.p0a.legacy_io_guard` and `intercept_legacy_process_io`, attempted each named route through `deny_direct_io`, and attempted nine low-level operations behind the patched APIs. The original socket, URL, process, filesystem-open, descriptor-read, and exec operations were not called.

## Results

| Measurement | Result |
|---|---:|
| Named guard routes attempted and blocked | 8 / 8 |
| Low-level primitive attempts blocked | 9 / 9 |
| Total blocked probes | 17 / 17 |
| Unexpected outcomes | 0 |
| Handler invocations | 0 |
| Python tool-use handler registry at clean-process start | 0 |
| Native `UseTool` handler registry at clean-process start | 0 |
| Default-core boot graph nodes | 747 |
| Default-core boot ToolSpec nodes | 0 |
| Default-core boot Python/native handler counts | 0 / 0 |
| Default-core `runtime_capabilities()` names | `describe_self`, `op_count`, `op_mean_cost`, `op_total_cost` |
| Explicit demo ToolSpec registrations | 5 (`gcd`, `is_prime`, `factorial`, `upper`, `uname`) |
| Demo Python/native callback registrations | 5 / 5 |
| Demo ToolCall graph nodes | 0 |
| Native tool-fire counter | 0 before and after registration/probes |
| Explicit ToolBox capability names | `read_file`, `write_file`, `run_command` |

Raw per-attempt outcomes, guard-reported route names, source hashes, and environment are in [`evaluation/reports/substrate_p0a_denial_probe_20260925.json`](../../../evaluation/reports/substrate_p0a_denial_probe_20260925.json). The loaded native extension hash is `2e31b4f9…e1b030e` and matches `_native.build.json`; the report also records the full extension and manifest hashes.

## Claim boundary

This verifies the local activated Python ContextVar guard and monkeypatch/audit-hook compatibility interceptors for these 17 probes. It does **not** verify kernel/OS isolation, separate evaluator custody, or a signed/attested P0-A run. The adapter snapshot proves only that the default `WorldAdapter` core seed boot registers no ToolSpec or tool callbacks; optional profiles and daemon startup are not covered. Demo-pack registration proves that explicit setup creates five graph ToolSpecs and five callbacks in each registry; it does not show those handlers are installed in the default adapter. The ToolBox names describe a separate capability pack, not installed or authorized capabilities. The route-name probes call the guard directly rather than executing each high-level adapter. No authorization grant, action, tool handler, subprocess, or network request was exercised.

## Next measurement

After satisfying the P0-A launch/custody prerequisites, snapshot the active Python/native handler registries and enabled adapter paths for each optional boot profile and daemon startup in the evaluator-controlled worker. For each registered route, attempt the corresponding intercepted boundary with a sentinel request and require a blocked result plus a receipt; verify no state or external effect changed. Keep clean-process, default-core, optional-profile, and daemon inventories separate.
