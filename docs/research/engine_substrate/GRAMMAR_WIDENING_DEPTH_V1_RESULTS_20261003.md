# Grammar widening depth study v1 results

## Result

The source-locked study replays all five additive and five product panels from
the model-adequacy audit v1.1. Independent analysis passes all four gates:
locked panel replay, fixed arm settings, exact rescoring of every returned
candidate on the 1,296-point fractional grid, and source/capture binding.

With Neg/Eq/And plus the task-relevant operator, the size-7 search finds at
least one exact model in every panel (5/5 additive, 5/5 product) and does not
time out. Median wall/CPU time is 2.21/2.20 seconds for additive and
1.82/1.82 seconds for product. The size-9 search also returns an exact model
in all ten panels, but every arm reaches the 12-second timeout. It returns
134 additive candidates (median 12.01 s wall) and 65 product candidates
(median 12.01 s wall), versus 24 and 20 candidates at size 7. Partial results
are retained; timeouts do not erase the exact candidates found before the cap.

## Interpretation

This demonstrates bounded recovery on two harness-authored numeric targets
when a task-informed primitive is supplied. The size-7 bound covers the
compact target expression and is materially cheaper in this design. Size 9
adds candidates and consumes the full budget without improving exact-recovery
frequency. Because the operator is supplied from task identity, this does not
measure autonomous primitive discovery or a policy that chooses between
querying, widening, and asking for help. The earlier worker-0 pilot's
Plus/Eq-only and Times/Eq-only arms are exploratory and are not included in
these statistics.

The results support a next-stage experiment that separates two costs:
identifying a useful operator family and searching within it. Candidate work
should be allocated adaptively by size, with a measured stopping rule and a
fallback when the current grammar still has no adequate model. Such a policy
must be evaluated with target identity and held-out labels hidden.

## Reproduction artifacts

- [Preregistration](GRAMMAR_WIDENING_DEPTH_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/grammar_widening_depth_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_grammar_widening_depth_v1.py)
- [Source and panel lock](../../../evaluation/substrate_capability/grammar_widening_depth_v1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/grammar_widening_depth_v1_20261003.json)
- [Independent analysis](../../../evaluation/reports/grammar_widening_depth_v1_analysis_20261003.json)
