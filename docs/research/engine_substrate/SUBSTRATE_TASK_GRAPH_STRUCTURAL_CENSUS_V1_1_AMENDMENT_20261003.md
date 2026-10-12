# Task-graph structural census v1.1 amendment

Date: 2026-10-03

The v1 runner failed before processing any graph because the discourse input records runs with `arm` (`plain`, `trace`, `repeat`) rather than a `replicate` field. The failure and source lock are retained; the failed stdout/stderr log records the `KeyError`. V1.1 uses the upstream `arm` as the stable run identifier for discourse snapshots. Graph selection, the planned 78 observations, metrics, structural projection, and claim boundary are unchanged. The v1.1 runner uses the shared manifest and fresh source lock; only it can produce confirmatory output.
