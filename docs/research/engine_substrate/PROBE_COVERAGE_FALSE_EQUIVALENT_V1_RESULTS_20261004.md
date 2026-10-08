# Probe-coverage false-equivalent control v1 results

## Result

The current coverage-aware policy returns all three supplied candidates as a
single behavior class in all five frozen opposition panels. It expands its
probe domain once, declares numeric coverage adequate, and asks for zero
oracle labels. The candidates are the exact relation `ax == -ex`, its
structurally different equivalent `-ax == ex`, and the restricted candidate
`(ax == -ex) AND (ax < 4)`.

Independent replay confirms the class members agree on every policy probe.
All three also pass the registered 6,560-row holdout, whose `ax` values stop
at 3.5. On a separate 3,024-case balanced wider domain, both exact candidates
remain correct, while the restricted candidate makes a median of 741 errors
per panel, concentrated on positive opposition examples at or above its
unobserved boundary. The predeclared numeric coverage condition (zero and
values at or below -2 and at or above +2 for each variable) therefore does not
certify candidate equivalence outside the observed support.

The independent analyzer passes because it reproduces the registered
false-safe outcome from the frozen source and capture. The policy result is a
failure finding: five of five returned classes include a candidate that
fails the wider evaluation.

## Interpretation and limits

This is one authored counterexample repeated over five training/probe panels.
It establishes a concrete insufficiency in the current coverage rule, not the
prevalence of hidden-boundary candidates in real synthesis. The candidate
Terms are supplied by the harness. The next repair gate should extract
comparison constants from surviving Terms, probe around those boundaries,
and compare against fixed expansion and abstention controls; it must then
repeat on distinct task families before generalizing.

## Reproduction artifacts

- [Preregistration](PROBE_COVERAGE_FALSE_EQUIVALENT_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/probe_coverage_false_equivalent_v1.py)
- [Source lock](../../../evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json)
- [Capture](../../../evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_probe_coverage_false_equivalent_v1.py)
- [Analysis](../../../evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json)
