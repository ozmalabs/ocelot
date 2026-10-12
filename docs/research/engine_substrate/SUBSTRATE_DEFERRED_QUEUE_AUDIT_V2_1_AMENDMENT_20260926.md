# Deferred queue audit v2.1 analysis amendment

The source-locked v2 capture is unchanged. Its first analyzer stopped before producing an analysis because it looked up `native_extension_sha256`, while the lock schema names that field `native_extension`. The original analyzer source is restored to the version hashed by the capture lock. A separately versioned v2.1 analyzer uses the recorded field name, verifies the v2 analyzer hash, and passes all 157 independent checks.

This is an analysis-only correction. No workload, engine, queue counter, raw observation, or acceptance criterion changed. See the [v2 results](SUBSTRATE_DEFERRED_QUEUE_AUDIT_V2_RESULTS_20260926.md), [captured analyzer](../../../scripts/analyze_substrate_deferred_queue_audit_v2.py), [corrected analyzer](../../../scripts/analyze_substrate_deferred_queue_audit_v2_1.py), and [amended analysis](../../../evaluation/reports/substrate_deferred_queue_audit_v2_1_analysis_20260926.json).
