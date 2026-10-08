# Production retinal join-order panel v1.1 amendment

Date: 2026-10-01

## Reason

The v1 runner completed all nine workers and preserved their raw data, but the analyzer raised a Python `TypeError` while computing the per-permutation median. It therefore did not produce a valid gate report. The v1 capture is retained as diagnostic pilot evidence only.

## Amendment

No fixture, workload, comparison, or gate changes. Correct the analyzer's aggregation expression, assign the confirmatory runner/analyzer/lock/capture distinct v1.1 artifact names, refresh the source/native lock, and rerun all nine workers. The confirmatory analysis must pass the complete set of gates in the [v1 preregistration](PHOTON_RETINAL_JOIN_ORDER_V1_PREREG_20261001.md).
