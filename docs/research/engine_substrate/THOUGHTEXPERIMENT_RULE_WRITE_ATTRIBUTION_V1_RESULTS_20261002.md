# Thoughtexperiment per-rule write attribution v1 results

The three-worker source-locked panel passes all semantic reconciliation gates on both direct-write fixtures. Ordinary, attributed, and exact-snapshot runs agree on fixed-point status, progress steps, and passes. In every worker, attributed targets cover all exact changed nodes and edges, aggregate mutation targets cover all per-rule event targets, and no events are dropped. The overlap fixture records both writers and a no-progress attempt. The capture contains 3 distinct worker PIDs and 45 timing pairs per fixture.

Across 45 paired samples per arm and fixture, median ordinary versus attributed settlement is 0.113 versus 0.171 ms for mixed direct writes (1.52×), and 0.112 versus 0.180 ms for overlapping/no-op writes (1.60×). These are small-fixture, single-host diagnostic costs; they do not estimate production workload overhead or show that tracing is free. Fixture construction is excluded.

## Interpretation

This validates rule-name-to-touched-location attribution for direct graph mutation APIs in the measured fixtures, including conservative no-op targets. It does not identify attribute keys, bindings, pre/post values, or ownership for deferred effects that drain between rule attempts. Therefore the trace is a useful causal-observation candidate but not sufficient for target-blind diagnosis or exact minimal-residual extraction. Those are the next learning and instrumentation gates.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RULE_WRITE_ATTRIBUTION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_rule_write_attribution_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_rule_write_attribution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_rule_write_attribution_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_rule_write_attribution_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_rule_write_attribution_v1_analysis_20261002.json)
