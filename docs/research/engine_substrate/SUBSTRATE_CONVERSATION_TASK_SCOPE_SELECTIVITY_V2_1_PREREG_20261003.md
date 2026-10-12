# Conversation scope matcher selectivity v2.1 preregistration

Date: 2026-10-03  
Status: preregistered before implementation and capture.  
Prior evidence: [v2.0.2 semantic-edge attribution](SUBSTRATE_CONVERSATION_TASK_SCOPE_EDGE_ATTRIBUTION_V2_0_2_RESULTS_20261003.md)

## Question

Does declared-anchor matching reduce candidate and Term work when each task frame contains fixed true bindings but the shared graph also contains many structurally complete, lifecycle-ineligible Goal/Event matches outside every frame?

## Workload construction

Use the existing connected conversation panel and add 32, 256, or 1,024 decoy Goal/Event pairs to the `concurrent_goals` two-goal case, alongside the existing zero-decoy case. Each pair has the same four relation types as the lifecycle rules (`has_active_goal`, `originated_in`, `has_event`, `for_goal`), but its Goal lifecycle status is `decoy_ineligible`; rule predicates therefore reject it after structural matching. Decoy nodes have no `has_concept` membership in any frame. Add identical decoys before closure in monolithic, full-fallback, declared-anchor, and trace arms. The authored true goals, events, bindings, and task outcomes remain unchanged.

Run three replicates for each ascending, descending, and outside-in scope order. Retain the existing four aligned baseline cases and cross-frame/orphan-owner controls. Total: seven aligned cells (the four existing cases plus three decoy doses) and two ownership controls per worker; nine workers produce 81 paired cases.

## Measurements and gates

- Require source stability and nine fresh workers.
- Require exact monolithic/fallback/anchor graph equality at every checkpoint and final state, goal lifecycle equality, and trace-on/off parity.
- Require anchor-path use on aligned cells and proof-guard rejection on cross-frame/orphan controls.
- Record candidate expansion calls and Candidate pairs by semantic match edge, aggregate Candidate and Term work, and wall time as secondary evidence.
- Report each decoy dose separately. The prediction is increasing fallback work with decoy count, while anchor work grows more slowly because decoy goals are not owned by a frame. Do not declare an optimization unless both total Candidate and Term work are lower at nonzero doses and semantic gates pass.

## Interpretation boundary

This is a controlled selectivity stress, not a sample of natural tasks. It tests whether the declared anchor can exclude complete but irrelevant pattern instances under the present rule matcher. It does not establish natural-task cheap-cut prevalence, general multi-edge matcher performance, or broad tractability.

## Amendment — 2026-10-03, verify fallback-arm isolation

Inspection of the previous runner showed that patching `substrate.seed_loader.manifest_for` alone did not remove metadata: `substrate.boot_core` imports that function at module scope, and the panel imports `load_seeds_into` before subsequent arm changes. The earlier v2.0.1/v2.0.2 captures therefore do not establish an anchor-versus-full-fallback work comparison. This runner patches and restores both module references. A new hard gate requires zero declared-anchor attempts and zero anchor-proof rejections in every fallback checkpoint, while requiring at least one full-fallback invocation. The v2.0 state-parity and anchor-control evidence remains valid for its tested arms; its performance comparison and conclusion about equal anchor/fallback work are withdrawn. The selectivity workload, decoy counts, semantic gates, and performance thresholds remain unchanged.

### Amendment — 2026-10-03, analyzer coverage assertion

The first 81-case capture passes every runner gate, but its copied independent analyzer retained a six-cases-per-worker assertion from the earlier matrix. The analyzer reported this coverage mismatch despite processing all 81 rows and finding exact parity and lower aggregate work. Preserve that capture and failed analysis as diagnostic artifacts. The v2.1.1 rerun changes only artifact names and the analyzer's expected case count to nine per worker; all workload, run gates, and success thresholds remain unchanged.
