# Live task runtime join capture analysis correction

Recorded 2026-09-27 after the three-worker capture; no worker data or input lock changed.

The locked first analyzer (`analyze_substrate_live_task_runtime_join_capture_v1.py`) used `kind` where captured rows name the field `event_kind`. Its first corrected copy also treated JSON object keys in event-time RuleIdx maps as integers even though JSON decoding yields strings. These analysis-only defects caused false-negative rule-pattern checks, not worker or counter failures. Version 1.2 converts those keys to integers and validates patterns against each closure's event-time rule snapshot. The raw 3-worker capture, task graph snapshot, and original locked analyzer bytes remain preserved. The v1.2 independent analysis now passes all capture-integrity checks while retaining the separate failed legacy reply-semantic gate.
