# Navigation polarity repair v1.1 review amendment — analyzer import path

The v1.1 three-worker raw capture completed under its source/native lock. The preregistered analyzer then stopped before computing any gate because it did not add the workspace to `sys.path` and could not import `substrate.boot_core`. No v1.1 analysis file was written by that attempt. The worker capture, source lock, and initial analyzer are retained unchanged.

A separate corrected reviewer now sets the workspace import path and independently recomputes the semantic, candidate, and source gates from the raw capture. It also checks the current source/native hashes against the capture lock. The reviewer has a separate path and records its own SHA-256. This amendment changes no worker result, oracle, treatment, or gate; it only makes the post-capture analysis executable. The corrected reviewer is the confirmatory analysis, while the failed analyzer invocation remains disclosed.

- [Original preregistration](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md)
- [NodeID serialization amendment](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_1_AMENDMENT_20261002.md)
- [V1.1 lock](../../../evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1_lock_20261002.json)
- [V1.1 raw capture](../../../evaluation/reports/thoughtexperiment_navigation_polarity_repair_v1_1_raw_20261002.json)
