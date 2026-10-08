# Live describe-scene threaded interleaving v1.4 amendment

**Amendment before capture.** V1.3 produced exactly replicated helper work counters and all lifecycle/concurrency gates passed, but its source lock omitted transitive full-boot inputs: `load_all_seeds()` reads every eligible `seeds/*.json` and `seeds/generated/*.json` manifest. V1.3 remains preserved as diagnostic evidence and its work counts are not the source-locked headline.

V1.4 repeats the v1.3 schedule and measurements. Its pre-run lock adds hashes for every top-level `seeds/*.json` and `seeds/generated/*.json` manifest (the exact two globs consumed by `load_all_seeds()`), plus every Python source file under `domains/`, `substrate/`, and `runners/dsl/python/`, in addition to direct runner/analyzer/protocol/native/build inputs. Worker start, worker finish, and parent post-run locks must match exactly. The full source hash map is intentionally retained in the raw record.

No semantic changes, added routes, new task vocabulary, or changes to the counter wrapper are introduced. The same limits from v1.3 apply: one `describe_scene` workload on one WorldAdapter, one serialized two-thread schedule, instrumentation scoped to six lifecycle helper calls, and no natural-task or general concurrency claim.
