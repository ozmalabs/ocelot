# Live self-report lifecycle producer probe v1.1 amendment

The initial capture at `evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_20260926.json` passed the runner's route and semantic gates. Its independent audit found that `substrate/world_adapter.py` no longer matched the locked digest. File metadata places the source edit after initial lock creation and before capture completion, so one or more workers may have imported a different source revision. The capture is retained as a source-drift attempt and is not confirmatory evidence.

The confirmatory repeat uses a new lock and new output paths. In addition to the original gates, each worker records the complete locked-input fingerprint immediately before production imports and again after its turns. The parent records the fingerprint after all workers exit. The repeat passes source stability only when every worker start/end fingerprint and the final parent fingerprint equal the preregistered lock. A mismatch is a failed confirmatory run and must be preserved rather than relabeled.

No task text, route, outcome gates, or interpretation changed. The first run is not pooled with the amended run.
