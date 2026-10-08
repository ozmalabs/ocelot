# Preregistration: full-closure fallback for scoped deferred effects

**Question.** When scoped settlement reports `deferred_effects_pending`, does the explicit caller policy “discard scoped completeness, run global closure, then verify fixed point” recover the same graph-authored TrackIdentity result as ordinary global closure?

**Protocol.** Fresh processes in three arms: `full` runs one global closure; `scoped_only` runs the controller Microtheory with progress budget 1 and stops; `scoped_fallback` runs the same scoped call and, only when the report says deferred work is pending, immediately runs global closure. Each instance contains 1, 2, or 4 separated previous/current percept pairs (2/4/8 frame owners), one controller-owned trigger, and one `TrackIdentity` effect using the registered feature key. Two repeats per cell; all task keys and process IDs are retained. No performance threshold is imposed.

**Gates.** The scoped call must report pending deferred work and must not be treated as a complete owner notification report. Global closure must settle without a cap. Fallback final identity assignments and completion state must exactly equal `full`; the scoped-only arm is retained to show the pre-fallback state. A terminal global closure after fallback must make zero progress. Every worker is fresh and inputs/build/source hashes match the pre-run lock.

**Claim boundary.** This tests one deferred native effect family and one conservative caller fallback policy on a synthetic fixture. It does not implement automatic fallback, prove that all deferred queues are surfaced, establish owner notifications for deferred writes, or justify scoped closure for arbitrary workloads. Full global closure is the semantic safety fallback; its cost is not measured here.

## Harness amendment v1.1

The initial 18-worker capture completed, but the independent analyzer stopped because settled global closure reports omit `hit_progress_budget`. The analyzer now treats the absent global-only flag as false; scoped reports still must explicitly report the flag and must expose pending deferred work. The initial raw capture is retained as [`v1 raw`](../../../evaluation/reports/substrate_scoped_deferred_fallback_v1_20260926.json); it is exploratory because its locked analyzer failed. The amended runner/analyzer lock and v1.1 raw capture are separate, and no task, arm, or correctness gate changes.

## Harness amendment v1.2

The v1.1 independent analysis passed, but did not encode the scoped-only negative control’s expected unfinished state as a gate. V1.2 adds a gate requiring every scoped-only worker to retain unset identity fields despite the writer trigger being marked done. This verifies that pending work is consequential and that the global fallback, rather than merely calling the report, restores the expected state. The fixture, arms, and full-versus-fallback criterion are unchanged. V1/v1.1 locks, captures, and analysis are retained; v1.2 is the confirmatory result.
