# Rooted frame access-scope reconciliation v1 preregistration

Date: 2026-09-28
Status: preregistered before the reconciliation replay

## Question

For the accepted rooted-frame self-report workload, how do observed native rule-access events relate to the engine's declared static read/write sets, and how much observed concrete read/write overlap is refined by node identity? Can current scale counters account for selected trace-site event totals?

## Frozen workload and baseline

Replay the two prompts from the accepted [rooted proposal panel v1.1](SUBSTRATE_ROOTED_FRAME_PROPOSAL_PANEL_V1_1_RESULTS_20260928.md) in three fresh workers. Require the exact current source/native lock used by v1.1 and hash the accepted raw capture. Preserve per-prompt trace intervals and compare trace rows, task outcomes, and final semantic graph digest to v1.1. Do not modify task prompts, graph construction, proposal radii, or trace instrumentation.

During each request, enable native access tracing and scale audit over the complete `converse` call, resetting both before the request. After each request, snapshot the observed trace rows, `rule_access_sets()`, rule UID/index metadata, and per-rule scale counters. Retain static access records only for UIDs with trace events, plus unmatched UID counts. Source-access mapping is fixed in the analyzer by event kind and resource vocabulary.

## Registered analyses

1. **Static-key concordance:** map supported trace kinds to read/write resources (`edge:`, `attr:`, `type:`) and compare each observed UID/resource/direction to the rule's static keys or corresponding `reads_any`/`writes_any` wildcard. Treat implicit `SetAttrIfDifferent` old-value reads as a separately labeled case; treat edge-attribute storage and index type symbols, node deletion without resource, and tool dispatch as distinct limited/uncheckable classes rather than guessing.
2. **Concrete identity refinement:** within attribute and typed-edge read/write event classes, intersect exact node/key or directed-edge identities across writer and reader UIDs. Compare observed UID pairs with static possible dependency pairs over the observed rules. An unobserved pair is not evidence of independence.
3. **Counter reconciliation:** compare per-rule `pattern_edge` weighted counts with `binding_leaves × match_edge_count`, `term_attr_read` with `Attr` evaluations, `effect_attr_write` with effect-attribute-set attempts, and `effect_edge_upsert` with edge-insert attempts. Report any nonconserved site separately; do not force a pass threshold by changing formulas after capture.
4. **Trace distribution:** report weighted counts and distinct rows by prompt, event kind, matched/unmatched/uncheckable class, and node/peer localization. Report trace drops and `RuleUid`-unattributed work as coverage caveats.

## Integrity gates

- Three distinct fresh PIDs; recorded start/end locks equal the preregistered lock.
- Accepted v1.1 source-lock hash matches current lock inputs.
- Per-prompt replies/routes/lifecycle and final semantic graph digest match accepted v1.1.
- Per-prompt trace rows and scale counters reconcile internally; zero trace drops.
- Independent analyzer reconstructs static resource concordance, identity overlaps, and counter formulas from raw rows.

## Claim boundary

Static key concordance is not trace completeness. Dynamic identity overlap proves observed sharing only; lack of overlap does not prove independence. Rule-scoped trace excludes known host/tool/scheduler and selected specialized/matcher work. The two-prompt single-family replay does not establish learned boundaries, causal necessity, local-execution correctness, natural-task prevalence, or a general complexity bound.
