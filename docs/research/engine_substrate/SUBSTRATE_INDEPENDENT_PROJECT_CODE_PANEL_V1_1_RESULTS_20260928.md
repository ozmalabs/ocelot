# Independent-project code prediction panel v1.1 results

Date: 2026-09-28  
Status: complete; all 11 independent analysis gates pass.

## Project and syntax coverage

The metadata-only sampler selected 41 installed distributions with exact MIT, Apache-2.0, or BSD-3-Clause licensing metadata, a packaged license document, and at least ten production Python files. The snapshot contains 1,740 source files and 55 license/notice files. Under the frozen function grammar, only one project had any eligible top-level function: SQLAlchemy, with two eligible functions. The preregistered one-representative-per-project hash rule selected `sqlalchemy/ext/orderinglist.py::count_from_1`. The other eligible function and all 40 zero-eligible projects remain in the denominator. No project or function was hand-selected.

The nine fixed integer inputs all returned exact typed outputs in both workers: 9/9 correct, zero abstentions, and zero wrong returns. There were no receipts or minted observations. This is one narrow function from one of 41 independently licensed projects; exact conditional accuracy is not a broad transfer estimate. Syntax coverage is the main result: 1/41 projects yielded eligible functions under the frozen grammar.

| Measure | Worker 0 | Worker 1 |
|---|---:|---:|
| Exact outputs | 9/9 | 9/9 |
| Predictions / abstentions / wrong returns | 9 / 0 / 0 | 9 / 0 / 0 |
| Receipts / observations / minted axes | 0 / 0 / 0 | 0 / 0 / 0 |
| Median / p95 call wall | 23.98 ms / 1.759 s | 25.64 ms / 1.769 s |
| Median / p95 call CPU | 23.99 ms / 1.758 s | 25.65 ms / 1.767 s |
| Boot | 731/742; 11 failures | 731/742; 11 failures |
| Peak RSS | 1.806 GB | 1.807 GB |

The p95 includes the cold first call (about 1.76 seconds); the median summarizes the warmed calls. Full runtime boot is separate and takes about 12 seconds.

## Integrity and provenance

Independent frame reconstruction and AST-oracle scoring passed for all nine cases. Both fresh workers had distinct PIDs, complete matching schedules, exact source hashes, stable full locks, and successful full-runtime boot. The shared run manifest and console capture verified. The raw runner passed its parent/worker lock gates.

- Snapshot manifest SHA-256: `7ab2290067fd005b48f8935a270e810988e459838eb124dd1aa74e08413a22a1`
- Frozen frame SHA-256: `f391c0e8e9a957fd5d8848b7b64202613e4eefe079be3cc4d8232fe91ad7f80f`
- Source lock SHA-256: `0b3840aa60713f33788d93b4c798ab30239a3816b3b723d07eb7707e2bdfb776`
- Raw report SHA-256: `5441cbc65ceafd45ea418c2fde96bc1dfe3336b71dc28b3174cc8a770dc92b22`
- Independent analysis SHA-256: `08248964dd6c58c86c115afecc152e895babbff02323520bfa24f0fc5152f6a2`

## Claim boundary and next gate

This provides one reproducible successful prediction in SQLAlchemy under a frozen licensed source snapshot. The v1 project-only filelock selection had zero eligible functions; v1.1 expands to the complete metadata-qualified project set and still finds only one project with eligible syntax. Preserve that limited coverage rather than treating 9/9 as an accuracy estimate. A next version needs a preregistered broader grammar that has an independently justified oracle, or a task-level benchmark whose target sample is not filtered by this emitter’s current syntax.

## Artifacts

- [v1 preregistration](SUBSTRATE_INDEPENDENT_PROJECT_CODE_PANEL_V1_PREREG_20260928.md)
- [v1.1 preregistration](SUBSTRATE_INDEPENDENT_PROJECT_CODE_PANEL_V1_1_PREREG_20260928.md)
- [Project snapshotter](../../../scripts/snapshot_independent_code_projects_v1_1.py)
- [Frozen project snapshot manifest](../../../data/independent_python_projects_v1_1/manifest.json)
- [Selector](../../../scripts/select_independent_projects_code_frame_v1_1.py)
- [Runner](../../../scripts/substrate_independent_projects_code_panel_v1_1.py)
- [Independent analyzer and oracle](../../../scripts/analyze_independent_projects_code_panel_v1_1.py)
- [Frame](../../../evaluation/substrate_capability/independent_projects_code_panel_v1_1_frame_20260928.json)
- [Raw report](../../../evaluation/reports/independent_projects_code_panel_v1_1_20260928.json)
- [Analysis](../../../evaluation/reports/independent_projects_code_panel_v1_1_analysis_20260928.json)
- [Source lock](../../../evaluation/substrate_capability/independent_projects_code_panel_v1_1_lock_20260928.json)
