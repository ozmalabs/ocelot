# Held-topic structural trace capture v1 results

> **Superseded for current-worktree capability claims.** This report records an isolated snapshot that omitted the repository's `data/` runtime corpus. The snapshot's Python/seed hashes matched, but its boot graph was smaller and its query outcomes differed from the actual workspace. Keep the details below as historical evidence for that snapshot only. The current-workspace paired result is [v1.1](SUBSTRATE_HELD_TOPIC_TRACE_SEMANTIC_PARITY_V1_1_RESULTS_20260928.md).

Date: 2026-09-28  
Protocol: [preregistration](SUBSTRATE_HELD_TOPIC_STRUCTURAL_TRACE_CAPTURE_V1_PREREG_20260928.md)  
Amendment: [baseline provenance amendment](SUBSTRATE_HELD_TOPIC_STRUCTURAL_TRACE_CAPTURE_V1_AMENDMENT_20260928.md)

## Historical isolated-snapshot result

The three-worker capture passes all 357 independent capture-integrity checks. Workers have distinct PIDs, replay the fixed schedule, and report matching source/native locks before and after execution. The independent analyzer reports no failed integrity checks. The capability oracle fails consistently: 12/30 teaching/query outcomes pass across the three workers (all nine teaching operations and one of seven query cases per worker).

All three taught answers are returned exactly by `learn_from_teacher`. The table query, “What is copper?”, returns the supported copper answer with a released receipt. The other six queries fail their specified oracle:

- Three meta questions (“What do you know about …?”) return `I am Jabberwock.` even when the corresponding held answer and evidence exist. No answer-topic Goal is created on these routes.
- “Can you tell me about copper?” routes to `frontier`, creates an answer-topic Goal for the whole phrase, and returns `I don't know 'Can' — what does it mean?` despite held copper evidence.
- The unknown-topic and injected-local-hit cases both take the meta route and return the generic fallback. The unresolved grounder and injected local source are not called, so these cases do not establish refusal or local-hit behavior on the current source.

## Historical route observations

The isolated graph lacked the complete workspace runtime assets, so these route observations are not a valid localization for the current workspace. The later workspace capture shows `comp_topic` and a resolved/unresolved `answer_topic` Goal on all seven query cases; held-answer retrieval works on six cases. The remaining request-form gap is a production/capability outcome, not the missing-topic route described in this historical snapshot.

The v1 raw capture and analysis below remain useful for inspecting this historical snapshot's trace accounting, but the v1.1 workspace capture supersedes its route and capability conclusions.

The task frame projection contains 9–11 nodes and 9–11 internal edges, with a deterministic min-fill induced-width upper bound of 2. Its complete direct cut contains 34–45 boundary incidences and 23–32 unique external nodes. For these manually declared frames, the boundary is several times larger than the internal edge set; the small frame and width therefore do not demonstrate a cheap effective interface. The whole graph at the measured turns has 25,033 nodes and 11,485 edges. This is one authored task family, and the frame members were selected by the harness rather than discovered by the substrate.

For conversation calls, access traces contain 15,780–56,945 rows and 83,020–296,238 weighted events; all event weights conserve, there are zero dropped events, every RuleUID resolves, and no static-resource mismatch is observed. Per-operation all-scope scheduler/deferred rows reconcile exactly with scope and process-global counters. These checks establish consistency of the exposed instrumentation, not complete observation of host-language reads or proof of frame independence. Teaching operations produce no native access rows in this measurement boundary. The instrumented elapsed times are retained in raw data but are not treated as an uninstrumented performance estimate.

## Provenance and limits

The accepted v1.6 report is a historical reference only. Its source lock differs from this capture: 29 common Python/seed paths changed, two seed files were added, and the native extension and build manifest changed. Task outputs and boundary summaries do not match v1.6. The fresh capture locks the current source closure, including all 1,671 Python/seed inputs; an end-of-run comparison against the worktree found no changed or missing files. Reproduce the checks with the captured runner and analyzer from the repository root, using the locked native package selected by `SUBSTRATE_NATIVE_PACKAGE`.

This result is not a prevalence estimate, a claim about all query formulations, or evidence that small operational frames are discovered automatically. It does not measure partitioned fixed-point correctness, rule-closure termination, learner search, minting, or scaling to large graphs. The measured user-facing failure is nevertheless a direct capability gap in this locked source snapshot: held evidence can be present while common query paths fail to retrieve and release it.

## Artifacts

- [Raw three-worker capture](../../../evaluation/reports/held_topic_structural_trace_capture_v1_20260928.json)
- [Independent analysis](../../../evaluation/reports/held_topic_structural_trace_capture_v1_analysis_20260928.json)
- [Source/native lock](../../../evaluation/substrate_capability/held_topic_structural_trace_capture_v1_lock_20260928.json)
- [Capture runner](../../../scripts/substrate_held_topic_structural_trace_capture_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_held_topic_structural_trace_capture_v1.py)
- [Aggregator](../../../scripts/aggregate_substrate_held_topic_structural_trace_capture_v1.py)

## Next work

1. Trace the failed meta and frontier routes from comprehension through answer selection, evidence grounding, goal state, and production receipt; localize where held-answer retrieval is bypassed.
2. Add route-level controls for a known held answer, an unknown topic, and an injected local hit, while retaining the existing table positive control. Require the local-hit case to reach the grounder before interpreting it as a retrieval failure.
3. After any route repair, rerun the same source-locked three-worker panel and compare semantic outcomes, complete task cuts, and exposed work counters.
4. Keep the structural tractability gate open. Select frames independently or learn them, perturb omitted boundary dependencies, and compare monolithic with partitioned closure before claiming locality or factorisation.
