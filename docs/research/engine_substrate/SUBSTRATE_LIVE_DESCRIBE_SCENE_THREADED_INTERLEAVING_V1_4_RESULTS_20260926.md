# Live describe-scene interleaving and producer work v1.4 (2026-09-26)

## Question and method

This capture extends the existing two-thread `describe_scene` interleaving schedule by recording native work inside each call to the production `_record_live_goal_event` helper. Request A pauses after selection; request B attempts the same adapter lock and waits. After A finishes, B completes. The wrapper scopes the native scale audit to each helper call, recording elapsed time, global counters, and per-rule counters without changing the helper's arguments or result.

V1.3 produced identical work counts, but its lock omitted the full seed corpus consumed by `load_all_seeds()`; it is retained as diagnostic evidence and is not used as the source-locked result. V1.4 locks 1,669 files: all eligible top-level and `generated/` seed JSON manifests, Python sources under `domains/`, `substrate/`, and `runners/dsl/python/`, plus direct protocol/runner/analyzer/native/build inputs. Worker start/end and parent post-run source fingerprints match exactly.

## Result

Three fresh workers pass all runner gates and all 11 independent analysis checks. In each worker, B is blocked while A is paused after selection; both then emit their own ordered selection→execution→result sequence, resolve and close the correct Goal, return the established baseline reply, and join without thread errors. The six helper calls per worker have exactly replicated candidate and Term counts across processes. Per-rule/global candidate and Term counter conservation passes.

Across the two live requests in each worker, production helper work is:

| Lifecycle event kind | Calls per worker | Candidate pairs | Term evaluations | Median elapsed per helper call |
|---|---:|---:|---:|---:|
| Selection | 2 | 112,502 | 562,138 | 41.94 ms |
| Execution | 2 | 112,514 | 562,178 | 43.44 ms |
| Action result | 2 | 112,506 | 562,140 | 46.06 ms |

The six helper calls total 337,522 candidate pairs and 1,686,456 Term evaluations per two-request schedule. Timed ranges across the six calls per kind are 31.81–48.11 ms for selection, 32.87–44.72 ms for execution, and 34.52–50.95 ms for results. The counts include the full active rule set run by the helper, not only the four discourse lifecycle rules. Elapsed time includes helper event preparation and native closure.

## Interpretation and limits

The result demonstrates that this production lifecycle helper performs substantial, reproducible rule-engine work on the fully loaded seed profile even for two short live requests. It makes a per-route operating cost measurable and shows that helper closure work is material to end-to-end accounting. It does not establish that this cost is typical across action routes, that all counted rule work is necessary for the lifecycle transition, or that a cheaper scoped closure would preserve global semantics.

This is still one `describe_scene` workload, one scene vocabulary, one adapter, and one serialized two-thread schedule. It is not a natural-task sample or a general concurrency guarantee. No unlocked control, alternative route, rule ablation, or large-N scaling arm was measured. Do not compare its operation counts directly with the small-seed v2.1 fixture capture: the loaded rule sets differ.

## Reproduction artifacts

- V1.4 amendment and source-closure rationale: [amendment](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_V1_4_AMENDMENT_20260926.md)
- Base schedule: [protocol](SUBSTRATE_LIVE_DESCRIBE_SCENE_THREADED_INTERLEAVING_PREREG_20260926.md)
- Runner: [`substrate_live_describe_scene_threaded_interleaving_v1_4.py`](../../../scripts/substrate_live_describe_scene_threaded_interleaving_v1_4.py)
- Independent analyzer: [`analyze_substrate_live_describe_scene_threaded_interleaving_v1_4.py`](../../../scripts/analyze_substrate_live_describe_scene_threaded_interleaving_v1_4.py)
- Source lock with full hash map: [v1.4 lock](../../../evaluation/substrate_capability/live_describe_scene_threaded_interleaving_v1_4_lock_20260926.json)
- Raw capture: [three workers](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_4_20260926.json)
- Independent analysis: [11 gates and work attribution](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_4_analysis_20260926.json)
- Preserved partial-lock diagnostic: [v1.3 capture](../../../evaluation/reports/substrate_live_describe_scene_threaded_interleaving_v1_3_20260926.json)

## Next gate

V1.5 repeats this schedule under the source closure later used for self-report v1.7. The resulting matched-context comparison is descriptive only; broaden next to independently authored request/evidence families and interleaved multi-Goal cases before estimating any route-level cost envelope.
