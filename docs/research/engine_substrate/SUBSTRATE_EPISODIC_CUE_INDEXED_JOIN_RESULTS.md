# Indexed episodic retrieval join: results

**Run:** `substrate-episodic-cue-native-index-join-20260925-v2`, built with engine `5eb76b82e8e4` and frozen in the [v2 lock](SUBSTRATE_EPISODIC_CUE_INDEXED_JOIN_LOCK_V2_20260925.json). V1 behavioral checks passed but the raw hash manifest pointed to the previous experiment's preregistration; v1 is retained as development evidence. V2 corrects that metadata, repeats all 48 cells, and passes the independent hash and correctness checks.

## Change and protocol

The native `IndexJoinHint` matcher now applies when a match edge has one bound endpoint. For the episodic `agent --recorded_episode--> episode` join, it reads the cue key from the already-bound request, probes the maintained `(Episode,cue_key)` attribute index, then verifies each returned edge with direct graph lookup. The matcher continues to use ordinary adjacency traversal when the hint or index is unavailable. The hint-aware edge ordering binds the request before the Episode edge. The existing attribute index is automatically declared from the rule hint and reconstituted during rule import after `WorldAdapter.load`.

The isolated experiment compared baseline, request-count, and indexed-join variants on unique cue and two-event collision workloads, N=6/24/78/192, two independent checkpoints per cell, separate control and audit readers. Exact event identity, recalled provenance, `not_observed`, confidence, and clean close passed for all readers. Baseline persisted collision caps/status; both prototype variants intentionally did not. Thus parity is response-level, not persistent graph-state parity.

## Results

At N=192, the retrieval rule's candidate tests fell from 196 to 5 on unique cues (97.4% reduction) and from 197 to 9 on the collision case (95.4%). The hinted join enumerated a mean of 2 candidate pairs per unique query and 6 per collision query at every tested size from 6 through 192. This confirms that the join itself follows the indexed cue matches rather than the full Episode population for these workloads.

Other rules still execute. Total candidate tests fell from 1,166 to 975 (16.4%) on unique cues and 1,167 to 979 (16.1%) on collisions, comparing request-count with indexed join. Total term evaluations fell 27.1% in both cases; where evaluations were unchanged. Median uninstrumented tick fell from 0.699 to 0.548 ms on unique cues and 0.746 to 0.642 ms on collisions (two-replicate descriptive measurements). At N=6 the join setup did not improve latency, so the latency benefit grows with the removed scan and is not a universal constant-factor speedup.

## Interpretation and limits

This is a measured matcher-level tractability improvement, not a substrate-wide complexity result. It demonstrates that a hint plus a maintained exact-key attribute index can turn one episodic match edge from population enumeration into match-count enumeration. It does not make other rules local, establish natural-task frame locality, or measure graphs beyond 192 episodes. The prototype still changes the persistent collision-mark contract. Concurrency, adversarial index corruption, multiple agents, broader deletion/retraction behavior, and production integration remain to be evaluated.

The bound-source implementation checks the indexed attr and verifies the actual graph edge. A focused Rust unit test was added and compiles under `cargo check --tests`; the `cargo test` executable could not link Python C-API symbols under the crate's extension-module configuration. The fresh-process native integration run exercises the real seed-loader, auto-index, matcher, checkpoint import, and answer path. A follow-up should add a test target/configuration that links Python correctly, and test indexed updates/deletes through full rule execution.

## Artifacts

- [Preregistration and v1 metadata amendment](SUBSTRATE_EPISODIC_CUE_INDEXED_JOIN_PREREG_20260925.md)
- [V2 frozen lock](SUBSTRATE_EPISODIC_CUE_INDEXED_JOIN_LOCK_V2_20260925.json)
- [Raw measurements](../../../evaluation/reports/substrate_episodic_cue_native_index_join_v2_20260925.json)
- [Independent analysis](../../../evaluation/reports/substrate_episodic_cue_native_index_join_analysis_20260925.json)
- [Harness](../../../scripts/substrate_episodic_cue_native_index.py) and [analyzer](../../../scripts/analyze_substrate_episodic_cue_indexed_join.py)
- [Matcher source](../../../runners/dsl/src/rewrite.rs)
