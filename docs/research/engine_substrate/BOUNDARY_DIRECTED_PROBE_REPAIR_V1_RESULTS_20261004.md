# Candidate-boundary-directed probe repair v1 results

## Result

All five frozen opposition panels pass the targeted repair. Extracting the
`ax < 4` comparison from the restricted candidate produces three probes at
`ax=3.5, 4, 4.5`, paired with `ex=-ax`. The native discriminating-input
selector chooses `[4, 0, -4, 0]` in every panel. One oracle label removes the
restricted candidate and retains the two structurally distinct exact Terms.
The boundary generator evaluates nine candidate/probe pairs per panel.

Independent replay confirms the query, oracle label, candidate transitions,
and remaining behavior class. Both survivors match the opposition relation
on the registered holdout and all 3,024 independent balanced wide-range and
boundary examples per member. Across the paired comparison, the fixed
coverage policy has five false-safe returns; the targeted boundary probe has
zero.

## Interpretation and limits

Candidate-directed probing repairs the registered `x < 4` counterexample
cheaply: one strategically placed label replaces an unsafe zero-label class
return. This is a narrow constructive repair, not a general guarantee. The
harness supplies the opposition task and exact candidate family; the probe
builder is specialized to solving `ax == -ex` at a comparison threshold. It
does not cover arbitrary operators, multiple interacting constraints,
non-numeric domains, or candidates whose relevant boundary is absent from
their syntax. Broader task families and comparison with abstention remain
necessary.

## Reproduction artifacts

- [Preregistration](BOUNDARY_DIRECTED_PROBE_REPAIR_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/boundary_directed_probe_repair_v1.py)
- [Source lock](../../../evaluation/substrate_capability/boundary_directed_probe_repair_v1_lock_20261004.json)
- [Capture](../../../evaluation/reports/boundary_directed_probe_repair_v1_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_boundary_directed_probe_repair_v1.py)
- [Analysis](../../../evaluation/reports/boundary_directed_probe_repair_v1_analysis_20261004.json)
- [False-safe baseline](PROBE_COVERAGE_FALSE_EQUIVALENT_V1_RESULTS_20261004.md)
