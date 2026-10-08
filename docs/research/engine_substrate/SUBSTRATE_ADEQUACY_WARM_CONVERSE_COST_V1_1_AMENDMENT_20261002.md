# Warm-converse cost v1.1 amendment — evidence timing order

Date: 2026-10-02

The locked runner follows the preregistered timing scopes but not the preregistered order for audit-request construction. It parses the candidate Term before the first timed turn, measures `converse("hello")`, then constructs the request/receipt, then measures the target `converse`. The protocol says to construct the request before timing.

This is a disclosed protocol-order deviation. Request/receipt construction is outside both timers; the first `hello` call has no evidence input, and the target route receives fully constructed evidence before its timer starts. Therefore the measured warm-up and target-call scopes remain isolated from receipt-construction cost, but the strict preregistered order was not followed. The v1 capture is retained; do not describe it as exact protocol-order adherence. A future replication should construct both candidate and request evidence before the cold warm-up, without using it in that call.

No gates or outcomes were changed after capture. See the [v1 results](SUBSTRATE_ADEQUACY_WARM_CONVERSE_COST_V1_RESULTS_20261002.md), [protocol](SUBSTRATE_ADEQUACY_WARM_CONVERSE_COST_V1_PREREG_20261002.md), and locked raw capture.
