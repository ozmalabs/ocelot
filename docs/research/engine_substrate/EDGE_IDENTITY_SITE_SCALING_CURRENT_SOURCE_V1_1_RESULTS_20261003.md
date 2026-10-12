# Edge identity site scaling — current-source results

Date: 2026-10-03

## Result

The source-locked matrix covers 1/2/4/8/16/32/64/128/256 direct bound fields,
with two warmups and seven trials per size. All 10 independent checks pass:
the seven-field source lock is current and stable, candidate counts match the
preregistered formula, every direct field is represented, unsupported constant
and computed fields are excluded, and timing records are complete.

At 256 direct fields, the finder returns 32,897 attribute signatures plus one
relation site, with 44.39 ms median extraction. At 128 fields it returns 8,257
attribute signatures plus one relation site in 7.60 ms; at 64 fields it
returns 2,081 plus one in 1.46 ms. The observed counts follow
`m + choose(m,2) + 1[m>2]`, confirming quadratic site-count growth under the
singleton/pair/full-set grammar.

## Boundary and next gate

This is candidate extraction on a synthetic rule, not complete composer cost.
The measured function takes a rule and has no host-graph input; it says nothing
about graph-resident `EditSite` insertion, native Term choice, memory, or
task-level utility as graph size grows. Separate composer studies test a
fixed actor+verb proposal on large unrelated-node graphs, but a current-source
cross of field count and graph size remains open. The next gate should vary
both axes through the complete extraction/materialization/selection path,
add field-count resource caps, and retain unsupported computed/constant cases
as fail-closed controls. After this, test cue formation from residual evidence
without naming the operator.

## Artifacts

- [Preregistration](EDGE_IDENTITY_SITE_SCALING_CURRENT_SOURCE_V1_PREREG_20261003.md) and [lock amendment](EDGE_IDENTITY_SITE_SCALING_CURRENT_SOURCE_V1_1_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/measure_edge_identity_site_scaling_current_source_v1_1.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_edge_identity_site_scaling_current_source_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/edge_identity_site_scaling_current_source_v1_1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/edge_identity_site_scaling_current_source_v1_1_20261003.json), [analysis](../../../evaluation/reports/edge_identity_site_scaling_current_source_v1_1_analysis_20261003.json)
- The initial incomplete-lock run remains preserved as a diagnostic [pilot capture](../../../evaluation/reports/edge_identity_site_scaling_current_source_v1_20261003.json).
